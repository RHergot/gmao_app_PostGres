from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel
from PySide6.QtCore import Qt
from datetime import datetime

class HistoriqueCompteurView(QDialog):
    """
    Dialog pour visualiser l'historique des relevés d'un compteur.
    """
    def __init__(self, compteur, historiques, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr(f"Historique des relevés - {compteur.nom}"))
        self.compteur = compteur
        self.historiques = historiques
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr(f"Compteur : {self.compteur.nom} ({self.compteur.unite})")))
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            self.tr("Date relevé"),
            self.tr("Valeur"),
            self.tr("Utilisateur")
        ])
        self.table.setRowCount(len(self.historiques))
        for i, hist in enumerate(self.historiques):
            date_str = hist.date_releve.strftime("%d/%m/%Y %H:%M") if isinstance(hist.date_releve, datetime) else str(hist.date_releve)
            self.table.setItem(i, 0, QTableWidgetItem(date_str))
            self.table.setItem(i, 1, QTableWidgetItem(str(hist.valeur)))
            utilisateur = getattr(hist, 'utilisateur_id', None)
            self.table.setItem(i, 2, QTableWidgetItem(str(utilisateur) if utilisateur else "-"))
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        self.close_btn = QPushButton(self.tr("Fermer"), self)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn)
