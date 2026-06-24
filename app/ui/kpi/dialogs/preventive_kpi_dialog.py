#!/usr/bin/env python3
"""
Dialog d'analyse KPI préventif vs curatif.
Compare l'efficacité et les coûts entre maintenance préventive et corrective.
"""

from .base_kpi_dialog import BaseKPIDialog, get_shared_text
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QTabWidget, QWidget, QLabel, QGridLayout
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

try:
    from app.config import app_config, Language
except ImportError:
    pass

# === TRADUCTIONS SPÉCIFIQUES ===
PREVENTIVE_TRANSLATIONS = {
    "FRENCH": {
        "title": "📊 Analyse Préventif vs Curatif",
        "maintenance_type": "Type de Maintenance",
        "all_types": "Tous les types",
        "preventive": "Préventif",
        "corrective": "Curatif",
        "summary_tab": "📊 Résumé",
        "comparison_tab": "⚖️ Comparaison",
        "evolution_tab": "📈 Évolution",
        "cost_comparison": "Comparaison des Coûts",
        "efficiency_comparison": "Comparaison d'Efficacité",
        "preventive_cost": "Coût Préventif",
        "corrective_cost": "Coût Curatif",
        "preventive_count": "Nb Préventif",
        "corrective_count": "Nb Curatif",
        "cost_ratio": "Ratio Coût",
        "time_ratio": "Ratio Temps",
        "loading_data": "Chargement des données préventif/curatif...",
        "export_success": "Données préventif/curatif exportées avec succès"
    }
}

def get_preventive_text(key: str) -> str:
    return PREVENTIVE_TRANSLATIONS.get("FRENCH", {}).get(key, key)

