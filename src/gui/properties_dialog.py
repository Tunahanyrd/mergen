import os
import subprocess

from PySide6.QtCore import QFileInfo, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets.custom_widgets import ModernButton


class PropertiesDialog(QDialog):
    def __init__(self, download_item, parent=None):
        super().__init__(parent)
        self.item = download_item
        self.setWindowTitle("Properties")
        self.resize(500, 500)

        # Apply Glassmorphism/Dark style to dialog
        self.setStyleSheet(
            """
            QDialog { background-color: #2b2b2b; color: #fff; }
            QLabel { color: #ddd; font-size: 13px; }
            QLineEdit { 
                background: #333; color: #fff; border: 1px solid #555; 
                border-radius: 4px; padding: 4px; selection-background-color: #007acc;
            }
            QGroupBox { 
                border: 1px solid #444; margin-top: 20px; font-weight: bold; color: #aaa;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """
        )

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header (Icon + Filename)
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        icon_lbl.setPixmap(icon.pixmap(64, 64))

        title_box = QVBoxLayout()
        fname = os.path.basename(self.item.filename)
        lbl_name = QLabel(fname)
        lbl_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff;")
        lbl_name.setWordWrap(True)

        lbl_type = QLabel("File Type: " + (os.path.splitext(fname)[1].upper() or "File"))
        lbl_type.setStyleSheet("color: #888;")

        title_box.addWidget(lbl_name)
        title_box.addWidget(lbl_type)

        header.addWidget(icon_lbl)
        header.addLayout(title_box)
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(
            """
            QTabWidget::pane { border: 1px solid #444; background: #2b2b2b; }
            QTabBar::tab { background: #333; color: #bbb; padding: 8px 12px; }
            QTabBar::tab:selected { background: #444; color: #fff; border-bottom: 2px solid #007acc; }
        """
        )

        tabs.addTab(self.create_general_tab(), "General")
        tabs.addTab(self.create_details_tab(), "Details")
        layout.addWidget(tabs)

        # Footer Buttons
        btns = QHBoxLayout()
        btn_open = ModernButton("Open File")
        btn_open.clicked.connect(self.open_file)

        btn_folder = ModernButton("Open Folder")
        btn_folder.clicked.connect(self.open_folder)

        btn_close = ModernButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("background-color: #444; border: 1px solid #555;")

        btns.addWidget(btn_open)
        btns.addWidget(btn_folder)
        btns.addStretch()
        btns.addWidget(btn_close)

        layout.addLayout(btns)

    def create_general_tab(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        def copyable_line(text):
            le = QLineEdit(str(text))
            le.setReadOnly(True)
            return le

        layout.addRow("Location:", copyable_line(os.path.dirname(self.item.filename)))
        layout.addRow("URL:", copyable_line(self.item.url))
        layout.addRow("Size:", copyable_line(self.item.size))
        layout.addRow("Status:", QLabel(self.item.status))  # Keep dynamic? No, static snapshot ok.
        layout.addRow("Added:", QLabel(self.item.date_added))

        return w

    def create_details_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        g_adv = QGroupBox("Advanced")
        f_adv = QFormLayout(g_adv)

        exist = os.path.exists(self.item.filename)

        f_adv.addRow("File Exists:", QLabel("Yes" if exist else "No"))
        if exist:
            fi = QFileInfo(self.item.filename)
            f_adv.addRow("Created:", QLabel(fi.birthTime().toString()))
            f_adv.addRow("Modified:", QLabel(fi.lastModified().toString()))
            f_adv.addRow("Permissions:", QLabel(f"{oct(os.stat(self.item.filename).st_mode)[-3:]}"))

        layout.addWidget(g_adv)
        layout.addStretch()
        return w

    def open_file(self):
        if os.path.exists(self.item.filename):
            try:
                subprocess.Popen(["xdg-open", self.item.filename])
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.item.filename))

    def open_folder(self):
        path = os.path.dirname(self.item.filename)
        if os.path.exists(path):
            try:
                subprocess.Popen(["xdg-open", path])
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
