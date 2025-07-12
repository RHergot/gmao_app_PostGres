"""
Dialog KPI Machines (nouvelle version)
Squelette de l'interface pour validation fonctionnelle et ergonomique.

- Sélection période (date début/fin)
- Filtres : machine, type, équipe, site (ComboBox)
- Actions : reset, export, fermer
- Deux onglets : Overview (tableau), Graphiques (Bar/Lines)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QComboBox, QDateEdit, QWidget, QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout,
    QHeaderView, QAbstractItemView, QSplitter, QMessageBox, QProgressBar, QSlider, QCheckBox, QSizePolicy,
    QScrollArea, QFrame, QLineEdit, QGridLayout
)

from PySide6.QtCore import Qt, QDate, QTranslator, QLocale
import importlib.util
import os

from app.kpi.services.kpi_service import KPIService


class MachineKPIDialogNew(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # --- Setup QTranslator (en anglais par défaut) ---
        self.translator = QTranslator(self)
        # Ici on pourrait charger un .qm selon la langue, mais anglais par défaut
        self.setWindowTitle(self.tr("KPI Machines (new version)"))
        self.setFixedSize(1600, 900)
        main_layout = QVBoxLayout(self)

        # --- Service KPI ---
        self.kpi_service = KPIService()

        # --- Bloc fusionné période + filtres + boutons, ancré en haut ---
        filter_period_box = QGroupBox()
        filter_period_box.setStyleSheet("QGroupBox { background-color: #f7f7fa; border: 1px solid #e0e0e0; margin-top: 4px; }")
        filter_period_layout = QHBoxLayout()
        filter_period_layout.setContentsMargins(8, 4, 8, 4)
        filter_period_layout.setSpacing(12)

        # Dates dans QFormLayout vertical, police lisible
        date_form = QFormLayout()
        today = QDate.currentDate()
        self.date_start = QDateEdit(today.addDays(-90))
        self.date_end = QDateEdit(today)
        self.date_start.setCalendarPopup(True)
        self.date_end.setCalendarPopup(True)
        self.date_start.setMinimumWidth(120)
        self.date_end.setMinimumWidth(120)
        self.date_start.setStyleSheet("font-size: 12px; padding: 2px 6px;")
        self.date_end.setStyleSheet("font-size: 12px; padding: 2px 6px;")
        date_form.addRow(QLabel(self.tr("From :")), self.date_start)
        date_form.addRow(QLabel(self.tr("To :")), self.date_end)
        date_widget = QWidget()
        date_widget.setLayout(date_form)
        filter_period_layout.addWidget(date_widget)

        # Filtres à droite, tailles fixes
        filters_layout = QHBoxLayout()
        self.combo_machine = QComboBox(); self.combo_machine.setMinimumWidth(120); self.combo_machine.setMaximumWidth(200)
        self.combo_type = QComboBox(); self.combo_type.setMinimumWidth(120); self.combo_type.setMaximumWidth(200)
        self.combo_team = QComboBox(); self.combo_team.setMinimumWidth(120); self.combo_team.setMaximumWidth(200)
        self.combo_site = QComboBox(); self.combo_site.setMinimumWidth(120); self.combo_site.setMaximumWidth(200)
        filters_layout.addWidget(QLabel(self.tr("Machine :")))
        filters_layout.addWidget(self.combo_machine)
        filters_layout.addWidget(QLabel(self.tr("Type :")))
        filters_layout.addWidget(self.combo_type)
        filters_layout.addWidget(QLabel(self.tr("Team :")))
        filters_layout.addWidget(self.combo_team)
        filters_layout.addWidget(QLabel(self.tr("Site :")))
        filters_layout.addWidget(self.combo_site)
        filters_widget = QWidget()
        filters_widget.setLayout(filters_layout)
        filter_period_layout.addWidget(filters_widget)

        # Boutons à droite dans le même bloc
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        self.btn_export = QPushButton(self.tr("Export")); self.btn_export.setMinimumWidth(90)
        self.btn_reset = QPushButton(self.tr("Reset")); self.btn_reset.setMinimumWidth(90)
        self.btn_close = QPushButton(self.tr("Close")); self.btn_close.setMinimumWidth(90)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addWidget(self.btn_reset)
        actions_layout.addWidget(self.btn_close)
        actions_widget = QWidget()
        actions_widget.setLayout(actions_layout)
        filter_period_layout.addWidget(actions_widget)

        filter_period_box.setLayout(filter_period_layout)
        filter_period_box.setFixedHeight(90)
        main_layout.insertWidget(0, filter_period_box)

        # Forcer l'ancrage top du layout principal
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        main_layout.setAlignment(Qt.AlignTop)

        
        # Connexions boutons
        self.btn_close.clicked.connect(self.close)
        self.btn_reset.clicked.connect(self.reset_and_reload)

        # Connexions filtres/période → MAJ tableau automatique
        self.date_start.dateChanged.connect(self.fill_table_overview)
        self.date_end.dateChanged.connect(self.fill_table_overview)
        self.combo_machine.currentIndexChanged.connect(self.fill_table_overview)
        self.combo_type.currentIndexChanged.connect(self.fill_table_overview)
        self.combo_team.currentIndexChanged.connect(self.fill_table_overview)
        self.combo_site.currentIndexChanged.connect(self.fill_table_overview)

        # --- Onglets ---
        self.tabs = QTabWidget()
        
        # === OVERVIEW ===
        self.tab_overview = QWidget()
        overview_layout = QVBoxLayout()

        # --- Statistiques/totaux (avant le tableau) ---
        stats_layout = QHBoxLayout()
        self.stats_labels = {}
        stats_items = [
            ("total_machines", self.tr("Total machines")),
            ("total_cost", self.tr("Total cost")),
            ("avg_cost", self.tr("Average cost")),
            ("total_interventions", self.tr("Interventions")),
            ("preventive_ratio", self.tr("% preventive")),
            ("efficiency", self.tr("Efficiency"))
        ]
        for key, label in stats_items:
            lbl = QLabel(f"{label} : --")
            lbl.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px;")
            self.stats_labels[key] = lbl
            stats_layout.addWidget(lbl)
        stats_layout.addStretch()
        overview_layout.addLayout(stats_layout)

        # --- Tableau principal (affichage moderne, toujours visible) ---
        from PySide6.QtWidgets import QSizePolicy
        headers = [
            self.tr("Machine"), self.tr("Type"), self.tr("Status"), self.tr("Total cost"), self.tr("Interventions"), self.tr("Preventive"), self.tr("Corrective"), self.tr("Urgency"),
            self.tr("Total time"), self.tr("Average cost"), self.tr("Average time"), self.tr("Last maintenance"), self.tr("Criticality"), self.tr("Preventive/Corrective ratio")
        ]
        self.data_table = QTableWidget(0, len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        self.data_table.setRowCount(0)
        self.data_table.setMinimumHeight(200)
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.insertWidget(1, self.data_table)

        self.tab_overview.setLayout(overview_layout)
        self.tabs.addTab(self.tab_overview, self.tr("Overview"))
        
        # Ajouter les onglets au layout principal
        main_layout.addWidget(self.tabs)

        # --- Remplissage initial des combos et du tableau (APRÈS création complète de l'UI) ---
        self.populate_all_combos()
        self.fill_table_overview()

    def fill_table_overview(self):
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
        headers = [
            "Machine", "Type", "Status", "Total cost", "Interventions", "Preventive", "Corrective", "Urgency",
            "Total time", "Average cost", "Average time", "Criticality", "Preventive/Corrective ratio"
        ]
        # Mapping colonnes DataFrame -> headers UI
        col_map = {
            "Machine": "machine_nom",
            "Type": "type_nom",
            "Status": "machine_criticite",
            "Total cost": "cout_total_jour",
            "Interventions": "nb_interventions",
            "Preventive": "nb_preventif",
            "Corrective": "nb_correctif",
            "Urgency": "nb_urgence",
            "Total time": "duree_moyenne_h",
            "Average cost": "cout_moyen_intervention",
            "Average time": "duree_moyenne_h",
            "Criticality": "machine_criticite",
            "Preventive/Corrective ratio": "ratio_preventif_curatif"
        }
        self.data_table.setRowCount(0)
        if df.empty:
            return
        for i, row in df.iterrows():
            self.data_table.insertRow(i)
            for j, header in enumerate(headers):
                col = col_map[header]
                try:
                    value = row[col]
                except KeyError:
                    value = "--"
                # Pour Last maintenance, afficher '--' si la colonne n'existe pas
                if header == "Last maintenance":
                    value = row[col] if col in row else "--"
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.data_table.setItem(i, j, item)

    def populate_all_combos(self):
        try:
            # Machines
            self.combo_machine.blockSignals(True)
            self.combo_machine.clear()
            self.combo_machine.addItem(self.tr("All machines"), None)
            df_m = self.kpi_service.get_all_machines()
            for _, row in df_m.iterrows():
                self.combo_machine.addItem(str(row['nom']), row['id_machine'])
            self.combo_machine.blockSignals(False)
            # Types
            self.combo_type.blockSignals(True)
            self.combo_type.clear()
            self.combo_type.addItem(self.tr("All types"), None)
            df_t = self.kpi_service.get_all_types()
            for _, row in df_t.iterrows():
                self.combo_type.addItem(str(row['nom']), row['id_type_machine'])
            self.combo_type.blockSignals(False)
            # Teams
            self.combo_team.blockSignals(True)
            self.combo_team.clear()
            self.combo_team.addItem(self.tr("All teams"), None)
            df_e = self.kpi_service.get_all_teams()
            for _, row in df_e.iterrows():
                self.combo_team.addItem(str(row['nom']), row['id_equipe'])
            self.combo_team.blockSignals(False)
            # Sites
            self.combo_site.blockSignals(True)
            self.combo_site.clear()
            self.combo_site.addItem(self.tr("All sites"), None)
            df_s = self.kpi_service.get_all_sites()
            for _, row in df_s.iterrows():
                self.combo_site.addItem(str(row['nom']), row['id_site'])
            self.combo_site.blockSignals(False)
        except Exception as e:
            print(f"[KPI Dialog] Error loading combos: {e}")

        # Après remplissage, relancer l'affichage du tableau
        self.fill_table_overview()

    def reset_and_reload(self):
        self.populate_all_combos()
        self.combo_machine.setCurrentIndex(0)
        self.combo_type.setCurrentIndex(0)
        self.combo_team.setCurrentIndex(0)
        self.combo_site.setCurrentIndex(0)
        self.fill_table_overview()

# Pour test manuel :
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dlg = MachineKPIDialogNew()
    dlg.show()
    sys.exit(app.exec())
