#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt-dlp subprocess wrapper with process control and error handling.

This module provides a managed interface to yt-dlp CLI with:
- Process control (pause/resume/terminate)
- Automatic retry on connection errors
- Progress parsing
- Downloaded file tracking
"""

import os
import signal
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional

from src.core.logger import get_logger

logger = get_logger(__name__)

# Import models for type hints
from src.core.models import DownloadProgress


class ProcessState(Enum):
    """yt-dlp process state machine"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class YtDlpConfig:
    """Configuration for yt-dlp subprocess"""

    format_id: str = "bestvideo+bestaudio/best"
    output_template: str = "%(title)s.%(ext)s"
    no_continue: bool = True  # Avoid HTTP 416 errors
    merge_format: str = "mp4"
    quiet: bool = False
    cookies_from_browser: Optional[str] = None  # "firefox" or "chrome"
    skip_unavailable: bool = True  # Skip private/deleted videos

    def build_command(self, url: str, output_dir: Path) -> List[str]:
        """Build yt-dlp command with all options"""
        cmd = ["yt-dlp", "-f", self.format_id]
        cmd.extend(["-o", str(output_dir / self.output_template)])
        cmd.extend(["--newline", "--no-colors"])

        if self.no_continue:
            cmd.append("--no-continue")

        if self.merge_format:
            cmd.extend(["--merge-output-format", self.merge_format])

        if self.cookies_from_browser:
            cmd.extend(["--cookies-from-browser", self.cookies_from_browser])

        if self.skip_unavailable:
            cmd.append("--ignore-errors")  # Continue on private/deleted videos

        cmd.append(url)
        return cmd


class YtDlpProcess:
    """Managed yt-dlp subprocess with process control and error handling"""

    def __init__(self, config: YtDlpConfig, url: str, output_dir: Path):
        self.config = config
        self.url = url
        self.output_dir = output_dir
        self.process: Optional[subprocess.Popen] = None
        self.state = ProcessState.IDLE
        self.retry_count = 0
        self.max_retries = 3
        self.downloaded_files: List[Path] = []

    def start(
        self,
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None,
    ) -> bool:
        """
        Start download with automatic retry on errors.

        Args:
            progress_callback: Called with DownloadProgress object
            status_callback: Called with status message (str)
            completion_callback: Called with (success: bool, files: List[Path])

        Returns:
            True if download succeeded, False otherwise
        """
        self.state = ProcessState.RUNNING

        while self.retry_count < self.max_retries:
            try:
                cmd = self.config.build_command(self.url, self.output_dir)
                logger.debug(f"Running: {' '.join(cmd[:4])}...")

                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    preexec_fn=os.setsid,  # Enable process group for clean termination
                )

                # Parse output
                for line in self.process.stdout:
                    line = line.strip()
                    if not line:
                        continue

                    # Detect downloaded files
                    if "[download] Destination:" in line:
                        filename = line.split("Destination:")[-1].strip()
                        self.downloaded_files.append(Path(filename))
                        logger.debug(f"File tracked: {filename}")

                    # Handle private video errors (skip and continue)
                    if "ERROR: [youtube]" in line and "Private video" in line:
                        if status_callback:
                            status_callback("⚠️ Skipping private video")
                        continue

                    # Handle connection errors (retry)
                    if any(err in line for err in ["HTTP Error", "Connection reset", "Network unreachable"]):
                        logger.warning(f"Connection error, retrying ({self.retry_count + 1}/{self.max_retries})")
                        self.retry_count += 1
                        self.terminate()
                        break

                    # Progress callback
                    if progress_callback and "[download]" in line and "%" in line:
                        progress = self._parse_progress(line)
                        if progress:
                            progress_callback(progress)

                    # Status callback
                    if status_callback:
                        status_callback(line)

                # Wait for completion
                self.process.wait()

                if self.process.returncode == 0:
                    self.state = ProcessState.COMPLETED
                    if completion_callback:
                        completion_callback(True, self.downloaded_files)
                    return True

            except Exception as e:
                logger.error(f"yt-dlp error: {e}")
                self.retry_count += 1

        # Failed after all retries
        self.state = ProcessState.FAILED
        if completion_callback:
            completion_callback(False, [])
        return False

    def pause(self):
        """Pause the download (SIGSTOP)"""
        if self.process and self.state == ProcessState.RUNNING:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGSTOP)
                self.state = ProcessState.PAUSED
                logger.info("Download paused")
                return True
            except Exception as e:
                logger.error(f"Failed to pause: {e}")
                return False
        return False

    def resume(self):
        """Resume the download (SIGCONT)"""
        if self.process and self.state == ProcessState.PAUSED:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGCONT)
                self.state = ProcessState.RUNNING
                logger.info("Download resumed")
                return True
            except Exception as e:
                logger.error(f"Failed to resume: {e}")
                return False
        return False

    def terminate(self):
        """Stop the download (SIGTERM)"""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.state = ProcessState.STOPPED
                logger.info("Download stopped")
                return True
            except Exception as e:
                logger.error(f"Failed to terminate: {e}")
                return False
        return False

    def _parse_progress(self, line: str) -> Optional[DownloadProgress]:
        """
        Parse yt-dlp progress line into DownloadProgress.

        Example line:
        [download]   0.6% of    1.74GiB at    1.02MiB/s ETA 28:49
        """
        try:
            parts = line.split()
            pct = 0.0
            total_bytes = 0
            speed_bytes = 0.0
            eta_seconds = None

            # Extract percentage
            for part in parts:
                if "%" in part:
                    pct = float(part.replace("%", ""))
                    break

            # Extract total size (look for "of XXXMiB" or "of XXXGiB")
            for i, part in enumerate(parts):
                if part == "of" and i + 1 < len(parts):
                    size_str = parts[i + 1]
                    try:
                        if "GiB" in size_str:
                            total_gb = float(size_str.replace("GiB", "").replace("~", ""))
                            total_bytes = int(total_gb * 1024 * 1024 * 1024)
                        elif "MiB" in size_str or "MB" in size_str:
                            total_mb = float(size_str.replace("MiB", "").replace("MB", "").replace("~", ""))
                            total_bytes = int(total_mb * 1024 * 1024)
                    except ValueError:
                        pass
                    break

            # Extract speed (look for "at XXXMiB/s" or "XXXKiB/s")
            for i, part in enumerate(parts):
                if part == "at" and i + 1 < len(parts):
                    speed_str = parts[i + 1]
                    if "MiB/s" in speed_str:
                        speed_mb = float(speed_str.replace("MiB/s", ""))
                        speed_bytes = speed_mb * 1024 * 1024
                    elif "KiB/s" in speed_str:
                        speed_kb = float(speed_str.replace("KiB/s", ""))
                        speed_bytes = speed_kb * 1024
                    break

            # Extract ETA (look for "ETA HH:MM:SS")
            for i, part in enumerate(parts):
                if part == "ETA" and i + 1 < len(parts):
                    eta_str = parts[i + 1]
                    try:
                        # Parse HH:MM:SS or MM:SS
                        time_parts = eta_str.split(":")
                        if len(time_parts) == 3:
                            eta_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
                        elif len(time_parts) == 2:
                            eta_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                    except ValueError:
                        pass
                    break

            # Calculate downloaded bytes from percentage
            if total_bytes > 0:
                downloaded_bytes = int(total_bytes * pct / 100)

                return DownloadProgress(
                    downloaded_bytes=downloaded_bytes,
                    total_bytes=total_bytes,
                    speed_bps=speed_bytes,
                    eta_seconds=eta_seconds,
                )

        except (ValueError, IndexError):
            pass  # Ignore parse errors

        return None
