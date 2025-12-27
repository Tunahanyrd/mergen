#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mergen Download Manager
Main entry point with verbose mode support
"""

import argparse
import os
import signal
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.core.version import get_version_string
from src.gui.main_window import MainWindow

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        prog="mergen",
        description="Mergen - Modern download manager with browser integration and stream support",
        epilog="Homepage: https://github.com/Tunahanyrd/mergen",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=get_version_string(),
        help="Show version information",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    args = parser.parse_args()

    # Set verbose mode
    if args.verbose:
        os.environ["MERGEN_VERBOSE"] = "1"
        print("🔊 Verbose mode enabled")

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)

    # Set application-wide icon (all windows inherit this)
    icon_path = "data/mergen.png"
    if hasattr(sys, "_MEIPASS"):
        # Nuitka/PyInstaller compiled mode
        icon_path = os.path.join(sys._MEIPASS, "data", "mergen.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply theme
    from src.gui.styles import MERGEN_THEME

    app.setStyleSheet(MERGEN_THEME)

    # Initialize language BEFORE creating UI
    from src.core.config import ConfigManager
    from src.core.i18n import I18n

    config = ConfigManager()
    lang = config.get("language", I18n.detect_os_lang())  # Respect system locale
    I18n.set_language(lang)

    # Now create main window with correct language
    window = MainWindow()

    # Start browser integration server
    from src.core.browser_integration import start_http_server

    start_http_server(window, port=8765)

    window.show()

    sys.exit(app.exec())
