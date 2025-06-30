# gmao_app/app/ui/dialogs/technicien_dialog.py
""" Dialogue pour ajouter/modifier un Technicien. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox,
    QComboBox, QCheckBox, QDoubleSpinBox # Utiliser QDoubleSpinBox pour le coût horaire
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any, List

from app.core.models.technicien import Technicien
from app.core.models.equipe import Equipe
from app.core.services.maintenance_service import MaintenanceService

logger = logging.getLogger(__name__)

class TechnicienDialog(QDialog):
    """Dialogue pour créer ou éditer un Technicien."""

    def __init__(self,
                 maintenance_service: MaintenanceService,
                 technicien: Optional[Technicien] = None,
                 parent=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.tech_original = technicien
        self.is_edit_mode = technicien is not None

        self.setWindowTitle(self.tr("Add Technician") if not self.is_edit_mode else self.tr("Edit Technician"))
        self.setMinimumWidth(400)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.prenom_input = QLineEdit(self)
        self.qualification_input = QLineEdit(self)
        self.contact_input = QLineEdit(self)
        self.cout_horaire_spinbox = QDoubleSpinBox(self)
        self.cout_horaire_spinbox.setSuffix(self.tr(" €/h")) # Or other currency
        self.cout_horaire_spinbox.setRange(0.0, 999.99)
        self.cout_horaire_spinbox.setDecimals(2)
        self.equipe_combo = QComboBox(self)
        self.actif_checkbox = QCheckBox(self.tr("Active Technician"), self)
        self.actif_checkbox.setChecked(True)

        # Charger les équipes
        self._populate_equipe_combo()

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Last Name (*):"), self.nom_input)
        form_layout.addRow(self.tr("First Name:"), self.prenom_input)
        form_layout.addRow(self.tr("Qualification:"), self.qualification_input)
        form_layout.addRow(self.tr("Contact (Phone/Email):"), self.contact_input)
        form_layout.addRow(self.tr("Hourly Rate:"), self.cout_horaire_spinbox)
        form_layout.addRow(self.tr("Team:"), self.equipe_combo)
        form_layout.addRow(self.actif_checkbox)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir
        if self.is_edit_mode and self.tech_original:
            self._populate_fields()

        logger.debug(f"TechnicienDialog initialisé mode {'Édition' if self.is_edit_mode else 'Création'}")


    def _populate_equipe_combo(self):
        self.equipe_combo.clear()
        self.equipe_combo.addItem(self.tr("None"), userData=None)
        try:
            equipes = self.maintenance_service.get_all_equipes()
            for eq in equipes:
                self.equipe_combo.addItem(eq.nom, userData=eq.id_equipe)
        except BusinessLogicError as e:
            logger.error(f"Erreur chargement equipes: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Unable to load the list of teams."))

    def _populate_fields(self):
        t = self.tech_original
        self.nom_input.setText(t.nom or "")
        self.prenom_input.setText(t.prenom or "")
        self.qualification_input.setText(t.qualification or "")
        self.contact_input.setText(t.contact or "")
        self.cout_horaire_spinbox.setValue(t.cout_horaire or 0.0)
        self.actif_checkbox.setChecked(t.actif)
        # Sélectionner équipe
        eq_id = t.equipe_id
        index = self.equipe_combo.findData(eq_id)
        self.equipe_combo.setCurrentIndex(index if index != -1 else 0) # 'Aucune' si non trouvé ou Null


    def _validate_input(self) -> bool:
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, self.tr("Missing Field"), self.tr("'Last Name' is required."))
            self.nom_input.setFocus(); return False
        # Autres validations si nécessaire
        return True

    @Slot()
    def accept(self):
        if self._validate_input(): super().accept()

    def get_technicien_data(self) -> Dict[str, Any]:
        data = {
            "nom": self.nom_input.text().strip(),
            "prenom": self.prenom_input.text().strip() or None,
            "qualification": self.qualification_input.text().strip() or None,
            "contact": self.contact_input.text().strip() or None,
            "cout_horaire": self.cout_horaire_spinbox.value(),
            "equipe_id": self.equipe_combo.currentData(), # Peut être None
            "actif": self.actif_checkbox.isChecked(),
        }
        if self.is_edit_mode and self.tech_original:
             data["id_technicien"] = self.tech_original.id_technicien
        return data