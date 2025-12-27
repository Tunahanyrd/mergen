# -*- coding: utf-8 -*-
"""
Playlist Choice Dialog
Asks user if they want to download single video or full playlist.
"""

from src.core.i18n import I18n
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class PlaylistChoiceDialog(QDialog):
    """
    Dialog to ask user: Single video or full playlist?
    Shown when playlist URL is detected.
    """

    def __init__(self, playlist_title, video_count, parent=None):
        super().__init__(parent)
        self.playlist_title = playlist_title
        self.video_count = video_count
        self.choice = None  # "single" or "playlist"

        self.setWindowTitle(I18n.get("playlist_detected"))
        self.setModal(True)
        self.setMinimumWidth(450)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Icon + Title
        header = QHBoxLayout()

        icon_label = QLabel("🎵")
        icon_label.setStyleSheet("font-size: 32px;")
        header.addWidget(icon_label)

        from src.core.i18n import I18n

        title_label = QLabel(I18n.get("playlist_detected"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Playlist info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # Title
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel(f"<b>{I18n.get('playlist_title_label')}</b>"))
        playlist_title_label = QLabel(self.playlist_title)
        playlist_title_label.setWordWrap(True)
        title_row.addWidget(playlist_title_label, 1)
        info_layout.addLayout(title_row)

        # Video count
        count_row = QHBoxLayout()
        count_row.addWidget(QLabel(f"<b>{I18n.get('video_count_label')}</b>"))
        count_row.addWidget(QLabel(str(self.video_count)))
        count_row.addStretch()
        info_layout.addLayout(count_row)

        layout.addLayout(info_layout)

        # Question
        question = QLabel(I18n.get("what_download"))
        question.setStyleSheet("margin-top: 10px; font-size: 13px; color: #888;")
        layout.addWidget(question)

        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        # Single video button
        self.single_btn = QPushButton(I18n.get("single_video"))
        self.single_btn.setMinimumHeight(50)
        self.single_btn.setStyleSheet(
            """
            QPushButton {
                background: #2a2a2a;
                border: 2px solid #444;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #333;
                border-color: #00f2ff;
            }
        """
        )
        self.single_btn.clicked.connect(self.choose_single)
        btn_layout.addWidget(self.single_btn)

        # Full playlist button
        count_str = f"({self.video_count} videos)" if self.video_count else I18n.get("unknown_count")
        playlist_text = f"{I18n.get('full_playlist')} {count_str}"
        self.playlist_btn = QPushButton(playlist_text)
        self.playlist_btn.setMinimumHeight(50)
        self.playlist_btn.setStyleSheet(
            """
            QPushButton {
                background: #1a4d5e;
                border: 2px solid #00a8cc;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                color: #00f2ff;
            }
            QPushButton:hover {
                background: #235d70;
                border-color: #00f2ff;
            }
        """
        )
        self.playlist_btn.clicked.connect(self.choose_playlist)
        btn_layout.addWidget(self.playlist_btn)

        layout.addLayout(btn_layout)

        # Warning
        warning = QLabel(I18n.get("playlist_analysis_warning"))
        warning.setStyleSheet(
            """
            color: #ff9800;
            font-size: 11px;
            padding: 10px;
            background: rgba(255, 152, 0, 0.1);
            border-radius: 4px;
            border-left: 3px solid #ff9800;
        """
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)

    def choose_single(self):
        """User chose single video."""
        self.choice = "single"
        self.accept()

    def choose_playlist(self):
        """User chose full playlist."""
        self.choice = "playlist"
        self.accept()

    def get_choice(self):
        """Returns 'single' or 'playlist' or None if cancelled."""
        return self.choice
