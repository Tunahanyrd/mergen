import json
import os
from pathlib import Path

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

        self.config_dir = Path(os.getcwd())  # Or use user home .config ideally, but sticking to CWD for portability
        self.config = {}
        self.defaults = {
            "default_download_dir": str(Path.home() / "Downloads"),
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
                "Compressed": (["zip", "rar", "7z", "tar", "gz"], "zip", str(Path.home() / "Downloads/Compressed")),
                "Documents": (
                    ["doc", "docx", "pdf", "txt", "xls", "ppt"],
                    "doc",
                    str(Path.home() / "Downloads/Documents"),
                ),
                "Music": (["mp3", "wav", "flac", "aac"], "music", str(Path.home() / "Downloads/Music")),
                "Programs": (["exe", "msi", "deb", "rpm", "AppImage"], "app", str(Path.home() / "Downloads/Programs")),
                "Video": (["mp4", "mkv", "avi", "mov", "webm"], "video", str(Path.home() / "Downloads/Video")),
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
                sys_lang = locale.getdefaultlocale()[0]
                if not sys_lang:
                    # Fallback for some linux envs
                    sys_lang = os.getenv("LANG", "en")

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
