"""
Utility functions for Mergen.

Shared helpers to reduce code duplication.
"""

import re


def parse_ytdlp_progress(line: str) -> dict:
    """
    Parse yt-dlp progress output line.

    Extracts:
    - Downloaded bytes
    - Total size
    - Download speed
    - ETA

    Args:
        line: Output line from yt-dlp

    Returns:
        Dict with parsed values (or empty if no match)
    """
    result = {}

    # Extract total size (look for "of XXXMiB" or "of XXXGiB")
    of_match = re.search(r"of\s+([\d.]+)([KMG])iB", line)
    if of_match:
        size_val = float(of_match.group(1))
        size_unit = of_match.group(2)

        multiplier = {"K": 1024, "M": 1024**2, "G": 1024**3}
        result["total_bytes"] = int(size_val * multiplier.get(size_unit, 1))

    # Extract speed (look for "at XXXMiB/s" or "XXXKiB/s")
    speed_match = re.search(r"at\s+([\d.]+)([KMG])iB/s", line)
    if speed_match:
        speed_val = float(speed_match.group(1))
        speed_unit = speed_match.group(2)

        multiplier = {"K": 1024, "M": 1024**2, "G": 1024**3}
        result["speed"] = int(speed_val * multiplier.get(speed_unit, 1))

    # Extract percentage
    percent_match = re.search(r"(\d+(?:\.\d+)?)%", line)
    if percent_match:
        result["percent"] = float(percent_match.group(1))

    # Extract ETA
    eta_match = re.search(r"ETA\s+(\d+:[\d:]+)", line)
    if eta_match:
        result["eta"] = eta_match.group(1)

    return result


def format_bytes(bytes_val: int) -> str:
    """
    Format bytes to human-readable string.

    Args:
        bytes_val: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def format_speed(bytes_per_sec: int) -> str:
    """
    Format speed to human-readable string.

    Args:
        bytes_per_sec: Bytes per second

    Returns:
        Formatted string (e.g., "1.5 MB/s")
    """
    return f"{format_bytes(bytes_per_sec)}/s"


def format_time(seconds: int) -> str:
    """
    Format seconds to human-readable time.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "1h 23m")
    """
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m {seconds % 60}s"

    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for filesystem.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Remove invalid chars
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Trim whitespace and dots
    filename = filename.strip(". ")

    # Limit length
    if len(filename) > 200:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[: 200 - len(ext) - 1] + "." + ext if ext else name[:200]

    return filename or "download"
