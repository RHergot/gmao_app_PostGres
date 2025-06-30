# gmao_app/app/ui/dialogs/piece_dialog.py
""" Dialogue pour ajouter/modifier une Pièce détachée. """
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QGroupBox # Ajouts SpinBox, Double, Combo, GroupBox
)
from PySide6.QtCore import Slot, Qt
from typing import Optional, Dict, Any, List

# Importer modèles et service (pour liste fournisseurs)
from app.core.models.piece import Piece
from app.core.models.fournisseur import Fournisseur
from app.core.services.stock_service import StockService, VALID_PIECE_UNITES, VALID_PIECE_STATUS

logger = logging.getLogger(__name__)

class PieceDialog(QDialog):
    """Dialogue pour créer ou éditer une Pièce."""

    def __init__(self,
                 stock_service: StockService, # Reçoit le service Stock
                 piece: Optional[Piece] = None,
                 parent=None):
        super().__init__(parent)
        self.stock_service = stock_service
        self.piece_original = piece
        self.is_edit_mode = piece is not None

        self.setWindowTitle(self.tr("Ajouter Pièce Détachée") if not self.is_edit_mode else self.tr("Modifier Pièce Détachée"))
        self.setMinimumWidth(500)

        # Données ComboBox
        self._fournisseurs: List[Fournisseur] = []

        # Widgets
        # Groupe Identification
        self.reference_input = QLineEdit(self)
        self.nom_input = QLineEdit(self)
        self.categorie_input = QLineEdit(self) # Ou ComboBox éditable?
        self.statut_combo = QComboBox(self)
        self.statut_combo.addItems([self.tr(status) for status in VALID_PIECE_STATUS])
        self.statut_combo.setCurrentText(self.tr("Actif"))

        # Groupe Stock & Prix
        self.unite_combo = QComboBox(self)
        self.unite_combo.addItems(VALID_PIECE_UNITES)
        self.unite_combo.setEditable(True) # Permettre nouvelles unités
        self.prix_spinbox = QDoubleSpinBox(self)
        self.prix_spinbox.setSuffix(self.tr(" €")) # Adapter devise si besoin
        self.prix_spinbox.setRange(0.0, 99999.99)
        self.prix_spinbox.setDecimals(2)
        self.stock_actuel_spin = QSpinBox(self) # Lecture seule ici? Stock màj par mouvements
        self.stock_actuel_spin.setRange(-9999, 999999) # Permettre négatif? Mieux = 0
        self.stock_actuel_spin.setReadOnly(True) # Stock actuel non modifiable ici
        self.stock_actuel_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons) # Cacher boutons +/-
        self.stock_alerte_spin = QSpinBox(self)
        self.stock_alerte_spin.setRange(0, 99999)
        self.stock_reserve_spin = QSpinBox(self) # Lecture seule aussi?
        self.stock_reserve_spin.setRange(0, 99999)
        self.stock_reserve_spin.setReadOnly(True)
        self.stock_reserve_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.emplacement_input = QLineEdit(self)

        # Groupe Fournisseur
        self.fournisseur_combo = QComboBox(self)

        # Charger fournisseurs
        self._populate_fournisseur_combo()

        # Layouts
        main_layout = QVBoxLayout(self)

        group_id = QGroupBox(self.tr("Identification"))
        form1 = QFormLayout(group_id)
        form1.addRow(self.tr("Référence (*):"), self.reference_input)
        form1.addRow(self.tr("Nom/Description (*):"), self.nom_input)
        form1.addRow(self.tr("Catégorie:"), self.categorie_input)
        form1.addRow(self.tr("Statut:"), self.statut_combo)
        main_layout.addWidget(group_id)

        group_stock = QGroupBox(self.tr("Stock & Prix"))
        form2 = QFormLayout(group_stock)
        form2.addRow(self.tr("Unité (*):"), self.unite_combo)
        form2.addRow(self.tr("Prix Unitaire:"), self.prix_spinbox)
        form2.addRow(self.tr("Stock Actuel:"), self.stock_actuel_spin)
        form2.addRow(self.tr("Seuil Alerte:"), self.stock_alerte_spin)
        # form2.addRow(self.tr("Stock Réservé:"), self.stock_reserve_spin) # Moins utile à afficher/modifier ici?
        form2.addRow(self.tr("Emplacement Stockage:"), self.emplacement_input)
        main_layout.addWidget(group_stock)

        group_fours = QGroupBox(self.tr("Fournisseur Préférentiel"))
        form3 = QFormLayout(group_fours)
        form3.addRow(self.tr("Fournisseur:"), self.fournisseur_combo)
        main_layout.addWidget(group_fours)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        # Les boutons Ok/Cancel sont traduits automatiquement par Qt selon la langue du système/du .qm
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

        # Pré-remplir
        if self.is_edit_mode and self.piece_original:
            self._populate_fields()
            # Réf non modifiable? Souvent clé métier importante
            self.reference_input.setReadOnly(True)
            self.reference_input.setStyleSheet("background-color: #eee;")

        logger.debug(f"PieceDialog initialisé mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _populate_fournisseur_combo(self):
        self.fournisseur_combo.clear()
        self.fournisseur_combo.addItem(self.tr("Aucun"), userData=None)
        try:
            fournisseurs = self.stock_service.get_all_fournisseurs()
            self._fournisseurs = fournisseurs # Stocker
            for f in fournisseurs:
                 self.fournisseur_combo.addItem(f.nom, userData=f.id_fournisseur)
        except BusinessLogicError as e:
             logger.error(f"Erreur chargement fournisseurs pour PieceDialog: {e}")
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible charger liste fournisseurs."))

    def _populate_fields(self):
        p = self.piece_original
        self.reference_input.setText(p.reference or "")
        self.nom_input.setText(p.nom or "")
        self.categorie_input.setText(p.categorie or "")
        self.statut_combo.setCurrentText(p.statut or self.tr("Actif"))
        self.unite_combo.setCurrentText(p.unite or "") # Unité est obligatoire normalement
        self.prix_spinbox.setValue(p.prix_unitaire or 0.0)
        self.stock_actuel_spin.setValue(p.stock_actuel or 0)
        self.stock_alerte_spin.setValue(p.stock_alerte or 0)
        self.stock_reserve_spin.setValue(p.stock_reserve or 0)
        self.emplacement_input.setText(p.emplacement_stockage or "")
        # Sélectionner fournisseur
        f_id = p.fournisseur_pref_id
        index = self.fournisseur_combo.findData(f_id)
        self.fournisseur_combo.setCurrentIndex(index if index != -1 else 0) # Index 0 = Aucun


    def _select_combo_item_by_data(self, combo: QComboBox, target_id: Optional[int]):
         # Copié depuis OTDialog - pourrait être dans un utilitaire UI
         if target_id is None: combo.setCurrentIndex(0); return
         for index in range(combo.count()):
             if combo.itemData(index) == target_id: combo.setCurrentIndex(index); return
         logger.warning(f"ID {target_id} non trouvé dans {combo.objectName()}. Défaut.")
         combo.setCurrentIndex(0)

    def _validate_input(self) -> bool:
        if not self.reference_input.text().strip():
             QMessageBox.warning(self,self.tr("Champ manquant"),self.tr("'Référence' obligatoire.")); return False
        if not self.nom_input.text().strip():
             QMessageBox.warning(self,self.tr("Champ manquant"),self.tr("'Nom/Description' obligatoire.")); return False
        if not self.unite_combo.currentText().strip():
             QMessageBox.warning(self,self.tr("Champ manquant"),self.tr("'Unité' obligatoire.")); return False
        # Autres validations? Prix > 0 ? Alerte <= Stock Max (pas de max défini)?
        return True

    @Slot()
    def accept(self):
        if self._validate_input(): super().accept()

    def get_piece_data(self) -> Dict[str, Any]:
        """ Récupère les données pour le service. """
        data = {
            "reference": self.reference_input.text().strip(),
            "nom": self.nom_input.text().strip(),
            "categorie": self.categorie_input.text().strip() or None,
            "statut": self.statut_combo.currentText(),
            "unite": self.unite_combo.currentText().strip(),
            "prix_unitaire": self.prix_spinbox.value(),
            "stock_alerte": self.stock_alerte_spin.value(),
            "emplacement_stockage": self.emplacement_input.text().strip() or None,
            "fournisseur_pref_id": self.fournisseur_combo.currentData(), # Peut être None
            # Ne pas passer stock_actuel et stock_reserve car lecture seule
        }
        if self.is_edit_mode and self.piece_original:
             data["id_piece"] = self.piece_original.id_piece
        # else: # Valeurs par défaut pour création (déjà dans modèle)
        #     data["stock_actuel"] = 0
        #     data["stock_reserve"] = 0

        return data