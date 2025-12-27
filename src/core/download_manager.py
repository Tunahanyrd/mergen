#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download Manager with state persistence and resume capability.

This module provides centralized download management with:
- State persistence to JSON
- Resume capability on app restart
- Download tracking and status updates
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from src.core.models import (
    DownloadItem,
    VideoDownload,
    PlaylistDownload,
    DownloadStatus,
    DownloadType,
    VideoFormat,
)


class DownloadManager:
    """Central manager for all downloads with state persistence"""
    
    def __init__(self, stateFile: Path):
        """
        Initialize download manager.
        
        Args:
            state_file: Path to JSON file for persisting state
        """
        self.state_file = state_file
        self.downloads: Dict[str, DownloadItem] = {}
        self.load_state()
    
    def add_download(self, item: DownloadItem) -> str:
        """
        Add a download and persist state.
        
        Args:
            item: DownloadItem to add
            
        Returns:
            download_id: Unique ID for this download
        """
        download_id = self._generate_id(item.url)
        self.downloads[download_id] = item
        self.save_state()
        return download_id
    
    def get_download(self, download_id: str) -> Optional[DownloadItem]:
        """Get download by ID"""
        return self.downloads.get(download_id)
    
    def remove_download(self, download_id: str):
        """Remove download and update state"""
        if download_id in self.downloads:
            del self.downloads[download_id]
            self.save_state()
    
    def update_status(self, download_id: str, status: DownloadStatus, error_message: Optional[str] = None):
        """Update download status"""
        if item := self.downloads.get(download_id):
            item.status = status
            if error_message:
                item.error_message = error_message
            self.save_state()
    
    def save_state(self):
        """Persist all downloads to JSON"""
        try:
            state = {
                did: self._serialize_download(item)
                for did, item in self.downloads.items()
            }
            
            # Create parent directory if needed
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with atomic rename
            temp_file = self.state_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(state, indent=2))
            temp_file.replace(self.state_file)
            
            print(f"💾 State saved: {len(self.downloads)} downloads")
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
    
    def load_state(self):
        """Load downloads from JSON on startup"""
        if not self.state_file.exists():
            print("📁 No existing state file, starting fresh")
            return
        
        try:
            state = json.loads(self.state_file.read_text())
            self.downloads = {
                did: self._deserialize_download(data)
                for did, data in state.items()
            }
            print(f"📂 State loaded: {len(self.downloads)} downloads")
        except Exception as e:
            print(f"⚠️ Failed to load state: {e}")
            # Create backup and start fresh
            if self.state_file.exists():
                backup = self.state_file.with_suffix(".bak")
                self.state_file.rename(backup)
                print(f"📋 Created backup at {backup}")
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    def _serialize_download(self, item: DownloadItem) -> dict:
        """Convert DownloadItem to JSON-serializable dict"""
        return item.to_dict()
    
    def _deserialize_download(self, data: dict) -> DownloadItem:
        """Reconstruct DownloadItem from dict"""
        download_type = DownloadType(data.get("download_type", "direct"))
        
        # Determine which class to use
        if download_type == DownloadType.PLAYLIST:
            # Reconstruct PlaylistDownload
            videos = [
                self._deserialize_video(v)
                for v in data.get("videos", [])
            ]
            item = PlaylistDownload(
                url=data["url"],
                save_path=Path(data["save_path"]),
                playlist_title=data.get("playlist_title", "Playlist"),
                videos=videos,
            )
        elif download_type == DownloadType.STREAMING_VIDEO:
            # Reconstruct VideoDownload
            item = VideoDownload(
                url=data["url"],
                save_path=Path(data["save_path"]),
                title=data.get("title"),
                thumbnail_url=data.get("thumbnail_url"),
                duration=data.get("duration"),
                uploader=data.get("uploader"),
            )
        else:
            # Base DownloadItem
            item = DownloadItem(
                url=data["url"],
                save_path=Path(data["save_path"]),
            )
        
        # Restore common fields
        item.status = DownloadStatus(data.get("status", "pending"))
        item.download_type = download_type
        item.error_message = data.get("error_message")
        
        if "created_at" in data:
            item.created_at = datetime.fromisoformat(data["created_at"])
        
        # Restore format info if present
        if fmt_data := data.get("format_info"):
            item.format_info = VideoFormat(
                format_id=fmt_data["format_id"],
                ext=fmt_data["ext"],
                resolution=fmt_data.get("resolution"),
            )
        
        return item
    
    def _deserialize_video(self, data: dict) -> VideoDownload:
        """Helper to deserialize a video within a playlist"""
        video = VideoDownload(
            url=data["url"],
            save_path=Path(data["save_path"]),
            title=data.get("title"),
            thumbnail_url=data.get("thumbnail_url"),
            duration=data.get("duration"),
            uploader=data.get("uploader"),
        )
        video.status = DownloadStatus(data.get("status", "pending"))
        video.error_message = data.get("error_message")
        return video
    
    def get_all_downloads(self) -> list[DownloadItem]:
        """Get all downloads as a list"""
        return list(self.downloads.values())
    
    def get_pending_downloads(self) -> list[DownloadItem]:
        """Get downloads waiting to start"""
        return [
            item for item in self.downloads.values()
            if item.status == DownloadStatus.PENDING
        ]
    
    def get_active_downloads(self) -> list[DownloadItem]:
        """Get currently downloading items"""
        return [
            item for item in self.downloads.values()
            if item.status == DownloadStatus.DOWNLOADING
        ]
