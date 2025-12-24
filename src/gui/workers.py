import sys

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
        """Run yt-dlp analysis in a subprocess to avoid Python GIL + QThread blocking issues."""
        try:
            print(f"🔍 AnalysisWorker.run() started for {self.url}")
            sys.stdout.flush()

            import json
            import os
            import subprocess

            print("📡 Calling yt-dlp via subprocess (fixes QThread blocking for YouTube)...")
            sys.stdout.flush()

            # Create Python script to run in subprocess
            script = f"""
import json
import sys
sys.path.insert(0, '.')
from src.core.downloader import Downloader

try:
    d = Downloader('{self.url}', proxy_config={self.proxy_config})
    info = d.fetch_video_info()
    
    if info:
        # Extract JSON-serializable fields only
        result = {{
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'formats': info.get('formats', []),
            'url': info.get('url'),
            'ext': info.get('ext'),
        }}
        print(json.dumps(result))
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
"""

            # CRITICAL: Pass environment variables including DENO path
            env = os.environ.copy()
            deno_path = os.path.expanduser("~/.deno/bin")
            if os.path.exists(deno_path):
                env["PATH"] = f"{deno_path}:{env.get('PATH', '')}"
                env["DENO_INSTALL"] = os.path.expanduser("~/.deno")

            # Run subprocess with timeout (increased for YouTube web client)
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=120,  # YouTube web client can take 60-90s
                cwd=".",
                env=env,  # Pass environment with deno path
            )

            print(f"📦 subprocess: code={result.returncode}, stdout={len(result.stdout)} chars, stderr={len(result.stderr)} chars")
            sys.stdout.flush()

            if result.stderr:
                print(f"⚠️ subprocess stderr: {result.stderr[:500]}")
                sys.stdout.flush()

            if result.returncode == 0 and result.stdout.strip():
                try:
                    info = json.loads(result.stdout.strip())
                    print(f"✅ Got {len(info.get('formats', []))} formats, emitting signal")
                    sys.stdout.flush()
                    self.finished.emit(info)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON error: {e}, stdout: {result.stdout[:200]}")
                    sys.stdout.flush()
                    self.error.emit(f"Invalid response format")
            else:
                error = result.stderr[:300] if result.stderr else "Analysis failed"
                print(f"⚠️ Subprocess failed: {error}")
                sys.stdout.flush()
                self.error.emit(error)

        except subprocess.TimeoutExpired:
            print("⏱️ Timeout after 45s")
            sys.stdout.flush()
            self.error.emit("Analysis timeout. URL may not be supported or network is slow.")
        except Exception as e:
            print(f"❌ Exception: {e}")
            sys.stdout.flush()
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
