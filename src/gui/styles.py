# Colors
C_BG_MAIN = "#11111b"  # Main Background (Darkest)
C_BG_PANEL = "#1e1e2e"  # Panel/Card Background
C_BG_HOVER = "#313244"  # Hover State
C_ACCENT_CYAN = "#00f2ff"  # Cyan Accent
C_ACCENT_BLUE = "#007acc"  # Blue Accent
C_TEXT_MAIN = "#cdd6f4"  # Main Text
C_TEXT_SUB = "#a6adc8"  # Sub Text
C_BORDER = "#45475a"  # Borders

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
    border: none;
    font-size: 14px;
    padding: 10px;
    border-right: 1px solid {C_BG_HOVER};
    border-radius: 12px;
    margin: 10px;
}}
QTreeWidget::item {{
    height: 38px;
    border-radius: 8px;
    padding-left: 8px;
    margin-bottom: 4px;
}}
QTreeWidget::item:selected {{
    background-color: rgba(49, 50, 68, 0.6); /* Translucent Hover */
    color: {C_ACCENT_CYAN};
    border-left: 3px solid {C_ACCENT_CYAN};
}}
QTreeWidget::item:hover {{
    background-color: rgba(49, 50, 68, 0.4);
}}

/* Table */
QTableWidget {{
    background-color: {C_BG_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: {C_BG_HOVER};
    alternate-background-color: {C_BG_MAIN};
    padding: 5px;
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid rgba(69, 71, 90, 0.3);
}}
QTableWidget::item:selected {{
    background-color: rgba(0, 242, 255, 0.1); 
    color: white;
}}
QHeaderView::section {{
    background-color: transparent;
    border: none;
    color: {C_TEXT_SUB};
    padding: 8px;
    font-weight: bold;
    border-bottom: 1px solid {C_BORDER};
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 1px;
}}

/* Dialogs */
QDialog {{
    background-color: {C_BG_MAIN};
}}

/* Buttons */
QPushButton {{
    background-color: rgba(49, 50, 68, 0.5);
    color: {C_TEXT_MAIN};
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: rgba(69, 71, 90, 0.8);
    border-color: rgba(255, 255, 255, 0.2);
}}
QPushButton:pressed {{
    background-color: {C_BG_MAIN};
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

# Refined Light Theme
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
    border: 1px solid #d1d1d1;
    border-radius: 8px;
    font-size: 13px;
    outline: none;
}
QTreeWidget::item {
    height: 32px;
    padding-left: 4px;
}
QTreeWidget::item:selected {
    background-color: #e3f2fd;
    color: #005a9e;
    border-left: 3px solid #005a9e;
}
QTreeWidget::item:hover {
    background-color: #f0f0f0;
}

/* Table */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
    gridline-color: transparent;
    selection-background-color: #e3f2fd;
    selection-color: #1a1a1a;
    outline: none;
}
QHeaderView::section {
    background-color: #f0f0f0;
    border: none;
    border-bottom: 1px solid #d1d1d1;
    color: #555;
    padding: 6px;
    font-weight: bold;
}
QTableWidget::item {
    padding: 4px;
    border-bottom: 1px solid #eeeeee;
}

/* Buttons */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
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
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px;
    color: #1a1a1a;
}
QLineEdit:focus {
    border: 1px solid #007acc;
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
