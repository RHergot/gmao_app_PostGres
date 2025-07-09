# machine_kpi_chart_widget.py
#!/usr/bin/env python3
"""
Widget graphique spécialisé pour l'analyse KPI des machines.
Affiche les coûts et interventions avec double axe Y.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Imports PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QFrame, QGroupBox,
    QDateEdit, QButtonGroup, QRadioButton, QMessageBox,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QFont

# Imports pour graphiques
try:
    # Configuration matplotlib pour PySide6
    import matplotlib
    matplotlib.use('Qt5Agg')  # Backend Qt pour PySide6
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"Matplotlib non disponible - graphiques désactivés: {e}")

# Import des traductions
from .machine_kpi_chart_translations import get_chart_text

import logging
logger = logging.getLogger(__name__)

class PeriodType(Enum):
    """Types de périodes disponibles."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class ChartMode(Enum):
    """Modes de visualisation du graphique."""
    BARS = "bars"
    LINES = "lines"

class MachineKPIChartWidget(QWidget):
    """
    Widget graphique pour l'analyse KPI des machines.
    
    Fonctionnalités:
    - Filtres par site, machine, type
    - Sélection de période (jour/semaine/mois)
    - Double axe Y (coûts + interventions)
    - Mode barres ou courbes
    - Support multilingue
    """
    
    # Signaux
    filters_changed = Signal()
    chart_updated = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.current_period_type = PeriodType.MONTHLY
        self.current_chart_mode = ChartMode.BARS
        self.chart_data = {}
        
        # Données pour les filtres
        self.sites_data = []
        self.machines_data = []
        self.types_data = []
        
        # Interface
        self.setup_ui()
        self.setup_connections()
        
        # Graphique matplotlib
        if MATPLOTLIB_AVAILABLE:
            self.setup_matplotlib()
        
        logger.info("MachineKPIChartWidget initialisé")
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === SECTION FILTRES ===
        self.create_filters_section(layout)
        
        # === SECTION CONTRÔLES ===
        self.create_controls_section(layout)
        
        # === SECTION GRAPHIQUE ===
        self.create_chart_section(layout)
    
    def create_filters_section(self, parent_layout):
        """Crée la section des filtres."""
        filters_group = QGroupBox("🎚️ " + get_chart_text("site_filter"))
        filters_layout = QHBoxLayout(filters_group)
        filters_layout.setSpacing(20)
        
        # === FILTRE SITE ===
        site_container = QFrame()
        site_layout = QVBoxLayout(site_container)
        site_layout.setSpacing(5)
        
        site_label = QLabel(get_chart_text("site_filter"))
        site_label.setFont(QFont("Arial", 9, QFont.Bold))
        
        self.site_combo = QComboBox()
        self.site_combo.addItem(get_chart_text("all_sites"))
        self.site_combo.setMinimumWidth(150)
        
        site_layout.addWidget(site_label)
        site_layout.addWidget(self.site_combo)
        filters_layout.addWidget(site_container)
        
        # === FILTRE MACHINE ===
        machine_container = QFrame()
        machine_layout = QVBoxLayout(machine_container)
        machine_layout.setSpacing(5)
        
        machine_label = QLabel(get_chart_text("machine_filter_chart"))
        machine_label.setFont(QFont("Arial", 9, QFont.Bold))
        
        self.machine_combo = QComboBox()
        self.machine_combo.addItem(get_chart_text("all_machines_chart"))
        self.machine_combo.setMinimumWidth(150)
        
        machine_layout.addWidget(machine_label)
        machine_layout.addWidget(self.machine_combo)
        filters_layout.addWidget(machine_container)
        
        # === FILTRE TYPE ===
        type_container = QFrame()
        type_layout = QVBoxLayout(type_container)
        type_layout.setSpacing(5)
        
        type_label = QLabel(get_chart_text("type_filter_chart"))
        type_label.setFont(QFont("Arial", 9, QFont.Bold))
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(get_chart_text("all_types_chart"))
        self.type_combo.setMinimumWidth(150)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        filters_layout.addWidget(type_container)
        
        # Stretch pour répartir l'espace
        filters_layout.addStretch()
        
        parent_layout.addWidget(filters_group)
    
    def create_controls_section(self, parent_layout):
        """Crée la section des contrôles."""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(20)
        
        # === CONTRÔLES DE PÉRIODE ===
        period_group = QGroupBox(get_chart_text("period_controls"))
        period_layout = QGridLayout(period_group)
        period_layout.setSpacing(10)
        
        # Type de période
        period_type_label = QLabel(get_chart_text("period_type"))
        period_type_label.setFont(QFont("Arial", 9, QFont.Bold))
        period_layout.addWidget(period_type_label, 0, 0)
        
        self.period_button_group = QButtonGroup()
        
        self.daily_radio = QRadioButton(get_chart_text("daily"))
        self.weekly_radio = QRadioButton(get_chart_text("weekly"))
        self.monthly_radio = QRadioButton(get_chart_text("monthly"))
        self.monthly_radio.setChecked(True)  # Par défaut
        
        self.period_button_group.addButton(self.daily_radio, 0)
        self.period_button_group.addButton(self.weekly_radio, 1)
        self.period_button_group.addButton(self.monthly_radio, 2)
        
        period_layout.addWidget(self.daily_radio, 0, 1)
        period_layout.addWidget(self.weekly_radio, 0, 2)
        period_layout.addWidget(self.monthly_radio, 0, 3)
        
        # Dates
        start_date_label = QLabel(get_chart_text("start_date"))
        start_date_label.setFont(QFont("Arial", 9, QFont.Bold))
        period_layout.addWidget(start_date_label, 1, 0)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))
        period_layout.addWidget(self.start_date_edit, 1, 1)
        
        end_date_label = QLabel(get_chart_text("end_date"))
        end_date_label.setFont(QFont("Arial", 9, QFont.Bold))
        period_layout.addWidget(end_date_label, 1, 2)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        period_layout.addWidget(self.end_date_edit, 1, 3)
        
        controls_layout.addWidget(period_group)
        
        # === CONTRÔLES DE GRAPHIQUE ===
        chart_group = QGroupBox(get_chart_text("chart_type_controls"))
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setSpacing(10)
        
        # Mode de graphique
        chart_mode_label = QLabel(get_chart_text("chart_mode"))
        chart_mode_label.setFont(QFont("Arial", 9, QFont.Bold))
        chart_layout.addWidget(chart_mode_label)
        
        self.chart_button_group = QButtonGroup()
        
        self.bars_radio = QRadioButton(get_chart_text("bars_mode"))
        self.lines_radio = QRadioButton(get_chart_text("lines_mode"))
        self.bars_radio.setChecked(True)  # Par défaut
        
        self.chart_button_group.addButton(self.bars_radio, 0)
        self.chart_button_group.addButton(self.lines_radio, 1)
        
        chart_layout.addWidget(self.bars_radio)
        chart_layout.addWidget(self.lines_radio)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton(get_chart_text("refresh_chart"))
        self.refresh_button.setMinimumWidth(120)
        buttons_layout.addWidget(self.refresh_button)
        
        self.export_button = QPushButton(get_chart_text("export_chart"))
        self.export_button.setMinimumWidth(120)
        buttons_layout.addWidget(self.export_button)
        
        chart_layout.addLayout(buttons_layout)
        
        controls_layout.addWidget(chart_group)
        
        parent_layout.addWidget(controls_frame)
    
    def create_chart_section(self, parent_layout):
        """Crée la section du graphique."""
        chart_group = QGroupBox(get_chart_text("chart_title"))
        chart_layout = QVBoxLayout(chart_group)
        
        if MATPLOTLIB_AVAILABLE:
            # Canvas matplotlib
            self.figure = Figure(figsize=(12, 6), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            chart_layout.addWidget(self.canvas)
        else:
            # Placeholder si matplotlib n'est pas disponible
            placeholder = QLabel("📈 " + get_chart_text("no_data_chart"))
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    color: #7f8c8d;
                    padding: 50px;
                    border: 2px dashed #bdc3c7;
                    border-radius: 10px;
                }
            """)
            chart_layout.addWidget(placeholder)
        
        # Stretch pour que le graphique prenne tout l'espace
        chart_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        parent_layout.addWidget(chart_group, 1)
    
    def setup_matplotlib(self):
        """Configure matplotlib."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Configuration des styles
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9
        
        # Créer les axes
        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()  # Axe secondaire pour les interventions
        
        # Configuration des axes
        self.ax1.set_xlabel(get_chart_text("x_axis_label"))
        self.ax1.set_ylabel(get_chart_text("y_axis_costs"), color='#3498db')
        self.ax2.set_ylabel(get_chart_text("y_axis_interventions"), color='#e74c3c')
        
        self.ax1.tick_params(axis='y', labelcolor='#3498db')
        self.ax2.tick_params(axis='y', labelcolor='#e74c3c')
        
        # Titre
        self.ax1.set_title(get_chart_text("chart_title"), fontsize=14, fontweight='bold')
        
        # Grille
        self.ax1.grid(True, alpha=0.3)
        
        # Affichage initial
        self.canvas.draw()
    
    def setup_connections(self):
        """Configure les connexions des signaux."""
        # Filtres
        self.site_combo.currentTextChanged.connect(self.on_filters_changed)
        self.machine_combo.currentTextChanged.connect(self.on_filters_changed)
        self.type_combo.currentTextChanged.connect(self.on_filters_changed)
        
        # Contrôles de période
        self.period_button_group.buttonClicked.connect(self.on_period_changed)
        self.start_date_edit.dateChanged.connect(self.on_dates_changed)
        self.end_date_edit.dateChanged.connect(self.on_dates_changed)
        
        # Mode de graphique
        self.chart_button_group.buttonClicked.connect(self.on_chart_mode_changed)
        
        # Boutons
        self.refresh_button.clicked.connect(self.refresh_chart)
        self.export_button.clicked.connect(self.export_chart)
    
    def on_filters_changed(self):
        """Gère le changement des filtres."""
        self.filters_changed.emit()
        # Déclencher la mise à jour du graphique avec un délai
        QTimer.singleShot(100, self.refresh_chart)
    
    def on_period_changed(self):
        """Gère le changement du type de période."""
        button_id = self.period_button_group.checkedId()
        
        if button_id == 0:
            self.current_period_type = PeriodType.DAILY
        elif button_id == 1:
            self.current_period_type = PeriodType.WEEKLY
        elif button_id == 2:
            self.current_period_type = PeriodType.MONTHLY
        
        self.refresh_chart()
    
    def on_dates_changed(self):
        """Gère le changement des dates."""
        # Valider la plage de dates
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        if start_date >= end_date:
            QMessageBox.warning(self, "Erreur", get_chart_text("invalid_date_range"))
            return
        
        self.refresh_chart()
    
    def on_chart_mode_changed(self):
        """Gère le changement du mode de graphique."""
        button_id = self.chart_button_group.checkedId()
        
        if button_id == 0:
            self.current_chart_mode = ChartMode.BARS
        elif button_id == 1:
            self.current_chart_mode = ChartMode.LINES
        
        self.refresh_chart()
    
    def set_data(self, sites: List[str], machines: List[str], types: List[str]):
        """Configure les données pour les filtres."""
        self.sites_data = sites
        self.machines_data = machines
        self.types_data = types
        
        # Mettre à jour les combos
        self.update_filter_combos()
    
    def update_filter_combos(self):
        """Met à jour les combos de filtres."""
        # Bloquer les signaux
        self.site_combo.blockSignals(True)
        self.machine_combo.blockSignals(True)
        self.type_combo.blockSignals(True)
        
        # Site
        self.site_combo.clear()
        self.site_combo.addItem(get_chart_text("all_sites"))
        self.site_combo.addItems(self.sites_data)
        
        # Machine
        self.machine_combo.clear()
        self.machine_combo.addItem(get_chart_text("all_machines_chart"))
        self.machine_combo.addItems(self.machines_data)
        
        # Type
        self.type_combo.clear()
        self.type_combo.addItem(get_chart_text("all_types_chart"))
        self.type_combo.addItems(self.types_data)
        
        # Réactiver les signaux
        self.site_combo.blockSignals(False)
        self.machine_combo.blockSignals(False)
        self.type_combo.blockSignals(False)
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Retourne les filtres actuels."""
        return {
            'site': self.site_combo.currentText() if self.site_combo.currentText() != get_chart_text("all_sites") else None,
            'machine': self.machine_combo.currentText() if self.machine_combo.currentText() != get_chart_text("all_machines_chart") else None,
            'type': self.type_combo.currentText() if self.type_combo.currentText() != get_chart_text("all_types_chart") else None,
            'start_date': self.start_date_edit.date().toPython(),
            'end_date': self.end_date_edit.date().toPython(),
            'period_type': self.current_period_type.value,
            'chart_mode': self.current_chart_mode.value
        }
    
    def update_chart(self, chart_data: Dict[str, Any]):
        """Met à jour le graphique avec de nouvelles données."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.chart_data = chart_data
        
        # Vider les axes
        self.ax1.clear()
        self.ax2.clear()
        
        # Créer un troisième axe pour la durée (partageant l'axe X avec ax1)
        if hasattr(self, 'ax3'):
            self.ax3.remove()
        self.ax3 = self.ax1.twinx()
        self.ax3.spines['right'].set_position(('outward', 60))
        
        # Vérifier si on a des données
        if not chart_data or 'periods' not in chart_data:
            self.ax1.text(0.5, 0.5, get_chart_text("no_data_chart"), 
                         transform=self.ax1.transAxes, ha='center', va='center',
                         fontsize=14, color='#7f8c8d')
            self.canvas.draw()
            return
        
        periods = chart_data['periods']
        costs = chart_data.get('costs', [])
        interventions = chart_data.get('interventions', [])
        durations = chart_data.get('durations', [])
        
        if not periods or not costs:
            self.ax1.text(0.5, 0.5, get_chart_text("no_data_period"), 
                         transform=self.ax1.transAxes, ha='center', va='center',
                         fontsize=14, color='#7f8c8d')
            self.canvas.draw()
            return
        
        # Dessiner selon le mode
        if self.current_chart_mode == ChartMode.BARS:
            self.draw_bars_chart(periods, costs, interventions, durations)
        else:
            self.draw_lines_chart(periods, costs, interventions, durations)
        
        # Configuration des axes
        self.ax1.set_xlabel(get_chart_text("x_axis_label"))
        self.ax1.set_ylabel(get_chart_text("y_axis_costs"), color='#3498db')
        self.ax2.set_ylabel(get_chart_text("y_axis_interventions"), color='#e74c3c')
        self.ax3.set_ylabel(get_chart_text("y_axis_duration"), color='#9b59b6')
        
        self.ax1.tick_params(axis='y', labelcolor='#3498db')
        self.ax2.tick_params(axis='y', labelcolor='#e74c3c')
        self.ax3.tick_params(axis='y', labelcolor='#9b59b6')
        
        # Titre
        self.ax1.set_title(get_chart_text("chart_title"), fontsize=14, fontweight='bold')
        
        # Grille
        self.ax1.grid(True, alpha=0.3)
        
        # Légende
        lines1, labels1 = self.ax1.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        lines3, labels3 = self.ax3.get_legend_handles_labels()
        self.ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left')
        
        # Ajuster le layout
        self.figure.tight_layout()
        
        # Actualiser l'affichage
        self.canvas.draw()
        
        self.chart_updated.emit()
    
    def draw_bars_chart(self, periods, costs, interventions, durations):
        """Dessine le graphique en barres."""
        width = 0.25
        x = range(len(periods))
        
        # Barres pour les coûts
        self.ax1.bar([i - width for i in x], costs, width, 
                    label=get_chart_text("legend_costs"), color='#3498db', alpha=0.7)
        
        # Barres pour les interventions
        self.ax2.bar([i for i in x], interventions, width,
                    label=get_chart_text("legend_interventions"), color='#e74c3c', alpha=0.7)
        
        # Barres pour la durée
        self.ax3.bar([i + width for i in x], durations, width,
                    label=get_chart_text("legend_duration"), color='#9b59b6', alpha=0.7)
        
        # Labels des périodes
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels(periods, rotation=45, ha='right')
    
    def draw_lines_chart(self, periods, costs, interventions, durations):
        """Dessine le graphique en courbes."""
        x = range(len(periods))
        
        # Courbe pour les coûts
        self.ax1.plot(x, costs, 'o-', label=get_chart_text("legend_costs"), 
                     color='#3498db', linewidth=2, markersize=6)
        
        # Courbe pour les interventions
        self.ax2.plot(x, interventions, 's-', label=get_chart_text("legend_interventions"),
                     color='#e74c3c', linewidth=2, markersize=6)
        
        # Courbe pour la durée
        self.ax3.plot(x, durations, '^-', label=get_chart_text("legend_duration"),
                     color='#9b59b6', linewidth=2, markersize=6)
        
        # Labels des périodes
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels(periods, rotation=45, ha='right')
    
    def refresh_chart(self):
        """Rafraîchit le graphique."""
        # Émettre le signal pour que le parent recharge les données
        self.filters_changed.emit()
    
    def export_chart(self):
        """Exporte le graphique."""
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "Erreur", "Matplotlib non disponible pour l'export")
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            get_chart_text("export_chart"),
            f"machine_kpi_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "Images PNG (*.png);;Images PDF (*.pdf)"
        )
        
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Succès", f"Graphique exporté vers:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{e}")
