# gmao_app/app/ui/dialogs/intervenant_dialog.py
"""
Dialogue pour ajouter ou modifier un intervenant dans une maintenance.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QMessageBox, QDoubleSpinBox,
    QRadioButton, QButtonGroup, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from app.core.models.maintenance_intervenant import MaintenanceIntervenant
from app.core.models.technicien import Technicien

logger = logging.getLogger(__name__)

class IntervenantDialog(QDialog):
    """Dialogue pour ajouter ou modifier un intervenant dans une maintenance."""
    
    def __init__(self, parent=None, techniciens=None, intervenant=None, maintenance_id=None):
        """
        Initialise le dialogue d'intervenant.
        
        Args:
            parent: Widget parent
            techniciens: Liste des techniciens disponibles
            intervenant: Intervenant existant à modifier (None pour création)
            maintenance_id: ID de la maintenance associée (nécessaire pour la création)
        """
        super().__init__(parent)
        self.techniciens = techniciens or []
        self.intervenant = intervenant
        self.maintenance_id = maintenance_id
        self.is_edit_mode = intervenant is not None
        
        self._setup_ui()
        
        if self.is_edit_mode:
            self._populate_form_data()
        else:
            # Mode création, vérifier que l'ID de maintenance est fourni
            if not self.maintenance_id:
                logger.error("ID de maintenance non fourni pour création d'intervenant")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("ID de maintenance manquant."))
                self.reject()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle(self.tr("Intervenant") if self.is_edit_mode else self.tr("Nouvel Intervenant"))
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Choix du type d'intervenant
        type_group = QGroupBox(self.tr("Type d'intervenant"))
        type_layout = QHBoxLayout()
        
        self.rb_interne = QRadioButton(self.tr("Technicien interne"))
        self.rb_externe = QRadioButton(self.tr("Intervenant externe"))
        self.type_group = QButtonGroup()
        self.type_group.addButton(self.rb_interne, 1)
        self.type_group.addButton(self.rb_externe, 2)
        self.rb_interne.setChecked(True)
        
        type_layout.addWidget(self.rb_interne)
        type_layout.addWidget(self.rb_externe)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Technicien interne (combobox)
        self.technicien_layout = QHBoxLayout()
        self.technicien_layout.addWidget(QLabel(self.tr("Technicien:")))
        self.cb_technicien = QComboBox()
        for tech in self.techniciens:
            self.cb_technicien.addItem(f"{tech.nom} {tech.prenom or ''}".strip(), tech.id_technicien)
        self.technicien_layout.addWidget(self.cb_technicien)
        layout.addLayout(self.technicien_layout)
        
        # Intervenant externe (champ texte)
        self.externe_layout = QHBoxLayout()
        self.externe_layout.addWidget(QLabel(self.tr("Nom:")))
        self.txt_externe = QLineEdit()
        self.externe_layout.addWidget(self.txt_externe)
        layout.addLayout(self.externe_layout)
        
        # Heures travaillées
        heures_layout = QHBoxLayout()
        heures_layout.addWidget(QLabel(self.tr("Heures travaillées:")))
        self.sp_heures = QDoubleSpinBox()
        self.sp_heures.setMinimum(0.1)
        self.sp_heures.setMaximum(168)  # 1 semaine max
        self.sp_heures.setDecimals(1)
        self.sp_heures.setSingleStep(0.5)
        self.sp_heures.setValue(1)
        heures_layout.addWidget(self.sp_heures)
        layout.addLayout(heures_layout)
        
        # Coût horaire
        cout_layout = QHBoxLayout()
        cout_layout.addWidget(QLabel(self.tr("Coût horaire (€):")))
        self.sp_cout = QDoubleSpinBox()
        self.sp_cout.setMinimum(0)
        self.sp_cout.setMaximum(500)
        self.sp_cout.setDecimals(2)
        self.sp_cout.setSingleStep(5)
        self.sp_cout.setValue(35)
        cout_layout.addWidget(self.sp_cout)
        layout.addLayout(cout_layout)
        
        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel(self.tr("Notes:")))
        self.txt_notes = QLineEdit()
        notes_layout.addWidget(self.txt_notes)
        layout.addLayout(notes_layout)
        
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
        self.type_group.buttonClicked.connect(self._on_type_changed)
        self.cb_technicien.currentIndexChanged.connect(self._on_technicien_changed)
        
        # État initial
        self._on_type_changed()
    
    def _on_type_changed(self):
        """Gère le changement de type d'intervenant."""
        is_interne = self.rb_interne.isChecked()
        self.technicien_layout.setEnabled(is_interne)
        self.externe_layout.setEnabled(not is_interne)
        
        # Si on sélectionne un technicien interne et qu'il y a une sélection,
        # mettre à jour le coût horaire
        if is_interne and self.cb_technicien.count() > 0:
            self._on_technicien_changed()
    
    def _on_technicien_changed(self):
        """Met à jour le coût horaire en fonction du technicien sélectionné."""
        if not self.rb_interne.isChecked():
            return
            
        selected_id = self.cb_technicien.currentData()
        if selected_id is None:
            return
            
        # Trouver le technicien sélectionné
        for tech in self.techniciens:
            if tech.id_technicien == selected_id:
                # Mettre à jour le coût horaire
                self.sp_cout.setValue(float(tech.cout_horaire or 0))
                break
    
    def _populate_form_data(self):
        """Remplit le formulaire avec les données de l'intervenant existant."""
        if not self.intervenant:
            return
        
        # Type d'intervenant
        if self.intervenant.technicien_id:
            self.rb_interne.setChecked(True)
            # Sélectionner le technicien dans la combobox
            index = self.cb_technicien.findData(self.intervenant.technicien_id)
            if index >= 0:
                self.cb_technicien.setCurrentIndex(index)
        else:
            self.rb_externe.setChecked(True)
            if self.intervenant.nom_intervenant_externe:
                self.txt_externe.setText(self.intervenant.nom_intervenant_externe)
        
        # Mettre à jour l'interface selon le type
        self._on_type_changed()
        
        # Autres champs
        self.sp_heures.setValue(self.intervenant.heures_travaillees)
        self.sp_cout.setValue(self.intervenant.cout_horaire)
        if self.intervenant.notes:
            self.txt_notes.setText(self.intervenant.notes)
    
    def get_form_data(self):
        """Récupère les données du formulaire."""
        is_interne = self.rb_interne.isChecked()
        
        data = {
            'maintenance_id': self.maintenance_id,
            'heures_travaillees': self.sp_heures.value(),
            'cout_horaire': self.sp_cout.value(),
            'notes': self.txt_notes.text().strip() or None
        }
        
        if is_interne:
            data['technicien_id'] = self.cb_technicien.currentData()
            data['nom_intervenant_externe'] = None
        else:
            data['technicien_id'] = None
            data['nom_intervenant_externe'] = self.txt_externe.text().strip()
        
        if self.is_edit_mode:
            data['id_intervenant'] = self.intervenant.id_intervenant
        
        return data
    
    def validate_form(self):
        """Valide les données du formulaire."""
        is_interne = self.rb_interne.isChecked()
        
        if is_interne and self.cb_technicien.currentData() is None:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez sélectionner un technicien."))
            return False
        
        if not is_interne and not self.txt_externe.text().strip():
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Veuillez saisir le nom de l'intervenant externe."))
            return False
        
        if self.sp_heures.value() <= 0:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Les heures travaillées doivent être positives."))
            return False
        
        if self.sp_cout.value() < 0:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le coût horaire ne peut pas être négatif."))
            return False
        
        return True
    
    def accept(self):
        """Validation et acceptation du dialogue."""
        if not self.validate_form():
            return
        
        super().accept()