#!/usr/bin/env python3
"""
Configuration des styles et thèmes pour Machine KPI Dialog v2.
"""

# === COULEURS PRINCIPALES ===
COLORS = {
    # Couleurs principales Material Design
    'primary': '#3498db',
    'primary_dark': '#2980b9',
    'primary_darker': '#21618c',
    
    # Couleurs de statut
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#17a2b8',
    
    # Couleurs secondaires
    'secondary': '#6c757d',
    'light': '#f8f9fa',
    'dark': '#343a40',
    
    # Couleurs de fond
    'background': '#f5f5f5',
    'surface': '#ffffff',
    'border': '#e0e0e0',
    'text': '#2c3e50',
    'text_secondary': '#6c757d'
}

# === STYLES CSS ===
MODERN_STYLE = f"""
QDialog {{
    background-color: {COLORS['background']};
    font-family: 'Segoe UI', Arial, sans-serif;
}}

QGroupBox {{
    font-weight: bold;
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
    background-color: {COLORS['surface']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: {COLORS['text']};
    font-size: 14px;
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 12px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_darker']};
}}

QComboBox {{
    border: 2px solid #bdc3c7;
    border-radius: 6px;
    padding: 6px;
    background-color: {COLORS['surface']};
    font-size: 12px;
}}

QComboBox:focus {{
    border-color: {COLORS['primary']};
}}

QLineEdit {{
    border: 2px solid #bdc3c7;
    border-radius: 6px;
    padding: 8px;
    background-color: {COLORS['surface']};
    font-size: 12px;
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QTableWidget {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['surface']};
    alternate-background-color: {COLORS['light']};
    gridline-color: #e9ecef;
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid #e9ecef;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QHeaderView::section {{
    background-color: #34495e;
    color: white;
    padding: 10px;
    border: none;
    font-weight: bold;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['surface']};
}}

QTabBar::tab {{
    background-color: #ecf0f1;
    padding: 10px 15px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QTabBar::tab:hover {{
    background-color: #d5dbdb;
}}
"""

# === STYLES POUR CARTES ===
def get_card_style(color: str, dark_factor: float = 0.8) -> str:
    """Génère le style pour une carte avec la couleur spécifiée."""
    from PySide6.QtGui import QColor
    
    base_color = QColor(color)
    dark_color = QColor(
        int(base_color.red() * dark_factor),
        int(base_color.green() * dark_factor),
        int(base_color.blue() * dark_factor)
    )
    
    return f"""
    QFrame {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {color}, stop:1 {dark_color.name()});
        border-radius: 12px;
        border: none;
        color: white;
        margin: 4px;
    }}
    QLabel {{
        color: white;
        background: transparent;
        border: none;
    }}
    """

# === COULEURS PAR TYPE DE CARTE ===
CARD_COLORS = {
    'total_machines': COLORS['primary'],
    'active_machines': COLORS['success'],
    'critical_machines': COLORS['danger'],
    'total_cost': COLORS['warning'],
    'avg_cost': '#9b59b6',  # Violet
    'efficiency': '#1abc9c'  # Turquoise
}

# === STYLES POUR STATUTS ===
STATUS_STYLES = {
    'Actif': {
        'background': '#d4edda',
        'color': '#155724',
        'border': '#c3e6cb'
    },
    'Attention': {
        'background': '#f8d7da',
        'color': '#721c24',
        'border': '#f5c6cb'
    },
    'Inactif': {
        'background': '#e2e3e5',
        'color': '#383d41',
        'border': '#d6d8db'
    }
}

# === CONFIGURATION DES ANIMATIONS ===
ANIMATION_CONFIG = {
    'duration': 250,  # ms
    'easing': 'OutCubic',
    'fade_duration': 150
}

# === CONFIGURATION DES MÉTRIQUES ===
METRICS_CONFIG = {
    'card_height': 120,
    'card_min_width': 150,
    'icon_size': 16,
    'title_size': 10,
    'value_size': 18
}

# === CONFIGURATION DU TABLEAU ===
TABLE_CONFIG = {
    'row_height': 35,
    'header_height': 40,
    'alternating_colors': True,
    'sort_enabled': True,
    'selection_behavior': 'rows'
}

# === CONFIGURATION DES FILTRES ===
FILTER_CONFIG = {
    'search_delay': 300,  # ms
    'max_results_default': 50,
    'max_results_range': (10, 100)
}
