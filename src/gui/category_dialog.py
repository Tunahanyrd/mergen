# -*- coding: utf-8 -*-
import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
)

from src.core.i18n import I18n


class CategoryDialog(QDialog):
    def __init__(self, parent=None, name="", exts="", icon="folder", save_path=""):
        super().__init__(parent)
        self.setWindowTitle(
            I18n.get("add_category") if not name else I18n.get("category_properties", "Category Properties")
        )
        self.resize(500, 300)
        self.save_path = save_path

        self.setStyleSheet(
            """
            QDialog { background-color: #2b2b2b; color: #e0e0e0; font-family: 'Segoe UI'; }
            QLineEdit, QComboBox {
                background: #444; border: 1px solid #555; color: white; padding: 4px; border-radius: 3px;
            }
            QLabel { color: #e0e0e0; }
            QPushButton {
                background-color: #444; color: white; border: 1px solid #555; padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #555; border-color: #007acc; }
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Name
        self.name_edit = QLineEdit(name)
        form.addRow(I18n.get("category_name", "Category Name:"), self.name_edit)

        # Extensions
        self.ext_edit = QLineEdit(exts)
        self.ext_edit.setPlaceholderText("e.g. zip, rar, 7z")
        form.addRow(I18n.get("auto_category_prompt"), self.ext_edit)

        # Icon Selector with Browse
        icon_layout = QHBoxLayout()
        self.icon_combo = QComboBox()
        self.icon_combo.setMinimumWidth(150)
        self.icons = ["folder", "music", "video", "app", "doc", "zip"]

        # Pre-fill standard icons
        for ic in self.icons:
            qicon = self.get_std_icon(ic)
            self.icon_combo.addItem(qicon, ic.capitalize(), ic)

        # Handle custom/existing icon
        if icon not in self.icons and icon:
            # It's a path or unknown
            if os.path.exists(icon):
                self.icon_combo.addItem(QIcon(icon), "Custom", icon)
            else:
                self.icon_combo.addItem(self.get_std_icon("folder"), "Unknown", icon)

        # Select current
        idx = self.icon_combo.findData(icon)
        if idx >= 0:
            self.icon_combo.setCurrentIndex(idx)

        browse_icon_btn = QPushButton(I18n.get("browse"))
        browse_icon_btn.clicked.connect(self.browse_icon)

        icon_layout.addWidget(self.icon_combo)
        icon_layout.addWidget(browse_icon_btn)
        form.addRow("Icon:", icon_layout)

        # Save Path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(save_path)
        self.path_edit.setPlaceholderText(I18n.get("general_downloads_folder"))
        browse_path_btn = QPushButton(I18n.get("browse"))
        browse_path_btn.clicked.connect(self.browse_path)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_path_btn)
        form.addRow(I18n.get("save_category_to"), path_layout)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_icon(self):
        fname, _ = QFileDialog.getOpenFileName(self, I18n.get("select_icon"), "", "Images (*.png *.ico *.jpg)")
        if fname:
            self.icon_combo.addItem(QIcon(fname), "Custom", fname)
            self.icon_combo.setCurrentIndex(self.icon_combo.count() - 1)

    def browse_path(self):
        d = QFileDialog.getExistingDirectory(self, I18n.get("select_directory"))
        if d:
            self.path_edit.setText(d)

    def get_std_icon(self, name):
        style = QApplication.style()
        if name == "folder":
            return style.standardIcon(QStyle.SP_DirIcon)
        if name == "music":
            return style.standardIcon(QStyle.SP_MediaVolume)
        if name == "video":
            return style.standardIcon(QStyle.SP_MediaVolume)
        if name == "app":
            return style.standardIcon(QStyle.SP_DesktopIcon)
        if name == "doc":
            return style.standardIcon(QStyle.SP_FileIcon)
        if name == "zip":
            return style.standardIcon(QStyle.SP_DriveFDIcon)
        return style.standardIcon(QStyle.SP_DirIcon)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "exts": [e.strip() for e in self.ext_edit.text().split(",") if e.strip()],
            "icon": self.icon_combo.currentData(),
            "path": self.path_edit.text(),
        }
