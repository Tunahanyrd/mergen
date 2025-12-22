# Mock Worker needs QObject
from src.gui.workers import AnalysisWorker, ThumbnailWorker


def test_analysis_worker_success(mocker, qtbot):
    worker = AnalysisWorker("http://example.com/video")

    # Mock Downloader class used in workers.py
    mock_downloader_cls = mocker.patch("src.gui.workers.Downloader")
    mock_instance = mock_downloader_cls.return_value
    mock_instance.fetch_video_info.return_value = {
        "title": "Test Video",
        "formats": [{"format_id": "18", "ext": "mp4"}],
    }

    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()

    assert blocker.args[0]["title"] == "Test Video"


def test_analysis_worker_failure(mocker, qtbot):
    worker = AnalysisWorker("http://invalid.url")

    mock_downloader_cls = mocker.patch("src.gui.workers.Downloader")
    mock_instance = mock_downloader_cls.return_value
    mock_instance.fetch_video_info.side_effect = Exception("Download Error")

    with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
        worker.run()

    assert "Download Error" in blocker.args[0]


def test_thumbnail_worker(mocker, qtbot):
    worker = ThumbnailWorker("http://example.com/thumb.jpg")

    # Mock requests.get
    mock_get = mocker.patch("requests.get")
    mock_resp = mocker.Mock()
    mock_resp.status_code = 200
    mock_resp.content = b"fake_image_data"
    mock_get.return_value = mock_resp

    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()

    assert blocker.args[0] == b"fake_image_data"
