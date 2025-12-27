"""
Quality Dialog v2.0 - Complete Redesign
Features: Audio-only mode, Playlist support, Quality badges, Enhanced format display
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.core.i18n import I18n
from src.gui.workers import ThumbnailWorker


class QualityDialogV2(QDialog):
    """
    Enhanced Quality Dialog with:
    - Audio-only mode
    - Playlist detection
    - Quality badges (BEST, 4K, HD, SD)
    - Smart recommendations
    """

    quality_selected = Signal(dict)

    def __init__(self, parent=None, video_info=None):
        super().__init__(parent)
        self.setWindowTitle(I18n.get("select_quality"))
        self.setMinimumSize(800, 600)
        self.video_info = video_info or {}
        self.all_formats = []

        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                color: #ffffff;
            }
            QRadioButton {
                color: #ffffff;
                font-size: 13px;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QPushButton#cancel {
                background-color: #3e3e42;
            }
            QPushButton#cancel:hover {
                background-color: #505056;
            }
            QTableWidget {
                background-color: #252526;
                gridline-color: #3e3e42;
                border: 1px solid #3e3e42;
                color: #cccccc;
            }
            QHeaderView::section {
                background-color: #333337;
                padding: 6px;
                border: 1px solid #3e3e42;
                color: #cccccc;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #094771;
            }
        """
        )

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Build UI
        self.setup_header()
        self.setup_playlist_info()
        self.setup_format_type_selector()
        self.setup_format_table()
        self.setup_buttons()

        # Load data
        if self.video_info:
            self.load_info(self.video_info)

    def setup_header(self):
        """Header with thumbnail and video info"""
        header_layout = QHBoxLayout()

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 90)
        self.thumb_label.setStyleSheet("background-color: #000; border: 1px solid #555; border-radius: 4px;")
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setText("🎬")
        header_layout.addWidget(self.thumb_label)

        # Info
        info_layout = QVBoxLayout()
        self.title_label = QLabel("Analyzing video...")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")

        self.meta_label = QLabel("--:-- • --")
        self.meta_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.meta_label)
        info_layout.addStretch()
        header_layout.addLayout(info_layout, 1)

        self.main_layout.addLayout(header_layout)

    def setup_playlist_info(self):
        """Playlist info banner (hidden by default)"""
        self.playlist_banner = QLabel()
        self.playlist_banner.setStyleSheet(
            """
            background-color: #2d2d30;
            border: 1px solid #007acc;
            border-radius: 4px;
            padding: 8px;
            color: #00d4ff;
            font-size: 12px;
        """
        )
        self.playlist_banner.hide()
        self.main_layout.addWidget(self.playlist_banner)

    def setup_format_type_selector(self):
        """Radio buttons for format type selection"""
        selector_layout = QHBoxLayout()

        label = QLabel("📂 Format Type:")
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        selector_layout.addWidget(label)

        self.format_type_group = QButtonGroup()

        self.video_audio_rb = QRadioButton("🎬 Video + Audio")
        self.audio_only_rb = QRadioButton("🎵 Audio Only")
        self.video_only_rb = QRadioButton("🎞️ Video Only")

        self.video_audio_rb.setChecked(True)

        # Connect signals
        self.video_audio_rb.toggled.connect(self.filter_formats)
        self.audio_only_rb.toggled.connect(self.filter_formats)
        self.video_only_rb.toggled.connect(self.filter_formats)

        self.format_type_group.addButton(self.video_audio_rb)
        self.format_type_group.addButton(self.audio_only_rb)
        self.format_type_group.addButton(self.video_only_rb)

        selector_layout.addWidget(self.video_audio_rb)
        selector_layout.addWidget(self.audio_only_rb)
        selector_layout.addWidget(self.video_only_rb)
        selector_layout.addStretch()

        self.main_layout.addLayout(selector_layout)

    def setup_format_table(self):
        """Format table with quality badges"""
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Quality", "Resolution", "Format", "Size", "Codec"])

        # Column sizes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        self.table.setColumnWidth(0, 100)  # Quality badge
        self.table.setColumnWidth(1, 90)  # Resolution
        self.table.setColumnWidth(2, 70)  # Format
        self.table.setColumnWidth(3, 90)  # Size

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.main_layout.addWidget(self.table)

    def setup_buttons(self):
        """Bottom buttons"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton(I18n.get("cancel_btn"))
        self.cancel_btn.setObjectName("cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.download_btn = QPushButton(I18n.get("download_label"))
        self.download_btn.clicked.connect(self.accept_selection)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.download_btn)

        self.main_layout.addLayout(button_layout)

    def load_info(self, info):
        """Load video info and populate formats"""
        self.video_info = info
        self.title_label.setText(info.get("title", I18n.get("unknown_title")))

        # Duration and uploader
        dur = info.get("duration")
        if dur:
            mins, secs = divmod(dur, 60)
            hrs, mins = divmod(mins, 60)
            dur_str = f"{int(hrs)}:{int(mins):02}:{int(secs):02}" if hrs else f"{int(mins)}:{int(secs):02}"
        else:
            dur_str = "--:--"

        uploader = info.get("uploader", info.get("channel", "Unknown"))
        self.meta_label.setText(f"⏱️ {dur_str} • 👤 {uploader}")

        # Thumbnail (async, non-blocking)
        thumb_url = info.get("thumbnail")
        if thumb_url:
            self.thumb_worker = ThumbnailWorker(thumb_url)
            self.thumb_worker.finished.connect(self.set_thumbnail)
            self.thumb_worker.start()
            # Don't wait for thumbnail - let it load async

        # Playlist detection
        if "playlist_title" in info or "playlist" in info.get("webpage_url_basename", ""):
            playlist_title = info.get("playlist_title", "Playlist")
            playlist_count = info.get("playlist_count", "?")
            self.playlist_banner.setText(
                f"📋 Playlist: {playlist_title} ({playlist_count} items) • Currently: Single video"
            )
            self.playlist_banner.show()

        # Store ALL formats from yt-dlp
        self.all_formats = info.get("formats", [])
        self.playlist_entries = info.get("entries", [])

        # Determine mode
        if not self.all_formats and self.playlist_entries:
            # Flat Playlist Mode (Fast analysis result)
            self.setup_flat_playlist_mode()
        else:
            # Normal Video Mode
            self.populate_table(self.all_formats)

    def set_thumbnail(self, data):
        """Set thumbnail from worker (only if dialog still open)"""
        if not self.isVisible():
            return  # Dialog already closed

        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            scaled = pixmap.scaled(160, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)

    def setup_flat_playlist_mode(self):
        """Setup UI for flat playlist (list of videos without format info)"""
        print(f"📋 Entering Flat Playlist Mode: {len(self.playlist_entries)} entries")

        # Hide format selector logic (existing)
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item and item.layout() and isinstance(item.layout(), QHBoxLayout):
                if item.layout().count() > 0:
                    w = item.layout().itemAt(0).widget()
                    if isinstance(w, QLabel) and "Format Type" in w.text():
                        for j in range(item.layout().count()):
                            wdg = item.layout().itemAt(j).widget()
                            if wdg:
                                wdg.hide()

        # Add Global Quality Selector
        quality_layout = QHBoxLayout()
        quality_layout.setContentsMargins(0, 10, 0, 10)

        lbl = QLabel("🌍 Global Playlist Quality:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #00bef7;")
        quality_layout.addWidget(lbl)

        self.playlist_quality_combo = QComboBox()
        self.playlist_quality_combo.addItems(
            [
                "⭐ Best Quality (Auto)",
                "🎬 4K (2160p)",
                "📺 2K (1440p)",
                "📺 Full HD (1080p)",
                "📱 HD (720p)",
                "💾 SD (480p)",
                "📉 Low (360p)",
                "🎵 Audio Only (Best Audio)",
            ]
        )
        self.playlist_quality_combo.setStyleSheet(
            """
            QComboBox {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 4px;
                background: #333;
                color: white;
                min-width: 200px;
            }
        """
        )
        quality_layout.addWidget(self.playlist_quality_combo)
        quality_layout.addStretch()

        # Insert before table (index 3 usually, but safer to add to layout)
        # Finding the layout index for table... simplifying by adding to main_layout before simple table check
        # But we need it above the table.
        # Let's insert it before the table widget

        idx = self.main_layout.indexOf(self.table)
        if idx != -1:
            self.main_layout.insertLayout(idx, quality_layout)

        # Reconfigure table headers
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["#", "Video Title", "ID"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 120)

        # Populate table with playlist entries
        self.table.setRowCount(len(self.playlist_entries))

        for row, entry in enumerate(self.playlist_entries):
            # Index
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            # Title
            title = entry.get("title", "Unknown")
            self.table.setItem(row, 1, QTableWidgetItem(title))
            # ID
            vid_id = entry.get("id", "-")
            self.table.setItem(row, 2, QTableWidgetItem(vid_id))

        # Update download button text with size estimate
        total_videos = len(self.playlist_entries)

        # Calculate ACTUAL total duration from playlist entries
        total_duration_seconds = 0
        for entry in self.playlist_entries:
            duration = entry.get("duration", 0)  # duration in seconds from yt-dlp
            if duration:
                total_duration_seconds += duration

        # Calculate estimated size based on selected quality and REAL duration
        def get_size_estimate(quality_idx):
            """Get estimated size based on quality and actual video durations"""
            if total_duration_seconds == 0:
                return "Size unknown"

            # Typical bitrates per quality (kbps for video+audio)
            bitrate_map = {
                0: 8000,  # Best (high quality, ~8 Mbps)
                1: 20000,  # 4K (~20 Mbps)
                2: 12000,  # 2K (~12 Mbps)
                3: 8000,  # 1080p (~8 Mbps)
                4: 4000,  # 720p (~4 Mbps)
                5: 2000,  # 480p (~2 Mbps)
                6: 1000,  # 360p (~1 Mbps)
                7: 256,  # Audio only (~256 kbps)
            }

            bitrate_kbps = bitrate_map.get(quality_idx, 5000)
            # Size = bitrate (kbps) * duration (seconds) / 8 / 1024 = MB
            total_mb = (bitrate_kbps * total_duration_seconds) / 8 / 1024

            if total_mb > 1024:
                return f"~{total_mb/1024:.1f} GB"
            return f"~{int(total_mb)} MB"

        # Calculate total duration for display
        hours = int(total_duration_seconds // 3600)
        minutes = int((total_duration_seconds % 3600) // 60)
        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        # Update button when quality changes
        def update_button_text():
            idx = self.playlist_quality_combo.currentIndex()
            size_est = get_size_estimate(idx)
            self.download_btn.setText(f"Download All ({total_videos} Videos, {duration_str}, {size_est})")

        self.playlist_quality_combo.currentIndexChanged.connect(update_button_text)
        update_button_text()  # Initial text

        # Show banner
        self.playlist_banner.setText(f"📚 Full Playlist Mode: {len(self.playlist_entries)} videos found.")
        self.playlist_banner.show()

    def filter_formats(self):
        """Filter formats based on selected type"""

        if self.audio_only_rb.isChecked():
            # Audio only
            filtered = [f for f in self.all_formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
        elif self.video_only_rb.isChecked():
            # Video only
            filtered = [f for f in self.all_formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
        else:
            # All formats (prefer combined or mergeable)
            filtered = self.all_formats
            print(f"🎬 All formats mode: {len(filtered)} formats")

        self.populate_table(filtered)

    def populate_table(self, formats):
        """Populate table with format data"""

        # Filter out storyboards (mhtml with no real codec)
        valid_formats = [
            f
            for f in formats
            if not (f.get("ext") == "mhtml" and f.get("vcodec") == "none" and f.get("acodec") == "none")
        ]

        # Remove duplicates by format_id only
        seen = set()
        unique_formats = []
        for f in valid_formats:
            fmt_id = f.get("format_id")
            if fmt_id and fmt_id not in seen:
                seen.add(fmt_id)
                unique_formats.append(f)

        # Sort by quality (height desc, then bitrate)
        unique_formats.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)

        self.table.setRowCount(len(unique_formats))

        for row, fmt in enumerate(unique_formats):
            # Column 0: Quality badge
            badge = self.get_quality_badge(fmt, row == 0)
            badge_item = QTableWidgetItem(badge)

            if "BEST" in badge or row == 0:
                font = badge_item.font()
                font.setBold(True)
                badge_item.setFont(font)
                badge_item.setForeground(QColor("#FFD700"))  # Gold

            self.table.setItem(row, 0, badge_item)

            # Column 1: Resolution
            height = fmt.get("height")
            if height:
                res = f"{height}p"
            elif fmt.get("acodec") != "none":
                res = "Audio"
            else:
                res = "Unknown"
            self.table.setItem(row, 1, QTableWidgetItem(res))

            # Column 2: Format
            ext = fmt.get("ext", "?").upper()
            self.table.setItem(row, 2, QTableWidgetItem(ext))

            # Column 3: Size
            size_str = self.format_size(fmt)
            self.table.setItem(row, 3, QTableWidgetItem(size_str))

            # Column 4: Codec
            codec_str = self.format_codec(fmt)
            self.table.setItem(row, 4, QTableWidgetItem(codec_str))

            # Store format data in first column
            badge_item.setData(Qt.UserRole, fmt)

        # Auto-select first (best) format
        if unique_formats:
            self.table.selectRow(0)

    def get_quality_badge(self, fmt, is_first=False):
        """Get quality badge for format"""
        height = fmt.get("height", 0)
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")

        # Audio only
        if vcodec == "none" and acodec != "none":
            abr = fmt.get("abr", 0)
            if abr >= 128:
                return "🎵 High"
            elif abr >= 96:
                return "🎵 Medium"
            else:
                return "🎵 Low"

        # Video
        if is_first and height:
            return "⭐ BEST"
        elif height >= 2160:
            return "🎬 4K UHD"
        elif height >= 1440:
            return "📺 2K"
        elif height >= 1080:
            return "📺 Full HD"
        elif height >= 720:
            return "📱 HD"
        elif height >= 480:
            return "💾 SD"
        elif height >= 360:
            return "📉 Low"
        else:
            return "📉 Very Low"

    def format_size(self, fmt):
        """Format file size"""
        size = fmt.get("filesize") or fmt.get("filesize_approx")
        if not size:
            # Estimate from bitrate and duration
            tbr = fmt.get("tbr")
            duration = self.video_info.get("duration")
            if tbr and duration:
                size = int((tbr * 1024 / 8) * duration)

        if not size:
            return "~"

        if size > 1024**3:  # GB
            return f"{size / (1024**3):.1f} GB"
        elif size > 1024**2:  # MB
            return f"{size / (1024**2):.1f} MB"
        else:
            return f"{size / 1024:.1f} KB"

    def format_codec(self, fmt):
        """Format codec string"""
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")

        if vcodec != "none" and acodec != "none":
            # Both
            v_short = vcodec.split(".")[0][:8]
            a_short = acodec.split(".")[0][:6]
            return f"{v_short}+{a_short}"
        elif vcodec != "none":
            # Video only
            return vcodec.split(".")[0][:15]
        else:
            # Audio only
            abr = fmt.get("abr", 0)
            a_short = acodec.split(".")[0][:10]
            return f"{a_short} ({int(abr)}k)" if abr else a_short

    def accept_selection(self):
        """Accept selected format and emit signal"""

        # Check for Flat Playlist Mode
        # Check for Flat Playlist Mode
        if hasattr(self, "playlist_entries") and self.playlist_entries and not self.all_formats:
            # Get selected global quality
            idx = self.playlist_quality_combo.currentIndex()

            fmt_map = {
                0: ("bestvideo+bestaudio/best", "mp4"),  # Best (Auto)
                1: ("bestvideo[height<=2160]+bestaudio/best[height<=2160]", "mp4"),  # 4K
                2: ("bestvideo[height<=1440]+bestaudio/best[height<=1440]", "mp4"),  # 2K
                3: ("bestvideo[height<=1080]+bestaudio/best[height<=1080]", "mp4"),  # 1080p
                4: ("bestvideo[height<=720]+bestaudio/best[height<=720]", "mp4"),  # 720p
                5: ("bestvideo[height<=480]+bestaudio/best[height<=480]", "mp4"),  # 480p
                6: ("bestvideo[height<=360]+bestaudio/best[height<=360]", "mp4"),  # 360p
                7: ("bestaudio/best", "mp3"),  # Audio Only
            }

            format_id, ext = fmt_map.get(idx, ("bestvideo+bestaudio/best", "mp4"))

            result = {"format_id": format_id, "ext": ext, "is_playlist": True, "entries": self.playlist_entries}
            self.quality_selected.emit(result)
            self.accept()
            return

        selected_items = self.table.selectedItems()
        if not selected_items:
            # Auto-select first row (best quality) if user didn't select anything
            if self.table.rowCount() > 0:
                self.table.selectRow(0)
                print("ℹ️ No format selected, auto-selecting best quality (first row)")
            else:
                print("⚠️ No formats available")
                return

        # Get format data from first column
        format_data = self.table.item(self.table.currentRow(), 0).data(Qt.UserRole)

        result = {
            "format_id": format_data["format_id"],
            "ext": format_data["ext"],
            "vcodec": format_data.get("vcodec"),
            "acodec": format_data.get("acodec"),
            "height": format_data.get("height"),
            "tbr": format_data.get("tbr"),
        }

        self.quality_selected.emit(result)
        self.accept()
