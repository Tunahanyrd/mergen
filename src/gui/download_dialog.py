# -*- coding: utf-8 -*-
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar, 
                               QHBoxLayout, QPushButton, QTabWidget, QWidget, 
                               QGridLayout, QFrame, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QCheckBox, QApplication, QStyle, QLineEdit)
from PySide6.QtCore import Qt, Signal, QThread, QTime, QTimer, QRectF, QUrl
from PySide6.QtGui import QColor, QPainter, QBrush, QIcon, QDesktopServices
from src.core.downloader import Downloader
import time
import sys, os, subprocess

class ConnectionGrid(QWidget):
    """Visualizes 8 connection threads like IDM."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(30)
        self.segments = [0.0] * 8 # 0.0 to 1.0 progress per segment

    def update_segments(self, progress_list):
        self.segments = progress_list
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width() / 8
        h = self.height()
        
        for i, prog in enumerate(self.segments):
            x = i * w
            rect = QRectF(x + 2, 2, w - 4, h - 4)
            painter.fillRect(rect, QColor("#333333"))
            fill_rect = QRectF(x + 2, 2, (w - 4) * prog, h - 4)
            painter.fillRect(fill_rect, QColor("#007acc"))
            painter.setPen(QColor("#555555"))
            painter.drawRect(rect)

class DownloadWorker(QThread):
    progress_signal = Signal(int, int, float)
    status_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, url, save_dir=None, proxy_config=None):
        super().__init__()
        self.url = url
        self.save_dir = save_dir
        self.proxy_config = proxy_config
        self.downloader = None
        self.is_running = True
        self.last_time = time.time()
        self.last_bytes = 0

    def run(self):
        self.downloader = Downloader(
            self.url, 
            save_dir=self.save_dir,
            progress_callback=self.emit_progress,
            status_callback=self.emit_status,
            completion_callback=self.emit_finished,
            proxy_config=self.proxy_config
        )
        self.downloader.start()

    def emit_progress(self, downloaded, total):
        if self.is_running:
            now = time.time()
            elapsed = now - self.last_time
            speed = 0.0
            if elapsed > 0:
                diff = downloaded - self.last_bytes
                speed = diff / elapsed
                self.last_bytes = downloaded
                self.last_time = now
            
            self.progress_signal.emit(downloaded, total, speed)

    def emit_status(self, msg):
        if self.is_running:
            self.status_signal.emit(msg)

    def emit_finished(self, success, filename):
        if self.is_running:
            self.finished_signal.emit(success, filename)
    
    def stop(self):
        self.is_running = False
        self.terminate() 

from src.core.config import ConfigManager

class DownloadCompleteDialog(QDialog):
    """Popup shown when download finishes."""
    def __init__(self, filename, url, size_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download complete")
        self.resize(500, 250)
        self.filename = filename
        self.config = ConfigManager()
        
        # Make modal and topmost to catch attention
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; font-family: 'Segoe UI'; }
            QLabel { color: #e0e0e0; }
            QLineEdit { background: #444; border: 1px solid #555; color: white; padding: 4px; }
            QPushButton { 
                background: #333; border: 1px solid #555; padding: 6px 14px; min-width: 80px; color: #e0e0e0;
            }
            QPushButton:hover { background: #444; border-color: #007acc; }
            QPushButton#OpenBtn { font-weight: bold; border: 1px solid #007acc; background-color: #005a9e; color: white; }
            QPushButton#OpenBtn:hover { background-color: #0078d7; }
            QCheckBox { color: #ccc; }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header: Icon + Details
        h_layout = QHBoxLayout()
        
        # Icon
        icon_lbl = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_DialogApplyButton) 
        icon_lbl.setPixmap(icon.pixmap(48, 48))
        h_layout.addWidget(icon_lbl)
        
        # Text Info
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("<b>Download complete</b>"))
        info_layout.addWidget(QLabel(f"Downloaded {size_str}"))
        h_layout.addLayout(info_layout)
        h_layout.addStretch()
        
        layout.addLayout(h_layout)

        # Address
        layout.addWidget(QLabel("Address"))
        self.url_edit = QLineEdit(url)
        self.url_edit.setReadOnly(True)
        layout.addWidget(self.url_edit)

        # File Saved As
        layout.addWidget(QLabel("The file saved as"))
        self.path_edit = QLineEdit(os.path.abspath(filename))
        self.path_edit.setReadOnly(True)
        layout.addWidget(self.path_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("Open")
        self.open_btn.setObjectName("OpenBtn")
        self.with_btn = QPushButton("Open with...")
        self.folder_btn = QPushButton("Open folder")
        self.close_btn = QPushButton("Close")
        
        self.open_btn.clicked.connect(self.action_open)
        self.folder_btn.clicked.connect(self.action_folder)
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.with_btn)
        btn_layout.addWidget(self.folder_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        # Footer
        self.not_show_chk = QCheckBox("Don't show this dialog again")
        layout.addWidget(self.not_show_chk)

    def accept(self):
        if self.not_show_chk.isChecked():
            self.config.set("show_complete_dialog", False)
        super().accept()

    def action_open(self):
        self.open_file_system(self.filename)
        self.accept()

    def action_folder(self):
        path = os.path.dirname(os.path.abspath(self.filename))
        self.open_file_system(path, is_folder=True)
        
    def open_file_system(self, path, is_folder=False):
        url = QUrl.fromLocalFile(path)
        QDesktopServices.openUrl(url)

class DownloadDialog(QDialog):
    # Defined at class level
    download_complete = Signal(bool, str)

    def __init__(self, url, parent=None, save_dir=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading...")
        self.resize(600, 450)
        self.url = url
        self.save_dir = save_dir
        self.success = False
        self.filename = "Unknown"
        self.expanded = True
        self.final_total_bytes = 0
        
        self.config = ConfigManager()

        self.setup_ui()
        
        # Prepare proxy config
        proxy_cfg = {
            "enabled": self.config.get("proxy_enabled"),
            "host": self.config.get("proxy_host"),
            "port": self.config.get("proxy_port"),
            "user": self.config.get("proxy_user"),
            "pass": self.config.get("proxy_pass")
        }
        
        # Worker
        self.worker = DownloadWorker(url, save_dir, proxy_config=proxy_cfg)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: 1px solid #444; background: #333; }
            QTabBar::tab { background: #2b2b2b; color: #ccc; border: 1px solid #444; padding: 5px; }
            QTabBar::tab:selected { background: #333; color: white; border-bottom: 2px solid #007acc; }
            QLabel { color: #e0e0e0; }
            
            QProgressBar {
                border: 1px solid #555; background-color: #333; height: 20px; text-align: center; color: white;
            }
            QProgressBar::chunk { background-color: #00cc00; width: 10px; margin: 1px; }
            
            QPushButton {
                background-color: #333; border: 1px solid #555; padding: 4px 12px; border-radius: 2px;
                min-width: 80px; color: #e0e0e0;
            }
            QPushButton:hover { background-color: #444; border-color: #007acc; }
            
            QTableWidget {
                background-color: #333; gridline-color: #444; color: #e0e0e0; border: 1px solid #555;
            }
            QHeaderView::section {
                background-color: #2b2b2b; color: #ccc; border: 1px solid #444; padding: 4px;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabs
        tabs = QTabWidget()
        self.status_tab = QWidget()
        tabs.addTab(self.status_tab, "Download status")
        tabs.addTab(QWidget(), "Speed Limiter")
        tabs.addTab(QWidget(), "Options on completion")
        layout.addWidget(tabs)

        # Status Tab Layout
        stab_layout = QVBoxLayout(self.status_tab)
        
        # Info Grid
        grid = QGridLayout()
        grid.addWidget(QLabel(self.url), 0, 0, 1, 2)
        
        grid.addWidget(QLabel("Status:"), 1, 0)
        self.status_val = QLabel("Initializing...")
        self.status_val.setStyleSheet("color: #007acc;")
        grid.addWidget(self.status_val, 1, 1)
        
        grid.addWidget(QLabel("File size:"), 2, 0)
        self.size_val = QLabel("Unknown")
        grid.addWidget(self.size_val, 2, 1)
        
        grid.addWidget(QLabel("Downloaded:"), 3, 0)
        self.downloaded_val = QLabel("0 bytes")
        grid.addWidget(self.downloaded_val, 3, 1)
        
        grid.addWidget(QLabel("Transfer rate:"), 4, 0)
        self.speed_val = QLabel("0 KB/sec")
        grid.addWidget(self.speed_val, 4, 1)
        
        grid.addWidget(QLabel("Time left:"), 5, 0)
        self.time_val = QLabel("Calculating...")
        grid.addWidget(self.time_val, 5, 1)
        
        grid.addWidget(QLabel("Resume capability:"), 6, 0)
        self.resume_val = QLabel("Yes")
        grid.addWidget(self.resume_val, 6, 1)
        
        stab_layout.addLayout(grid)

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Middle Buttons
        mid_layout = QHBoxLayout()
        self.toggle_details_btn = QPushButton("<< Hide details")
        self.toggle_details_btn.clicked.connect(self.toggle_details)
        mid_layout.addWidget(self.toggle_details_btn)
        mid_layout.addStretch()
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.toggle_pause) 
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        mid_layout.addWidget(self.pause_btn)
        mid_layout.addWidget(self.cancel_btn)
        layout.addLayout(mid_layout)

        # Details Area (Connections + Log)
        self.details_frame = QFrame()
        d_layout = QVBoxLayout(self.details_frame)
        d_layout.setContentsMargins(0, 0, 0, 0)
        
        d_layout.addWidget(QLabel("Start positions and download progress by connections"))
        self.conn_grid = ConnectionGrid()
        d_layout.addWidget(self.conn_grid)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["N.", "Downloaded", "Info"])
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setAlternatingRowColors(True)
        # Dummy data
        for i in range(1, 9):
            r = self.log_table.rowCount()
            self.log_table.insertRow(r)
            self.log_table.setItem(r, 0, QTableWidgetItem(str(i)))
            self.log_table.setItem(r, 1, QTableWidgetItem("0 KB"))
            self.log_table.setItem(r, 2, QTableWidgetItem("Connecting..."))
            
        d_layout.addWidget(self.log_table)
        layout.addWidget(self.details_frame)

    def toggle_details(self):
        if self.expanded:
            self.details_frame.hide()
            self.toggle_details_btn.setText("Show details >>")
            self.resize(self.width(), 250)
        else:
            self.details_frame.show()
            self.toggle_details_btn.setText("<< Hide details")
            self.resize(self.width(), 450)
        self.expanded = not self.expanded

    def update_progress(self, downloaded, total, speed):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(downloaded)
        self.final_total_bytes = total
        
        dl_mb = downloaded / (1024*1024)
        tot_mb = total / (1024*1024)
        pct = (downloaded / total) * 100 if total else 0
        self.downloaded_val.setText(f"{dl_mb:.2f} MB ({pct:.1f}%)")
        self.size_val.setText(f"{tot_mb:.2f} MB")
        
        if speed > 0:
            if speed < 1024*1024:
                self.speed_val.setText(f"{speed/1024:.2f} KB/sec")
            else:
                self.speed_val.setText(f"{speed/(1024*1024):.2f} MB/sec")
            
            rem = total - downloaded
            secs = int(rem / speed)
            if secs < 60:
                self.time_val.setText(f"{secs} sec")
            else:
                self.time_val.setText(QTime(0,0,0).addSecs(secs).toString("HH:mm:ss"))
        
        self.status_val.setText("Receiving data...")
        
        segments = []
        base_fill = pct / 100.0
        for i in range(8):
            v = base_fill + ((i % 3) * 0.05) if base_fill < 1.0 else 1.0
            segments.append(min(v, 1.0))
        self.conn_grid.update_segments(segments)

    def toggle_pause(self):
        if self.worker.is_running:
            self.worker.stop()
            self.pause_btn.setText("Resume")
            self.status_val.setText("Paused")
            self.time_val.setText("--")
            self.speed_val.setText("0 KB/s")
        else:
            self.worker = DownloadWorker(self.url)
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.status_signal.connect(self.update_status)
            self.worker.finished_signal.connect(self.on_finished)
            self.worker.start()
            self.pause_btn.setText("Pause")

    def update_status(self, msg):
        pass

    def on_finished(self, success, filename):
        self.success = success
        self.filename = filename
        
        # Always emit signal first
        self.download_complete.emit(success, filename)
        
        # If success, Switch to Complete Dialog
        if success:
            # Hide this dialog
            self.hide()
            
            # Show the "Download Complete" popup if enabled
            from src.core.config import ConfigManager
            cfg = ConfigManager()
            if cfg.get("show_complete_dialog", True):
                size_str = f"{self.final_total_bytes / (1024*1024):.2f} MB"
                comp_dlg = DownloadCompleteDialog(filename, self.url, size_str, self.parent())
                comp_dlg.exec()
            
            # Now close the progress dialog for real
            self.accept()
        else:
            self.status_val.setText("Failed")
            self.status_val.setStyleSheet("color: red")
            # Keep dialog open to show error
