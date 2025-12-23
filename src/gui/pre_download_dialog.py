# -*- coding: utf-8 -*-
"""
Pre Download Dialog - Shows before starting download to select location and queue.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.core.i18n import I18n


class PreDownloadDialog(QDialog):
    """Dialog shown before download starts for configuration."""

    def __init__(self, url, config, queue_manager, parent=None):
        super().__init__(parent)
        self.url = url
        self.config = config
        self.queue_manager = queue_manager

        self.setWindowTitle(I18n.get("download_options"))
        self.resize(600, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # URL display
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel(I18n.get("url") + ":"))
        self.url_edit = QLineEdit(self.url)
        self.url_edit.setReadOnly(True)
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        # Category (optional, can add later)
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel(I18n.get("categories") + ":"))
        self.category_combo = QComboBox()

        # Translate category names for display
        category_names = []
        for cat_name in self.config.get("categories", {}).keys():
            # Translate if it's a default category
            display_name = self.translate_category_name(cat_name)
            category_names.append(display_name)

        self.category_combo.addItems(category_names)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        layout.addLayout(category_layout)

        # Save As
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel(I18n.get("save_to") + ":"))
        self.save_path = QLineEdit(self.config.get("default_download_dir", str(Path.home() / "Downloads")))
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(self.browse_save_location)
        save_layout.addWidget(self.save_path)
        save_layout.addWidget(browse_btn)
        layout.addLayout(save_layout)

        # Queue selection
        queue_group = QGroupBox(I18n.get("add_to_queue") + ":")
        queue_layout = QVBoxLayout()

        queue_select_layout = QHBoxLayout()
        self.queue_combo = QComboBox()
        self.queue_combo.addItems(self.queue_manager.get_queues())
        self.queue_combo.setCurrentText(self.config.get("default_queue", I18n.get("main_queue")))
        queue_select_layout.addWidget(self.queue_combo)

        add_queue_btn = QPushButton("+")
        add_queue_btn.setMaximumWidth(30)
        add_queue_btn.clicked.connect(self.add_new_queue)
        queue_select_layout.addWidget(add_queue_btn)
        queue_layout.addLayout(queue_select_layout)

        self.start_queue_chk = QCheckBox(I18n.get("start_queue_processing"))
        self.start_queue_chk.setChecked(True)
        queue_layout.addWidget(self.start_queue_chk)

        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText(I18n.get("start_download_btn"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Don't ask again
        self.dont_ask_chk = QCheckBox(I18n.get("dont_ask_again"))
        layout.addWidget(self.dont_ask_chk)

    def browse_save_location(self):
        """Open folder browser."""
        folder = QFileDialog.getExistingDirectory(self, I18n.get("select_download_folder"), self.save_path.text())
        if folder:
            self.save_path.setText(folder)

    def add_new_queue(self):
        """Quick add new queue."""
        from PySide6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, I18n.get("new_queue"), I18n.get("queue_name"))
        if ok and text:
            if self.queue_manager.create_queue(text):
                self.queue_combo.clear()
                self.queue_combo.addItems(self.queue_manager.get_queues())
                self.queue_combo.setCurrentText(text)

    def get_values(self):
        """Returns user selections."""
        return {
            "url": self.url_edit.text(),
            "save_path": self.save_path.text(),
            "queue": self.queue_combo.currentText(),
            "start_queue": self.start_queue_chk.isChecked(),
            "dont_ask": self.dont_ask_chk.isChecked(),
            "category": self.category_combo.currentText() if self.category_combo.count() > 0 else None,
        }

    def translate_category_name(self, cat_name):
        """Translate category name if it's a default category."""
        name_map = {
            "Compressed": "compressed",
            "Documents": "documents",
            "Music": "music",
            "Programs": "programs",
            "Video": "video",
            "Arşivler": "compressed",
            "Belgeler": "documents",
            "Müzikler": "music",
            "Programlar": "programs",
            "Videolar": "video",
        }
        i18n_key = name_map.get(cat_name)
        return I18n.get(i18n_key) if i18n_key else cat_name
