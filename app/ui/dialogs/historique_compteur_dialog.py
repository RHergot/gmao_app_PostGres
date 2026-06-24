from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDateTimeEdit, QDoubleSpinBox, QPushButton, QMessageBox
from PySide6.QtCore import QDateTime
from datetime import datetime

class HistoriqueCompteurDialog(QDialog):
    """
    Dialog pour saisir un nouveau relevé de compteur.
    """
    def __init__(self, compteur, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Enregistrer un relevé pour '{}'").format(compteur.nom))
        self.compteur = compteur
        self.valeur = None
        self.date_releve = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Date et heure du relevé
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel(self.tr("Date et heure du relevé :")))
        self.date_edit = QDateTimeEdit(self)
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # Valeur relevée
        valeur_layout = QHBoxLayout()
        valeur_layout.addWidget(QLabel(self.tr("Valeur relevée ({}) :").format(self.compteur.unite)))
        self.valeur_spin = QDoubleSpinBox(self)
        self.valeur_spin.setDecimals(2)
        self.valeur_spin.setRange(-1e9, 1e9)
        self.valeur_spin.setValue(self.compteur.valeur_actuelle or 0)
        valeur_layout.addWidget(self.valeur_spin)
        layout.addLayout(valeur_layout)

        # Boutons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton(self.tr("Enregistrer"), self)
        self.cancel_btn = QPushButton(self.tr("Annuler"), self)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_data(self):
        # Récupère les données saisies
        self.valeur = self.valeur_spin.value()
        self.date_releve = self.date_edit.dateTime().toPython()
        return {
            "valeur": self.valeur,
            "date_releve": self.date_releve
        }
