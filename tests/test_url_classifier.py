"""Tests for url_classifier module."""

import pytest
from src.core.url_classifier import URLClassifier


class TestURLClassifier:
    """Test URL classification for download optimization."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = URLClassifier()
    
    def test_direct_mp4(self):
        """Test direct MP4 URL classification."""
        url = "https://example.com/video.mp4"
        assert self.classifier.classify(url) == "direct"
        assert self.classifier.is_direct_download(url) is True
    
    def test_direct_zip(self):
        """Test direct ZIP URL classification."""
        url = "https://cdn.example.com/file.zip"
        assert self.classifier.classify(url) == "direct"
    
    def test_youtube_url(self):
        """Test YouTube URL classification."""
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ]
        for url in urls:
            assert self.classifier.classify(url) == "streaming"
            assert self.classifier.is_streaming_site(url) is True
    
    def test_instagram_url(self):
        """Test Instagram URL classification."""
        url = "https://www.instagram.com/p/ABC123/"
        assert self.classifier.classify(url) == "streaming"
    
    def test_twitter_url(self):
        """Test Twitter/X URL classification."""
        urls = [
            "https://twitter.com/user/status/123",
            "https://x.com/user/status/123",
        ]
        for url in urls:
            assert self.classifier.classify(url) == "streaming"
    
    def test_unknown_url(self):
        """Test unknown URL classification."""
        url = "https://example.com/page.html"
        assert self.classifier.classify(url) == "unknown"
    
    def test_all_extensions(self):
        """Test various direct download extensions."""
        extensions = ['.mp4', '.mkv', '.avi', '.mp3', '.zip', '.pdf']
        for ext in extensions:
            url = f"https://example.com/file{ext}"
            assert self.classifier.classify(url) == "direct"
    
    def test_domain_without_www(self):
        """Test domain matching without www prefix."""
        url1 = "https://www.youtube.com/watch?v=123"
        url2 = "https://youtube.com/watch?v=123"
        assert self.classifier.classify(url1) == self.classifier.classify(url2)
