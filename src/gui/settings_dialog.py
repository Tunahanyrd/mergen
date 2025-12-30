# -*- coding: utf-8 -*-
import os

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

        # 6. Browser Integration
        tabs.addTab(self.create_browser_tab(), "🌐 Browser Integration")

        # 7. About
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

        from src.core.version import __version__

        version = QLabel(f"Version {__version__}")
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
        l_copy = QLabel(I18n.get("copyright"))
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
                "Please restart the application for language changes to take effect.\n"
                "Lütfen dil değişikliklerinin etkili olması için uygulamayı yeniden başlatın.",
            )

        self.config.set("close_to_tray", self.close_to_tray_chk.isChecked())

        # Handle auto-startup
        autostart_enabled = self.launch_startup.isChecked()
        self.config.set("launch_startup", autostart_enabled)

        if autostart_enabled:
            self.enable_autostart()
        else:
            self.disable_autostart()

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

    def create_browser_tab(self):
        """Create browser integration tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Header
        header = QLabel(I18n.get("browser_integration_header"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Status indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout()
        self.browser_status_icon = QLabel("⚫")
        self.browser_status_text = QLabel(I18n.get("browser_status_checking"))
        status_layout.addWidget(self.browser_status_icon)
        status_layout.addWidget(self.browser_status_text)
        status_layout.addStretch()
        status_widget.setLayout(status_layout)
        layout.addWidget(status_widget)

        layout.addSpacing(10)

        # Installation Guide
        guide_group = QGroupBox(I18n.get("browser_installation_header"))
        guide_layout = QVBoxLayout()

        # Easy Install Button (New Feature)
        easy_install_frame = QFrame()
        easy_install_frame.setStyleSheet("background-color: #333; border-radius: 6px; padding: 10px;")
        eil = QVBoxLayout(easy_install_frame)

        ei_label = QLabel("✨ " + I18n.get("browser_easy_install_title", "Easy Installation"))
        ei_label.setStyleSheet("font-weight: bold; color: #00f2ff;")
        eil.addWidget(ei_label)

        ei_desc = QLabel(
            I18n.get("browser_easy_install_desc", "Automatically open extension folder and browser setup page.")
        )
        ei_desc.setWordWrap(True)
        eil.addWidget(ei_desc)

        self.easy_install_btn = QPushButton(I18n.get("browser_easy_install_btn", "Launch Installation Helper"))
        self.easy_install_btn.setStyleSheet("background-color: #007acc; font-weight: bold; padding: 8px;")
        self.easy_install_btn.clicked.connect(self.launch_extension_helper)
        eil.addWidget(self.easy_install_btn)

        guide_layout.addWidget(easy_install_frame)

        # Manual Instructions (Collapsible/Secondary)
        guide_layout.addSpacing(10)
        manual_lbl = QLabel(I18n.get("browser_manual_install", "Manual Installation:"))
        manual_lbl.setStyleSheet("font-weight: bold; color: #aaa;")
        guide_layout.addWidget(manual_lbl)

        manual_text = QLabel(
            f"1. {I18n.get('browser_chrome_step1')}<br>"
            f"2. {I18n.get('browser_chrome_step2')}<br>"
            f"3. {I18n.get('browser_chrome_step3')}<br>"
            f"4. {I18n.get('browser_chrome_step4')}"
        )
        manual_text.setWordWrap(True)
        manual_text.setStyleSheet("color: #888; margin-left: 10px;")
        guide_layout.addWidget(manual_text)

        guide_group.setLayout(guide_layout)
        layout.addWidget(guide_group)

        # Registration section
        reg_group = QGroupBox(I18n.get("browser_register_header"))
        reg_layout = QVBoxLayout()

        # Extension ID input
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel(I18n.get("browser_ext_id_label")))
        self.ext_id_input = QLineEdit()
        self.ext_id_input.setPlaceholderText(I18n.get("ext_id_placeholder"))
        self.ext_id_input.setToolTip(I18n.get("ext_id_help"))
        id_layout.addWidget(self.ext_id_input)
        reg_layout.addLayout(id_layout)

        # Register button
        register_btn = QPushButton(I18n.get("browser_register_btn"))
        register_btn.clicked.connect(self.register_extension)
        reg_layout.addWidget(register_btn)

        reg_group.setLayout(reg_layout)
        layout.addWidget(reg_group)

        layout.addStretch()
        widget.setLayout(layout)

        # Check status
        self.check_browser_integration_status()

        return widget

    def launch_extension_helper(self):
        """Run the helper script to make installation easy."""
        import subprocess
        import sys
        from pathlib import Path

        script_name = "install_extension.sh"
        if sys.platform == "win32":
            # On Windows we might not have the shell script, but we can open the folder
            # TODO: A batch file would be better, but for now open folder
            folder = Path.cwd() / "browser-extension"
            os.startfile(folder)
            # Also try to open chrome extensions
            import webbrowser

            webbrowser.open("chrome://extensions")
            return

        # Linux/Mac
        script_path = Path.cwd() / script_name
        if not script_path.exists():
            # Try looking up
            script_path = Path.cwd().parent / script_name

        if script_path.exists():
            subprocess.Popen(["bash", str(script_path)])
        else:
            # Fallback: just open the folder
            folder = Path.cwd() / "browser-extension"
            subprocess.Popen(["xdg-open", str(folder)])

    def check_browser_integration_status(self):
        """Check if browser integration is registered."""
        try:
            import json
            from pathlib import Path

            # Check Chrome manifest
            chrome_manifest = Path.home() / ".config/google-chrome/NativeMessagingHosts/com.tunahanyrd.mergen.json"
            firefox_manifest = Path.home() / ".mozilla/native-messaging-hosts/com.tunahanyrd.mergen.json"

            if chrome_manifest.exists():
                with open(chrome_manifest) as f:
                    data = json.load(f)
                    origins = data.get("allowed_origins", [])
                    if origins and "PLACEHOLDER" not in origins[0]:
                        self.browser_status_icon.setText("🟢")
                        self.browser_status_text.setText(I18n.get("browser_status_connected"))
                        return

            if firefox_manifest.exists():
                self.browser_status_icon.setText("🟢")
                self.browser_status_text.setText(I18n.get("browser_status_connected_firefox"))
                return

            # Not registered
            self.browser_status_icon.setText("🔴")
            self.browser_status_text.setText(I18n.get("browser_status_not_registered"))

        except Exception:
            self.browser_status_icon.setText("⚠️")
            self.browser_status_text.setText(I18n.get("browser_status_error"))

    def register_extension(self):
        """Register browser extension with given Extension ID."""
        import json
        from pathlib import Path

        from PySide6.QtWidgets import QMessageBox

        ext_id = self.ext_id_input.text().strip()

        if not ext_id:
            QMessageBox.warning(self, I18n.get("warning"), I18n.get("enter_ext_id"))
            return

        try:
            # 1. Install Native Host Script
            import shutil
            import sys

            # Determine source path of native host script
            if hasattr(sys, "_MEIPASS"):
                # Frozen/compiled mode
                base_dir = sys._MEIPASS
                src_script = Path(base_dir) / "native-host/mergen-native-host.py"
            else:
                # Source mode: src/gui/../../native-host/mergen-native-host.py
                base_dir = Path(__file__).resolve().parent.parent.parent
                src_script = base_dir / "native-host/mergen-native-host.py"

            if not src_script.exists():
                # Fallback check
                if (Path.cwd() / "native-host/mergen-native-host.py").exists():
                    src_script = Path.cwd() / "native-host/mergen-native-host.py"
                else:
                    raise FileNotFoundError(f"Native host script not found at {src_script}")

            # Install destination
            bin_dir = Path.home() / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            dst_script = bin_dir / "mergen-native-host.py"

            # Copy and set permissions
            shutil.copy2(src_script, dst_script)
            dst_script.chmod(0o755)  # rwxr-xr-x

            print(f"✅ Installed native host to {dst_script}")

            # 2. Update Chrome manifest
            chrome_dir = Path.home() / ".config/google-chrome/NativeMessagingHosts"
            chrome_dir.mkdir(parents=True, exist_ok=True)

            chrome_manifest = chrome_dir / "com.tunahanyrd.mergen.json"
            manifest_data = {
                "name": "com.tunahanyrd.mergen",
                "description": "Mergen Download Manager Native Messaging Host",
                "path": str(dst_script),
                "type": "stdio",
                "allowed_origins": [f"chrome-extension://{ext_id}/"],
            }

            with open(chrome_manifest, "w") as f:
                json.dump(manifest_data, f, indent=2)

            # Update Firefox manifest
            firefox_dir = Path.home() / ".mozilla/native-messaging-hosts"
            firefox_dir.mkdir(parents=True, exist_ok=True)

            firefox_manifest = firefox_dir / "com.tunahanyrd.mergen.json"
            firefox_data = manifest_data.copy()
            firefox_data["allowed_origins"] = [f"moz-extension://{ext_id}/"]

            with open(firefox_manifest, "w") as f:
                json.dump(firefox_data, f, indent=2)

            QMessageBox.information(
                self,
                I18n.get("success"),
                f"✅ {I18n.get('ext_registered_success')}\\n\\n{I18n.get('reload_extension')}",
            )

            # Update status
            self.check_browser_integration_status()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to register:\\n{str(e)}")

    def enable_autostart(self):
        """Enable auto-startup on system boot (Linux/macOS/Windows)."""
        import os
        import sys
        from pathlib import Path

        try:
            if sys.platform == "linux":
                # Linux: XDG autostart
                autostart_dir = Path.home() / ".config/autostart"
                autostart_dir.mkdir(parents=True, exist_ok=True)

                desktop_file = autostart_dir / "mergen.desktop"

                # Get current script path
                current_exec = os.path.abspath(sys.argv[0])

                desktop_content = f"""[Desktop Entry]
