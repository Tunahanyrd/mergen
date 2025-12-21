# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                               QFormLayout, QLineEdit, QSpinBox, QCheckBox, 
                               QDialogButtonBox, QGroupBox, QLabel, QHBoxLayout,
                               QComboBox, QRadioButton, QPlainTextEdit, QPushButton, QFileDialog)
from PySide6.QtCore import Qt
from src.core.config import ConfigManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(650, 480)
        self.config = ConfigManager()

        self.setStyleSheet("""
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
            QGroupBox { border: 1px solid #555; margin-top: 20px; font-weight: bold; color: #007acc; border-radius: 4px; }
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
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 1. General
        tabs.addTab(self.create_general_tab(), "General")
        
        # 2. File Types
        tabs.addTab(self.create_file_types_tab(), "File Types")
        
        # 3. Save To
        tabs.addTab(self.create_save_to_tab(), "Save To")
        
        # 4. Connection
        tabs.addTab(self.create_connection_tab(), "Connection")
        
        # 5. Proxy
        tabs.addTab(self.create_proxy_tab(), "Proxy")
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def create_general_tab(self):
        w = QWidget()
        l = QVBoxLayout()
        
        g1 = QGroupBox("System")
        f1 = QVBoxLayout()
        self.launch_startup = QCheckBox("Launch PyDownload Manager on startup")
        self.launch_startup.setChecked(self.config.get("launch_startup", False))
        f1.addWidget(self.launch_startup)
        g1.setLayout(f1)
        l.addWidget(g1)
        
        g2 = QGroupBox("View")
        f2 = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.config.get("theme", "Dark").capitalize())
        f2.addWidget(QLabel("Theme:"))
        f2.addWidget(self.theme_combo)
        f2.addStretch()
        g2.setLayout(f2)
        l.addWidget(g2)
        
        g3 = QGroupBox("Dialogs")
        f3 = QVBoxLayout()
        self.show_complete = QCheckBox("Show 'Download Complete' dialog")
        self.show_complete.setChecked(self.config.get("show_complete_dialog", True))
        f3.addWidget(self.show_complete)
        g3.setLayout(f3)
        l.addWidget(g3)
        
        l.addStretch()
        w.setLayout(l)
        return w

    def create_file_types_tab(self):
        w = QWidget()
        l = QVBoxLayout()
        
        l.addWidget(QLabel("Configure Categories:"))
        
        # Category Selector
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(self.config.get("categories", {}).keys())
        self.cat_combo.currentIndexChanged.connect(self.load_category_settings)
        l.addWidget(self.cat_combo)
        
        # Path
        g_path = QGroupBox("Save Path (Leave empty for default)")
        h = QHBoxLayout()
        self.cat_path = QLineEdit()
        self.cat_browse = QPushButton("Browse...")
        self.cat_browse.clicked.connect(self.browse_cat_path)
        h.addWidget(self.cat_path)
        h.addWidget(self.cat_browse)
        g_path.setLayout(h)
        l.addWidget(g_path)
        
        # Extensions
        g_ext = QGroupBox("Extensions (Space separated)")
        v = QVBoxLayout()
        self.cat_exts = QPlainTextEdit()
        self.cat_exts.setMaximumHeight(80)
        v.addWidget(self.cat_exts)
        g_ext.setLayout(v)
        l.addWidget(g_ext)
        
        # Store temporary changes? 
        # For simplicity, we save current values to a dict when switching combo, 
        # and write all to config on Save.
        self.temp_cats = self.config.get("categories", {}).copy()
        self.current_cat = self.cat_combo.currentText()
        self.load_category_settings() # Load initial
        
        # Connect change events to temporary updater
        self.cat_path.textChanged.connect(self.update_temp_cat)
        self.cat_exts.textChanged.connect(self.update_temp_cat)

        l.addStretch()
        w.setLayout(l)
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
            icon = "file" # Default
            if len(val) >= 2: icon = val[1]
            
            path = self.cat_path.text()
            exts = self.cat_exts.toPlainText().replace("\n", " ").split()
            
            self.temp_cats[cat_name] = (exts, icon, path)

    def browse_cat_path(self):
        d = QFileDialog.getExistingDirectory(self, "Select Directory", self.cat_path.text())
        if d:
            self.cat_path.setText(d)

    def create_save_to_tab(self):
        w = QWidget()
        l = QVBoxLayout()
        
        g = QGroupBox("Default Download Directory")
        f = QHBoxLayout()
        
        self.def_path_edit = QLineEdit(self.config.get("default_download_dir", ""))
        self.def_path_btn = QPushButton("Browse...")
        self.def_path_btn.clicked.connect(self.browse_def_path)
        
        f.addWidget(self.def_path_edit)
        f.addWidget(self.def_path_btn)
        g.setLayout(f)
        l.addWidget(g)
        
        l.addWidget(QLabel("Note: Categories can override this setting individually."))
        l.addStretch()
        w.setLayout(l)
        return w
        
    def create_connection_tab(self):
        w = QWidget()
        l = QVBoxLayout()
        
        g = QGroupBox("Connection / Speed Limiter")
        f = QFormLayout()
        
        self.max_conn = QComboBox()
        self.max_conn.addItems(["1", "2", "4", "8", "16", "32"])
        current = str(self.config.get("max_connections", 8))
        if current in ["1", "2", "4", "8", "16", "32"]:
             self.max_conn.setCurrentText(current)
        else:
             self.max_conn.setCurrentText("8")
             
        f.addRow("Max. connections number:", self.max_conn)
        
        g.setLayout(f)
        l.addWidget(g)
        l.addStretch()
        w.setLayout(l)
        return w

    def create_proxy_tab(self):
        w = QWidget()
        l = QVBoxLayout()
        
        self.proxy_chk = QCheckBox("Use Proxy")
        self.proxy_chk.setChecked(self.config.get("proxy_enabled", False))
        l.addWidget(self.proxy_chk)
        
        g = QGroupBox("Proxy Settings")
        f = QFormLayout()
        
        self.proxy_host = QLineEdit(self.config.get("proxy_host", ""))
        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(self.config.get("proxy_port", 8080))
        
        self.proxy_user = QLineEdit(self.config.get("proxy_user", ""))
        self.proxy_pass = QLineEdit(self.config.get("proxy_pass", ""))
        self.proxy_pass.setEchoMode(QLineEdit.Password)
        
        f.addRow("Host:", self.proxy_host)
        f.addRow("Port:", self.proxy_port)
        f.addRow("Username:", self.proxy_user)
        f.addRow("Password:", self.proxy_pass)
        
        g.setLayout(f)
        l.addWidget(g)
        
        # Enable/Disable based on checkbox
        g.setEnabled(self.proxy_chk.isChecked())
        self.proxy_chk.toggled.connect(g.setEnabled)
        
        l.addStretch()
        w.setLayout(l)
        return w

    def browse_def_path(self):
        d = QFileDialog.getExistingDirectory(self, "Select Directory", self.def_path_edit.text())
        if d:
            self.def_path_edit.setText(d)

    def save_settings(self):
        # Save values to config
        self.config.set("launch_startup", self.launch_startup.isChecked())
        self.config.set("theme", self.theme_combo.currentText().lower())
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
