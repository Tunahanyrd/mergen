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

        # Ensure dir exists
        if self.save_dir and not os.path.exists(self.save_dir):
            try:
                os.makedirs(self.save_dir, exist_ok=True)
            except Exception:
                pass

        # 1. Determine temporary filename from URL (will be updated if server provides real name)
        name = self.get_filename_from_url(url)
        self.filename = os.path.join(self.save_dir, name)
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
        # If no extension, append .download to prevent category detection issues
        if not Path(name).suffix:
            name = f"{name}.download"
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

    def prepare(self):
        """Prepares for a fresh download: checks existence, gets size, allocate file."""
        # 1. 2. Check resume capability (skipped for brevity of snippet context)
        resume_bytes = self.load_resume_state()
        if resume_bytes is not None:
            self.downloaded_total = resume_bytes
            return True

        # 3. Request metadata (HEAD/GET range 0-0)
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
                self.log(f"Size: {self.total_size / (1024*1024):.2f} MB")
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
            traceback.print_exc()
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
            traceback.print_exc()

    def start(self):
        """Main execution flow."""
        self.log("Starting process...")
        self.start_time = time.time()

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
