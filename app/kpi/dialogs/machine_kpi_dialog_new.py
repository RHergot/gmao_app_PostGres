"""
Dialog KPI Machines (nouvelle version)
Interface refaite avec structure claire :
- Cadre filtres/période autonome en haut (commun aux 2 onglets)
- Onglet Overview : uniquement le tableau
- Onglet Chart : uniquement le graphique avec commande barres/lignes
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QComboBox, QDateEdit, QWidget, QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout,
    QHeaderView, QAbstractItemView, QSplitter, QMessageBox, QProgressBar, QSlider, QCheckBox, QSizePolicy,
    QScrollArea, QFrame, QLineEdit, QGridLayout, QRadioButton, QButtonGroup
)

from PySide6.QtCore import Qt, QDate, QTranslator, QLocale, QTimer
from PySide6.QtGui import QFont

# Imports pour les graphiques
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime

# Import conditionnel de pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("[WARNING] Pandas not available. Some features may be limited.")
    PANDAS_AVAILABLE = False
    pd = None

import importlib.util
import os

from app.kpi.services.kpi_service import KPIService


class MachineKPIDialogNew(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # --- Setup QTranslator (en anglais par défaut) ---
        self.translator = QTranslator(self)
        self.setWindowTitle(self.tr("KPI Machines"))
        # self.setFixedSize(1600, 900)
        self.setGeometry(100, 100, 1920, 1080)  # Positionner la fenêtre au centre de l'écran
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Service KPI ---
        self.kpi_service = KPIService()

        # === CADRE FILTRES/PÉRIODE AUTONOME (commun aux 2 onglets) ===
        self.create_filters_frame(main_layout)
        
        # === CADRE STATISTIQUES SYNTHÉTIQUES ===
        self.create_stats_frame(main_layout)
        
        # === ONGLETS ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #c0c0c0; }")
        
        # Onglet 1 : Overview (tableau seul)
        self.create_overview_tab()
        
        # Onglet 2 : Chart (graphique seul)
        self.create_chart_tab()
        
        # Onglet 3 : Trends (statistiques temporelles)
        self.create_trends_tab()
        
        main_layout.addWidget(self.tabs)

        # === INITIALISATION (avant les connexions pour éviter les signaux prématurés) ===
        self.populate_all_combos()
        
        # === CONNEXIONS (après peuplement des combos) ===
        self.setup_connections()
        
        # === REMPLISSAGE INITIAL DU TABLEAU ===
        # Utiliser QTimer pour s'assurer que l'UI est complètement initialisée
        QTimer.singleShot(100, self.refresh_data)  # Délai de 100ms

    def create_filters_frame(self, main_layout):
        """Crée le cadre filtres/période autonome en haut"""
        filter_frame = QGroupBox()
        filter_frame.setStyleSheet("""
            QGroupBox { 
                background-color: #f8f9fa; 
                border: 2px solid #dee2e6; 
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
            }
        """)
        filter_frame.setFixedHeight(180)
        
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(20)

        # === PÉRIODE ===
        period_group = QGroupBox(self.tr("Period"))
        period_layout = QFormLayout(period_group)
        
        today = QDate.currentDate()
        self.date_start = QDateEdit(today.addDays(-90))
        self.date_end = QDateEdit(today)
        self.date_start.setCalendarPopup(True)
        self.date_end.setCalendarPopup(True)
        self.date_start.setMinimumWidth(130)
        self.date_end.setMinimumWidth(130)
        
        period_layout.addRow(self.tr("From:"), self.date_start)
        period_layout.addRow(self.tr("To:"), self.date_end)
        filter_layout.addWidget(period_group)

        # === FILTRES ===
        filters_group = QGroupBox(self.tr("Filters"))
        filters_layout = QHBoxLayout(filters_group)
        
        # Machine
        filters_layout.addWidget(QLabel(self.tr("Machine:")))
        self.combo_machine = QComboBox()
        self.combo_machine.setMinimumWidth(150)
        filters_layout.addWidget(self.combo_machine)
        
        # Type
        filters_layout.addWidget(QLabel(self.tr("Type:")))
        self.combo_type = QComboBox()
        self.combo_type.setMinimumWidth(120)
        filters_layout.addWidget(self.combo_type)
        
        # Team
        filters_layout.addWidget(QLabel(self.tr("Team:")))
        self.combo_team = QComboBox()
        self.combo_team.setMinimumWidth(120)
        filters_layout.addWidget(self.combo_team)
        
        # Site
        filters_layout.addWidget(QLabel(self.tr("Site:")))
        self.combo_site = QComboBox()
        self.combo_site.setMinimumWidth(120)
        filters_layout.addWidget(self.combo_site)
        
        filter_layout.addWidget(filters_group)

        # === ACTIONS ===
        actions_group = QGroupBox(self.tr("Actions"))
        actions_layout = QVBoxLayout(actions_group)
        
        buttons_layout = QHBoxLayout()
        self.btn_reset = QPushButton(self.tr("Reset"))
        self.btn_export = QPushButton(self.tr("Export"))
        self.btn_close = QPushButton(self.tr("Close"))
        
        self.btn_reset.setMinimumWidth(80)
        self.btn_export.setMinimumWidth(80)
        self.btn_close.setMinimumWidth(80)
        
        buttons_layout.addWidget(self.btn_reset)
        buttons_layout.addWidget(self.btn_export)
        buttons_layout.addWidget(self.btn_close)
        actions_layout.addLayout(buttons_layout)
        
        filter_layout.addWidget(actions_group)
        
        main_layout.addWidget(filter_frame)

    def create_stats_frame(self, main_layout):
        """Crée le cadre de statistiques synthétiques"""
        stats_frame = QGroupBox(self.tr("Statistics Summary"))
        stats_frame.setStyleSheet("""
            QGroupBox {
                background-color: #f0f8ff;
                border: 2px solid #b3d9ff;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #2c3e50;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        stats_frame.setFixedHeight(80)
        
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 15, 15, 15)
        stats_layout.setSpacing(30)
        
        # Dictionnaire pour stocker les labels de statistiques
        self.stats_labels = {}
        
        # Total Machines
        total_machines_label = QLabel(self.tr("Total Machines: 0"))
        total_machines_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.stats_labels["total_machines"] = total_machines_label
        stats_layout.addWidget(total_machines_label)
        
        # Total Cost
        total_cost_label = QLabel(self.tr("Total Cost: 0€"))
        total_cost_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self.stats_labels["total_cost"] = total_cost_label
        stats_layout.addWidget(total_cost_label)
        
        # Average Cost
        avg_cost_label = QLabel(self.tr("Avg Cost: 0€"))
        avg_cost_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        self.stats_labels["avg_cost"] = avg_cost_label
        stats_layout.addWidget(avg_cost_label)
        
        # Total Interventions
        total_interventions_label = QLabel(self.tr("Total Interventions: 0"))
        total_interventions_label.setStyleSheet("font-weight: bold; color: #3498db;")
        self.stats_labels["total_interventions"] = total_interventions_label
        stats_layout.addWidget(total_interventions_label)
        
        # Preventive Ratio
        preventive_ratio_label = QLabel(self.tr("Preventive Ratio: 0%"))
        preventive_ratio_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.stats_labels["preventive_ratio"] = preventive_ratio_label
        stats_layout.addWidget(preventive_ratio_label)
        
        # Efficiency
        efficiency_label = QLabel(self.tr("Efficiency: 0%"))
        efficiency_label.setStyleSheet("font-weight: bold; color: #8e44ad;")
        self.stats_labels["efficiency"] = efficiency_label
        stats_layout.addWidget(efficiency_label)
        
        main_layout.addWidget(stats_frame)

    def create_overview_tab(self):
        """Crée l'onglet Overview avec uniquement le tableau"""
        self.tab_overview = QWidget()
        overview_layout = QVBoxLayout(self.tab_overview)
        overview_layout.setContentsMargins(10, 10, 10, 10)

        # === TABLEAU SEUL ===
        headers = [
            self.tr("Machine"), self.tr("Type"), self.tr("Site"), self.tr("Team"),
            self.tr("Total Cost"), self.tr("Interventions"), self.tr("Preventive"), 
            self.tr("Corrective"), self.tr("Urgency"), self.tr("Avg Cost"), 
            self.tr("Total Time"), self.tr("Avg Time"), self.tr("Criticality")
        ]
        
        self.data_table = QTableWidget(0, len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # Style bleu pastel pour les headers
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #e6f3ff;
                color: #2c3e50;
                padding: 8px;
                border: 1px solid #b3d9ff;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #cce7ff;
                cursor: pointer;
            }
            QTableWidget::item:selected {
                background-color: #b3d9ff;
            }
        """)
        
        # Activer le tri par colonnes
        self.data_table.setSortingEnabled(False)
        
        # Configuration des largeurs de colonnes pour une meilleure lisibilité
        self.data_table.setColumnWidth(0, 200)  # Machine - plus large
        self.data_table.setColumnWidth(1, 120)  # Type
        self.data_table.setColumnWidth(2, 100)  # Site
        self.data_table.setColumnWidth(3, 100)  # Team
        self.data_table.setColumnWidth(4, 100)  # Total Cost
        self.data_table.setColumnWidth(5, 100)   # Interventions
        self.data_table.setColumnWidth(6, 100)   # Preventive
        self.data_table.setColumnWidth(7, 100)   # Corrective
        self.data_table.setColumnWidth(8, 100)   # Urgency
        self.data_table.setColumnWidth(9, 100)   # Avg Cost
        self.data_table.setColumnWidth(10, 100)  # Total Time
        self.data_table.setColumnWidth(11, 100)  # Avg Time
        self.data_table.setColumnWidth(12, 100)  # Criticality
        
        overview_layout.addWidget(self.data_table)
        
        self.tabs.addTab(self.tab_overview, self.tr("Overview"))

    def create_chart_tab(self):
        """Crée l'onglet Chart avec uniquement le graphique"""
        self.tab_chart = QWidget()
        chart_layout = QVBoxLayout(self.tab_chart)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        # === COMMANDES GRAPHIQUE ===
        chart_controls = QHBoxLayout()
        
        # Type de graphique
        chart_type_group = QButtonGroup(self)
        self.radio_bars = QRadioButton(self.tr("Bar Chart"))
        self.radio_lines = QRadioButton(self.tr("Line Chart"))
        self.radio_bars.setChecked(True)  # Par défaut
        
        chart_type_group.addButton(self.radio_bars)
        chart_type_group.addButton(self.radio_lines)
        
        chart_controls.addWidget(QLabel(self.tr("Chart Type:")))
        chart_controls.addWidget(self.radio_bars)
        chart_controls.addWidget(self.radio_lines)
        chart_controls.addStretch()
        
        chart_layout.addLayout(chart_controls)

        # === ZONE GRAPHIQUE ===
        # Widget matplotlib pour les graphiques
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(400)
        
        chart_layout.addWidget(self.canvas)
        
        self.tabs.addTab(self.tab_chart, self.tr("Chart"))

    def create_trends_tab(self):
        """Crée l'onglet Trends avec statistiques temporelles"""
        self.tab_trends = QWidget()
        trends_layout = QVBoxLayout(self.tab_trends)
        trends_layout.setContentsMargins(10, 10, 10, 10)

        # === COMMANDES GRANULARITÉ ===
        granularity_controls = QHBoxLayout()
        
        # Granularité temporelle
        granularity_group = QButtonGroup(self)
        self.radio_daily = QRadioButton(self.tr("Daily"))
        self.radio_weekly = QRadioButton(self.tr("Weekly"))
        self.radio_monthly = QRadioButton(self.tr("Monthly"))
        self.radio_daily.setChecked(True)  # Par défaut
        
        granularity_group.addButton(self.radio_daily)
        granularity_group.addButton(self.radio_weekly)
        granularity_group.addButton(self.radio_monthly)
        
        granularity_controls.addWidget(QLabel(self.tr("Time Granularity:")))
        granularity_controls.addWidget(self.radio_daily)
        granularity_controls.addWidget(self.radio_weekly)
        granularity_controls.addWidget(self.radio_monthly)
        granularity_controls.addStretch()
        
        trends_layout.addLayout(granularity_controls)

        # === ZONE GRAPHIQUE TEMPOREL ===
        # Widget matplotlib pour les courbes temporelles
        self.trends_figure = Figure(figsize=(14, 8))
        self.trends_canvas = FigureCanvas(self.trends_figure)
        self.trends_canvas.setMinimumHeight(500)
        
        trends_layout.addWidget(self.trends_canvas)
        
        self.tabs.addTab(self.tab_trends, self.tr("Trends"))

    def setup_connections(self):
        """Configure toutes les connexions de signaux"""
        # Boutons
        self.btn_close.clicked.connect(self.close)
        self.btn_reset.clicked.connect(self.reset_and_reload)
        self.btn_export.clicked.connect(self.export_data)

        # Filtres/période → MAJ automatique des données
        self.date_start.dateChanged.connect(self.refresh_data)
        self.date_end.dateChanged.connect(self.refresh_data)
        self.combo_machine.currentIndexChanged.connect(self.refresh_data)
        self.combo_type.currentIndexChanged.connect(self.refresh_data)
        self.combo_team.currentIndexChanged.connect(self.refresh_data)
        self.combo_site.currentIndexChanged.connect(self.refresh_data)
        
        # Type de graphique
        self.radio_bars.toggled.connect(self.update_chart)
        self.radio_lines.toggled.connect(self.update_chart)
        
        # Granularité temporelle
        self.radio_daily.toggled.connect(self.update_trends)
        self.radio_weekly.toggled.connect(self.update_trends)
        self.radio_monthly.toggled.connect(self.update_trends)
        
        # Clic sur une machine pour afficher la synthèse détaillée
        self.data_table.cellClicked.connect(self.on_machine_clicked)

    def refresh_data(self):
        """Méthode centrale pour rafraîchir les données (tableau et graphique)"""
        try:
            # print("[KPI Dialog] Début refresh_data...")
            self.fill_table_overview()
            self.update_stats()
            self.update_chart()
            self.update_trends()
            # print("[KPI Dialog] refresh_data terminé avec succès")
        except Exception as e:
            print(f"[KPI Dialog] Erreur dans refresh_data: {e}")
            # En cas d'erreur, on essaie au moins de remplir le tableau
            try:
                self.fill_table_overview()
                self.update_stats()
            except Exception as e2:
                print(f"[KPI Dialog] Erreur critique dans fill_table_overview: {e2}")

    def fill_table_overview(self):
        """Remplit le tableau avec les données KPI filtrées"""
        try:
            # Récupère la période depuis les QDateEdit
            date_start = self.date_start.date().toString("yyyy-MM-dd")
            date_end = self.date_end.date().toString("yyyy-MM-dd")
            print(f"[DEBUG] Période: {date_start} à {date_end}")
            
            # Récupérer les filtres sélectionnés
            machine_id = self.combo_machine.currentData()
            type_id = self.combo_type.currentData()
            team_id = self.combo_team.currentData()
            site_id = self.combo_site.currentData()
            
            print(f"[DEBUG] Filtres - Machine ID: {machine_id}, Type ID: {type_id}, Team ID: {team_id}, Site ID: {site_id}")
            print(f"[DEBUG] Filtres - Machine: '{self.combo_machine.currentText()}', Type: '{self.combo_type.currentText()}', Team: '{self.combo_team.currentText()}', Site: '{self.combo_site.currentText()}'")
            
            # Stratégie d'extraction des données selon le contexte
            if machine_id:
                # Si une machine spécifique est sélectionnée, utiliser la méthode dédiée
                print(f"[DEBUG] Récupération données pour machine ID: {machine_id}")
                df = self.kpi_service.get_kpi_for_machine_by_period(machine_id, date_start, date_end)
            else:
                # Sinon, récupérer toutes les machines et appliquer les filtres
                print(f"[DEBUG] Récupération données pour toutes les machines")
                df = self.kpi_service.get_kpi_all_machines_by_period(date_start, date_end)
            
            print(f"[DEBUG] DataFrame initial - Shape: {df.shape if not df.empty else 'VIDE'}")
            if not df.empty:
                print(f"[DEBUG] Colonnes disponibles: {list(df.columns)}")
                print(f"[DEBUG] Premières lignes:\n{df.head(2)}")
                
                # Diagnostiquer les valeurs uniques pour le filtrage
                if 'type_nom' in df.columns:
                    print(f"[DEBUG] Types uniques dans DataFrame: {sorted(df['type_nom'].dropna().unique())}")
                if 'equipe_nom' in df.columns:
                    print(f"[DEBUG] Équipes uniques dans DataFrame: {sorted(df['equipe_nom'].dropna().unique())}")
                if 'site_nom' in df.columns:
                    print(f"[DEBUG] Sites uniques dans DataFrame: {sorted(df['site_nom'].dropna().unique())}")
            
            # Appliquer les autres filtres (type, équipe, site) sur le DataFrame
            if not df.empty:
                # FILTRE 1: Type Machine (par nom car pas d'ID dans la vue)
                if type_id:
                    selected_type_name = self.combo_type.currentText()
                    if selected_type_name != self.tr("All types"):
                        print(f"[DEBUG] Filtrage par type: '{selected_type_name}'")
                        df_before = len(df)
                        df = df[df['type_nom'] == selected_type_name]
                        print(f"[DEBUG] Après filtre type: {df_before} -> {len(df)} lignes")
                
                # FILTRE 2: Équipe (par nom car pas d'ID dans la vue)
                if team_id:
                    selected_team_name = self.combo_team.currentText()
                    if selected_team_name != self.tr("All teams"):
                        print(f"[DEBUG] Filtrage par équipe: '{selected_team_name}'")
                        df_before = len(df)
                        df = df[df['equipe_nom'] == selected_team_name]
                        print(f"[DEBUG] Après filtre équipe: {df_before} -> {len(df)} lignes")
                
                # FILTRE 3: Site (par nom car pas d'ID dans la vue)
                if site_id:
                    selected_site_name = self.combo_site.currentText()
                    if selected_site_name != self.tr("All sites"):
                        print(f"[DEBUG] Filtrage par site: '{selected_site_name}'")
                        df_before = len(df)
                        df = df[df['site_nom'] == selected_site_name]
                        print(f"[DEBUG] Après filtre site: {df_before} -> {len(df)} lignes")
            
            # CORRECTION CRITIQUE: Reset des index après filtrage
            if not df.empty:
                df = df.reset_index(drop=True)
                print(f"[DEBUG] Index DataFrame réinitialisés: {df.index.tolist()}")
            
            # Headers correspondant à l'onglet Overview
            headers = [
                "Machine", "Type", "Site", "Team", "Total Cost", "Interventions", 
                "Preventive", "Corrective", "Urgency", "Avg Cost", "Total Time", "Avg Time", "Criticality"
            ]
            
            # Mapping colonnes DataFrame -> headers UI
            col_map = {
                "Machine": "machine_nom",
                "Type": "type_nom",
                "Site": "site_nom",
                "Team": "equipe_nom",
                "Total Cost": "cout_total_jour",
                "Interventions": "nb_interventions",
                "Preventive": "nb_preventif",
                "Corrective": "nb_correctif",
                "Urgency": "nb_urgence",
                "Avg Cost": "cout_moyen_intervention",
                "Total Time": "duree_totale",  # Nouvelle colonne
                "Avg Time": "duree_moyenne_h",
                "Criticality": "machine_criticite"
            }
            
            # Vider le tableau
            self.data_table.setRowCount(0)
            
            # print(f"[DEBUG] DataFrame final - Shape: {df.shape if not df.empty else 'VIDE'}")
            
            if df.empty:
                # print(f"[DEBUG] TABLEAU VIDE - Aucune donnée à afficher")
                return
            
            # print(f"[DEBUG] Remplissage du tableau avec {len(df)} lignes")
            
            # Remplir le tableau
            for i, row in df.iterrows():
                # print(f"[DEBUG] Ligne {i}: {dict(row)}")
                self.data_table.insertRow(i)
                for j, header in enumerate(headers):
                    col = col_map[header]
                    try:
                        value = row[col] if col in row else "--"
                        # print(f"[DEBUG] Colonne {j} ({header} -> {col}): {value}")
                        # Formatage des valeurs numériques
                        if isinstance(value, (int, float)) and value != "--":
                            if "Cost" in header or "cost" in header:
                                formatted_value = f"{value:.2f} €"
                            elif "Time" in header or "time" in header:
                                formatted_value = f"{value:.1f} h"
                            else:
                                formatted_value = str(int(value)) if value == int(value) else f"{value:.2f}"
                        else:
                            formatted_value = str(value)
                    except (KeyError, TypeError) as e:
                        print(f"[DEBUG] ERREUR colonne {header} -> {col}: {e}")
                        formatted_value = "--"
                    
                    item = QTableWidgetItem(formatted_value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.data_table.setItem(i, j, item)
                    # print(f"[DEBUG] Item ajouté en ({i}, {j}): '{formatted_value}'")
                    
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors du remplissage du tableau: {e}")
            QMessageBox.warning(self, self.tr("Error"), f"Error loading data: {str(e)}")

    def populate_all_combos(self):
        """Peuple tous les ComboBox avec les données de la base"""
        try:
            # Récupérer toutes les machines (DataFrame -> dictionnaires)
            machines_df = self.kpi_service.get_all_machines()
            self.combo_machine.clear()
            self.combo_machine.addItem(self.tr("All machines"), None)
            if not machines_df.empty:
                # Trier par nom en ordre ascendant pour stabiliser le tableau
                machines_df = machines_df.sort_values('nom', ascending=True)
                for _, row in machines_df.iterrows():
                    self.combo_machine.addItem(row['nom'], row['id_machine'])
            
            # Récupérer tous les types (DataFrame -> dictionnaires)
            types_df = self.kpi_service.get_all_types()
            self.combo_type.clear()
            self.combo_type.addItem(self.tr("All types"), None)
            if not types_df.empty:
                # Trier par nom en ordre ascendant
                types_df = types_df.sort_values('nom', ascending=True)
                for _, row in types_df.iterrows():
                    self.combo_type.addItem(row['nom'], row['id_type_machine'])
            
            # Récupérer toutes les équipes (DataFrame -> dictionnaires)
            teams_df = self.kpi_service.get_all_teams()
            self.combo_team.clear()
            self.combo_team.addItem(self.tr("All teams"), None)
            if not teams_df.empty:
                # Trier par nom en ordre ascendant
                teams_df = teams_df.sort_values('nom', ascending=True)
                for _, row in teams_df.iterrows():
                    self.combo_team.addItem(row['nom'], row['id_equipe'])
            
            # Récupérer tous les sites (DataFrame -> dictionnaires)
            sites_df = self.kpi_service.get_all_sites()
            self.combo_site.clear()
            self.combo_site.addItem(self.tr("All sites"), None)
            if not sites_df.empty:
                # Trier par nom en ordre ascendant
                sites_df = sites_df.sort_values('nom', ascending=True)
                for _, row in sites_df.iterrows():
                    self.combo_site.addItem(row['nom'], row['id_site'])
                
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors du peuplement des combos: {e}")
            QMessageBox.warning(self, self.tr("Error"), f"Error loading filters: {str(e)}")

    def reset_and_reload(self):
        """Remet à zéro tous les filtres et recharge les données"""
        try:
            print("[KPI Dialog] Début reset_and_reload...")
            
            # Désactiver temporairement le tri pour éviter les conflits
            self.data_table.setSortingEnabled(False)
            
            # Vider le tableau d'abord
            self.data_table.setRowCount(0)
            
            # NE PAS remettre les dates par défaut lors du reset
            # L'utilisateur garde sa période choisie pour calculer les stats
            
            # Recharger les combos (sans déclencher les signaux)
            self.combo_machine.blockSignals(True)
            self.combo_type.blockSignals(True)
            self.combo_team.blockSignals(True)
            self.combo_site.blockSignals(True)
            
            self.populate_all_combos()
            
            # Reset des combos à "All"
            self.combo_machine.setCurrentIndex(0)
            self.combo_type.setCurrentIndex(0)
            self.combo_team.setCurrentIndex(0)
            self.combo_site.setCurrentIndex(0)
            
            # Réactiver les signaux
            self.combo_machine.blockSignals(False)
            self.combo_type.blockSignals(False)
            self.combo_team.blockSignals(False)
            self.combo_site.blockSignals(False)
            
            # Forcer le rechargement des données avec un délai
            QTimer.singleShot(200, self.force_refresh_data)
            
            print("[KPI Dialog] reset_and_reload terminé")
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors du reset: {e}")
            QMessageBox.warning(self, self.tr("Error"), f"Error during reset: {str(e)}")
    
    def force_refresh_data(self):
        """Force le rechargement des données (utilisé après reset)"""
        try:
            print("[KPI Dialog] Force refresh des données...")
            # Utiliser refresh_data() pour mettre à jour TOUT (tableau + graphiques + statistiques)
            self.refresh_data()
            
            # Réactiver le tri après le rechargement
            self.data_table.setSortingEnabled(True)
            
            # Forcer un tri par défaut sur la colonne Machine (ascendant)
            self.data_table.sortItems(0, Qt.AscendingOrder)
            
            print("[KPI Dialog] Force refresh terminé")
        except Exception as e:
            print(f"[KPI Dialog] Erreur dans force_refresh_data: {e}")

    def update_stats(self):
        """Met à jour les statistiques synthétiques basées sur les données du tableau"""
        try:
            if not hasattr(self, 'stats_labels') or self.data_table.rowCount() == 0:
                # Réinitialiser les statistiques si pas de données
                if hasattr(self, 'stats_labels'):
                    self.stats_labels["total_machines"].setText(self.tr("Total Machines: 0"))
                    self.stats_labels["total_cost"].setText(self.tr("Total Cost: 0€"))
                    self.stats_labels["avg_cost"].setText(self.tr("Avg Cost: 0€"))
                    self.stats_labels["total_interventions"].setText(self.tr("Total Interventions: 0"))
                    self.stats_labels["preventive_ratio"].setText(self.tr("Preventive Ratio: 0%"))
                    self.stats_labels["efficiency"].setText(self.tr("Efficiency: 0%"))
                return
            
            # Calculer les statistiques à partir du tableau
            total_machines = self.data_table.rowCount()
            total_cost = 0
            total_interventions = 0
            total_preventive = 0
            total_time = 0  # Temps total d'intervention en heures
            
            for row in range(total_machines):
                # Total Cost (colonne 4)
                cost_item = self.data_table.item(row, 4)
                if cost_item:
                    try:
                        cost_text = cost_item.text().replace('€', '').replace(',', '').strip()
                        total_cost += float(cost_text) if cost_text else 0
                    except ValueError:
                        pass
                
                # Total Interventions (colonne 5)
                interventions_item = self.data_table.item(row, 5)
                if interventions_item:
                    try:
                        total_interventions += int(interventions_item.text()) if interventions_item.text() else 0
                    except ValueError:
                        pass
                
                # Preventive (colonne 6)
                preventive_item = self.data_table.item(row, 6)
                if preventive_item:
                    try:
                        total_preventive += int(preventive_item.text()) if preventive_item.text() else 0
                    except ValueError:
                        pass
                
                # Total Time (colonne 10)
                time_item = self.data_table.item(row, 10)
                if time_item:
                    try:
                        time_text = time_item.text().replace('h', '').replace(',', '').strip()
                        total_time += float(time_text) if time_text else 0
                    except ValueError:
                        pass
            
            # Calculer les ratios
            avg_cost = total_cost / total_interventions if total_interventions > 0 else 0
            preventive_ratio = (total_preventive / total_interventions * 100) if total_interventions > 0 else 0
            
            # Calcul d'efficience approximative (temps intervention / temps théorique)
            # Temps théorique : 6h par jour par machine
            THEORETICAL_WORK_TIME_PER_DAY = 6.0  # heures
            
            # Calculer le nombre de jours dans la période sélectionnée
            start_date = self.date_start.date()
            end_date = self.date_end.date()
            days_in_period = (end_date.toPython() - start_date.toPython()).days + 1
            
            # Temps théorique total pour toutes les machines sur la période
            theoretical_total_time = total_machines * THEORETICAL_WORK_TIME_PER_DAY * days_in_period
            
            # Efficience = 100 - (Temps intervention / Temps théorique) * 100
            # Plus le pourcentage est élevé, mieux c'est (temps de disponibilité)
            intervention_ratio = (total_time / theoretical_total_time * 100) if theoretical_total_time > 0 else 0
            efficiency = 100 - intervention_ratio
            
            # Mettre à jour les labels
            self.stats_labels["total_machines"].setText(self.tr(f"Total Machines: {total_machines}"))
            self.stats_labels["total_cost"].setText(self.tr(f"Total Cost: {total_cost:,.0f}€"))
            self.stats_labels["avg_cost"].setText(self.tr(f"Avg Cost: {avg_cost:,.0f}€"))
            self.stats_labels["total_interventions"].setText(self.tr(f"Total Interventions: {total_interventions}"))
            self.stats_labels["preventive_ratio"].setText(self.tr(f"Preventive Ratio: {preventive_ratio:.0f}%"))
            self.stats_labels["efficiency"].setText(self.tr(f"Availability (6h/day): {efficiency:.1f}%"))
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors de la mise à jour des statistiques: {e}")

    def export_data(self):
        """Exporte les données du tableau vers un fichier CSV"""
        try:
            if self.data_table.rowCount() == 0:
                QMessageBox.information(self, self.tr("Export"), self.tr("No data to export"))
                return
            
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                self.tr("Export KPI Data"), 
                f"kpi_machines_{QDate.currentDate().toString('yyyy-MM-dd')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Headers
                    headers = []
                    for col in range(self.data_table.columnCount()):
                        headers.append(self.data_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Data
                    for row in range(self.data_table.rowCount()):
                        row_data = []
                        for col in range(self.data_table.columnCount()):
                            item = self.data_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                QMessageBox.information(self, self.tr("Export"), 
                                      self.tr(f"Data exported successfully to {file_path}"))
                
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors de l'export: {e}")
            QMessageBox.warning(self, self.tr("Error"), f"Error during export: {str(e)}")

    def update_trends(self):
        """Met à jour les courbes temporelles selon la granularité sélectionnée"""
        try:
            # Vérifier si pandas est disponible
            if not PANDAS_AVAILABLE:
                # Afficher un message d'erreur si pandas n'est pas disponible
                self.trends_figure.clear()
                ax = self.trends_figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Pandas library is required for trends analysis.\nPlease install pandas: pip install pandas',
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14, color='red')
                ax.set_title(self.tr('Trends Analysis - Missing Dependency'))
                self.trends_canvas.draw()
                return
            
            # Effacer le graphique précédent
            self.trends_figure.clear()
            
            # Récupérer les dates
            start_date = self.date_start.date().toPython()
            end_date = self.date_end.date().toPython()
            
            # Récupérer les données temporelles (par jour) depuis v_kpi_machine_jour
            df = self.kpi_service.get_temporal_kpi_data(start_date, end_date)
            
            if not df.empty:
                # Appliquer les filtres - utiliser le TEXTE et non l'ID pour filtrer les DataFrame
                machine_filter = self.combo_machine.currentText()
                type_filter = self.combo_type.currentText()
                team_filter = self.combo_team.currentText()
                site_filter = self.combo_site.currentText()
                
                # Appliquer les filtres par NOM (pas par ID)
                if machine_filter and machine_filter != self.tr("All machines"):
                    df = df[df['machine_nom'] == machine_filter]
                if type_filter and type_filter != self.tr("All types"):
                    df = df[df['type_nom'] == type_filter]
                if team_filter and team_filter != self.tr("All teams"):
                    df = df[df['equipe_nom'] == team_filter]
                if site_filter and site_filter != self.tr("All sites"):
                    df = df[df['site_nom'] == site_filter]
            
            if df.empty:
                # Afficher un message si pas de données
                ax = self.trends_figure.add_subplot(111)
                ax.text(0.5, 0.5, self.tr('No data available for the selected period and filters'),
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14)
                ax.set_title(self.tr('Temporal Trends'))
                self.trends_canvas.draw()
                return
            
            # Déterminer la granularité
            if self.radio_daily.isChecked():
                granularity = 'D'  # Daily
                title_suffix = self.tr('(Daily)')
            elif self.radio_weekly.isChecked():
                granularity = 'W'  # Weekly
                title_suffix = self.tr('(Weekly)')
            else:  # Monthly
                granularity = 'M'  # Monthly
                title_suffix = self.tr('(Monthly)')
            
            # Traitement des vraies données temporelles
            
            # Convertir la colonne 'jour' en datetime
            df['jour'] = pd.to_datetime(df['jour'])
            
            # Agréger les données par jour (somme de toutes les machines pour chaque jour)
            daily_df = df.groupby('jour').agg({
                'cout_total_jour': 'sum',
                'nb_interventions': 'sum', 
                'duree_totale': 'sum'
            }).reset_index()
            
            # Renommer les colonnes pour cohérence
            daily_df = daily_df.rename(columns={
                'jour': 'date',
                'cout_total_jour': 'total_cost',
                'nb_interventions': 'interventions',
                'duree_totale': 'duration'
            })
            
            # Agréger selon la granularité sélectionnée
            if granularity != 'D' and not daily_df.empty:
                temp_df = daily_df.set_index('date').resample(granularity).agg({
                    'total_cost': 'sum',
                    'interventions': 'sum',
                    'duration': 'sum'
                }).reset_index()
            else:
                temp_df = daily_df
            
            # Créer les 3 sous-graphiques (si on a des données)
            if not temp_df.empty:
                fig = self.trends_figure
                
                # Graphique 1: Total Cost
                ax1 = fig.add_subplot(3, 1, 1)
                ax1.plot(temp_df['date'], temp_df['total_cost'], 'b-', linewidth=2, marker='o')
                ax1.set_title(f"{self.tr('Total Cost')} {title_suffix}", fontsize=12, fontweight='bold')
                ax1.set_ylabel(self.tr('Cost (€)'), fontsize=10)
                ax1.grid(True, alpha=0.3)
                
                # Graphique 2: Nombre d'interventions
                ax2 = fig.add_subplot(3, 1, 2)
                ax2.plot(temp_df['date'], temp_df['interventions'], 'g-', linewidth=2, marker='s')
                ax2.set_title(f"{self.tr('Number of Interventions')} {title_suffix}", fontsize=12, fontweight='bold')
                ax2.set_ylabel(self.tr('Interventions'), fontsize=10)
                ax2.grid(True, alpha=0.3)
                
                # Graphique 3: Durée des interventions
                ax3 = fig.add_subplot(3, 1, 3)
                ax3.plot(temp_df['date'], temp_df['duration'], 'r-', linewidth=2, marker='^')
                ax3.set_title(f"{self.tr('Intervention Duration')} {title_suffix}", fontsize=12, fontweight='bold')
                ax3.set_ylabel(self.tr('Duration (h)'), fontsize=10)
                ax3.set_xlabel(self.tr('Date'), fontsize=10)
                ax3.grid(True, alpha=0.3)
                
                # Ajuster l'espacement
                fig.tight_layout(pad=2.0)
            
            # Rafraîchir l'affichage
            self.trends_canvas.draw()
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur dans update_trends: {e}")
            QMessageBox.warning(self, self.tr("Error"), f"Trends error: {str(e)}")

    def on_machine_clicked(self, row, column):
        """Affiche une synthèse détaillée de la machine sélectionnée"""
        try:
            # Récupérer les informations de la machine cliquée
            machine_item = self.data_table.item(row, 0)  # Colonne Machine
            if not machine_item:
                return
            
            machine_name = machine_item.text()
            
            # Récupérer toutes les données de la ligne
            row_data = {}
            headers = [
                "Machine", "Type", "Site", "Team", "Total Cost", "Interventions", 
                "Preventive", "Corrective", "Urgency", "Avg Cost", "Avg Time", "Criticality"
            ]
            
            for col in range(self.data_table.columnCount()):
                item = self.data_table.item(row, col)
                if item and col < len(headers):
                    row_data[headers[col]] = item.text()
            
            # Créer le message de synthèse détaillée
            synthesis_msg = self.tr(f"""MACHINE SYNTHESIS: {machine_name}

📍 IDENTIFICATION:
   • Type: {row_data.get('Type', 'N/A')}
   • Site: {row_data.get('Site', 'N/A')}
   • Team: {row_data.get('Team', 'N/A')}
   • Criticality: {row_data.get('Criticality', 'N/A')}

💰 FINANCIAL PERFORMANCE:
   • Total Cost: {row_data.get('Total Cost', 'N/A')}
   • Average Cost per Intervention: {row_data.get('Avg Cost', 'N/A')}

🔧 MAINTENANCE ACTIVITY:
   • Total Interventions: {row_data.get('Interventions', 'N/A')}
   • Preventive: {row_data.get('Preventive', 'N/A')}
   • Corrective: {row_data.get('Corrective', 'N/A')}
   • Urgency: {row_data.get('Urgency', 'N/A')}

⏱️ TIME PERFORMANCE:
   • Average Time per Intervention: {row_data.get('Avg Time', 'N/A')}

📊 ANALYSIS PERIOD:
   • From: {self.date_start.date().toString('dd/MM/yyyy')}
   • To: {self.date_end.date().toString('dd/MM/yyyy')}
""")
            
            # Afficher la synthèse dans une boîte de dialogue
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.tr(f"Machine Details - {machine_name}"))
            msg_box.setText(synthesis_msg)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Style de la boîte de dialogue
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f9fa;
                }
                QMessageBox QLabel {
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 11px;
                    color: #2c3e50;
                }
            """)
            
            msg_box.exec()
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors de l'affichage de la synthèse: {e}")

    def update_chart(self):
        """Met à jour le graphique selon le type sélectionné"""
        try:
            # print("[KPI Dialog] Début update_chart...")
            
            # Effacer le graphique précédent
            self.figure.clear()
            
            # Récupérer les données filtrées (même logique que le tableau)
            start_date = self.date_start.date().toPython()
            end_date = self.date_end.date().toPython()
            
            # Récupérer les données KPI (même logique que le tableau Overview)
            df = self.kpi_service.get_kpi_all_machines_by_period(start_date, end_date)
            
            # Appliquer les filtres (même logique que fill_table_overview)
            if not df.empty:
                # Récupérer les filtres - utiliser le TEXTE et non l'ID pour filtrer les DataFrame
                machine_filter = self.combo_machine.currentText()
                type_filter = self.combo_type.currentText()
                team_filter = self.combo_team.currentText()
                site_filter = self.combo_site.currentText()
                
                # Appliquer les filtres par NOM (pas par ID)
                if machine_filter and machine_filter != self.tr("All machines"):
                    df = df[df['machine_nom'] == machine_filter]
                if type_filter and type_filter != self.tr("All types"):
                    df = df[df['type_nom'] == type_filter]
                if team_filter and team_filter != self.tr("All teams"):
                    df = df[df['equipe_nom'] == team_filter]
                if site_filter and site_filter != self.tr("All sites"):
                    df = df[df['site_nom'] == site_filter]
                
                # Réinitialiser les index après filtrage
                df = df.reset_index(drop=True)
            
            if df.empty:
                # Afficher un message si pas de données
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No data available for the selected filters', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14, color='gray')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                self.canvas.draw()
                return
            
            # Limiter à 10 machines max pour la lisibilité
            df_chart = df.head(10).copy()
            
            # Créer le graphique selon le type sélectionné
            if self.radio_bars.isChecked():
                self._create_bar_chart(df_chart)
            else:
                self._create_line_chart(df_chart)
            
            # Rafraîchir l'affichage
            self.canvas.draw()
            # print("[KPI Dialog] update_chart terminé avec succès")
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur dans update_chart: {e}")
            # Afficher un message d'erreur sur le graphique
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Error loading chart: {str(e)}', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=12, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.canvas.draw()
    
    def _create_bar_chart(self, df):
        """Crée un graphique en barres"""
        ax = self.figure.add_subplot(111)
        
        # Données pour le graphique
        machines = df['machine_nom'].tolist()
        costs = df['cout_total_jour'].tolist()
        interventions = df['nb_interventions'].tolist()
        
        # Créer un graphique à double axe Y
        ax2 = ax.twinx()
        
        # Barres pour les coûts (axe gauche)
        bars1 = ax.bar([i - 0.2 for i in range(len(machines))], costs, 
                      width=0.4, label='Total Cost (€)', color='#3498db', alpha=0.7)
        
        # Barres pour les interventions (axe droit)
        bars2 = ax2.bar([i + 0.2 for i in range(len(machines))], interventions, 
                       width=0.4, label='Interventions', color='#e74c3c', alpha=0.7)
        
        # Configuration des axes
        ax.set_xlabel('Machines', fontsize=12)
        ax.set_ylabel('Total Cost (€)', fontsize=12, color='#3498db')
        ax2.set_ylabel('Number of Interventions', fontsize=12, color='#e74c3c')
        
        # Étiquettes des machines (rotation pour lisibilité)
        ax.set_xticks(range(len(machines)))
        ax.set_xticklabels(machines, rotation=45, ha='right')
        
        # Légendes
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
        # Titre
        period_str = f"{self.date_start.date().toString('dd/MM/yyyy')} - {self.date_end.date().toString('dd/MM/yyyy')}"
        ax.set_title(f'Machine KPI - Cost & Interventions\n{period_str}', fontsize=14, pad=20)
        
        # Ajuster la mise en page
        self.figure.tight_layout()
    
    def _create_line_chart(self, df):
        """Crée un graphique en lignes"""
        ax = self.figure.add_subplot(111)
        
        # Données pour le graphique
        machines = df['machine_nom'].tolist()
        costs = df['cout_total_jour'].tolist()
        avg_costs = df['cout_moyen_intervention'].tolist()
        
        # Créer les lignes
        x_pos = range(len(machines))
        
        line1 = ax.plot(x_pos, costs, marker='o', linewidth=2, 
                       label='Total Cost (€)', color='#3498db', markersize=6)
        
        # Axe secondaire pour les coûts moyens
        ax2 = ax.twinx()
        line2 = ax2.plot(x_pos, avg_costs, marker='s', linewidth=2, 
                        label='Avg Cost (€)', color='#e74c3c', markersize=6)
        
        # Configuration des axes
        ax.set_xlabel('Machines', fontsize=12)
        ax.set_ylabel('Total Cost (€)', fontsize=12, color='#3498db')
        ax2.set_ylabel('Average Cost per Intervention (€)', fontsize=12, color='#e74c3c')
        
        # Étiquettes des machines
        ax.set_xticks(x_pos)
        ax.set_xticklabels(machines, rotation=45, ha='right')
        
        # Légendes
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
        # Titre
        period_str = f"{self.date_start.date().toString('dd/MM/yyyy')} - {self.date_end.date().toString('dd/MM/yyyy')}"
        ax.set_title(f'Machine KPI - Cost Trends\n{period_str}', fontsize=14, pad=20)
        
        # Grille pour améliorer la lisibilité
        ax.grid(True, alpha=0.3)
        
        # Ajuster la mise en page
        self.figure.tight_layout()

# Pour test manuel :
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dlg = MachineKPIDialogNew()
    dlg.show()
    sys.exit(app.exec())
