# gmao_app/app/ui/dialogs/stock_adjustment_dialog.py
"""
Boîte de dialogue pour ajuster manuellement le stock d'une pièce.
"""
import logging
from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, 
    QLineEdit, QDialogButtonBox, QFormLayout, QMessageBox
)

from app.core.models.piece import Piece
from app.core.services.stock_service import StockService

logger = logging.getLogger(__name__)

class StockAdjustmentDialog(QDialog):
    """Dialogue pour saisir la quantité, le type et la raison d'un ajustement de stock."""

    # Définir les types de mouvement standard ici pour les utiliser comme valeurs internes
    TYPE_ENTREE = "ENTREE"
    TYPE_SORTIE = "SORTIE"

    def __init__(self, piece: Piece, stock_service: StockService, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Ajuster le stock - {nom} ({reference})").format(nom=piece.nom, reference=piece.reference))
        self.piece = piece
        self.stock_service = stock_service

        # --- Widgets ---        
        self.type_mouvement_combo = QComboBox()
        # Ajouter les items avec des données utilisateur pour stocker la valeur interne
        self.type_mouvement_combo.addItem(self.tr("ENTREE"), self.TYPE_ENTREE)
        self.type_mouvement_combo.addItem(self.tr("SORTIE"), self.TYPE_SORTIE)
        
        self.quantite_spinbox = QSpinBox()
        self.quantite_spinbox.setMinimum(1) # Doit ajuster au moins 1 unité
        self.quantite_spinbox.setMaximum(99999) # Limite arbitraire
        self.quantite_spinbox.setValue(1)
        
        self.raison_edit = QLineEdit()
        self.raison_edit.setPlaceholderText(self.tr("Ex: Inventaire initial, Correction, Mise au rebut..."))

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # --- Layout ---        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow(QLabel(self.tr("Pièce:")), QLabel(f"<b>{piece.nom}</b> ({piece.reference})<br>{self.tr('Stock Actuel:')} {piece.stock_actuel}"))
        form_layout.addRow(QLabel(self.tr("Type d'ajustement:")), self.type_mouvement_combo)
        form_layout.addRow(QLabel(self.tr("Quantité:")), self.quantite_spinbox)
        form_layout.addRow(QLabel(self.tr("Raison:")), self.raison_edit)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        # --- Connections ---        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_adjustment_details(self) -> Optional[Tuple[str, int, str]]:
        """Retourne le type, la quantité et la raison si les données sont valides."""
        logger.debug("--- get_adjustment_details: Début ---")
        # PAS BESOIN DE VERIFIER self.result() ici

        # Récupérer la donnée interne (valeur non traduite)
        type_mvt = self.type_mouvement_combo.currentData() 
        quantite = self.quantite_spinbox.value()
        raison = self.raison_edit.text().strip()
        logger.debug(f"Raison saisie: '{raison}' (longueur: {len(raison)}) - Type: {type_mvt} - Qte: {quantite}")

        if not raison:
            logger.debug("    Raison manquante, affichage warning.")
            QMessageBox.warning(self, self.tr("Raison manquante"), self.tr("Veuillez fournir une raison pour l'ajustement de stock."))
            logger.debug("    --- get_adjustment_details: Fin (Raison manquante -> None) ---")
            return None # Empêche la fermeture si la raison est vide

        logger.debug(f"--- get_adjustment_details: Fin (Valide -> ({type_mvt}, {quantite}, '{raison}')) ---")
        return type_mvt, quantite, raison
        # PAS DE 'return None' ici à la fin

    # Override accept pour inclure la validation
    def accept(self): 
        logger.debug("--- accept: Début (Bouton OK cliqué) ---") # Log ajouté précédemment
        details = self.get_adjustment_details()
        if details: # Seulement si les détails sont valides (raison fournie)
            type_mvt, quantite, raison = details
            try:
                # Appeler directement le service pour enregistrer le mouvement
                mvt = self.stock_service.enregistrer_mouvement(
                    piece_id=self.piece.id_piece,
                    type_mouvement=type_mvt,
                    quantite=quantite,
                    raison=raison,
                    # user_id=... # Pourrait être ajouté si l'utilisateur connecté est connu
                )
                if mvt:
                    QMessageBox.information(
    self,
    self.tr("Succès"),
    self.tr("Stock ajusté avec succès pour {nom}. Nouveau stock: {stock}").format(nom=self.piece.nom, stock=mvt.stock_apres)
)
                    super().accept() # Ferme le dialogue si succès
                else:
                    # L'erreur devrait avoir été loggée par le service
                    QMessageBox.critical(self, self.tr("Erreur"), "L'enregistrement du mouvement de stock a échoué. Vérifiez les logs.")
            except Exception as e:
                logger.error(f"Erreur lors de l'appel à enregistrer_mouvement: {e}", exc_info=True)
                QMessageBox.critical(
    self,
    self.tr("Erreur Critique"),
    self.tr("Une erreur inattendue est survenue: {error}").format(error=e)
)
            # Ne pas appeler super().accept() si les détails sont None (validation échouée)
