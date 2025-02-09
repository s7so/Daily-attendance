from PyQt6.QtGui import QColor

# Color Scheme
COLORS = {
    'primary': '#2C3E50',      # Dark Blue
    'secondary': '#34495E',    # Lighter Blue
    'accent': '#3498DB',       # Bright Blue
    'success': '#27AE60',      # Green
    'warning': '#F39C12',      # Orange
    'danger': '#E74C3C',       # Red
    'light': '#ECF0F1',       # Light Gray
    'dark': '#2C3E50',        # Dark Blue
    'white': '#FFFFFF',       # White
    'gray': '#BDC3C7'         # Gray
}

# Styles
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #ECF0F1;
}
"""

TAB_WIDGET_STYLE = """
QTabWidget::pane {
    border: 1px solid #BDC3C7;
    background: white;
    border-radius: 5px;
}

QTabWidget::tab-bar {
    alignment: right;
}

QTabBar::tab {
    background: #ECF0F1;
    color: #2C3E50;
    padding: 12px 20px;
    margin: 2px;
    border: 1px solid #BDC3C7;
    border-radius: 5px;
    min-width: 120px;
    font-size: 14px;
}

QTabBar::tab:selected {
    background: #3498DB;
    color: white;
    border: 1px solid #2980B9;
}

QTabBar::tab:hover {
    background: #2980B9;
    color: white;
}
"""

BUTTON_STYLE = """
QPushButton {
    background-color: #3498DB;
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 5px;
    font-size: 14px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #2980B9;
}

QPushButton:pressed {
    background-color: #2475A8;
}

QPushButton:disabled {
    background-color: #BDC3C7;
}
"""

TABLE_STYLE = """
QTableWidget {
    background-color: white;
    alternate-background-color: #F9F9F9;
    border: 1px solid #BDC3C7;
    border-radius: 5px;
    padding: 5px;
    gridline-color: #ECF0F1;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #ECF0F1;
}

QHeaderView::section {
    background-color: #34495E;
    color: white;
    padding: 10px;
    border: none;
    font-size: 14px;
}

QTableWidget::item:selected {
    background-color: #3498DB;
    color: white;
}
"""

INPUT_STYLE = """
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit {
    padding: 8px;
    border: 1px solid #BDC3C7;
    border-radius: 5px;
    background-color: white;
    color: #2C3E50;
    font-size: 14px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {
    border: 2px solid #3498DB;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: url(:/icons/down_arrow.png);
    width: 12px;
    height: 12px;
}
"""

LABEL_STYLE = """
QLabel {
    color: #2C3E50;
    font-size: 14px;
    padding: 5px;
}
"""

GROUP_BOX_STYLE = """
QGroupBox {
    border: 1px solid #BDC3C7;
    border-radius: 5px;
    margin-top: 10px;
    font-size: 14px;
    padding: 15px;
}

QGroupBox::title {
    color: #2C3E50;
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
}
"""

# Font Configuration
FONT_CONFIG = {
    'family': 'Arial',
    'size': {
        'small': 12,
        'normal': 14,
        'large': 16,
        'title': 18
    }
}

# Layout Configuration
LAYOUT_SPACING = 10
LAYOUT_MARGINS = 15
WIDGET_MARGINS = 8 