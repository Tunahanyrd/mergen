# -*- coding: utf-8 -*-
"""
Properties Dialog - file properties viewer with tabs
"""

import os
import subprocess

from PySide6.QtCore import QFileInfo, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class PropertiesDialog(QDialog):
    """IDM-style Properties Dialog with modern glassmorphism design."""

    def __init__(self, download_item, parent=None):
        super().__init__(parent)
        self.item = download_item
        self.setWindowTitle("File Properties")
        self.resize(600, 550)
        self.setup_ui()

    def setup_ui(self):
        """Build dialog UI with tabs."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Section
        header = self.create_header()
        layout.addLayout(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget::pane { border: 2px solid #404050; }")

        tabs.addTab(self.create_general_tab(), "General")
        tabs.addTab(self.create_details_tab(), "Details")
        tabs.addTab(self.create_download_tab(), "Download Info")

        layout.addWidget(tabs)

        # Footer Buttons
        footer = self.create_footer()
        layout.addLayout(footer)

    def create_header(self):
        """Create header with file icon and name."""
        header = QHBoxLayout()
        header.setSpacing(15)

        # File Icon
        icon_lbl = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        icon_lbl.setPixmap(icon.pixmap(72, 72))
        icon_lbl.setStyleSheet(
            "background-color: #242432; border-radius: 12px; padding: 12px; border: 2px solid #404050;"
        )

        # File Info
        title_box = QVBoxLayout()
        fname = os.path.basename(self.item.filename)

        lbl_name = QLabel(fname)
        lbl_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #e8e8f0;")
        lbl_name.setWordWrap(True)

        ext = os.path.splitext(fname)[1].upper() or "File"
        lbl_type = QLabel(f"Type: {ext}")
        lbl_type.setStyleSheet("color: #b8b8c8; font-size: 13px;")

        title_box.addWidget(lbl_name)
        title_box.addWidget(lbl_type)
        title_box.addStretch()

        header.addWidget(icon_lbl)
        header.addLayout(title_box)
        header.addStretch()

        return header

    def create_general_tab(self):
        """General tab with file location, size, status."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # File Information Group
        file_group = QGroupBox("File Information")
        file_layout = QFormLayout()
        file_layout.setSpacing(12)

        # Location
        location_edit = self.copyable_line(os.path.dirname(self.item.filename))
        file_layout.addRow("Location:", location_edit)

        # Full path
        path_edit = self.copyable_line(self.item.filename)
        file_layout.addRow("Full Path:", path_edit)

        # Size
        size_label = QLabel(self.format_size())
        size_label.setStyleSheet("color: #e8e8f0;")
        file_layout.addRow("Size:", size_label)

        # File exists
        exists = os.path.exists(self.item.filename)
        exists_label = QLabel("✓ Yes" if exists else "✗ No")
        exists_label.setStyleSheet(f"color: {'#00d4ff' if exists else '#ff0066'}; font-weight: bold;")
        file_layout.addRow("File Exists:", exists_label)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # System Information Group (if file exists)
        if exists:
            sys_group = QGroupBox("System Information")
            sys_layout = QFormLayout()
            sys_layout.setSpacing(12)

            fi = QFileInfo(self.item.filename)

            sys_layout.addRow("Created:", QLabel(fi.birthTime().toString("yyyy-MM-dd HH:mm:ss")))
            sys_layout.addRow("Modified:", QLabel(fi.lastModified().toString("yyyy-MM-dd HH:mm:ss")))
            sys_layout.addRow("Accessed:", QLabel(fi.lastRead().toString("yyyy-MM-dd HH:mm:ss")))

            try:
                perms = oct(os.stat(self.item.filename).st_mode)[-3:]
                sys_layout.addRow("Permissions:", QLabel(perms))
            except Exception:
                pass

            sys_group.setLayout(sys_layout)
            layout.addWidget(sys_group)

        layout.addStretch()
        return widget

    def create_details_tab(self):
        """Details tab with advanced file information."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Download Status Group
        status_group = QGroupBox("Download Status")
        status_layout = QFormLayout()
        status_layout.setSpacing(12)

        status_layout.addRow("Status:", QLabel(self.item.status))
        status_layout.addRow("Date Added:", QLabel(self.item.date_added))
        status_layout.addRow("Queue:", QLabel(self.item.queue or "None"))

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # File System Details
        if os.path.exists(self.item.filename):
            fs_group = QGroupBox("File System Details")
            fs_layout = QFormLayout()
            fs_layout.setSpacing(12)

            fi = QFileInfo(self.item.filename)

            fs_layout.addRow("Is Readable:", QLabel("✓ Yes" if fi.isReadable() else "✗ No"))
            fs_layout.addRow("Is Writable:", QLabel("✓ Yes" if fi.isWritable() else "✗ No"))
            fs_layout.addRow("Is Executable:", QLabel("✓ Yes" if fi.isExecutable() else "✗ No"))
            fs_layout.addRow("Is Symlink:", QLabel("✓ Yes" if fi.isSymLink() else "✗ No"))

            fs_group.setLayout(fs_layout)
            layout.addWidget(fs_group)

        layout.addStretch()
        return widget

    def create_download_tab(self):
        """Download info tab with URL and metadata."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # URL Information
        url_group = QGroupBox("URL Information")
        url_layout = QVBoxLayout()
        url_layout.setSpacing(10)

        url_label = QLabel("Download URL:")
        url_label.setStyleSheet("font-weight: bold; color: #b8b8c8;")
        url_layout.addWidget(url_label)

        url_edit = self.copyable_line(self.item.url)
        url_layout.addWidget(url_edit)

        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # Download Metadata
        meta_group = QGroupBox("Download Metadata")
        meta_layout = QFormLayout()
        meta_layout.setSpacing(12)

        meta_layout.addRow("Download ID:", QLabel(str(self.item.id)))
        meta_layout.addRow("Filename:", QLabel(os.path.basename(self.item.filename)))

        if hasattr(self.item, "category") and self.item.category:
            meta_layout.addRow("Category:", QLabel(self.item.category))

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        layout.addStretch()
        return widget

    def create_footer(self):
        """Create footer with action buttons."""
        footer = QHBoxLayout()
        footer.setSpacing(10)

        btn_open = QPushButton("Open File")
        btn_open.clicked.connect(self.open_file)
        btn_open.setEnabled(os.path.exists(self.item.filename))

        btn_folder = QPushButton("Open Folder")
        btn_folder.clicked.connect(self.open_folder)

        btn_copy_url = QPushButton("Copy URL")
        btn_copy_url.clicked.connect(self.copy_url)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)

        footer.addWidget(btn_open)
        footer.addWidget(btn_folder)
        footer.addWidget(btn_copy_url)
        footer.addStretch()
        footer.addWidget(btn_close)

        return footer

    def copyable_line(self, text):
        """Create a read-only copyable line edit."""
        edit = QLineEdit(str(text))
        edit.setReadOnly(True)
        return edit

    def format_size(self):
        """Format file size with proper units."""
        try:
            if os.path.exists(self.item.filename):
                size_bytes = os.path.getsize(self.item.filename)
                if size_bytes > 1024**3:
                    return f"{size_bytes / (1024**3):.2f} GB ({size_bytes:,} bytes)"
                elif size_bytes > 1024**2:
                    return f"{size_bytes / (1024**2):.2f} MB ({size_bytes:,} bytes)"
                elif size_bytes > 1024:
                    return f"{size_bytes / 1024:.2f} KB ({size_bytes:,} bytes)"
                else:
                    return f"{size_bytes} bytes"
            else:
                return self.item.size or "Unknown"
        except Exception:
            return self.item.size or "Unknown"

    def open_file(self):
        """Open the downloaded file."""
        if os.path.exists(self.item.filename):
            try:
                subprocess.Popen(["xdg-open", self.item.filename])
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.item.filename))

    def open_folder(self):
        """Open the folder containing the file."""
        path = os.path.dirname(self.item.filename)
        if os.path.exists(path):
            try:
                subprocess.Popen([" xdg-open", path])
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def copy_url(self):
        """Copy download URL to clipboard."""
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(self.item.url)
