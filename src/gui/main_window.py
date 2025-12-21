# -*- coding: utf-8 -*-
import sys
import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QToolBar, QTreeWidget, QTreeWidgetItem, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QInputDialog, QMessageBox,
                               QSplitter, QMenu, QApplication, QStyle)
from PySide6.QtGui import QAction, QIcon, QCursor, QColor, QBrush, QDesktopServices
from PySide6.QtCore import Qt, QSize, QUrl
import os, re
import subprocess
from src.gui.download_dialog import DownloadDialog
from src.gui.settings_dialog import SettingsDialog
from src.core.queue_manager import QueueManager

from src.core.config import ConfigManager
from src.core.queue_manager import QueueManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyDownload Manager")
        self.resize(1000, 600)
        
        self.config = ConfigManager()
        self.queue_manager = QueueManager() # Init singleton
        
        # Load Geometry
        geom = self.config.get("geometry")
        if geom:
            try:
                self.restoreGeometry(bytes.fromhex(geom))
            except: pass
            
        self.downloads = self.config.get_history()
        self.active_dialogs = [] # Track open download dialogs
        
        # UI Setup
        self.setup_ui()
        self.apply_theme()
        # Refresh table with loaded history
        self.refresh_table()

    def closeEvent(self, event):
        # Save Geometry
        self.config.set("geometry", self.saveGeometry().toHex().data().decode())
        # Save History
        self.config.save_history(self.downloads)
        super().closeEvent(event)

    def apply_theme(self):
        theme = self.config.get("theme", "dark").lower()
        
        if theme == "light":
            # LIGHT THEME
            self.setStyleSheet("""
                QMainWindow { background-color: #f0f0f0; color: #333333; }
                QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }
                QToolBar { background-color: #e0e0e0; border-bottom: 2px solid #007acc; spacing: 15px; padding: 8px; }
                QToolButton { color: #333333; border: 1px solid transparent; border-radius: 4px; padding: 6px; }
                QToolButton:hover { background-color: #d0d0d0; border: 1px solid #bbbbbb; }
                QToolButton:pressed { background-color: #007acc; color: white; }
                
                QTreeWidget { background-color: #ffffff; color: #333333; border: 1px solid #cccccc; }
                QTreeWidget::item { height: 28px; }
                QTreeWidget::item:selected { background-color: #007acc; color: white; }
                
                QTableWidget { background-color: #ffffff; gridline-color: #dddddd; border: 1px solid #cccccc; color: #333333; selection-background-color: #007acc; selection-color: white; }
                QHeaderView::section { background-color: #e0e0e0; padding: 6px; border: none; border-right: 1px solid #cccccc; border-bottom: 1px solid #cccccc; color: #333333; font-weight: bold; }
                
                QSplitter::handle { background-color: #cccccc; }
                QMenu { background-color: #ffffff; color: #333333; border: 1px solid #cccccc; }
                QMenu::item:selected { background-color: #007acc; color: white; }
                QMenu::separator { background: #cccccc; height: 1px; margin: 4px; }
            """)
        else:
            # DARK THEME (Default)
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #e0e0e0; }
                QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; }
                QToolBar { background-color: #333333; border-bottom: 2px solid #007acc; spacing: 15px; padding: 8px; }
                QToolButton { background-color: transparent; border: 1px solid transparent; border-radius: 4px; color: #e0e0e0; padding: 6px; font-weight: 500; }
                QToolButton:hover { background-color: #454545; border: 1px solid #666666; }
                QToolButton:pressed { background-color: #007acc; color: white; }
                
                QTreeWidget { background-color: #333333; color: #dddddd; border: none; font-size: 13px; outline: 0; }
                QTreeWidget::item { height: 28px; }
                QTreeWidget::item:selected { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #005a9e); color: white; border: none; }
                
                QTableWidget { background-color: #2b2b2b; gridline-color: #3a3a3a; border: none; color: #e0e0e0; selection-background-color: #005a9e; selection-color: white; }
                QHeaderView::section { background-color: #333333; padding: 6px; border: none; border-right: 1px solid #444444; border-bottom: 1px solid #444444; color: #cccccc; font-weight: bold; }
                
                QSplitter::handle { background-color: #2b2b2b; }
                QSplitter::handle:hover { background-color: #007acc; }
                
                QMenu { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #444444; }
                QMenu::item { padding: 6px 24px; }
                QMenu::item:selected { background-color: #007acc; color: white; }
                QMenu::separator { background: #444444; height: 1px; margin: 4px; }
            """)

    def setup_ui(self):
        # Central Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Menu Bar
        self.create_menubar()

        # Toolbar
        self.toolbar_ref = self.create_toolbar()

        # Splitter Layout (Sidebar | Table)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(8) 
        main_layout.addWidget(self.splitter)

        # Sidebar (Categories)
        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderLabel("Categories")
        self.sidebar.setMinimumWidth(220)
        self.sidebar.setMaximumWidth(300)
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        self.sidebar.setContextMenuPolicy(Qt.CustomContextMenu) 
        self.sidebar.customContextMenuRequested.connect(self.show_sidebar_menu)
        self.sidebar.setRootIsDecorated(False) # FIX: Remove expander boxes for cleaner look
        
        self.setup_sidebar()
        self.sidebar.itemClicked.connect(self.filter_by_category)
        self.splitter.addWidget(self.sidebar)

        # Downloads Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "File Name", "Size", "Status", "Time Left", 
            "Transfer Rate", "Last Try", "Description"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False) 
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemDoubleClicked.connect(self.handle_double_click)
        self.table.verticalHeader().setVisible(False) 
        self.table.setSortingEnabled(True) # FIX: Enable Sorting
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch) 
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        self.splitter.addWidget(self.table)
        
        # State
        if not hasattr(self, 'downloads'):
             self.downloads = []

    def get_std_icon(self, name):
        """Helper to get standard system icons."""
        style = QApplication.style()
        if name == "folder": return style.standardIcon(QStyle.SP_DirIcon)
        if name == "file": return style.standardIcon(QStyle.SP_FileIcon)
        if name == "stop": return style.standardIcon(QStyle.SP_MediaStop)
        if name == "play": return style.standardIcon(QStyle.SP_MediaPlay)
        if name == "pause": return style.standardIcon(QStyle.SP_MediaPause)
        if name == "delete": return style.standardIcon(QStyle.SP_TrashIcon)
        if name == "add": return style.standardIcon(QStyle.SP_FileDialogNewFolder) # Close enough
        if name == "settings": return style.standardIcon(QStyle.SP_ComputerIcon) # Placeholder
        if name == "video": return style.standardIcon(QStyle.SP_MediaVolume)
        if name == "music": return style.standardIcon(QStyle.SP_MediaVolume) 
        if name == "doc": return style.standardIcon(QStyle.SP_FileIcon)
        if name == "app": return style.standardIcon(QStyle.SP_DesktopIcon)
        if name == "zip": return style.standardIcon(QStyle.SP_DriveFDIcon)
        if name == "success": return style.standardIcon(QStyle.SP_DialogApplyButton)
        if name == "error": return style.standardIcon(QStyle.SP_MessageBoxCritical)
        if name == "link": return style.standardIcon(QStyle.SP_DirLinkIcon)
        if name == "sched": return style.standardIcon(QStyle.SP_FileDialogDetailedView) 
        
        return style.standardIcon(QStyle.SP_FileIcon)

    def create_menubar(self):
        menubar = self.menuBar()
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        toggle_toolbar_act = QAction("Show Toolbar", self, checkable=True)
        toggle_toolbar_act.setChecked(True)
        toggle_toolbar_act.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(toggle_toolbar_act)
        
        # Help/Debug
        # (Optional)

    def toggle_toolbar(self, checked):
        if hasattr(self, 'toolbar_ref'):
            self.toolbar_ref.setVisible(checked)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        actions = [
            ("Add URL", self.get_std_icon("add"), self.add_url),
            ("Resume", self.get_std_icon("play"), self.resume_download),
            ("Stop", self.get_std_icon("pause"), self.stop_download), # Use 'pause' icon for stop/pause visual
            ("Stop All", self.get_std_icon("stop"), self.stop_all_downloads),
            ("Delete", self.get_std_icon("delete"), self.delete_download),
            (None, None, None), # Separator
            ("Options", self.get_std_icon("settings"), self.open_settings),
            ("Queues", self.get_std_icon("sched"), self.open_queue_manager)
        ]

        for item in actions:
            if item[0] is None:
                toolbar.addSeparator()
                continue
            name, icon, slot = item
            act = QAction(icon, name, self)
            if slot: act.triggered.connect(slot)
            toolbar.addAction(act)
            
        # Add Delete All Action (Manual addition to Toolbar)
        toolbar.addSeparator()
        del_all_act = QAction(self.get_std_icon("trash"), "Delete All", self)
        del_all_act.setToolTip("Clear Download History")
        del_all_act.triggered.connect(self.delete_all_action)
        toolbar.addAction(del_all_act)
        
        return toolbar

    def open_queue_manager(self):
         # Highlight/Focus Queues in Sidebar
         # Or show a message if we don't have a dedicated dialog yet
         QMessageBox.information(self, "Queue Manager", "Manage queues via the Sidebar context menu (Right-click 'Queues').")

    def delete_all_action(self):
        res = QMessageBox.question(self, "Delete All", 
                                   "Are you sure you want to delete all download history? Downloaded files will NOT be deleted from disk.", 
                                   QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.downloads.clear()
            self.config.save_history(self.downloads)
            self.refresh_table()

    def setup_sidebar(self):
        self.sidebar.clear()
        
        # Helper to create items
        def add_item(parent, title, icon_name, user_data):
            # Styling spacer using whitespace if needed or stylesheet padding
            item = QTreeWidgetItem(parent, [title]) 
            item.setIcon(0, self.get_std_icon(icon_name))
            item.setData(0, Qt.UserRole, user_data)
            return item

        root = add_item(self.sidebar, "All Downloads", "link", "all")
        root.setExpanded(True)

        # Load from Config
        categories = self.config.get("categories", {})
        
        for cat, val in categories.items():
            # Handle legacy vs new structure safely
            if len(val) == 3:
                exts, icon, _ = val
            elif len(val) == 2:
                exts, icon = val
            else:
                continue # Skip invalid
                
            add_item(root, cat, icon, exts)

        add_item(self.sidebar, "Unfinished", "pause", "unfinished")
        add_item(self.sidebar, "Finished", "success", "finished")

    def show_sidebar_menu(self, pos):
        item = self.sidebar.itemAt(pos)
        menu = QMenu(self)
        
        # Actions
        add_act = QAction(self.get_std_icon("add"), "Add Category", self)
        add_act.triggered.connect(self.add_category_action)
        menu.addAction(add_act)
        
        if item:
            data = item.data(0, Qt.UserRole)
            # Helper: Valid categories are lists (exts) or tuples (exts, icon, path)
            # Default ones are tuples in config now.
            
            # Allow properties for ALL categories except "All Downloads", "Unfinished", "Finished"
            if item.text(0) not in ["All Downloads", "Unfinished", "Finished"]:
                menu.addSeparator()
                prop_act = QAction(self.get_std_icon("settings"), "Properties", self)
                prop_act.triggered.connect(lambda: self.edit_category_action(item))
                menu.addAction(prop_act)
                
                # Only allow deleting NON-DEFAULT categories? 
                # For now allow deleting all to be flexible, or restrict. 
                # Let's restrict deleting default ones if preferred, but user requested editing.
                if item.text(0) not in ["Compressed", "Documents", "Music", "Programs", "Video"]:
                     del_act = QAction(self.get_std_icon("delete"), "Delete Category", self)
                     del_act.triggered.connect(lambda: self.delete_category_action(item))
                     menu.addAction(del_act)

        menu.exec(QCursor.pos())

    def add_category_action(self):
        from src.gui.category_dialog import CategoryDialog
        dlg = CategoryDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            name = data["name"]
            if not name: return
            
            cats = self.config.get("categories", {})
            # Store as (exts, icon_path/name, save_path)
            cats[name] = (data["exts"], data["icon"], data["path"])
            self.config.set("categories", cats)
            self.setup_sidebar()

    def edit_category_action(self, item):
        from src.gui.category_dialog import CategoryDialog
        name = item.text(0)
        cats = self.config.get("categories", {})
        if name not in cats: return
        
        # Handle 2-element tuple legacy (exts, icon) vs 3-element (exts, icon, path)
        val = cats[name]
        if len(val) == 2:
             exts, icon = val
             path = ""
        else:
             exts, icon, path = val
             
        ext_str = ", ".join(exts)
        
        dlg = CategoryDialog(self, name, ext_str, icon, path)
        if dlg.exec():
            new_data = dlg.get_data()
            # If name changed, delete old (only if not a default category rename - technically new cat)
            if new_data["name"] != name:
                del cats[name]
            
            cats[new_data["name"]] = (new_data["exts"], new_data["icon"], new_data["path"])
            self.config.set("categories", cats)
            self.setup_sidebar()

    def delete_category_action(self, item):
        name = item.text(0)
        res = QMessageBox.question(self, "Delete", f"Delete category '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            cats = self.config.get("categories", {})
            if name in cats:
                del cats[name]
                self.config.set("categories", cats)
                self.setup_sidebar()

    def get_file_icon(self, filename_or_icon):
        # 1. Check if it's a known file extension logic
        if "." in str(filename_or_icon):
            ext = Path(filename_or_icon).suffix.lstrip(".").lower()
            cats = self.config.get("categories", {})
            for name, val in cats.items():
                # Handle legacy vs new
                cat_exts = val[0]
                cat_icon = val[1]
                
                if ext in cat_exts:
                    # Found category, resolve its icon
                    return self.get_file_icon(cat_icon) # Recursive resolve of icon name/path
            
            # Fallback for file
            return self.get_std_icon("file")
            
        # 2. It's an icon name or path
        # Check custom path
        icon_str = str(filename_or_icon)
        if os.path.exists(icon_str):
            return QIcon(icon_str)
            
        # Standard icon fallback
        return self.get_std_icon(icon_str)

    def add_url(self):
        text, ok = QInputDialog.getText(self, "Enter URL", "Address:")
        if ok and text:
            text = text.strip()
            # 1. Validate URL
            if not re.match(r'^https?://', text):
                QMessageBox.warning(self, "Invalid URL", "Please enter a valid HTTP or HTTPS URL starting with 'http://' or 'https://'.")
                return

            # Check for duplicate URL
            for d in self.downloads:
                if d.url == text:
                    res = QMessageBox.warning(self, "Duplicate", 
                                              "This URL is already in the list. Download again?", 
                                              QMessageBox.Yes | QMessageBox.No)
                    if res == QMessageBox.No:
                        return
                    else:
                        break # Stop checking, user allowed it

            fname = Path(text.split("?")[0]).name or "file.dat"
            
            # Determine Save Directory
            save_dir = self.config.get("default_download_dir")
            cats = self.config.get("categories", {})
            ext = Path(fname).suffix.lstrip(".").lower()
            
            for name, val in cats.items():
                if len(val) == 3:
                     cexts, _, cpath = val
                else: 
                     cexts, _, = val
                     cpath = ""
                     
                if ext in cexts and cpath and os.path.exists(cpath):
                    save_dir = cpath
                    break
            
            from src.core.models import DownloadItem
            new_item = DownloadItem(url=text, filename=os.path.join(save_dir, fname), save_path=save_dir)
            new_item.status = "Downloading..."
            new_item.size = "Calculating..."
            
            self.downloads.append(new_item)
            self.config.save_history(self.downloads)
            self.refresh_table()

            dlg = DownloadDialog(text, self, save_dir=save_dir)
            dlg.download_complete.connect(lambda s, f: self.update_download_status(new_item, s, f))
            # Track dialog
            self.active_dialogs.append(dlg)
            dlg.finished.connect(lambda: self.cleanup_dialog(dlg))
            dlg.show()

    def cleanup_dialog(self, dlg):
        if dlg in self.active_dialogs:
            # Mark status as stopped if closed before finish? 
            # Ideally logic should be: if manual close -> Stopped.
            # But dlg.finished fires always.
            self.active_dialogs.remove(dlg)

    
    def update_download_status(self, download_item, success, filename):
        download_item.status = "Complete" if success else "Failed"
        if success:
            download_item.filename = filename 
            download_item.size = "Done" 
            
        self.config.save_history(self.downloads)
        self.refresh_table()

    def handle_double_click(self, item):
        row = item.row()
        if row < len(self.downloads):
            data = self.downloads[row]
            # Open Properties Dialog
            from src.gui.properties_dialog import PropertiesDialog
            dlg = PropertiesDialog(self, data)
            if dlg.exec():
                self.config.save_history(self.downloads)
                self.refresh_table()

    def refresh_table(self, filter_data=None):
        self.table.setRowCount(0)
        
        # Determine filters
        filter_status = None
        filter_queue = None
        filter_exts = None
        
        if filter_data == "unfinished": filter_status = ["Downloading...", "Failed"] 
        elif filter_data == "finished": filter_status = ["Complete"]
        elif isinstance(filter_data, str) and filter_data.startswith("queue:"):
            filter_queue = filter_data.split(":", 1)[1]
        elif isinstance(filter_data, list):
            filter_exts = filter_data
            
        for d in self.downloads:
            # Filter Logic
            if filter_status:
                if d.status not in filter_status: continue
            if filter_queue:
                 if d.queue != filter_queue: continue
            if filter_exts:
                ext = Path(d.filename).suffix.lstrip(".").lower()
                if ext not in filter_exts: continue
            
            self.add_table_row(d)

    def filter_by_category(self, item, col):
        data = item.data(0, Qt.UserRole)
        self.refresh_table(data)

    def create_queue_action(self):
        text, ok = QInputDialog.getText(self, "Create Queue", "Queue Name:")
        if ok and text:
            # Add to config
            queues = self.config.get("queues", ["Main Queue"])
            if text not in queues:
                queues.append(text)
                self.config.set("queues", queues)
                self.setup_sidebar()

    def delete_queue_action(self, q_name):
        res = QMessageBox.question(self, "Delete Queue", f"Delete queue '{q_name}'? Downloads will remain in history.", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            queues = self.config.get("queues", ["Main Queue"])
            if q_name in queues:
                queues.remove(q_name)
                self.config.set("queues", queues)
                self.setup_sidebar()

    def add_table_row(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        fname = os.path.basename(data.filename)
        self.table.setItem(row, 0, QTableWidgetItem(fname))
        self.table.setItem(row, 1, QTableWidgetItem(str(data.size)))
        self.table.setItem(row, 2, QTableWidgetItem(data.status))
        self.table.setItem(row, 3, QTableWidgetItem("")) # Time left
        self.table.setItem(row, 4, QTableWidgetItem("")) # Speed
        self.table.setItem(row, 5, QTableWidgetItem("")) # Last try
        self.table.setItem(row, 6, QTableWidgetItem(data.description or data.url))

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        
        open_act = QAction(self.get_std_icon("play"), "Open", self)
        open_with_act = QAction(self.get_std_icon("app"), "Open With...", self)
        open_folder_act = QAction(self.get_std_icon("folder"), "Open Folder", self)
        prop_act = QAction(self.get_std_icon("settings"), "Properties", self) # NEW
        delete_act = QAction(self.get_std_icon("delete"), "Delete", self)
        
        open_act.triggered.connect(self.open_file_action)
        open_with_act.triggered.connect(self.open_with_action)
        open_folder_act.triggered.connect(self.open_folder_action)
        prop_act.triggered.connect(lambda: self.handle_double_click(self.table.currentItem()))
        delete_act.triggered.connect(self.delete_download)
        
        menu.addAction(open_act)
        menu.addAction(open_with_act)
        menu.addAction(open_folder_act)
        menu.addSeparator()
        menu.addAction(prop_act)
        
        # Add to Queue Submenu
        q_menu = menu.addMenu(self.get_std_icon("sched"), "Add to Queue")
        queues = self.config.get("queues", ["Main Queue"])
        for q in queues:
            act = QAction(q, self)
            act.triggered.connect(lambda checked=False, q=q: self.add_to_queue_action(q))
            q_menu.addAction(act)
            
        menu.addSeparator()
        menu.addAction(delete_act)
        
        menu.exec(QCursor.pos())
        
    def add_to_queue_action(self, queue_name):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            data.queue = queue_name
            self.config.save_history(self.downloads)
            QMessageBox.information(self, "Queue", f"Added to {queue_name}")

    def open_with_action(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            path = data.filename
            if os.path.exists(path):
                try:
                    subprocess.Popen(['kopenwith', path])
                except FileNotFoundError:
                     QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_file_action(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            if data.status == "Complete":
                self.open_file_system(data.filename)
            else:
                QMessageBox.warning(self, "Wait", "File is not ready yet.")

    def open_folder_action(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            data = self.downloads[rows[0].row()]
            path = Path(data.filename).resolve().parent
            self.open_file_system(str(path), is_folder=True)

    def open_file_system(self, path, is_folder=False):
        # Cross-platform opener with QDesktopServices
        url = QUrl.fromLocalFile(path)
        if not QDesktopServices.openUrl(url):
             QMessageBox.critical(self, "Error", f"Could not open: {path}")

    # Slots
    def resume_download(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        data = self.downloads[rows[0].row()]
        
        # If already downloading (in active list), bring to front
        for dlg in self.active_dialogs:
            if dlg.url == data.url: 
                dlg.raise_()
                dlg.activateWindow()
                return

        if data.status == "Complete":
             res = QMessageBox.question(self, "Redownload", "File is complete. Redownload?", QMessageBox.Yes | QMessageBox.No)
             if res == QMessageBox.No: return
        
        save_dir = data.save_path or self.config.get("default_download_dir")
        
        dlg = DownloadDialog(data.url, self, save_dir=save_dir)
        dlg.download_complete.connect(lambda s, f: self.update_download_status(data, s, f))
        
        self.active_dialogs.append(dlg)
        dlg.finished.connect(lambda: self.cleanup_dialog(dlg))
        
        dlg.show()
        data.status = "Downloading..."
        self.config.save_history(self.downloads)
        self.refresh_table()

    def stop_download(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        data = self.downloads[rows[0].row()]
        
        # Find active dialog
        for dlg in self.active_dialogs:
            if dlg.url == data.url:
                dlg.close() # This will trigger cleanup
                
        # Update status
        data.status = "Stopped"
        self.config.save_history(self.downloads)
        self.refresh_table()

    def stop_all_downloads(self):
        # iterate copy
        for dlg in self.active_dialogs[:]:
            dlg.close()

    def delete_download(self): 
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        
        row = rows[0].row()
        data = self.downloads[row]
        
        choice = QMessageBox.question(self, "Delete", 
                                      f"Delete '{os.path.basename(data.filename)}' from list?\n\nAlso delete file from disk?", 
                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        
        if choice == QMessageBox.Cancel: return
        
        delete_file = (choice == QMessageBox.Yes)
        
        if delete_file and os.path.exists(data.filename):
            try:
                os.remove(data.filename)
            except: pass
            
        self.downloads.pop(row)
        self.config.save_history(self.downloads)
        self.refresh_table()

    def open_settings(self): 
        SettingsDialog(self).exec()