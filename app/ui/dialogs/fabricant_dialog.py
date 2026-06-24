# gmao_app/app/ui/dialogs/fabricant_dialog.py
""" Dialogue pour ajouter/modifier un Fabricant. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QTextEdit
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any
from app.core.models.fabricant import Fabricant

logger = logging.getLogger(__name__)

class FabricantDialog(QDialog):
    """Dialogue pour créer ou éditer un Fabricant."""

    def __init__(self, fabricant: Optional[Fabricant] = None, parent=None):
        super().__init__(parent)
        self.fabricant_original = fabricant
        self.is_edit_mode = fabricant is not None

        self.setWindowTitle(self.tr("Ajouter Fabricant") if not self.is_edit_mode else self.tr("Modifier Fabricant"))
        self.setMinimumWidth(400)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.nom_input.setPlaceholderText(self.tr("Nom du fabricant"))
        self.contact_input = QLineEdit(self)
        self.contact_input.setPlaceholderText(self.tr("Contact"))
        self.site_web_input = QLineEdit(self)
        self.site_web_input.setPlaceholderText(self.tr("Site Web"))
        self.support_input = QTextEdit(self) # Peut être multi-lignes
        self.support_input.setPlaceholderText(self.tr("Support Technique"))
        self.support_input.setMaximumHeight(80)

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Nom (*):"), self.nom_input)
        form_layout.addRow(self.tr("Contact:"), self.contact_input)
        form_layout.addRow(self.tr("Site Web:"), self.site_web_input)
        form_layout.addRow(self.tr("Support Technique:"), self.support_input)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir
        if self.is_edit_mode and self.fabricant_original:
            self._populate_fields()

        logger.debug(self.tr("FabricantDialog initialisé en mode {}").format("Édition" if self.is_edit_mode else "Création"))

    def _populate_fields(self):
        f = self.fabricant_original
        self.nom_input.setText(f.nom or "")
        self.contact_input.setText(f.contact or "")
        self.site_web_input.setText(f.site_web or "")
        self.support_input.setText(f.support_technique or "")

    def _validate_input(self) -> bool:
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, self.tr("Champs obligatoires"), self.tr("Veuillez renseigner le nom du fabricant."))
            self.nom_input.setFocus()
            return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input():
            logger.debug("Validation FabricantDialog réussie.")
            super().accept()
        else:
            logger.warning("Validation FabricantDialog échouée.")

    def get_fabricant_data(self) -> Dict[str, Any]:
        """ Récupère les données pour le service. """
        data = {
            "nom": self.nom_input.text().strip(),
            "contact": self.contact_input.text().strip() or None,
            "site_web": self.site_web_input.text().strip() or None,
            "support_technique": self.support_input.toPlainText().strip() or None,
        }
        if self.is_edit_mode and self.fabricant_original:
             data["id_fabricant"] = self.fabricant_original.id_fabricant
        logger.debug(f"Données récupérées du FabricantDialog: {data}")
        return data