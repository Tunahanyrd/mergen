"""Tests for filename_tracker module."""

import pytest
from src.core.filename_tracker import DownloadFilenameTracker


class TestFilenameTracker:
    """Test filename tracking from yt-dlp output."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.tracker = DownloadFilenameTracker()
    
    def test_parse_download_destination(self):
        """Test parsing [download] Destination: output."""
        line = "[download] Destination: /home/user/video.f398.mp4"
        result = self.tracker.parse_output_line(line)
        assert result == "/home/user/video.f398.mp4"
    
    def test_parse_merger_output(self):
        """Test parsing [Merger] output."""
        line = '[Merger] Merging formats into "/home/user/video.mp4"'
        result = self.tracker.parse_output_line(line)
        assert result == "/home/user/video.mp4"
    
    def test_parse_already_downloaded(self):
        """Test parsing already downloaded message."""
        line = "[download] /home/user/video.mp4 has already been downloaded"
        result = self.tracker.parse_output_line(line)
        assert result == "/home/user/video.mp4"
    
    def test_parse_irrelevant_line(self):
        """Test that irrelevant lines return None."""
        line = "[youtube] Extracting URL: https://youtube.com/..."
        result = self.tracker.parse_output_line(line)
        assert result is None
    
    def test_is_temporary_file(self):
        """Test temporary file detection."""
        assert self.tracker.is_temporary_file("video.f398.mp4") is True
        assert self.tracker.is_temporary_file("video.f251.webm") is True
        assert self.tracker.is_temporary_file("video.mp4") is False
        assert self.tracker.is_temporary_file("audio.f140.m4a") is True
    
    def test_get_final_filename(self):
        """Test final filename prediction."""
        # Temporary files should have .fXXX removed
        assert "video.mp4" in self.tracker.get_final_filename("video.f398.mp4")
        assert "audio.webm" in self.tracker.get_final_filename("audio.f251.webm")
        
        # Non-temporary files should remain unchanged
        assert self.tracker.get_final_filename("video.mp4") == "video.mp4"
