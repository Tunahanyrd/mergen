import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QAbstractItemView, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap, QColor, QBrush, QImage
import requests
from src.gui.workers import ThumbnailWorker

class QualityDialog(QDialog):
    quality_selected = Signal(dict)  # Emits selected format info: {'format_id': '...', 'ext': 'mp4', ...}

    def __init__(self, parent=None, video_info=None):
        super().__init__(parent)
        self.setWindowTitle("Select Download Quality - Mergen")
        self.setFixedSize(700, 500)
        self.video_info = video_info or {}
        
        # Stylesheet (Glassmorphism adapted from main theme)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                color: white;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QTableWidget {
                background-color: #252526;
                gridline-color: #3e3e42;
                border: 1px solid #3e3e42;
                color: #cccccc;
            }
            QHeaderView::section {
                background-color: #333337;
                padding: 4px;
                border: 1px solid #3e3e42;
                color: #cccccc;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header Area (Thumbnail + Title)
        self.header_layout = QHBoxLayout()
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 90)
        self.thumb_label.setStyleSheet("background-color: #000; border: 1px solid #444;")
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.header_layout.addWidget(self.thumb_label)
        
        # Info
        self.info_layout = QVBoxLayout()
        self.title_label = QLabel("Analyzing video...")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.meta_label = QLabel("--:-- • -- MB")
        self.meta_label.setStyleSheet("color: #aaaaaa;")
        
        self.info_layout.addWidget(self.title_label)
        self.info_layout.addWidget(self.meta_label)
        self.info_layout.addStretch()
        self.header_layout.addLayout(self.info_layout)
        
        self.layout.addLayout(self.header_layout)

        # 2. Quality List
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Resolution", "Format", "Size", "Codec"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.table)

        # 3. Bottom Controls
        self.bottom_layout = QHBoxLayout()
        
        # Audio Selection (for video-only streams)
        self.audio_combo = QComboBox()
        self.audio_combo.setPlaceholderText("Select Audio Track")
        self.audio_combo.addItem("Best Audio (Auto-Merge)", "best")
        
        self.bottom_layout.addWidget(QLabel("Audio:"))
        self.bottom_layout.addWidget(self.audio_combo, 1)
        
        self.bottom_layout.addStretch()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.accept_selection)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #3e3e42;")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.bottom_layout.addWidget(self.cancel_btn)
        self.bottom_layout.addWidget(self.download_btn)
        
        self.layout.addLayout(self.bottom_layout)
        
        # Load data if provided
        if self.video_info:
            self.load_info(self.video_info)

    def load_info(self, info):
        self.video_info = info
        self.title_label.setText(info.get('title', 'Unknown Title'))
        
        # Duration
        dur = info.get('duration')
        if dur:
            mins, secs = divmod(dur, 60)
            hrs, mins = divmod(mins, 60)
            dur_str = f"{int(hrs)}:{int(mins):02}:{int(secs):02}" if hrs else f"{int(mins)}:{int(secs):02}"
        else:
            dur_str = "--:--"
        self.meta_label.setText(f"{dur_str} • {info.get('uploader', 'Unknown Source')}")

        # Load Thumbnail (Async)
        thumb_url = info.get('thumbnail')
        if thumb_url:
            self.thumb_worker = ThumbnailWorker(thumb_url)
            self.thumb_worker.finished.connect(self.set_thumbnail)
            self.thumb_worker.start()

        # Populate Formats
        formats = info.get('formats', [])
        # Filter and sort formats
        # Priority: Video+Audio > Video Only (high res) > Audio Only
        
        filtered_formats = []
        for f in formats:
            # Skip m3u8 playlists if mp4 available, skip dash manifests
            if f.get('protocol') in ['m3u8', 'm3u8_native', 'http_dash_segments']:
               continue
            
            # Simple metadata
            res = f.get('resolution') or 'Unknown'
            ext = f['ext']
            filesize = f.get('filesize_approx') or f.get('filesize')
            
            if filesize:
                size_str = f"{filesize / 1024 / 1024:.1f} MB"
            else:
                size_str = "--"
            
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            
            note = f.get('format_note', '')
            
            # Friendly name
            if vcodec != 'none' and acodec != 'none':
                type_str = f"Video + Audio ({note})"
            elif vcodec != 'none':
                type_str = f"Video Only ({note})"
            else:
                type_str = "Audio Only"
                
            filtered_formats.append({
                'data': f,
                'res': f"{f.get('height', 0)}p" if f.get('height') else note,
                'ext': ext,
                'size': size_str,
                'codec': vcodec,
                'is_video': vcodec != 'none'
            })
            
        # Sort by resolution (height) descending
        filtered_formats.sort(key=lambda x: x['data'].get('height', 0) or 0, reverse=True)
        
        self.table.setRowCount(len(filtered_formats))
        for row, item in enumerate(filtered_formats):
            self.table.setItem(row, 0, QTableWidgetItem(item['res']))
            self.table.setItem(row, 1, QTableWidgetItem(item['ext']))
            self.table.setItem(row, 2, QTableWidgetItem(item['size']))
            self.table.setItem(row, 3, QTableWidgetItem(item['codec']))
            
            # Store format ID in first item
            self.table.item(row, 0).setData(Qt.UserRole, item['data'])

        # Select top item
        if filtered_formats:
            self.table.selectRow(0)

    def set_thumbnail(self, data):
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            scaled = pixmap.scaled(160, 90, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Center crop or just set content
            self.thumb_label.setPixmap(scaled)


    def accept_selection(self):
        # Get selected format
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
            
        format_data = selected_items[0].data(Qt.UserRole)
        audio_choice = self.audio_combo.currentData()
        
        # Prepare result
        result = {
            'format_id': format_data['format_id'],
            'ext': format_data['ext'],
            'vcodec': format_data.get('vcodec'),
            'acodec': format_data.get('acodec')
        }
        
        self.quality_selected.emit(result)
        self.accept()
