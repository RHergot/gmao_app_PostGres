import logging
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDialogButtonBox, QLabel, QMessageBox
)
from app.core.models.compteur import Compteur

logger = logging.getLogger(__name__)

class CompteurDialog(QDialog):
    """Dialogue pour créer ou éditer un Compteur."""

    def __init__(self, compteur_service, machine_id: int, compteur: Optional[Compteur] = None, parent=None):
        super().__init__(parent)
        self.compteur_service = compteur_service
        self.machine_id = machine_id
        self.compteur_original = compteur
        self.is_edit_mode = compteur is not None

        self.setWindowTitle(self.tr("Ajouter Compteur") if not self.is_edit_mode else self.tr("Modifier Compteur"))
        self.setMinimumWidth(400)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.nom_input.setPlaceholderText(self.tr("Nom du compteur (ex: Horamètre)"))
        self.unite_input = QLineEdit(self)
        self.unite_input.setPlaceholderText(self.tr("Unité (ex: h, km, cycles)"))
        self.seuil_alerte_spin = QSpinBox(self)
        self.seuil_alerte_spin.setMinimum(0)
        self.seuil_alerte_spin.setMaximum(999999)
        self.seuil_alerte_spin.setValue(0)
        self.seuil_prev_spin = QSpinBox(self)
        self.seuil_prev_spin.setMinimum(0)
        self.seuil_prev_spin.setMaximum(999999)
        self.seuil_prev_spin.setValue(0)

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Nom (*):"), self.nom_input)
        form_layout.addRow(self.tr("Unité (*):"), self.unite_input)
        form_layout.addRow(self.tr("Seuil alerte:"), self.seuil_alerte_spin)
        form_layout.addRow(self.tr("Seuil préventif OT:"), self.seuil_prev_spin)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir si édition
        if self.is_edit_mode and self.compteur_original:
            self._populate_fields()

        logger.debug(f"CompteurDialog initialisé en mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _populate_fields(self):
        self.nom_input.setText(self.compteur_original.nom)
        self.unite_input.setText(self.compteur_original.unite)
        self.seuil_alerte_spin.setValue(self.compteur_original.seuil_alerte or 0)
        self.seuil_prev_spin.setValue(self.compteur_original.seuil_prev_ot or 0)

    def get_data(self):
        """Retourne les données saisies sous forme de dict."""
        data = {
            "nom": self.nom_input.text().strip(),
            "unite": self.unite_input.text().strip(),
            "seuil_alerte": self.seuil_alerte_spin.value(),
            "seuil_preventif_ot": self.seuil_prev_spin.value(),
        }
        return data

    def accept(self):
        # Validation simple
        if not self.nom_input.text().strip() or not self.unite_input.text().strip():
            QMessageBox.warning(self, self.tr("Champs obligatoires"), self.tr("Veuillez renseigner le nom et l'unité du compteur."))
            return
        super().accept()
