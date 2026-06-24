# gmao_app/app/ui/dialogs/site_dialog.py
""" Dialogue pour ajouter/modifier un Site. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any
from app.core.models.site import Site # Importer le modèle

logger = logging.getLogger(__name__)

class SiteDialog(QDialog):
    """Dialogue pour créer ou éditer un Site."""

    def __init__(self, site: Optional[Site] = None, parent=None):
        super().__init__(parent)
        self.site_original = site
        self.is_edit_mode = site is not None

        self.setWindowTitle(self.tr("Ajouter un Site") if not self.is_edit_mode else self.tr("Modifier le Site"))
        self.setMinimumWidth(350)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.adresse_input = QLineEdit(self)
        self.ville_input = QLineEdit(self)
        self.pays_input = QLineEdit(self)
        self.contact_input = QLineEdit(self)

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Nom (*):"), self.nom_input)
        form_layout.addRow(self.tr("Adresse:"), self.adresse_input)
        form_layout.addRow(self.tr("Ville:"), self.ville_input)
        form_layout.addRow(self.tr("Pays:"), self.pays_input)
        form_layout.addRow(self.tr("Contact Principal:"), self.contact_input)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir si édition
        if self.is_edit_mode and self.site_original:
            self._populate_fields()

        logger.debug(self.tr(f"SiteDialog initialisé en mode {'Édition' if self.is_edit_mode else 'Création'}"))

    def _populate_fields(self):
        s = self.site_original
        self.nom_input.setText(s.nom or "")
        self.adresse_input.setText(s.adresse or "")
        self.ville_input.setText(s.ville or "")
        self.pays_input.setText(s.pays or "")
        self.contact_input.setText(s.contact_principal or "")

    def _validate_input(self) -> bool:
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le 'Nom' du site est obligatoire."))
            self.nom_input.setFocus()
            return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input():
            logger.debug(self.tr("Validation SiteDialog réussie."))
            super().accept()
        else:
            logger.warning(self.tr("Validation SiteDialog échouée."))

    def get_site_data(self) -> Dict[str, Any]:
        """ Récupère les données saisies pour le service. """
        data = {
            "nom": self.nom_input.text().strip(),
            "adresse": self.adresse_input.text().strip() or None,
            "ville": self.ville_input.text().strip() or None,
            "pays": self.pays_input.text().strip() or None,
            "contact_principal": self.contact_input.text().strip() or None,
        }
        # Ajouter ID si mode édition
        if self.is_edit_mode and self.site_original:
             data["id_site"] = self.site_original.id_site
        logger.debug(self.tr("Données récupérées du SiteDialog: {}").format(data))
        return data