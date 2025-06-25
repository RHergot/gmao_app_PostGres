# gmao_app/app/ui/dialogs/gamme_etape_dialog.py
""" Dialogue simple pour ajouter/modifier une Étape de Gamme. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QTextEdit, QDialogButtonBox, QMessageBox,
    QSpinBox, QLabel # S'assurer que tous les widgets utilisés sont importés
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any
# Importer le modèle GammeEtape si on veut utiliser le type hint dans __init__
# Mais ce n'est pas strictement nécessaire pour le fonctionnement ici.
# from app.core.models.gamme_etape import GammeEtape

logger = logging.getLogger(__name__)

class GammeEtapeDialog(QDialog):
    """Dialogue pour éditer les détails d'une étape de gamme."""

    # On passe un dict ou None pour l'étape existante pour simplifier l'appel
    def __init__(self, etape_data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self.etape_data_original = etape_data # Pour pré-remplissage
        self.is_edit_mode = etape_data is not None
        ordre_display = etape_data.get('ordre', self.tr('Nouvelle')) if etape_data else self.tr('Nouvelle')

        self.setWindowTitle(self.tr("Ajouter Étape") if not self.is_edit_mode else self.tr("Modifier Étape {ordre}").format(ordre=ordre_display))
        self.setMinimumWidth(450)

        # Widgets
        self.description_edit = QTextEdit(self)
        self.description_edit.setPlaceholderText(self.tr("Description de la tâche à effectuer pour cette étape..."))
        self.description_edit.setMinimumHeight(60)
        self.instructions_edit = QTextEdit(self)
        self.instructions_edit.setPlaceholderText(self.tr("Instructions plus détaillées, points de contrôle, outils (optionnel)..."))
        self.instructions_edit.setMinimumHeight(80)
        self.duree_spinbox = QSpinBox(self)
        self.duree_spinbox.setSuffix(self.tr(" min"))
        self.duree_spinbox.setRange(0, 999) # Max ~16h
        self.duree_spinbox.setSpecialValueText(self.tr("Non estimée")) # Texte si valeur = 0

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Description Tâche (*):"), self.description_edit)
        form_layout.addRow(self.tr("Instructions Détaillées:"), self.instructions_edit)
        form_layout.addRow(self.tr("Durée Estimée:"), self.duree_spinbox)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-remplir si édition
        if self.is_edit_mode and self.etape_data_original:
            self._populate_fields()

        logger.debug(self.tr(f"GammeEtapeDialog initialisé mode {'Édition' if self.is_edit_mode else 'Création'}"))

    def _populate_fields(self):
        e = self.etape_data_original
        self.description_edit.setText(e.get('description', ""))
        self.instructions_edit.setText(e.get('instructions_detaillees', ""))
        duree = e.get('duree_estimee_min')
        if duree is not None:
            self.duree_spinbox.setValue(duree)
        else:
            self.duree_spinbox.setValue(self.duree_spinbox.minimum())

    def _validate_input(self) -> bool:
        if not self.description_edit.toPlainText().strip():
             QMessageBox.warning(self, self.tr("Champ Manquant"), self.tr("La description de l'étape est obligatoire."))
             self.description_edit.setFocus(); return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input(): super().accept()

    def get_etape_data(self) -> Dict[str, Any]:
        """ Récupère les données modifiées ou nouvelles pour l'étape. """
        duree_val = self.duree_spinbox.value()
        # Retourner None pour la durée si c'est la valeur spéciale (0)
        duree = duree_val if duree_val > self.duree_spinbox.minimum() else None
        data = {
            "description": self.description_edit.toPlainText().strip(),
            "instructions_detaillees": self.instructions_edit.toPlainText().strip() or None,
            "duree_estimee_min": duree,
            # L'ordre est géré par GammeDialog, l'ID par le service/repo
        }
        return data