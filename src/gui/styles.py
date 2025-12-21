# Colors - Improved Contrast
C_BG_MAIN = "#1a1a24"  # Lighter main background
C_BG_PANEL = "#242432"  # Lighter panel background
C_BG_HOVER = "#2d2d3d"  # More visible hover
C_ACCENT_CYAN = "#00d4ff"  # Brighter cyan
C_ACCENT_BLUE = "#0088cc"  # Brighter blue
C_TEXT_MAIN = "#e8e8f0"  # Brighter text
C_TEXT_SUB = "#b8b8c8"  # Lighter subtext
C_BORDER = "#404050"  # Much more visible borders
C_BORDER_FOCUS = "#00d4ff"  # Bright focus border

MERGEN_THEME = f"""
/* Global Reset */
QWidget {{
    font-family: 'Segoe UI', sans-serif;
    color: {C_TEXT_MAIN};
}}

/* Main Window */
QMainWindow {{
    background-color: {C_BG_MAIN};
}}

/* Sidebar */
QTreeWidget {{
    background-color: {C_BG_PANEL};
    border: 2px solid {C_BORDER};
    font-size: 14px;
    padding: 10px;
    border-radius: 12px;
    margin:  10px;
}}
QTreeWidget::item {{
    height: 38px;
    border-radius: 8px;
    padding-left: 8px;
    margin-bottom: 4px;
    border: 1px solid transparent;
}}
QTreeWidget::item:selected {{
    background-color: rgba(0, 212, 255, 0.15);
    color: {C_ACCENT_CYAN};
    border-left: 3px solid {C_ACCENT_CYAN};
    border: 1px solid {C_BORDER};
}}
QTreeWidget::item:hover {{
    background-color: rgba(64, 64, 80, 0.6);
    border: 1px solid {C_BORDER};
}}

/* Table */
QTableWidget {{
    background-color: {C_BG_PANEL};
    border: 2px solid {C_BORDER};
    border-radius: 12px;
    gridline-color: {C_BORDER};
    selection-background-color: rgba(0, 212, 255, 0.2);
    alternate-background-color: {C_BG_MAIN};
    padding: 5px;
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {C_BORDER};
}}
QTableWidget::item:selected {{
    background-color: rgba(0, 212, 255, 0.25); 
    color: white;
    border: 1px solid {C_BORDER_FOCUS};
}}
QTableWidget::item:hover {{
    background-color: rgba(64, 64, 80, 0.5);
}}
QHeaderView::section {{
    background-color: {C_BG_HOVER};
    border: 1px solid {C_BORDER};
    border-bottom: 2px solid {C_BORDER};
    color: {C_TEXT_MAIN};
    padding: 8px;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 1px;
}}

/* Dialogs */
QDialog {{
    background-color: {C_BG_MAIN};
    border: 2px solid {C_BORDER};
}}

/* Buttons */
QPushButton {{
    background-color: {C_BG_HOVER};
    color: {C_TEXT_MAIN};
    border: 2px solid {C_BORDER};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: rgba(0, 212, 255, 0.15);
    border-color: {C_BORDER_FOCUS};
}}
QPushButton:pressed {{
    background-color: {C_BG_MAIN};
    border-color: {C_ACCENT_CYAN};
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: {C_BG_PANEL};
    border: 2px solid {C_BORDER};
    border-radius: 6px;
    padding: 6px;
    color: {C_TEXT_MAIN};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 2px solid {C_BORDER_FOCUS};
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: {C_BG_PANEL};
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    min-height: 20px;
    border-radius: 5px;
    border: 1px solid {C_BORDER};
}}
QScrollBar::handle:vertical:hover {{
    background: {C_ACCENT_CYAN};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* GroupBox */
QGroupBox {{
    border: 2px solid {C_BORDER};
    border-radius: 8px;
    margin-top: 20px;
    font-weight: bold;
    color: {C_ACCENT_CYAN};
    padding: 15px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}

/* TabWidget */
QTabWidget::pane {{
    border: 2px solid {C_BORDER};
    background: {C_BG_PANEL};
    border-radius: 8px;
}}
QTabBar::tab {{
    background: {C_BG_PANEL};
    color: {C_TEXT_SUB};
    padding: 8px 16px;
    border: 2px solid {C_BORDER};
    border-bottom: none;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background: {C_BG_HOVER};
    color: {C_ACCENT_CYAN};
    border-top: 3px solid {C_ACCENT_CYAN};
}}
QTabBar::tab:hover {{
    background: {C_BG_HOVER};
    color: white;
}}

/* Checkboxes and Radio Buttons */
QCheckBox, QRadioButton {{
    color: {C_TEXT_MAIN};
    spacing: 8px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {C_BORDER};
    border-radius: 4px;
    background: {C_BG_PANEL};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {C_ACCENT_CYAN};
    border-color: {C_ACCENT_CYAN};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {C_BORDER_FOCUS};
}}

/* ListWidget */
QListWidget {{
    background-color: {C_BG_PANEL};
    border: 2px solid {C_BORDER};
    border-radius: 8px;
    padding: 5px;
}}
QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
    border: 1px solid transparent;
}}
QListWidget::item:selected {{
    background-color: rgba(0, 212, 255, 0.2);
    border: 1px solid {C_BORDER_FOCUS};
    color: white;
}}
QListWidget::item:hover {{
    background-color: {C_BG_HOVER};
    border: 1px solid {C_BORDER};
}}
"""

