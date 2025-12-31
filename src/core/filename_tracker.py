"""
Filename Tracker - Monitor yt-dlp output for filename changes

Handles yt-dlp's behavior of creating temporary files (.f398.mp4)
and then merging them into final files (.mp4). This prevents
resume functionality from re-downloading entire files.
"""

import re
from pathlib import Path
from typing import Optional


class DownloadFilenameTracker:
    """Track yt-dlp filename changes during download process."""

    def __init__(self):
        # Regex patterns for yt-dlp output
        self.destination_pattern = re.compile(r'\[download\] Destination: (.+)$')
        self.merger_pattern = re.compile(r'\[Merger\] Merging formats into "(.+)"')
        self.already_downloaded_pattern = re.compile(r'\[download\] (.+) has already been downloaded')
        
    def parse_output_line(self, line: str) -> Optional[str]:
        """
        Parse a single line of yt-dlp output for filename information.
        
        Returns:
            str: Full path to file if filename found, None otherwise
            
        Examples:
            "[download] Destination: /path/video.f398.mp4" → "/path/video.f398.mp4"
            '[Merger] Merging formats into "/path/video.mp4"' → "/path/video.mp4"
        """
        line = line.strip()
        
        # Check for download destination
        match = self.destination_pattern.search(line)
        if match:
            return match.group(1).strip()
        
        # Check for merger output (final filename)
        match = self.merger_pattern.search(line)
        if match:
            return match.group(1).strip()
        
        # Check for already downloaded
        match = self.already_downloaded_pattern.search(line)
        if match:
            return match.group(1).strip()
        
        return None
    
    def is_temporary_file(self, filepath: str) -> bool:
        """
        Check if file is a temporary yt-dlp download file.
        
        Examples:
            "video.f398.mp4" → True
            "video.f251.webm" → True  
            "video.mp4" → False
        """
        path = Path(filepath)
        name = path.stem
        
        # Check for .fXXX pattern (format specifier)
        return re.match(r'.*\.f\d+$', name) is not None
    
    def get_final_filename(self, current_path: str) -> str:
        """
        Predict final filename from temporary filename.
        
        Examples:
            "video.f398.mp4" → "video.mp4"
            "video.f251.webm" → "video.mp4" (merged result)
        """
        path = Path(current_path)
        
        if not self.is_temporary_file(current_path):
            return current_path
        
        # Remove .fXXX suffix
        name_parts = path.stem.split('.')
        
        # Find and remove the .fXXX part
        clean_parts = [p for p in name_parts if not re.match(r'^f\d+$', p)]
        clean_name = '.'.join(clean_parts)
        
        # Most common final extension is .mp4 for merged files
        # but we'll keep the current extension if it's not a part file
        final_path = path.parent / f"{clean_name}{path.suffix}"
        
        return str(final_path)
