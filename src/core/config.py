import json
import os
from pathlib import Path

from PySide6.QtCore import QStandardPaths

CONFIG_FILE = "config.json"
HISTORY_FILE = "history.json"


class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Use Standard Config Location (e.g., ~/.config/mergen or %APPDATA%/mergen)
        # Assuming app name is set in main.py, but QStandardPaths uses app name if set,
        # else usually generic. We should ensure main sets Org/App Name.
        self.config_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))

        # Ensure dir exists
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass  # Fallback?

        self.config = {}

        # Localized Download Path
        dl_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        if not dl_path:
            dl_path = str(Path.home() / "Downloads")

        self.defaults = {
            "default_download_dir": dl_path,
            "max_connections": 8,
            "theme": "dark",
            "show_complete_dialog": True,
            "proxy_enabled": False,
            "proxy_host": "",
            "proxy_port": "",
            "proxy_user": "",
            "proxy_pass": "",
            "geometry": "",
            "categories": {
                "Compressed": (["zip", "rar", "7z", "tar", "gz"], "zip", str(Path(dl_path) / "Compressed")),
                "Documents": (["doc", "docx", "pdf", "txt", "xls", "ppt"], "doc", str(Path(dl_path) / "Documents")),
                "Music": (["mp3", "wav", "flac", "aac"], "music", str(Path(dl_path) / "Music")),
                "Programs": (["exe", "msi", "deb", "rpm", "AppImage"], "app", str(Path(dl_path) / "Programs")),
                "Video": (["mp4", "mkv", "avi", "mov", "webm"], "video", str(Path(dl_path) / "Video")),
            },
            "queues": ["Main Queue"],
        }

        self.load_config()
        self._initialized = True

    def load_config(self):
        config_path = self.config_dir / CONFIG_FILE
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

        # Merge defaults
        for k, v in self.defaults.items():
            if k not in self.config:
                self.config[k] = v

        # System Language Auto-Detection (First Run)
        if "language" not in self.config:
            import locale

            # Try to get system locale
            try:
                sys_lang, _ = locale.getlocale()
                if not sys_lang:
                    # Fallback for some linux envs
                    sys_lang = os.getenv("LANG", "en_US").split(".")[0]

                if sys_lang and sys_lang.lower().startswith("tr"):
                    self.config["language"] = "tr"
                else:
                    self.config["language"] = "en"
            except Exception:
                self.config["language"] = "en"

        # Ensure categories are merged if partial
        if "categories" in self.config:
            # Check for missing default categories
            for cat, val in self.defaults["categories"].items():
                if cat not in self.config["categories"]:
                    self.config["categories"][cat] = val

    def save_config(self):
        config_path = self.config_dir / CONFIG_FILE
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default if default is not None else self.defaults.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_history(self):
        from src.core.models import DownloadItem

        history_path = self.config_dir / HISTORY_FILE
        if not os.path.exists(history_path):
            return []
        try:
            with open(history_path, "r") as f:
                data = json.load(f)
                # Convert list of dicts to list of objects
                return [DownloadItem.from_dict(d) for d in data]
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    def save_history(self, downloads):
        history_path = self.config_dir / HISTORY_FILE
        try:
            # Convert list of objects to list of dicts
            data = [d.to_dict() for d in downloads]
            with open(history_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def get_proxy_config(self):
        """
        Returns a dictionary with proxy configuration.
        """
        return {
            "enabled": self.get("proxy_enabled"),
            "host": self.get("proxy_host"),
            "port": int(self.get("proxy_port") or 8080),
            "user": self.get("proxy_user"),
            "pass": self.get("proxy_pass"),
        }
