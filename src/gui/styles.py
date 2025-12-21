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
