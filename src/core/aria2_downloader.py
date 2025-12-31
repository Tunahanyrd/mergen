"""
aria2 Download Wrapper - Combines yt-dlp extraction with aria2 downloading

Flow:
1. yt-dlp subprocess extracts best format URL
2. aria2c downloads the file with RPC enabled
3. Aria2Monitor optimizes in real-time
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional

import aiohttp

from src.core.aria2_monitor import Aria2Monitor
from src.core.logger import get_logger

logger = get_logger(__name__)


class Aria2Downloader:
    """
    Download manager using yt-dlp for extraction + aria2 for downloading.

    Architecture:
    - yt-dlp: Platform support, format selection, authentication
    - aria2c: Multi-threaded download, RPC control
    - Aria2Monitor: Dynamic optimization
    """

    def __init__(self, rpc_port: int = 6800, rpc_secret: str = "mergen_secret", max_connections: int = 16):
        self.rpc_port = rpc_port
        self.rpc_secret = rpc_secret
        self.max_connections = max_connections
        self.rpc_url = f"http://localhost:{rpc_port}/jsonrpc"
        self.monitor = Aria2Monitor(self.rpc_url, rpc_secret)
        self.aria2_process: Optional[subprocess.Popen] = None

    async def start_aria2_daemon(self):
        """Start aria2c in RPC daemon mode"""
        if self.aria2_process:
            logger.debug("aria2 daemon already running")
            return

        cmd = [
            "aria2c",
            "--enable-rpc",
            f"--rpc-listen-port={self.rpc_port}",
            f"--rpc-secret={self.rpc_secret}",
            "--rpc-listen-all=false",
            "--daemon=false",  # We'll manage the process
            f"--max-connection-per-server={self.max_connections}",
            f"--split={self.max_connections}",
            "--min-split-size=1M",
            "--max-concurrent-downloads=16",
            "--continue=true",
            "--auto-file-renaming=false",
            "--allow-overwrite=true",
            "--quiet=true",
        ]

        try:
            self.aria2_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for RPC to be ready
            await asyncio.sleep(1.0)
            logger.info(f"✅ aria2 RPC daemon started on port {self.rpc_port}")

        except Exception as e:
            logger.error(f"Failed to start aria2: {e}")
            raise

    def stop_aria2_daemon(self):
        """Stop aria2 daemon"""
        if self.aria2_process:
            self.aria2_process.terminate()
            self.aria2_process.wait(timeout=5)
            self.aria2_process = None
            logger.info("⏹️ aria2 daemon stopped")

    async def download(
        self, url: str, output_path: Path, format_id: str = "bestvideo+bestaudio/best", progress_callback=None
    ) -> bool:
        """
        Download using yt-dlp extraction + aria2 downloading.

        Args:
            url: Video/playlist URL
            output_path: Where to save the file
            format_id: yt-dlp format string
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Extract download URL using yt-dlp subprocess
            logger.info(f"🔍 Extracting format from: {url}")
            download_url = await self._extract_download_url(url, format_id)

            if not download_url:
                logger.error("Failed to extract download URL")
                return False

            logger.info(f"✅ Got direct URL: {download_url[:80]}...")

            # Step 2: Start aria2 daemon if not running
            await self.start_aria2_daemon()

            # Step 3: Start download via aria2 RPC
            gid = await self._start_aria2_download(download_url, output_path)

            if not gid:
                logger.error("Failed to start aria2 download")
                return False

            logger.info(f"📥 Download started with GID: {gid}")

            # Step 4: Monitor and optimize
            await self.monitor.start_monitoring(gid, callback=progress_callback)

            # Step 5: Wait for completion
            success = await self._wait_for_completion(gid)

            await self.monitor.stop_monitoring(gid)

            return success

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    async def _extract_download_url(self, url: str, format_id: str) -> Optional[str]:
        """
        Extract direct download URL using yt-dlp subprocess.

        Uses: yt-dlp -f {format} -g {url}
        The -g flag outputs the direct URL without downloading.
        """
        try:
            cmd = [
                "yt-dlp",
                "-f",
                format_id,
                "-g",  # Get URL only
                "--no-playlist",  # Single video for now
                url,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                direct_url = result.stdout.strip()
                return direct_url if direct_url else None
            else:
                logger.error(f"yt-dlp error: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("yt-dlp timed out")
            return None
        except Exception as e:
            logger.error(f"yt-dlp extraction failed: {e}")
            return None

    async def _start_aria2_download(self, url: str, output_path: Path) -> Optional[str]:
        """
        Start download via aria2 RPC.

        Returns:
            GID (download ID) if successful, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": "1",
                        "method": "aria2.addUri",
                        "params": [
                            f"token:{self.rpc_secret}",
                            [url],
                            {
                                "out": output_path.name,
                                "dir": str(output_path.parent),
                                "max-connection-per-server": str(self.max_connections),
                                "split": str(self.max_connections),
                                "continue": "true",
                            },
                        ],
                    },
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    data = await response.json()

                    if "result" in data:
                        return data["result"]  # GID
                    elif "error" in data:
                        logger.error(f"aria2 RPC error: {data['error']}")
                        return None

        except Exception as e:
            logger.error(f"Failed to start aria2 download: {e}")
            return None

    async def _wait_for_completion(self, gid: str, timeout: int = 3600) -> bool:
        """
        Wait for download to complete.

        Args:
            gid: Download GID
            timeout: Max wait time in seconds

        Returns:
            True if completed successfully
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Download timeout after {timeout}s")
                return False

            # Get status
            status = await self.monitor._get_status(gid)

            if not status:
                await asyncio.sleep(1)
                continue

            download_status = status.get("status", "")

            if download_status == "complete":
                logger.info(f"✅ Download complete: {gid}")
                return True
            elif download_status in ["error", "removed"]:
                logger.error(f"❌ Download {download_status}: {gid}")
                return False

            # Still downloading, wait
            await asyncio.sleep(1)
