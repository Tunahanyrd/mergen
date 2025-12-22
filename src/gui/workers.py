from PySide6.QtCore import QThread, Signal
from src.core.downloader import Downloader

class AnalysisWorker(QThread):
    """
    Background worker to fetch video metadata via yt-dlp.
    Used for pre-download analysis (Format Selector).
    """
    finished = Signal(object)  # Returns info dict or None
    error = Signal(str)        # Returns error message

    def __init__(self, url, proxy_config=None):
        super().__init__()
        self.url = url
        self.proxy_config = proxy_config
        
    def run(self):
        try:
            # Initialize minimal downloader just for fetching info
            d = Downloader(self.url, proxy_config=self.proxy_config)
            # This method (added in v0.9.0) uses yt-dlp extract_info(download=False)
            info = d.fetch_video_info()
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))
