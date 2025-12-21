from src.core.models import DownloadItem


def test_download_item_defaults():
    item = DownloadItem(url="http://example.com/file.zip", filename="file.zip", save_path="/tmp")
    assert item.status == "Pending"
    assert item.size == "Unknown"
    assert item.total_bytes == 0
    assert item.downloaded_bytes == 0


def test_download_item_date_added():
    item = DownloadItem(url="http://example.com", filename="test", save_path="/tmp", added_at=1700000000.0)
    # Check simple formatting
    assert "2023" in item.date_added


def test_to_dict_from_dict():
    item = DownloadItem(url="http://a.com", filename="a", save_path="/b")
    item.status = "Done"
    data = item.to_dict()
    assert data["url"] == "http://a.com"
    assert data["status"] == "Done"

    item2 = DownloadItem.from_dict(data)
    assert item2.url == item.url
    assert item2.filename == item.filename
