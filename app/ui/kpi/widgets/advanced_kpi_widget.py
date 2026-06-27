#!/usr/bin/env python3
"""
Widget avancé pour les fonctionnalités d'analyse et d'export des KPI.
Intègre les graphiques interactifs, filtres avancés et exports.
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import json

# Imports PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDateEdit, QPushButton, QFrame,
    QScrollArea, QGroupBox, QSplitter, QTabWidget,
    QMessageBox, QProgressBar, QCheckBox, QSlider,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QTextEdit, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QIcon

import logging
logger = logging.getLogger(__name__)

try:
    from app.core.services.kpi_service import KPIService
    from app.utils.logging_config import setup_logging
except ImportError as e:
    logger.debug("Erreur d'import KPIService: %s", e)
    KPIService = None
    setup_logging = None


class AdvancedKPIWidget(QWidget):
    """
    Widget avancé pour l'analyse KPI avec fonctionnalités interactives.
    
    Fonctionnalités:
    - Filtres avancés multi-critères  
    - Graphiques interactifs avec zoom
    - Export Excel/CSV/PDF avec mise en forme
    - Comparaisons temporelles
    - Alertes et seuils personnalisables
    - Tableaux de bord personnalisés
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kpi_service = None
        self.current_data = {}
        self.filters = {}
        self.alerts = {}
        
        if KPIService:
            self.kpi_service = KPIService()
            
        if setup_logging:
            setup_logging()
        logger.info("Initialisation du widget KPI avancé")
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configure l'interface utilisateur avancée."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === TITRE ET DESCRIPTION ===
        self.create_header(main_layout)
        
        # === CONTRÔLES AVANCÉS ===
        controls_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(controls_splitter)
        
        # Panneau de filtres avancés
        self.create_advanced_filters(controls_splitter)
        
        # Zone de visualisation principale
        self.create_visualization_area(controls_splitter)
        
        # === PANNEAU D'EXPORT ET ACTIONS ===
        self.create_export_panel(main_layout)
        
        # Proportions des panneaux
        controls_splitter.setSizes([300, 700])
    
    def create_header(self, parent_layout):
        """Crée l'en-tête du widget."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("QFrame { background-color: #E3F2FD; border-radius: 8px; }")
        
        header_layout = QVBoxLayout(header_frame)
        
        # Titre principal
        title_label = QLabel("🔬 Analyse KPI Avancée")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Filtres avancés • Graphiques interactifs • Export intelligent • Alertes personnalisées")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("QLabel { color: #666666; margin: 5px; }")
        header_layout.addWidget(desc_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_advanced_filters(self, parent_splitter):
        """Crée le panneau de filtres avancés."""
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.StyledPanel)
        filters_frame.setStyleSheet("QFrame { background-color: #F5F5F5; }")
        
        filters_layout = QVBoxLayout(filters_frame)
        
        # === TITRE FILTRES ===
        filters_title = QLabel("🎛️ Filtres Avancés")
        filters_title.setFont(QFont("Arial", 12, QFont.Bold))
        filters_layout.addWidget(filters_title)
        
        # === FILTRES TEMPORELS ===
        self.create_temporal_filters(filters_layout)
        
        # === FILTRES PAR ENTITÉ ===
        self.create_entity_filters(filters_layout)
        
        # === FILTRES PAR MONTANT ===
        self.create_amount_filters(filters_layout)
        
        # === ALERTES ET SEUILS ===
        self.create_alerts_section(filters_layout)
        
        # === BOUTONS D'ACTION FILTRES ===
        self.create_filter_actions(filters_layout)
        
        # Spacer
        filters_layout.addStretch()
        
        parent_splitter.addWidget(filters_frame)
    
    def create_temporal_filters(self, parent_layout):
        """Crée les filtres temporels avancés."""
        temporal_group = QGroupBox("📅 Période & Comparaison")
        temporal_layout = QVBoxLayout(temporal_group)
        
        # Sélection de période
        period_layout = QGridLayout()
        
        period_layout.addWidget(QLabel("Du:"), 0, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-3))
        self.date_debut.setCalendarPopup(True)
        period_layout.addWidget(self.date_debut, 0, 1)
        
        period_layout.addWidget(QLabel("Au:"), 1, 0)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        period_layout.addWidget(self.date_fin, 1, 1)
        
        temporal_layout.addLayout(period_layout)
        
        # Options de comparaison
        self.chk_compare_previous = QCheckBox("Comparer avec période précédente")
        temporal_layout.addWidget(self.chk_compare_previous)
        
        self.chk_show_trend = QCheckBox("Afficher les tendances")
        temporal_layout.addWidget(self.chk_show_trend)
        
        # Groupement temporel
        grouping_layout = QHBoxLayout()
        grouping_layout.addWidget(QLabel("Grouper par:"))
        self.combo_grouping = QComboBox()
        self.combo_grouping.addItems(["Jour", "Semaine", "Mois", "Trimestre", "Année"])
        self.combo_grouping.setCurrentText("Mois")
        grouping_layout.addWidget(self.combo_grouping)
        temporal_layout.addLayout(grouping_layout)
        
        parent_layout.addWidget(temporal_group)
    
    def create_entity_filters(self, parent_layout):
        """Crée les filtres par entité."""
        entity_group = QGroupBox("🏗️ Filtres par Entité")
        entity_layout = QVBoxLayout(entity_group)
        
        # Filtres machines
        machines_layout = QHBoxLayout()
        machines_layout.addWidget(QLabel("Machines:"))
        self.combo_machines = QComboBox()
        self.combo_machines.addItem("Toutes les machines")
        machines_layout.addWidget(self.combo_machines)
        entity_layout.addLayout(machines_layout)
        
        # Filtres sites
        sites_layout = QHBoxLayout()
        sites_layout.addWidget(QLabel("Sites:"))
        self.combo_sites = QComboBox()
        self.combo_sites.addItem("Tous les sites")
        sites_layout.addWidget(self.combo_sites)
        entity_layout.addLayout(sites_layout)
        
        # Filtres équipes
        equipes_layout = QHBoxLayout()
        equipes_layout.addWidget(QLabel("Équipes:"))
        self.combo_equipes = QComboBox()
        self.combo_equipes.addItem("Toutes les équipes")
        equipes_layout.addWidget(self.combo_equipes)
        entity_layout.addLayout(equipes_layout)
        
        # Type de maintenance
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.combo_type_maintenance = QComboBox()
        self.combo_type_maintenance.addItems(["Tous", "Préventif", "Curatif", "Urgence"])
        type_layout.addWidget(self.combo_type_maintenance)
        entity_layout.addLayout(type_layout)
        
        parent_layout.addWidget(entity_group)
    
    def create_amount_filters(self, parent_layout):
        """Crée les filtres par montant."""
        amount_group = QGroupBox("💰 Filtres par Montant")
        amount_layout = QVBoxLayout(amount_group)
        
        # Coût minimum
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Coût min:"))
        self.spin_cout_min = QSpinBox()
        self.spin_cout_min.setRange(0, 999999)
        self.spin_cout_min.setSuffix(" €")
        min_layout.addWidget(self.spin_cout_min)
        amount_layout.addLayout(min_layout)
        
        # Coût maximum
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Coût max:"))
        self.spin_cout_max = QSpinBox()
        self.spin_cout_max.setRange(0, 999999)
        self.spin_cout_max.setValue(50000)
        self.spin_cout_max.setSuffix(" €")
        max_layout.addWidget(self.spin_cout_max)
        amount_layout.addLayout(max_layout)
        
        # Slider pour ajustement rapide
        self.slider_cout = QSlider(Qt.Horizontal)
        self.slider_cout.setRange(0, 100000)
        self.slider_cout.setValue(25000)
        amount_layout.addWidget(QLabel("Ajustement rapide:"))
        amount_layout.addWidget(self.slider_cout)
        
        parent_layout.addWidget(amount_group)
    
    def create_alerts_section(self, parent_layout):
        """Crée la section d'alertes et seuils."""
        alerts_group = QGroupBox("🚨 Alertes & Seuils")
        alerts_layout = QVBoxLayout(alerts_group)
        
        # Activation des alertes
        self.chk_enable_alerts = QCheckBox("Activer les alertes")
        alerts_layout.addWidget(self.chk_enable_alerts)
        
        # Seuil d'alerte coût
        seuil_layout = QHBoxLayout()
        seuil_layout.addWidget(QLabel("Seuil coût:"))
        self.spin_seuil_cout = QSpinBox()
        self.spin_seuil_cout.setRange(100, 100000)
        self.spin_seuil_cout.setValue(5000)
        self.spin_seuil_cout.setSuffix(" €")
        seuil_layout.addWidget(self.spin_seuil_cout)
        alerts_layout.addLayout(seuil_layout)
        
        # Alertes par email
        self.chk_email_alerts = QCheckBox("Alertes par email")
        alerts_layout.addWidget(self.chk_email_alerts)
        
        parent_layout.addWidget(alerts_group)
    
    def create_filter_actions(self, parent_layout):
        """Crée les boutons d'actions pour les filtres."""
        actions_layout = QVBoxLayout()
        
        # Appliquer les filtres
        self.btn_apply_filters = QPushButton("🔍 Appliquer Filtres")
        self.btn_apply_filters.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        actions_layout.addWidget(self.btn_apply_filters)
        
        # Réinitialiser
        self.btn_reset_filters = QPushButton("🔄 Réinitialiser")
        self.btn_reset_filters.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        actions_layout.addWidget(self.btn_reset_filters)
        
        # Sauvegarder filtres
        self.btn_save_filters = QPushButton("💾 Sauvegarder")
        actions_layout.addWidget(self.btn_save_filters)
        
        parent_layout.addLayout(actions_layout)
    
    def create_visualization_area(self, parent_splitter):
        """Crée la zone de visualisation principale."""
        viz_frame = QFrame()
        viz_frame.setFrameStyle(QFrame.StyledPanel)
        
        viz_layout = QVBoxLayout(viz_frame)
        
        # === ONGLETS DE VISUALISATION ===
        self.viz_tabs = QTabWidget()
        
        # Onglet Graphiques
        self.create_charts_tab()
        
        # Onglet Tableau détaillé
        self.create_table_tab()
        
        # Onglet Comparaisons
        self.create_comparison_tab()
        
        # Onglet Tendances
        self.create_trends_tab()
        
        viz_layout.addWidget(self.viz_tabs)
        
        parent_splitter.addWidget(viz_frame)
    
    def create_charts_tab(self):
        """Crée l'onglet des graphiques."""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # Zone de graphiques (placeholder pour maintenant)
        self.charts_area = QScrollArea()
        self.charts_content = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_content)
        
        # Placeholder pour graphiques
        placeholder_label = QLabel("📊 Zone de Graphiques Interactifs\n\nIci s'afficheront:\n• Graphiques en barres/courbes\n• Graphiques secteurs\n• Histogrammes\n• Graphiques de tendances\n• Cartes de chaleur")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                background-color: #F0F0F0;
                border: 2px dashed #CCCCCC;
                border-radius: 10px;
                padding: 50px;
                font-size: 14px;
                color: #666666;
            }
        """)
        self.charts_layout.addWidget(placeholder_label)
        
        self.charts_area.setWidget(self.charts_content)
        charts_layout.addWidget(self.charts_area)
        
        self.viz_tabs.addTab(charts_widget, "📊 Graphiques")
    
    def create_table_tab(self):
        """Crée l'onglet du tableau détaillé."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Contrôles du tableau
        controls_layout = QHBoxLayout()
        
        # Recherche
        controls_layout.addWidget(QLabel("🔍 Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher dans les données...")
        controls_layout.addWidget(self.search_input)
        
        # Nombre de lignes
        controls_layout.addWidget(QLabel("Lignes:"))
        self.combo_rows = QComboBox()
        self.combo_rows.addItems(["10", "25", "50", "100", "Toutes"])
        self.combo_rows.setCurrentText("25")
        controls_layout.addWidget(self.combo_rows)
        
        table_layout.addLayout(controls_layout)
        
        # Tableau des données
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self.data_table)
        
        self.viz_tabs.addTab(table_widget, "📋 Tableau")
    
    def create_comparison_tab(self):
        """Crée l'onglet de comparaisons."""
        comp_widget = QWidget()
        comp_layout = QVBoxLayout(comp_widget)
        
        comp_label = QLabel("⚖️ Comparaisons Temporelles\n\nIci s'afficheront:\n• Comparaisons période vs période précédente\n• Évolutions en pourcentage\n• Graphiques de variance\n• Analyse des écarts")
        comp_label.setAlignment(Qt.AlignCenter)
        comp_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3E0;
                border: 2px dashed #FF9800;
                border-radius: 10px;
                padding: 50px;
                font-size: 14px;
                color: #E65100;
            }
        """)
        comp_layout.addWidget(comp_label)
        
        self.viz_tabs.addTab(comp_widget, "⚖️ Comparaisons")
    
    def create_trends_tab(self):
        """Crée l'onglet des tendances."""
        trends_widget = QWidget()
        trends_layout = QVBoxLayout(trends_widget)
        
        trends_label = QLabel("📈 Analyse de Tendances\n\nIci s'afficheront:\n• Courbes de tendances\n• Prédictions\n• Saisonnalité\n• Corrélations\n• Indicateurs de performance")
        trends_label.setAlignment(Qt.AlignCenter)
        trends_label.setStyleSheet("""
            QLabel {
                background-color: #E8F5E8;
                border: 2px dashed #4CAF50;
                border-radius: 10px;
                padding: 50px;
                font-size: 14px;
                color: #2E7D32;
            }
        """)
        trends_layout.addWidget(trends_label)
        
        self.viz_tabs.addTab(trends_widget, "📈 Tendances")
    
    def create_export_panel(self, parent_layout):
        """Crée le panneau d'export et d'actions."""
        export_frame = QFrame()
        export_frame.setFrameStyle(QFrame.StyledPanel)
        export_frame.setStyleSheet("QFrame { background-color: #E1F5FE; }")
        
        export_layout = QHBoxLayout(export_frame)
        
        # === EXPORTS ===
        export_group = QGroupBox("📤 Export & Sauvegarde")
        export_group_layout = QHBoxLayout(export_group)
        
        self.btn_export_excel = QPushButton("📊 Excel")
        self.btn_export_excel.setToolTip("Exporter vers Excel avec graphiques")
        export_group_layout.addWidget(self.btn_export_excel)
        
        self.btn_export_csv = QPushButton("📋 CSV")
        self.btn_export_csv.setToolTip("Exporter en CSV")
        export_group_layout.addWidget(self.btn_export_csv)
        
        self.btn_export_pdf = QPushButton("📄 PDF")
        self.btn_export_pdf.setToolTip("Générer rapport PDF")
        export_group_layout.addWidget(self.btn_export_pdf)
        
        self.btn_print = QPushButton("🖨️ Imprimer")
        export_group_layout.addWidget(self.btn_print)
        
        export_layout.addWidget(export_group)
        
        # === PARTAGE ===
        share_group = QGroupBox("🔗 Partage")
        share_group_layout = QHBoxLayout(share_group)
        
        self.btn_share_email = QPushButton("📧 Email")
        share_group_layout.addWidget(self.btn_share_email)
        
        self.btn_share_link = QPushButton("🔗 Lien")
        share_group_layout.addWidget(self.btn_share_link)
        
        self.btn_schedule = QPushButton("⏰ Programmer")
        share_group_layout.addWidget(self.btn_schedule)
        
        export_layout.addWidget(share_group)
        
        # === STATUS ===
        status_group = QGroupBox("ℹ️ Statut")
        status_group_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Prêt pour l'analyse")
        self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
        status_group_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_group_layout.addWidget(self.progress_bar)
        
        export_layout.addWidget(status_group)
        
        parent_layout.addWidget(export_frame)
    
    def setup_connections(self):
        """Configure les connexions des signaux."""
        # Filtres
        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.btn_reset_filters.clicked.connect(self.reset_filters)
        self.btn_save_filters.clicked.connect(self.save_filters)
        
        # Dates
        self.date_debut.dateChanged.connect(self.on_date_changed)
        self.date_fin.dateChanged.connect(self.on_date_changed)
        
        # Exports
        self.btn_export_excel.clicked.connect(self.export_to_excel)
        self.btn_export_csv.clicked.connect(self.export_to_csv)
        self.btn_export_pdf.clicked.connect(self.export_to_pdf)
        
        # Slider
        self.slider_cout.valueChanged.connect(self.update_cout_from_slider)
        
        # Recherche
        self.search_input.textChanged.connect(self.filter_table)
    
    # === MÉTHODES D'ACTIONS ===
    
    def apply_filters(self):
        """Applique les filtres sélectionnés."""
        logger.info("Application des filtres avancés")
        self.status_label.setText("🔍 Application des filtres...")
        self.status_label.setStyleSheet("QLabel { color: #FF9800; font-weight: bold; }")
        
        try:
            # Récupérer les paramètres de filtres
            self.filters = {
                'periode_debut': self.date_debut.date().toPython(),
                'periode_fin': self.date_fin.date().toPython(),
                'machine_id': None if self.combo_machines.currentText() == "Toutes les machines" else self.combo_machines.currentData(),
                'site_id': None if self.combo_sites.currentText() == "Tous les sites" else self.combo_sites.currentData(),
                'equipe_id': None if self.combo_equipes.currentText() == "Toutes les équipes" else self.combo_equipes.currentData(),
                'type_maintenance': None if self.combo_type_maintenance.currentText() == "Tous" else self.combo_type_maintenance.currentText(),
                'cout_min': self.spin_cout_min.value(),
                'cout_max': self.spin_cout_max.value(),
                'grouping': self.combo_grouping.currentText().lower(),
                'compare_previous': self.chk_compare_previous.isChecked(),
                'show_trend': self.chk_show_trend.isChecked()
            }
            
            # Charger les données avec filtres
            self.load_filtered_data()
            
            self.status_label.setText("✅ Filtres appliqués avec succès")
            self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des filtres: {e}")
            self.status_label.setText(f"❌ Erreur: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")
    
    def reset_filters(self):
        """Remet les filtres à zéro."""
        logger.info("Réinitialisation des filtres")
        
        # Remettre les dates par défaut
        self.date_debut.setDate(QDate.currentDate().addMonths(-3))
        self.date_fin.setDate(QDate.currentDate())
        
        # Remettre les combos par défaut
        self.combo_machines.setCurrentIndex(0)
        self.combo_sites.setCurrentIndex(0)
        self.combo_equipes.setCurrentIndex(0)
        self.combo_type_maintenance.setCurrentIndex(0)
        
        # Remettre les montants
        self.spin_cout_min.setValue(0)
        self.spin_cout_max.setValue(50000)
        self.slider_cout.setValue(25000)
        
        # Remettre les checkboxes
        self.chk_compare_previous.setChecked(False)
        self.chk_show_trend.setChecked(False)
        self.chk_enable_alerts.setChecked(False)
        self.chk_email_alerts.setChecked(False)
        
        # Vider la recherche
        self.search_input.clear()
        
        self.status_label.setText("🔄 Filtres réinitialisés")
        self.status_label.setStyleSheet("QLabel { color: #2196F3; font-weight: bold; }")
    
    def save_filters(self):
        """Sauvegarde la configuration actuelle des filtres."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Sauvegarder la configuration des filtres",
                "filtres_kpi.json",
                "JSON Files (*.json)"
            )
            
            if filename:
                config = {
                    'filters': self.filters,
                    'ui_state': {
                        'periode_debut': self.date_debut.date().toString(),
                        'periode_fin': self.date_fin.date().toString(),
                        'machine_selection': self.combo_machines.currentText(),
                        'site_selection': self.combo_sites.currentText(),
                        'equipe_selection': self.combo_equipes.currentText(),
                        'type_maintenance': self.combo_type_maintenance.currentText(),
                        'cout_min': self.spin_cout_min.value(),
                        'cout_max': self.spin_cout_max.value(),
                        'options': {
                            'compare_previous': self.chk_compare_previous.isChecked(),
                            'show_trend': self.chk_show_trend.isChecked(),
                            'enable_alerts': self.chk_enable_alerts.isChecked(),
                            'email_alerts': self.chk_email_alerts.isChecked()
                        }
                    }
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "Succès", f"Configuration sauvegardée dans:\n{filename}")
                logger.info(f"Configuration filtres sauvegardée: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde:\n{str(e)}")
            logger.error(f"Erreur sauvegarde filtres: {e}")
    
    def load_filtered_data(self):
        """Charge les données avec les filtres appliqués."""
        if not self.kpi_service:
            self.status_label.setText("❌ Service KPI non disponible")
            return
        
        try:
            # Récupérer les filtres
            periode_debut = self.filters['periode_debut']
            periode_fin = self.filters['periode_fin']
            machine_id = self.filters.get('machine_id')
            type_machine = self.filters.get('type_machine')

            # Charger les données selon les filtres
            if machine_id:
                machines_data = self.kpi_service.get_couts_par_machine(
                    periode_debut=periode_debut, 
                    periode_fin=periode_fin,
                    machine_ids=[machine_id],
                    type_machine=type_machine
                )
                data = {'machines': machines_data, 'sites': []}
            else:
                # Charger les données pour toutes les machines (potentiellement filtrées par type)
                machines_data = self.kpi_service.get_couts_par_machine(
                    periode_debut=periode_debut, 
                    periode_fin=periode_fin,
                    machine_ids=None,
                    type_machine=type_machine
                )
                sites_data = self.kpi_service.get_couts_par_site(
                    periode_debut=periode_debut, 
                    periode_fin=periode_fin
                )
                data = {
                    'machines': machines_data,
                    'sites': sites_data
                }
            
            self.current_data = data
            self.update_displays()
            
        except Exception as e:
            logger.error(f"Erreur chargement données filtrées: {e}")
            self.status_label.setText(f"❌ Erreur chargement: {str(e)}")
    
    def update_displays(self):
        """Met à jour tous les affichages avec les nouvelles données."""
        try:
            # Mettre à jour le tableau
            self.update_table()
            
            # Mettre à jour les graphiques (placeholder)
            self.update_charts_placeholder()
            
            logger.info("Affichages mis à jour avec succès")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour affichages: {e}")
    
    def update_table(self):
        """Met à jour le tableau de données."""
        if not self.current_data:
            return
        
        try:
            # Préparer les données pour le tableau
            if isinstance(self.current_data, dict) and 'machines' in self.current_data:
                rows_data = self.current_data['machines']
                headers = ['Machine', 'Site', 'Coût Total', 'Nb Interventions', 'Coût Moyen']
            elif isinstance(self.current_data, list):
                rows_data = self.current_data
                headers = ['ID', 'Nom', 'Coût Total', 'Nb Interventions', 'Coût Moyen']
            else:
                return
            
            # Configurer le tableau
            self.data_table.setRowCount(len(rows_data))
            self.data_table.setColumnCount(len(headers))
            self.data_table.setHorizontalHeaderLabels(headers)
            
            # Remplir les données
            for row_idx, row_data in enumerate(rows_data):
                if isinstance(row_data, dict):
                    # Extraire les valeurs selon les en-têtes
                    values = []
                    for header in headers:
                        if header == 'Machine':
                            values.append(row_data.get('machine_nom', ''))
                        elif header == 'Site':
                            values.append(row_data.get('site_nom', ''))
                        elif header == 'Coût Total':
                            values.append(f"{row_data.get('cout_total', 0):,.0f} €")
                        elif header == 'Nb Interventions':
                            values.append(str(row_data.get('nb_interventions', 0)))
                        elif header == 'Coût Moyen':
                            values.append(f"{row_data.get('cout_moyen_intervention', 0):,.0f} €")
                        else:
                            values.append(str(row_data.get(header.lower().replace(' ', '_'), '')))
                    
                    for col_idx, value in enumerate(values):
                        item = QTableWidgetItem(str(value))
                        self.data_table.setItem(row_idx, col_idx, item)
            
            # Auto-redimensionner les colonnes
            self.data_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour tableau: {e}")
    
    def update_charts_placeholder(self):
        """Met à jour le placeholder des graphiques."""
        if not self.current_data:
            return
        
        # Calculer quelques statistiques pour le placeholder
        try:
            if isinstance(self.current_data, dict) and 'machines' in self.current_data:
                nb_machines = len(self.current_data['machines'])
                total_cost = sum(m.get('cout_total', 0) for m in self.current_data['machines'])
                
                stats_text = f"📊 Données Chargées pour Graphiques\n\n"
                stats_text += f"• {nb_machines} machines analysées\n"
                stats_text += f"• Coût total: {total_cost:,.0f} €\n"
                stats_text += f"• Période: {self.filters.get('periode_debut', '')} à {self.filters.get('periode_fin', '')}\n\n"
                stats_text += "Graphiques disponibles:\n"
                stats_text += "• Répartition des coûts par machine\n"
                stats_text += "• Évolution temporelle\n"
                stats_text += "• Comparaisons préventif/curatif\n"
                stats_text += "• Top 10 des machines les plus coûteuses"
                
                # Mettre à jour le placeholder
                for i in reversed(range(self.charts_layout.count())):
                    self.charts_layout.itemAt(i).widget().setParent(None)
                
                updated_label = QLabel(stats_text)
                updated_label.setAlignment(Qt.AlignCenter)
                updated_label.setStyleSheet("""
                    QLabel {
                        background-color: #E8F5E8;
                        border: 2px solid #4CAF50;
                        border-radius: 10px;
                        padding: 30px;
                        font-size: 12px;
                        color: #2E7D32;
                    }
                """)
                self.charts_layout.addWidget(updated_label)
                
        except Exception as e:
            logger.error(f"Erreur mise à jour placeholder graphiques: {e}")
    
    def on_date_changed(self):
        """Gestionnaire de changement de dates."""
        # Auto-application après 2 secondes d'inactivité
        if hasattr(self, '_date_timer'):
            self._date_timer.stop()
        
        self._date_timer = QTimer()
        self._date_timer.setSingleShot(True)
        self._date_timer.timeout.connect(self.apply_filters)
        self._date_timer.start(2000)
    
    def update_cout_from_slider(self, value):
        """Met à jour les spinbox depuis le slider."""
        self.spin_cout_max.setValue(value)
    
    def filter_table(self, text):
        """Filtre le tableau selon le texte de recherche."""
        for row in range(self.data_table.rowCount()):
            match = False
            for col in range(self.data_table.columnCount()):
                item = self.data_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.data_table.setRowHidden(row, not match)
    
    # === MÉTHODES D'EXPORT ===
    
    def export_to_excel(self):
        """Exporte vers Excel."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Exporter vers Excel",
                f"kpi_analyse_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if filename:
                # TODO: Implémenter l'export Excel complet
                QMessageBox.information(self, "Export", f"Export Excel prévu vers:\n{filename}")
                logger.info(f"Export Excel demandé: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur export Excel:\n{str(e)}")
    
    def export_to_csv(self):
        """Exporte vers CSV."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Exporter vers CSV",
                f"kpi_analyse_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "CSV Files (*.csv)"
            )
            
            if filename:
                # TODO: Implémenter l'export CSV
                QMessageBox.information(self, "Export", f"Export CSV prévu vers:\n{filename}")
                logger.info(f"Export CSV demandé: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur export CSV:\n{str(e)}")
    
    def export_to_pdf(self):
        """Génère un rapport PDF."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Générer rapport PDF",
                f"rapport_kpi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if filename:
                # TODO: Implémenter la génération PDF
                QMessageBox.information(self, "Rapport", f"Rapport PDF prévu vers:\n{filename}")
                logger.info(f"Rapport PDF demandé: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur génération PDF:\n{str(e)}")


# === MAIN STANDALONE ===

if __name__ == "__main__":
    """Test standalone du widget avancé."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Créer et afficher le widget
    widget = AdvancedKPIWidget()
    widget.show()
    widget.resize(1400, 900)
    
    sys.exit(app.exec())
