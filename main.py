#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mergen - High-performance download manager.

Python 3.13 optimization enabled:
- JIT compiler support
- 64-thread concurrent downloads
- Network resilience
"""

import argparse
import difflib
import os
import signal
import sys

from PySide6.QtWidgets import QApplication

# Fix Qt portal warning by setting proper app ID
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "qt6ct")
os.environ.setdefault("DESKTOP_STARTUP_ID", "mergen.desktop")

# Enable JIT compiler for Python 3.13+ (experimental)
if sys.version_info >= (3, 13):
    os.environ.setdefault("PYTHON_JIT", "1")


class MergenParser(argparse.ArgumentParser):
    """Custom parser to provide suggestions for typos."""

    def error(self, message):
        # Look for the last argument if it seems like a flag
        invalid_arg = sys.argv[-1] if sys.argv[-1].startswith("-") else None

        if invalid_arg:
            valid_options = [opt for action in self._actions for opt in action.option_strings]
            suggestion = difflib.get_close_matches(invalid_arg, valid_options, n=1, cutoff=0.6)

            if suggestion:
                message = f"{message}\n💡 Did you mean: '{suggestion[0]}'?"

        super().error(message)


def setup_environment(args):
    """Handle Python optimizations and logging levels."""
    if args.no_jit:
        os.environ.pop("PYTHON_JIT", None)

    if args.verbose:
        os.environ["MERGEN_VERBOSE"] = "1"
        print("🔊 Verbose mode enabled")

        if sys.version_info >= (3, 13):
            jit_enabled = os.environ.get("PYTHON_JIT") == "1"
            print(f"⚡ Python 3.{sys.version_info.minor}.{sys.version_info.micro}")
            print(f"   JIT: {'Enabled' if jit_enabled else 'Disabled'}")


def main():
    """Main entry point with Python 3.13 optimizations."""
    from src.core.version import get_version_string
    from src.gui.main_window import MainWindow

    parser = MergenParser(description="Mergen Download Manager")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging (yt-dlp output, debug messages)"
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--no-jit", action="store_true", help="Disable JIT compiler (Python 3.13+)")

    args = parser.parse_args()

    if args.version:
        print(f"Mergen {get_version_string()}")
        return

    # Apply optimizations and environment settings
    setup_environment(args)

    # Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Mergen")
    app.setOrganizationName("Tunahanyrd")
    app.setDesktopFileName("mergen")

    # Main Window
    window = MainWindow()
    window.show()

    # Cleanup on exit
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