# Light theme - already good, just slight tweaks
MERGEN_THEME_LIGHT = """
/* Global Reset */
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #1a1a1a;
}

/* Main Window */
QMainWindow {
    background-color: #f5f5f7;
}

/* Sidebar */
QTreeWidget {
    background-color: #ffffff;
    border: 2px solid #d1d1d1;
    border-radius: 8px;
    font-size: 13px;
    outline: none;
}
QTreeWidget::item {
    height: 32px;
    padding-left: 4px;
    border: 1px solid transparent;
}
QTreeWidget::item:selected {
    background-color: #e3f2fd;
    color: #005a9e;
    border-left: 3px solid #005a9e;
    border: 1px solid #b0d4f1;
}
QTreeWidget::item:hover {
    background-color: #f0f0f0;
    border: 1px solid #e0e0e0;
}

/* Table */
QTableWidget {
    background-color: #ffffff;
    border: 2px solid #d1d1d1;
    border-radius: 8px;
    gridline-color: #e8e8e8;
    selection-background-color: #e3f2fd;
    selection-color: #1a1a1a;
    outline: none;
}
QHeaderView::section {
    background-color: #f0f0f0;
    border: 1px solid #d1d1d1;
    border-bottom: 2px solid #c0c0c0;
    color: #555;
    padding: 6px;
    font-weight: bold;
}
QTableWidget::item {
    padding: 4px;
    border-bottom: 1px solid #eeeeee;
}
QTableWidget::item:hover {
    background-color: #f8f8f8;
}

/* Buttons */
QPushButton {
    background-color: #ffffff;
    border: 2px solid #c0c0c0;
    border-radius: 6px;
    padding: 6px 12px;
    color: #1a1a1a;
}
QPushButton:hover {
    background-color: #f8f9fa;
    border-color: #007acc;
}
QPushButton:pressed {
    background-color: #e9ecef;
}

/* ToolBar & Inputs */
QToolBar {
    background: transparent;
    border: none;
    spacing: 10px;
}
QToolButton {
    color: #1a1a1a;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px;
}
QToolButton:hover {
    background-color: #e0e0e0;
    border: 1px solid #d0d0d0;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 2px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px;
    color: #1a1a1a;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 2px solid #007acc;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #f0f0f0;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #c1c1c1;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #a8a8a8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
