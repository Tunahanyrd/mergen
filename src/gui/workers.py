from PySide6.QtCore import QThread, Signal

from src.core.downloader import Downloader


class AnalysisWorker(QThread):
    """
    Background worker to fetch video metadata via yt-dlp.
    Used for pre-download analysis (Format Selector).
    """

    finished = Signal(object)  # Returns info dict or None
    error = Signal(str)  # Returns error message

    def __init__(self, url, proxy_config=None):
        super().__init__()
        self.url = url
        self.proxy_config = proxy_config

    def run(self):
        try:
            print(f"🔍 AnalysisWorker.run() started for {self.url}")
            # Initialize minimal downloader just for fetching info
            d = Downloader(self.url, proxy_config=self.proxy_config)
            # This method (added in v0.9.0) uses yt-dlp extract_info(download=False)
            info = d.fetch_video_info()
            
            if info:
                print(f"✅ AnalysisWorker got info, emitting finished signal")
                self.finished.emit(info)
            else:
                print(f"❌ AnalysisWorker got None, emitting error signal")
                self.error.emit("No video info available")
        except Exception as e:
            print(f"❌ AnalysisWorker exception: {e}")
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
