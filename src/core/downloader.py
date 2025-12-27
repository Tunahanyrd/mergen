#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on December 20, 2025 19:43:23

@author: tunahan
"""

import hashlib
import json
import os
import re
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

# Constants for buffer handling
READ_SIZE = 1024 * 1024  # 1 MB
WRITE_SIZE = 1024 * 1024 * 16  # 16 MB


class Downloader:
    """
    Multi-threaded file downloader with resume support and robust state management.
    """

    def __init__(
        self,
        url,
        save_dir=None,
        worker_count=None,
        progress_callback=None,
        status_callback=None,
        completion_callback=None,
        proxy_config=None,
    ):
        self.url = url
        self.save_dir = save_dir or os.getcwd()  # Default to CWD if not specified
        self.progress_callback = progress_callback  # func(downloaded_bytes, total_bytes, speed)
        self.status_callback = status_callback  # func(message_string)
        self.completion_callback = completion_callback  # func(success, filename)
        self.proxy_config = proxy_config  # {enabled, host, port, user, pass}
        self.format_info = None  # NEW v0.9.0: Stores selected format metadata

        # Ensure dir exists
        if self.save_dir and not os.path.exists(self.save_dir):
            try:
                os.makedirs(self.save_dir, exist_ok=True)
            except Exception:
                pass

        # 1. Determine temporary filename from URL (will be updated if server provides real name)
        name = self.get_filename_from_url(url)
        self.filename = os.path.join(self.save_dir, name)

        # Check if filename collides with existing directory
        if os.path.isdir(self.filename):
            # Append numeric suffix to avoid collision
            base = self.filename
            counter = 1
            while os.path.isdir(self.filename):
                self.filename = f"{base}_{counter}"
                counter += 1

        self.temp_filename = f"{self.filename}.part"

        # Use MD5 hash of URL for the state file to ensure persistence stability
        # State file goes in same dir as temp file to be safe
        self.state_file = os.path.join(self.save_dir, hashlib.md5(url.encode()).hexdigest() + ".progress")

        # Configure worker threads based on CPU cores
        cores = os.cpu_count()
        self.worker_count = worker_count or max(1, cores // 4)

        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}
        self.total_size = 0
        self.segments = []
        self.lock = threading.Lock()
        self.last_save_time = 0

        # Stats
        self.start_time = 0
        self.running = True

        # NEW: Stream detection for v0.8.0
        self.stream_type = self._detect_stream_type(url)
        if self.stream_type in ["hls", "dash"]:
            self.log(f"🎬 Detected {self.stream_type.upper()} stream")

    def stop(self):
        """Stops the download gracefully."""
        self.running = False
        self.save_state()

    def log(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

    def get_filename_from_url(self, url):
        """Fallback method to extract filename from URL path."""
        name = Path(url.split("?")[0]).name
        if not name:
            name = "downloaded_file"
        # yt-dlp will add the correct extension automatically during download
        return name

    def update_filenames(self, real_name):
        """Updates internal filenames when the server returns a Content-Disposition header."""
        if real_name:
            # Re-construct full path with new name
            new_filename = os.path.join(self.save_dir, real_name)
            if new_filename != self.filename:
                self.filename = new_filename
                self.temp_filename = f"{self.filename}.part"
                # NOTE: self.state_file (hash based) stays the same

    def validate_segments(self):
        """
        Validates the integrity of loaded segments.
        Ensures downloaded bytes don't exceed segment size and resets invalid segments.
        """
        validated_segments = []
        for seg in self.segments:
            expected_size = (seg["end"] - seg["start"]) + 1

            # If marked finished but data is missing -> Mark as incomplete
            if seg["finished"] and seg["downloaded"] < expected_size:
                self.log(
                    f"Correction: Segment {seg['index']} marked invalid "
                    f"(Downloaded: {seg['downloaded']}, Expected: {expected_size}). Resetting."
                )
                seg["finished"] = False

            # If downloaded more than expected (overshoot) -> Clip it
            if seg["downloaded"] > expected_size:
                seg["downloaded"] = expected_size
                seg["finished"] = True

            validated_segments.append(seg)
        self.segments = validated_segments

    def load_resume_state(self):
        """
        Attempts to load previous download state.
        Priority: Check state file -> Get real filename -> Check part file.
        """
        # Step 1: Check for stable state file (hash-based)
        if not os.path.exists(self.state_file):
            return None

        self.log("Previous download state found, verifying...")
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)

                # Step 2: Retrieve real filename from state
                if "real_filename" in data:
                    self.update_filenames(data["real_filename"])

            # Step 3: Check if the actual data file exists with the resolved name
            if not os.path.exists(self.temp_filename):
                self.log("Part file not found, starting directly.")
                return None

            # Reload data confirm integrity
            with open(self.state_file, "r") as f:
                data = json.load(f)

            self.segments = data["segments"]
            self.total_size = data["total_size"]

            # Step 4: Validate segment logic
            self.validate_segments()

            downloaded_so_far = sum(s["downloaded"] for s in self.segments)
            return downloaded_so_far

        except Exception as e:
            self.log(f"Resume file corrupted ({e}), starting from scratch.")
            return None

    def save_state(self):
        """Thread-safe state saving to JSON."""
        with self.lock:
            data = {
                "url": self.url,
                "real_filename": self.filename,  # Persist true filename
                "total_size": self.total_size,
                "segments": self.segments,
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f)

    def get_proxies(self):
        """Constructs httpx proxy dictionary from config."""
        if not self.proxy_config or not self.proxy_config.get("enabled"):
            return None

        scheme = "http"  # Default scheme
        host = self.proxy_config.get("host")
        port = self.proxy_config.get("port")
        user = self.proxy_config.get("user")
        pwd = self.proxy_config.get("pass")

        if not host:
            return None

        url = f"{host}:{port}"
        if user and pwd:
            url = f"{user}:{pwd}@{url}"

        proxy_url = f"{scheme}://{url}"
        return {"all://": proxy_url}

    # ==================== v0.8.0: Stream Support ====================

    def _detect_stream_type(self, url):
        """Detect if URL is a streaming protocol."""
        if re.search(r"\.m3u8(\?.*)?$", url, re.I):
            return "hls"
        elif re.search(r"\.mpd(\?.*)?$", url, re.I):
            return "dash"
        elif re.search(r"\.(ts|mp4|mp3)(\?.*)?$", url, re.I):
            return "media"
        return "direct"

    def _check_ytdlp(self):
        """Check if yt-dlp is available."""
        try:
            import yt_dlp  # noqa: F401

            return True
        except ImportError:
            self.log("❌ yt-dlp not installed! Install with: pip install yt-dlp")
            return False

    def _check_ffmpeg(self):
        """Check if FFmpeg is installed on system."""
        import shutil

        return shutil.which("ffmpeg") is not None

    def _show_ffmpeg_guide(self):
        """Show platform-specific FFmpeg installation guide."""
        guides = {
            "linux": (
                "⚠️ FFmpeg not found! Install via package manager:\n"
                "  • Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  • Fedora/RHEL: sudo dnf install ffmpeg\n"
                "  • Arch Linux: sudo pacman -S ffmpeg"
            ),
            "darwin": (
                "⚠️ FFmpeg not found! Install via Homebrew:\n"
                "  • brew install ffmpeg\n"
                "  Or download from: https://ffmpeg.org/download.html"
            ),
            "win32": (
                "⚠️ FFmpeg not found! Install options:\n"
                "  • Recommended: winget install Gyan.FFmpeg\n"
                "  • Alternative: choco install ffmpeg\n"
                "  • Manual: https://www.gyan.dev/ffmpeg/builds/"
            ),
        }

        platform = sys.platform
        guide = guides.get(platform, "Install FFmpeg from https://ffmpeg.org")
        self.log(guide)

    def _ytdlp_progress_hook(self, d):
        """Progress hook for yt-dlp downloads."""

        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)

            if self.progress_callback:
                self.progress_callback(downloaded, total)

    def download_stream_ydl(self):
        """
        Download streaming content using yt-dlp CLI (subprocess).
        
        CRITICAL: Uses subprocess instead of Python API to avoid:
        - HTTP 416 errors
        - Range request issues  
        - GIL blocking
        """
        import subprocess
        import shutil
        
        self.log("🔀 Using yt-dlp CLI subprocess for reliable download")
        
        # Check ffmpeg
        has_ffmpeg = shutil.which("ffmpeg") is not None
        if not has_ffmpeg:
            self._show_ffmpeg_guide()
            self.log("⚠️ Continuing without FFmpeg (may fail for some streams)")
        
        # Prepare output file
        output_path = self.filename.replace(".part", "")
        
        # Build yt-dlp CLI command
        cmd = ["yt-dlp"]
        
        # Format selection (from Quality Dialog)
        if self.format_info and "format_id" in self.format_info:
            fid = self.format_info["format_id"]
            vcodec = self.format_info.get("vcodec", "none")
            acodec = self.format_info.get("acodec", "none")
            
            if vcodec != "none" and acodec != "none":
                # Combined format
                cmd.extend(["-f", fid])
            elif vcodec != "none":
                # Video only - merge with best audio
                cmd.extend(["-f", f"{fid}+bestaudio/best"])
            else:
                # Audio only
                cmd.extend(["-f", fid])
            
            self.log(f"🎯 Format: {fid}")
        else:
            # Default: best quality
            cmd.extend(["-f", "bestvideo+bestaudio/best"])
        
        # Output template
        cmd.extend(["-o", output_path])
        
        # Progress
        cmd.append("--newline")  # Each progress on new line
        cmd.append("--no-colors")  # Clean output
        
        # YouTube-specific (if needed)
        from src.core.ytdlp_config import is_youtube
        if is_youtube(self.url):
            cmd.append("--no-playlist")
        
        # Merge format if FFmpeg available
        if has_ffmpeg:
            cmd.extend(["--merge-output-format", "mp4"])
        
        # CRITICAL: Disable resume to avoid HTTP 416 errors
        cmd.append("--no-continue")
        
        # URL
        cmd.append(self.url)
        
        self.log(f"📦 Running: yt-dlp {' '.join(cmd[1:4])}...")
        
        try:
            # Run subprocess with progress parsing
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            
            # Parse progress
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                
                # yt-dlp progress: [download]  45.2% of 12.34MiB at 1.23MiB/s ETA 00:05
                if "[download]" in line and "%" in line:
                    try:
                        # Extract percentage
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "%" in part:
                                pct_str = part.replace("%", "")
                                pct = float(pct_str)
                                
                                # Extract size if available
                                if "of" in parts and i+2 < len(parts):
                                    size_str = parts[i+2]
                                    # Convert to bytes (approximate)
                                    if "MiB" in size_str:
                                        total_mb = float(size_str.replace("MiB", ""))
                                        total_bytes = int(total_mb * 1024 * 1024)
                                        downloaded_bytes = int(total_bytes * pct / 100)
                                        
                                        # Call progress callback (downloaded, total)
                                        if self.progress_callback:
                                            self.progress_callback(downloaded_bytes, total_bytes)
                                
                                break
                    except (ValueError, IndexError):
                        pass
                elif line.startswith("["):
                    pass  # Skip yt-dlp info lines
                else:
                    print(f"yt-dlp: {line}")  # Print non-progress info

            process.wait()

            if process.returncode == 0:
                print("✅ Terminal yt-dlp download complete")
                self.log("✅ Download complete")

                # Call completion callback
                if self.completion_callback:
                    self.completion_callback(True, self.filename)

                return True
            else:
                self.log("❌ Download failed")
                return False

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.log(f"❌ yt-dlp error: {e}")
            # Log full traceback only in debug mode
            import logging

            logging.debug(f"yt-dlp traceback: {traceback.format_exc()}")
            return False

    # ==================== End Stream Support ====================

    def prepare(self):
        """Prepares for a fresh download: checks existence, gets size, allocate file."""
        # 1. 2. Check resume capability (skipped for brevity of snippet context)
        resume_bytes = self.load_resume_state()
        if resume_bytes is not None:
            self.downloaded_total = resume_bytes
            return True

        # 3. Request metadata (HEAD/GET range 0-0)
        # Validate URL protocol
        if self.url.startswith(("chrome://", "about://", "file://", "chrome-extension://", "moz-extension://")):
            self.log(f"❌ Cannot download browser-internal URL: {self.url[:50]}")
            raise ValueError(f"Browser-internal URLs are not downloadable: {self.url}")

        if not self.url.startswith(("http://", "https://", "ftp://")):
            self.log(f"⚠️ URL missing protocol, adding https://: {self.url[:50]}")
            self.url = "https://" + self.url

        req_headers = {**self.headers, "Range": "bytes=0-0"}
        try:
            r = httpx.get(self.url, headers=req_headers, follow_redirects=True, proxy=self.get_proxies(), timeout=10)

            # Intelligent Filename Detection
            content_disposition = r.headers.get("Content-Disposition")
            if content_disposition:
                fname = re.findall('filename="(.+)"', content_disposition)
                if not fname:
                    fname = re.findall("filename=(.+)", content_disposition)
                if fname:
                    clean_name = fname[0].strip().strip('"')

                    # Prevent overwriting if file exists under the NEW name
                    if os.path.exists(clean_name):
                        self.log(f"INFO: The actual file name ‘{clean_name}’ already exists. Skipping.")
                        return False

                    self.update_filenames(clean_name)

            # Size Detection
            content_range = r.headers.get("Content-Range")
            if content_range:
                self.total_size = int(content_range.split("/")[-1])
            else:
                self.total_size = int(r.headers.get("Content-Length", 0))

            self.log(f"File: {self.filename}")
            if self.total_size:
                self.log(f"Size: {self.total_size / (1024 * 1024):.2f} MB")
            else:
                self.log("Size: Unknown")

            # Pre-allocate file space
            try:
                with open(self.temp_filename, "wb") as f:
                    if self.total_size > 0:
                        f.truncate(self.total_size)

            except OSError as e:
                if e.errno == 28:  # POSIX "No space left on device"
                    self.log(f"ERROR: Disk full! Required: {self.total_size}")
                else:
                    self.log(f"A system error occurred: {e.strerror} (Error code: {e.errno})")

                return False

            # Calculate segments for workers
            self.worker_count = self.worker_count if self.total_size > 0 else 1
            segment_size = self.total_size // self.worker_count
            self.segments = []
            for i in range(self.worker_count):
                start = i * segment_size
                end = (i + 1) * segment_size - 1 if i < self.worker_count - 1 else self.total_size - 1

                self.segments.append({"index": i, "start": start, "end": end, "downloaded": 0, "finished": False})

            self.save_state()
            return True

        except Exception as e:
            self.log(f"Error during preparation: {e}")
            # Log full traceback only in debug mode
            import logging

            logging.debug(f"Prepare traceback: {traceback.format_exc()}")
            return False

    def download_segment(self, segment_idx):
        """Worker function to download a specific byte range."""
        seg = self.segments[segment_idx]
        if seg["finished"]:
            return

        current_pos = seg["start"] + seg["downloaded"]
        if current_pos > seg["end"]:
            seg["finished"] = True
            self.save_state()
            return

        req_headers = {**self.headers, "Range": f"bytes={current_pos}-{seg['end']}"}

        try:
            with httpx.stream("GET", self.url, headers=req_headers, timeout=30, proxy=self.get_proxies()) as r:
                buffer = bytearray()

                # Open file in Read+Binary mode to write at specific offsets
                if not os.path.exists(self.temp_filename):
                    raise FileNotFoundError(f"Temp file '{self.temp_filename}' missing/deleted.")

                with open(self.temp_filename, "r+b") as f:
                    f.seek(current_pos)

                    for chunk in r.iter_bytes(chunk_size=READ_SIZE):
                        if not self.running:
                            break
                        if chunk:
                            buffer.extend(chunk)
                            chunk_len = len(chunk)

                            # Safety check for thread updates
                            with self.lock:
                                self.downloaded_total += chunk_len
                                if self.progress_callback:
                                    # Calculate instantaneous speed or let GUI handle it?
                                    # We just send raw bytes for now.
                                    # Note: Calculating speed properly requires windowing.
                                    self.progress_callback(self.downloaded_total, self.total_size)

                            # Flush buffer to disk periodically
                            if len(buffer) >= WRITE_SIZE:
                                f.write(buffer)
                                seg["downloaded"] += len(buffer)
                                buffer.clear()

                                # Periodic state save (every 5 seconds)
                                if time.time() - self.last_save_time > 5:
                                    self.save_state()
                                    self.last_save_time = time.time()

                    # Flush remaining buffer
                    if buffer:
                        f.write(buffer)
                        seg["downloaded"] += len(buffer)

            seg["finished"] = True
            self.save_state()
        except Exception as e:
            # Silent fail for thread, main process or retry logic handles it
            self.log(f"Error in Segment {segment_idx}: {e}")

    # NEW v0.9.0: Fetch video info for Quality Selector
    def fetch_video_info(self):
        """
        Fetches metadata and available formats for the URL using yt-dlp.
        Does NOT download the video.
        Returns:
            dict: Structured metadata (title, thumbnail, duration, formats_list) or None on failure.
        """
        # Note: No logging to stdout in subprocess mode - it contaminates JSON output
        try:
            # SOLUTION: Use terminal yt-dlp instead of Python library
            # Terminal bypasses signature solving issues and returns all formats
            import json
            import subprocess
            import sys

            # Build yt-dlp command
            cmd = ["yt-dlp", "-J", "--no-warnings", "--no-playlist", self.url]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0 and result.stdout:
                    info = json.loads(result.stdout)
                    return info
                else:
                    return None

            except subprocess.TimeoutExpired:
                print("⏱️ Terminal yt-dlp timeout")
                return None
            except json.JSONDecodeError:
                return None

        except Exception as e:
            self.log(f"❌ Analysis failed: {e}")
            # Log full traceback only in debug mode
            import logging
            import sys

            logging.debug(f"Analysis traceback: {traceback.format_exc()}")
            sys.stdout.flush()
            import traceback as tb

            tb.print_exc()
            sys.stdout.flush()
            return None

    def start(self):
        """Main execution flow."""
        self.log("Starting process...")
        self.start_time = time.time()

        # Dynamic check using yt-dlp's 1800+ extractors
        is_streaming_site = False
        try:
            import yt_dlp.extractor

            # Iterate through all extractors to see if one matches (excluding generic)
            for ie in yt_dlp.extractor.gen_extractors():
                if ie.IE_NAME != "generic" and ie.suitable(self.url):
                    is_streaming_site = True
                    self.log(f"🌍 Detected supported platform: {ie.IE_NAME}")
                    break
        except ImportError:
            self.log("⚠️ yt-dlp not found, skipping advanced detection")
        except Exception as e:
            self.log(f"⚠️ Detection error: {e}")

        # Use yt-dlp for detected streaming sites OR known stream protocols
        if self.stream_type in ["hls", "dash"] or is_streaming_site:
            print("🔀 Taking yt-dlp streaming path (is_streaming_site=True)")
            success = self.download_stream_ydl()
            
            if success:
                print("✅ Download completed successfully")
            
            if self.completion_callback:
                self.completion_callback(success, self.filename)
            return

        # Standard multi-threaded download for direct files
        initial_downloaded = self.load_resume_state()
        if initial_downloaded is None:
            if not self.prepare():
                if self.completion_callback:
                    self.completion_callback(False, self.filename)
                return
            initial_downloaded = 0
            self.downloaded_total = 0
        else:
            self.downloaded_total = initial_downloaded

        # Skip text-based tqdm

        try:
            with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                list(executor.map(self.download_segment, range(len(self.segments))))

            # Final verification
            if all(s["finished"] for s in self.segments):
                self.log("\nDownload Complete. Merging file...")

                if os.path.exists(self.filename):
                    os.remove(self.filename)
                os.rename(self.temp_filename, self.filename)

                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
                self.log(f"Success: {self.filename}")

                if self.completion_callback:
                    self.completion_callback(True, self.filename)
            else:
                self.log("\nDownload incomplete (missing segments). Please try again.")
                if self.completion_callback:
                    self.completion_callback(False, self.filename)

        except KeyboardInterrupt:
            self.log("\n\nDownload stopped by user. Progress saved, can be resumed.")
            self.save_state()
            sys.exit(0)
