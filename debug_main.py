#!/usr/bin/env python3
"""
Test browser integration + analysis flow
"""
import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.core.browser_integration import start_http_server

if __name__ == "__main__":
    print("🚀 Starting Mergen with debug output...")
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    # Start browser integration server
    print("🌐 Starting HTTP server on port 8765...")
    start_http_server(window, port=8765)
    
    window.show()
    
    print("✅ Mergen ready. Send a URL from browser extension.")
    print("   Watch this terminal for debug output.")
    
    sys.exit(app.exec())
