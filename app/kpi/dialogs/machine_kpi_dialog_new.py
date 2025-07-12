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
import importlib.util
import os

from app.kpi.services.kpi_service import KPIService


class MachineKPIDialogNew(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # --- Setup QTranslator (en anglais par défaut) ---
        self.translator = QTranslator(self)
        self.setWindowTitle(self.tr("KPI Machines"))
        self.setFixedSize(1600, 900)
        
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
            self.tr("Avg Time"), self.tr("Criticality")
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
        self.data_table.setColumnWidth(10, 100)  # Avg Time
        self.data_table.setColumnWidth(11, 100)  # Criticality
        
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
        # Placeholder pour le graphique (à implémenter avec matplotlib/plotly)
        self.chart_placeholder = QLabel(self.tr("Chart will be displayed here"))
        self.chart_placeholder.setAlignment(Qt.AlignCenter)
        self.chart_placeholder.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                font-size: 16px;
                color: #666;
                min-height: 400px;
            }
        """)
        
        chart_layout.addWidget(self.chart_placeholder)
        
        self.tabs.addTab(self.tab_chart, self.tr("Chart"))

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
        
        # Clic sur une machine pour afficher la synthèse détaillée
        self.data_table.cellClicked.connect(self.on_machine_clicked)

    def refresh_data(self):
        """Méthode centrale pour rafraîchir les données (tableau et graphique)"""
        try:
            print("[KPI Dialog] Début refresh_data...")
            self.fill_table_overview()
            self.update_chart()
            print("[KPI Dialog] refresh_data terminé avec succès")
        except Exception as e:
            print(f"[KPI Dialog] Erreur dans refresh_data: {e}")
            # En cas d'erreur, on essaie au moins de remplir le tableau
            try:
                self.fill_table_overview()
            except Exception as e2:
                print(f"[KPI Dialog] Erreur critique dans fill_table_overview: {e2}")

    def fill_table_overview(self):
        """Remplit le tableau avec les données KPI filtrées"""
        try:
            # Récupère la période depuis les QDateEdit
            date_start = self.date_start.date().toString("yyyy-MM-dd")
            date_end = self.date_end.date().toString("yyyy-MM-dd")
            
            # Récupérer les filtres sélectionnés
            machine_id = self.combo_machine.currentData()
            type_id = self.combo_type.currentData()
            team_id = self.combo_team.currentData()
            site_id = self.combo_site.currentData()
            
            # Stratégie d'extraction des données selon le contexte
            if machine_id:
                # Si une machine spécifique est sélectionnée, utiliser la méthode dédiée
                df = self.kpi_service.get_kpi_for_machine_by_period(machine_id, date_start, date_end)
            else:
                # Sinon, récupérer toutes les machines et appliquer les filtres
                df = self.kpi_service.get_kpi_all_machines_by_period(date_start, date_end)
            
            # Appliquer les autres filtres (type, équipe, site) sur le DataFrame
            if not df.empty:
                if type_id:
                    df = df[df['type_nom'] == self.combo_type.currentText()]
                if team_id:
                    df = df[df['equipe_nom'] == self.combo_team.currentText()]
                if site_id:
                    df = df[df['site_nom'] == self.combo_site.currentText()]
            
            # Headers correspondant à l'onglet Overview
            headers = [
                "Machine", "Type", "Site", "Team", "Total Cost", "Interventions", 
                "Preventive", "Corrective", "Urgency", "Avg Cost", "Avg Time", "Criticality"
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
                "Avg Time": "duree_moyenne_h",
                "Criticality": "machine_criticite"
            }
            
            # Vider le tableau
            self.data_table.setRowCount(0)
            
            if df.empty:
                return
            
            # Remplir le tableau
            for i, row in df.iterrows():
                self.data_table.insertRow(i)
                for j, header in enumerate(headers):
                    col = col_map[header]
                    try:
                        value = row[col] if col in row else "--"
                        # Formatage des valeurs numériques
                        if isinstance(value, (int, float)) and value != "--":
                            if "Cost" in header or "cost" in header:
                                value = f"{value:.2f} €"
                            elif "Time" in header or "time" in header:
                                value = f"{value:.1f} h"
                            else:
                                value = str(int(value)) if value == int(value) else f"{value:.2f}"
                    except (KeyError, TypeError):
                        value = "--"
                    
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.data_table.setItem(i, j, item)
                    
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

    def setup_connections(self):
        """Configure les connexions des signaux pour l'interface"""
        try:
            # Connexions pour les boutons
            self.btn_reset.clicked.connect(self.reset_and_reload)
            self.btn_export.clicked.connect(self.export_data)
            self.btn_close.clicked.connect(self.close)
            
            # Connexions pour les changements de dates
            # Recalculer les données et stats quand l'utilisateur change les dates
            self.date_start.dateChanged.connect(self.on_date_changed)
            self.date_end.dateChanged.connect(self.on_date_changed)
            
            # Connexions pour les filtres (ComboBox)
            self.combo_machine.currentIndexChanged.connect(self.on_filter_changed)
            self.combo_type.currentIndexChanged.connect(self.on_filter_changed)
            self.combo_team.currentIndexChanged.connect(self.on_filter_changed)
            self.combo_site.currentIndexChanged.connect(self.on_filter_changed)
            
            # Connexion pour le clic sur une ligne du tableau
            self.data_table.cellClicked.connect(self.on_machine_clicked)
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors de la configuration des connexions: {e}")

    def on_date_changed(self):
        """Appelé quand l'utilisateur change une date - recalcule les données et stats"""
        try:
            print("[KPI Dialog] Changement de date détecté - rechargement des données...")
            # Recharger les données avec la nouvelle période
            self.fill_table_overview()
            # Recalculer les statistiques avec les nouvelles données
            self.update_stats()
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors du changement de date: {e}")

    def on_filter_changed(self):
        """Appelé quand l'utilisateur change un filtre - recalcule les données et stats"""
        try:
            print("[KPI Dialog] Changement de filtre détecté - rechargement des données...")
            # Recharger les données avec les nouveaux filtres
            self.fill_table_overview()
            # Recalculer les statistiques avec les nouvelles données
            self.update_stats()
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors du changement de filtre: {e}")

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
            self.fill_table_overview()
            
            # Réactiver le tri après le rechargement
            self.data_table.setSortingEnabled(True)
            
            # Forcer un tri par défaut sur la colonne Machine (ascendant)
            self.data_table.sortItems(0, Qt.AscendingOrder)
            
            # Mettre à jour les statistiques synthétiques
            self.update_stats()
            
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
            
            # Calculer les ratios
            avg_cost = total_cost / total_machines if total_machines > 0 else 0
            preventive_ratio = (total_preventive / total_interventions * 100) if total_interventions > 0 else 0
            efficiency = preventive_ratio  # Même calcul pour l'efficacité
            
            # Mettre à jour les labels
            self.stats_labels["total_machines"].setText(self.tr(f"Total Machines: {total_machines}"))
            self.stats_labels["total_cost"].setText(self.tr(f"Total Cost: {total_cost:,.0f}€"))
            self.stats_labels["avg_cost"].setText(self.tr(f"Avg Cost: {avg_cost:,.0f}€"))
            self.stats_labels["total_interventions"].setText(self.tr(f"Total Interventions: {total_interventions}"))
            self.stats_labels["preventive_ratio"].setText(self.tr(f"Preventive Ratio: {preventive_ratio:.0f}%"))
            self.stats_labels["efficiency"].setText(self.tr(f"Efficiency: {efficiency:.0f}%"))
            
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

    def update_chart(self):
        """Met à jour le graphique selon le type sélectionné"""
        try:
            # Pour l'instant, juste un placeholder
            chart_type = "Bar Chart" if self.radio_bars.isChecked() else "Line Chart"
            self.chart_placeholder.setText(
                self.tr(f"{chart_type} will be displayed here\n\n") +
                self.tr("Chart implementation with matplotlib/plotly coming soon...")
            )
            
        except Exception as e:
            print(f"[KPI Dialog] Erreur lors de la mise à jour du graphique: {e}")

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
            QMessageBox.warning(self, self.tr("Error"), f"Error displaying machine details: {str(e)}")

# Pour test manuel :
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dlg = MachineKPIDialogNew()
    dlg.show()
    sys.exit(app.exec())
