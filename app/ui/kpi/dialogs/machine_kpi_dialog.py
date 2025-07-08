#machine_kpi_dialog.py
#!/usr/bin/env python3
"""
Dialog d'analyse KPI par machine - Version améliorée.
Interface moderne avec cartes visuelles, graphiques intégrés et filtres avancés.
"""

import sys
import os
import importlib.util
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Imports PySide6
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QFrame, QLineEdit,
    QGroupBox, QTableWidget, QTableWidgetItem, QScrollArea,
    QHeaderView, QAbstractItemView, QTabWidget, QSplitter,
    QMessageBox, QWidget, QProgressBar, QSlider, QCheckBox, QSizePolicy
)

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter

# Import de la classe de base
from .base_kpi_dialog import BaseKPIDialog, get_shared_text
from .machine_kpi_styles import MODERN_STYLE, CARD_COLORS, get_card_style, STATUS_STYLES

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
    Language.ENGLISH: {
        "title": "📊 Machine KPI Analysis",
        "machine_filter": "🔍 Filter by Machine",
        "all_machines": "🏭 All machines",
        "type_filter": "⚙️ Machine Type",
        "all_types": "📋 All types",
        "search_placeholder": "🔍 Search for a machine...",
        "data_tab": "📊 Overview",
        "charts_tab": "📈 Charts & Trends",
        "details_tab": "🔧 Technical Details",
        "performance_tab": "⚡ Performance",
        "top_machines": "🔝 Top Machines by Cost",
        "machine_performance": "⚡ Key Indicators",
        "summary_totals": "📊 Global Summary",
        "machine_cards": "🏭 Machine Cards",
        "grand_total_cost": "💰 Total Cost:",
        "grand_avg_cost": "📊 Average Cost:",
        "cost_evolution": "📈 Cost Evolution",
        "machine_name": "Machine",
        "total_cost": "Total Cost (€)",
        "interventions": "Interventions",
        "avg_cost": "Average Cost (€)",
        "availability": "Availability (%)",
        "last_maintenance": "Last Maintenance",
        "next_maintenance": "Next Maintenance",
        "status": "Status",
        "critical_machines": "⚠️ Critical Machines",
        "active_machines": "✅ Active Machines", 
        "inactive_machines": "⏸️ Inactive Machines",
        "total_machines": "🏭 Total Machines",
        "total_intervention_time": "⏱️ Total Time (h)",
        "avg_intervention_time": "⏱️ Average Time (h)",
        "preventive_ratio": "🛡️ Preventive Ratio",
        "corrective_ratio": "🔧 Corrective Ratio",
        "urgency_ratio": "🚨 Urgency Ratio",
        "maintenance_efficiency": "⚡ Maintenance Efficiency",
        "no_data_message": "No machine data available for this period",
        "loading_machines": "Loading machine data...",
        "export_success": "Machine data exported successfully",
        "filter_by_status": "🎚️ Filter by Status",
        "filter_by_criticality": "⚠️ Filter by Criticality",
        "show_only_critical": "Critical machines only",
        "show_charts": "📊 Show charts",
        "refresh_data": "🔄 Refresh",
        "export_excel": "📄 Excel",
        "export_pdf": "📑 PDF",
        "export_csv": "📝 CSV",
        "advanced_filters": "🎚️ Advanced Filters",
        "status_filter": "Status:",
        "limit_filter": "Limit:",
        "statistics_selection": "📊 Selection Statistics",
        "chart_options": "📊 Chart Options",
        "chart_type": "Chart type:",
        "show_details": "📈 Show details",
        "charts_in_development": "Charts under development",
        "visualizations_coming_soon": "Visualizations will be available soon",
        "machine_details": "Details",
        "type": "Type:",
        "status": "Status:",
        "criticality": "Criticality:",
        "total_cost_detail": "💰 Total Cost:",
        "interventions_detail": "🔧 Interventions:",
        "preventive_detail": "🛡️ Preventive:",
        "corrective_detail": "🔧 Corrective:",
        "urgency_detail": "🚨 Urgency:",
        "total_time_detail": "⏱️ Total Time:",
        "avg_cost_detail": "📊 Avg Cost:",
        "all_statuses": "All statuses",
        "active_status": "Active",
        "attention_status": "Attention",
        "inactive_status": "Inactive"
    },
    Language.FRENCH: {
        "title": "📊 Analyse KPI par Machine",
        "machine_filter": "🔍 Filtrer par Machine",
        "all_machines": "🏭 Toutes les machines",
        "type_filter": "⚙️ Type de Machine",
        "all_types": "📋 Tous les types",
        "search_placeholder": "🔍 Rechercher une machine...",
        "data_tab": "📊 Vue d'ensemble",
        "charts_tab": "📈 Graphiques & Tendances",
        "details_tab": "🔧 Détails techniques",
        "performance_tab": "⚡ Performance",
        "top_machines": "🔝 Top Machines par Coût",
        "machine_performance": "⚡ Indicateurs Clés",
        "summary_totals": "📊 Résumé Global",
        "machine_cards": "🏭 Cartes Machines",
        "grand_total_cost": "💰 Coût Total:",
        "grand_avg_cost": "📊 Coût Moyen:",
        "cost_evolution": "📈 Évolution des Coûts",
        "machine_name": "Machine",
        "total_cost": "Coût Total (€)",
        "interventions": "Interventions",
        "avg_cost": "Coût Moyen (€)",
        "availability": "Disponibilité (%)",
        "last_maintenance": "Dernière Maintenance",
        "next_maintenance": "Prochaine Maintenance",
        "status": "Statut",
        "critical_machines": "⚠️ Machines Critiques",
        "active_machines": "✅ Machines Actives", 
        "inactive_machines": "⏸️ Machines Inactives",
        "total_machines": "🏭 Total Machines",
        "total_intervention_time": "⏱️ Temps Total (h)",
        "avg_intervention_time": "⏱️ Temps Moyen (h)",
        "preventive_ratio": "🛡️ Ratio Préventif",
        "corrective_ratio": "🔧 Ratio Correctif",
        "urgency_ratio": "🚨 Ratio Urgence",
        "maintenance_efficiency": "⚡ Efficacité Maintenance",
        "no_data_message": "Aucune donnée de machine disponible pour cette période",
        "loading_machines": "Chargement des données machines...",
        "export_success": "Données machines exportées avec succès",
        "filter_by_status": "🎚️ Filtrer par Statut",
        "filter_by_criticality": "⚠️ Filtrer par Criticité",
        "show_only_critical": "Machines critiques uniquement",
        "show_charts": "📊 Afficher graphiques",
        "refresh_data": "🔄 Actualiser",
        "export_excel": "📄 Excel",
        "export_pdf": "📑 PDF",
        "export_csv": "📝 CSV",
        "advanced_filters": "🎚️ Filtres Avancés",
        "status_filter": "Statut:",
        "limit_filter": "Limite:",
        "statistics_selection": "📊 Statistiques de la Sélection",
        "chart_options": "📊 Options des Graphiques",
        "chart_type": "Type de graphique:",
        "show_details": "📈 Afficher détails",
        "charts_in_development": "Graphiques en cours de développement",
        "visualizations_coming_soon": "Les visualisations seront bientôt disponibles",
        "machine_details": "Détails",
        "type": "Type:",
        "status": "Statut:",
        "criticality": "Criticité:",
        "total_cost_detail": "💰 Coût Total:",
        "interventions_detail": "🔧 Interventions:",
        "preventive_detail": "🛡️ Préventif:",
        "corrective_detail": "🔧 Correctif:",
        "urgency_detail": "🚨 Urgence:",
        "total_time_detail": "⏱️ Temps Total:",
        "avg_cost_detail": "📊 Coût Moyen:",
        "all_statuses": "Tous les statuts",
        "active_status": "Actif",
        "attention_status": "Attention", 
        "inactive_status": "Inactif"
    },
    Language.ENGLISH: {
        "title": "📊 Machine KPI Analysis",
        "machine_filter": "🔍 Filter by Machine",
        "all_machines": "🏭 All machines",
        "type_filter": "⚙️ Machine Type",
        "all_types": "📋 All types",
        "search_placeholder": "🔍 Search for a machine...",
        "data_tab": "📊 Overview",
        "charts_tab": "📈 Charts & Trends",
        "details_tab": "🔧 Technical Details",
        "performance_tab": "⚡ Performance",
        "top_machines": "🔝 Top Machines by Cost",
        "machine_performance": "⚡ Key Indicators",
        "summary_totals": "📊 Global Summary",
        "machine_cards": "🏭 Machine Cards",
        "grand_total_cost": "💰 Total Cost:",
        "grand_avg_cost": "📊 Average Cost:",
        "cost_evolution": "📈 Cost Evolution",
        "machine_name": "Machine",
        "total_cost": "Total Cost (€)",
        "interventions": "Interventions",
        "avg_cost": "Average Cost (€)",
        "availability": "Availability (%)",
        "last_maintenance": "Last Maintenance",
        "next_maintenance": "Next Maintenance",
        "status": "Status",
        "critical_machines": "⚠️ Critical Machines",
        "active_machines": "✅ Active Machines", 
        "inactive_machines": "⏸️ Inactive Machines",
        "total_machines": "🏭 Total Machines",
        "total_intervention_time": "⏱️ Total Time (h)",
        "avg_intervention_time": "⏱️ Average Time (h)",
        "preventive_ratio": "🛡️ Preventive Ratio",
        "corrective_ratio": "🔧 Corrective Ratio",
        "urgency_ratio": "🚨 Urgency Ratio",
        "maintenance_efficiency": "⚡ Maintenance Efficiency",
        "no_data_message": "No machine data available for this period",
        "loading_machines": "Loading machine data...",
        "export_success": "Machine data exported successfully",
        "filter_by_status": "🎚️ Filter by Status",
        "filter_by_criticality": "⚠️ Filter by Criticality",
        "show_only_critical": "Critical machines only",
        "show_charts": "📊 Show charts",
        "refresh_data": "🔄 Refresh",
        "export_excel": "📄 Excel",
        "export_pdf": "📑 PDF",
        "export_csv": "📝 CSV",
        "advanced_filters": "🎚️ Advanced Filters",
        "status_filter": "Status:",
        "limit_filter": "Limit:",
        "statistics_selection": "📊 Selection Statistics",
        "chart_options": "📊 Chart Options",
        "chart_type": "Chart type:",
        "show_details": "📈 Show details",
        "charts_in_development": "Charts under development",
        "visualizations_coming_soon": "Visualizations will be available soon",
        "machine_details": "Details",
        "type": "Type:",
        "status": "Status:",
        "criticality": "Criticality:",
        "total_cost_detail": "💰 Total Cost:",
        "interventions_detail": "🔧 Interventions:",
        "preventive_detail": "🛡️ Preventive:",
        "corrective_detail": "🔧 Corrective:",
        "urgency_detail": "🚨 Urgency:",
        "total_time_detail": "⏱️ Total Time:",
        "avg_cost_detail": "📊 Avg Cost:",
        "all_statuses": "All statuses",
        "active_status": "Active",
        "attention_status": "Attention",
        "inactive_status": "Inactive"
    },
    Language.GERMAN: {
        "title": "📊 Maschinen-KPI-Analyse",
        "machine_filter": "🔍 Nach Maschine filtern",
        "all_machines": "🏭 Alle Maschinen",
        "type_filter": "⚙️ Maschinentyp",
        "all_types": "📋 Alle Typen",
        "search_placeholder": "🔍 Maschine suchen...",
        "data_tab": "📊 Übersicht",
        "charts_tab": "📈 Diagramme & Trends",
        "details_tab": "🔧 Technische Details",
        "performance_tab": "⚡ Leistung",
        "top_machines": "🔝 Top Maschinen nach Kosten",
        "machine_performance": "⚡ Kennzahlen",
        "summary_totals": "📊 Globale Zusammenfassung",
        "machine_cards": "🏭 Maschinenkarten",
        "grand_total_cost": "💰 Gesamtkosten:",
        "grand_avg_cost": "📊 Durchschnittskosten:",
        "cost_evolution": "📈 Kostenentwicklung",
        "machine_name": "Maschine",
        "total_cost": "Gesamtkosten (€)",
        "interventions": "Interventionen",
        "avg_cost": "Durchschnittskosten (€)",
        "availability": "Verfügbarkeit (%)",
        "last_maintenance": "Letzte Wartung",
        "next_maintenance": "Nächste Wartung",
        "status": "Status",
        "critical_machines": "⚠️ Kritische Maschinen",
        "active_machines": "✅ Aktive Maschinen", 
        "inactive_machines": "⏸️ Inaktive Maschinen",
        "total_machines": "🏭 Maschinen Gesamt",
        "total_intervention_time": "⏱️ Gesamtzeit (h)",
        "avg_intervention_time": "⏱️ Durchschnitt Zeit (h)",
        "preventive_ratio": "🛡️ Präventiv-Verhältnis",
        "corrective_ratio": "🔧 Korrektiv-Verhältnis",
        "urgency_ratio": "🚨 Notfall-Verhältnis",
        "maintenance_efficiency": "⚡ Wartungseffizienz",
        "no_data_message": "Keine Maschinendaten für diesen Zeitraum verfügbar",
        "loading_machines": "Lade Maschinendaten...",
        "export_success": "Maschinendaten erfolgreich exportiert",
        "filter_by_status": "🎚️ Nach Status filtern",
        "filter_by_criticality": "⚠️ Nach Kritikalität filtern",
        "show_only_critical": "Nur kritische Maschinen",
        "show_charts": "📊 Diagramme anzeigen",
        "refresh_data": "🔄 Aktualisieren",
        "export_excel": "📄 Excel",
        "export_pdf": "📑 PDF",
        "export_csv": "📝 CSV",
        "advanced_filters": "🎚️ Erweiterte Filter",
        "status_filter": "Status:",
        "limit_filter": "Limit:",
        "statistics_selection": "📊 Auswahlstatistiken",
        "chart_options": "📊 Diagrammoptionen",
        "chart_type": "Diagrammtyp:",
        "show_details": "📈 Details anzeigen",
        "charts_in_development": "Diagramme in Entwicklung",
        "visualizations_coming_soon": "Visualisierungen werden bald verfügbar sein",
        "machine_details": "Details",
        "type": "Typ:",
        "status": "Status:",
        "criticality": "Kritikalität:",
        "total_cost_detail": "💰 Gesamtkosten:",
        "interventions_detail": "🔧 Interventionen:",
        "preventive_detail": "🛡️ Präventiv:",
        "corrective_detail": "🔧 Korrektiv:",
        "urgency_detail": "🚨 Dringend:",
        "total_time_detail": "⏱️ Gesamtzeit:",
        "avg_cost_detail": "📊 Ø Kosten:",
        "all_statuses": "Alle Status",
        "active_status": "Aktiv",
        "attention_status": "Achtung",
        "inactive_status": "Inaktiv"
    }
}

