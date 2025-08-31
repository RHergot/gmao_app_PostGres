# gmao_app/app/ui/views/maintenance_detail_view.py
"""
Vue détaillée d'une maintenance avec divers onglets (informations générales, coûts, pièces, etc.)
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QMessageBox, QGroupBox, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDateTimeEdit, QSpinBox, QCheckBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal, QDateTime, Slot
from PySide6.QtGui import QIcon

from app.core.models.maintenance import Maintenance
from app.core.models.ordre_travail import OrdreTravail
from app.core.models.machine import Machine
from app.core.models.technicien import Technicien
from app.core.services.maintenance_service import MaintenanceService
from app.core.services.machine_service import MachineService
from app.core.services.stock_service import StockService
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

from app.ui.widgets.maintenance_couts_widget import MaintenanceCoutsWidget
from app.ui.dialogs.intervenant_dialog import IntervenantDialog
from app.ui.dialogs.frais_externe_dialog import FraisExterneDialog

logger = logging.getLogger(__name__)

class MaintenanceDetailView(QWidget):
    """Vue détaillée d'une maintenance avec plusieurs onglets."""
    
    # Signaux
    maintenanceUpdated = Signal(int)  # Émis lorsque la maintenance est mise à jour
    
    def __init__(
        self,
        maintenance_service: MaintenanceService,
        machine_service: MachineService,
        stock_service: StockService,
        maintenance_id: Optional[int] = None,
        ot_id: Optional[int] = None,
        parent=None
    ):
        """
        Initialise la vue détaillée de maintenance.
        
        Args:
            maintenance_service: Service pour les opérations sur les maintenances
            machine_service: Service pour les opérations sur les machines
            stock_service: Service pour les opérations sur le stock et les pièces
            maintenance_id: ID de la maintenance à afficher
            ot_id: ID de l'OT associé (alternative à maintenance_id)
            parent: Widget parent
        """
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.machine_service = machine_service
        self.stock_service = stock_service
        
        self.maintenance_id = maintenance_id
        self.ot_id = ot_id
        
        self.maintenance = None
        self.ordre_travail = None
        self.machine = None
        self.technicien = None
        
        self._setup_ui()
        
        # Chargement initial
        if maintenance_id or ot_id:
            self.load_maintenance()
        
        logger.debug("MaintenanceDetailView initialisée")
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle(self.tr("Détails de la maintenance"))
        
        main_layout = QVBoxLayout(self)
        
        # En-tête avec informations essentielles
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        
        # Informations OT et machine
        info_group = QGroupBox(self.tr("Intervention"))
        info_layout = QFormLayout(info_group)
        
        self.lbl_ot_numero = QLabel("N/A")
        self.lbl_machine = QLabel("N/A")
        self.lbl_type = QLabel("N/A")
        self.lbl_statut = QLabel("N/A")
        self.lbl_demandeur = QLabel("N/A")
        
        info_layout.addRow(self.tr("OT n°:"), self.lbl_ot_numero)
        info_layout.addRow(self.tr("Machine:"), self.lbl_machine)
        info_layout.addRow(self.tr("Type:"), self.lbl_type)
        info_layout.addRow(self.tr("Statut:"), self.lbl_statut)
        info_layout.addRow(self.tr("Demandeur:"), self.lbl_demandeur)
        
        header_layout.addWidget(info_group)
        
        # Informations intervenant et dates
        dates_group = QGroupBox(self.tr("Réalisation"))
        dates_layout = QFormLayout(dates_group)
        
        self.lbl_technicien = QLabel("N/A")
        self.lbl_date_debut = QLabel("N/A")
        self.lbl_date_fin = QLabel("N/A")
        self.lbl_duree = QLabel("N/A")
        
        dates_layout.addRow(self.tr("Technicien:"), self.lbl_technicien)
        dates_layout.addRow(self.tr("Début:"), self.lbl_date_debut)
        dates_layout.addRow(self.tr("Fin:"), self.lbl_date_fin)
        dates_layout.addRow(self.tr("Durée:"), self.lbl_duree)
        
        header_layout.addWidget(dates_group)
        
        # Coût total
        cout_group = QGroupBox(self.tr("Coût"))
        cout_layout = QVBoxLayout(cout_group)
        
        self.lbl_cout_total = QLabel("0,00 €")
        self.lbl_cout_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #006400;")
        self.lbl_cout_total.setAlignment(Qt.AlignCenter)
        
        cout_layout.addWidget(self.lbl_cout_total)
        cout_layout.addStretch()
        
        header_layout.addWidget(cout_group)
        
        # Ajouter l'en-tête au layout principal
        main_layout.addWidget(self.header_widget)
        
        # Onglets pour les différentes sections
        self.tab_widget = QTabWidget()
        
        # Onglet Général
        self.general_tab = QWidget()
        general_layout = QVBoxLayout(self.general_tab)
        
        # Formulaire principal
        form_group = QGroupBox(self.tr("Rapport d'intervention"))
        form_layout = QFormLayout(form_group)
        
        # Résultat et constats
        self.resultat_combo = QComboBox()
        self.resultat_combo.addItems([self.tr("TERMINE"), self.tr("PARTIEL"), self.tr("ECHEC")])
        form_layout.addRow(self.tr("Résultat:"), self.resultat_combo)
        
        self.travaux_text = QTextEdit()
        form_layout.addRow(self.tr("Travaux réalisés:"), self.travaux_text)
        
        self.notes_text = QTextEdit()
        form_layout.addRow(self.tr("Notes techniques:"), self.notes_text)
        
        # Évaluations
        eval_group = QGroupBox(self.tr("Évaluations"))
        eval_layout = QFormLayout(eval_group)
        
        self.evaluation_combo = QComboBox()
        self.evaluation_combo.addItems(["", self.tr("EXCELLENT"), self.tr("BON"), self.tr("MOYEN"), self.tr("INSUFFISANT")])
        eval_layout.addRow(self.tr("Qualité:"), self.evaluation_combo)
        
        self.impact_combo = QComboBox()
        self.impact_combo.addItems(["", self.tr("AUCUN"), self.tr("FAIBLE"), self.tr("MOYEN"), self.tr("IMPORTANT"), self.tr("CRITIQUE")])
        eval_layout.addRow(self.tr("Impact production:"), self.impact_combo)
        
        form_layout.addRow("", eval_group)
        
        general_layout.addWidget(form_group)
        
        # Onglet Coûts
        self.couts_tab = QWidget()
        couts_layout = QVBoxLayout(self.couts_tab)
        
        # Widget de coûts
        self.couts_widget = MaintenanceCoutsWidget(parent=self)
        self.couts_widget.coutsModifies.connect(self._on_couts_modifies)
        
        couts_layout.addWidget(self.couts_widget)
        
        # Onglet Pièces
        self.pieces_tab = QWidget()
        pieces_layout = QVBoxLayout(self.pieces_tab)
        
        from app.ui.widgets.maintenance_pieces_widget import MaintenancePiecesWidget
        self.pieces_widget = MaintenancePiecesWidget(parent=self)
        pieces_layout.addWidget(self.pieces_widget)
        
        # Ajouter les onglets
        self.tab_widget.addTab(self.general_tab, self.tr("Général"))
        self.tab_widget.addTab(self.couts_tab, self.tr("Coûts"))
        self.tab_widget.addTab(self.pieces_tab, self.tr("Pièces"))
        
        main_layout.addWidget(self.tab_widget)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton(self.tr("Actualiser"))
        self.refresh_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_button.clicked.connect(self.load_maintenance)
        
        self.save_button = QPushButton(self.tr("Enregistrer les modifications"))
        self.save_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_button.clicked.connect(self.save_maintenance)
        
        self.print_button = QPushButton(self.tr("Imprimer rapport"))
        self.print_button.setIcon(QIcon.fromTheme("document-print"))
        self.print_button.clicked.connect(self.print_report)
        
        self.close_button = QPushButton(self.tr("Fermer"))
        self.close_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.print_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        
        main_layout.addLayout(buttons_layout)
        
        # État initial des boutons
        self.save_button.setEnabled(False)
        self.print_button.setEnabled(False)
        
        # Connexions
        self.resultat_combo.currentTextChanged.connect(self._on_form_changed)
        self.travaux_text.textChanged.connect(self._on_form_changed)
        self.notes_text.textChanged.connect(self._on_form_changed)
        self.evaluation_combo.currentTextChanged.connect(self._on_form_changed)
        self.impact_combo.currentTextChanged.connect(self._on_form_changed)
    
    def load_maintenance(self):
        """Charge les données de la maintenance."""
        try:
            # Déterminer quelle maintenance charger
            if self.maintenance_id:
                self.maintenance = self.maintenance_service.get_maintenance_by_id(self.maintenance_id)
                if self.maintenance:
                    self.ot_id = self.maintenance.ot_id  # Correction : ordre_travail_id -> ot_id
            elif self.ot_id:
                self.maintenance = self.maintenance_service.get_maintenance_for_ot(self.ot_id)
                if self.maintenance:
                    self.maintenance_id = self.maintenance.id_maintenance
            
            if not self.maintenance:
                QMessageBox.warning(self, "Erreur", "Maintenance non trouvée.")
                self.setEnabled(False)
                return
            
            # Charger l'OT associé
            self.ordre_travail = self.maintenance_service.get_ot_by_id(self.ot_id)
            
            # Charger les informations associées
            if self.ordre_travail and self.ordre_travail.machine_id:
                self.machine = self.machine_service.get_machine_by_id(self.ordre_travail.machine_id)
            
            if self.maintenance.technicien_id:
                self.technicien = self.maintenance_service.get_technicien_by_id(self.maintenance.technicien_id)
            
            # Mettre à jour l'interface
            self._populate_form()
            
            # Activer les boutons
            self.save_button.setEnabled(True)
            self.print_button.setEnabled(True)
            
            logger.info(f"Maintenance ID {self.maintenance_id} chargée avec succès")
            
        except (BusinessLogicError, DatabaseError, NotFoundError) as e:
            QMessageBox.warning(self, "Erreur Chargement", f"Impossible de charger la maintenance:\n{e}")
            logger.error(f"Erreur chargement maintenance: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inattendue", f"Erreur lors du chargement:\n{e}")
            logger.exception(f"Erreur inattendue chargement maintenance")
    
    def _populate_form(self):
        """Remplit le formulaire avec les données de la maintenance."""
        if not self.maintenance or not self.ordre_travail:
            return
        
        # En-tête
        ot_numero = self.ordre_travail.numero_ot or f"OT-{self.ordre_travail.id_ot}"
        self.lbl_ot_numero.setText(ot_numero)
        
        if self.machine:
            self.lbl_machine.setText(f"{self.machine.nom} ({self.machine.serial})")
        else:
            self.lbl_machine.setText(f"ID: {self.ordre_travail.machine_id}")
        
        self.lbl_type.setText(self.maintenance.type_reel or "N/A")
        self.lbl_statut.setText(self.ordre_travail.statut)
        
        # Remplacer demandeur par utilisateur_createur_id
        self.lbl_demandeur.setText(f"ID: {self.ordre_travail.utilisateur_createur_id}" or "N/A")
        
        # Réalisation
        if self.technicien:
            self.lbl_technicien.setText(f"{self.technicien.nom} {self.technicien.prenom or ''}".strip())
        else:
            self.lbl_technicien.setText("N/A")
        
        if self.maintenance.date_debut_reelle:
            self.lbl_date_debut.setText(self.maintenance.date_debut_reelle.strftime("%d/%m/%Y %H:%M"))
        
        if self.maintenance.date_fin_reelle:
            self.lbl_date_fin.setText(self.maintenance.date_fin_reelle.strftime("%d/%m/%Y %H:%M"))
        
        if self.maintenance.duree_intervention_h:
            self.lbl_duree.setText(f"{self.maintenance.duree_intervention_h:.1f} h")
        
        # Onglet Général
        if self.maintenance.resultat:
            index = self.resultat_combo.findText(self.maintenance.resultat)
            if index >= 0:
                self.resultat_combo.setCurrentIndex(index)
        
        if self.maintenance.description_travaux:
            self.travaux_text.setText(self.maintenance.description_travaux)
        
        if self.maintenance.notes_technicien:
            self.notes_text.setText(self.maintenance.notes_technicien)
        
        # Correction pour evaluation_qualite (conversion int -> str)
        if self.maintenance.evaluation_qualite is not None:
            # Mapping des valeurs numériques vers les textes
            evaluation_mapping = {
                1: "INSUFFISANT", 
                2: "MOYEN", 
                3: "BON", 
                4: "EXCELLENT"
            }
            qualite_texte = evaluation_mapping.get(self.maintenance.evaluation_qualite, "")
            if qualite_texte:
                index = self.evaluation_combo.findText(qualite_texte)
                if index >= 0:
                    self.evaluation_combo.setCurrentIndex(index)
        
        if self.maintenance.impact_production:
            index = self.impact_combo.findText(self.maintenance.impact_production)
            if index >= 0:
                self.impact_combo.setCurrentIndex(index)
        
        # Initialiser le widget de coûts avec tous les services nécessaires
        if self.maintenance_id:
            # Important: Assigner le service de maintenance avant d'appeler set_maintenance_id
            self.couts_widget.maintenance_service = self.maintenance_service
            # Maintenant définir l'ID (cela déclenche le calcul des coûts dans le widget)
            self.couts_widget.set_maintenance_id(self.maintenance_id)

            # Initialiser le widget des pièces
            self.pieces_widget.maintenance_service = self.maintenance_service
            self.pieces_widget.stock_service = self.stock_service
            self.pieces_widget.set_maintenance_id(self.maintenance_id)

            # Mettre à jour le coût total dans l'en-tête en utilisant les données du widget
            # Récupérer les données de coût déjà calculées par le widget
            cout_data = self.couts_widget.cout_data
            if cout_data and 'cout_total' in cout_data:
                cout_total = cout_data['cout_total']
                self.lbl_cout_total.setText(f"{cout_total:.2f} €")
            else:
                # Fallback si les données ne sont pas disponibles (devrait être rare)
                self.lbl_cout_total.setText("N/A")
                logger.warning("Données de coût non trouvées dans couts_widget après initialisation.")

        # Désactiver les signaux pendant le remplissage
        self._disconnect_signals()
        
        # Réactiver les signaux après le remplissage
        self._reconnect_signals()
    
    def _disconnect_signals(self):
        """Déconnecte les signaux temporairement."""
        try:
            self.resultat_combo.currentTextChanged.disconnect(self._on_form_changed)
            self.travaux_text.textChanged.disconnect(self._on_form_changed)
            self.notes_text.textChanged.disconnect(self._on_form_changed)
            self.evaluation_combo.currentTextChanged.disconnect(self._on_form_changed)
            self.impact_combo.currentTextChanged.disconnect(self._on_form_changed)
        except:
            pass
    
    def _reconnect_signals(self):
        """Reconnecte les signaux."""
        self.resultat_combo.currentTextChanged.connect(self._on_form_changed)
        self.travaux_text.textChanged.connect(self._on_form_changed)
        self.notes_text.textChanged.connect(self._on_form_changed)
        self.evaluation_combo.currentTextChanged.connect(self._on_form_changed)
        self.impact_combo.currentTextChanged.connect(self._on_form_changed)
    
    @Slot()
    def _on_form_changed(self):
        """Appelé lorsque le formulaire est modifié."""
        self.save_button.setEnabled(True)
    
    @Slot()
    def _on_couts_modifies(self):
        """Appelé lorsque les coûts sont modifiés."""
        # Mettre à jour le coût total dans l'en-tête
        try:
            cout_data = self.maintenance_service.calculate_maintenance_cost(self.maintenance_id)
            if cout_data and 'cout_total' in cout_data:
                cout_total = cout_data['cout_total']
                self.lbl_cout_total.setText(f"{cout_total:.2f} €")
        except Exception as e:
            logger.error(f"Erreur calcul coût total: {e}")
        
        # Marquer comme modifié
        self._on_form_changed()
    
    @Slot()
    def save_maintenance(self):
        """Enregistre les modifications de la maintenance."""
        if not self.maintenance or not self.maintenance_id:
            return
        
        try:
            # Récupérer les données du formulaire
            data = {
                'id_maintenance': self.maintenance_id,
                'resultat': self.resultat_combo.currentText(),
                'description_travaux': self.travaux_text.toPlainText(),
                'notes_technicien': self.notes_text.toPlainText() or None,
                'evaluation_qualite': self.evaluation_combo.currentText() or None,
                'impact_production': self.impact_combo.currentText() or None,
                # Ajouter technicien_id qui est obligatoire pour la mise à jour
                'technicien_id': self.maintenance.technicien_id
            }
            
            # Mise à jour via le service
            updated = self.maintenance_service.update_maintenance(data)
            
            if updated:
                QMessageBox.information(self, self.tr("Succès"), self.tr("Maintenance mise à jour avec succès."))
                self.save_button.setEnabled(False)
                
                # Recharger pour afficher les changements
                self.load_maintenance()
                
                # Émettre le signal de mise à jour
                self.maintenanceUpdated.emit(self.maintenance_id)
                
                logger.info(f"Maintenance ID {self.maintenance_id} mise à jour avec succès")
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Échec de la mise à jour de la maintenance."))
                
        except (BusinessLogicError, DatabaseError, NotFoundError) as e:
            QMessageBox.warning(self, self.tr("Erreur Mise à Jour"), self.tr("Impossible de mettre à jour la maintenance:\n%1").replace("%1", str(e)))
            logger.error(f"Erreur mise à jour maintenance: {e}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur lors de la mise à jour:\n%1").replace("%1", str(e)))
            logger.exception(f"Erreur inattendue mise à jour maintenance")
    
    @Slot()
    def print_report(self):
        """Imprime le rapport de maintenance."""
        if not self.maintenance_id or not self.ot_id:
            return
        
        try:
            # Utiliser la fonction existante de la vue OT
            # Cette fonction doit être implémentée pour imprimer le rapport
            # (réutiliser celle d'OTView)
            logger.info(f"Demande d'impression du rapport pour maintenance ID {self.maintenance_id}")
            QMessageBox.information(self, self.tr("Impression"), self.tr("Fonction d'impression à implémenter."))
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Impression"), self.tr("Impossible d'imprimer le rapport:\n%1").replace("%1", str(e)))
            logger.exception(f"Erreur impression rapport maintenance")
    
    def closeEvent(self, event):
        """Gère l'événement de fermeture de la fenêtre."""
        if self.save_button.isEnabled():
            reply = QMessageBox.question(
                self, 
                self.tr("Confirmation"), 
                self.tr("Des modifications non enregistrées seront perdues. Continuer?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()