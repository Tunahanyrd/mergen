# -*- coding: utf-8 -*-


class QueueManager:
    """
    Manages named queues of downloads.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueueManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Queues: { "Main Queue": [download_item_1, download_item_2], "Queue 2": [] }
        # Note: 'download_item' is the dict object shared with MainWindow list
        self.queues = {"Main Queue": []}
        self.active_queues = set()  # Set of queue names currently processing
        self.listeners = []  # Callbacks for when queue updates

    def get_queues(self):
        return self.queues.keys()

    def add_to_queue(self, queue_name, item):
        if queue_name not in self.queues:
            self.queues[queue_name] = []
        if item not in self.queues[queue_name]:
            self.queues[queue_name].append(item)
            item["queue"] = queue_name
            self.notify_listeners()

    def start_queue(self, queue_name, starter_func):
        """
        Starts processing the queue.
        starter_func: func(item) that initiates download
        """
        if queue_name not in self.queues:
            return
        self.active_queues.add(queue_name)

        # Start first pending item
        self.process_next(queue_name, starter_func)

    def stop_queue(self, queue_name):
        if queue_name in self.active_queues:
            self.active_queues.remove(queue_name)

    def process_next(self, queue_name, starter_func):
        if queue_name not in self.active_queues:
            return

        q = self.queues[queue_name]
        # Find first non-complete, non-downloading item?
        # Ideally, we look for 'Queued' items.

        for item in q:
            if getattr(item, "status", None) in ["Queued", "Stopped", "Failed", "Pending"]:  # Ready to start
                starter_func(item)
                # We start one, and wait for it to finish.
                # MainWindow needs to call 'on_download_finished' to trigger next.
                return

        # If we are here, queue might be empty of pending jobs
        # self.stop_queue(queue_name)

    def on_download_finished(self, item, starter_func):
        # Called by MainWindow when a download finishes
        q_name = getattr(item, "queue", None)
        if q_name and q_name in self.active_queues:
            self.process_next(q_name, starter_func)

    def add_listener(self, func):
        self.listeners.append(func)

    def notify_listeners(self):
        for f in self.listeners:
            try:
                f()
            except Exception:
                pass
