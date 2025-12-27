# -*- coding: utf-8 -*-
"""
Queue Manager - Manages download queues with scheduling and concurrent limits.
"""

from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

# Default queue name constant
from src.core.i18n import I18n


def DEFAULT_QUEUE_NAME():
    return I18n.get("main_queue")


class QueueManager(QObject):
    """
    Manages named download queues with:
    - Concurrent download limiting (per-queue and global)
    - Time-based scheduling
    - Automatic queue progression
    """

    # Signals
    queue_started = Signal(str)  # queue_name
    queue_stopped = Signal(str)  # queue_name
    queue_updated = Signal(str)  # queue_name - when contents change
    queue_created = Signal(str)  # queue_name
    queue_deleted = Signal(str)  # queue_name

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.active_queues = set()  # Currently running queue names
        self.active_downloads = {}  # {download_id: True} for tracking
        self.timers = {}  # {queue_name: QTimer} for scheduling
        self.max_concurrent_global = self.config.get("max_concurrent_downloads", 3)

        # Load existing queues from config
        self._ensure_default_queues()

    def _ensure_default_queues(self):
        """Ensures default queues exist in config."""
        queues = self.config.get("queues", {})
        if not queues:
            queues = {
                DEFAULT_QUEUE_NAME: {
                    "icon": "download",
                    "max_concurrent": 3,
                    "schedule_enabled": False,
                    "schedule_start": None,
                    "schedule_stop": None,
                }
            }
            self.config.set("queues", queues)
            self.config.set("default_queue", DEFAULT_QUEUE_NAME)

    def get_queues(self):
        """Returns list of all queue names."""

        queues = self.config.get("queues", {})
        if isinstance(queues, list):
            return queues
        return list(queues.keys())

    def create_queue(self, name, icon="folder", max_concurrent=3):
        """Creates a new queue with default settings."""
        if not name or name in self.get_queues():
            return False

        queues = self.config.get("queues", {})
        # Convert legacy list to dict
        if isinstance(queues, list):
            queues = {
                q: {
                    "icon": "folder",
                    "max_concurrent": 3,
                    "schedule_enabled": False,
                    "schedule_start": None,
                    "schedule_stop": None,
                }
                for q in queues
            }

        queues[name] = {
            "icon": icon,
            "max_concurrent": max_concurrent,
            "schedule_enabled": False,
            "schedule_start": None,
            "schedule_stop": None,
        }
        self.config.set("queues", queues)
        self.queue_created.emit(name)
        return True

    def delete_queue(self, name):
        """Deletes a queue and reassigns its downloads to default queue."""
        # Protect default queue from deletion
        if name == DEFAULT_QUEUE_NAME:
            return False

        if name not in self.get_queues():
            return False

        # Stop if active
        if name in self.active_queues:
            self.stop_queue(name)

        # Remove from config
        queues = self.config.get("queues", {})
        # Convert legacy list to dict first
        if isinstance(queues, list):
            queues = {
                q: {
                    "icon": "folder",
                    "max_concurrent": 3,
                    "schedule_enabled": False,
                    "schedule_start": None,
                    "schedule_stop": None,
                }
                for q in queues
            }

        del queues[name]
        self.config.set("queues", queues)

        self.queue_deleted.emit(name)
        return True

    def get_queue_settings(self, name):
        """Returns settings dict for a queue."""
        queues = self.config.get("queues", {})
        # Handle legacy list format
        if isinstance(queues, list):
            return {
                "icon": "folder",
                "max_concurrent": 3,
                "schedule_enabled": False,
                "schedule_start": None,
                "schedule_stop": None,
            }
        return queues.get(name, {})

    def update_queue_settings(self, name, settings):
        """Updates queue settings."""
        queues = self.config.get("queues", {})
        if name in queues:
            queues[name].update(settings)
            self.config.set("queues", queues)
            self.queue_updated.emit(name)

    def start_queue(self, name, downloads, start_callback):
        """
        Starts processing a queue.

        Args:
            name: Queue name
            downloads: List of all DownloadItem objects
            start_callback: Function to call to start a download (download_item)
        """
        if name in self.active_queues:
            return  # Already running

        self.active_queues.add(name)
        self.queue_started.emit(name)

        # Process initial batch
        self._process_queue(name, downloads, start_callback)

    def stop_queue(self, name):
        """Stops a queue (does not stop active downloads, just prevents new ones)."""
        if name in self.active_queues:
            self.active_queues.discard(name)
            self.queue_stopped.emit(name)

    def on_download_complete(self, download_item, downloads, start_callback):
        """
        Called when a download completes. Starts next item in queue if needed.

        Args:
            download_item: The completed DownloadItem
            downloads: List of all DownloadItem objects
            start_callback: Function to start a download
        """
        # Remove from active tracking
        if download_item.id in self.active_downloads:
            del self.active_downloads[download_item.id]

        # Check if queue should continue
        queue_name = download_item.queue
        if queue_name and queue_name in self.active_queues:
            self._process_queue(queue_name, downloads, start_callback)

    def _process_queue(self, name, downloads, start_callback):
        """Internal method to start next pending downloads in queue."""
        if name not in self.active_queues:
            return

        queue_settings = self.get_queue_settings(name)
        max_concurrent = queue_settings.get("max_concurrent", 3)

        # Get queue items
        queue_items = [d for d in downloads if d.queue == name]

        # Count currently downloading in this queue
        active_in_queue = sum(
            1 for d in queue_items if d.status in ["Downloading", "Downloading..."] or d.id in self.active_downloads
        )

        # Check global limit
        total_active = len(self.active_downloads)
        can_start = min(max_concurrent - active_in_queue, self.max_concurrent_global - total_active)

        if can_start <= 0:
            return

        # Find pending items
        pending = [d for d in queue_items if d.status in ["Pending", "Stopped", "Failed", "Queued"]]
        pending.sort(key=lambda x: x.queue_position)

        # Start up to 'can_start' downloads
        started = 0
        for item in pending:
            if started >= can_start:
                break

            self.active_downloads[item.id] = True
            start_callback(item)
            started += 1

    def set_schedule(self, name, enabled, start_time=None, stop_time=None):
        """
        Sets scheduling for a queue.

        Args:
            name: Queue name
            enabled: Whether scheduling is enabled
            start_time: datetime object for start time
            stop_time: datetime object for stop time
        """
        settings = self.get_queue_settings(name)
        settings["schedule_enabled"] = enabled
        settings["schedule_start"] = start_time.isoformat() if start_time else None
        settings["schedule_stop"] = stop_time.isoformat() if stop_time else None
        self.update_queue_settings(name, settings)

        # Setup or remove timer
        if enabled and start_time:
            self._setup_schedule_timer(name)
        elif name in self.timers:
            self.timers[name].stop()
            del self.timers[name]

    def _setup_schedule_timer(self, name):
        """Sets up a QTimer to check schedule every minute."""
        if name in self.timers:
            return

        timer = QTimer()
        timer.timeout.connect(lambda: self._check_schedule(name))
        timer.start(60000)  # Check every minute
        self.timers[name] = timer

    def _check_schedule(self, name):
        """Checks if current time is within scheduled window and starts/stops queue."""
        settings = self.get_queue_settings(name)
        if not settings.get("schedule_enabled"):
            return

        start_str = settings.get("schedule_start")
        stop_str = settings.get("schedule_stop")

        if not start_str:
            return

        now = datetime.now()
        start_time = datetime.fromisoformat(start_str)
        stop_time = datetime.fromisoformat(stop_str) if stop_str else None

        # Check if within window
        if start_time.hour == now.hour and start_time.minute == now.minute:
            if name not in self.active_queues and name in self.queue_callbacks:
                # Retrieve stored callback and start queue
                downloads, callback = self.queue_callbacks[name]
                self.start_queue(name, downloads, callback)

        if stop_time and stop_time.hour == now.hour and stop_time.minute == now.minute:
            self.stop_queue(name)
