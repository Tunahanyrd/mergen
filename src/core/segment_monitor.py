"""
IDM-Style Dynamic Segment Monitor

Monitors download segments in real-time and splits slow ones dynamically.
"""

import threading
import time
from typing import List, Dict, Optional


class SegmentMonitor:
    """
    Monitor download segments and perform IDM-style dynamic optimization.
    
    Features:
    - Real-time per-segment speed tracking
    - Detect slow segments (< 50% of average)
    - Split slow segments mid-download
    - Reassign to idle threads
    """
    
    def __init__(self, segments: List[Dict], lock: threading.Lock):
        """
        Initialize segment monitor.
        
        Args:
            segments: List of segment dicts from Downloader
            lock: Thread lock for safe access
        """
        self.segments = segments
        self.lock = lock
        self.segment_speeds: Dict[int, List[float]] = {}  # segment_index -> [speeds]
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self):
        """Start monitoring in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="SegmentMonitor"
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Main monitoring loop - runs every second"""
        last_check = {}  # segment_index -> (time, downloaded_bytes)
        
        while self.monitoring:
            time.sleep(1.0)  # Check every second
            
            with self.lock:
                # Calculate current speeds
                current_speeds = []
                
                for seg in self.segments:
                    if seg['finished']:
                        continue
                    
                    seg_idx = seg['index']
                    current_downloaded = seg['downloaded']
                    current_time = time.time()
                    
                    # Calculate speed since last check
                    if seg_idx in last_check:
                        prev_time, prev_downloaded = last_check[seg_idx]
                        time_diff = current_time - prev_time
                        
                        if time_diff > 0:
                            bytes_diff = current_downloaded - prev_downloaded
                            speed = bytes_diff / time_diff  # bytes/sec
                            
                            # Store speed
                            if seg_idx not in self.segment_speeds:
                                self.segment_speeds[seg_idx] = []
                            self.segment_speeds[seg_idx].append(speed)
                            
                            # Keep only last 5 readings
                            if len(self.segment_speeds[seg_idx]) > 5:
                                self.segment_speeds[seg_idx].pop(0)
                            
                            # Calculate average speed for this segment
                            avg_speed = sum(self.segment_speeds[seg_idx]) / len(self.segment_speeds[seg_idx])
                            current_speeds.append((seg_idx, avg_speed))
                    
                    last_check[seg_idx] = (current_time, current_downloaded)
                
                # Analyze and optimize
                if len(current_speeds) >= 2:
                    self._optimize_segments(current_speeds)
    
    def _optimize_segments(self, speeds: List[tuple]):
        """
        IDM-style optimization: Split slow segments.
        
        Args:
            speeds: List of (segment_index, avg_speed) tuples
        """
        # Calculate overall average speed
        total_speed = sum(s[1] for s in speeds)
        avg_speed = total_speed / len(speeds)
        
        if avg_speed == 0:
            return
        
        # Find slow segments (< 50% of average)
        slow_segments = [
            (idx, speed) for idx, speed in speeds
            if speed < avg_speed * 0.5 and speed > 0
        ]
        
        if not slow_segments:
            return
        
        # Count idle capacity (finished segments = available threads)
        finished_count = sum(1 for seg in self.segments if seg['finished'])
        max_workers = len(self.segments)  # Original worker count
        active_workers = len([seg for seg in self.segments if not seg['finished']])
        idle_capacity = max_workers - active_workers
        
        # Split slow segments if we have idle capacity
        for seg_idx, speed in slow_segments[:idle_capacity]:
            segment = next((s for s in self.segments if s['index'] == seg_idx), None)
            if segment:
                self._split_segment(segment)
    
    def _split_segment(self, segment: Dict) -> bool:
        """
        Split a segment in half (IDM technique).
        
        Args:
            segment: Segment dict to split
            
        Returns:
            True if split successful
        """
        # Check if segment is large enough to split
        remaining = (segment['end'] - segment['start'] + 1) - segment['downloaded']
        min_split_size = 1_000_000  # 1MB minimum
        
        if remaining < min_split_size * 2:
            return False
        
        # Calculate split point
        current_pos = segment['start'] + segment['downloaded']
        split_point = current_pos + (remaining // 2)
        
        # Create new segment for second half
        new_segment = {
            'index': len(self.segments),  # New index
            'start': split_point,
            'end': segment['end'],
            'downloaded': 0,
            'finished': False
        }
        
        # Adjust original segment's end
        segment['end'] = split_point - 1
        
        # Add new segment to list
        self.segments.append(new_segment)
        
        print(f"⚡ Split segment {segment['index']}: {remaining/1024/1024:.1f}MB → 2 segments")
        
        return True
