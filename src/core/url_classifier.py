"""
URL Classifier - Fast-path detection for downloads

Classifies URLs to enable optimization:
- Direct downloads: Skip yt-dlp analysis
- Streaming sites: Use yt-dlp analysis
"""

from typing import Literal
from urllib.parse import urlparse


class URLClassifier:
    """Classify URLs for download optimization."""
    
    # Direct download file extensions
    DIRECT_EXTENSIONS = [
        '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv',
        '.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.pdf', '.epub', '.mobi',
        '.iso', '.dmg', '.exe', '.apk',
    ]
    
    # Streaming platform domains
    STREAMING_DOMAINS = [
        'youtube.com', 'youtu.be', 'youtube-nocookie.com',
        'instagram.com', 'instagr.am',
        'twitter.com', 'x.com', 't.co',
        'tiktok.com',
        'vimeo.com',
        'dailymotion.com',
        'twitch.tv',
        'facebook.com', 'fb.watch',
        'reddit.com', 'redd.it',
        'soundcloud.com',
        'spotify.com',
        'bandcamp.com',
    ]
    
    def classify(self, url: str) -> Literal['direct', 'streaming', 'unknown']:
        """
        Classify URL type for optimization.
        
        Returns:
            'direct': Direct download URL (e.g., .mp4 file)
            'streaming': Streaming platform (needs yt-dlp)
            'unknown': Unknown type, use yt-dlp to be safe
        """
        try:
            parsed = urlparse(url)
            
            # Check extension
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in self.DIRECT_EXTENSIONS):
                return 'direct'
            
            # Check domain
            domain = parsed.netloc.lower()
            # Remove www. prefix
            domain = domain.replace('www.', '')
            
            if any(d in domain for d in self.STREAMING_DOMAINS):
                return 'streaming'
            
            return 'unknown'
            
        except Exception:
            return 'unknown'
    
    def is_direct_download(self, url: str) -> bool:
        """Check if URL is a direct download."""
        return self.classify(url) == 'direct'
    
    def is_streaming_site(self, url: str) -> bool:
        """Check if URL is from a streaming platform."""
        return self.classify(url) == 'streaming'
