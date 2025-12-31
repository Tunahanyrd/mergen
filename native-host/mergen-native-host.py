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
        logging.warning("Mergen not running, attempting to start it...")

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
        return {"status": "error", "message": "Mergen not running. Please start Mergen app."}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}


def try_start_mergen():
    """Try to start Mergen application."""
    import os
    import subprocess

    try:
        # Try different methods to start Mergen
        if os.name == "posix":  # Linux/macOS
            # Try desktop file first (most reliable)
            try:
                subprocess.Popen(["gtk-launch", "mergen.desktop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("Started Mergen via gtk-launch")
                return True
            except Exception:
                pass

            # Try direct command
            try:
                subprocess.Popen(["mergen"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info("Started Mergen via direct command")
                return True
            except Exception:
                pass

        logging.warning("Could not start Mergen automatically")
        return False
    except Exception as e:
        logging.error(f"Error starting Mergen: {e}")
        return False


def handle_message(message):
    """
    Handle message from browser extension.
    
    Expected message format:
    {
        "action": "download_url",
        "url": "https://...",
        "pageTitle": "...",
        "pageUrl": "...",
        "favicon": "..."
    }
    """
    try:
        action = message.get("action")
        
        if action == "register_extension":
            # Auto-register extension ID (IDM-style)
            extension_id = message.get("extensionId")
            if not extension_id:
                return {"success": False, "error": "No extension ID provided"}
            
            # Update native host JSON file
            import os
            host_file = Path.home() / ".config" / "google-chrome" / "NativeMessagingHosts" / "com.tunahanyrd.mergen.json"
            
            # Also check chromium
            if not host_file.exists():
                host_file = Path.home() / ".config" / "chromium" / "NativeMessagingHosts" / "com.tunahanyrd.mergen.json"
            
            try:
                # Read current config
                if host_file.exists():
                    with open(host_file, 'r') as f:
                        config = json.load(f)
                else:
                    # Create default config
                    config = {
                        "name": "com.tunahanyrd.mergen",
                        "description": "Mergen Native Host",
                        "path": str(Path.home() / "bin" / "mergen-native-host.py"),
                        "type": "stdio",
                        "allowed_origins": []
                    }
                
                # Add extension ID if not already present
                origin = f"chrome-extension://{extension_id}/"
                if origin not in config.get("allowed_origins", []):
                    config.setdefault("allowed_origins", []).append(origin)
                    
                    # Write back
                    host_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(host_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    logging.info(f"✅ Registered extension ID: {extension_id}")
                    return {"success": True, "message": "Extension registered"}
                else:
                    logging.info(f"Extension ID already registered: {extension_id}")
                    return {"success": True, "message": "Already registered"}
                    
            except Exception as e:
                logging.error(f"Failed to update host file: {e}")
                return {"success": False, "error": f"Failed to register: {e}"}
        
        elif action == "download_url":
            url = message.get("url")
            page_title = message.get("pageTitle", "")
            
            if not url:
                return {"success": False, "error": "No URL provided"}
            
            # Clean filename from page title
            filename = page_title or "download"
            # Remove common suffixes
            for suffix in [" - YouTube", " | Twitter", " | Instagram"]:
                filename = filename.replace(suffix, "")
            
            # Send to Mergen
            result = send_to_mergen(url, filename)
            
            if result.get("status") == "success":
                return {"success": True}
            else:
                return {"success": False, "error": result.get("message", "Unknown error")}
        
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
            
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main loop for native messaging host."""
    logging.info("=" * 60)
    logging.info("🚀 Mergen Native Messaging Host started")
    logging.info("=" * 60)

    while True:
        try:
            message = read_message()
            if not message:
                continue

            # Handle the message and get response
            response = handle_message(message)

            # Send response back to extension
            if response:
                send_message(response)

        except Exception as e:
            logging.error(f"❌ Error in main loop: {e}")
            send_message({"status": "error", "success": False, "error": str(e)})


if __name__ == "__main__":
    main()
