#!/home/tunahan/miniconda3/envs/ml_env/bin/python
# -*- coding: utf-8 -*-
"""
Created on December 20, 2025 19:43:23

@author: tunahan
"""
import os
import sys

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.svg.warning=false;qt.qpa.services=false"
import signal

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)

    # Optional: Set global style/palette here to look more 'premium' or dark mode
    # For now, using default system style

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
