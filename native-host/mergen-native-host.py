#!/usr/bin/env python3
"""
Mergen Native Messaging Host
Receives download requests from browser extension via stdio.
Sends to Mergen app via HTTP.
"""

import json
import logging
import struct
import sys

# Setup logging
from pathlib import Path

log_file = Path.home() / ".mergen-native-host.log"
logging.basicConfig(filename=str(log_file), level=logging.DEBUG, format="%(asctime)s - %(message)s")

MERGEN_HTTP_URL = "http://localhost:8765/add_download"


def send_message(message):
    """Send message to extension (JSON via stdout)."""
    try:
        encoded = json.dumps(message).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("I", len(encoded)))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
        logging.info(f"→ Extension: {message}")
    except Exception as e:
        logging.error(f"Error sending: {e}")


def read_message():
    """Read message from extension (JSON via stdin)."""
    try:
        text_length_bytes = sys.stdin.buffer.read(4)
        if len(text_length_bytes) == 0:
            sys.exit(0)

        text_length = struct.unpack("I", text_length_bytes)[0]
        text = sys.stdin.buffer.read(text_length).decode("utf-8")
        message = json.loads(text)

        logging.info(f"← Extension: {message}")
        return message
    except Exception as e:
        logging.error(f"Error reading: {e}")
        return None


def send_to_mergen(url, filename, stream_type="direct"):
    """Send download to Mergen app via HTTP."""
    try:
        import urllib.error
        import urllib.request

        payload = {
            "url": url,
            "filename": filename,
            "stream_type": stream_type,  # NEW: hls, dash, mp4, ts, mp3, direct
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(MERGEN_HTTP_URL, data=data, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                logging.info(f"✅ Mergen [{stream_type}]: {url}")
                return {"status": "success", "message": "Added to Mergen"}
            else:
                return {"status": "error", "message": f"HTTP {response.status}"}

    except urllib.error.URLError as e:
        # Mergen is not running - try to start it
        logging.warning(f"Mergen not running, attempting to start it...")
        
        if try_start_mergen():
            # Wait a bit for Mergen to start
            import time
            time.sleep(2)
            
            # Retry sending
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(MERGEN_HTTP_URL, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status == 200:
                        logging.info(f"✅ Mergen started and received [{stream_type}]: {url}")
                        return {"status": "success", "message": "Mergen started, download added"}
            except Exception:
                pass
        
        logging.error(f"Connection error: {e}")
        return {"status": "error", "message": f"Mergen not running. Please start Mergen app."}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}


def try_start_mergen():
    """Try to start Mergen application."""
    import subprocess
    import os
    
    try:
        # Try different methods to start Mergen
        if os.name == 'posix':  # Linux/macOS
            # Try desktop file first (most reliable)
            try:
                subprocess.Popen(['gtk-launch', 'mergen.desktop'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                logging.info("Started Mergen via gtk-launch")
                return True
            except Exception:
                pass
            
            # Try direct command
            try:
                subprocess.Popen(['mergen'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                logging.info("Started Mergen via direct command")
                return True
            except Exception:
                pass
                
        logging.warning("Could not start Mergen automatically")
        return False
    except Exception as e:
        logging.error(f"Error starting Mergen: {e}")
        return False


def main():
    """Main loop."""
    logging.info("=" * 50)
    logging.info("Mergen Native Host Started")
    logging.info("=" * 50)

    try:
        while True:
            message = read_message()
            if not message:
                continue

            action = message.get("action")

            if action == "add_download":
                url = message.get("url", "")
                filename = message.get("filename", "")
                stream_type = message.get("stream_type", "direct")  # NEW
                result = send_to_mergen(url, filename, stream_type)
                send_message(result)

            elif action in ["ping", "test_connection"]:
                # Do NOT send to Mergen, just reply to extension
                send_message({"status": "success", "message": "Pong"})

            else:
                send_message({"status": "error", "message": "Unknown action"})

    except KeyboardInterrupt:
        logging.info("Interrupted")
    except Exception as e:
        logging.error(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
