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
    QComboBox, QDateEdit, QWidget, QTableWidget, QTableWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt, QDate

class MachineKPIDialogNew(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KPI Machines (nouvelle version)")
        self.resize(1200, 700)
        main_layout = QVBoxLayout(self)

        # --- Cadre période ---
        period_box = QGroupBox("Période d'analyse")
        period_layout = QHBoxLayout()
        self.date_start = QDateEdit(QDate.currentDate())
        self.date_end = QDateEdit(QDate.currentDate())
        self.date_start.setCalendarPopup(True)
        self.date_end.setCalendarPopup(True)
        period_layout.addWidget(QLabel("Du : "))
        period_layout.addWidget(self.date_start)
        period_layout.addWidget(QLabel("au"))
        period_layout.addWidget(self.date_end)
        period_box.setLayout(period_layout)
        main_layout.addWidget(period_box)

        # --- Cadre filtres ---
        filters_box = QGroupBox("Filtres")
        filters_layout = QHBoxLayout()
        self.combo_machine = QComboBox()
        self.combo_type = QComboBox()
        self.combo_team = QComboBox()
        self.combo_site = QComboBox()
        self.combo_machine.addItem("Toutes les machines")
        self.combo_type.addItem("Tous les types")
        self.combo_team.addItem("Toutes les équipes")
        self.combo_site.addItem("Tous les sites")
        filters_layout.addWidget(QLabel("Machine :"))
        filters_layout.addWidget(self.combo_machine)
        filters_layout.addWidget(QLabel("Type :"))
        filters_layout.addWidget(self.combo_type)
        filters_layout.addWidget(QLabel("Équipe :"))
        filters_layout.addWidget(self.combo_team)
        filters_layout.addWidget(QLabel("Site :"))
        filters_layout.addWidget(self.combo_site)
        filters_box.setLayout(filters_layout)
        main_layout.addWidget(filters_box)

        # --- Actions globales ---
        actions_layout = QHBoxLayout()
        self.btn_export = QPushButton("Exporter")
        self.btn_reset = QPushButton("Réinitialiser")
        self.btn_close = QPushButton("Fermer")
        actions_layout.addWidget(self.btn_export)
        actions_layout.addWidget(self.btn_reset)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_close)
        main_layout.addLayout(actions_layout)

        # --- Onglets ---
        self.tabs = QTabWidget()
        # Overview Tab
        self.tab_overview = QWidget()
        overview_layout = QVBoxLayout()
        self.table = QTableWidget(0, 8)  # 8 colonnes par défaut (à ajuster)
        self.table.setHorizontalHeaderLabels([
            "Machine", "Type", "Équipe", "Site", "Coût total", "Nb interventions", "Préventif", "Correctif"
        ])
        overview_layout.addWidget(self.table)
        self.tab_overview.setLayout(overview_layout)
        self.tabs.addTab(self.tab_overview, "Overview")
        # Chart Tab
        self.tab_chart = QWidget()
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(QLabel("[Zone graphique : Bar/Lines]") )
        self.tab_chart.setLayout(chart_layout)
        self.tabs.addTab(self.tab_chart, "Graphiques")
        main_layout.addWidget(self.tabs)

        # Connexions (à compléter plus tard)
        self.btn_close.clicked.connect(self.close)
        # TODO: ajouter validation période, reset, export, filtrage, etc.

# Pour test manuel :
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    dlg = MachineKPIDialogNew()
    dlg.show()
    sys.exit(app.exec())
