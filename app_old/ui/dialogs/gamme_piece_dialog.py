# gmao_app/app/ui/dialogs/gamme_piece_dialog.py
""" Dialogue simple pour ajouter/modifier une Pièce Type à une Gamme. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any, List

from app.core.models.piece import Piece # Besoin modèle pièce
from app.core.services.stock_service import StockService # Besoin service stock

logger = logging.getLogger(__name__)

class GammePieceDialog(QDialog):
    """Dialogue pour sélectionner une pièce type et sa quantité."""

    def __init__(self,
                 stock_service: StockService,
                 current_piece_id: Optional[int] = None, # ID pièce si on modifie qté
                 current_quantite: int = 1,            # Quantité si on modifie
                 parent=None):
        super().__init__(parent)
        self.stock_service = stock_service
        self.is_edit_mode = current_piece_id is not None # Mode édition de quantité?
        self.selected_piece_info: Optional[Dict[str, Any]] = None # Pour stocker le résultat

        # Titre
        self.setWindowTitle(self.tr("Ajouter Pièce Type à la Gamme") if not self.is_edit_mode else self.tr("Modifier Quantité Pièce Type"))

        # Widgets
        self.piece_combo = QComboBox(self)
        self.piece_combo.setMinimumWidth(300)
        self.quantity_spin = QSpinBox(self)
        self.quantity_spin.setRange(1, 999) # Au moins 1
        self.quantity_spin.setValue(current_quantite if self.is_edit_mode else 1)

        # Charger les pièces disponibles
        self._populate_piece_combo()

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Pièce (*):"), self.piece_combo)
        form_layout.addRow(self.tr("Quantité Théorique (*):"), self.quantity_spin)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Pré-sélection si mode édition de quantité (trouver pièce par ID)
        if self.is_edit_mode and current_piece_id is not None:
             self.piece_combo.setEnabled(False) # Ne pas changer la pièce, juste la quantité
             self._select_combo_item_by_data(self.piece_combo, current_piece_id)

    def _populate_piece_combo(self):
        self.piece_combo.clear()
        self.piece_combo.addItem("", userData=None) # Item vide
        try:
            # Récupérer toutes les pièces (actives?) pour sélection
            pieces = self.stock_service.get_all_pieces(sort_by="nom") # Pourrait être filtré sur statut Actif
            for p in pieces:
                 # Afficher Réf + Nom
                 display_text = f"{p.reference} - {p.nom}"
                 self.piece_combo.addItem(display_text, userData=p.id_piece)
        except Exception as e:
             logger.error(f"Erreur chargement pièces pour GammePieceDialog: {e}")
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible charger liste pièces."))
             self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)


    def _select_combo_item_by_data(self, combo: QComboBox, target_id: Optional[int]):
         if target_id is None: combo.setCurrentIndex(0); return
         for index in range(combo.count()):
             if combo.itemData(index) == target_id: combo.setCurrentIndex(index); return
         logger.warning(f"ID pièce {target_id} non trouvé pour présélection.")
         combo.setCurrentIndex(0) # Ou lever erreur?

    def _validate_input(self) -> bool:
        if self.piece_combo.currentData() is None:
             QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner une pièce."))
             return False
        if self.quantity_spin.value() <= 0:
             QMessageBox.warning(self, self.tr("Quantité Invalide"), self.tr("La quantité doit être au moins 1."))
             return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input():
             # Stocker les données sélectionnées
             selected_id = self.piece_combo.currentData()
             selected_text = self.piece_combo.currentText()
             # Extraire réf et nom du texte (simple split)
             parts = selected_text.split(" - ", 1)
             ref = parts[0] if len(parts) > 0 else "N/A"
             nom = parts[1] if len(parts) > 1 else selected_text

             self.selected_piece_info = {
                 "piece_id": selected_id,
                 "piece_ref": ref,
                 "piece_nom": nom,
                 "quantite": self.quantity_spin.value(),
                 # Pas de lot pour pièce type
             }
             logger.debug(f"Pièce type sélectionnée/validée: {self.selected_piece_info}")
             super().accept()


    def get_piece_data(self) -> Optional[Dict[str, Any]]:
        """ Retourne les infos de la pièce sélectionnée et sa quantité. """
        # Les données sont stockées dans self.selected_piece_info lors de accept()
        return self.selected_piece_info