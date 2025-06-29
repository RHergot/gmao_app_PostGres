# gmao_app/app/ui/widgets/finance_couts_widget.py
"""
Widget pour la gestion des coûts d'une intervention de maintenance.
Permet la saisie des intervenants, pièces externes et autres frais,
ainsi que l'affichage du résumé des coûts.
"""
from typing import List, Dict, Optional, Callable, Any
import logging

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, 
                              QFormLayout, QGroupBox, QTabWidget, QDialog,
                              QMessageBox, QHeaderView, QFrame)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QFont

from app.core.models.maintenance_intervenant import MaintenanceIntervenant
from app.core.models.maintenance_frais_externe import (
    MaintenanceFraisExterne, VALID_TYPES_FRAIS
)
from app.core.models.technicien import Technicien

from app.data.repositories.technicien_repository import TechnicienRepository
from app.data.repositories.maintenance_intervenant_repository import MaintenanceIntervenantRepository
from app.data.repositories.maintenance_frais_externe_repository import MaintenanceFraisExterneRepository

from app.core.services.finance_service import FinanceService

logger = logging.getLogger(__name__)

class IntervenantDialog(QDialog):
    """Dialogue pour ajouter ou modifier un intervenant"""
    
    def __init__(self, maintenance_id: int, techniciens: List[Technicien], 
                 intervenant: Optional[MaintenanceIntervenant] = None, parent=None):
        super().__init__(parent)
        self.maintenance_id = maintenance_id
        self.techniciens = techniciens
        self.intervenant = intervenant
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setWindowTitle(self.tr("Intervenant") if not self.intervenant else self.tr("Modifier Intervenant"))
        self.setMinimumWidth(450)
        
        # Type d'intervenant (interne ou externe)
        type_group = QGroupBox(self.tr("Type d'intervenant"))
        type_layout = QVBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(self.tr("Technicien interne"), "interne")
        self.type_combo.addItem(self.tr("Intervenant externe"), "externe")
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Bloc technicien interne
        self.technicien_group = QGroupBox(self.tr("Technicien"))
        technicien_layout = QFormLayout()
        
        self.technicien_combo = QComboBox()
        for tech in self.techniciens:
            nom_tech = self.tr("%1 %2").replace("%1", tech.nom).replace("%2", tech.prenom or "")
            self.technicien_combo.addItem(nom_tech, tech.id_technicien)
        self.technicien_combo.currentIndexChanged.connect(self.on_technicien_changed)
        technicien_layout.addRow(self.tr("Sélectionner :"), self.technicien_combo)
        
        self.cout_horaire_interne = QDoubleSpinBox()
        self.cout_horaire_interne.setRange(0, 1000)
        self.cout_horaire_interne.setDecimals(2)
        self.cout_horaire_interne.setSuffix(self.tr(" €/h"))
        self.cout_horaire_interne.setReadOnly(True)  # Fixé selon le technicien
        technicien_layout.addRow(self.tr("Coût horaire :"), self.cout_horaire_interne)
        
        self.technicien_group.setLayout(technicien_layout)
        layout.addWidget(self.technicien_group)
        
        # Bloc intervenant externe
        self.externe_group = QGroupBox(self.tr("Intervenant externe"))
        externe_layout = QFormLayout()
        
        self.nom_externe = QLineEdit()
        externe_layout.addRow(self.tr("Nom :"), self.nom_externe)
        
        self.cout_horaire_externe = QDoubleSpinBox()
        self.cout_horaire_externe.setRange(0, 1000)
        self.cout_horaire_externe.setDecimals(2)
        self.cout_horaire_externe.setSuffix(self.tr(" €/h"))
        externe_layout.addRow(self.tr("Coût horaire :"), self.cout_horaire_externe)
        
        self.externe_group.setLayout(externe_layout)
        layout.addWidget(self.externe_group)
        
        # Données communes
        commun_group = QGroupBox(self.tr("Temps passé"))
        commun_layout = QFormLayout()
        
        self.heures_travaillees = QDoubleSpinBox()
        self.heures_travaillees.setRange(0.1, 1000)
        self.heures_travaillees.setDecimals(1)
        self.heures_travaillees.setSingleStep(0.5)
        self.heures_travaillees.setSuffix(self.tr(" h"))
        self.heures_travaillees.setValue(1.0)
        commun_layout.addRow(self.tr("Heures travaillées :"), self.heures_travaillees)
        
        self.notes = QLineEdit()
        commun_layout.addRow(self.tr("Notes :"), self.notes)
        
        commun_group.setLayout(commun_layout)
        layout.addWidget(commun_group)
        
        # Résumé du coût
        resume_layout = QHBoxLayout()
        self.cout_total_label = QLabel(self.tr("Coût total : 0.00 €"))
        font = QFont()
        font.setBold(True)
        self.cout_total_label.setFont(font)
        resume_layout.addWidget(self.cout_total_label)
        layout.addLayout(resume_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton(self.tr("Enregistrer"))
        self.save_button.clicked.connect(self.accept)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Connecter les signaux pour le calcul du coût total
        self.heures_travaillees.valueChanged.connect(self.update_cout_total)
        self.cout_horaire_externe.valueChanged.connect(self.update_cout_total)
        self.technicien_combo.currentIndexChanged.connect(self.update_cout_total)
        
        # Mode modification
        if self.intervenant:
            self.set_data_from_intervenant(self.intervenant)
        else:
            # Par défaut, afficher le bloc technicien et masquer le bloc externe
            self.on_type_changed(0)
            
        # Forcer une mise à jour initiale du coût horaire et total
        if self.technicien_combo.count() > 0:
            self.on_technicien_changed(0)
        self.update_cout_total()
    
    def on_type_changed(self, index):
        """Gère l'affichage selon le type d'intervenant sélectionné"""
        is_interne = self.type_combo.currentData() == "interne"
        self.technicien_group.setVisible(is_interne)
        self.externe_group.setVisible(not is_interne)
        
        # Réinitialiser les valeurs non pertinentes
        if is_interne:
            self.nom_externe.clear()
        else:
            # Ne pas réinitialiser le technicien sélectionné, juste au cas où l'utilisateur revient en arrière
            pass
        
        self.update_cout_total()
    
    def on_technicien_changed(self, index):
        """Met à jour le coût horaire en fonction du technicien sélectionné"""
        if index < 0 or index >= len(self.techniciens):
            return
            
        technicien_id = self.technicien_combo.currentData()
        technicien = next((t for t in self.techniciens if t.id_technicien == technicien_id), None)
        
        if technicien:
            self.cout_horaire_interne.setValue(technicien.cout_horaire or 0.0)
    
    def update_cout_total(self):
        """Calcule et affiche le coût total estimé"""
        is_interne = self.type_combo.currentData() == "interne"
        
        heures = self.heures_travaillees.value()
        taux = self.cout_horaire_interne.value() if is_interne else self.cout_horaire_externe.value()
        
        cout_total = heures * taux
        self.cout_total_label.setText(self.tr("Coût total : %1 €").replace("%1", f"{cout_total:.2f}"))
    
    def set_data_from_intervenant(self, intervenant: MaintenanceIntervenant):
        """Préremplir les champs avec les données d'un intervenant existant"""
        # Déterminer le type d'intervenant
        if intervenant.technicien_id:
            self.type_combo.setCurrentIndex(0)  # Interne
            index = self.technicien_combo.findData(intervenant.technicien_id)
            if index >= 0:
                self.technicien_combo.setCurrentIndex(index)
        else:
            self.type_combo.setCurrentIndex(1)  # Externe
            self.nom_externe.setText(intervenant.nom_intervenant_externe or "")
            self.cout_horaire_externe.setValue(intervenant.cout_horaire or 0.0)
        
        # Données communes
        self.heures_travaillees.setValue(intervenant.heures_travaillees or 1.0)
        self.notes.setText(intervenant.notes or "")
        
        # Forcer la mise à jour de l'interface
        self.on_type_changed(self.type_combo.currentIndex())
    
    def get_intervenant_data(self) -> dict:
        """Récupère les données saisies sous forme de dictionnaire"""
        is_interne = self.type_combo.currentData() == "interne"
        
        data = {
            'maintenance_id': self.maintenance_id,
            'heures_travaillees': self.heures_travaillees.value(),
            'notes': self.notes.text() or None
        }
        
        if is_interne:
            data['technicien_id'] = self.technicien_combo.currentData()
            data['cout_horaire'] = self.cout_horaire_interne.value()
            data['nom_intervenant_externe'] = None
        else:
            data['technicien_id'] = None
            data['nom_intervenant_externe'] = self.nom_externe.text()
            data['cout_horaire'] = self.cout_horaire_externe.value()
        
        # Ajouter l'ID si c'est une modification
        if self.intervenant and self.intervenant.id_intervenant:
            data['id_intervenant'] = self.intervenant.id_intervenant
            
        return data

class FraisExterneDialog(QDialog):
    """Dialogue pour ajouter ou modifier un frais externe"""
    
    def __init__(self, maintenance_id: int, 
                 frais: Optional[MaintenanceFraisExterne] = None, parent=None):
        super().__init__(parent)
        self.maintenance_id = maintenance_id
        self.frais = frais
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setWindowTitle(self.tr("Frais externe") if not self.frais else self.tr("Modifier frais externe"))
        self.setMinimumWidth(450)
        
        # Description
        self.description = QLineEdit()
        form_layout.addRow(self.tr("Description :"), self.description)
        
        # Montant unitaire
        self.montant = QDoubleSpinBox()
        self.montant.setRange(0, 100000)
        self.montant.setDecimals(2)
        self.montant.setSuffix(" €")
        self.montant.valueChanged.connect(self.update_montant_total)
        form_layout.addRow(self.tr("Montant unitaire :"), self.montant)
        
        # Quantité
        self.quantite = QSpinBox()
        self.quantite.setRange(1, 1000)
        self.quantite.setValue(1)
        self.quantite.valueChanged.connect(self.update_montant_total)
        form_layout.addRow(self.tr("Quantité :"), self.quantite)
        
        # Référence pièce (pour type PIECE_EXTERNE)
        self.reference_piece = QLineEdit()
        form_layout.addRow(self.tr("Référence pièce :"), self.reference_piece)
        
        # Fournisseur
        self.fournisseur = QLineEdit()
        form_layout.addRow(self.tr("Fournisseur :"), self.fournisseur)
        
        # Référence facture
        self.facture_reference = QLineEdit()
        form_layout.addRow(self.tr("Réf. facture :"), self.facture_reference)
        
        layout.addLayout(form_layout)
        
        # Résumé du montant
        resume_layout = QHBoxLayout()
        self.montant_total_label = QLabel(self.tr("Montant total : 0.00 €"))
        font = QFont()
        font.setBold(True)
        self.montant_total_label.setFont(font)
        resume_layout.addWidget(self.montant_total_label)
        layout.addLayout(resume_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        self.cancel_button = QPushButton(self.tr("Annuler"))
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton(self.tr("Enregistrer"))
        self.save_button.clicked.connect(self.accept)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Mode modification
        if self.frais:
            self.set_data_from_frais(self.frais)
        else:
            # Par défaut
            self.on_type_changed(0)
        
        # Forcer mise à jour initiale
        self.update_montant_total()
    
    def on_type_changed(self, index):
        """Ajuste l'interface selon le type de frais sélectionné"""
        type_frais = self.type_combo.currentData()
        
        # Les champs référence pièce et fournisseur sont plus pertinents pour les pièces externes
        self.reference_piece.setVisible(type_frais == 'PIECE_EXTERNE')
        
        # Mettre le focus sur la description
        self.description.setFocus()
    
    def update_montant_total(self):
        """Calcule et affiche le montant total"""
        montant = self.montant.value()
        quantite = self.quantite.value()
        
        montant_total = montant * quantite
        self.montant_total_label.setText(self.tr("Montant total : %1 €").replace("%1", f"{montant_total:.2f}"))
    
    def set_data_from_frais(self, frais: MaintenanceFraisExterne):
        """Préremplir les champs avec les données d'un frais existant"""
        # Type de frais
        index = self.type_combo.findData(frais.type_frais)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        self.description.setText(frais.description or "")
        self.montant.setValue(frais.montant or 0.0)
        self.quantite.setValue(frais.quantite or 1)
        self.reference_piece.setText(frais.reference_piece or "")
        self.fournisseur.setText(frais.fournisseur or "")
        self.facture_reference.setText(frais.facture_reference or "")
        
        # Forcer la mise à jour de l'interface
        self.on_type_changed(self.type_combo.currentIndex())
    
    def get_frais_data(self) -> dict:
        """Récupère les données saisies sous forme de dictionnaire"""
        data = {
            'maintenance_id': self.maintenance_id,
            'type_frais': self.type_combo.currentData(),
            'description': self.description.text(),
            'montant': self.montant.value(),
            'quantite': self.quantite.value(),
            'reference_piece': self.reference_piece.text() or None,
            'fournisseur': self.fournisseur.text() or None,
            'facture_reference': self.facture_reference.text() or None
        }
        
        # Ajouter l'ID si c'est une modification
        if self.frais and self.frais.id_frais:
            data['id_frais'] = self.frais.id_frais
            
        return data

class FinanceCoutsWidget(QWidget):
    """
    Widget principal pour la gestion des coûts d'une intervention.
    Comprend les onglets pour:
    - Les intervenants
    - Les frais externes
    - Le résumé des coûts
    """
    
    couts_updated = Signal()  # Signal émis quand les coûts sont mis à jour
    
    def __init__(self, maintenance_id: int, parent=None):
        super().__init__(parent)
        self.maintenance_id = maintenance_id
        # Initialisation explicite des labels à None pour éviter les erreurs d'attribut
        self.cout_main_oeuvre_label = None
        self.cout_pieces_internes_label = None
        self.cout_pieces_externes_label = None
        self.cout_autres_frais_label = None
        self.cout_total_label = None
        self.cout_total_detail_label = None
        # Repositories
        self.technicien_repo = TechnicienRepository()
        self.intervenant_repo = MaintenanceIntervenantRepository()
        self.frais_repo = MaintenanceFraisExterneRepository()
        # Service financier
        self.finance_service = FinanceService()
        # Liste des techniciens (pour les combos)
        self.techniciens = []
        self.init_ui()
        # Appeler load_data APRÈS l'initialisation complète de l'UI
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Onglets
        self.tab_widget = QTabWidget()
        
        # Onglet Intervenants
        self.intervenants_tab = QWidget()
        intervenants_layout = QVBoxLayout()
        
        # Tableau des intervenants
        self.intervenants_table = QTableWidget()
        self.intervenants_table.setColumnCount(6)
        self.intervenants_table.setHorizontalHeaderLabels([
            self.tr("Type"), self.tr("Nom"), self.tr("Heures"), self.tr("Taux"), self.tr("Coût"), self.tr("Actions")
        ])
        self.intervenants_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.intervenants_table.horizontalHeader().setStretchLastSection(True)
        self.intervenants_table.setSelectionBehavior(QTableWidget.SelectRows)
        intervenants_layout.addWidget(self.intervenants_table)
        
        # Boutons intervenants
        intervenants_buttons = QHBoxLayout()
        self.add_intervenant_button = QPushButton(self.tr("Ajouter intervenant"))
        self.add_intervenant_button.clicked.connect(self.add_intervenant)
        intervenants_buttons.addWidget(self.add_intervenant_button)
        intervenants_buttons.addStretch()
        intervenants_layout.addLayout(intervenants_buttons)
        
        self.intervenants_tab.setLayout(intervenants_layout)
        self.tab_widget.addTab(self.intervenants_tab, self.tr("Intervenants"))
        
        # Onglet Frais externes
        self.frais_tab = QWidget()
        frais_layout = QVBoxLayout()
        
        # Tableau des frais externes
        self.frais_table = QTableWidget()
        self.frais_table.setColumnCount(7)
        self.frais_table.setHorizontalHeaderLabels([
            self.tr("Type"), self.tr("Description"), self.tr("Montant"), self.tr("Quantité"), self.tr("Total"), self.tr("Référence"), self.tr("Actions")
        ])
        self.frais_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.frais_table.horizontalHeader().setStretchLastSection(True)
        self.frais_table.setSelectionBehavior(QTableWidget.SelectRows)
        frais_layout.addWidget(self.frais_table)
        # Pas de bouton "Ajouter frais" en mode consultation
        self.frais_tab.setLayout(frais_layout)
        self.tab_widget.addTab(self.frais_tab, self.tr("Frais externes"))

        # Onglet Résumé financier
        self.resume_tab = QWidget()
        resume_layout = QVBoxLayout()
        
        # En-tête résumé
        resume_header = QHBoxLayout()
        self.cout_total_label = QLabel(self.tr("Coût total : 0.00 €"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.cout_total_label.setFont(font)
        resume_header.addWidget(self.cout_total_label)
        resume_header.addStretch()
        
        self.refresh_button = QPushButton(self.tr("Recalculer"))
        self.refresh_button.clicked.connect(self.recalculer_couts)
        resume_header.addWidget(self.refresh_button)
        resume_layout.addLayout(resume_header)
        
        # Détail des coûts
        resume_group = QGroupBox(self.tr("Ventilation des coûts"))
        resume_form = QFormLayout()
        
        self.cout_main_oeuvre_label = QLabel(self.tr("0.00 €"))
        resume_form.addRow(self.tr("Main d'œuvre :"), self.cout_main_oeuvre_label)
        
        self.cout_pieces_internes_label = QLabel(self.tr("0.00 €"))
        resume_form.addRow(self.tr("Pièces internes :"), self.cout_pieces_internes_label)
        
        self.cout_pieces_externes_label = QLabel("0.00 €")
        resume_form.addRow(self.tr("Pièces externes :"), self.cout_pieces_externes_label)
        
        self.cout_autres_frais_label = QLabel("0.00 €")
        resume_form.addRow(self.tr("Autres frais :"), self.cout_autres_frais_label)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        resume_form.addRow("", separator)
        
        self.cout_total_detail_label = QLabel(self.tr("0.00 €"))
        self.cout_total_detail_label.setFont(font)
        resume_form.addRow(self.tr("Total :"), self.cout_total_detail_label)
        
        resume_group.setLayout(resume_form)
        resume_layout.addWidget(resume_group)
        resume_layout.addStretch()
        
        self.resume_tab.setLayout(resume_layout)
        self.tab_widget.addTab(self.resume_tab, self.tr("Résumé financier"))
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def load_data(self):
        """Charge les données initiales"""
        # Charger la liste des techniciens
        self.techniciens = self.technicien_repo.get_all_active()
        
        # Charger les intervenants
        self.refresh_intervenants()
        
        # Charger les frais externes
        self.refresh_frais()
        
        # Charger le résumé financier
        self.refresh_resume()
    
    def refresh_intervenants(self):
        """Rafraîchit la liste des intervenants"""
        self.intervenants_table.setRowCount(0)
        
        intervenants = self.intervenant_repo.get_by_maintenance_id(self.maintenance_id)
        
        for row, intervenant in enumerate(intervenants):
            self.intervenants_table.insertRow(row)
            
            # Type (interne/externe)
            type_cell = QTableWidgetItem(self.tr("Interne") if intervenant.technicien_id else self.tr("Externe"))
            self.intervenants_table.setItem(row, 0, type_cell)
            
            # Nom
            nom = ""
            if intervenant.technicien_id:
                technicien = next((t for t in self.techniciens 
                                  if t.id_technicien == intervenant.technicien_id), None)
                if technicien:
                    nom = self.tr("%1 %2").replace("%1", technicien.nom).replace("%2", technicien.prenom or "")
            else:
                nom = intervenant.nom_intervenant_externe or ""
            
            nom_cell = QTableWidgetItem(nom)
            self.intervenants_table.setItem(row, 1, nom_cell)
            
            # Heures
            heures_cell = QTableWidgetItem(self.tr("%1 h").replace("%1", f"{intervenant.heures_travaillees:.1f}"))
            heures_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.intervenants_table.setItem(row, 2, heures_cell)
            
            # Taux horaire
            taux_cell = QTableWidgetItem(self.tr("%1 €/h").replace("%1", f"{intervenant.cout_horaire:.2f}"))
            taux_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.intervenants_table.setItem(row, 3, taux_cell)
            
            # Coût total
            cout_cell = QTableWidgetItem(self.tr("%1 €").replace("%1", f"{intervenant.cout_total:.2f}"))
            cout_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.intervenants_table.setItem(row, 4, cout_cell)
            
            # Boutons d'action
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            
            edit_button = QPushButton(self.tr("Modifier"))
            edit_button.setMaximumWidth(80)
            edit_button.clicked.connect(lambda checked=False, i=intervenant: self.edit_intervenant(i))
            
            delete_button = QPushButton(self.tr("Supprimer"))
            delete_button.setMaximumWidth(80)
            delete_button.clicked.connect(lambda checked=False, i=intervenant: self.delete_intervenant(i))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            actions_widget.setLayout(actions_layout)
            
            self.intervenants_table.setCellWidget(row, 5, actions_widget)
        
        # Ajuster la largeur des colonnes
        self.intervenants_table.resizeColumnsToContents()
    
    def refresh_frais(self):
        """Rafraîchit la liste des frais externes"""
        self.frais_table.setRowCount(0)
        
        frais_list = self.frais_repo.get_by_maintenance_id(self.maintenance_id)
        
        for row, frais in enumerate(frais_list):
            self.frais_table.insertRow(row)
            
            # Type
            type_label = self.tr(frais.type_frais.replace('_', ' ').title())
            type_cell = QTableWidgetItem(type_label)
            self.frais_table.setItem(row, 0, type_cell)
            
            # Description
            desc_cell = QTableWidgetItem(frais.description)
            self.frais_table.setItem(row, 1, desc_cell)
            
            # Montant unitaire
            montant_cell = QTableWidgetItem(self.tr("%1 €").replace("%1", f"{frais.montant:.2f}"))
            montant_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.frais_table.setItem(row, 2, montant_cell)
            
            # Quantité
            quantite_cell = QTableWidgetItem(self.tr("%1").replace("%1", str(frais.quantite)))
            quantite_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.frais_table.setItem(row, 3, quantite_cell)
            
            # Montant total
            total_cell = QTableWidgetItem(self.tr("%1 €").replace("%1", f"{frais.montant_total:.2f}"))
            total_cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.frais_table.setItem(row, 4, total_cell)
            
            # Référence (combinant référence pièce et/ou fournisseur)
            ref_text = ""
            if frais.reference_piece:
                ref_text = frais.reference_piece
            if frais.fournisseur:
                if ref_text:
                    ref_text += f" - {frais.fournisseur}"
                else:
                    ref_text = frais.fournisseur
            
            ref_cell = QTableWidgetItem(self.tr(ref_text) if ref_text else "")
            self.frais_table.setItem(row, 5, ref_cell)
            
            # Boutons d'action
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            
            edit_button = QPushButton(self.tr("Modifier"))
            edit_button.setMaximumWidth(80)
            edit_button.clicked.connect(lambda checked=False, f=frais: self.edit_frais(f))
            
            delete_button = QPushButton(self.tr("Supprimer"))
            delete_button.setMaximumWidth(80)
            delete_button.clicked.connect(lambda checked=False, f=frais: self.delete_frais(f))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            actions_widget.setLayout(actions_layout)
            
            self.frais_table.setCellWidget(row, 6, actions_widget)
        
        # Ajuster la largeur des colonnes
        self.frais_table.resizeColumnsToContents()
    
    def refresh_resume(self):
        """Rafraîchit le résumé financier"""
        # Vérification explicite de l'initialisation des labels
        if not all([
            self.cout_main_oeuvre_label,
            self.cout_pieces_internes_label,
            self.cout_pieces_externes_label,
            self.cout_autres_frais_label,
            self.cout_total_label,
            self.cout_total_detail_label
        ]):
            raise RuntimeError("FinanceCoutsWidget: Un ou plusieurs labels ne sont pas initialisés avant refresh_resume() !")
        # Récupérer les données financières actuelles depuis la base de données
        resume = self.finance_service.get_resume_couts_maintenance(self.maintenance_id)
        if not resume:
            return
        
        # Mise à jour des labels
        self.cout_main_oeuvre_label.setText(self.tr("%1 €").replace("%1", f"{resume['ventilation']['main_oeuvre']['total']:.2f}"))
        self.cout_pieces_internes_label.setText(self.tr("%1 €").replace("%1", f"{resume['ventilation']['pieces_internes']['total']:.2f}"))
        self.cout_pieces_externes_label.setText(self.tr("%1 €").replace("%1", f"{resume['ventilation']['frais_externes']['pieces_externes']['total']:.2f}"))
        self.cout_autres_frais_label.setText(self.tr("%1 €").replace("%1", f"{resume['ventilation']['frais_externes']['autres_frais']['total']:.2f}"))
        
        # Total général
        cout_total = resume['cout_total']
        self.cout_total_label.setText(self.tr("Coût total : %1 €").replace("%1", f"{cout_total:.2f}"))
        self.cout_total_detail_label.setText(self.tr("%1 €").replace("%1", f"{cout_total:.2f}"))
    
    def add_intervenant(self):
        """Ajoute un nouvel intervenant"""
        dialog = IntervenantDialog(self.maintenance_id, self.techniciens, parent=self)
        if dialog.exec():
            try:
                # Créer un nouvel objet intervenant
                data = dialog.get_intervenant_data()
                intervenant = MaintenanceIntervenant(**data)
                
                # Ajouter à la base de données
                self.intervenant_repo.add(intervenant)
                
                # Rafraîchir l'affichage
                self.refresh_intervenants()
                
                # Recalculer les coûts
                self.recalculer_couts()
                
                # Notification
                QMessageBox.information(self, self.tr("Intervenant ajouté"), 
                                       self.tr("L'intervenant a été ajouté avec succès."))
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout d'un intervenant: {e}")
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ajouter l'intervenant : %1").replace("%1", str(e)))
    
    def edit_intervenant(self, intervenant: MaintenanceIntervenant):
        """Modifie un intervenant existant"""
        dialog = IntervenantDialog(self.maintenance_id, self.techniciens, intervenant, parent=self)
        if dialog.exec():
            try:
                # Mettre à jour l'intervenant
                data = dialog.get_intervenant_data()
                updated_intervenant = MaintenanceIntervenant(**data)
                # Enregistrer dans la base de données
                self.intervenant_repo.update(updated_intervenant)
            except Exception as e:
                logger.error(f"Erreur lors de la modification d'un intervenant: {e}")
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de modifier l'intervenant : %1").replace("%1", str(e)))
        # Rafraîchir l'affichage et les coûts
        self.refresh_intervenants()
        self.recalculer_couts()
    
    def add_intervenant(self):
        """Ajoute un nouvel intervenant"""
        dialog = IntervenantDialog(self.maintenance_id, self.techniciens, parent=self)
        if dialog.exec():
            try:
                data = dialog.get_intervenant_data()
                intervenant = MaintenanceIntervenant(**data)
                self.intervenant_repo.add(intervenant)
                self.refresh_intervenants()
                self.recalculer_couts()
                QMessageBox.information(self, self.tr("Intervenant ajouté"), 
                                       self.tr("L'intervenant a été ajouté avec succès."))
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout d'un intervenant: {e}")
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ajouter l'intervenant : %1").replace("%1", str(e)))

    def edit_intervenant(self, intervenant: MaintenanceIntervenant):
        """Modifie un intervenant existant"""
        dialog = IntervenantDialog(self.maintenance_id, self.techniciens, intervenant, parent=self)
        if dialog.exec():
            try:
                data = dialog.get_intervenant_data()
                updated_intervenant = MaintenanceIntervenant(**data)
                self.intervenant_repo.update(updated_intervenant)
                self.refresh_intervenants()
                self.recalculer_couts()
            except Exception as e:
                logger.error(f"Erreur lors de la modification d'un intervenant: {e}")
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de modifier l'intervenant : %1").replace("%1", str(e)))

    def recalculer_couts(self):
        try:
            self.refresh_resume()
            QMessageBox.information(self, self.tr("Coûts recalculés"), 
                                    self.tr("Les coûts ont été recalculés avec succès."))
        except Exception as e:
            logger.error(f"Erreur lors du recalcul des coûts: {e}")
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de recalculer les coûts : %1").replace("%1", str(e)))