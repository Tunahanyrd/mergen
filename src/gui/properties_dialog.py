from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTabWidget, QWidget, 
                               QFormLayout, QTextEdit, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
import os

class PropertiesDialog(QDialog):
    def __init__(self, parent, download_item):
        super().__init__(parent)
        self.item = download_item
        self.setWindowTitle("File Properties")
        self.resize(500, 450)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # File Info Header
        header_layout = QHBoxLayout()
        # Icon can be added here if passed or resolved
        self.info_label = QLabel(f"<b>{os.path.basename(self.item.filename)}</b>")
        self.info_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(self.info_label)
        layout.addLayout(header_layout)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # General Tab
        self.tab_general = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.tab_general, "General")
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self.open_file)
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.save_and_close)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_open)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def setup_general_tab(self):
        layout = QFormLayout(self.tab_general)
        
        self.lbl_type = QLabel("Unknown")
        layout.addRow("Type:", self.lbl_type)
        
        self.lbl_status = QLabel(self.item.status)
        layout.addRow("Status:", self.lbl_status)
        
        self.lbl_size = QLabel(self.item.size)
        layout.addRow("Size:", self.lbl_size)
        
        # Save To (Editable path if needed, usually just directory)
        path_layout = QHBoxLayout()
        self.txt_save_path = QLineEdit()
        self.txt_save_path.setReadOnly(True) 
        path_layout.addWidget(self.txt_save_path)
        self.btn_browse = QPushButton("Browse...") # Allow moving? Maybe just viewing for now.
        self.btn_browse.clicked.connect(self.browse_path)
        path_layout.addWidget(self.btn_browse)
        layout.addRow("Save To:", path_layout)
        
        self.txt_url = QLineEdit()
        self.txt_url.setReadOnly(True)
        layout.addRow("Address:", self.txt_url)
        
        self.txt_referer = QLineEdit()
        layout.addRow("Referer:", self.txt_referer)
        
        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(60)
        layout.addRow("Description:", self.txt_desc)
        
        # Login
        self.txt_user = QLineEdit()
        layout.addRow("Login:", self.txt_user)
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.txt_pass)
        
    def load_data(self):
        # Populate fields
        self.lbl_type.setText(os.path.splitext(self.item.filename)[1].upper().replace(".", "") + " File")
        self.txt_save_path.setText(os.path.dirname(self.item.filename))
        self.txt_url.setText(self.item.url)
        self.txt_referer.setText(self.item.referer)
        self.txt_desc.setText(self.item.description)
        self.txt_user.setText(self.item.username)
        self.txt_pass.setText(self.item.password)
        
        if self.item.status == "Complete":
            self.btn_open.setEnabled(True)
        else:
            self.btn_open.setEnabled(False)

    def browse_path(self):
        # Open folder selection? or File save dialog?
        # Typically IDM allows moving the file or changing download dir
        new_dir = QFileDialog.getExistingDirectory(self, "Select Directory", self.txt_save_path.text())
        if new_dir:
            self.txt_save_path.setText(new_dir)

    def open_file(self):
        if os.path.exists(self.item.filename):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.item.filename))
        else:
            QMessageBox.warning(self, "Error", "File not found.")

    def save_and_close(self):
        # Save editable fields back to item
        
        self.item.referer = self.txt_referer.text()
        self.item.description = self.txt_desc.toPlainText()
        self.item.username = self.txt_user.text()
        self.item.password = self.txt_pass.text()
        
        self.accept()
