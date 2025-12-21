# -*- coding: utf-8 -*-
"""
Queue Manager Dialog - UI for managing download queues with scheduling.
"""
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class QueueManagerDialog(QDialog):
    """Dialog for managing download queues."""

    def __init__(self, queue_manager, downloads, parent=None):
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.downloads = downloads  # Reference to main window's download list
        self.parent_window = parent

        self.setWindowTitle("Scheduler & Queue Manager")
        self.resize(1000, 600)
        self.setup_ui()
        self.load_queues()

    def setup_ui(self):
        """Build the dialog UI matching mockup."""
        main_layout = QHBoxLayout(self)

        # Left Panel: Queue List
        left_panel = QVBoxLayout()

        queue_label = QLabel("Queues")
        left_panel.addWidget(queue_label)

        self.queue_list = QListWidget()
        self.queue_list.currentItemChanged.connect(self.on_queue_selected)
        left_panel.addWidget(self.queue_list)

        # New Queue and Delete buttons
        btn_layout = QHBoxLayout()
        self.btn_new_queue = QPushButton("New Queue")
        self.btn_new_queue.clicked.connect(self.on_new_queue)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.on_delete_queue)

        btn_layout.addWidget(self.btn_new_queue)
        btn_layout.addWidget(self.btn_delete)
        left_panel.addLayout(btn_layout)

        main_layout.addLayout(left_panel, 1)

        # Right Panel: Tabs
        self.tabs = QTabWidget()

        # Tab 1: Files in Queue
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)

        # Concurrent downloads control
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("Download"))

        self.concurrent_spinner = QSpinBox()
        self.concurrent_spinner.setMinimum(1)
        self.concurrent_spinner.setMaximum(10)
        self.concurrent_spinner.setValue(3)
        self.concurrent_spinner.valueChanged.connect(self.on_concurrent_changed)
        concurrent_layout.addWidget(self.concurrent_spinner)

        concurrent_layout.addWidget(QLabel("files at the same time"))
        concurrent_layout.addStretch()
        files_layout.addLayout(concurrent_layout)

        # Files table
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["File Name", "Size", "Status", "Time Left"])
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        files_layout.addWidget(self.files_table)

        self.tabs.addTab(files_tab, "Files in Queue")

        # Tab 2: Schedule
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)

        schedule_label = QLabel("Schedule")
        schedule_layout.addWidget(schedule_label)

        # Start download at
        self.chk_start_at = QCheckBox("Start download at")
        self.chk_start_at.stateChanged.connect(self.on_schedule_changed)
        schedule_layout.addWidget(self.chk_start_at)

        self.datetime_start = QDateTimeEdit()
        self.datetime_start.setEnabled(False)
        schedule_layout.addWidget(self.datetime_start)

        # Stop download at
        self.chk_stop_at = QCheckBox("Stop download at")
        self.chk_stop_at.stateChanged.connect(self.on_schedule_changed)
        schedule_layout.addWidget(self.chk_stop_at)

        self.datetime_stop = QDateTimeEdit()
        self.datetime_stop.setEnabled(False)
        schedule_layout.addWidget(self.datetime_stop)

        # Periodic synchronization
        self.chk_periodic = QCheckBox("Periodic synchronization")
        schedule_layout.addWidget(self.chk_periodic)

        schedule_layout.addStretch()

        self.tabs.addTab(schedule_tab, "Schedule")

        main_layout.addWidget(self.tabs, 3)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.btn_start_now = QPushButton("Start Now")
        self.btn_start_now.clicked.connect(self.on_start_queue)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.on_stop_queue)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.clicked.connect(self.on_apply)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)

        bottom_layout.addWidget(self.btn_start_now)
        bottom_layout.addWidget(self.btn_stop)
        bottom_layout.addWidget(self.btn_apply)
        bottom_layout.addWidget(self.btn_close)

        # Add bottom buttons to main layout
        main_v_layout = QVBoxLayout()
        main_v_layout.addLayout(main_layout)
        main_v_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_v_layout)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.addWidget(container)

    def load_queues(self):
        """Loads all queues into the list."""
        self.queue_list.clear()
        for queue_name in self.queue_manager.get_queues():
            item = QListWidgetItem(queue_name)
            self.queue_list.addItem(item)

        # Select first queue
        if self.queue_list.count() > 0:
            self.queue_list.setCurrentRow(0)

    def on_queue_selected(self, current, previous):
        """Called when a queue is selected in the list."""
        if not current:
            return

        queue_name = current.text()
        self.refresh_files_table(queue_name)
        self.load_queue_settings(queue_name)

    def refresh_files_table(self, queue_name):
        """Refreshes the files table for selected queue."""
        self.files_table.setRowCount(0)

        # Filter downloads by queue
        queue_items = [d for d in self.downloads if d.queue == queue_name]

        for item in queue_items:
            row = self.files_table.rowCount()
            self.files_table.insertRow(row)

            self.files_table.setItem(row, 0, QTableWidgetItem(item.filename))
            self.files_table.setItem(row, 1, QTableWidgetItem(item.size))
            self.files_table.setItem(row, 2, QTableWidgetItem(item.status))
            self.files_table.setItem(row, 3, QTableWidgetItem("-"))

    def load_queue_settings(self, queue_name):
        """Loads queue settings into UI controls."""
        settings = self.queue_manager.get_queue_settings(queue_name)

        # Concurrent downloads
        self.concurrent_spinner.setValue(settings.get("max_concurrent", 3))

        # Schedule
        schedule_enabled = settings.get("schedule_enabled", False)
        self.chk_start_at.setChecked(schedule_enabled)
        self.datetime_start.setEnabled(schedule_enabled)

        # TODO: Load actual datetime values from settings

    def on_new_queue(self):
        """Creates a new queue."""
        text, ok = QInputDialog.getText(self, "New Queue", "Queue Name:")
        if ok and text:
            if self.queue_manager.create_queue(text):
                self.load_queues()
            else:
                QMessageBox.warning(self, "Error", "Queue already exists or invalid name.")

    def on_delete_queue(self):
        """Deletes the selected queue."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Queue",
            f"Delete queue '{queue_name}'?\nDownloads will be moved to default queue.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.queue_manager.delete_queue(queue_name):
                self.load_queues()

    def on_start_queue(self):
        """Starts the selected queue immediately."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()

        # Need to pass downloads and callback
        if hasattr(self.parent_window, "start_download_item"):
            self.queue_manager.start_queue(queue_name, self.downloads, self.parent_window.start_download_item)
            QMessageBox.information(self, "Started", f"Queue '{queue_name}' started.")

    def on_stop_queue(self):
        """Stops the selected queue."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()
        self.queue_manager.stop_queue(queue_name)
        QMessageBox.information(self, "Stopped", f"Queue '{queue_name}' stopped.")

    def on_concurrent_changed(self, value):
        """Called when concurrent downloads spinner changes."""
        current = self.queue_list.currentItem()
        if current:
            queue_name = current.text()
            settings = {"max_concurrent": value}
            self.queue_manager.update_queue_settings(queue_name, settings)

    def on_schedule_changed(self, state):
        """Called when schedule checkboxes change."""
        self.datetime_start.setEnabled(self.chk_start_at.isChecked())
        self.datetime_stop.setEnabled(self.chk_stop_at.isChecked())

    def on_apply(self):
        """Saves all settings."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()

        # Save schedule settings
        if self.chk_start_at.isChecked():
            start_time = self.datetime_start.dateTime().toPython()
            stop_time = self.datetime_stop.dateTime().toPython() if self.chk_stop_at.isChecked() else None
            self.queue_manager.set_schedule(queue_name, True, start_time, stop_time)
        else:
            self.queue_manager.set_schedule(queue_name, False)

        QMessageBox.information(self, "Saved", "Settings saved successfully.")
