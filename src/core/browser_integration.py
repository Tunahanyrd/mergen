"""
Browser Integration - HTTP + WebSocket Server
Receives downloads from native messaging host and browser extension.
"""

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import websockets

from src.core.logger import get_logger
from src.core.version import __version__

logger = get_logger(__name__)


class MergenHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for browser extension integration."""

    # Reference to main window (set from main.py)
    main_window = None

    def log_message(self, format, *args):
        """Suppress default HTTP server logs."""
        pass

    def do_POST(self):
        """Handle POST requests from browser extension."""
        if self.path == "/register":
            self.handle_register()
        elif self.path == "/add_download":
            self.handle_add_download()
        else:
            self.send_error(404)

    def handle_register(self):
        """Auto-register browser extension (zero-config setup)."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            ext_id = data.get("extension_id", "")
            browser = data.get("browser", "unknown")

            if not ext_id:
                self.send_error(400, "Missing extension_id")
                return

            logger.info(f"Auto-register request: {browser} extension {ext_id[:16]}...")

            # Create native messaging manifests
            import shutil
            import sys
            from pathlib import Path

            # Install native host script
            if hasattr(sys, "_MEIPASS"):
                src = Path(sys._MEIPASS) / "native-host/mergen-native-host.py"
            else:
                src = Path(__file__).parent.parent.parent / "native-host/mergen-native-host.py"

            if not src.exists():
                src = Path.cwd() / "native-host/mergen-native-host.py"

            dst = Path.home() / "bin/mergen-native-host.py"
            dst.parent.mkdir(parents=True, exist_ok=True)

            if src.exists():
                shutil.copy2(src, dst)
                dst.chmod(0o755)

            # Chrome manifest
            chrome_dir = Path.home() / ".config/google-chrome/NativeMessagingHosts"
            chrome_dir.mkdir(parents=True, exist_ok=True)
            (chrome_dir / "com.tunahanyrd.mergen.json").write_text(
                json.dumps(
                    {
                        "name": "com.tunahanyrd.mergen",
                        "description": "Mergen Native Host",
                        "path": str(dst),
                        "type": "stdio",
                        "allowed_origins": [f"chrome-extension://{ext_id}/"],
                    },
                    indent=2,
                )
            )

            # Firefox manifest
            ff_dir = Path.home() / ".mozilla/native-messaging-hosts"
            ff_dir.mkdir(parents=True, exist_ok=True)
            (ff_dir / "com.tunahanyrd.mergen.json").write_text(
                json.dumps(
                    {
                        "name": "com.tunahanyrd.mergen",
                        "description": "Mergen Native Host",
                        "path": str(dst),
                        "type": "stdio",
                        "allowed_origins": [f"moz-extension://{ext_id}/"],
                    },
                    indent=2,
                )
            )

            # Success response
            response = {"status": "success", "browser": browser, "app_version": __version__}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

            logger.info(f"Extension registered: {browser}")

        except Exception as e:
            logger.error(f"Registration failed: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def handle_add_download(self):
        """Handle download request from browser extension or native host."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            request_type = data.get("type", "add_download")  # NEW: support both formats

            # NEW: Handle URL download (simplified approach)
            if request_type == "download_url":
                url = data.get("url", "")
                filename = data.get("pageTitle", "")  # Use pageTitle as filename for download_url
                # page_url = data.get("pageUrl", "") # Not used currently
            else:  # Original add_download logic
                url = data.get("url", "")
                filename = data.get("filename", "")
            stream_type = data.get("stream_type", "direct")

            # NEW: Support simplified download_url format
            if request_type == "download_url":
                # For URL downloads, use page title as suggested name
                if filename:
                    # Clean up page title
                    for suffix in [" - YouTube", " • Instagram", " on Twitter", " / X"]:
                        filename = filename.replace(suffix, "")
                    filename = filename.strip()

            if not url:
                self.send_error(400, "Missing url parameter")
                return

            logger.info(f"{'URL' if request_type == 'download_url' else 'Direct'} download: {url}")

            # Wake main window if minimized
            if self.main_window:
                from PySide6.QtCore import QMetaObject, Qt

                QMetaObject.invokeMethod(self.main_window, "show", Qt.ConnectionType.QueuedConnection)
                QMetaObject.invokeMethod(self.main_window, "raise_", Qt.ConnectionType.QueuedConnection)
                QMetaObject.invokeMethod(self.main_window, "activateWindow", Qt.ConnectionType.QueuedConnection)

                # Add download (yt-dlp will handle format detection for URLs)
                QMetaObject.invokeMethod(
                    self.main_window.download_manager,
                    "add_download",
                    Qt.ConnectionType.QueuedConnection,
                    url,
                    filename or "",
                )
                logger.info(f"✅ Download added: {url}")

            # Send success response
            response = {"status": "success", "message": "Download added", "stream_type": stream_type}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            logger.error(f"Browser integration error: {e}")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def do_GET(self):
        """Handle GET requests (health check)."""
        if self.path == "/health" or self.path == "/":
            response = {"status": "ok", "app": "Mergen", "version": __version__}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())


def start_http_server(main_window, port=8765):
    """
    Start HTTP server for browser integration.

    Args:
        main_window: Reference to MainWindow instance
        port: Port number (default: 8765)
    """
    MergenHTTPHandler.main_window = main_window

    try:
        server = HTTPServer(("localhost", port), MergenHTTPHandler)

        # Run server in daemon thread
        server_thread = threading.Thread(target=server.serve_forever, daemon=True, name="BrowserIntegrationServer")
        server_thread.start()

        logger.info(f"Browser integration server started on http://localhost:{port}")
        return server

    except Exception as e:
        logger.error(f"Failed to start browser integration server: {e}")
        return None


# WebSocket server for faster communication
_ws_server = None
_ws_main_window = None


async def handle_websocket(websocket, path):
    """Handle WebSocket connections from browser extension."""
    global _ws_main_window

    remote_addr = websocket.remote_address
    logger.info(f"WebSocket connected from {remote_addr}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action", "")

                if action == "ping":
                    # Health check
                    await websocket.send(json.dumps({"status": "ok", "app": "Mergen", "version": __version__}))

                elif action == "register":
                    # Extension registration (same as HTTP)
                    ext_id = data.get("extension_id", "")
                    browser = data.get("browser", "unknown")
                    logger.info(f"WebSocket register: {browser} {ext_id[:16]}...")

                    # TODO: Create native messaging manifests (same as HTTP handler)
                    await websocket.send(
                        json.dumps({"status": "success", "browser": browser, "app_version": __version__})
                    )

                elif action == "add_download":
                    # Download request (legacy path, direct file download)
                    url = data.get("url", "")
                    filename = data.get("filename", "")
                    stream_type = data.get("stream_type", "direct")

                    logger.debug(f"WebSocket download: {url[:80]}...")

                    # Emit signal to main window
                    if _ws_main_window and hasattr(_ws_main_window, "browser_download_signal"):
                        # Auto-wake window
                        if _ws_main_window.isHidden() or _ws_main_window.isMinimized():
                            logger.debug("Auto-wake via WebSocket")
                            _ws_main_window.show()
                            _ws_main_window.raise_()
                            _ws_main_window.activateWindow()

                        _ws_main_window.browser_download_signal.emit(url, filename)

                        if stream_type in ["hls", "dash"]:
                            logger.info(f"WebSocket: {stream_type.upper()} stream detected")

                    await websocket.send(
                        json.dumps({"status": "success", "message": "Download added", "stream_type": stream_type})
                    )

                else:
                    await websocket.send(json.dumps({"status": "error", "message": f"Unknown action: {action}"}))

            except json.JSONDecodeError as e:
                logger.error(f"WebSocket JSON error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON"}))

            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send(json.dumps({"status": "error", "message": str(e)}))

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket disconnected: {remote_addr}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


def start_websocket_server(main_window, port=8765):
    """
    Start WebSocket server for browser extension (faster than HTTP).

    Args:
        main_window: Reference to MainWindow instance
        port: Port number (default: 8765, same as HTTP)
    """
    global _ws_server, _ws_main_window

    _ws_main_window = main_window

    def run_server():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def serve():
                global _ws_server
                _ws_server = await websockets.serve(handle_websocket, "localhost", port + 1)  # 8766
                logger.info(f"WebSocket server started on ws://localhost:{port + 1}")
                await _ws_server.wait_closed()

            loop.run_until_complete(serve())

        except Exception as e:
            logger.error(f"WebSocket server failed: {e}")

    # Run in daemon thread
    ws_thread = threading.Thread(target=run_server, daemon=True, name="WebSocketServer")
    ws_thread.start()

    return ws_thread


def start_browser_integration(main_window, port=8765):
    """
    Start both HTTP and WebSocket servers for browser integration.

    Args:
        main_window: Reference to MainWindow instance
        port: Base port number (HTTP on port, WebSocket on port+1)

    Returns:
        tuple: (http_server, ws_thread)
    """
    # Start HTTP server (backward compatibility)
    http_server = start_http_server(main_window, port)

    # Start WebSocket server (faster communication)
    ws_thread = start_websocket_server(main_window, port)

    logger.info("Browser integration ready (HTTP + WebSocket)")

    return http_server, ws_thread
