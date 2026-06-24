# gmao_app/app/ui/dialogs/maintenance_detail_dialog.py
"""
Dialogue pour afficher les détails d'une maintenance, y compris les aspects financiers.
Implémente la Phase 11 de la roadmap technique (Gestion Financière & Coûts).
"""
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, 
    QFormLayout, QGroupBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.core.models.maintenance import Maintenance
from app.core.models.ordre_travail import OrdreTravail
from app.core.services.maintenance_service import MaintenanceService
from app.ui.widgets.finance_couts_widget import FinanceCoutsWidget

logger = logging.getLogger(__name__)

class MaintenanceDetailDialog(QDialog):
    """
    Dialogue pour afficher les détails d'une maintenance avec onglets pour
    informations générales, pièces utilisées, intervenants, frais et coûts.
    """
    
    def __init__(self, maintenance_id: int, ot_id: Optional[int] = None, 
                 maintenance_service: Optional[MaintenanceService] = None, 
                 parent=None):
        super().__init__(parent)
        
        self.maintenance_id = maintenance_id
        self.ot_id = ot_id
        
        if maintenance_service is None:
            raise RuntimeError("L'instance de MaintenanceService doit être fournie par l'application principale (avec FinanceService injecté).")
        self.maintenance_service = maintenance_service
        
        # Récupérer les données
        self.maintenance = None
        self.ot = None
        self._load_data()
        
        # Configurer l'interface
        self.setWindowTitle(self.tr("Détails Maintenance %1").replace("%1", str(self.ot.numero_ot if self.ot else maintenance_id)))
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def _load_data(self):
        """Charge les données de la maintenance et de l'OT associé"""
        try:
            # Charger la maintenance
            self.maintenance = self.maintenance_service.get_maintenance_by_id(self.maintenance_id)
            if not self.maintenance:
                logger.error(f"Maintenance ID {self.maintenance_id} non trouvée")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Maintenance ID %1 introuvable").replace("%1", str(self.maintenance_id)))
                return
            
            # Si ot_id n'est pas fourni, utiliser celui de la maintenance
            if not self.ot_id and self.maintenance:
                self.ot_id = self.maintenance.ot_id
            
            # Charger l'OT
            if self.ot_id:
                self.ot = self.maintenance_service.get_ot_by_id(self.ot_id)
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données de maintenance: {e}")
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les données: %1").replace("%1", str(e)))
    
    def init_ui(self):
        """Initialise l'interface utilisateur du dialogue"""
        if not self.maintenance:
            # Si les données n'ont pas pu être chargées, afficher un message et fermer
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(self.tr("Impossible de charger les données de maintenance")))
            self.setLayout(layout)
            return
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # En-tête avec le titre et le numéro d'OT
        header_layout = QHBoxLayout()
        title_label = QLabel(self.tr("Maintenance %1").replace("%1", str(self.ot.numero_ot if self.ot else ''))) 
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Ajouter le statut de l'OT
        if self.ot:
            status_label = QLabel(self.tr("Statut: %1").replace("%1", str(self.ot.statut)))
            status_font = QFont()
            status_font.setBold(True)
            status_label.setFont(status_font)
            header_layout.addWidget(status_label)
        
        main_layout.addLayout(header_layout)
        
        # Créer les onglets
        self.tab_widget = QTabWidget()
        
        # Onglet Informations générales
        self.info_tab = self._create_info_tab()
        self.tab_widget.addTab(self.info_tab, self.tr("Informations"))
        
        # Onglet Coûts & Finances
        self.finance_tab = self._create_finance_tab()
        self.tab_widget.addTab(self.finance_tab, self.tr("Coûts & Finances"))
        
        main_layout.addWidget(self.tab_widget)
        
        # Boutons de dialogue
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def _create_info_tab(self) -> QWidget:
        """Crée l'onglet d'informations générales sur la maintenance"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Informations OT
        ot_group = QGroupBox(self.tr("Informations OT"))
        ot_form = QFormLayout()
        
        ot_numero_label = QLabel(self.ot.numero_ot if self.ot else "N/A")
        ot_form.addRow(self.tr("Numéro OT:"), ot_numero_label)
        
        ot_date_creation_label = QLabel(self.ot.date_creation.strftime('%Y-%m-%d %H:%M') if self.ot and self.ot.date_creation else "N/A")
        ot_form.addRow(self.tr("Date création:"), ot_date_creation_label)
        
        ot_description_label = QLabel(self.ot.description if self.ot else "N/A")
        ot_description_label.setWordWrap(True)
        ot_form.addRow(self.tr("Description:"), ot_description_label)
        
        ot_type_label = QLabel(self.ot.type if self.ot else "N/A")
        ot_form.addRow(self.tr("Type:"), ot_type_label)
        
        ot_priorite_label = QLabel(self.ot.priorite if self.ot else "N/A")
        ot_form.addRow(self.tr("Priorité:"), ot_priorite_label)
        
        ot_group.setLayout(ot_form)
        layout.addWidget(ot_group)
        
        # Groupe Détails Intervention
        maintenance_group = QGroupBox(self.tr("Détails Intervention"))
        maintenance_form = QFormLayout()
        
        technicien_label = QLabel(f"ID: {self.maintenance.technicien_id}")  # Idéalement, afficher le nom complet
        maintenance_form.addRow(self.tr("Technicien:"), technicien_label)
        
        date_debut_label = QLabel(self.maintenance.date_debut_reelle.strftime('%Y-%m-%d %H:%M') if self.maintenance.date_debut_reelle else "N/A")
        maintenance_form.addRow(self.tr("Date début:"), date_debut_label)
        
        date_fin_label = QLabel(self.maintenance.date_fin_reelle.strftime('%Y-%m-%d %H:%M') if self.maintenance.date_fin_reelle else "N/A")
        maintenance_form.addRow(self.tr("Date fin:"), date_fin_label)
        
        duree_label = QLabel(f"{self.maintenance.duree_intervention_h} {self.tr('heures')}" if self.maintenance.duree_intervention_h is not None else "N/A")
        maintenance_form.addRow(self.tr("Durée:"), duree_label)
        
        resultat_label = QLabel(self.maintenance.resultat if self.maintenance.resultat else "N/A")
        maintenance_form.addRow(self.tr("Résultat:"), resultat_label)
        
        travaux_label = QLabel(self.maintenance.description_travaux)
        travaux_label.setWordWrap(True)
        maintenance_form.addRow(self.tr("Travaux réalisés:"), travaux_label)
        
        if self.maintenance.notes_technicien:
            notes_label = QLabel(self.maintenance.notes_technicien)
            notes_label.setWordWrap(True)
            maintenance_form.addRow(self.tr("Notes:"), notes_label)
        
        maintenance_group.setLayout(maintenance_form)
        layout.addWidget(maintenance_group)
        
        # Ajouter un espace extensible
        layout.addStretch()
        
        return tab
    
    def _create_finance_tab(self) -> QWidget:
        """Crée l'onglet des coûts financiers de la maintenance"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Intégrer le widget de gestion des coûts
        self.finance_widget = FinanceCoutsWidget(self.maintenance_id)
        layout.addWidget(self.finance_widget)
        
        return tab
    
    def closeEvent(self, event):
        """Gérer la fermeture propre du dialogue"""
        # On pourrait ajouter des actions spécifiques à la fermeture ici
        super().closeEvent(event)