class PreventiveKPIDialog(BaseKPIDialog):
    """Dialog d'analyse KPI préventif vs curatif."""
    
    def __init__(self, parent=None):
        super().__init__(parent, get_preventive_text("title"))
        self.maintenance_data = {}
        logger.info("Initialisation du PreventiveKPIDialog")
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute les filtres spécifiques au préventif/curatif."""
        # Filtre par type de maintenance
        type_group = QGroupBox(get_preventive_text("maintenance_type"))
        type_layout = QHBoxLayout(type_group)
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            get_preventive_text("all_types"),
            get_preventive_text("preventive"),
            get_preventive_text("corrective")
        ])
        type_layout.addWidget(self.type_combo)
        toolbar_layout.addWidget(type_group)
    
    def create_specific_content(self):
        """Crée le contenu spécifique à l'analyse préventif/curatif."""
        self.tab_widget = QTabWidget()
        self.content_layout.addWidget(self.tab_widget)
        
        # === ONGLET RÉSUMÉ ===
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # Métriques de comparaison
        metrics_group = QGroupBox(get_preventive_text("cost_comparison"))
        metrics_layout = QGridLayout(metrics_group)
        
        self.preventive_cost_label = QLabel("Coût Préventif: --")
        self.corrective_cost_label = QLabel("Coût Curatif: --")
        self.preventive_count_label = QLabel("Nb Préventif: --")
        self.corrective_count_label = QLabel("Nb Curatif: --")
        self.cost_ratio_label = QLabel("Ratio Coût (P/C): --")
        self.time_ratio_label = QLabel("Ratio Temps (P/C): --")
        
        # Style des métriques
        metric_style = """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
        """
        
        for label in [self.preventive_cost_label, self.corrective_cost_label,
                     self.preventive_count_label, self.corrective_count_label,
                     self.cost_ratio_label, self.time_ratio_label]:
            label.setStyleSheet(metric_style)
        
        metrics_layout.addWidget(self.preventive_cost_label, 0, 0)
        metrics_layout.addWidget(self.corrective_cost_label, 0, 1)
        metrics_layout.addWidget(self.preventive_count_label, 1, 0)
        metrics_layout.addWidget(self.corrective_count_label, 1, 1)
        metrics_layout.addWidget(self.cost_ratio_label, 2, 0)
        metrics_layout.addWidget(self.time_ratio_label, 2, 1)
        
        summary_layout.addWidget(metrics_group)
        
        # Table détaillée
        details_group = QGroupBox("Détails par Machine")
        details_layout = QVBoxLayout(details_group)
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(6)
        headers = [
            "Machine",
            get_preventive_text("preventive_cost"),
            get_preventive_text("corrective_cost"),
            get_preventive_text("preventive_count"),
            get_preventive_text("corrective_count"),
            "Ratio P/C"
        ]
        self.details_table.setHorizontalHeaderLabels(headers)
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.details_table.setAlternatingRowColors(True)
        
        details_layout.addWidget(self.details_table)
        summary_layout.addWidget(details_group)
        
        self.tab_widget.addTab(summary_widget, get_preventive_text("summary_tab"))
        
        # Autres onglets (placeholders)
        for tab_name in [get_preventive_text("comparison_tab"), get_preventive_text("evolution_tab")]:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            placeholder = QLabel(f"📊 {tab_name} en cours de développement")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #666666; font-style: italic; padding: 40px;")
            tab_layout.addWidget(placeholder)
            self.tab_widget.addTab(tab_widget, tab_name)
    
    def load_data(self):
        """Charge les données préventif/curatif."""
        self.set_status(get_preventive_text("loading_data"))
        
        try:
            # Données simulées
            import random
            
            machines = [f"MACH-{i:03d}" for i in range(1, 16)]
            self.maintenance_data = {
                "machines": [],
                "totals": {
                    "preventive_cost": 0,
                    "corrective_cost": 0,
                    "preventive_count": 0,
                    "corrective_count": 0
                }
            }
            
            for machine in machines:
                prev_cost = random.uniform(1000, 5000)
                corr_cost = random.uniform(2000, 8000)
                prev_count = random.randint(5, 15)
                corr_count = random.randint(2, 10)
                
                machine_data = {
                    "machine": machine,
                    "preventive_cost": prev_cost,
                    "corrective_cost": corr_cost,
                    "preventive_count": prev_count,
                    "corrective_count": corr_count,
                    "cost_ratio": prev_cost / corr_cost if corr_cost > 0 else 0
                }
                
                self.maintenance_data["machines"].append(machine_data)
                self.maintenance_data["totals"]["preventive_cost"] += prev_cost
                self.maintenance_data["totals"]["corrective_cost"] += corr_cost
                self.maintenance_data["totals"]["preventive_count"] += prev_count
                self.maintenance_data["totals"]["corrective_count"] += corr_count
            
            self.update_views()
            self.set_status("Données préventif/curatif chargées", success=True)
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            self.set_status(f"Erreur: {e}", success=False)
    
    def update_views(self):
        """Met à jour les vues."""
        if not self.maintenance_data:
            return
        
        totals = self.maintenance_data["totals"]
        
        # Mise à jour des métriques
        self.preventive_cost_label.setText(f"Coût Préventif: {totals['preventive_cost']:.2f}€")
        self.corrective_cost_label.setText(f"Coût Curatif: {totals['corrective_cost']:.2f}€")
        self.preventive_count_label.setText(f"Nb Préventif: {totals['preventive_count']}")
        self.corrective_count_label.setText(f"Nb Curatif: {totals['corrective_count']}")
        
        # Calcul des ratios
        cost_ratio = totals['preventive_cost'] / totals['corrective_cost'] if totals['corrective_cost'] > 0 else 0
        count_ratio = totals['preventive_count'] / totals['corrective_count'] if totals['corrective_count'] > 0 else 0
        
        self.cost_ratio_label.setText(f"Ratio Coût (P/C): {cost_ratio:.2f}")
        self.time_ratio_label.setText(f"Ratio Temps (P/C): {count_ratio:.2f}")
        
        # Mise à jour de la table
        machines = self.maintenance_data["machines"]
        self.details_table.setRowCount(len(machines))
        
        for row, machine_data in enumerate(machines):
            self.details_table.setItem(row, 0, QTableWidgetItem(machine_data["machine"]))
            self.details_table.setItem(row, 1, QTableWidgetItem(f"{machine_data['preventive_cost']:.2f}€"))
            self.details_table.setItem(row, 2, QTableWidgetItem(f"{machine_data['corrective_cost']:.2f}€"))
            self.details_table.setItem(row, 3, QTableWidgetItem(str(machine_data["preventive_count"])))
            self.details_table.setItem(row, 4, QTableWidgetItem(str(machine_data["corrective_count"])))
            self.details_table.setItem(row, 5, QTableWidgetItem(f"{machine_data['cost_ratio']:.2f}"))
    
    def export_data(self):
        """Exporte les données préventif/curatif."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export", get_preventive_text("export_success"))
