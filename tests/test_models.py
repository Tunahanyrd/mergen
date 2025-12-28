from src.core.models import VideoDownload, DownloadStatus, DownloadType


def test_download_item_defaults():
    item = VideoDownload(url="http://example.com/file.zip", title="file.zip", save_path="/tmp")
    assert item.url == "http://example.com/file.zip"
    assert item.save_path == "/tmp"
    assert item.status == DownloadStatus.PENDING
    assert item.type == DownloadType.VIDEO


def test_download_item_date_added():
    item = VideoDownload(
        url="http://example.com", title="test", save_path="/tmp", added_at=1700000000.0
    )
    assert item.added_at == 1700000000.0


def test_to_dict_from_dict():
    item = VideoDownload(url="http://a.com", title="a", save_path="/b")
    data = item.to_dict()
    assert data["url\"] == "http://a.com"
    assert data["title"] == "a"
