# gmao_app/app/ui/dialogs/equipe_dialog.py
""" Dialogue pour ajouter/modifier une Equipe. """
import logging
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Slot, QTranslator, QLocale
from typing import Optional, Dict, Any, List

# Importer modèles et service (pour liste responsables potentiels)
from app.core.models.equipe import Equipe
from app.core.models.technicien import Technicien
from app.core.services.maintenance_service import MaintenanceService

logger = logging.getLogger(__name__)

class EquipeDialog(QDialog):
    """Dialogue pour créer ou éditer une Equipe."""

    def __init__(self,
                 maintenance_service: MaintenanceService,
                 equipe: Optional[Equipe] = None,
                 parent=None                
                 ):
                 
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.equipe_original = equipe
        self.is_edit_mode = equipe is not None


        self.setWindowTitle(self.tr("Ajouter Équipe") if not self.is_edit_mode else self.tr("Modifier Équipe"))
        self.setMinimumWidth(350)

        # Widgets
        self.nom_input = QLineEdit(self)
        self.domaine_input = QLineEdit(self)
        self.responsable_combo = QComboBox(self)

        # Charger les techniciens pour la liste des responsables
        self._populate_responsable_combo()

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Nom (*) :"), self.nom_input)
        form_layout.addRow(self.tr("Domaine Expertise :"), self.domaine_input)
        form_layout.addRow(self.tr("Responsable :"), self.responsable_combo)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir
        if self.is_edit_mode and self.equipe_original:
            self._populate_fields()

        logger.debug(self.tr("EquipeDialog initialisé en mode {}").format("Édition" if self.is_edit_mode else "Création"))

    def _populate_responsable_combo(self):
        """ Charge la liste des techniciens actifs pour le choix du responsable. """
        self.responsable_combo.clear()
        self.responsable_combo.addItem(self.tr("Aucun"), userData=None) # Permettre de ne pas avoir de responsable
        try:
            techniciens = self.maintenance_service.get_all_techniciens(include_inactive=False)
            for tech in techniciens:
                self.responsable_combo.addItem(tech.nom_complet, userData=tech.id_technicien)
        except BusinessLogicError as e:
            logger.error(self.tr("Erreur chargement techniciens pour responsable: {}").format(e))
            # Afficher erreur ou juste laisser la liste vide?
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger la liste des techniciens."))


    def _populate_fields(self):
        e = self.equipe_original
        self.nom_input.setText(e.nom or "")
        self.nom_input.setPlaceholderText(self.tr("Nom de l'équipe"))
        self.domaine_input.setText(e.domaine_expertise or "")
        # Sélectionner le responsable
        resp_id = e.responsable_id
        index = self.responsable_combo.findData(resp_id)
        if index != -1:
            self.responsable_combo.setCurrentIndex(index)
        else:
            self.responsable_combo.setCurrentIndex(0) # Aucun


    def _validate_input(self) -> bool:
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("'Nom' obligatoire."))
            self.nom_input.setFocus(); return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input(): super().accept()

    def get_equipe_data(self) -> Dict[str, Any]:
        data = {
            "nom": self.nom_input.text().strip(),
            "domaine_expertise": self.domaine_input.text().strip() or None,
            "responsable_id": self.responsable_combo.currentData(), # Peut être None
        }
        if self.is_edit_mode and self.equipe_original:
             data["id_equipe"] = self.equipe_original.id_equipe
        return data