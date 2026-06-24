# gmao_app/app/ui/dialogs/type_machine_dialog.py
""" Dialogue pour ajouter/modifier un Type de Machine. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any
from app.core.models.type_machine import TypeMachine

logger = logging.getLogger(__name__)

class TypeMachineDialog(QDialog):
    """Dialogue pour créer ou éditer un TypeMachine."""

    def __init__(self, type_machine: Optional[TypeMachine] = None, parent=None):
        super().__init__(parent)
        self.tm_original = type_machine
        self.is_edit_mode = type_machine is not None

        self.setWindowTitle(self.tr("Ajouter Type Machine") if not self.is_edit_mode else self.tr("Modifier Type Machine"))
        self.setMinimumWidth(350)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.description_input = QLineEdit(self)
        self.categorie_combo = QComboBox(self) # Ou QLineEdit si libre
        # Ajouter des catégories prédéfinies (pourrait venir d'une config/nomenclature)
        categories = [
            "",
            self.tr("Mécanique"),
            self.tr("Électrique"),
            self.tr("Hydraulique"),
            self.tr("Pneumatique"),
            self.tr("Automatisme"),
            self.tr("Bâtiment"),
            self.tr("Autre")
        ]
        self.categorie_combo.addItems(categories)
        self.categorie_combo.setEditable(True) # Permettre d'entrer une nouvelle catégorie

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Nom (*):"), self.nom_input)
        form_layout.addRow(self.tr("Description:"), self.description_input)
        form_layout.addRow(self.tr("Catégorie:"), self.categorie_combo)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir
        if self.is_edit_mode and self.tm_original:
            self._populate_fields()

        logger.debug(f"TypeMachineDialog initialisé en mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _populate_fields(self):
        tm = self.tm_original
        self.nom_input.setText(tm.nom or "")
        self.description_input.setText(tm.description or "")
        self.categorie_combo.setCurrentText(tm.categorie or "")

    def _validate_input(self) -> bool:
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("'Nom' obligatoire."))
            self.nom_input.setFocus()
            return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input():
            logger.debug("Validation TypeMachineDialog réussie.")
            super().accept()
        else:
            logger.warning("Validation TypeMachineDialog échouée.")

    def get_type_machine_data(self) -> Dict[str, Any]:
        """ Récupère les données pour le service. """
        data = {
            "nom": self.nom_input.text().strip(),
            "description": self.description_input.text().strip() or None,
            "categorie": self.categorie_combo.currentText().strip() or None,
        }
        if self.is_edit_mode and self.tm_original:
             data["id_type_machine"] = self.tm_original.id_type_machine
        logger.debug(self.tr("Données récupérées du TypeMachineDialog: {}").format(data))
        return data