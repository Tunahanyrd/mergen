import time
import uuid
from dataclasses import asdict, dataclass, field


@dataclass
class DownloadItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ""
    filename: str = ""
    save_path: str = ""
    status: str = "Pending"
    size: str = "Unknown"
    total_bytes: int = 0
    downloaded_bytes: int = 0
    added_at: float = field(default_factory=time.time)
    description: str = ""
    referer: str = ""
    queue: str = ""
    queue_position: int = 0  # Position within queue for ordering

    # Auth (Optional)
    username: str = ""
    password: str = ""

    @property
    def date_added(self):
        from datetime import datetime

        return datetime.fromtimestamp(self.added_at).strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        # Handle migration from old dict format
        # Old dict keys: url, filename, status, size, ext (ext is derived)

        # Ensure required fields exist
        url = data.get("url", "")
        filename = data.get("filename", "unknown")

        # Try to guess save_path if missing, or leave empty
        save_path = data.get("save_path", "")

        item = DownloadItem(url=url, filename=filename, save_path=save_path)

        # Restore ID if exists, else it stays new random
        if "id" in data:
            item.id = data["id"]

        item.status = data.get("status", "Pending")
        item.size = str(data.get("size", "Unknown"))
        item.total_bytes = data.get("total_bytes", 0)
        item.downloaded_bytes = data.get("downloaded_bytes", 0)
        item.added_at = data.get("added_at", time.time())
        item.description = data.get("description", "")
        item.referer = data.get("referer", "")
        item.queue = data.get("queue", "")
        item.queue_position = data.get("queue_position", 0)
        item.username = data.get("username", "")
        item.password = data.get("password", "")

        return item
