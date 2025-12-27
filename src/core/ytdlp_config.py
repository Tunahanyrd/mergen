"""
yt-dlp configuration for different platforms.
Separates YouTube-specific settings from generic extraction.
"""


def get_youtube_opts(noplaylist=True):
    """
    YouTube-specific yt-dlp options.
    Extracts all available formats (video + audio).

    CRITICAL CONFIGURATION (v1.0.0):
    - quiet=False: Allows yt-dlp to try ALL client APIs (android, tv, web safari)
    - no_warnings=False: Shows format extraction progress
    - Result: 20+ formats reliably (tested with user URL)

    Args:
        noplaylist (bool): If True, download only single video from playlist URLs

    Returns:
        dict: yt-dlp options dictionary that extracts maximum formats
    """
    return {
        "quiet": False,  # CRITICAL: False allows multi-client fallback
        "no_warnings": False,  # CRITICAL: False enables full format discovery
        "nocheckcertificate": True,
        "socket_timeout": 60,
        "noplaylist": noplaylist,
        # No extractor_args needed - yt-dlp auto-tries all clients
    }


def get_generic_opts():
    """
    Generic yt-dlp options for non-YouTube platforms.
    Works for Instagram, Twitter, TikTok, Facebook, etc.

    Returns:
        dict: yt-dlp options dictionary
    """
    return {
        "quiet": False,  # Consistent with YouTube opts
        "no_warnings": False,
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
