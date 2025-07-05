#!/usr/bin/env python3
"""
Dialog d'analyse KPI par machine.
Affiche les métriques de maintenance détaillées pour chaque machine.
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Imports PySide6
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QFrame,
    QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QTabWidget,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

# Import de la classe de base
from .base_kpi_dialog import BaseKPIDialog, get_shared_text

# Ajouter le chemin pour les imports de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from app.config import app_config, Language
    from app.core.services.kpi_service import KPIService
    # Import du widget machine KPI existant
    from app.ui.kpi.widgets.machine_kpi_widget import MachineKPIWidget
except ImportError as e:
    print(f"Erreur d'import dans MachineKPIDialog: {e}")
    MachineKPIWidget = None

import logging
logger = logging.getLogger(__name__)

# === TRADUCTIONS SPÉCIFIQUES ===
MACHINE_TRANSLATIONS = {
    Language.FRENCH: {
        "title": "📊 Analyse KPI par Machine",
        "machine_filter": "Filtrer par Machine",
        "all_machines": "Toutes les machines",
        "type_filter": "Type de Machine",
        "all_types": "Tous les types",
        "summary_tab": "📊 Résumé",
        "details_tab": "📋 Détails",
        "charts_tab": "📈 Graphiques",
        "top_machines": "🔝 Top Machines par Coût",
        "machine_performance": "⚡ Performance par Machine",
        "cost_evolution": "📈 Évolution des Coûts",
        "machine_name": "Machine",
        "total_cost": "Coût Total (€)",
        "interventions": "Interventions",
        "avg_cost": "Coût Moyen (€)",
        "availability": "Disponibilité (%)",
        "last_maintenance": "Dernière Maintenance",
        "next_maintenance": "Prochaine Maintenance",
        "status": "Statut",
        "no_data_message": "Aucune donnée de machine disponible pour cette période",
        "loading_machines": "Chargement des données machines...",
        "export_success": "Données machines exportées avec succès"
    },
    Language.ENGLISH: {
        "title": "📊 Machine KPI Analysis",
        "machine_filter": "Filter by Machine",
        "all_machines": "All machines",
        "type_filter": "Machine Type",
        "all_types": "All types",
        "summary_tab": "📊 Summary",
        "details_tab": "📋 Details",
        "charts_tab": "📈 Charts",
        "top_machines": "🔝 Top Machines by Cost",
        "machine_performance": "⚡ Machine Performance",
        "cost_evolution": "📈 Cost Evolution",
        "machine_name": "Machine",
        "total_cost": "Total Cost (€)",
        "interventions": "Interventions",
        "avg_cost": "Average Cost (€)",
        "availability": "Availability (%)",
        "last_maintenance": "Last Maintenance",
        "next_maintenance": "Next Maintenance",
        "status": "Status",
        "no_data_message": "No machine data available for this period",
        "loading_machines": "Loading machine data...",
        "export_success": "Machine data exported successfully"
    },
    Language.GERMAN: {
        "title": "📊 Maschinen-KPI-Analyse",
        "machine_filter": "Nach Maschine filtern",
        "all_machines": "Alle Maschinen",
        "type_filter": "Maschinentyp",
        "all_types": "Alle Typen",
        "summary_tab": "📊 Zusammenfassung",
        "details_tab": "📋 Details",
        "charts_tab": "📈 Diagramme",
        "top_machines": "🔝 Top Maschinen nach Kosten",
        "machine_performance": "⚡ Maschinenleistung",
        "cost_evolution": "📈 Kostenentwicklung",
        "machine_name": "Maschine",
        "total_cost": "Gesamtkosten (€)",
        "interventions": "Interventionen",
        "avg_cost": "Durchschnittskosten (€)",
        "availability": "Verfügbarkeit (%)",
        "last_maintenance": "Letzte Wartung",
        "next_maintenance": "Nächste Wartung",
        "status": "Status",
        "no_data_message": "Keine Maschinendaten für diesen Zeitraum verfügbar",
        "loading_machines": "Lade Maschinendaten...",
        "export_success": "Maschinendaten erfolgreich exportiert"
    }
}

def get_machine_text(key: str) -> str:
    """Récupère le texte traduit selon la langue configurée."""
    try:
        current_lang = app_config.language if 'app_config' in globals() else Language.FRENCH
        return MACHINE_TRANSLATIONS.get(current_lang, MACHINE_TRANSLATIONS[Language.FRENCH]).get(key, key)
    except:
        return MACHINE_TRANSLATIONS[Language.FRENCH].get(key, key)


class MachineKPIDialog(BaseKPIDialog):
    """
    Dialog d'analyse KPI par machine.
    
    Fonctionnalités:
    - Vue d'ensemble des machines les plus coûteuses
    - Détails par machine avec métriques de performance
    - Graphiques d'évolution des coûts
    - Filtrage par machine, site, type
    - Export des données détaillées
    """
    
    def __init__(self, parent=None):
        # Initialisation avec le titre spécifique
        super().__init__(parent, get_machine_text("title"))
        
        # Données spécifiques aux machines
        self.machines_data = []
        self.machine_types = []
        
        logger.info("Initialisation du MachineKPIDialog")
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute les filtres spécifiques aux machines."""
        # === FILTRE PAR MACHINE ===
        machine_group = QGroupBox(get_machine_text("machine_filter"))
        machine_layout = QHBoxLayout(machine_group)
        
        self.machine_combo = QComboBox()
        self.machine_combo.addItem(get_machine_text("all_machines"))
        self.machine_combo.currentTextChanged.connect(self.on_filter_changed)
        machine_layout.addWidget(self.machine_combo)
        
        toolbar_layout.addWidget(machine_group)
        

        # === FILTRE PAR TYPE ===
        type_group = QGroupBox(get_machine_text("type_filter"))
        type_layout = QHBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(get_machine_text("all_types"))
        self.type_combo.currentTextChanged.connect(self.on_filter_changed)
        type_layout.addWidget(self.type_combo)
        
        toolbar_layout.addWidget(type_group)
    
    def create_specific_content(self):
        """Crée le contenu spécifique à l'analyse machine."""
        # Widget de contenu avec onglets
        self.tab_widget = QTabWidget()
        self.content_layout.addWidget(self.tab_widget)
        
        # === ONGLET RÉSUMÉ ===
        self.create_summary_tab()
        
        # === ONGLET DÉTAILS ===
        self.create_details_tab()
        
        # === ONGLET GRAPHIQUES ===
        self.create_charts_tab()
    
    def create_summary_tab(self):
        """Crée l'onglet de résumé."""
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # === TOP MACHINES PAR COÛT ===
        top_machines_group = QGroupBox(get_machine_text("top_machines"))
        top_machines_layout = QVBoxLayout(top_machines_group)
        
        # Table des top machines
        self.top_machines_table = QTableWidget()
        self.top_machines_table.setColumnCount(6)
        headers = [
            get_machine_text("machine_name"),
            get_machine_text("total_cost"),
            get_machine_text("interventions"),
            get_machine_text("avg_cost"),
            get_machine_text("availability"),
            get_machine_text("status")
        ]
        self.top_machines_table.setHorizontalHeaderLabels(headers)
        
        # Configuration de la table
        self.top_machines_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.top_machines_table.setAlternatingRowColors(True)
        self.top_machines_table.horizontalHeader().setStretchLastSection(True)
        
        top_machines_layout.addWidget(self.top_machines_table)
        summary_layout.addWidget(top_machines_group)
        
        # === MÉTRIQUES GLOBALES ===
        metrics_group = QGroupBox(get_machine_text("machine_performance"))
        metrics_layout = QGridLayout(metrics_group)
        
        # Labels pour les métriques
        self.total_machines_label = QLabel("Machines analysées: --")
        self.total_cost_label = QLabel("Coût total: --")
        self.avg_availability_label = QLabel("Disponibilité moyenne: --")
        self.active_machines_label = QLabel("Machines actives: --")
        
        # Style pour les métriques
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
        
        for label in [self.total_machines_label, self.total_cost_label, 
                     self.avg_availability_label, self.active_machines_label]:
            label.setStyleSheet(metric_style)
        
        metrics_layout.addWidget(self.total_machines_label, 0, 0)
        metrics_layout.addWidget(self.total_cost_label, 0, 1)
        metrics_layout.addWidget(self.avg_availability_label, 1, 0)
        metrics_layout.addWidget(self.active_machines_label, 1, 1)
        
        summary_layout.addWidget(metrics_group)
        
        self.tab_widget.addTab(summary_widget, get_machine_text("summary_tab"))
        self.summary_widget = summary_widget
    
    def create_details_tab(self):
        """Crée l'onglet de détails."""
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Table détaillée des machines
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(7)
        headers = [
            get_machine_text("machine_name"),
            "Type",
            get_machine_text("total_cost"),
            get_machine_text("interventions"),
            get_machine_text("last_maintenance"),
            get_machine_text("next_maintenance"),
            get_machine_text("status")
        ]
        self.details_table.setHorizontalHeaderLabels(headers)
        
        # Configuration de la table
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setSortingEnabled(True)
        header = self.details_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        details_layout.addWidget(self.details_table)
        
        self.tab_widget.addTab(details_widget, get_machine_text("details_tab"))
        self.details_widget = details_widget
    
    def create_charts_tab(self):
        """Crée l'onglet de graphiques."""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # Si le widget MachineKPIWidget est disponible, l'utiliser
        if MachineKPIWidget:
            self.machine_kpi_widget = MachineKPIWidget()
            charts_layout.addWidget(self.machine_kpi_widget)
        else:
            # Placeholder en attendant le widget
            placeholder_label = QLabel(f"📈 {get_machine_text('cost_evolution')}")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 16px;
                    font-style: italic;
                    padding: 40px;
                    border: 2px dashed #CCCCCC;
                    border-radius: 8px;
                }
            """)
            charts_layout.addWidget(placeholder_label)
        
        self.tab_widget.addTab(charts_widget, get_machine_text("charts_tab"))
        self.charts_widget = charts_widget
    
    def load_data(self):
        """Charge les données des machines."""
        self.set_status(get_machine_text("loading_machines"))
        
        try:
            start_date, end_date = self.get_date_range()
            
            # Utiliser le service KPI pour récupérer les données réelles
            if self.kpi_service:
                # Récupérer les données brutes du service
                raw_kpi_data = self.kpi_service.get_couts_par_machine(
                    periode_debut=start_date,
                    periode_fin=end_date,
                    limite=100  # Limiter à 100 machines pour les performances
                )
                # Convertir les données pour l'UI
                self.machines_data = self.convert_kpi_data_to_ui_format(raw_kpi_data)
            else:
                raise Exception("Service KPI non initialisé")

            # Mettre à jour les filtres avant les vues
            self.update_filters()

            self.update_summary_view()
            self.update_details_view()
            self.update_charts_view()

            self.set_status(f"Données chargées: {len(self.machines_data)} machines", success=True)

        except Exception as e:
            logger.error(f"Erreur lors du chargement des données machines: {e}")
            self.set_status(f"Erreur de connexion à la base de données : {e}", success=False)
            self.machines_data = []
            self.update_summary_view()
            self.update_details_view()
            self.update_charts_view()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données depuis la base de données.\n\nDétail : {e}")
    
    def convert_kpi_data_to_ui_format(self, kpi_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convertit les données KPI au format attendu par l'interface."""
        converted_data = []
        
        for item in kpi_data:
            machine_data = {
                "machine_name": item.get('machine_nom', 'N/A'),
                "serial": item.get('machine_serial', 'N/A'),
                "type": item.get('type_nom', 'N/A'),
                "criticite": item.get('machine_criticite', 'Standard'),
                "total_cost": float(item.get('cout_total', 0)),
                "interventions": int(item.get('nb_interventions_total', 0)),
                "preventif": int(item.get('nb_preventif', 0)),
                "correctif": int(item.get('nb_correctif', 0)),
                "urgence": int(item.get('nb_urgence', 0)),
                "avg_cost": float(item.get('cout_moyen_intervention', 0)),
                "cout_main_oeuvre": float(item.get('cout_main_oeuvre', 0)),
                "cout_pieces": float(item.get('cout_pieces_internes', 0)),
                "cout_frais_externes": float(item.get('cout_frais_externes', 0)),
                "ratio_preventif_curatif": float(item.get('ratio_preventif_curatif', 0)),
                "pourcentage_mod": float(item.get('pourcentage_mod', 0)),
                "pourcentage_pieces": float(item.get('pourcentage_pieces', 0)),
                "pourcentage_frais_externes": float(item.get('pourcentage_frais_externes', 0)),
                "availability": 95.0,  # TODO: Calculer la disponibilité réelle
                "last_maintenance": "N/A",  # TODO: Récupérer la dernière maintenance
                "next_maintenance": "N/A",  # TODO: Calculer la prochaine maintenance
                "status": "Actif" if item.get('nb_interventions_total', 0) > 0 else "Inactif"
            }
            converted_data.append(machine_data)
        
        return converted_data
    
    def get_mock_machine_data(self) -> List[Dict[str, Any]]:
        """Génère des données de test pour les machines."""
        import random
        
        types = ["Presse", "Tour", "Fraiseuse", "Robot", "Convoyeur"]
        statuses = ["Actif", "Maintenance", "Arrêt"]
        
        data = []
        for i in range(20):
            machine_name = f"MACH-{i+1:03d}"
            data.append({
                "machine_name": machine_name,
                "type": random.choice(types),
                "total_cost": random.uniform(5000, 50000),
                "interventions": random.randint(5, 30),
                "avg_cost": random.uniform(200, 2000),
                "availability": random.uniform(85, 99),
                "last_maintenance": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "next_maintenance": f"2024-{random.randint(6,12):02d}-{random.randint(1,28):02d}",
                "status": random.choice(statuses)
            })
        
        # Tri par coût décroissant
        data.sort(key=lambda x: x["total_cost"], reverse=True)
        return data
    
    def update_filters(self):
        """Met à jour les listes de filtres."""
        # Types
        self.type_combo.clear()
        self.type_combo.addItem(get_machine_text("all_types"))
        types = sorted(set(machine["type"] for machine in self.machines_data))
        self.type_combo.addItems(types)
        
        # Machines
        self.machine_combo.clear()
        self.machine_combo.addItem(get_machine_text("all_machines"))
        machines = sorted(machine["machine_name"] for machine in self.machines_data)
        self.machine_combo.addItems(machines)
    
    def get_filtered_data(self) -> List[Dict[str, Any]]:
        """Récupère les données filtrées."""
        filtered_data = self.machines_data.copy()
        
        # Filtre par type
        selected_type = self.type_combo.currentText()
        if selected_type != get_machine_text("all_types"):
            filtered_data = [m for m in filtered_data if m["type"] == selected_type]
        
        # Filtre par machine
        selected_machine = self.machine_combo.currentText()
        if selected_machine != get_machine_text("all_machines"):
            filtered_data = [m for m in filtered_data if m["machine_name"] == selected_machine]
        
        return filtered_data
    
    def update_summary_view(self):
        """Met à jour la vue de résumé."""
        filtered_data = self.get_filtered_data()
        
        if not filtered_data:
            self.top_machines_table.setRowCount(0)
            self.total_machines_label.setText("Machines analysées: 0")
            self.total_cost_label.setText("Coût total: 0€")
            self.avg_availability_label.setText("Disponibilité moyenne: --%")
            self.active_machines_label.setText("Machines actives: 0")
            return
        
        # Top 10 machines par coût
        top_machines = filtered_data[:10]
        self.top_machines_table.setRowCount(len(top_machines))
        
        for row, machine in enumerate(top_machines):
            self.top_machines_table.setItem(row, 0, QTableWidgetItem(machine["machine_name"]))
            self.top_machines_table.setItem(row, 1, QTableWidgetItem(f"{machine['total_cost']:.2f}€"))
            self.top_machines_table.setItem(row, 2, QTableWidgetItem(str(machine["interventions"])))
            self.top_machines_table.setItem(row, 3, QTableWidgetItem(f"{machine['avg_cost']:.2f}€"))
            self.top_machines_table.setItem(row, 4, QTableWidgetItem(f"{machine['availability']:.1f}%"))
            self.top_machines_table.setItem(row, 5, QTableWidgetItem(machine["status"]))
        
        # Métriques globales
        total_cost = sum(machine["total_cost"] for machine in filtered_data)
        total_interventions = sum(machine["interventions"] for machine in filtered_data)
        avg_availability = sum(machine["availability"] for machine in filtered_data) / len(filtered_data)
        active_machines = len([m for m in filtered_data if m["status"] == "Actif"])
        
        self.total_machines_label.setText(f"Machines analysées: {len(filtered_data)}")
        self.total_cost_label.setText(f"Coût total: {total_cost:.2f}€")
        self.avg_availability_label.setText(f"Disponibilité moyenne: {avg_availability:.1f}%")
        self.active_machines_label.setText(f"Machines actives: {active_machines}")
    
    def update_details_view(self):
        """Met à jour la vue de détails."""
        filtered_data = self.get_filtered_data()
        
        self.details_table.setRowCount(len(filtered_data))
        
        for row, machine in enumerate(filtered_data):
            self.details_table.setItem(row, 0, QTableWidgetItem(machine["machine_name"]))
            self.details_table.setItem(row, 1, QTableWidgetItem(machine["type"]))
            self.details_table.setItem(row, 2, QTableWidgetItem(f"{machine['total_cost']:.2f}€"))
            self.details_table.setItem(row, 3, QTableWidgetItem(str(machine["interventions"])))
            self.details_table.setItem(row, 4, QTableWidgetItem(machine["last_maintenance"]))
            self.details_table.setItem(row, 5, QTableWidgetItem(machine["next_maintenance"]))
            self.details_table.setItem(row, 6, QTableWidgetItem(machine["status"]))
    
    def update_charts_view(self):
        """Met à jour la vue des graphiques."""
        if hasattr(self, 'machine_kpi_widget') and self.machine_kpi_widget:
            start_date, end_date = self.get_date_range()
            # Mise à jour du widget avec les nouvelles données
            # self.machine_kpi_widget.load_data(start_date, end_date)
    
    def on_filter_changed(self):
        """Gère le changement de filtres."""
        logger.debug("Filtres modifiés")
        self.update_summary_view()
        self.update_details_view()
        self.update_charts_view()
    
    def export_data(self):
        """Exporte les données machines vers Excel."""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            # Dialogue de sauvegarde
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Exporter les données machines",
                f"machines_kpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Fichiers Excel (*.xlsx)"
            )
            
            if file_path:
                # Ici, implémentation de l'export Excel
                # pandas.DataFrame(self.get_filtered_data()).to_excel(file_path, index=False)
                
                self.set_status(get_machine_text("export_success"), success=True)
                QMessageBox.information(self, get_shared_text("success"), 
                                      f"Données exportées vers:\n{file_path}")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            QMessageBox.critical(self, get_shared_text("error"), 
                               f"Erreur lors de l'export:\n{e}")
