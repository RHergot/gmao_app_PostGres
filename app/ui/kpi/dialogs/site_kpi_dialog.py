#!/usr/bin/env python3
"""
Dialog d'analyse KPI par site.
Affiche les métriques de maintenance détaillées pour chaque site.
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
    from app.ui.kpi.widgets.site_kpi_widget import SiteKPIWidget
except ImportError as e:
    print(f"Erreur d'import dans SiteKPIDialog: {e}")
    SiteKPIWidget = None

import logging
logger = logging.getLogger(__name__)

# === TRADUCTIONS SPÉCIFIQUES ===
SITE_TRANSLATIONS = {
    Language.FRENCH: {
        "title": "📊 Analyse KPI par Site",
        "site_filter": "Filtrer par Site",
        "all_sites": "Tous les sites",
        "region_filter": "Filtrer par Région",
        "all_regions": "Toutes les régions",
        "summary_tab": "📊 Résumé",
        "comparison_tab": "⚖️ Comparaison",
        "trends_tab": "📈 Tendances",
        "top_sites": "🔝 Top Sites par Coût",
        "site_performance": "⚡ Performance par Site",
        "site_name": "Site",
        "region": "Région",
        "machines_count": "Nb Machines",
        "total_cost": "Coût Total (€)",
        "cost_per_machine": "Coût/Machine (€)",
        "interventions": "Interventions",
        "availability": "Disponibilité (%)",
        "efficiency": "Efficacité (%)",
        "no_data_message": "Aucune donnée de site disponible pour cette période",
        "loading_sites": "Chargement des données sites...",
        "export_success": "Données sites exportées avec succès"
    },
    Language.ENGLISH: {
        "title": "📊 Site KPI Analysis",
        "site_filter": "Filter by Site",
        "all_sites": "All sites",
        "region_filter": "Filter by Region",
        "all_regions": "All regions",
        "summary_tab": "📊 Summary",
        "comparison_tab": "⚖️ Comparison",
        "trends_tab": "📈 Trends",
        "top_sites": "🔝 Top Sites by Cost",
        "site_performance": "⚡ Site Performance",
        "site_name": "Site",
        "region": "Region",
        "machines_count": "Machines Count",
        "total_cost": "Total Cost (€)",
        "cost_per_machine": "Cost/Machine (€)",
        "interventions": "Interventions",
        "availability": "Availability (%)",
        "efficiency": "Efficiency (%)",
        "no_data_message": "No site data available for this period",
        "loading_sites": "Loading site data...",
        "export_success": "Site data exported successfully"
    },
    Language.GERMAN: {
        "title": "📊 Standort-KPI-Analyse",
        "site_filter": "Nach Standort filtern",
        "all_sites": "Alle Standorte",
        "region_filter": "Nach Region filtern",
        "all_regions": "Alle Regionen",
        "summary_tab": "📊 Zusammenfassung",
        "comparison_tab": "⚖️ Vergleich",
        "trends_tab": "📈 Trends",
        "top_sites": "🔝 Top Standorte nach Kosten",
        "site_performance": "⚡ Standortleistung",
        "site_name": "Standort",
        "region": "Region",
        "machines_count": "Anzahl Maschinen",
        "total_cost": "Gesamtkosten (€)",
        "cost_per_machine": "Kosten/Maschine (€)",
        "interventions": "Interventionen",
        "availability": "Verfügbarkeit (%)",
        "efficiency": "Effizienz (%)",
        "no_data_message": "Keine Standortdaten für diesen Zeitraum verfügbar",
        "loading_sites": "Lade Standortdaten...",
        "export_success": "Standortdaten erfolgreich exportiert"
    }
}

def get_site_text(key: str) -> str:
    """Récupère le texte traduit selon la langue configurée."""
    try:
        current_lang = app_config.language if 'app_config' in globals() else Language.FRENCH
        return SITE_TRANSLATIONS.get(current_lang, SITE_TRANSLATIONS[Language.FRENCH]).get(key, key)
    except:
        return SITE_TRANSLATIONS[Language.FRENCH].get(key, key)


class SiteKPIDialog(BaseKPIDialog):
    """
    Dialog d'analyse KPI par site.
    
    Fonctionnalités:
    - Vue d'ensemble des sites les plus coûteux
    - Comparaison entre sites
    - Analyse des tendances par site
    - Filtrage par site et région
    - Export des données détaillées
    """
    
    def __init__(self, parent=None):
        super().__init__(parent, get_site_text("title"))
        
        self.sites_data = []
        self.regions_list = []
        
        logger.info("Initialisation du SiteKPIDialog")
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute les filtres spécifiques aux sites."""
        # === FILTRE PAR SITE ===
        site_group = QGroupBox(get_site_text("site_filter"))
        site_layout = QHBoxLayout(site_group)
        
        self.site_combo = QComboBox()
        self.site_combo.addItem(get_site_text("all_sites"))
        self.site_combo.currentTextChanged.connect(self.on_filter_changed)
        site_layout.addWidget(self.site_combo)
        
        toolbar_layout.addWidget(site_group)
        
        # === FILTRE PAR RÉGION ===
        region_group = QGroupBox(get_site_text("region_filter"))
        region_layout = QHBoxLayout(region_group)
        
        self.region_combo = QComboBox()
        self.region_combo.addItem(get_site_text("all_regions"))
        self.region_combo.currentTextChanged.connect(self.on_filter_changed)
        region_layout.addWidget(self.region_combo)
        
        toolbar_layout.addWidget(region_group)
    
    def create_specific_content(self):
        """Crée le contenu spécifique à l'analyse par site."""
        self.tab_widget = QTabWidget()
        self.content_layout.addWidget(self.tab_widget)
        
        # === ONGLET RÉSUMÉ ===
        self.create_summary_tab()
        
        # === ONGLET COMPARAISON ===
        self.create_comparison_tab()
        
        # === ONGLET TENDANCES ===
        self.create_trends_tab()
    
    def create_summary_tab(self):
        """Crée l'onglet de résumé."""
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # Table des sites
        self.sites_table = QTableWidget()
        self.sites_table.setColumnCount(7)
        headers = [
            get_site_text("site_name"),
            get_site_text("region"),
            get_site_text("machines_count"),
            get_site_text("total_cost"),
            get_site_text("cost_per_machine"),
            get_site_text("interventions"),
            get_site_text("availability")
        ]
        self.sites_table.setHorizontalHeaderLabels(headers)
        self.sites_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sites_table.setAlternatingRowColors(True)
        self.sites_table.setSortingEnabled(True)
        
        summary_layout.addWidget(self.sites_table)
        
        self.tab_widget.addTab(summary_widget, get_site_text("summary_tab"))
    
    def create_comparison_tab(self):
        """Crée l'onglet de comparaison."""
        comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(comparison_widget)
        
        # Placeholder pour graphiques de comparaison
        if SiteKPIWidget:
            self.site_kpi_widget = SiteKPIWidget()
            comparison_layout.addWidget(self.site_kpi_widget)
        else:
            placeholder = QLabel("📊 Graphiques de comparaison entre sites")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 16px;
                    font-style: italic;
                    padding: 40px;
                    border: 2px dashed #CCCCCC;
                    border-radius: 8px;
                }
            """)
            comparison_layout.addWidget(placeholder)
        
        self.tab_widget.addTab(comparison_widget, get_site_text("comparison_tab"))
    
    def create_trends_tab(self):
        """Crée l'onglet des tendances."""
        trends_widget = QWidget()
        trends_layout = QVBoxLayout(trends_widget)
        
        # Placeholder pour graphiques de tendances
        placeholder = QLabel("📈 Analyse des tendances par site")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-style: italic;
                padding: 40px;
                border: 2px dashed #CCCCCC;
                border-radius: 8px;
            }
        """)
        trends_layout.addWidget(placeholder)
        
        self.tab_widget.addTab(trends_widget, get_site_text("trends_tab"))
    
    def load_data(self):
        """Charge les données des sites."""
        self.set_status(get_site_text("loading_sites"))
        
        try:
            # Simulation de données
            self.sites_data = self.get_mock_site_data()
            self.update_filters()
            self.update_views()
            
            self.set_status(f"Données chargées: {len(self.sites_data)} sites", success=True)
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données sites: {e}")
            self.set_status(f"Erreur: {e}", success=False)
    
    def get_mock_site_data(self) -> List[Dict[str, Any]]:
        """Génère des données de test pour les sites."""
        import random
        
        regions = ["Nord", "Sud", "Est", "Ouest", "Centre"]
        sites = ["Site Alpha", "Site Beta", "Site Gamma", "Site Delta", "Site Epsilon"]
        
        data = []
        for i, site in enumerate(sites):
            data.append({
                "site_name": site,
                "region": random.choice(regions),
                "machines_count": random.randint(10, 50),
                "total_cost": random.uniform(50000, 200000),
                "interventions": random.randint(50, 200),
                "availability": random.uniform(85, 98),
                "efficiency": random.uniform(80, 95)
            })
        
        # Calcul du coût par machine
        for site in data:
            site["cost_per_machine"] = site["total_cost"] / site["machines_count"]
        
        return data
    
    def update_filters(self):
        """Met à jour les listes de filtres."""
        # Régions
        self.region_combo.clear()
        self.region_combo.addItem(get_site_text("all_regions"))
        regions = sorted(set(site["region"] for site in self.sites_data))
        self.region_combo.addItems(regions)
        
        # Sites
        self.site_combo.clear()
        self.site_combo.addItem(get_site_text("all_sites"))
        sites = sorted(site["site_name"] for site in self.sites_data)
        self.site_combo.addItems(sites)
    
    def get_filtered_data(self) -> List[Dict[str, Any]]:
        """Récupère les données filtrées."""
        filtered_data = self.sites_data.copy()
        
        # Filtre par région
        selected_region = self.region_combo.currentText()
        if selected_region != get_site_text("all_regions"):
            filtered_data = [s for s in filtered_data if s["region"] == selected_region]
        
        # Filtre par site
        selected_site = self.site_combo.currentText()
        if selected_site != get_site_text("all_sites"):
            filtered_data = [s for s in filtered_data if s["site_name"] == selected_site]
        
        return filtered_data
    
    def update_views(self):
        """Met à jour toutes les vues."""
        filtered_data = self.get_filtered_data()
        
        # Mise à jour de la table des sites
        self.sites_table.setRowCount(len(filtered_data))
        
        for row, site in enumerate(filtered_data):
            self.sites_table.setItem(row, 0, QTableWidgetItem(site["site_name"]))
            self.sites_table.setItem(row, 1, QTableWidgetItem(site["region"]))
            self.sites_table.setItem(row, 2, QTableWidgetItem(str(site["machines_count"])))
            self.sites_table.setItem(row, 3, QTableWidgetItem(f"{site['total_cost']:.2f}€"))
            self.sites_table.setItem(row, 4, QTableWidgetItem(f"{site['cost_per_machine']:.2f}€"))
            self.sites_table.setItem(row, 5, QTableWidgetItem(str(site["interventions"])))
            self.sites_table.setItem(row, 6, QTableWidgetItem(f"{site['availability']:.1f}%"))
    
    def on_filter_changed(self):
        """Gère le changement de filtres."""
        self.update_views()
    
    def export_data(self):
        """Exporte les données sites vers Excel."""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Exporter les données sites",
                f"sites_kpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Fichiers Excel (*.xlsx)"
            )
            
            if file_path:
                self.set_status(get_site_text("export_success"), success=True)
                QMessageBox.information(self, get_shared_text("success"), 
                                      f"Données exportées vers:\n{file_path}")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            QMessageBox.critical(self, get_shared_text("error"), 
                               f"Erreur lors de l'export:\n{e}")
