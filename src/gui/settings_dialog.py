# -*- coding: utf-8 -*-
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.config import ConfigManager
from src.core.i18n import I18n


class SettingsDialog(QDialog):
    def __init__(self, parent=None, initial_tab=0):
        super().__init__(parent)
        self.setWindowTitle(I18n.get("options"))
        self.resize(650, 480)
        self.initial_tab = initial_tab
        self.config = ConfigManager()

        self.setStyleSheet(
            """
            QDialog { background-color: #2b2b2b; color: #e0e0e0; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: 1px solid #444; background: #333; }
            QTabBar::tab {
                background: #2b2b2b;
                color: #ccc;
                padding: 6px 14px;
                border: 1px solid #444;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #333;
                color: white;
                border-top: 2px solid #007acc;
            }
            QGroupBox { 
                border: 1px solid #555; 
                margin-top: 20px; 
                font-weight: bold; 
                color: #007acc; 
                border-radius: 4px; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLabel { color: #e0e0e0; }
            QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {
                background: #444; border: 1px solid #555; color: white; padding: 4px; border-radius: 3px;
            }
            QLineEdit:focus, QSpinBox:focus { border: 1px solid #007acc; }
            QPushButton {
                background-color: #444; color: white; border: 1px solid #555; padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #555; border-color: #007acc; }
            QCheckBox, QRadioButton { color: #ccc; spacing: 5px; }
        """
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 1. General
        tabs.addTab(self.create_general_tab(), I18n.get("general"))

        # 2. File Types
        tabs.addTab(self.create_file_types_tab(), I18n.get("file_types"))

        # 3. Save To
        tabs.addTab(self.create_save_to_tab(), I18n.get("save_to"))

        # 4. Connection
        tabs.addTab(self.create_connection_tab(), I18n.get("connection"))

        # 5. Proxy
        tabs.addTab(self.create_proxy_tab(), I18n.get("proxy"))

        # 6. About
        tabs.addTab(self.create_about_tab(), I18n.get("about"))

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def create_general_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        # Language
        h_lang = QHBoxLayout()
        h_lang.addWidget(QLabel(I18n.get("language")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Türkçe"])
        curr_lang = self.config.get("language", "en")
        self.lang_combo.setCurrentIndex(1 if curr_lang == "tr" else 0)
        h_lang.addWidget(self.lang_combo)
        h_lang.addStretch()
        layout.addLayout(h_lang)

        g1 = QGroupBox(I18n.get("system"))
        f1 = QVBoxLayout()
        self.launch_startup = QCheckBox(I18n.get("launch_startup"))
        self.launch_startup.setChecked(self.config.get("launch_startup", False))
        f1.addWidget(self.launch_startup)
        g1.setLayout(f1)
        layout.addWidget(g1)

        # Theme removed - only dark mode now

        g3 = QGroupBox(I18n.get("dialogs"))
        f3 = QVBoxLayout()

        self.close_to_tray_chk = QCheckBox(I18n.get("minimize_to_tray"))
        self.close_to_tray_chk.setChecked(self.config.get("close_to_tray", False))
        f3.addWidget(self.close_to_tray_chk)

        self.show_complete = QCheckBox(I18n.get("show_complete_dialog"))
        self.show_complete.setChecked(self.config.get("show_complete_dialog", True))
        f3.addWidget(self.show_complete)
        g3.setLayout(f3)
        layout.addWidget(g3)

        layout.addStretch()
        w.setLayout(layout)
        return w

    def create_file_types_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel(I18n.get("config_cats")))

        # Category Selector
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(self.config.get("categories", {}).keys())
        self.cat_combo.currentIndexChanged.connect(self.load_category_settings)
        layout.addWidget(self.cat_combo)

        # Path
        g_path = QGroupBox(I18n.get("save_path"))
        h = QHBoxLayout()
        self.cat_path = QLineEdit()
        self.cat_browse = QPushButton(I18n.get("browse"))
        self.cat_browse.clicked.connect(self.browse_cat_path)
        h.addWidget(self.cat_path)
        h.addWidget(self.cat_browse)
        g_path.setLayout(h)
        layout.addWidget(g_path)

        # Extensions
        g_ext = QGroupBox(I18n.get("extensions"))
        v = QVBoxLayout()
        self.cat_exts = QPlainTextEdit()
        self.cat_exts.setMaximumHeight(80)
        v.addWidget(self.cat_exts)
        g_ext.setLayout(v)
        layout.addWidget(g_ext)

        # Store temporary changes?
        # For simplicity, we save current values to a dict when switching combo,
        # and write all to config on Save.
        self.temp_cats = self.config.get("categories", {}).copy()
        self.current_cat = self.cat_combo.currentText()
        self.load_category_settings()  # Load initial

        # Connect change events to temporary updater
        self.cat_path.textChanged.connect(self.update_temp_cat)
        self.cat_exts.textChanged.connect(self.update_temp_cat)

        layout.addStretch()
        w.setLayout(layout)
        return w

    def load_category_settings(self):
        # First save previous if necessary (handled by signals?)
        # No, signals handle immediate updates to temp_cats.

        cat_name = self.cat_combo.currentText()
        self.current_cat = cat_name

        if cat_name in self.temp_cats:
            val = self.temp_cats[cat_name]
            # Handle tuple variants
            path = ""
            exts = []
            if len(val) == 3:
                exts, icon, path = val
            elif len(val) == 2:
                exts, icon = val

            self.cat_path.blockSignals(True)
            self.cat_exts.blockSignals(True)

            self.cat_path.setText(path)
            self.cat_exts.setPlainText(" ".join(exts))

            self.cat_path.blockSignals(False)
            self.cat_exts.blockSignals(False)

    def update_temp_cat(self):
        cat_name = self.current_cat
        if cat_name in self.temp_cats:
            val = self.temp_cats[cat_name]
            # We need to preserve icon
            icon = "file"  # Default
            if len(val) >= 2:
                icon = val[1]

            path = self.cat_path.text()
            exts = self.cat_exts.toPlainText().replace("\n", " ").split()

            self.temp_cats[cat_name] = (exts, icon, path)

    def browse_cat_path(self):
        d = QFileDialog.getExistingDirectory(self, "Select Directory", self.cat_path.text())
        if d:
            self.cat_path.setText(d)

    def create_save_to_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        g = QGroupBox(I18n.get("default_dir"))
        f = QHBoxLayout()

        self.def_path_edit = QLineEdit(self.config.get("default_download_dir", ""))
        self.def_path_btn = QPushButton(I18n.get("browse"))
        self.def_path_btn.clicked.connect(self.browse_def_path)

        f.addWidget(self.def_path_edit)
        f.addWidget(self.def_path_btn)
        g.setLayout(f)
        layout.addWidget(g)

        layout.addWidget(QLabel(I18n.get("cat_override_note")))
        layout.addStretch()
        w.setLayout(layout)
        return w

    def create_connection_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        g = QGroupBox(I18n.get("conn_limit"))
        f = QFormLayout()

        self.max_conn = QComboBox()
        self.max_conn.addItems(["1", "2", "4", "8", "16", "32"])
        current = str(self.config.get("max_connections", 8))
        if current in ["1", "2", "4", "8", "16", "32"]:
            self.max_conn.setCurrentText(current)
        else:
            self.max_conn.setCurrentText("8")

        f.addRow(I18n.get("max_connections"), self.max_conn)

        g.setLayout(f)
        layout.addWidget(g)
        layout.addStretch()
        w.setLayout(layout)
        return w

    def create_proxy_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        self.proxy_chk = QCheckBox(I18n.get("use_proxy"))
        self.proxy_chk.setChecked(self.config.get("proxy_enabled", False))
        layout.addWidget(self.proxy_chk)

        g = QGroupBox(I18n.get("proxy_settings"))
        f = QFormLayout()

        self.proxy_host = QLineEdit(self.config.get("proxy_host", ""))
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(int(self.config.get("proxy_port") or 8080))

        self.proxy_user = QLineEdit(self.config.get("proxy_user", ""))
        self.proxy_pass = QLineEdit(self.config.get("proxy_pass", ""))
        self.proxy_pass.setEchoMode(QLineEdit.Password)

        f.addRow(I18n.get("host"), self.proxy_host)
        f.addRow(I18n.get("port"), self.proxy_port)
        f.addRow(I18n.get("username"), self.proxy_user)
        f.addRow(I18n.get("password"), self.proxy_pass)

        g.setLayout(f)
        layout.addWidget(g)

        # Enable/Disable based on checkbox
        g.setEnabled(self.proxy_chk.isChecked())
        self.proxy_chk.toggled.connect(g.setEnabled)

        layout.addStretch()
        w.setLayout(layout)
        return w

    def create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Logo/Icon
        icon_lbl = QLabel()
        if hasattr(self.parent(), "get_std_icon"):
            icon = self.parent().get_std_icon("app")
        else:
            icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        icon_lbl.setPixmap(icon.pixmap(100, 100))
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Title
        title = QLabel("MERGEN")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00f2ff; margin-top: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel("Version 1.0")
        version.setStyleSheet("font-size: 14px; color: #aaa; margin-bottom: 20px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        # Info Box
        info_frame = QFrame()
        info_frame.setStyleSheet(
            """
            QFrame {
                background-color: rgba(30, 30, 46, 150);
                border: 1px solid #45475a;
                border-radius: 12px;
                padding: 15px;
            }
            QLabel { font-size: 14px; margin: 2px; }
        """
        )
        il = QVBoxLayout(info_frame)

        def add_row(k, v, is_link=False):
            h = QHBoxLayout()
            l1 = QLabel(k)
            l1.setStyleSheet("color: #cdd6f4; font-weight: bold;")
            l2 = QLabel(v)
            if is_link:
                l2.setOpenExternalLinks(True)
                l2.setText(f'<a href="{v}" style="color: #89b4fa; text-decoration: none;">{v}</a>')
            else:
                l2.setStyleSheet("color: #a6adc8;")
            h.addWidget(l1)
            h.addStretch()
            h.addWidget(l2)
            il.addLayout(h)

        add_row(I18n.get("developed_by"), "Tunahanyrd")
        add_row(I18n.get("github"), "https://github.com/Tunahanyrd/mergen", True)
        add_row(I18n.get("support"), "tunahanyrd@gmail.com")
        add_row(I18n.get("license"), "MIT License")
        il.addStretch()
        l_copy = QLabel("© 2024 Tunahanyrd. All rights reserved.")
        l_copy.setAlignment(Qt.AlignCenter)
        l_copy.setStyleSheet("color: #555; margin-top: 10px; font-size: 12px;")
        il.addWidget(l_copy)

        layout.addWidget(info_frame)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def browse_def_path(self):
        d = QFileDialog.getExistingDirectory(self, I18n.get("select_directory"), self.def_path_edit.text())
        if d:
            self.def_path_edit.setText(d)

    def save_settings(self):
        # Save values to config
        old_lang = self.config.get("language", "en")
        lang_code = "tr" if self.lang_combo.currentIndex() == 1 else "en"
        self.config.set("language", lang_code)
        I18n.set_language(lang_code)

        # Check if language changed
        if old_lang != lang_code:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.information(
                self,
                I18n.get("info"),
                "Please restart the application for language changes to take effect.\nLütfen dil değişikliklerinin etkili olması için uygulamayı yeniden başlatın.",
            )

        self.config.set("close_to_tray", self.close_to_tray_chk.isChecked())

        self.config.set("launch_startup", self.launch_startup.isChecked())
        # Theme removed - always dark
        self.config.set("show_complete_dialog", self.show_complete.isChecked())

        # Save modified categories
        self.config.set("categories", self.temp_cats)

        self.config.set("default_download_dir", self.def_path_edit.text())

        self.config.set("max_connections", int(self.max_conn.currentText()))

        self.config.set("proxy_enabled", self.proxy_chk.isChecked())
        self.config.set("proxy_host", self.proxy_host.text())
        self.config.set("proxy_port", self.proxy_port.value())
        self.config.set("proxy_user", self.proxy_user.text())
        self.config.set("proxy_pass", self.proxy_pass.text())

        self.accept()

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
