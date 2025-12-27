from PySide6.QtCore import QThread, Signal


class AnalysisWorker(QThread):
    """
    Background worker to fetch video metadata via yt-dlp.
    Used for pre-download analysis (Format Selector).
    """

    finished = Signal(object)  # Returns info dict or None
    error = Signal(str)  # Returns error message

    def __init__(self, url, proxy_config=None, no_playlist=True):
        super().__init__()
        self.url = url
        self.proxy_config = proxy_config
        self.no_playlist = no_playlist  # NEW: Control playlist analysis

    def run(self):
        """Fetch video info directly using yt-dlp (no subprocess needed)."""
        try:
            import subprocess
            import json
            import sys
            
            # Pure CLI subprocess for analysis
            cmd = ["yt-dlp", "-J"]
            
            # Conditional --no-playlist flag
            if self.no_playlist:
                cmd.append("--no-playlist")
                print("🔍 AnalysisWorker: Using --no-playlist (Fast Video Analysis)")
            else:
                print("📚 AnalysisWorker: Full Playlist Analysis Mode (No --no-playlist)")
            
            cmd.append(self.url)
            print(f"🚀 Running command: {' '.join(cmd)}")
            
            # Run subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode == 0 and result.stdout:
                # Parse JSON
                info = json.loads(result.stdout)
                
                # Extract key metadata
                result_dict = {
                    "title": info.get("title", "Unknown Title"),
                    "thumbnail": info.get("thumbnail"),
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader") or info.get("channel"),
                    "formats": info.get("formats", []),
                    "playlist_title": info.get("playlist_title"),
                    "playlist_count": info.get("playlist_count"),
                    "webpage_url_basename": info.get("webpage_url_basename"),
                }
                
                self.finished.emit(result_dict)
            else:
                self.error.emit(f"Analysis failed: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            self.error.emit("Analysis timeout (120s)")
        except json.JSONDecodeError as e:
            self.error.emit(f"JSON parse error: {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class ThumbnailWorker(QThread):
    """
    Background worker to fetch video thumbnail.
    """

    finished = Signal(bytes)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            import requests

            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                self.finished.emit(response.content)
        except Exception:
            pass
