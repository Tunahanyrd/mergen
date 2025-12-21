#!/home/tunahan/anaconda3/envs/ml_env/bin/python3
# -*- coding: utf-8 -*-
"""
Created on December 20, 2025 19:43:23

@author: tunahan
"""

import os, httpx, json, threading, time, re, sys, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Constants for buffer handling
READ_SIZE = 1024 * 1024         # 1 MB
WRITE_SIZE = 1024 * 1024 * 16   # 16 MB

class Downloader:
    """
    Multi-threaded file downloader with resume support and robust state management.
    """
    def __init__(self, url, worker_count=None):
        self.url = url
        
        # 1. Determine temporary filename from URL (will be updated if server provides real name)
        self.filename = self.get_filename_from_url(url)
        self.temp_filename = f"{self.filename}.part" 
        
        # Use MD5 hash of URL for the state file to ensure persistence stability 
        # even if the resolved filename changes during runtime.
        self.state_file = hashlib.md5(url.encode()).hexdigest() + ".progress"
        
        # Configure worker threads based on CPU cores
        cores = os.cpu_count()
        self.worker_count = worker_count or max(1, cores // 4)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
        }
        self.total_size = 0
        self.segments = []     
        self.lock = threading.Lock()
        self.last_save_time = 0
        self.main_bar = None

    def get_filename_from_url(self, url):
        """Fallback method to extract filename from URL path."""
        name = Path(url.split('?')[0]).name
        return name if name else "downloaded_file"

    def update_filenames(self, real_name):
        """Updates internal filenames when the server returns a Content-Disposition header."""
        if real_name and real_name != self.filename:
            self.filename = real_name
            self.temp_filename = f"{self.filename}.part"
            # NOTE: self.state_file must NOT be updated here to maintain resume capability.

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
                print(f"Correction: Segment {seg['index']} marked invalid (Downloaded: {seg['downloaded']}, Expected: {expected_size}). Resetting.")
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

        print("Previous download state found, verifying...")
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                
                # Step 2: Retrieve real filename from state
                if "real_filename" in data:
                    self.update_filenames(data["real_filename"])
            
            # Step 3: Check if the actual data file exists with the resolved name
            if not os.path.exists(self.temp_filename):
                print("Part file not found, starting directly.")
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
            print(f"Resume file corrupted ({e}), starting from scratch.")
            return None
            
    def save_state(self):
        """Thread-safe state saving to JSON."""
        with self.lock:
            data = {
                "url": self.url,
                "real_filename": self.filename, # Persist true filename
                "total_size": self.total_size,
                "segments": self.segments
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f)

    def prepare(self):
        """Prepares for a fresh download: checks existence, gets size, allocates file."""
        # 1. Check if target file already exists
        if os.path.exists(self.filename):
            print(f"INFO: '{self.filename}' already exists. Skipping.")
            return False

        # 2. Check resume capability
        resume_bytes = self.load_resume_state()
        if resume_bytes is not None:
            return True 

        # 3. Request metadata (HEAD/GET range 0-0)
        req_headers = {**self.headers, "Range": "bytes=0-0"}
        try:
            r = httpx.get(self.url, headers=req_headers, follow_redirects=True)
            
            # Intelligent Filename Detection
            content_disposition = r.headers.get("Content-Disposition")
            if content_disposition:
                fname = re.findall('filename="(.+)"', content_disposition)
                if not fname:
                    fname = re.findall('filename=(.+)', content_disposition)
                if fname:
                    clean_name = fname[0].strip().strip('"')
                    self.update_filenames(clean_name)
                    
                    if os.path.exists(self.filename):
                        print(f"INFO: The actual file name ‘{self.filename}’ already exists. Skipping.")
                        return False
            
            # Size Detection
            content_range = r.headers.get("Content-Range")
            if content_range:
                self.total_size = int(content_range.split("/")[-1])
            else:
                self.total_size = int(r.headers.get("Content-Length", 0))

            print(f"File: {self.filename}")
            print(f"Size: {self.total_size / (1024*1024):.2f} MB")

            # Pre-allocate file space
            try:
                with open(self.temp_filename, "wb") as f:
                    f.truncate(self.total_size)
                    
            except OSError as e:
                if e.errno == 28: # POSIX sistemlerde "No space left on device"
                    print(f"ERROR: Disk full! Required: {self.total_size}, Insufficient space available.")
                else:
                    print(f"A system error occurred: {e.strerror} (Error code: {e.errno})")
                
                return False

            # Calculate segments for workers
            segment_size = self.total_size // self.worker_count
            self.segments = []
            for i in range(self.worker_count):
                start = i * segment_size
                end = (i + 1) * segment_size - 1 if i < self.worker_count - 1 else self.total_size - 1
                
                self.segments.append({
                    "index": i, "start": start, "end": end,
                    "downloaded": 0, "finished": False
                })
            
            self.save_state()
            return True

        except Exception as e:
            print(f"Error during preparation: {e}")
            return False

    def download_segment(self, segment_idx):
        """Worker function to download a specific byte range."""
        seg = self.segments[segment_idx]
        if seg["finished"]: return

        current_pos = seg["start"] + seg["downloaded"]
        if current_pos > seg["end"]:
            seg["finished"] = True; self.save_state(); return

        req_headers = {**self.headers, "Range": f"bytes={current_pos}-{seg['end']}"}

        try:
            with httpx.stream("GET", self.url, headers=req_headers, timeout=30) as r:
                buffer = bytearray()

                # Open file in Read+Binary mode to write at specific offsets
                with open(self.temp_filename, "r+b") as f:
                    f.seek(current_pos)
                    
                    with tqdm(total=(seg['end'] - seg['start']) + 1, 
                        initial=seg['downloaded'],              
                        unit='B', unit_scale=True, 
                        desc=f"P{segment_idx}", 
                        position=segment_idx+1, leave=False) as pbar:
                        
                        for chunk in r.iter_bytes(chunk_size=READ_SIZE):
                            if chunk:
                                buffer.extend(chunk)
                                chunk_len = len(chunk)
                                pbar.update(chunk_len)
                                if self.main_bar: self.main_bar.update(chunk_len)
                                
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
            print(f"Error in Segment {segment_idx}: {e}") 

    def start(self):
        """Main execution flow."""
        print("Starting process...")
        
        initial_downloaded = self.load_resume_state()
        if initial_downloaded is None:
            if not self.prepare(): return
            initial_downloaded = 0

        print("\n" * (self.worker_count + 1))
        
        try:
            with tqdm(total=self.total_size, initial=initial_downloaded, unit='B', unit_scale=True, 
                      desc="TOTAL", position=0, leave=True) as main_bar:
                
                self.main_bar = main_bar

                with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                    list(executor.map(self.download_segment, range(len(self.segments))))

            # Final verification
            if all(s["finished"] for s in self.segments):
                print("\nDownload Complete. Merging file...")
                
                if os.path.exists(self.filename):
                    os.remove(self.filename)
                os.rename(self.temp_filename, self.filename)
                
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
                print(f"Success: {self.filename}")
            else:
                print("\nDownload incomplete (missing segments). Please try again.")

        except KeyboardInterrupt:
            print("\n\nDownload stopped by user. Progress saved, can be resumed.")
            self.save_state() 
            sys.exit(0)
