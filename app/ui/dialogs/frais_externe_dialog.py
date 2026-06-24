# gmao_app/app/ui/dialogs/frais_externe_dialog.py
"""
Dialogue pour ajouter ou modifier un frais externe dans une maintenance.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QDoubleSpinBox,
    QSpinBox, QGroupBox, QFormLayout, QTextEdit
)
from PySide6.QtCore import Qt

from app.core.models.maintenance_frais_externe import MaintenanceFraisExterne, VALID_TYPES_FRAIS

logger = logging.getLogger(__name__)

class FraisExterneDialog(QDialog):
    """Dialogue pour ajouter ou modifier un frais externe dans une maintenance."""
    
    def __init__(self, parent=None, frais=None, maintenance_id=None):
        """
        Initialise le dialogue de frais externe.
        
        Args:
            parent: Widget parent
            frais: Frais externe existant à modifier (None pour création)
            maintenance_id: ID de la maintenance associée (nécessaire pour la création)
        """
        super().__init__(parent)
        self.frais = frais
        self.maintenance_id = maintenance_id if maintenance_id is not None else (frais.maintenance_id if frais else None)
        self.is_edit_mode = frais is not None
        
        self._setup_ui()
        
        if self.is_edit_mode:
            self._populate_form_data()
        else:
            # Mode création, vérifier que l'ID de maintenance est fourni
            if not self.maintenance_id:
                logger.error("ID de maintenance non fourni pour création de frais externe")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("ID de maintenance manquant."))
                self.reject()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle(self.tr("Frais externe") if self.is_edit_mode else self.tr("Nouveau frais externe"))
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Formulaire principal
        form_layout = QFormLayout()
        
        # Type de frais
        self.cb_type = QComboBox()
        for type_frais in VALID_TYPES_FRAIS:
            self.cb_type.addItem(self._format_type_frais(type_frais), type_frais)
        form_layout.addRow(self.tr("Type de frais:"), self.cb_type)
        
        # Description
        self.txt_description = QTextEdit()
        self.txt_description.setMaximumHeight(80)
        form_layout.addRow(self.tr("Description:"), self.txt_description)
        
        # Montant unitaire
        self.sp_montant = QDoubleSpinBox()
        self.sp_montant.setMinimum(0)
        self.sp_montant.setMaximum(100000)
        self.sp_montant.setDecimals(2)
        self.sp_montant.setSingleStep(10)
        self.sp_montant.setValue(0)
        self.sp_montant.setSuffix(" €")
        form_layout.addRow(self.tr("Montant unitaire:"), self.sp_montant)
        
        # Quantité
        self.sp_quantite = QSpinBox()
        self.sp_quantite.setMinimum(1)
        self.sp_quantite.setMaximum(10000)
        self.sp_quantite.setValue(1)
        form_layout.addRow(self.tr("Quantité:"), self.sp_quantite)
        
        # Référence pièce (optionnel)
        self.txt_reference = QLineEdit()
        form_layout.addRow(self.tr("Référence pièce:"), self.txt_reference)
        
        # Fournisseur (optionnel)
        self.txt_fournisseur = QLineEdit()
        form_layout.addRow(self.tr("Fournisseur:"), self.txt_fournisseur)
        
        # Référence facture (optionnel)
        self.txt_facture = QLineEdit()
        form_layout.addRow(self.tr("Référence facture:"), self.txt_facture)
        
        # Montant total (non éditable)
        self.lbl_total = QLabel("0.00 €")
        form_layout.addRow(self.tr("Montant total:"), self.lbl_total)
        
        layout.addLayout(form_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton(self.tr("Annuler"))
        self.btn_ok = QPushButton(self.tr("Enregistrer"))
        self.btn_ok.setDefault(True)
        
        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_ok)
        layout.addLayout(buttons_layout)
        
        # Connexions
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)
        self.sp_montant.valueChanged.connect(self._update_total)
        self.sp_quantite.valueChanged.connect(self._update_total)
        self.cb_type.currentIndexChanged.connect(self._on_type_changed)
        
        # État initial
        self._update_total()
        self._on_type_changed()
    
    def _on_type_changed(self):
        """Gère le changement de type de frais."""
        # Permettre l'édition des champs spécifiques en fonction du type sélectionné
        current_type = self.cb_type.currentData()
        
        # Pour les pièces externes, activer les champs de référence/fournisseur
        is_piece = current_type == "PIECE_EXTERNE"
        self.txt_reference.setEnabled(is_piece)
        self.txt_fournisseur.setEnabled(True)  # Toujours actif mais plus pertinent pour les pièces
        
        # Suggestion de description selon le type
        if not self.is_edit_mode and not self.txt_description.toPlainText().strip():
            suggestions = {
                "PIECE_EXTERNE": self.tr("Pièce commandée auprès d'un fournisseur externe"),
                "DEPLACEMENT": self.tr("Frais de déplacement"),
                "SOUS_TRAITANCE": self.tr("Prestation de sous-traitance"),
                "AUTRE": self.tr("Frais divers")
            }
            if current_type in suggestions:
                self.txt_description.setPlainText(suggestions[current_type])
    
    def _update_total(self):
        """Met à jour le montant total en fonction du montant unitaire et de la quantité."""
        montant = self.sp_montant.value()
        quantite = self.sp_quantite.value()
        total = montant * quantite
        self.lbl_total.setText(self.tr("%1 €").replace("%1", f"{total:.2f}"))
    
    def _format_type_frais(self, type_frais):
        """Formate le type de frais pour l'affichage."""
        mapping = {
            "PIECE_EXTERNE": self.tr("Pièce externe"),
            "DEPLACEMENT": self.tr("Frais de déplacement"),
            "SOUS_TRAITANCE": self.tr("Sous-traitance"),
            "AUTRE": self.tr("Autre frais")
        }
        return mapping.get(type_frais, type_frais)
    
    def _populate_form_data(self):
        """Remplit le formulaire avec les données du frais existant."""
        if not self.frais:
            return
        
        # Type de frais
        index = self.cb_type.findData(self.frais.type_frais)
        if index >= 0:
            self.cb_type.setCurrentIndex(index)
        
        # Autres champs
        self.txt_description.setPlainText(self.frais.description)
        self.sp_montant.setValue(self.frais.montant)
        self.sp_quantite.setValue(self.frais.quantite)
        
        if self.frais.reference_piece:
            self.txt_reference.setText(self.frais.reference_piece)
        if self.frais.fournisseur:
            self.txt_fournisseur.setText(self.frais.fournisseur)
        if self.frais.facture_reference:
            self.txt_facture.setText(self.frais.facture_reference)
        
        # Mettre à jour l'interface selon le type
        self._on_type_changed()
        self._update_total()
    
    def get_form_data(self):
        """Récupère les données du formulaire."""
        data = {
            'maintenance_id': self.maintenance_id,
            'type_frais': self.cb_type.currentData(),
            'description': self.txt_description.toPlainText().strip(),
            'montant': self.sp_montant.value(),
            'quantite': self.sp_quantite.value(),
            'reference_piece': self.txt_reference.text().strip() or None,
            'fournisseur': self.txt_fournisseur.text().strip() or None,
            'facture_reference': self.txt_facture.text().strip() or None
        }
        
        if self.is_edit_mode:
            data['id_frais'] = self.frais.id_frais
        
        return data
    
    def validate_form(self):
        """Valide les données du formulaire."""
        if not self.cb_type.currentData():
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez sélectionner un type de frais."))
            return False
        
        if not self.txt_description.toPlainText().strip():
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez saisir une description."))
            return False
        
        if self.sp_montant.value() < 0:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le montant ne peut pas être négatif."))
            return False
        
        if self.sp_quantite.value() <= 0:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("La quantité doit être positive."))
            return False
        
        # Vérifications spécifiques au type
        current_type = self.cb_type.currentData()
        if current_type == "PIECE_EXTERNE" and not self.txt_reference.text().strip():
            # Avertissement mais pas bloquant
            if QMessageBox.question(
                self, self.tr("Validation"),
                self.tr("Aucune référence n'est spécifiée pour cette pièce externe. Continuer quand même?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            ) == QMessageBox.No:
                return False
        
        return True
    
    def accept(self):
        """Validation et acceptation du dialogue."""
        if not self.validate_form():
            return
        
        super().accept()