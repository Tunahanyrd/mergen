import importlib.util
import io
import json
import struct
import sys
from pathlib import Path

# Load mergen-native-host.py dynamically
native_host_path = Path(__file__).parent.parent / "native-host" / "mergen-native-host.py"
spec = importlib.util.spec_from_file_location("mergen_native_host", native_host_path)
native_host = importlib.util.module_from_spec(spec)
sys.modules["mergen_native_host"] = native_host
spec.loader.exec_module(native_host)


class MockStdin:
    def __init__(self, buffer_io):
        self.buffer = buffer_io


def test_ping_response(monkeypatch, capsys):
    # Prepare input
    msg = json.dumps({"action": "ping"}).encode("utf-8")
    data = struct.pack("I", len(msg)) + msg
    mock_stdin_buffer = io.BytesIO(data)

    # Replace native_host.sys.stdin with our mock
    # Note: we need to replace the stdin accessed by native_host
    # Since native_host uses `sys.stdin.buffer`, we provide an object with that attribute
    monkeypatch.setattr(native_host.sys, "stdin", MockStdin(mock_stdin_buffer))

    # Replace stdout as well to capture binary output
    # native_host uses sys.stdout.buffer
    mock_stdout_buffer = io.BytesIO()
    monkeypatch.setattr(native_host.sys, "stdout", MockStdin(mock_stdout_buffer))

    # Test read_message
    assert native_host.read_message() == {"action": "ping"}

    # Test send_message
    native_host.send_message({"status": "success"})

    mock_stdout_buffer.seek(0)
    length_data = mock_stdout_buffer.read(4)
    length = struct.unpack("I", length_data)[0]
    content = mock_stdout_buffer.read(length).decode("utf-8")
    assert json.loads(content) == {"status": "success"}


def test_add_download(mocker):
    # Mock urllib.request.urlopen since we replaced requests with urllib
    mock_response = mocker.MagicMock()
    mock_response.status = 200
    mock_response.__enter__ = mocker.MagicMock(return_value=mock_response)
    mock_response.__exit__ = mocker.MagicMock(return_value=False)

    mock_urlopen = mocker.patch("urllib.request.urlopen", return_value=mock_response)

    res = native_host.send_to_mergen("http://example.com", "file.mp4", "direct")

    assert res["status"] == "success"
    mock_urlopen.assert_called_once()

    # Verify the request was made correctly
    call_args = mock_urlopen.call_args
    request_obj = call_args[0][0]  # First positional arg is the Request object
    assert request_obj.full_url == "http://localhost:8765/add_download"
