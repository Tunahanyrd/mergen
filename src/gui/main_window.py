# -*- coding: utf-8 -*-
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTime, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QCursor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.config import ConfigManager
from src.core.i18n import I18n
from src.core.models import DownloadItem
from src.core.queue_manager import QueueManager
from src.gui.download_dialog import DownloadDialog
from src.gui.first_run_dialog import FirstRunDialog
from src.gui.properties_dialog import PropertiesDialog
from src.gui.quality_dialog_v2 import QualityDialogV2  # v2.0 with audio-only, playlist, badges
from src.gui.queue_manager_dialog import QueueManagerDialog
from src.gui.settings_dialog import SettingsDialog
from src.gui.styles import MERGEN_THEME, MERGEN_THEME_LIGHT
from src.gui.workers import AnalysisWorker


class MainWindow(QMainWindow):
    browser_download_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(I18n.get("app_title"))
        self.resize(1000, 600)

        # Icon Setup
        # Handle Nuitka/PyInstaller _MEIPASS
        if hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # If we are in src/gui, we need to go up to root
            # layout is root/data and root/src/gui
            # So from src/gui, we go up two levels?
            # Actually, standardizing on os.getcwd() usually works for dev,
            # but let's try to be robust.
            base_dir = os.getcwd()

        icon_path = os.path.join(base_dir, "data", "mergen.png")
        if not os.path.exists(icon_path):
            # Fallback: maybe we are in src/gui and data is in ../../data
            # But usually running from 'main.py' at root sets CWD to root.
            pass

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            self.app_icon = QIcon(icon_path)
        else:
            self.app_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)

        self.config = ConfigManager()

        geom = self.config.get("geometry")
        if geom:
            try:
                self.restoreGeometry(bytes.fromhex(geom))
            except Exception:
                pass

        self.downloads = self.config.get_history()
        self.active_dialogs = []
        self.row_map = {}
        self.queue_manager = QueueManager(self.config)
        self.browser_download_signal.connect(self.handle_browser_download)
        self.setup_ui()

        self.apply_theme()
        self.refresh_table()
        self.setup_tray()

        # First Run / Version Update Check
        try:
            from importlib.metadata import version

            current_version = version("mergen")
        except Exception:
            # Fallback for bundled/dev mode - read from pyproject.toml
            from pathlib import Path

            import tomllib

            try:
                if hasattr(sys, "_MEIPASS"):
                    # Bundled mode - version baked into config or use default
                    current_version = "0.9.3"  # Hardcoded for bundled releases
                else:
                    # Dev mode - read from pyproject.toml
                    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
                    if pyproject_path.exists():
                        with open(pyproject_path, "rb") as f:
                            pyproject = tomllib.load(f)
                            current_version = pyproject.get("project", {}).get("version", "0.0.0")
                    else:
                        current_version = "0.0.0"
            except Exception:
                current_version = "0.0.0"

        last_version = self.config.get("last_version", None)

        if self.config.get("first_run", True):
            # True first run
            QTimer.singleShot(100, self.show_first_run_dialog)
        elif last_version != current_version:
            # Version changed - could show "What's New" dialog
            # For now, just update the version
            self.config.set("last_version", current_version)

    def show_first_run_dialog(self):
        dlg = FirstRunDialog(self)
        if dlg.exec():
            # Save version on first run completion
            # Use already-detected version from __init__
            current_version = self.config.get("last_version", "0.9.3")
            self.config.set("last_version", current_version)

    def closeEvent(self, event):
        """Handle window close - minimize to tray if enabled."""
        close_to_tray = self.config.get("close_to_tray", False)

        if close_to_tray and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "Mergen",
                    "Application minimized to tray. Double-click tray icon to restore.",
                    QSystemTrayIcon.Information,
                    2000,
                )
        else:
            # Actually close
            self.config.set("geometry", self.saveGeometry().toHex().data().decode())
            self.config.save_history(self.downloads)
            super().closeEvent(event)

    def apply_theme(self):
        theme = self.config.get("theme", "dark").lower()
        if theme == "light":
            self.setStyleSheet(MERGEN_THEME_LIGHT)
            # Update icons/text color for toolbar if needed manually,
            # but stylesheet handles most.
            if hasattr(self, "total_speed_lbl"):
                self.total_speed_lbl.setStyleSheet("color: #007acc; font-weight: bold;")
        else:
            self.setStyleSheet(MERGEN_THEME)
            if hasattr(self, "total_speed_lbl"):
                self.total_speed_lbl.setStyleSheet("color: #00f2ff; font-weight: bold;")

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_menubar()

        self.toolbar_ref = self.create_toolbar()
        # Initial style, apply_theme will override
        main_layout.addWidget(self.toolbar_ref)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(10, 0, 10, 10)
        body_layout.setSpacing(10)

        # Sidebar - 1 Column Only (Requested fix)
        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderHidden(True)
        self.sidebar.setColumnCount(1)
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(240)
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        self.sidebar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sidebar.customContextMenuRequested.connect(self.show_sidebar_menu)
        self.sidebar.setRootIsDecorated(False)
        self.sidebar.setIndentation(10)

        self.setup_sidebar()
        self.sidebar.itemClicked.connect(self.filter_by_category)

        body_layout.addWidget(self.sidebar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                I18n.get("file_name"),
                I18n.get("size"),
                I18n.get("status"),
                I18n.get("time_left"),
                I18n.get("transfer_rate"),
                I18n.get("last_try"),
                I18n.get("description"),
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemDoubleClicked.connect(self.handle_double_click)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setHighlightSections(False)

        body_layout.addWidget(self.table)

        main_layout.addLayout(body_layout)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 5, 20, 5)
        footer_layout.addStretch()
        self.total_speed_lbl = QLabel(I18n.get("total_speed") + ": 0.0 MB/s")
        footer_layout.addWidget(self.total_speed_lbl)

        main_layout.addLayout(footer_layout)

        self.speed_timer = QTimer(self)
        self.speed_timer.timeout.connect(self.update_total_speed)
        self.speed_timer.start(1000)

    # Removed update_sidebar_counts logic (Column 2 removed)

    def create_menubar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu(I18n.get("file"))

        add_url_act = QAction(I18n.get("add_url"), self)
        add_url_act.setShortcut("Ctrl+N")
        add_url_act.triggered.connect(self.add_url)
        file_menu.addAction(add_url_act)

        exit_act = QAction(I18n.get("exit"), self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        help_menu = menu_bar.addMenu(I18n.get("help"))

        about_act = QAction(I18n.get("about"), self)
        about_act.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_act)

    def toggle_toolbar(self, checked):
        if hasattr(self, "toolbar_ref"):
            self.toolbar_ref.setVisible(checked)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(28, 28))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        actions = [
            (I18n.get("add_url"), self.get_std_icon("add"), self.add_url),
            (I18n.get("resume"), self.get_std_icon("play"), self.resume_download),
            (I18n.get("stop"), self.get_std_icon("pause"), self.stop_download),
            (I18n.get("stop"), self.get_std_icon("stop"), self.stop_all_downloads),
            (I18n.get("delete"), self.get_std_icon("delete"), self.delete_download),
            (None, None, None),
            (I18n.get("options"), self.get_std_icon("settings"), self.open_settings),
            (I18n.get("scheduler"), self.get_std_icon("sched"), self.open_queue_manager_dialog),
        ]

        for item in actions:
            if item[0] is None:
                toolbar.addSeparator()
                continue
            name, icon, slot = item
            act = QAction(icon, name, self)
            if slot:
                act.triggered.connect(slot)
            toolbar.addAction(act)

        toolbar.addSeparator()
        del_all_act = QAction(self.get_std_icon("trash"), I18n.get("delete_all"), self)
        del_all_act.triggered.connect(self.delete_all_action)
        toolbar.addAction(del_all_act)

        return toolbar

    def get_std_icon(self, name):
        # ... (Same helper) ...
        style = QApplication.style()
        if name == "folder":
            return style.standardIcon(QStyle.SP_DirIcon)
        if name == "file":
            return style.standardIcon(QStyle.SP_FileIcon)
        if name == "stop":
            return style.standardIcon(QStyle.SP_MediaStop)
        if name == "play":
            return style.standardIcon(QStyle.SP_MediaPlay)
        if name == "pause":
            return style.standardIcon(QStyle.SP_MediaPause)
        if name == "delete":
            return style.standardIcon(QStyle.SP_TrashIcon)
        if name == "add":
            return style.standardIcon(QStyle.SP_FileDialogNewFolder)
        if name == "settings":
            return style.standardIcon(QStyle.SP_ComputerIcon)
        if name == "video":
            return style.standardIcon(QStyle.SP_MediaVolume)
        if name == "music":
            return style.standardIcon(QStyle.SP_MediaVolume)
        if name == "doc":
            return style.standardIcon(QStyle.SP_FileIcon)
        if name == "app":
            return style.standardIcon(QStyle.SP_DesktopIcon)
        if name == "zip":
            return style.standardIcon(QStyle.SP_DriveFDIcon)
        if name == "success":
            return style.standardIcon(QStyle.SP_DialogApplyButton)
        if name == "error":
            return style.standardIcon(QStyle.SP_MessageBoxCritical)
        if name == "link":
            return style.standardIcon(QStyle.SP_DirLinkIcon)
        if name == "sched":
            return style.standardIcon(QStyle.SP_FileDialogDetailedView)
        return style.standardIcon(QStyle.SP_FileIcon)

    def setup_sidebar(self):
        self.sidebar.clear()

        def add_item(parent, title, icon_name, user_data):
            item = QTreeWidgetItem(parent, [title])
            item.setIcon(0, self.get_std_icon(icon_name))
            item.setData(0, Qt.UserRole, user_data)
            return item

        root = add_item(self.sidebar, I18n.get("all_downloads"), "link", ("all", None))
        root.setExpanded(True)

        cats = self.config.get("categories", {})
        for cat_key, val in cats.items():
            if len(val) >= 2:
                icon = val[1]
            else:
                continue

            # Translate category names based on key
            display_name = cat_key
            lower_cat = cat_key.lower()

            # Check for each default category type
            if (
                "compress" in lower_cat
                or "zip" in lower_cat
                or "rar" in lower_cat
                or "archive" in lower_cat
                or "arş" in lower_cat
            ):
                display_name = I18n.get("compressed")
            elif "video" in lower_cat:
                display_name = I18n.get("videos")
            elif "music" in lower_cat or "müz" in lower_cat:
                display_name = I18n.get("music")
            elif "doc" in lower_cat or "belge" in lower_cat:
                display_name = I18n.get("documents")
            elif "program" in lower_cat:
                display_name = I18n.get("programs")

            # Key change: Data is now tuple ("cat", cat_key)
            add_item(root, display_name, icon, ("cat", cat_key))

        add_item(root, I18n.get("others"), "file", ("others", None))

        add_item(self.sidebar, I18n.get("unfinished"), "pause", ("unfinished", None))
        add_item(self.sidebar, I18n.get("finished"), "success", ("finished", None))

    # Queue Logic Integration
    def on_queue_update(self):
        # Refresh if queue status changes? Not strictly visual unless we show queue status in table.
        # But we can verify active queues.
        pass

    def start_download_item_func(self, item_data):
        # Check if already open
        for dlg in self.active_dialogs:
            if dlg.url == item_data.url:
                return

        save_dir = item_data.save_path or self.config.get("default_download_dir")

        # Auto start
        dlg = DownloadDialog(item_data.url, self, save_dir=save_dir)

        # 1. Completion
        dlg.download_complete.connect(lambda s, f: self.update_download_status(item_data, s, f))

        # 2. Live Updates
        dlg.worker.progress_signal.connect(lambda d, t, s, seg: self.update_live_row(item_data, d, t, s))

        # 3. Status Updates
        dlg.worker.status_signal.connect(lambda m: self.update_item_status(item_data, m))

        self.active_dialogs.append(dlg)
        dlg.finished.connect(lambda: self.cleanup_dialog(dlg))

        # Item status update
        item_data.status = I18n.get("downloading")
        self.config.save_history(self.downloads)
        self.refresh_table()

        dlg.show()

    def update_live_row(self, item_data, downloaded, total, speed):
        # Lookup row by ID
        if not hasattr(self, "row_map") or item_data.id not in self.row_map:
            return

        row = self.row_map[item_data.id]

        # Verify row integrity (in case of clears)
        if row < 0 or row >= self.table.rowCount():
            return

        # Format strings
        if speed > 1024 * 1024:
            sp_str = f"{speed / (1024 * 1024):.1f} MB/s"
        else:
            sp_str = f"{speed / 1024:.1f} KB/s"

        if downloaded > 1024 * 1024 * 1024:
            dl_str = f"{downloaded / (1024 * 1024 * 1024):.2f} GB"
        else:
            dl_str = f"{downloaded / (1024 * 1024):.2f} MB"

        if total > 1024 * 1024 * 1024:
            tot_str = f"{total / (1024 * 1024 * 1024):.2f} GB"
        else:
            tot_str = f"{total / (1024 * 1024):.2f} MB"

        # ETA
        eta_str = "--:--:--"
        if total > 0 and speed > 0:
            rem = total - downloaded
            secs = int(rem / speed)
            if secs > 86400:
                eta_str = "> 1d"
            else:
                try:
                    eta_str = QTime(0, 0, 0).addSecs(secs).toString("HH:mm:ss")
                except Exception:
                    eta_str = "--:--:--"

        # Update Table Items (Columns: File, Size, Status, Time, Rate, LastTry, Desc)
        # Col 0: File Name (Already set, but ensure)

        # Col 1: Size -> "DL / Total"
        self.table.item(row, 1).setText(f"{dl_str} / {tot_str}")

        # Col 2: Status
        pct = int((downloaded / total) * 100) if total > 0 else 0
        if item_data.status not in ["Stopped", "Paused", I18n.get("complete"), I18n.get("failed")]:
            self.table.item(row, 2).setText(f"{I18n.get('downloading')} {pct}%")
        else:
            self.table.item(row, 2).setText(item_data.status)

        # Col 3: Time Left
        self.table.item(row, 3).setText(eta_str)
        # Col 4: Rate
        self.table.item(row, 4).setText(sp_str)

    def add_category_action(self):
        text, ok = QInputDialog.getText(self, I18n.get("add_category"), I18n.get("category_name"))
        if ok and text:
            cats = self.config.get("categories", {})
            if text in cats:
                QMessageBox.warning(self, I18n.get("error"), I18n.get("category_exists"))
                return

            exts_txt, ok2 = QInputDialog.getMultiLineText(self, I18n.get("extensions"), I18n.get("enter_extensions"))
            if ok2:
                exts = exts_txt.split()
                cats[text] = (exts, "folder")  # Default icon
                self.config.set("categories", cats)
                self.setup_sidebar()

    def edit_category_action(self, item):
        QMessageBox.information(self, I18n.get("info"), I18n.get("edit_in_settings"))
        self.open_settings()

    # Queue Manager methods
    def open_queue_manager_dialog(self):
        """Opens the Queue Manager dialog."""
        dialog = QueueManagerDialog(self.queue_manager, self.downloads, self)
        dialog.exec()
        self.refresh_table()

    def move_to_queue(self, queue_name):
        """Moves selected download to specified queue."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        if row >= len(self.downloads):
            return

        download_item = self.downloads[row]
        download_item.queue = queue_name
        download_item.queue_position = len([d for d in self.downloads if d.queue == queue_name])

        self.config.save_history(self.downloads)
        self.refresh_table()

    def start_download_item(self, download_item):
        """Starts a download item (callback for queue manager)."""
        download_item.status = "Downloading..."
        self.refresh_table()
        # This is called by queue manager; actual download handled by DownloadDialog

    # Removed open_scheduler

    def update_item_status(self, item_data, status_msg):
        # Called by worker signal to update status in real-time
        item_data.status = status_msg
        # Immediate row update
        if hasattr(self, "row_map") and item_data.id in self.row_map:
            row = self.row_map[item_data.id]
            if 0 <= row < self.table.rowCount():
                self.table.item(row, 2).setText(status_msg)

    def on_download_finished_trigger_queue(self, download_item):
        # REMOVED QUEUE LOGIC TO PREVENT CRASH
        pass

    def update_download_status(self, download_item, success, filename):
        # Existing logic...
        download_item.status = I18n.get("complete") if success else I18n.get("failed")
        if success:
            download_item.filename = filename
            download_item.size = I18n.get("done")

        self.config.save_history(self.downloads)
        self.refresh_table()

        # Trigger Queue
        self.on_download_finished_trigger_queue(download_item)

        # Notify queue manager for automatic progression
        if download_item.queue:
            self.queue_manager.on_download_complete(download_item, self.downloads, self.start_download_item)

    # ... (Rest of methods: refresh_table, actions etc, keeping consistent) ...

    def refresh_table(self, filter_data=None):
        self.table.setRowCount(0)

        filter_status = None
        filter_queue = None
        filter_exts = None
        is_others = False

        if filter_data == "unfinished":
            filter_status = [
                "Downloading...",
                "Failed",
                I18n.get("downloading"),
                I18n.get("failed"),
                "Pending",
                "Stopped",
            ]
        elif filter_data == "finished":
            filter_status = ["Complete", I18n.get("complete")]
        elif filter_data == "others":
            is_others = True
        elif isinstance(filter_data, str) and filter_data.startswith("queue:"):
            filter_queue = filter_data.split(":", 1)[1]
        elif isinstance(filter_data, list):
            filter_exts = filter_data

        all_exts = []
        if is_others:
            cats = self.config.get("categories", {})
            for val in cats.values():
                if len(val) >= 1:
                    all_exts.extend(val[0])

        # Reset Row Map on refresh
        self.row_map = {}

        for d in self.downloads:
            # Filter logic
            if filter_status:
                if d.status not in filter_status:
                    continue
            if filter_queue:
                if d.queue != filter_queue:
                    continue
            if filter_exts:
                ext = Path(d.filename).suffix.lstrip(".").lower()
                if ext not in filter_exts:
                    continue
            if is_others:
                ext = Path(d.filename).suffix.lstrip(".").lower()
                if ext in all_exts:
                    continue

            # Row mapping
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.row_map[d.id] = row  # Map ID to Row Index

            # Populate Columns
            # Col 0: File Name
            self.table.setItem(row, 0, QTableWidgetItem(os.path.basename(d.filename)))
            # Col 1: Size (Show Known Size)
            size_str = d.size
            if d.total_bytes > 0:
                gb = d.total_bytes / (1024**3)
                mb = d.total_bytes / (1024**2)
                size_str = f"{gb:.2f} GB" if gb > 1 else f"{mb:.2f} MB"
            self.table.setItem(row, 1, QTableWidgetItem(size_str))

            # Col 2: Status
            self.table.setItem(row, 2, QTableWidgetItem(d.status))

            # Col 3: Time Left (Empty initially)
            self.table.setItem(row, 3, QTableWidgetItem("--:--:--"))

            # Col 4: Rate
            self.table.setItem(row, 4, QTableWidgetItem("0.0 MB/s"))

            # Col 5: Date Added
            self.table.setItem(row, 5, QTableWidgetItem(d.date_added))

            # Col 6: Desc / URL
            self.table.setItem(row, 6, QTableWidgetItem(d.url))

            # self.add_table_row(d) -> Removed, handled above

    def add_table_row(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)

        fname = os.path.basename(data.filename)
        self.table.setItem(row, 0, QTableWidgetItem(fname))
        self.table.setItem(row, 1, QTableWidgetItem(str(data.size)))
        self.table.setItem(row, 2, QTableWidgetItem(data.status))
        self.table.setItem(row, 3, QTableWidgetItem(""))
        self.table.setItem(row, 4, QTableWidgetItem(""))
        self.table.setItem(row, 5, QTableWidgetItem(""))
        self.table.setItem(row, 6, QTableWidgetItem(data.description or data.url))

    def update_total_speed(self):
        total_speed = 0
        active_count = 0
        for dlg in self.active_dialogs:
            if hasattr(dlg, "worker") and dlg.worker.is_running:
                try:
                    txt = dlg.card_speed.lbl_value.text()
                    parts = txt.split()
                    val = float(parts[0])
                    unit = parts[1]
                    if "KB" in unit:
                        val *= 1024
                    elif "MB" in unit:
                        val *= 1024 * 1024
                    total_speed += val
                    active_count += 1
                except Exception:
                    pass

        if total_speed < 1024 * 1024:
            s_str = f"{total_speed / 1024:.1f} KB/s"
        else:
            s_str = f"{total_speed / (1024 * 1024):.1f} MB/s"

        self.total_speed_lbl.setText(f"Total Speed: {s_str}")

    def add_url(self):
        # Triggered by toolbar/menu
        text, ok = QInputDialog.getText(self, I18n.get("add_url"), I18n.get("address"))
        if ok and text:
            # Basic validation
            text = text.strip()
            if not re.match(r"^https?://", text):
                text = "https://" + text

            # Validate URL format
            if not re.match(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", text):
                QMessageBox.warning(self, I18n.get("error"), I18n.get("invalid_url"))
                return

            # Use pre-download dialog
            show_pre_dialog = self.config.get("show_pre_download_dialog", True)

            if show_pre_dialog:
                from src.gui.pre_download_dialog import PreDownloadDialog

                pre_dlg = PreDownloadDialog(text, self.config, self.queue_manager, parent=self)
                if pre_dlg.exec() == QDialog.Accepted:
                    values = pre_dlg.get_values()
                    save_dir = values["save_path"]
                    queue_name = values["queue"]
                    if values["dont_ask"]:
                        self.config.set("show_pre_download_dialog", False)
                else:
                    return  # Cancelled
            else:
                save_dir = self.config.get("default_download_dir")
                queue_name = self.config.get("default_queue", "Main download queue")

            # Trigger Analysis Flow
            self.analyze_and_start(text, save_dir, queue_name)

    def handle_browser_download(self, url, filename):
        """
        Handle download from browser (called via signal from HTTP server).
        This runs in UI thread thanks to Qt signal/slot mechanism.
        """
        # Show desktop notification
        if hasattr(self, "tray_icon") and self.tray_icon:
            display_name = filename if filename else url[:50]
            self.tray_icon.showMessage(I18n.get("app_title"), f"📥 {display_name}", QSystemTrayIcon.Information, 2000)

        # Add URL using existing dialog system
        if url and url.strip():
            text = url.strip()

            # Use pre-download dialog if enabled, otherwise auto-add
            if self.config.get("show_pre_download_dialog", True):
                from src.gui.pre_download_dialog import PreDownloadDialog

                pre_dlg = PreDownloadDialog(text, self.config, self.queue_manager, parent=self)
                # Ensure PreDialog is brought to front
                pre_dlg.activateWindow()
                pre_dlg.raise_()

                if pre_dlg.exec() == QDialog.Accepted:
                    values = pre_dlg.get_values()
                    save_dir = values["save_path"]
                    queue_name = values["queue"]
                    if values["dont_ask"]:
                        self.config.set("show_pre_download_dialog", False)
                else:
                    return  # User cancelled
            else:
                # Auto-add without dialog
                save_dir = self.config.get("default_download_dir")
                queue_name = self.config.get("default_queue", "Main download queue")

            # Trigger Analysis Flow
            self.analyze_and_start(text, save_dir, queue_name)

    def cleanup_dialog(self, dlg):
        if dlg in self.active_dialogs:
            self.active_dialogs.remove(dlg)

    # NEW v0.9.0: Final step of download initiation
    def start_download_final(self, url, save_dir, queue_name, format_info=None):
        import os
        from pathlib import Path
        
        # Check for Playlist Mode
        if format_info and format_info.get("is_playlist") and format_info.get("entries"):
            entries = format_info["entries"]
            format_id = format_info.get("format_id", "bestvideo+bestaudio/best")
            ext = format_info.get("ext", "mp4")
            
            print(f"📚 Playlist Download: Starting {len(entries)} videos with format '{format_id}'")
            
            # For playlists, pass the original playlist URL to yt-dlp
            # yt-dlp will handle downloading all videos in the playlist
            # We create a SINGLE download item for the entire playlist
            
            fname = "playlist"  # Generic name, yt-dlp will create proper names
            new_item = DownloadItem(
                url=url, 
                filename=os.path.join(save_dir, fname), 
                save_path=save_dir, 
                queue=queue_name
            )
            new_item.status = f"Downloading playlist ({len(entries)} videos)"
            new_item.size = I18n.get("initializing")
            
            self.downloads.append(new_item)
            self.config.save_history(self.downloads)
            self.refresh_table()
            
            # Start download with playlist URL and format
            # yt-dlp automatically downloads all videos when URL is a playlist
            playlist_format_info = {
                "format_id": format_id,
                "ext": ext,
                "is_playlist": True
            }
            
            try:
                dlg = DownloadDialog(url, self, save_dir=save_dir, format_info=playlist_format_info)
            except Exception as e:
                print(f"❌ FAILED to create DownloadDialog for playlist: {e}")
                import traceback
                traceback.print_exc()
                return
            
            try:
                dlg.download_complete.connect(lambda s, f: self.update_download_status(new_item, s, f))
                dlg.worker.progress_signal.connect(lambda d, t, s, seg: self.update_live_row(new_item, d, t, s))
                dlg.worker.status_signal.connect(lambda m: self.update_item_status(new_item, m))
            except AttributeError as e:
                print(f"⚠️ Worker not ready: {e}")
            
            self.active_dialogs.append(dlg)
            dlg.finished.connect(lambda: self.cleanup_dialog(dlg))
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()
            return  # Exit after handling playlist

        # Standard Single Video Download
        fname = Path(url.split("?")[0]).name or "file.dat"
        # If we have format info, update extension
        if format_info and format_info.get("ext"):
            base = os.path.splitext(fname)[0]
            fname = f"{base}.{format_info['ext']}"

        new_item = DownloadItem(url=url, filename=os.path.join(save_dir, fname), save_path=save_dir, queue=queue_name)
        new_item.status = I18n.get("downloading")
        new_item.size = I18n.get("initializing")

        # Store format info in item (we will need to update DownloadItem model later to support this persistence)
        # For now, pass it to DownloadDialog directly

        self.downloads.append(new_item)
        self.config.save_history(self.downloads)
        self.refresh_table()

        # Start download dialog (worker auto-starts in __init__)
        try:
            dlg = DownloadDialog(url, self, save_dir=save_dir, format_info=format_info)
        except Exception as e:
            print(f"❌ FAILED to create DownloadDialog: {e}")
            import traceback

            traceback.print_exc()
            return

        # Connect signals AFTER dialog is fully initialized
        # CRITICAL: These must be connected after DownloadDialog.__init__ completes
        # to avoid SIGSEGV from accessing worker before it's ready
        try:
            dlg.download_complete.connect(lambda s, f: self.update_download_status(new_item, s, f))
            dlg.worker.progress_signal.connect(lambda d, t, s, seg: self.update_live_row(new_item, d, t, s))
            dlg.worker.status_signal.connect(lambda m: self.update_item_status(new_item, m))
        except AttributeError as e:
            print(f"⚠️ Worker not ready: {e}")

        self.active_dialogs.append(dlg)
        dlg.finished.connect(lambda: self.cleanup_dialog(dlg))
        dlg.show()
        dlg.raise_()  # Bring to front
        dlg.activateWindow()  # Give focus

    # NEW v0.9.0: Analysis Flow
    def analyze_and_start(self, url, save_dir, queue_name):
        # Interactive mode check (default True for now)
        interactive = self.config.get("interactive_mode", True)

        if not interactive:
            self.start_download_final(url, save_dir, queue_name)
            return

        # Try analysis with yt-dlp (supports 1300+ sites)
        # If it fails or URL isn't supported, fallback to direct download
        print("🔍 Attempting analysis with yt-dlp...")

        # Show non-blocking status message
        self.statusBar().showMessage("🔍 Analyzing formats...", 30000)

        worker = AnalysisWorker(url, self.config.get_proxy_config())

        # Define callback
        def on_analysis_finished(info):
            self.statusBar().clearMessage()

            if not info:
                print("⚠️ No info, falling back to direct download")
                self.start_download_final(url, save_dir, queue_name)
                return

            # Check if playlist detected
            playlist_title = info.get('playlist_title')
            playlist_count = info.get('playlist_count')
            
            # Fallback for Mix playlists (where --no-playlist hides count)
            is_playlist_url = 'list=' in url or 'playlist' in url
            potential_playlist = is_playlist_url and not playlist_count
            
            print(f"🔍 Playlist Check: Title='{playlist_title}', Count={playlist_count}, DetectPattern={is_playlist_url}")
            
            if (playlist_title and playlist_count and playlist_count > 1) or potential_playlist:
                print("🎵 Playlist detected in MainWindow! Showing dialog...")
                # Playlist detected! Ask user what they want
                from src.gui.playlist_choice_dialog import PlaylistChoiceDialog
                
                # If falling back, use a generic title
                display_title = playlist_title if playlist_title else "Detected Playlist"
                display_count = playlist_count if playlist_count else None
                
                choice_dlg = PlaylistChoiceDialog(display_title, display_count, self)
                choice_dlg.exec()
                choice = choice_dlg.get_choice()
                print(f"👤 User choice: {choice}")
                
                if choice == "playlist":
                    # User wants full playlist - re-analyze without --no-playlist
                    self.analyze_full_playlist(url, save_dir, queue_name)
                    return
                elif choice is None:
                    # User cancelled
                    return
                # else: choice == "single", continue with current info
            
            # Show Quality Dialog (single video or user chose single from playlist)
            q_dlg = QualityDialogV2(self, info)

            # Handle selection
            def on_selected(fmt_info):
                self.start_download_final(url, save_dir, queue_name, fmt_info)
                print("📥 start_download_final completed")

            q_dlg.quality_selected.connect(on_selected)
            q_dlg.exec()

        def on_analysis_error(error_msg):
            """Handle errors from AnalysisWorker"""
            print(f"❌ on_analysis_error called: {error_msg}")
            self.statusBar().clearMessage()
            self.statusBar().showMessage("⚠️ Analysis failed, using direct download", 5000)
            self.start_download_final(url, save_dir, queue_name)

        # Keep ref BEFORE starting worker (prevent GC)
        self._analysis_worker = worker

        # Use Qt.QueuedConnection for thread-safe signal handling
        from PySide6.QtCore import Qt

        worker.finished.connect(on_analysis_finished, Qt.QueuedConnection)
        worker.error.connect(on_analysis_error, Qt.QueuedConnection)

        print("🔗 Signals connected with QueuedConnection")
        worker.start()
        print("🚀 Worker started, waiting for callbacks...")
    
    def analyze_full_playlist(self, url, save_dir, queue_name):
        """Re-analyze URL without --no-playlist flag for full playlist."""
        from PySide6.QtWidgets import QProgressDialog
        from PySide6.QtCore import Qt
        
        # Show loading dialog
        from src.core.i18n import I18n
        progress = QProgressDialog(I18n.get("analyzing_playlist"), "Cancel", 0, 0, self)
        progress.setWindowTitle(I18n.get("playlist_analysis"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        # Create worker WITHOUT --no-playlist flag
        worker = AnalysisWorker(url, self.config.get_proxy_config(), no_playlist=False)
        
        def on_playlist_finished(info):
            progress.close()
            
            if not info:
                QMessageBox.warning(self, I18n.get("error"), I18n.get("failed_analyze_playlist"))
                return
            
            # Show Quality Dialog with full playlist
            q_dlg = QualityDialogV2(self, info)
            
            def on_selected(fmt_info):
                self.start_download_final(url, save_dir, queue_name, fmt_info)
                print("📥 start_download_final completed (playlist)")
            
            q_dlg.quality_selected.connect(on_selected)
            q_dlg.exec()
        
        def on_playlist_error(error_msg):
            progress.close()
            QMessageBox.warning(self, I18n.get("error"), I18n.get("playlist_analysis_failed") + f": {error_msg}")
        
        # Check if cancelled
        progress.canceled.connect(lambda: worker.terminate())
        
        # Connect signals
        worker.finished.connect(on_playlist_finished, Qt.QueuedConnection)
        worker.error.connect(on_playlist_error, Qt.QueuedConnection)
        
        # Keep reference
        self._playlist_worker = worker
        worker.start()

    # Copying remaining methods to ensure file completeness
    def open_settings(self, tab_index=0):
        dlg = SettingsDialog(self, initial_tab=tab_index)
        if dlg.exec():
            self.apply_theme()  # Re-apply theme on save

    def open_queue_manager(self):
        # Quick actions
        queues = self.config.get("queues", ["Main Queue"])

        choices = [
            I18n.get("start_queue"),
            I18n.get("stop_queue"),
            I18n.get("create_new_queue"),
            I18n.get("delete_queue"),
        ]
        item, ok = QInputDialog.getItem(self, I18n.get("scheduler"), I18n.get("select_action"), choices, 0, False)
        if not ok or not item:
            return

        if item == "Create New Queue":
            text, ok = QInputDialog.getText(self, "New Queue", "Queue Name:")
            if ok and text and text not in queues:
                queues.append(text)
                self.config.set("queues", queues)

        elif item == "Delete Queue":
            q, ok = QInputDialog.getItem(self, "Delete Queue", "Select Queue:", queues, 0, False)
            if ok and q:
                if q == "Main Queue":
                    QMessageBox.warning(self, I18n.get("error"), I18n.get("cannot_delete_main_queue"))
                else:
                    queues.remove(q)
                    self.config.set("queues", queues)

        elif item == "Start Queue...":
            q, ok = QInputDialog.getItem(self, "Start Queue", "Select Queue:", queues, 0, False)
            if ok and q:
                self.queue_manager.start_queue(q, self.start_download_item_func)
                QMessageBox.information(self, "Started", f"Queue '{q}' started.")

        elif item == "Stop Queue":
            q, ok = QInputDialog.getItem(
                self, "Stop Queue", "Select Queue:", list(self.queue_manager.active_queues), 0, False
            )
            if ok and q:
                self.queue_manager.stop_queue(q)
                QMessageBox.information(self, "Stopped", f"Queue '{q}' stopped.")

    # Context menus, etc...
    def show_sidebar_menu(self, pos):
        item = self.sidebar.itemAt(pos)
        menu = QMenu(self)
        add_act = QAction(self.get_std_icon("add"), "Add Category", self)
        add_act.triggered.connect(self.add_category_action)
        menu.addAction(add_act)

        if item:
            text = item.text(0)
            # Protect system categories
            # User might have renamed them in Config? No, we use standard keys in sidebar setup.

            # Actually, if user wants to delete standard ones (Video/Music etc),
            # we might need to allow it if they are in 'categories' dict.
            # In setup_sidebar, we read 'categories' dict.
            # 'Videos', 'Music' etc ARE in that dict by default.
            # So we should match against keys in self.config.get("categories").

            # Items we definitely CANNOT delete: All, Unfinished, Finished, Others (hardcoded in setup)
            protected = [I18n.get("all_downloads"), I18n.get("unfinished"), I18n.get("finished"), I18n.get("others")]

            if text not in protected:
                menu.addSeparator()
                prop_act = QAction(self.get_std_icon("settings"), "Properties", self)
                prop_act.triggered.connect(lambda: self.edit_category_action(item))
                menu.addAction(prop_act)

                del_act = QAction(self.get_std_icon("delete"), "Delete Category", self)
                del_act.triggered.connect(lambda: self.delete_category_action(item))
                menu.addAction(del_act)

        menu.exec(QCursor.pos())

    def delete_category_action(self, item):
        data = item.data(0, Qt.UserRole)
        # Convert list to tuple if needed (PySide behavior)
        if isinstance(data, list):
            data = tuple(data)

        if isinstance(data, tuple) and len(data) == 2:
            ftype, key = data
            if ftype == "cat":
                res = QMessageBox.question(
                    self, "Delete", f"Delete category '{key}'?", QMessageBox.Yes | QMessageBox.No
                )
                if res == QMessageBox.Yes:
                    cats = self.config.get("categories", {})
                    if key in cats:
                        del cats[key]
                        self.config.set("categories", cats)
                        self.setup_sidebar()
                        self.refresh_table()

    def open_properties_dialog(self, item=None):
        if isinstance(item, QTableWidgetItem):
            row = item.row()
        else:
            rows = self.table.selectionModel().selectedRows()
            if not rows:
                return
            row = rows[0].row()

        data = self.downloads[row]
        dlg = PropertiesDialog(data, self)
        dlg.exec()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        # Standard Actions
        open_act = QAction(self.get_std_icon("play"), "Open", self)
        open_act.triggered.connect(self.open_file_action)
        menu.addAction(open_act)

        folder_act = QAction(self.get_std_icon("folder"), "Show in Folder", self)
        folder_act.triggered.connect(self.open_folder_action)
        menu.addAction(folder_act)

        menu.addSeparator()

        resume_act = QAction(self.get_std_icon("play"), "Resume", self)
        resume_act.triggered.connect(self.resume_download)
        menu.addAction(resume_act)

        stop_act = QAction(self.get_std_icon("stop"), "Stop", self)
        stop_act.triggered.connect(self.stop_download)
        menu.addAction(stop_act)

        menu.addSeparator()

        prop_act = QAction(self.get_std_icon("settings"), "Properties", self)
        prop_act.triggered.connect(lambda: self.open_properties_dialog(item))
        menu.addAction(prop_act)

        menu.addSeparator()

        # Move to Queue submenu
        queue_menu = menu.addMenu("Move to Queue")
        for queue_name in self.queue_manager.get_queues():
            q_act = QAction(queue_name, self)
            q_act.triggered.connect(lambda checked, q=queue_name: self.move_to_queue(q))
            queue_menu.addAction(q_act)

        menu.addSeparator()

        del_act = QAction(self.get_std_icon("delete"), I18n.get("delete"), self)
        del_act.triggered.connect(self.delete_download)
        menu.addAction(del_act)

        menu.exec(QCursor.pos())

    def open_folder_action(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            path = str(Path(data.filename).parent)
            if os.path.exists(path):
                try:
                    subprocess.Popen(["xdg-open", path])
                except Exception:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def add_to_queue_action(self, queue_name):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            self.queue_manager.add_to_queue(queue_name, data)
            QMessageBox.information(self, "Queue", f"Added to {queue_name}")

    def filter_by_category(self, item, col):
        data = item.data(0, Qt.UserRole)
        if isinstance(data, list):
            data = tuple(data)

        if isinstance(data, tuple) and len(data) >= 2:
            ftype, key = data[0], data[1]  # Robust unpacking
            if ftype == "all":
                self.refresh_table("all")
            elif ftype == "unfinished":
                self.refresh_table("unfinished")
            elif ftype == "finished":
                self.refresh_table("finished")
            elif ftype == "others":
                self.refresh_table("others")
            elif ftype == "cat":
                cats = self.config.get("categories", {})
                val = cats.get(key)
                if val and len(val) >= 1:
                    self.refresh_table(val[0])
        elif isinstance(data, str):
            self.refresh_table(data)

    def delete_all_action(self):
        res = QMessageBox.question(self, "Delete All", "Clear history?", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.downloads.clear()
            self.config.save_history(self.downloads)
            self.refresh_table()

    def open_file_action(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            path = data.filename
            url = QUrl.fromLocalFile(path)
            QDesktopServices.openUrl(url)

    def delete_download(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        data = self.downloads[row]

        # New: Ask confirmation with checkbox
        from PySide6.QtWidgets import QCheckBox

        msg = QMessageBox(self)
        msg.setWindowTitle(I18n.get("delete"))
        msg.setText(f"Delete '{os.path.basename(data.filename)}'?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setIcon(QMessageBox.Question)

        cb = QCheckBox("Delete file from disk permanently")
        msg.setCheckBox(cb)

        if msg.exec() == QMessageBox.Yes:
            # Stop if running
            for dlg in list(self.active_dialogs):
                if dlg.url == data.url:
                    dlg.close()
                    if dlg in self.active_dialogs:
                        self.active_dialogs.remove(dlg)
                    break

            if cb.isChecked():
                # Delete Main
                if os.path.exists(data.filename):
                    try:
                        os.remove(data.filename)
                    except Exception:
                        pass
                # Delete Part
                part_file = data.filename + ".part"
                if os.path.exists(part_file):
                    try:
                        os.remove(part_file)
                    except Exception:
                        pass
                # Delete Progress (Hash based)
                try:
                    h = hashlib.md5(data.url.encode()).hexdigest()
                    prog_file = os.path.join(os.path.dirname(data.filename), h + ".progress")
                    if os.path.exists(prog_file):
                        os.remove(prog_file)
                except Exception:
                    pass

            del self.downloads[row]
            self.config.save_history(self.downloads)
            self.refresh_table()

    def resume_download(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        data = self.downloads[rows[0].row()]

        # Check if already running
        for dlg in self.active_dialogs:
            if dlg.url == data.url:
                dlg.show()
                dlg.activateWindow()
                if not dlg.worker.is_running:
                    dlg.toggle_pause()  # Restart if was paused/stopped
                return

        # Start new
        self.start_download_item_func(data)

    def stop_all_downloads(self):
        for dlg in list(self.active_dialogs):
            if dlg.worker.is_running:
                dlg.toggle_pause()
                # Update status
                for item in self.downloads:
                    if item.url == dlg.url:
                        item.status = "Stopped"
        self.refresh_table()

    def stop_download(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        data = self.downloads[rows[0].row()]

        found = False
        for dlg in self.active_dialogs:
            if dlg.url == data.url:
                if dlg.worker.is_running:
                    dlg.toggle_pause()
                    data.status = "Stopped"
                found = True
                break

        if not found:
            data.status = "Stopped"

        self.refresh_table()

        # If not open, maybe just update status?
        if data.status == "Downloading...":
            data.status = "Stopped"
            self.config.save_history(self.downloads)
            self.refresh_table()

    def handle_double_click(self, item):
        # Double click opens dialog (resume/view)
        # item is TableItem, need row
        row = item.row()
        data = self.downloads[row]

        if data.status == I18n.get("complete") or data.status == "Complete":
            self.open_file_action()
        else:
            self.resume_download()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(getattr(self, "app_icon", self.get_std_icon("app")))

        tray_menu = QMenu()
        show_act = QAction("Show MERGEN", self)
        show_act.triggered.connect(self.show)
        tray_menu.addAction(show_act)

        quit_act = QAction("Exit", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_act)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def show_about_dialog(self):
        """Show About dialog with app information."""
        from PySide6.QtWidgets import QMessageBox

        about_text = """
        <h2>MERGEN</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Multi-threaded Download Manager</b></p>
        <br>
        <p>Built with PySide6 & Python</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle(I18n.get("about"))
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
