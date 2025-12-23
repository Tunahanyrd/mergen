# -*- coding: utf-8 -*-
"""
Queue Manager Dialog - UI for managing download queues with advanced scheduling.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.i18n import I18n


class QueueManagerDialog(QDialog):
    """IDM-inspired Queue Manager Dialog with tabbed interface."""

    def __init__(self, queue_manager, downloads, parent=None):
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.downloads = downloads
        self.parent_window = parent

        self.setWindowTitle("Scheduler & Queue Manager")
        self.resize(950, 600)
        self.setup_ui()
        self.load_queues()

    def setup_ui(self):
        """Build IDM-style tabbed interface."""
        # Main vertical layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Content area (horizontal: left panel + tabs)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Left Panel: Queue List
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        queue_label = QLabel(I18n.get("queues"))
        queue_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_panel.addWidget(queue_label)

        self.queue_list = QListWidget()
        self.queue_list.currentItemChanged.connect(self.on_queue_selected)
        left_panel.addWidget(self.queue_list)

        # Queue management buttons
        btn_layout = QHBoxLayout()
        self.btn_new_queue = QPushButton(I18n.get("new_queue"))
        self.btn_new_queue.clicked.connect(self.on_new_queue)

        self.btn_delete = QPushButton(I18n.get("delete"))
        self.btn_delete.clicked.connect(self.on_delete_queue)

        btn_layout.addWidget(self.btn_new_queue)
        btn_layout.addWidget(self.btn_delete)
        left_panel.addLayout(btn_layout)

        content_layout.addLayout(left_panel, 1)

        # Right Panel: Tabbed Content
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 2px solid #404050; }")

        # Tab 1: Schedule (IDM-style)
        self.schedule_tab = self.create_schedule_tab()
        self.tabs.addTab(self.schedule_tab, I18n.get("schedule"))

        # Tab 2: Files in Queue
        self.files_tab = self.create_files_tab()
        self.tabs.addTab(self.files_tab, I18n.get("files_in_queue"))

        content_layout.addWidget(self.tabs, 3)

        # Add content to main layout
        main_layout.addLayout(content_layout)

        # Bottom buttons (at the very bottom of dialog)
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()  # Push buttons to the right

        self.btn_start_now = QPushButton(I18n.get("start_now"))
        self.btn_start_now.clicked.connect(self.on_start_queue)

        self.btn_stop = QPushButton(I18n.get("stop"))
        self.btn_stop.clicked.connect(self.on_stop_queue)

        self.btn_help = QPushButton(I18n.get("help"))
        self.btn_apply = QPushButton(I18n.get("apply"))
        self.btn_apply.clicked.connect(self.on_apply)

        self.btn_close = QPushButton(I18n.get("close"))
        self.btn_close.clicked.connect(self.accept)

        bottom_layout.addWidget(self.btn_start_now)
        bottom_layout.addWidget(self.btn_stop)
        bottom_layout.addWidget(self.btn_help)
        bottom_layout.addWidget(self.btn_apply)
        bottom_layout.addWidget(self.btn_close)

        # Add bottom buttons to main layout
        main_layout.addLayout(bottom_layout)

    def create_schedule_tab(self):
        """Create IDM-style schedule tab with one-time/periodic modes."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Schedule Mode Group
        mode_group = QGroupBox("Schedule")
        mode_layout = QVBoxLayout()

        # One-time downloading
        self.radio_one_time = QCheckBox(I18n.get("one_time_downloading"))
        self.radio_one_time.setChecked(True)
        self.radio_one_time.stateChanged.connect(self.on_schedule_mode_changed)
        mode_layout.addWidget(self.radio_one_time)

        # Periodic synchronization
        self.radio_periodic = QCheckBox(I18n.get("periodic_synchronization"))
        self.radio_periodic.stateChanged.connect(self.on_schedule_mode_changed)
        mode_layout.addWidget(self.radio_periodic)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Start time
        start_group = QGroupBox(I18n.get("start_download"))
        start_layout = QVBoxLayout()

        self.chk_start_at = QCheckBox(I18n.get("start_download_at"))
        self.chk_start_at.stateChanged.connect(self.on_schedule_changed)
        start_layout.addWidget(self.chk_start_at)

        self.datetime_start = QDateTimeEdit()
        self.datetime_start.setDateTime(datetime.now())  # Initialize with current time
        self.datetime_start.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_start.setCalendarPopup(True)
        self.datetime_start.setEnabled(False)
        start_layout.addWidget(self.datetime_start)

        # Repeat options (only for one-time mode)
        repeat_layout = QHBoxLayout()
        self.chk_repeat = QCheckBox(I18n.get("start_again_every"))
        self.chk_repeat.stateChanged.connect(self.on_schedule_changed)
        repeat_layout.addWidget(self.chk_repeat)

        self.spin_repeat_value = QSpinBox()
        self.spin_repeat_value.setRange(1, 999)
        self.spin_repeat_value.setValue(2)
        self.spin_repeat_value.setEnabled(False)
        repeat_layout.addWidget(self.spin_repeat_value)

        self.combo_repeat_unit = QComboBox()
        self.combo_repeat_unit.addItems([I18n.get("hours"), I18n.get("minutes")])
        self.combo_repeat_unit.setEnabled(False)
        repeat_layout.addWidget(self.combo_repeat_unit)

        repeat_layout.addStretch()
        start_layout.addLayout(repeat_layout)

        start_group.setLayout(start_layout)
        layout.addWidget(start_group)

        # Daily schedule (only for periodic mode)
        self.daily_group = QGroupBox("Daily Schedule")
        daily_layout = QVBoxLayout()

        self.chk_daily = QCheckBox("Daily")
        daily_layout.addWidget(self.chk_daily)

        # Day selection
        days_layout = QHBoxLayout()
        self.day_checkboxes = []
        for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            chk = QCheckBox(day[:3])  # Short names
            self.day_checkboxes.append(chk)
            days_layout.addWidget(chk)
        daily_layout.addLayout(days_layout)

        self.daily_group.setLayout(daily_layout)
        self.daily_group.setVisible(False)  # Hidden by default
        layout.addWidget(self.daily_group)

        # Stop time
        stop_group = QGroupBox(I18n.get("stop_download"))
        stop_layout = QVBoxLayout()

        self.chk_stop_at = QCheckBox(I18n.get("stop_download_at"))
        self.chk_stop_at.stateChanged.connect(self.on_schedule_changed)
        stop_layout.addWidget(self.chk_stop_at)

        self.datetime_stop = QDateTimeEdit()
        self.datetime_stop.setDateTime(datetime.now())  # Initialize with current time
        self.datetime_stop.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_stop.setCalendarPopup(True)
        self.datetime_stop.setEnabled(False)
        stop_layout.addWidget(self.datetime_stop)

        stop_group.setLayout(stop_layout)
        layout.addWidget(stop_group)

        # Post-download actions
        actions_group = QGroupBox(I18n.get("post_download_actions"))
        actions_layout = QVBoxLayout()

        self.chk_open_file = QCheckBox(I18n.get("open_file_when_done"))
        actions_layout.addWidget(self.chk_open_file)

        self.chk_hang_up = QCheckBox(I18n.get("hang_up_modem"))
        actions_layout.addWidget(self.chk_hang_up)

        self.chk_exit_app = QCheckBox(I18n.get("exit_app_when_done"))
        actions_layout.addWidget(self.chk_exit_app)

        shutdown_layout = QHBoxLayout()
        self.chk_turn_off = QCheckBox(I18n.get("turn_off_computer"))
        shutdown_layout.addWidget(self.chk_turn_off)

        self.combo_shutdown_mode = QComboBox()
        self.combo_shutdown_mode.addItems([I18n.get("shut_down"), I18n.get("hibernate"), I18n.get("sleep")])
        self.combo_shutdown_mode.setEnabled(False)
        shutdown_layout.addWidget(self.combo_shutdown_mode)
        shutdown_layout.addStretch()

        self.chk_turn_off.stateChanged.connect(
            lambda: self.combo_shutdown_mode.setEnabled(self.chk_turn_off.isChecked())
        )

        actions_layout.addLayout(shutdown_layout)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()

        # Wrap entire layout in scroll area to prevent dialog resize
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content_widget = QWidget()
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)

        # Final tab layout
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

        return tab

    def create_files_tab(self):
        """Create files in queue tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Concurrent downloads
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel(I18n.get("download_label")))

        self.concurrent_spinner = QSpinBox()
        self.concurrent_spinner.setRange(1, 32)
        self.concurrent_spinner.setValue(3)
        self.concurrent_spinner.valueChanged.connect(self.on_concurrent_changed)
        concurrent_layout.addWidget(self.concurrent_spinner)

        concurrent_layout.addWidget(QLabel(I18n.get("files_at_same_time")))
        concurrent_layout.addStretch()
        layout.addLayout(concurrent_layout)

        # Files table
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(
            [I18n.get("file_name"), I18n.get("size"), I18n.get("status"), I18n.get("time_left")]
        )
        self.files_table.horizontalHeader().setStretchLastSection(True)
        self.files_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.files_table)

        # File management buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_move_up = QToolButton()
        btn_move_up.setText("↑")
        btn_move_up.setToolTip("Move up")
        btn_layout.addWidget(btn_move_up)

        btn_move_down = QToolButton()
        btn_move_down.setText("↓")
        btn_move_down.setToolTip("Move down")
        btn_layout.addWidget(btn_move_down)

        btn_remove = QToolButton()
        btn_remove.setText("✕")
        btn_remove.setToolTip("Remove from queue")
        btn_layout.addWidget(btn_remove)

        layout.addLayout(btn_layout)

        return tab

    def on_schedule_mode_changed(self, state):
        """Toggle between one-time and periodic mode."""
        sender = self.sender()

        if sender == self.radio_one_time and state:
            self.radio_periodic.setChecked(False)
            self.chk_repeat.setVisible(True)
            self.spin_repeat_value.setVisible(True)
            self.combo_repeat_unit.setVisible(True)
            self.daily_group.setVisible(False)
        elif sender == self.radio_periodic and state:
            self.radio_one_time.setChecked(False)
            self.chk_repeat.setVisible(False)
            self.spin_repeat_value.setVisible(False)
            self.combo_repeat_unit.setVisible(False)
            self.daily_group.setVisible(True)

    def on_schedule_changed(self, state):
        """Enable/disable schedule controls."""
        self.datetime_start.setEnabled(self.chk_start_at.isChecked())
        self.datetime_stop.setEnabled(self.chk_stop_at.isChecked())

        if self.chk_repeat.isChecked():
            self.spin_repeat_value.setEnabled(True)
            self.combo_repeat_unit.setEnabled(True)
        else:
            self.spin_repeat_value.setEnabled(False)
            self.combo_repeat_unit.setEnabled(False)

    def load_queues(self):
        """Load all queues into the list."""
        self.queue_list.clear()
        for queue_name in self.queue_manager.get_queues():
            item = QListWidgetItem(queue_name)
            self.queue_list.addItem(item)

        if self.queue_list.count() > 0:
            self.queue_list.setCurrentRow(0)

    def on_queue_selected(self, current, previous):
        """Called when a queue is selected."""
        if not current:
            return

        queue_name = current.text()
        self.refresh_files_table(queue_name)
        self.load_queue_settings(queue_name)

    def refresh_files_table(self, queue_name):
        """Refresh files table for selected queue."""
        self.files_table.setRowCount(0)

        queue_items = [d for d in self.downloads if d.queue == queue_name]

        for item in queue_items:
            row = self.files_table.rowCount()
            self.files_table.insertRow(row)

            self.files_table.setItem(row, 0, QTableWidgetItem(item.filename))
            self.files_table.setItem(row, 1, QTableWidgetItem(item.size))
            self.files_table.setItem(row, 2, QTableWidgetItem(item.status))
            self.files_table.setItem(row, 3, QTableWidgetItem("-"))

    def load_queue_settings(self, queue_name):
        """Load queue settings into UI."""
        settings = self.queue_manager.get_queue_settings(queue_name)

        # Concurrent downloads
        self.concurrent_spinner.setValue(settings.get("max_concurrent", 3))

        # Schedule
        schedule_enabled = settings.get("schedule_enabled", False)
        self.chk_start_at.setChecked(schedule_enabled)
        self.datetime_start.setEnabled(schedule_enabled)

    def on_new_queue(self):
        """Create a new queue."""
        text, ok = QInputDialog.getText(self, "New Queue", "Queue Name:")
        if ok and text:
            if self.queue_manager.create_queue(text):
                self.load_queues()
            else:
                QMessageBox.warning(self, "Error", "Queue already exists or invalid name.")

    def on_delete_queue(self):
        """Delete the selected queue."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()

        reply = QMessageBox.question(
            self,
            I18n.get("delete"),
            I18n.get("delete_queue_confirm").format(queue_name),
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            result = self.queue_manager.delete_queue(queue_name)
            if result:
                self.load_queues()
            else:
                from src.core.queue_manager import DEFAULT_QUEUE_NAME

                if queue_name == DEFAULT_QUEUE_NAME:
                    QMessageBox.warning(self, "Error", f"Cannot delete default queue '{DEFAULT_QUEUE_NAME}'.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete queue.")

    def on_start_queue(self):
        """Start the selected queue."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()

        if hasattr(self.parent_window, "start_download_item"):
            self.queue_manager.start_queue(queue_name, self.downloads, self.parent_window.start_download_item)
            QMessageBox.information(self, "Started", f"Queue '{queue_name}' started.")

    def on_stop_queue(self):
        """Stop the selected queue."""
        current = self.queue_list.currentItem()
        if not current:
            return

        queue_name = current.text()
        self.queue_manager.stop_queue(queue_name)
        QMessageBox.information(self, "Stopped", f"Queue '{queue_name}' stopped.")

    def on_concurrent_changed(self, value):
        """Update concurrent downloads limit."""
        current = self.queue_list.currentItem()
        if current:
            queue_name = current.text()
            settings = {"max_concurrent": value}
            self.queue_manager.update_queue_settings(queue_name, settings)

    def on_apply(self):
        """Save all settings."""
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