Type=Application
Name=Mergen
Exec={current_exec}
Icon=mergen
Comment=Mergen Download Manager
X-GNOME-Autostart-enabled=true
"""
                desktop_file.write_text(desktop_content)

            elif sys.platform == "darwin":
                # macOS: LaunchAgent
                launch_agents_dir = Path.home() / "Library/LaunchAgents"
                launch_agents_dir.mkdir(parents=True, exist_ok=True)

                plist_file = launch_agents_dir / "com.tunahanyrd.mergen.plist"

                current_exec = os.path.abspath(sys.argv[0])

                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tunahanyrd.mergen</string>
    <key>ProgramArguments</key>
    <array>
        <string>{current_exec}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
                plist_file.write_text(plist_content)

            elif sys.platform == "win32":
                # Windows: Registry
                import winreg

                current_exec = os.path.abspath(sys.argv[0])

                # Open/Create registry key
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE
                )

                # Set Mergen to start on boot
                winreg.SetValueEx(key, "Mergen", 0, winreg.REG_SZ, current_exec)
                winreg.CloseKey(key)

        except Exception as e:
            print(f"Failed to enable autostart: {e}")

    def disable_autostart(self):
        """Disable auto-startup on system boot (Linux/macOS/Windows)."""
        import sys
        from pathlib import Path

        try:
            if sys.platform == "linux":
                autostart_file = Path.home() / ".config/autostart/mergen.desktop"
                if autostart_file.exists():
                    autostart_file.unlink()

            elif sys.platform == "darwin":
                plist_file = Path.home() / "Library/LaunchAgents/com.tunahanyrd.mergen.plist"
                if plist_file.exists():
                    plist_file.unlink()

            elif sys.platform == "win32":
                # Windows: Remove from Registry
                import winreg

                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_SET_VALUE,
                    )
                    winreg.DeleteValue(key, "Mergen")
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass  # Key doesn't exist, already disabled

        except Exception as e:
            print(f"Failed to disable autostart: {e}")
