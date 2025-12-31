"""
Test aria2 downloader integration
"""

import asyncio
from pathlib import Path

from src.core.aria2_downloader import Aria2Downloader
from src.core.logger import get_logger

logger = get_logger(__name__)


async def test_download():
    """Test downloading a video"""

    # Test with a short YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Never Gonna Give You Up
    output_path = Path("/tmp/mergen_test.mp4")

    downloader = Aria2Downloader()

    def progress_callback(status):
        """Print progress updates"""
        if "downloadSpeed" in status:
            speed = int(status.get("downloadSpeed", 0))
            completed = int(status.get("completedLength", 0))
            total = int(status.get("totalLength", 1))
            pct = (completed / total * 100) if total > 0 else 0

            speed_mb = speed / 1_000_000
            logger.info(f"📊 Progress: {pct:.1f}% - Speed: {speed_mb:.2f} MB/s")

    try:
        logger.info(f"🎬 Testing download: {test_url}")
        logger.info(f"💾 Output: {output_path}")

        success = await downloader.download(url=test_url, output_path=output_path, progress_callback=progress_callback)

        if success:
            logger.info(f"✅ Test successful! File: {output_path}")
            if output_path.exists():
                size_mb = output_path.stat().st_size / 1_000_000
                logger.info(f"📁 File size: {size_mb:.2f} MB")
        else:
            logger.error("❌ Test failed")

    finally:
        downloader.stop_aria2_daemon()


if __name__ == "__main__":
    asyncio.run(test_download())
