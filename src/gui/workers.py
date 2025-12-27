from PySide6.QtCore import QThread, Signal


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
        """Fetch video info directly using yt-dlp (no subprocess needed)."""
        try:
            from src.core.downloader import Downloader

            # Create downloader instance
            downloader = Downloader(self.url, proxy_config=self.proxy_config)

            # Fetch video info
            info = downloader.fetch_video_info()

            if info:
                # Emit the info dict
                self.finished.emit(info)
            else:
                self.error.emit("Could not fetch video information")

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
