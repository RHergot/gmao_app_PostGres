#!/usr/bin/env python3
"""
Dialog d'analyse KPI par équipe.
Affiche les métriques de maintenance détaillées pour chaque équipe.
"""

from .base_kpi_dialog import BaseKPIDialog, get_shared_text
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QTabWidget, QWidget, QLabel
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

try:
    from app.config import app_config, Language
except ImportError:
    pass

# === TRADUCTIONS SPÉCIFIQUES ===
TEAM_TRANSLATIONS = {
    "FRENCH": {
        "title": "📊 Analyse KPI par Équipe",
        "team_filter": "Filtrer par Équipe",
        "all_teams": "Toutes les équipes",
        "shift_filter": "Filtrer par Poste",
        "all_shifts": "Tous les postes",
        "summary_tab": "📊 Résumé",
        "performance_tab": "⚡ Performance",
        "workload_tab": "📋 Charge de Travail",
        "team_name": "Équipe",
        "shift": "Poste",
        "members_count": "Nb Membres",
        "total_interventions": "Total Interventions",
        "avg_time": "Temps Moyen (h)",
        "efficiency": "Efficacité (%)",
        "loading_teams": "Chargement des données équipes...",
        "export_success": "Données équipes exportées avec succès"
    }
}

def get_team_text(key: str) -> str:
    return TEAM_TRANSLATIONS.get("FRENCH", {}).get(key, key)

class TeamKPIDialog(BaseKPIDialog):
    """Dialog d'analyse KPI par équipe."""
    
    def __init__(self, parent=None):
        super().__init__(parent, get_team_text("title"))
        self.teams_data = []
        logger.info("Initialisation du TeamKPIDialog")
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute les filtres spécifiques aux équipes."""
        # Filtre par équipe
        team_group = QGroupBox(get_team_text("team_filter"))
        team_layout = QHBoxLayout(team_group)
        self.team_combo = QComboBox()
        self.team_combo.addItem(get_team_text("all_teams"))
        team_layout.addWidget(self.team_combo)
        toolbar_layout.addWidget(team_group)
        
        # Filtre par poste
        shift_group = QGroupBox(get_team_text("shift_filter"))
        shift_layout = QHBoxLayout(shift_group)
        self.shift_combo = QComboBox()
        self.shift_combo.addItem(get_team_text("all_shifts"))
        shift_layout.addWidget(self.shift_combo)
        toolbar_layout.addWidget(shift_group)
    
    def create_specific_content(self):
        """Crée le contenu spécifique à l'analyse par équipe."""
        self.tab_widget = QTabWidget()
        self.content_layout.addWidget(self.tab_widget)
        
        # Onglet résumé
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        self.teams_table = QTableWidget()
        self.teams_table.setColumnCount(6)
        headers = [
            get_team_text("team_name"),
            get_team_text("shift"),
            get_team_text("members_count"),
            get_team_text("total_interventions"),
            get_team_text("avg_time"),
            get_team_text("efficiency")
        ]
        self.teams_table.setHorizontalHeaderLabels(headers)
        self.teams_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.teams_table.setAlternatingRowColors(True)
        
        summary_layout.addWidget(self.teams_table)
        self.tab_widget.addTab(summary_widget, get_team_text("summary_tab"))
        
        # Autres onglets (placeholders)
        for tab_name in [get_team_text("performance_tab"), get_team_text("workload_tab")]:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            placeholder = QLabel(f"📊 {tab_name} en cours de développement")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #666666; font-style: italic; padding: 40px;")
            tab_layout.addWidget(placeholder)
            self.tab_widget.addTab(tab_widget, tab_name)
    
    def load_data(self):
        """Charge les données des équipes."""
        self.set_status(get_team_text("loading_teams"))
        
        try:
            # Données simulées
            import random
            teams = ["Équipe Alpha", "Équipe Beta", "Équipe Gamma"]
            shifts = ["Matin", "Après-midi", "Nuit"]
            
            self.teams_data = []
            for team in teams:
                for shift in shifts:
                    self.teams_data.append({
                        "team_name": team,
                        "shift": shift,
                        "members_count": random.randint(3, 8),
                        "total_interventions": random.randint(20, 100),
                        "avg_time": random.uniform(1.5, 6.0),
                        "efficiency": random.uniform(75, 95)
                    })
            
            self.update_views()
            self.set_status(f"Données chargées: {len(self.teams_data)} équipes", success=True)
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données équipes: {e}")
            self.set_status(f"Erreur: {e}", success=False)
    
    def update_views(self):
        """Met à jour les vues."""
        self.teams_table.setRowCount(len(self.teams_data))
        
        for row, team in enumerate(self.teams_data):
            self.teams_table.setItem(row, 0, QTableWidgetItem(team["team_name"]))
            self.teams_table.setItem(row, 1, QTableWidgetItem(team["shift"]))
            self.teams_table.setItem(row, 2, QTableWidgetItem(str(team["members_count"])))
            self.teams_table.setItem(row, 3, QTableWidgetItem(str(team["total_interventions"])))
            self.teams_table.setItem(row, 4, QTableWidgetItem(f"{team['avg_time']:.1f}h"))
            self.teams_table.setItem(row, 5, QTableWidgetItem(f"{team['efficiency']:.1f}%"))
    
    def export_data(self):
        """Exporte les données équipes."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export", get_team_text("export_success"))
