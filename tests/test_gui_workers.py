# Mock Worker needs QObject
from src.gui.workers import AnalysisWorker, ThumbnailWorker


def test_analysis_worker_success(mocker, qtbot):
    worker = AnalysisWorker("http://example.com/video")

    # Mock fetch_video_info function
    mock_fetch = mocker.patch("src.gui.workers.fetch_video_info")
    mock_fetch.return_value = {"title": "Test Video", "formats": []}

    # Signals
    result = None

    def capture_result(r):
        nonlocal result
        result = r

    worker.result_signal.connect(capture_result)
    worker.run()

    assert result is not None
    assert result["title"] == "Test Video"


def test_analysis_worker_failure(mocker, qtbot):
    worker = AnalysisWorker("http://invalid.url")

    # Mock fetch_video_info to raise exception
    mock_fetch = mocker.patch("src.gui.workers.fetch_video_info")
    mock_fetch.side_effect = Exception("Failed to fetch")

    # Signals
    error = None

    def capture_error(e):
        nonlocal error
        error = e

    worker.error_signal.connect(capture_error)
    worker.run()

    assert error is not None
    assert "Failed to fetch" in str(error)


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
