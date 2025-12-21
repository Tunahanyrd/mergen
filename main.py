#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on December 20, 2025 19:43:23

@author: tunahan
"""

import os
import sys

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.svg.warning=false;qt.qpa.services=false"
import signal

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow

if __name__ == "__main__":
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
    lang = config.get("language", "tr")  # Default to Turkish
    I18n.set_language(lang)

    # Now create main window with correct language
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
