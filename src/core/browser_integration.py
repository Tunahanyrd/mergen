"""
Browser Integration HTTP Server
Receives downloads from native messaging host.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.core.version import __version__


class MergenHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for browser extension integration."""

    # Reference to main window (set from main.py)
    main_window = None

    def log_message(self, format, *args):
        """Suppress default HTTP server logs."""
        pass

    def do_POST(self):
        """Handle POST requests from native host."""
        if self.path == "/add_download":
            try:
                # Read request body
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))

                url = data.get("url", "")
                filename = data.get("filename", "")
                stream_type = data.get("stream_type", "direct")  # NEW: Support stream type detection

                # Emit signal to main window (thread-safe)
                if self.main_window and hasattr(self.main_window, "browser_download_signal"):
                    # Auto-wake: Show window if hidden/minimized
                    if self.main_window.isHidden() or self.main_window.isMinimized():
                        print("📱 Auto-wake: Restoring window for incoming download")
                        self.main_window.show()
                        self.main_window.raise_()
                        self.main_window.activateWindow()

                    self.main_window.browser_download_signal.emit(url, filename)

                    # Log stream type for debugging
                    if stream_type in ["hls", "dash"]:
                        print(f"🎬 Detected {stream_type.upper()} stream: {url[:80]}...")

                # Send success response
                response = {"status": "success", "message": "Download added", "stream_type": stream_type}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                # Send error response with better logging
                print(f"❌ Browser integration error: {e}")
                error_response = {"status": "error", "message": str(e)}
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())

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

        print(f"✅ Browser integration server started on http://localhost:{port}")
        return server

    except Exception as e:
        print(f"❌ Failed to start browser integration server: {e}")
        return None
