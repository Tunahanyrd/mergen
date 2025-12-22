import platform
import shutil
import sys
from pathlib import Path

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from src.core.autostart import AutoStartManager
from src.core.config import ConfigManager
from src.core.i18n import I18n


class FirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(I18n.get("first_run_title"))
        self.resize(400, 300)
        self.config = ConfigManager()

        layout = QVBoxLayout(self)

        # Welcome Text
        lbl_welcome = QLabel(I18n.get("first_run_welcome"))
        lbl_welcome.setWordWrap(True)
        lbl_welcome.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_welcome)

        # Auto Start
        self.chk_autostart = QCheckBox(I18n.get("setting_autostart"))
        self.chk_autostart.setChecked(True)
        layout.addWidget(self.chk_autostart)

        # Tray
        self.chk_tray = QCheckBox(I18n.get("setting_close_to_tray"))
        self.chk_tray.setChecked(True)
        layout.addWidget(self.chk_tray)

        # Browser Extension (Platform specific info)
        self.chk_extension = QCheckBox(I18n.get("first_run_extension"))
        self.chk_extension.setChecked(True)

        # If macOS, emphasize this
        if platform.system() == "Darwin":
            self.chk_extension.setText(I18n.get("first_run_extension_mac"))

        layout.addWidget(self.chk_extension)

        layout.addStretch()

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.apply_and_close)
        layout.addWidget(buttons)

    def apply_and_close(self):
        # Apply Settings

        # 1. Auto Start
        if self.chk_autostart.isChecked():
            AutoStartManager.set_autostart(True)
            self.config.set("autostart", True)
        else:
            AutoStartManager.set_autostart(False)
            self.config.set("autostart", False)

        # 2. Tray
        self.config.set("close_to_tray", self.chk_tray.isChecked())

        # 3. Extension (macOS runtime check)
        if self.chk_extension.isChecked() and platform.system() == "Darwin":
            self.register_mac_extension()

        # Disable first run
        self.config.set("first_run", False)
        self.accept()

    def register_mac_extension(self):
        """macOS only: Copy external extension json to Chrome support dir"""
        try:
            # We assume the app is bundled and resources are in Mergen.app/Contents/Resources
            # Or we can just use the hardcoded ID since the JSON content is simple.
            ext_id = "jahgeondjmbcjleahkcmegfenejicoeb"

            # Chrome External Extensions Dir
            chrome_ext_dir = (
                Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "External Extensions"
            )
            if not chrome_ext_dir.exists():
                chrome_ext_dir.mkdir(parents=True, exist_ok=True)

            json_target = chrome_ext_dir / f"{ext_id}.json"

            # The CRX should be inside the app bundle.
            # In pyinstaller/py2app, resources are usually in specific places.
            # But for "External Extensions" on macOS, it's safer to point to an absolute path
            # if we can ensure the CRX stays there, OR use the "update_url" method if we had a web store link.
            # Since we want offline install, we must point to a file globally readable or user readable.
            #
            # Best practice for detached apps: Copy CRX to a stable user location
            # like ~/Library/Application Support/Mergen/
            mergen_support_dir = Path.home() / "Library" / "Application Support" / "Mergen"
            if not mergen_support_dir.exists():
                mergen_support_dir.mkdir(parents=True, exist_ok=True)

            # Find bundled CRX
            # Sys._MEIPASS logic similar to main_window
            if hasattr(sys, "_MEIPASS"):
                base_dir = Path(sys._MEIPASS)
            else:
                # Dev mode
                base_dir = Path.cwd()

            # Look for browser-extension/mergen-browser-extension.crx (as per build.yml layout)
            # In build.yml: --add-data="browser-extension:browser-extension"
            bundled_crx = base_dir / "browser-extension" / "mergen-browser-extension.crx"

            target_crx = mergen_support_dir / "mergen-browser-extension.crx"

            if bundled_crx.exists():
                shutil.copy2(bundled_crx, target_crx)

                # Create the JSON pointing to this target_crx
                content = f"""{{
  "external_crx": "{str(target_crx)}",
  "external_version": "0.9.3"
}}"""
                with open(json_target, "w") as f:
                    f.write(content)
            else:
                print(f"Bundled CRX not found at {bundled_crx}")

        except Exception as e:
            print(f"Failed to register mac extension: {e}")