def get_machine_text(key: str) -> str:
    """Récupère le texte traduit selon la langue configurée."""
    try:
        current_lang = app_config.language if 'app_config' in globals() else Language.ENGLISH
        return MACHINE_TRANSLATIONS.get(current_lang, MACHINE_TRANSLATIONS[Language.ENGLISH]).get(key, key)
    except:
        return MACHINE_TRANSLATIONS[Language.ENGLISH].get(key, key)


class MachineKPIDialog(BaseKPIDialog):
    """
    Dialog d'analyse KPI par machine - Version améliorée.
    
    Nouvelles fonctionnalités:
    - Interface moderne avec cartes visuelles
    - Graphiques intégrés directement dans l'interface  
    - Filtres avancés avec recherche textuelle
    - Indicateurs visuels de performance
    - Tri et export multiples
    - Animations et transitions fluides
    """
    
    def __init__(self, parent=None):
        # Initialisation avec le titre spécifique
        super().__init__(parent, get_machine_text("title"))
        
        # Données spécifiques aux machines
        self.machines_data = []
        self.machine_types = []
        self.filtered_data = []
        self.current_sort_column = 2  # Trier par coût par défaut
        self.current_sort_order = Qt.DescendingOrder
        
        # Configuration du style moderne
        self.setup_modern_style()
        
        # Utiliser un timer pour configurer les scrollbars après l'initialisation complète
        QTimer.singleShot(100, self.configure_scroll_policies)
        
        # Configurer une taille optimale pour éviter les problèmes de scroll
        self.resize(1440, 900)  # Taille plus adaptée aux écrans modernes
        self.setMinimumSize(1300, 800)  # Taille minimale pour assurer une bonne visibilité
        
        logger.info("Initialisation du MachineKPIDialog - Version améliorée")
    
    def configure_scroll_policies(self):
        """Configure les politiques de scroll après l'initialisation complète."""
        # Plus de scroll_area globale, donc on configure seulement le tableau
        if hasattr(self, 'data_table'):
            self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.data_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    def setup_modern_style(self):
        """Configure le style moderne pour l'interface."""
        self.setStyleSheet(MODERN_STYLE)
    
    def create_content_area(self, parent_layout):
        """Surcharge pour éliminer complètement la scroll area globale problématique."""
        # Au lieu d'utiliser une scroll area, créer directement le widget de contenu
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        # Appel de la méthode abstraite pour créer le contenu spécifique
        self.create_specific_content()
        
        # Ajouter directement le content_widget sans scroll area
        parent_layout.addWidget(self.content_widget)
        
        # Pas de scroll_area pour ce dialog
        self.scroll_area = None
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute les filtres spécifiques aux machines sur une seule ligne."""
        
        # Container principal pour les filtres
        filters_container = QFrame()
        filters_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                margin: 5px;
            }
        """)
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setSpacing(15)
        filters_layout.setContentsMargins(15, 15, 15, 15)
        
        # === FILTRE PAR MACHINE ===
        machine_group = QGroupBox(get_machine_text("machine_filter"))
        machine_layout = QHBoxLayout(machine_group)
        
        self.machine_combo = QComboBox()
        self.machine_combo.addItem(get_machine_text("all_machines"))
        self.machine_combo.currentTextChanged.connect(self.on_filter_changed)
        self.machine_combo.setMinimumWidth(180)
        machine_layout.addWidget(self.machine_combo)
        
        filters_layout.addWidget(machine_group)
        
        # === FILTRE PAR TYPE ===
        type_group = QGroupBox(get_machine_text("type_filter"))
        type_layout = QHBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(get_machine_text("all_types"))
        self.type_combo.currentTextChanged.connect(self.on_filter_changed)
        self.type_combo.setMinimumWidth(180)
        type_layout.addWidget(self.type_combo)
        
        filters_layout.addWidget(type_group)
        
        # === FILTRES AVANCÉS ===
        advanced_group = QGroupBox(get_machine_text("advanced_filters"))
        advanced_layout = QHBoxLayout(advanced_group)
        
        # Filtre par statut
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            get_machine_text("all_statuses"), 
            get_machine_text("active_status"), 
            get_machine_text("attention_status"), 
            get_machine_text("inactive_status")
        ])
        self.status_combo.currentTextChanged.connect(self.on_filter_changed)
        advanced_layout.addWidget(QLabel(get_machine_text("status_filter")))
        advanced_layout.addWidget(self.status_combo)
        
        # Checkbox pour machines critiques uniquement
        self.critical_only_checkbox = QCheckBox(get_machine_text("show_only_critical"))
        self.critical_only_checkbox.stateChanged.connect(self.on_filter_changed)
        advanced_layout.addWidget(self.critical_only_checkbox)
        
        # Slider pour le nombre max de résultats
        advanced_layout.addWidget(QLabel(get_machine_text("limit_filter")))
        self.limit_slider = QSlider(Qt.Horizontal)
        self.limit_slider.setRange(10, 100)
        self.limit_slider.setValue(50)
        self.limit_slider.setTickPosition(QSlider.TicksBelow)
        self.limit_slider.setTickInterval(10)
        self.limit_slider.valueChanged.connect(self.on_limit_changed)
        advanced_layout.addWidget(self.limit_slider)
        
        self.limit_label = QLabel("50")
        self.limit_label.setMinimumWidth(30)
        advanced_layout.addWidget(self.limit_label)
        
        filters_layout.addWidget(advanced_group)
        
        toolbar_layout.addWidget(filters_container)
    
    def on_limit_changed(self, value):
        """Gère le changement de limite de résultats."""
        self.limit_label.setText(str(value))
        self.apply_filters_and_update_views()
    
    def on_filter_changed(self):
        """Gère le changement de filtres en appelant la logique centrale."""
        logger.debug("Filtres modifiés, déclenchement de la mise à jour.")
        self.apply_filters_and_update_views()
    
    def export_data(self, format_type='excel'):
        """Exporte les données machines dans le format spécifié."""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            if not self.filtered_data:
                QMessageBox.warning(self, "Attention", "Aucune donnée à exporter")
                return
            
            # Préparer les données pour l'export
            export_data = []
            for machine in self.filtered_data:
                export_data.append({
                    'Machine': machine['machine_name'],
                    'Type': machine['type'],
                    'Site': machine.get('site', 'N/A'),
                    'Statut': machine['status'],
                    'Criticité': machine.get('criticite', 'Standard'),
                    'Coût Total (€)': machine['total_cost'],
                    'Nombre Interventions': machine['interventions'],
                    'Interventions Préventives': machine.get('preventif', 0),
                    'Interventions Correctives': machine.get('correctif', 0),
                    'Interventions Urgence': machine.get('urgence', 0),
                    'Temps Total (h)': machine['total_intervention_time'],
                    'Temps Moyen (h)': machine['avg_intervention_time'],
                    'Coût Moyen (€)': machine['avg_cost'],
                    'Ratio Préventif/Correctif': machine.get('ratio_preventif_curatif', 0),
                    'Dernière Maintenance': machine['last_maintenance'],
                    'Prochaine Maintenance': machine['next_maintenance']
                })
            
            # Déterminer l'extension et le filtre
            if format_type == 'excel':
                ext = 'xlsx'
                filter_str = "Fichiers Excel (*.xlsx)"
            elif format_type == 'csv':
                ext = 'csv'
                filter_str = "Fichiers CSV (*.csv)"
            else:
                ext = 'xlsx'
                filter_str = "Fichiers Excel (*.xlsx)"
            
            # Dialogue de sauvegarde
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Exporter les données machines ({format_type.upper()})",
                f"machines_kpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                filter_str
            )
            
            if file_path:
                # Export selon le format
                if format_type == 'excel':
                    self._export_to_excel(export_data, file_path)
                elif format_type == 'csv':
                    self._export_to_csv(export_data, file_path)
                
                self.set_status(get_machine_text("export_success"), success=True)
                QMessageBox.information(
                    self, 
                    "Succès", 
                    f"Données exportées avec succès vers:\n{file_path}\n\n"
                    f"Format: {format_type.upper()}\n"
                    f"Nombre de machines: {len(self.filtered_data)}"
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export {format_type}: {e}")
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Erreur lors de l'export {format_type}:\n{e}"
            )
    
    def _export_to_csv(self, data, file_path):
        """Exporte les données vers un fichier CSV."""
        import csv
        
        if not data:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
    
    def _export_to_excel(self, data, file_path):
        """Exporte les données vers un fichier Excel."""
        try:
            # Import dynamique de pandas pour éviter les erreurs de compilation
            import importlib.util
            pandas_spec = importlib.util.find_spec("pandas")
            if pandas_spec is not None:
                import pandas as pd  # type: ignore
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False, sheet_name='Machines KPI')
            else:
                raise ImportError("pandas non disponible")
        except ImportError:
            # Fallback vers CSV si pandas n'est pas disponible
            csv_path = file_path.replace('.xlsx', '.csv')
            self._export_to_csv(data, csv_path)
            QMessageBox.information(
                self,
                "Information",
                f"pandas n'est pas installé.\nExport effectué en CSV vers:\n{csv_path}"
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            QMessageBox.critical(
                self, 
                "Erreur", 
                f"Erreur lors de l'export Excel:\n{e}"
            )
    
    def create_specific_content(self):
        """Crée le contenu spécifique à l'analyse machine simplifié."""
        
        # === ONGLETS PRINCIPAUX ===
        self.tab_widget = QTabWidget()
        
        # Configuration du QTabWidget pour occuper tout l'espace disponible
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Ajouter le tab_widget avec stretch factor pour qu'il prenne tout l'espace
        self.content_layout.addWidget(self.tab_widget, 1)

        # === CRÉATION DES ONGLETS ===
        self.create_overview_tab()
        self.create_charts_tab()
    
    def create_overview_tab(self):
        """Crée l'onglet de vue d'ensemble amélioré."""
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)

        # === RÉSUMÉ STATISTIQUE (au-dessus du tableau) - UNE SEULE LIGNE ===
        stats_group = QGroupBox(get_machine_text("statistics_selection"))
        stats_layout = QHBoxLayout(stats_group)  # Layout horizontal au lieu de GridLayout
        stats_layout.setSpacing(15)
        
        self.selection_stats_labels = {}
        stats_items = [
            ("total_machines", "Machines:", "🏭"),
            ("total_cost", "Coût Total:", "💰"),
            ("avg_cost", "Coût Moyen:", "📊"),
            ("total_interventions", "Interventions:", "🔧"),
            ("preventive_ratio", "Ratio Préventif:", "🛡️"),
            ("efficiency", "Efficacité:", "⚡")
        ]
        
        for key, label, icon in stats_items:
            container = QFrame()
            container.setStyleSheet("""
                QFrame { 
                    background-color: #f8f9fa; 
                    border-radius: 6px; 
                    border: 1px solid #e9ecef; 
                    padding: 8px;
                    min-width: 160px;
                    max-height: 42px;
                }
            """)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(4, 4, 8, 4)
            layout.setSpacing(6)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 10px; min-width: 15px; max-width: 15px;")  # Icône plus petite et largeur fixe
            icon_label.setAlignment(Qt.AlignCenter)
            
            text_label = QLabel(f"{label} --")
            text_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px;")  # Police légèrement plus grande
            text_label.setWordWrap(False)  # Éviter le retour à la ligne
            
            layout.addWidget(icon_label, 0)  # L'icône ne prend pas d'espace supplémentaire
            layout.addWidget(text_label, 1)  # Le texte prend tout l'espace restant
            
            self.selection_stats_labels[key] = text_label
            stats_layout.addWidget(container)
        
        # Ajouter un stretch à la fin pour centrer les boîtes
        stats_layout.addStretch()
        
        overview_layout.addWidget(stats_group)

        # === TABLEAU INDÉPENDANT (en dehors du cadre) ===
        # Créer directement le tableau sans GroupBox
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(14)
        headers = [
            "Machine", "Type", "Statut", "Coût Total (€)", 
            "Interventions", "Préventif", "Correctif", "Urgence",
            "Temps Total (h)", "Coût Moyen (€)", "Temps Moyen (h)",
            "Dernière Maint.", "Criticité", "Ratio P/C"
        ]
        self.data_table.setHorizontalHeaderLabels(headers)
        
        # Configuration avancée du tableau
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSortingEnabled(True)
        self.data_table.verticalHeader().setVisible(False)
        
        # Style du tableau avec titre intégré
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                selection-background-color: #3498db;
                selection-color: white;
                font-size: 11px;
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        
        # Configuration des colonnes
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Machine
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Statut
        
        # Double-clic pour voir les détails
        self.data_table.doubleClicked.connect(self.show_machine_details)
        
        # Configuration basique du tableau - optimisé pour remplir l'espace disponible
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # S'assurer que le tableau utilise tout l'espace disponible de l'onglet
        self.data_table.setMinimumHeight(400)  # Hauteur minimale raisonnable
        
        # Ajouter directement le tableau à l'overview_layout avec stretch factor maximal
        overview_layout.addWidget(self.data_table, 1)  # Le tableau prend tout l'espace restant
        
        self.tab_widget.addTab(overview_widget, get_machine_text("data_tab"))
        self.overview_widget = overview_widget
    
    def show_machine_details(self, index):
        """Affiche les détails d'une machine sélectionnée."""
        row = index.row()
        if row < len(self.filtered_data):
            machine = self.filtered_data[row]
            
            # Créer une popup avec les détails de la machine
            details_dialog = QMessageBox(self)
            details_dialog.setWindowTitle(f"{get_machine_text('machine_details')} - {machine['machine_name']}")
            details_dialog.setIcon(QMessageBox.Information)
            
            details_text = f"""
            <h3>🏭 {machine['machine_name']}</h3>
            <p><b>{get_machine_text('type')}</b> {machine['type']}</p>
            <p><b>{get_machine_text('status')}</b> {machine['status']}</p>
            <p><b>{get_machine_text('criticality')}</b> {machine.get('criticite', 'N/A')}</p>
            <hr>
            <p><b>{get_machine_text('total_cost_detail')}</b> {machine['total_cost']:.2f}€</p>
            <p><b>{get_machine_text('interventions_detail')}</b> {machine['interventions']}</p>
            <p><b>{get_machine_text('preventive_detail')}</b> {machine.get('preventif', 0)}</p>
            <p><b>{get_machine_text('corrective_detail')}</b> {machine.get('correctif', 0)}</p>
            <p><b>{get_machine_text('urgency_detail')}</b> {machine.get('urgence', 0)}</p>
            <hr>
            <p><b>{get_machine_text('total_time_detail')}</b> {machine['total_intervention_time']:.1f}h</p>
            <p><b>{get_machine_text('avg_cost_detail')}</b> {machine['avg_cost']:.2f}€</p>
            """
            
            details_dialog.setText(details_text)
            details_dialog.exec()
    
    def create_data_tab(self):
        """Méthode de compatibilité - redirige vers create_overview_tab."""
        # Cette méthode existe pour la compatibilité avec l'ancien code
        pass
    
    def create_charts_tab(self):
        """Crée l'onglet de graphiques modernisé avec le nouveau widget spécialisé."""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        
        # Importer le nouveau widget graphique
        try:
            from .machine_kpi_chart_widget import MachineKPIChartWidget
            from .machine_kpi_chart_translations import get_chart_text
            
            # Créer le widget graphique spécialisé
            self.chart_widget = MachineKPIChartWidget()
            
            # Connecter les signaux
            self.chart_widget.filters_changed.connect(self.on_chart_filters_changed)
            self.chart_widget.chart_updated.connect(self.on_chart_updated)
            
            # Ajouter le widget à l'onglet
            charts_layout.addWidget(self.chart_widget)
            
            # Initialiser avec les données disponibles
            self.update_chart_data()
            
            # Titre de l'onglet avec traduction
            tab_title = get_chart_text("charts_tab_title")
            
        except ImportError as e:
            logger.error(f"Erreur d'import du widget graphique: {e}")
            
            # Fallback en cas d'erreur d'import
            placeholder_frame = QFrame()
            placeholder_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f8f9fa, stop:1 #e9ecef);
                    border: 2px dashed #bdc3c7;
                    border-radius: 15px;
                }
            """)
            placeholder_layout = QVBoxLayout(placeholder_frame)
            
            icon_label = QLabel("📈")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px; color: #95a5a6; margin: 20px;")
            
            text_label = QLabel("Graphique en cours de développement")
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setStyleSheet("""
                font-size: 18px; 
                color: #7f8c8d; 
                font-weight: bold;
                margin: 10px;
            """)
            
            subtitle_label = QLabel(f"Erreur: {e}")
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setStyleSheet("font-size: 12px; color: #e74c3c; font-style: italic;")
            
            placeholder_layout.addStretch()
            placeholder_layout.addWidget(icon_label)
            placeholder_layout.addWidget(text_label)
            placeholder_layout.addWidget(subtitle_label)
            placeholder_layout.addStretch()
            
            charts_layout.addWidget(placeholder_frame)
            
            tab_title = get_machine_text("charts_tab")
        
        self.tab_widget.addTab(charts_widget, tab_title)
        self.charts_widget = charts_widget
    
    def load_data(self):
        """Charge les données des machines depuis la base de données."""
        self.set_status(get_machine_text("loading_machines"))
        
        try:
            start_date, end_date = self.get_date_range()
            
            # Récupérer les données via le service KPI
            if not self.kpi_service:
                raise Exception("Service KPI non initialisé")
                
            # Récupérer les données KPI machines
            raw_kpi_data = self.kpi_service.get_couts_par_machine(
                periode_debut=start_date,
                periode_fin=end_date,
                machine_ids=None,
                type_machine=None,
                limite=100  # Limiter pour les performances
            )
            
            # Convertir au format UI
            self.machines_data = self._convert_kpi_to_ui_format(raw_kpi_data)
            self.filtered_data = self.machines_data.copy()

            # RÉINITIALISER TOUS LES FILTRES AVANT DE METTRE À JOUR
            self._reset_all_filters()
            
            # Mettre à jour les vues
            self.update_initial_filters()
            self.apply_filters_and_update_views()

            self.set_status(f"Données chargées: {len(self.machines_data)} machines", success=True)

        except Exception as e:
            logger.error(f"Erreur lors du chargement des données machines: {e}")
            self._handle_data_load_error(e)
    
    def _convert_kpi_to_ui_format(self, kpi_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convertit les données KPI du service au format attendu par l'interface.
        
        Args:
            kpi_data: Données KPI brutes du service
            
        Returns:
            Liste des données formatées pour l'UI
        """
        converted_data = []
        
        for item in kpi_data:
            # Conversion avec gestion des erreurs pour chaque champ
            machine_data = {
                "machine_id": self._safe_int(item.get('machine_id')), # AJOUT IMPORTANT
                "machine_name": str(item.get('machine_nom', 'N/A')),
                "serial": str(item.get('machine_serial', 'N/A')),
                "type": str(item.get('type_nom', 'N/A')),
                "site": str(item.get('site_nom', 'N/A')),  # Ajout du site
                "criticite": str(item.get('machine_criticite', 'Standard')),
                "total_cost": self._safe_float(item.get('cout_total', 0)),
                "interventions": self._safe_int(item.get('nb_interventions_total', 0)),
                "preventif": self._safe_int(item.get('nb_preventif', 0)),
                "correctif": self._safe_int(item.get('nb_correctif', 0)),
                "urgence": self._safe_int(item.get('nb_urgence', 0)),
                "avg_cost": self._safe_float(item.get('cout_moyen_intervention', 0)),
                "cout_main_oeuvre": self._safe_float(item.get('cout_main_oeuvre', 0)),
                "cout_pieces": self._safe_float(item.get('cout_pieces_internes', 0)),
                "cout_frais_externes": self._safe_float(item.get('cout_frais_externes', 0)),
                "ratio_preventif_curatif": self._safe_float(item.get('ratio_preventif_curatif', 0)),
                "pourcentage_mod": self._safe_float(item.get('pourcentage_mod', 0)),
                "pourcentage_pieces": self._safe_float(item.get('pourcentage_pieces', 0)),
                "pourcentage_frais_externes": self._safe_float(item.get('pourcentage_frais_externes', 0)),
                "total_intervention_time": self._safe_float(item.get('duree_intervention_totale', 0)),
                "avg_intervention_time": self._safe_float(item.get('duree_intervention_moyenne', 0)),
                "last_maintenance": "N/A",  # TODO: Récupérer depuis les données
                "next_maintenance": "N/A",  # TODO: Calculer la prochaine maintenance
                "status": self._determine_machine_status(item)
            }
            converted_data.append(machine_data)
        
        return converted_data
    
    def _safe_float(self, value):
        """Conversion sécurisée en float."""
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value):
        """Conversion sécurisée en int."""
        try:
            return int(value) if value is not None else 0
        except (ValueError, TypeError):
            return 0
    
    def _determine_machine_status(self, item):
        """Détermine le statut d'une machine basé sur ses données KPI."""
        nb_interventions = self._safe_int(item.get('nb_interventions_total', 0))
        nb_urgence = self._safe_int(item.get('nb_urgence', 0))
        
        if nb_urgence > 0:
            return "Attention"
        elif nb_interventions > 0:
            return "Actif"
        else:
            return "Inactif"
    
    def _handle_data_load_error(self, error):
        """Gère les erreurs de chargement des données."""
        self.set_status(f"Erreur de connexion à la base de données : {error}", success=False)
        self.machines_data = []
        self.filtered_data = []
        self.update_initial_filters()
        self.apply_filters_and_update_views()
        
        # Afficher message d'erreur à l'utilisateur
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self, 
            "Erreur", 
            f"Impossible de charger les données depuis la base de données.\n\nDétail : {error}"
        )
    
    def _reset_all_filters(self):
        """Réinitialise tous les filtres à leurs valeurs par défaut."""
        # Bloquer les signaux pour éviter les mises à jour multiples
        self.type_combo.blockSignals(True)
        self.machine_combo.blockSignals(True)
        
        # Réinitialiser les combos principaux
        self.type_combo.setCurrentText(get_machine_text("all_types"))
        self.machine_combo.setCurrentText(get_machine_text("all_machines"))
        
        # Réinitialiser les filtres avancés s'ils existent
        if hasattr(self, 'status_combo'):
            self.status_combo.blockSignals(True)
            self.status_combo.setCurrentText(get_machine_text("all_statuses"))
            self.status_combo.blockSignals(False)
        
        if hasattr(self, 'critical_only_checkbox'):
            self.critical_only_checkbox.blockSignals(True)
            self.critical_only_checkbox.setChecked(False)
            self.critical_only_checkbox.blockSignals(False)
        
        if hasattr(self, 'limit_slider'):
            self.limit_slider.blockSignals(True)
            self.limit_slider.setValue(50)  # Valeur par défaut
            self.limit_label.setText("50")
            self.limit_slider.blockSignals(False)
        
        # Réactiver les signaux
        self.type_combo.blockSignals(False)
        self.machine_combo.blockSignals(False)
        
        logger.debug("Tous les filtres ont été réinitialisés")

    def update_initial_filters(self):
        """
        Met à jour les filtres une seule fois après le chargement des données.
        """
        self.type_combo.blockSignals(True)
        self.machine_combo.blockSignals(True)

        # Remplir les types
        self.type_combo.clear()
        self.type_combo.addItem(get_machine_text("all_types"))
        types = sorted(set(m["type"] for m in self.machines_data))
        self.type_combo.addItems(types)

        # Remplir les machines
        self.machine_combo.clear()
        self.machine_combo.addItem(get_machine_text("all_machines"))
        machines = sorted(set(m["machine_name"] for m in self.machines_data))
        self.machine_combo.addItems(machines)

        self.type_combo.blockSignals(False)
        self.machine_combo.blockSignals(False)

    def apply_filters_and_update_views(self):
        """
        Méthode centrale simplifiée qui applique tous les filtres et met à jour l'UI.
        """
        # Partir des données complètes
        filtered_data = self.machines_data.copy()
        
        # === FILTRE 1: Type de machine ===
        selected_type = self.type_combo.currentText()
        if selected_type != get_machine_text("all_types"):
            filtered_data = [m for m in filtered_data if m["type"] == selected_type]

        # === FILTRE 2: Machine spécifique ===
        selected_machine = self.machine_combo.currentText()
        if selected_machine != get_machine_text("all_machines"):
            filtered_data = [m for m in filtered_data if m["machine_name"] == selected_machine]
        
        # === FILTRE 3: Statut ===
        selected_status = getattr(self, 'status_combo', None)
        if selected_status and selected_status.currentText() != get_machine_text("all_statuses"):
            status_text = selected_status.currentText()
            # Mapper les statuts traduits vers les statuts internes
            status_mapping = {
                get_machine_text("active_status"): "Actif",
                get_machine_text("attention_status"): "Attention", 
                get_machine_text("inactive_status"): "Inactif"
            }
            internal_status = status_mapping.get(status_text, status_text)
            filtered_data = [m for m in filtered_data if m["status"] == internal_status]
        
        # === FILTRE 4: Machines critiques uniquement ===
        critical_only = getattr(self, 'critical_only_checkbox', None)
        if critical_only and critical_only.isChecked():
            filtered_data = [m for m in filtered_data if m["status"] == "Attention"]
        
        # === FILTRE 5: Limite de résultats ===
        limit = getattr(self, 'limit_slider', None)
        if limit:
            max_results = limit.value()
            # Trier avant de limiter
            if hasattr(self, 'current_sort_column'):
                filtered_data = self._sort_data(filtered_data)
            filtered_data = filtered_data[:max_results]
        
        # === MISE À JOUR DES FILTRES DÉPENDANTS ===
        self._update_dependent_filters(filtered_data)
        
        # === MISE À JOUR DE L'INTERFACE ===
        self.filtered_data = filtered_data
        self.update_data_view()
        self.update_charts_view()
    
    def _sort_data(self, data):
        """Trie les données selon la colonne et l'ordre sélectionnés."""
        if not data:
            return data
            
        sort_key_mapping = {
            0: lambda x: x["machine_name"].lower(),
            1: lambda x: x["type"].lower(),
            3: lambda x: x["total_cost"],
            4: lambda x: x["interventions"],
            9: lambda x: x["avg_cost"],
            10: lambda x: x["avg_intervention_time"]
        }
        
        sort_key = sort_key_mapping.get(self.current_sort_column, lambda x: x["total_cost"])
        reverse = self.current_sort_order == Qt.DescendingOrder
        
        try:
            return sorted(data, key=sort_key, reverse=reverse)
        except Exception as e:
            logger.warning(f"Erreur de tri: {e}")
            return data
    
    def _update_dependent_filters(self, filtered_data):
        """Met à jour les filtres dépendants sans déclencher d'événements."""
        # Mise à jour du filtre machine
        self.machine_combo.blockSignals(True)
        current_machine = self.machine_combo.currentText()
        self.machine_combo.clear()
        self.machine_combo.addItem(get_machine_text("all_machines"))
        
        available_machines = sorted(set(m["machine_name"] for m in filtered_data))
        self.machine_combo.addItems(available_machines)
        
        if current_machine in available_machines:
            self.machine_combo.setCurrentText(current_machine)
        
        self.machine_combo.blockSignals(False)

    def update_data_view(self):
        """Met à jour la vue de données avec le nouveau tableau amélioré."""
        filtered_data = self.filtered_data

        # === MISE À JOUR DU TABLEAU PRINCIPAL ===
        self.data_table.setRowCount(len(filtered_data))
        
        for row, machine in enumerate(filtered_data):
            # Colonnes de base
            self.data_table.setItem(row, 0, QTableWidgetItem(machine["machine_name"]))
            self.data_table.setItem(row, 1, QTableWidgetItem(machine["type"]))
            
            # Statut avec couleur
            status_item = QTableWidgetItem(machine["status"])
            if machine["status"] == "Actif":
                status_item.setBackground(QColor("#d4edda"))
            elif machine["status"] == "Attention":
                status_item.setBackground(QColor("#f8d7da"))
            else:  # Inactif
                status_item.setBackground(QColor("#e2e3e5"))
            self.data_table.setItem(row, 2, status_item)
            
            # Données numériques
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{machine['total_cost']:.2f}"))
            self.data_table.setItem(row, 4, QTableWidgetItem(str(machine["interventions"])))
            self.data_table.setItem(row, 5, QTableWidgetItem(str(machine.get("preventif", 0))))
            self.data_table.setItem(row, 6, QTableWidgetItem(str(machine.get("correctif", 0))))
            self.data_table.setItem(row, 7, QTableWidgetItem(str(machine.get("urgence", 0))))
            self.data_table.setItem(row, 8, QTableWidgetItem(f"{machine['total_intervention_time']:.1f}"))
            self.data_table.setItem(row, 9, QTableWidgetItem(f"{machine['avg_cost']:.2f}"))
            self.data_table.setItem(row, 10, QTableWidgetItem(f"{machine['avg_intervention_time']:.1f}"))
            self.data_table.setItem(row, 11, QTableWidgetItem(machine["last_maintenance"]))
            self.data_table.setItem(row, 12, QTableWidgetItem(machine.get("criticite", "Standard")))
            
            # Ratio préventif/correctif
            ratio = machine.get("ratio_preventif_curatif", 0)
            self.data_table.setItem(row, 13, QTableWidgetItem(f"{ratio:.2f}"))

        # === MISE À JOUR DES STATISTIQUES ===
        if hasattr(self, 'selection_stats_labels'):
            self._update_selection_stats(filtered_data)
    
    def _update_selection_stats(self, filtered_data):
        """Met à jour les statistiques de sélection."""
        if not filtered_data:
            stats = {
                "total_machines": "0",
                "total_cost": "0€",
                "avg_cost": "0€",
                "total_interventions": "0",
                "preventive_ratio": "0%",
                "efficiency": "0%"
            }
        else:
            total_cost = sum(m["total_cost"] for m in filtered_data)
            total_interventions = sum(m["interventions"] for m in filtered_data)
            preventive_interventions = sum(m.get("preventif", 0) for m in filtered_data)
            
            stats = {
                "total_machines": str(len(filtered_data)),
                "total_cost": f"{total_cost:,.0f}€",  # Arrondi sans virgule
                "avg_cost": f"{total_cost/len(filtered_data):,.0f}€",  # Arrondi sans virgule
                "total_interventions": str(total_interventions),
                "preventive_ratio": f"{(preventive_interventions/total_interventions*100) if total_interventions > 0 else 0:.0f}%",  # Arrondi sans virgule
                "efficiency": f"{(preventive_interventions/total_interventions*100) if total_interventions > 0 else 0:.0f}%"  # Arrondi sans virgule
            }
        
        # Mise à jour des labels
        for key, value in stats.items():
            if key in self.selection_stats_labels:
                current_text = self.selection_stats_labels[key].text()
                new_text = current_text.split(':')[0] + f': {value}'
                self.selection_stats_labels[key].setText(new_text)

    def update_charts_view(self):
        """Met à jour la vue des graphiques."""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            # Mettre à jour les données du widget graphique
            self.update_chart_data()
    
    def update_chart_data(self):
        """Met à jour les données du widget graphique."""
        if not hasattr(self, 'chart_widget'):
            return
        
        try:
            # Extraire les données pour les filtres
            sites = sorted(set(m.get('site', 'N/A') for m in self.machines_data if m.get('site')))
            machines = sorted(set(m['machine_name'] for m in self.machines_data))
            types = sorted(set(m['type'] for m in self.machines_data))
            
            # Configurer les données du widget
            self.chart_widget.set_data(sites, machines, types)
            
            # Calculer et envoyer les données du graphique
            self.calculate_and_send_chart_data();
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données graphiques: {e}")
    
    def calculate_and_send_chart_data(self):
        """Calcule et envoie les données du graphique au widget."""
        if not hasattr(self, 'chart_widget'):
            return
        
        try:
            # Récupérer les filtres actuels du widget graphique
            filters = self.chart_widget.get_current_filters()
            
            # Filtrer les données selon les critères du graphique
            filtered_data = self.machines_data.copy()
            
            if filters.get('site'):
                filtered_data = [m for m in filtered_data if m.get('site') == filters['site']]
            
            if filters.get('machine'):
                filtered_data = [m for m in filtered_data if m['machine_name'] == filters['machine']]
            
            if filters.get('type'):
                filtered_data = [m for m in filtered_data if m['type'] == filters['type']]
            
            # Générer les données temporelles selon le type de période
            chart_data = self.generate_time_series_data(filtered_data, filters)
            
            # Envoyer au widget graphique
            self.chart_widget.update_chart(chart_data)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des données graphiques: {e}")
    
    def generate_time_series_data(self, filtered_data, filters):
        """Génère les données temporelles réelles pour le graphique."""
        if not filtered_data:
            return {}
        
        try:
            from datetime import datetime, timedelta
            
            start_date = filters['start_date']
            end_date = filters['end_date']
            period_type = filters['period_type']
            
            # Extraire les IDs des machines filtrées
            machine_ids = [m.get('machine_id') for m in filtered_data if m.get('machine_id')]
            if not machine_ids:
                logger.warning("Aucun ID de machine trouvé pour le graphique.")
                return self._generate_empty_time_series_data(filters)

            # Vérifier la disponibilité du service KPI
            if not self.kpi_service:
                logger.warning("KPI Service non disponible, impossible de générer le graphique.")
                return self._generate_empty_time_series_data(filters)
            
            # Récupérer les vraies données d'interventions par période (incluent déjà les durées)
            interventions_raw_data = self.kpi_service.get_interventions_by_period(
                machine_ids=machine_ids,
                start_date=start_date,
                end_date=end_date,
                period_type=period_type
            )
            
            # Récupérer les vraies données de coûts par période
            costs_raw_data = self.kpi_service.get_costs_by_period(
                machine_ids=machine_ids,
                start_date=start_date,
                end_date=end_date,
                period_type=period_type
            )
            
            # Organiser les données par clé de période pour un accès rapide
            interventions_map = {item['period_key']: item.get('intervention_count', 0) for item in interventions_raw_data}
            durations_map = {item['period_key']: item.get('total_duration_hours', 0.0) for item in interventions_raw_data}
            costs_map = {item['period_key']: item.get('total_cost', 0.0) for item in costs_raw_data}

            # Générer les périodes et assembler les données
            periods, costs, interventions, durations = [], [], [], []
            
            current_date = start_date
            if period_type == 'monthly':
                current_date = start_date.replace(day=1)

            while current_date <= end_date:
                if period_type == 'daily':
                    period_key = current_date.strftime('%Y-%m-%d')
                    periods.append(period_key)
                    current_date += timedelta(days=1)
                elif period_type == 'weekly':
                    week_start = current_date - timedelta(days=current_date.weekday())
                    period_key = f"{week_start.strftime('%Y-W%W')}"
                    periods.append(f"S{week_start.strftime('%W')} {week_start.strftime('%Y')}")
                    current_date += timedelta(weeks=1)
                elif period_type == 'monthly':
                    period_key = current_date.strftime('%Y-%m')
                    periods.append(period_key)
                    # Aller au mois suivant
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)
                
                interventions.append(interventions_map.get(period_key, 0))
                costs.append(max(0.0, costs_map.get(period_key, 0.0)))
                durations.append(max(0.0, durations_map.get(period_key, 0.0)))

            logger.info(f"Données temporelles générées: {len(periods)} périodes.")
            
            return {
                'periods': periods,
                'costs': costs,
                'interventions': interventions,
                'durations': durations,
                'period_type': period_type
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Erreur lors de la génération des données temporelles: {e}")
            traceback.print_exc()
            return self._generate_empty_time_series_data(filters)

    def _generate_empty_time_series_data(self, filters):
        """Génère des données temporelles vides (pas de simulation)."""
        try:
            from datetime import datetime, timedelta
            
            start_date = filters['start_date']
            end_date = filters['end_date']
            period_type = filters['period_type']
            
            periods = []
            costs = []
            interventions = []
            durations = []
            
            if period_type == 'daily':
                current_date = start_date
                while current_date <= end_date:
                    periods.append(current_date.strftime('%Y-%m-%d'))
                    costs.append(0.0)
                    interventions.append(0)
                    durations.append(0.0)
                    current_date += timedelta(days=1)
            
            elif period_type == 'weekly':
                current_date = start_date
                while current_date <= end_date:
                    week_start = current_date - timedelta(days=current_date.weekday())
                    periods.append(f"S{week_start.strftime('%W')} {week_start.strftime('%Y')}")
                    costs.append(0.0)
                    interventions.append(0)
                    durations.append(0.0)
                    current_date += timedelta(weeks=1)
            
            elif period_type == 'monthly':
                current_date = start_date.replace(day=1)
                while current_date <= end_date:
                    periods.append(current_date.strftime('%Y-%m'))
                    costs.append(0.0)
                    interventions.append(0)
                    durations.append(0.0)
                    # Aller au mois suivant
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)
            
            return {
                'periods': periods,
                'costs': costs,
                'interventions': interventions,
                'durations': durations,
                'period_type': period_type
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des données vides: {e}")
            return {}

    def on_chart_filters_changed(self):
        """Gère le changement des filtres dans le widget graphique."""
        # Recalculer et envoyer les nouvelles données
        self.calculate_and_send_chart_data()
    
    def on_chart_updated(self):
        """Gère la mise à jour du graphique."""
        # Mettre à jour le statut
        try:
            from .machine_kpi_chart_translations import get_chart_text
            self.set_status(get_chart_text("chart_updated"), success=True)
        except:
            self.set_status("Graphique mis à jour", success=True)
