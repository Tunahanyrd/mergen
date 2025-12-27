#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data models for download system using dataclasses.

This module defines all core data structures for managing downloads,
including videos, playlists, and progress tracking.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class DownloadType(Enum):
    """Type of download"""

    DIRECT_FILE = "direct"
    STREAMING_VIDEO = "streaming_video"
    PLAYLIST = "playlist"
    AUDIO_ONLY = "audio"


class DownloadStatus(Enum):
    """Download status states"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DownloadProgress:
    """Immutable progress snapshot for a download"""

    downloaded_bytes: int
    total_bytes: int
    speed_bps: float  # Bytes per second
    eta_seconds: Optional[int] = None
    current_item: Optional[int] = None  # For playlists: current video number
    total_items: Optional[int] = None  # For playlists: total videos

    @property
    def percentage(self) -> float:
        """Calculate download percentage"""
        return (self.downloaded_bytes / self.total_bytes * 100) if self.total_bytes > 0 else 0.0

    @property
    def speed_mbps(self) -> float:
        """Speed in MB/s"""
        return self.speed_bps / (1024 * 1024)

    @property
    def downloaded_mb(self) -> float:
        """Downloaded size in MB"""
        return self.downloaded_bytes / (1024 * 1024)

    @property
    def total_mb(self) -> float:
        """Total size in MB"""
        return self.total_bytes / (1024 * 1024)


@dataclass
class VideoFormat:
    """Represents a single quality/format option"""

    format_id: str
    ext: str
    resolution: Optional[str] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize: Optional[int] = None
    fps: Optional[int] = None
    tbr: Optional[float] = None  # Total bitrate


@dataclass
class DownloadItem:
    """Base class for all download types"""

    url: str
    save_path: Path
    status: DownloadStatus = DownloadStatus.PENDING
    download_type: DownloadType = DownloadType.DIRECT_FILE
    created_at: datetime = field(default_factory=datetime.now)
    format_info: Optional[VideoFormat] = None

    # Runtime state (not persisted to JSON)
    progress: Optional[DownloadProgress] = field(default=None, repr=False)
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "url": self.url,
            "save_path": str(self.save_path),
            "status": self.status.value,
            "download_type": self.download_type.value,
            "created_at": self.created_at.isoformat(),
            "format_info": (
                {
                    "format_id": self.format_info.format_id,
                    "ext": self.format_info.ext,
                    "resolution": self.format_info.resolution,
                }
                if self.format_info
                else None
            ),
            "error_message": self.error_message,
        }


@dataclass
class VideoDownload(DownloadItem):
    """Single video download"""

    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None  # Seconds
    uploader: Optional[str] = None

    def __post_init__(self):
        """Set download type automatically"""
        if self.download_type == DownloadType.DIRECT_FILE:
            self.download_type = DownloadType.STREAMING_VIDEO

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "title": self.title,
                "thumbnail_url": self.thumbnail_url,
                "duration": self.duration,
                "uploader": self.uploader,
            }
        )
        return base_dict


@dataclass
class PlaylistDownload(DownloadItem):
    """Playlist with multiple videos"""

    playlist_title: str = "Playlist"
    videos: List[VideoDownload] = field(default_factory=list)

    def __post_init__(self):
        """Set download type and create playlist subfolder"""
        self.download_type = DownloadType.PLAYLIST

        # Create playlist subfolder
        playlist_folder = self.save_path / self.sanitize_filename(self.playlist_title)
        self.save_path = playlist_folder

        # Create directory
        self.save_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Remove invalid characters from folder/file name"""
        # Remove invalid characters for Windows/Linux/macOS
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")
        # Limit length (255 chars max on most systems)
        return sanitized[:255]

    @property
    def total_size(self) -> int:
        """Total size of all videos in bytes"""
        return sum(v.format_info.filesize or 0 for v in self.videos if v.format_info)

    @property
    def completed_count(self) -> int:
        """Number of completed videos"""
        return sum(1 for v in self.videos if v.status == DownloadStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        """Number of failed videos"""
        return sum(1 for v in self.videos if v.status == DownloadStatus.FAILED)

    @property
    def progress_ratio(self) -> float:
        """Completion ratio (0.0 to 1.0)"""
        if not self.videos:
            return 0.0
        return self.completed_count / len(self.videos)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "playlist_title": self.playlist_title,
                "videos": [v.to_dict() for v in self.videos],
                "completed_count": self.completed_count,
                "total_videos": len(self.videos),
            }
        )
        return base_dict


# Legacy DownloadItem class for backward compatibility
# This will be phased out in favor of the new dataclass models
class LegacyDownloadItem:
    """Legacy download item (deprecated - use VideoDownload instead)"""

    def __init__(self, url, filename, save_path, queue="Default"):
        import time
        import uuid

        self.id = str(uuid.uuid4())[:8]
        self.url = url
        self.filename = filename
        self.save_path = save_path
        self.queue = queue
        self.status = "Pending"
        self.size = "0 MB"
        self.speed = "0 MB/s"
        self.progress = 0
        self.total_bytes = 0
        self.downloaded_bytes = 0
        self.added_at = time.time()
        self.description = ""
        self.referer = ""
        self.queue_position = 0
        self.username = ""
        self.password = ""

    @property
    def date_added(self):
        from datetime import datetime

        return datetime.fromtimestamp(self.added_at).strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        """Serialize to dictionary for JSON storage"""
        return {
            "id": self.id,
            "url": self.url,
            "filename": self.filename,
            "save_path": self.save_path,
            "queue": self.queue,
            "status": self.status,
            "size": self.size,
            "speed": self.speed,
            "progress": self.progress,
            "total_bytes": self.total_bytes,
            "downloaded_bytes": self.downloaded_bytes,
            "added_at": self.added_at,
            "description": self.description,
            "referer": self.referer,
            "queue_position": self.queue_position,
            "username": self.username,
            "password": self.password,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize from dictionary"""
        item = cls(
            url=data.get("url", ""),
            filename=data.get("filename", ""),
            save_path=data.get("save_path", ""),
            queue=data.get("queue", "Default"),
        )
        # Restore fields
        item.id = data.get("id", item.id)
        item.status = data.get("status", "Pending")
        item.size = data.get("size", "0 MB")
        item.speed = data.get("speed", "0 MB/s")
        item.progress = data.get("progress", 0)
        item.total_bytes = data.get("total_bytes", 0)
        item.downloaded_bytes = data.get("downloaded_bytes", 0)
        item.added_at = data.get("added_at", item.added_at)
        item.description = data.get("description", "")
        item.referer = data.get("referer", "")
        item.queue_position = data.get("queue_position", 0)
        item.username = data.get("username", "")
        item.password = data.get("password", "")
        return item
