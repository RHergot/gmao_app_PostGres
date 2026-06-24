# gmao_app/app/ui/dialogs/fournisseur_dialog.py
""" Dialogue pour ajouter/modifier un Fournisseur. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox,
    QSpinBox, QComboBox, QDoubleSpinBox # Ajout SpinBox, ComboBox, DoubleSpinBox
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any
from app.core.models.fournisseur import Fournisseur

logger = logging.getLogger(__name__)

# TODO: Mettre les devises dans une config?
VALID_DEVISES = ["EUR", "USD", "GBP", "CHF", "CAD"]

class FournisseurDialog(QDialog):
    """Dialogue pour créer ou éditer un Fournisseur."""

    def __init__(self, fournisseur: Optional[Fournisseur] = None, parent=None):
        super().__init__(parent)
        self.fours_original = fournisseur
        self.is_edit_mode = fournisseur is not None

        self.setWindowTitle(self.tr("Ajouter Fournisseur") if not self.is_edit_mode else self.tr("Modifier Fournisseur"))
        self.setMinimumWidth(450)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.contact_input = QLineEdit(self)
        self.adresse_input = QLineEdit(self)
        self.telephone_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.delai_livraison_spinbox = QSpinBox(self) # Pour délai en jours
        self.delai_livraison_spinbox.setSuffix(self.tr(" jours"))
        self.delai_livraison_spinbox.setRange(0, 365)
        self.delai_livraison_spinbox.setSpecialValueText(self.tr("Non défini"))
        self.devise_combo = QComboBox(self)
        self.devise_combo.addItems(VALID_DEVISES)
        self.note_qualite_spinbox = QDoubleSpinBox(self) # Pour note
        self.note_qualite_spinbox.setRange(0.0, 5.0) # Note sur 5
        self.note_qualite_spinbox.setDecimals(1)
        self.note_qualite_spinbox.setSpecialValueText(self.tr("Non noté"))

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Nom (*):"), self.nom_input)
        form_layout.addRow(self.tr("Contact:"), self.contact_input)
        form_layout.addRow(self.tr("Adresse:"), self.adresse_input)
        form_layout.addRow(self.tr("Téléphone:"), self.telephone_input)
        form_layout.addRow(self.tr("Email:"), self.email_input)
        form_layout.addRow(self.tr("Délai Livraison Moyen:"), self.delai_livraison_spinbox)
        form_layout.addRow(self.tr("Devise:"), self.devise_combo)
        form_layout.addRow(self.tr("Note Qualité (../5):"), self.note_qualite_spinbox)


        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir
        if self.is_edit_mode and self.fours_original:
            self._populate_fields()

        logger.debug(f"FournisseurDialog initialisé mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _populate_fields(self):
        f = self.fours_original
        self.nom_input.setText(f.nom or "")
        self.contact_input.setText(f.contact or "")
        self.adresse_input.setText(f.adresse or "")
        self.telephone_input.setText(f.telephone or "")
        self.email_input.setText(f.email or "")
        self.devise_combo.setCurrentText(f.devise or "EUR")

        # Gérer valeurs spéciales pour SpinBox
        if f.delai_livraison_moyen_j is not None:
             self.delai_livraison_spinbox.setValue(f.delai_livraison_moyen_j)
        else:
             self.delai_livraison_spinbox.setValue(self.delai_livraison_spinbox.minimum()) # Affiche texte spécial

        if f.note_qualite is not None:
             self.note_qualite_spinbox.setValue(f.note_qualite)
        else:
             self.note_qualite_spinbox.setValue(self.note_qualite_spinbox.minimum()) # Affiche texte spécial


    def _validate_input(self) -> bool:
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("'Nom' obligatoire."))
            self.nom_input.setFocus(); return False
        # TODO: Valider format email? Téléphone?
        return True

    @Slot()
    def accept(self):
        if self._validate_input(): super().accept()

    def get_fournisseur_data(self) -> Dict[str, Any]:
        """ Récupère les données pour le service. """
        delai = self.delai_livraison_spinbox.value()
        delai_final = delai if delai > self.delai_livraison_spinbox.minimum() else None

        note = self.note_qualite_spinbox.value()
        note_final = note if note > self.note_qualite_spinbox.minimum() else None

        data = {
            "nom": self.nom_input.text().strip(),
            "contact": self.contact_input.text().strip() or None,
            "adresse": self.adresse_input.text().strip() or None,
            "telephone": self.telephone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "delai_livraison_moyen_j": delai_final,
            "devise": self.devise_combo.currentText(),
            "note_qualite": note_final,
        }
        if self.is_edit_mode and self.fours_original:
             data["id_fournisseur"] = self.fours_original.id_fournisseur
        return data