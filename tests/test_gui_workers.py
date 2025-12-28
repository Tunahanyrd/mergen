# Mock Worker needs QObject
from src.gui.workers import AnalysisWorker, ThumbnailWorker


def test_analysis_worker_success(mocker, qtbot):
    worker = AnalysisWorker("http://example.com/video")

    # Mock subprocess.run
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = '{"title": "Test Video", "formats": []}'

    with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
        worker.run()

    result = blocker.args[0]
    assert result["title"] == "Test Video"


def test_analysis_worker_failure(mocker, qtbot):
    worker = AnalysisWorker("http://invalid.url")

    # Mock subprocess.run to verify error handling
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "Download Failure"

    with qtbot.waitSignal(worker.error, timeout=5000) as blocker:
        worker.run()

    assert "Download Failure" in blocker.args[0]


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
