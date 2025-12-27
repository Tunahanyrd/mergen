"""
yt-dlp configuration for different platforms.
Separates YouTube-specific settings from generic extraction.
"""


def get_youtube_opts(noplaylist=True):
    """
    YouTube-specific yt-dlp options.
    Uses web client for maximum format availability.
    
    Args:
        noplaylist (bool): If True, download only single video from playlist URLs
        
    Returns:
        dict: yt-dlp options dictionary
    """
    return {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "socket_timeout": 60,
        "noplaylist": noplaylist,
        # No extractor_args - let yt-dlp use default extraction
        # This gives us all available formats
    }


def get_generic_opts():
    """
    Generic yt-dlp options for non-YouTube platforms.
    Fast and reliable for Instagram, Twitter, etc.
    
    Returns:
        dict: yt-dlp options dictionary
    """
    return {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "socket_timeout": 30,
    }


def is_youtube(url):
    """Check if URL is YouTube."""
    return "youtube.com" in url or "youtu.be" in url


def get_opts_for_url(url, noplaylist=True):
    """
    Get appropriate yt-dlp options based on URL.
    
    Args:
        url (str): The URL to download/analyze
        noplaylist (bool): For YouTube, whether to skip playlists
        
    Returns:
        dict: Platform-appropriate yt-dlp options
    """
    if is_youtube(url):
        return get_youtube_opts(noplaylist=noplaylist)
    else:
        return get_generic_opts()
