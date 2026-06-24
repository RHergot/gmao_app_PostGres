# gmao_app/app/ui/views/ot_view.py
"""
Widget pour afficher et gérer la liste des Ordres de Travail (OT).
Avec bouton d'action dynamique pour le statut.
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from PySide6.QtCore import Qt, Signal, Slot, QPoint, QSize, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QLabel, QComboBox, QCheckBox,
    QMenu, QDialog, QApplication, QStyle
)
from PySide6.QtGui import QAction, QPainter, QTextDocument, QTextCursor, QTextTableFormat, \
    QTextCharFormat, QTextLength, QTextBlockFormat, QTextFormat, QPageSize, QPageLayout, QPdfWriter
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from app.core.services.maintenance_service import MaintenanceService, BusinessLogicError, DatabaseError, NotFoundError
from app.core.services.machine_service import MachineService
from app.core.services.stock_service import StockService
from app.core.services.user_service import UserService
from app.core.models.ordre_travail import OrdreTravail
from app.core.models.maintenance import Maintenance
from app.config import app_config, Language  # Import de la configuration centralisée
from app.utils.i18n import (
    translate_type, translate_priority, translate_status, translate_label,
    reverse_translate_type, reverse_translate_priority, reverse_translate_status
)
from app.ui.dialogs.ot_dialog import OTDialog
from app.ui.dialogs.maintenance_report_dialog import MaintenanceReportDialog
from app.ui.views.maintenance_detail_view import MaintenanceDetailView
from app.ui.dialogs.maintenance_detail_dialog import MaintenanceDetailDialog

# Importer les constantes depuis le service de maintenance
from app.core.services.maintenance_service import (
    OT_TYPES, 
    OT_PRIORITES, 
    OT_STATUTS_OUVERT, 
    OT_STATUTS_FERME
)

logger = logging.getLogger(__name__)

class OTView(QWidget):
    
    """Vue pour la gestion des Ordres de Travail."""

    def __init__(self,
                 machine_service: MachineService,
                 maintenance_service: MaintenanceService,
                 stock_service: StockService,
                 user_service: UserService,  # Ajout du user_service
                 parent=None,
                 app_language=None):
        super().__init__(parent)
        
        # Initialiser les statuts avec traduction
        self.ALL_OT_STATUTS = [
            self.tr("Tous"), self.tr("Tous Ouverts"), self.tr("Tous Fermés")
        ] + OT_STATUTS_OUVERT + OT_STATUTS_FERME
        self.machine_service = machine_service
        self.stock_service = stock_service
        self.maintenance_service = maintenance_service
        self.user_service = user_service
        self.app_language = app_language if app_language is not None else getattr(app_config, 'language', None)
        self.current_ots: List[OrdreTravail] = []
        self.machines_map: Dict[int, str] = {}
        self.techniciens_map: Dict[int, str] = {}
        self.current_user_id = 1 # Placeholder!

        logger.debug("Initialisation de OTView...")

        # --- Filtres ---
        self.filter_machine_combo = QComboBox()
        self.filter_type_combo = QComboBox()
        self.filter_statut_combo = QComboBox()
        self.filter_technicien_combo = QComboBox()
        self.filter_priorite_combo = QComboBox()  # Remplace la case à cocher
        
        self.clear_filters_button = QPushButton(translate_label("ClearFilters"))
        self._populate_filter_combos() # Charge listes

        # --- Table ---
        self.table_widget = QTableWidget(self)
        self.setup_table()

        # --- Boutons d'Action ---
        self.add_button = QPushButton(self.tr("➕ Créer OT"))
        self.edit_button = QPushButton(self.tr("✏️ Modifier Détails"))
        # Bouton intelligent pour Start/Pause/Resume
        self.action_srp_button = QPushButton(self.tr("...")) # Texte mis à jour dynamiquement
        self.action_srp_button.setEnabled(False) # Désactivé par défaut
        self.action_srp_button.setToolTip(self.tr("Démarrer, Suspendre ou Reprendre l'OT sélectionné"))

        self.report_button = QPushButton(self.tr("📝 Saisir Rapport"))
        self.cancel_button = QPushButton(self.tr("❌ Annuler OT"))
        self.delete_button = QPushButton(self.tr("🗑️ Supprimer OT"))
        self.refresh_button = QPushButton(self.tr("🔄 Rafraîchir"))

        # --- Layouts ---
        filter_layout1 = QHBoxLayout()
        filter_layout1.addWidget(QLabel(self.tr("Machine:")))
        filter_layout1.addWidget(self.filter_machine_combo, 1); filter_layout1.addWidget(QLabel(self.tr("Type:")))
        filter_layout1.addWidget(self.filter_type_combo); filter_layout1.addWidget(QLabel(self.tr("Statut:")))
        filter_layout1.addWidget(self.filter_statut_combo)
        filter_layout2 = QHBoxLayout()
        filter_layout2.addWidget(QLabel(self.tr("Technicien:")))
        filter_layout2.addWidget(self.filter_technicien_combo)
        filter_layout2.addWidget(QLabel(self.tr("Priorité:")))
        filter_layout2.addWidget(self.filter_priorite_combo)
        filter_layout2.addStretch()
        filter_layout2.addWidget(self.clear_filters_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.action_srp_button) # Bouton Start/Pause/Resume
        
        # Bouton pour les détails complets de maintenance (désactivé pour l'instant)
        self.details_maintenance_button = QPushButton(self.tr("🔍 Détails Maintenance"), self)
        self.details_maintenance_button.setToolTip(self.tr("Voir tous les détails de la maintenance (rapport, coûts, pièces)"))
        self.details_maintenance_button.clicked.connect(self.open_maintenance_details)
        self.details_maintenance_button.setVisible(False)  # Masqué pour l'instant
        # button_layout.addWidget(self.details_maintenance_button)  # Désactivé pour usage ultérieur
        
        # Bouton pour imprimer le rapport de maintenance
        self.print_report_button = QPushButton(self.tr("🖨️ Imprimer Rapport"), self)
        self.print_report_button.setToolTip(self.tr("Imprimer le rapport d'intervention de l'OT sélectionné"))
        self.print_report_button.clicked.connect(self._on_print_maintenance_report)
        button_layout.addWidget(self.print_report_button)

        # Création du bouton d'impression AVANT de l'ajouter au layout
        self.print_button = QPushButton(self.tr("🖨️ Imprimer OT"), self)
        self.print_button.setToolTip(self.tr("Générer un PDF de l'OT sélectionné"))
        self.print_button.clicked.connect(self.print_ot)
        button_layout.addWidget(self.print_button)
        button_layout.addStretch()
        # Ajouter un bouton pour réinitialiser complètement les filtres
        self.reset_all_button = QPushButton(self.tr("🔄 Réinitialiser Tout"), self)
        self.reset_all_button.setToolTip(self.tr("Réinitialiser tous les filtres et forcer un rafraîchissement complet"))
        self.reset_all_button.clicked.connect(self.reset_all_filters)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.reset_all_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(filter_layout1); main_layout.addLayout(filter_layout2)
        main_layout.addWidget(self.table_widget); main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- Connexions ---
        self.connect_signals()

        # --- Init ---
        self.ALL_OT_STATUTS_TRANSLATED = [
            self.tr("All"),
            self.tr("All Open"),
            self.tr("All Closed")
        ] + [self.tr(s) for s in OT_STATUTS_OUVERT] + [self.tr(s) for s in OT_STATUTS_FERME]
        self._update_button_states(); self.refresh_ots()
        logger.debug("OTView initialisée.")


    def setup_table(self):
        """Configure la table des OT."""
        # ... (Identique à la version précédente) ...
        self.table_widget.setColumnCount(9)
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"),
            self.tr("OT Number"),
            self.tr("Machine"),
            self.tr("Type"),
            self.tr("Priority"),
            self.tr("Status"),
            self.tr("Assigned Technician"),
            self.tr("Planned Date"),
            self.tr("Description")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Numéro OT
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)    # Machine
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Priorité
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Statut
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)    # Technicien
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Date Prévue
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)         # Description
        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 7; self._sort_order = Qt.SortOrder.AscendingOrder
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)

    def _populate_filter_combos(self):
        """Remplit les combobox de filtre avec les données nécessaires."""
        error_msg = ""
        try:
            # Charger les maps nécessaires
            self._load_machines_map()
            self._load_techniciens_map()
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur chargement données filtres: {e}", exc_info=True)

        # Remplir le filtre des machines
        self.filter_machine_combo.clear()
        self.filter_machine_combo.addItem(translate_label("All"), None)
        
        # Trier les machines par nom
        sorted_machines = sorted(self.machines_map.items(), key=lambda item: item[1])
        for m_id, m_nom in sorted_machines:
            self.filter_machine_combo.addItem(m_nom, m_id)

        # Remplir le filtre des types de maintenance - CORRIGÉ
        self.filter_type_combo.clear()
        self.filter_type_combo.addItem(translate_label("All"), None)
        
        # Ajouter les types de maintenance avec traduction, mais stocker la valeur originale
        for ot_type in OT_TYPES:
            translated_type = self._convert_db_to_ui_value(ot_type, "type")
            self.filter_type_combo.addItem(translated_type, ot_type)  # Stocker la valeur DB originale

        # Configurer le filtre de statut - CORRIGÉ
        self.filter_statut_combo.clear()
        
        # Ajouter les statuts avec traduction et les bonnes données
        # Groupes spéciaux
        self.filter_statut_combo.addItem(translate_label("All"), "")
        self.filter_statut_combo.addItem(translate_label("AllOpen"), "Tous Ouverts")
        self.filter_statut_combo.addItem(translate_label("AllClosed"), "Tous Fermés")
        
        # Ajouter les statuts ouverts avec traduction
        for statut in OT_STATUTS_OUVERT:
            translated_statut = self._convert_db_to_ui_value(statut, "status")
            self.filter_statut_combo.addItem(translated_statut, statut)
            
        # Ajouter les statuts fermés avec traduction
        for statut in OT_STATUTS_FERME:
            translated_statut = self._convert_db_to_ui_value(statut, "status")
            self.filter_statut_combo.addItem(translated_statut, statut)
        
        # Définir la valeur par défaut à "Tous Ouverts"
        index_all_open = self.filter_statut_combo.findData("Tous Ouverts")
        if index_all_open >= 0:
            self.filter_statut_combo.setCurrentIndex(index_all_open)
        else:
            # Fallback sur le premier élément
            self.filter_statut_combo.setCurrentIndex(0)

        # Configurer le filtre de technicien
        self.filter_technicien_combo.clear()
        self.filter_technicien_combo.addItem(translate_label("All"), None)
        self.filter_technicien_combo.addItem(translate_label("Unassigned"), -1)
        
        # Trier les techniciens par nom
        sorted_techs = sorted(self.techniciens_map.items(), key=lambda item: item[1])
        for t_id, t_nom in sorted_techs:
            self.filter_technicien_combo.addItem(t_nom, t_id)

        # Configurer le filtre de priorité - NOUVEAU
        self.filter_priorite_combo.clear()
        self.filter_priorite_combo.addItem(translate_label("All"), None)
        
        # Ajouter les priorités avec traduction, mais stocker la valeur originale
        for priorite in OT_PRIORITES:
            translated_priorite = self._convert_db_to_ui_value(priorite, "priority")
            self.filter_priorite_combo.addItem(translated_priorite, priorite)  # Stocker la valeur DB originale

        # Afficher un message d'erreur s'il y en a un
        if error_msg:
            QMessageBox.warning(
                self, 
                self.tr("Erreur Chargement Filtres"), 
                self.tr("Certaines données n'ont pas pu être chargées :") + f"\n{error_msg}"
            )


    def _load_machines_map(self):
        """ Charge map ID->Nom machines. """
        # ... (Identique à la version précédente) ...
        try:
            machines = self.machine_service.get_all_machines(sort_by="nom")
            self.machines_map = {m.id_machine: m.nom + (f" (S/N:{m.serial})" if m.serial else "") for m in machines if m.id_machine is not None}
        except Exception as e:
            logger.error(f"Erreur récupération machines map: {e}")
            self.machines_map = {}
            raise

    def _load_techniciens_map(self):
        """ Charge map ID->Nom techniciens actifs. """
        # ... (Identique à la version précédente) ...
        try:
            techs = self.maintenance_service.get_all_techniciens(include_inactive=False)
            self.techniciens_map = {t.id_technicien: t.nom_complet for t in techs if t.id_technicien is not None}
        except Exception as e:
            logger.error(f"Erreur récupération techniciens map: {e}")
            self.techniciens_map = {}
            raise

    def connect_signals(self):
        """ Connecte signaux/slots. """
        self.add_button.clicked.connect(self.add_ot)
        self.edit_button.clicked.connect(self.edit_ot)
        self.delete_button.clicked.connect(self.delete_ot)
        self.refresh_button.clicked.connect(self.refresh_ots)
        self.report_button.clicked.connect(self.record_maintenance_report)
        self.cancel_button.clicked.connect(self.cancel_selected_ot) # Connecter bouton Annuler

        # Bouton intelligent Start/Pause/Resume
        self.action_srp_button.clicked.connect(self.handle_srp_button_click)

        # Table et Filtres
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_ot)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)
        # Filtres
        self.filter_machine_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_type_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_statut_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_technicien_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_priorite_combo.currentIndexChanged.connect(self.apply_filters)  # Remplace stateChanged
        self.clear_filters_button.clicked.connect(self.clear_filters)


    def _update_button_states(self):
        """ Met à jour état TOUS les boutons selon sélection et statut OT. """
        selected_id = self._get_selected_ot_id()
        has_selection = selected_id is not None
        # Désactiver tout par défaut si pas de sélection
        can_edit_details = False
        can_delete = False
        can_report = False
        can_srp_action = None # Garde l'action possible: "start", "pause", "resume", None
        can_cancel = False

        if has_selection:
             ot = next((ot for ot in self.current_ots if ot.id_ot == selected_id), None)
             if ot:
                 current_status = ot.statut
                 # Règles d'activation
                 can_edit_details = current_status in OT_STATUTS_OUVERT
                 can_delete = current_status in ["Créé", "Planifié", "Annule"]
                 can_report = current_status in ["EnCours", "Suspendu", "Pret"]
                 can_cancel = current_status in OT_STATUTS_OUVERT

                 # Logique pour le bouton intelligent Start/Pause/Resume
                 if current_status in ["Pret", "Planifié", "Créé"]:
                     can_srp_action = "start"
                 elif current_status == "EnCours":
                     can_srp_action = "pause"
                 elif current_status == "Suspendu":
                     can_srp_action = "resume"
                 # else: None (bouton désactivé)

        # Mettre à jour les boutons
        self.edit_button.setEnabled(has_selection and can_edit_details)
        self.delete_button.setEnabled(has_selection and can_delete)
        self.report_button.setEnabled(has_selection and can_report)
        self.cancel_button.setEnabled(has_selection and can_cancel)

        # Mettre à jour le bouton intelligent
        if can_srp_action == "start":
             self.action_srp_button.setText("▶️ Démarrer")
             self.action_srp_button.setEnabled(True)
        elif can_srp_action == "pause":
             self.action_srp_button.setText("⏸️ Suspendre")
             self.action_srp_button.setEnabled(True)
        elif can_srp_action == "resume":
             self.action_srp_button.setText("▶️ Reprendre")
             self.action_srp_button.setEnabled(True)
        else:
             self.action_srp_button.setText("...") # Ou vide
             self.action_srp_button.setEnabled(False)


    def _get_selected_ot_id(self) -> Optional[int]:
        """ Retourne ID OT sélectionné. """
        # ... (Identique) ...
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        first_row_index = selected_rows[0].row()
        id_item = self.table_widget.item(first_row_index, 0)
        if id_item:
            try: return int(id_item.data(Qt.ItemDataRole.UserRole))
            except (ValueError, TypeError) as e: logger.error(f"ID invalide L{first_row_index}: {e}"); return None
        return None

    # ... (refresh_data, refresh_ots, populate_table, sort_table, _get_sort_column_name) ...
    # S'assurer que populate_table utilise les bonnes maps _loadées par refresh_ots

    # --- Méthodes pour les Filtres ---
    @Slot()
    def apply_filters(self): self.refresh_ots()

    def _get_current_filters(self) -> Dict[str, Any]:
        """ Construit le dict de filtres avec conversion UI->DB. """
        try:
            logger.debug("Début construction des filtres OT...")
            filters = {}
            
            # Filtre par machine
            machine_id = self.filter_machine_combo.currentData()
            if machine_id is not None: 
                filters['machine_id'] = machine_id
                logger.debug(f"Filtre machine_id ajouté: {machine_id}")
            
            # Filtre par type - CORRIGÉ avec data() de la combobox
            type_data = self.filter_type_combo.currentData()
            type_text = self.filter_type_combo.currentText()
            if type_data is not None:
                filters['type'] = type_data
                logger.debug(f"Filtre type ajouté: '{type_text}' -> '{type_data}'")
            
            # Filtre par statut - CORRIGÉ avec data() de la combobox
            statut_data = self.filter_statut_combo.currentData()
            statut_text = self.filter_statut_combo.currentText()
            logger.debug(f"Statut sélectionné - Data: '{statut_data}', Text: '{statut_text}'")
            
            if statut_data:  # Si data n'est pas None ou vide
                if statut_data == "Tous Ouverts":
                    logger.debug(f"Ajout filtre statut__in pour statuts ouverts: {OT_STATUTS_OUVERT}")
                    filters['statut__in'] = OT_STATUTS_OUVERT.copy()
                elif statut_data == "Tous Fermés":
                    logger.debug(f"Ajout filtre statut__in pour statuts fermés: {OT_STATUTS_FERME}")
                    filters['statut__in'] = OT_STATUTS_FERME.copy()
                else:
                    # Statut individuel - utiliser directement la data (qui est déjà en français)
                    filters['statut'] = statut_data
                    logger.debug(f"Filtre statut ajouté: '{statut_text}' -> '{statut_data}'")
            else:
                logger.debug("Aucun filtre de statut appliqué (data = vide)")
            
            # Traitement du technicien (inchangé)
            tech_id = self.filter_technicien_combo.currentData()
            if tech_id is not None:
                if tech_id == -1:  # Non assigné
                    logger.debug("Ajout filtre technicien_assigne_id = NULL (non assigné)")
                    filters['technicien_assigne_id'] = None
                else:
                    logger.debug(f"Ajout filtre technicien_assigne_id: {tech_id}")
                    filters['technicien_assigne_id'] = tech_id
            
            # Filtre de priorité - NOUVEAU remplace le filtre urgence
            priorite_data = self.filter_priorite_combo.currentData()
            priorite_text = self.filter_priorite_combo.currentText()
            if priorite_data is not None:
                filters['priorite'] = priorite_data
                logger.debug(f"Filtre priorité ajouté: '{priorite_text}' -> '{priorite_data}'")
                
            logger.debug(f"Filtres OT finaux: {filters}")
            return filters
        except Exception as e:
            logger.exception(f"Erreur lors de la construction des filtres: {e}")
            # En cas d'erreur, retourner un dictionnaire vide pour éviter de bloquer l'application
            return {}

    @Slot()
    def clear_filters(self):
        """ Réinitialise les filtres. """
        logger.debug("Réinitialisation des filtres OT...")
        self.filter_machine_combo.setCurrentIndex(0)
        self.filter_type_combo.setCurrentIndex(0)
        
        # Trouver l'index de "Tous Ouverts" ou sa traduction
        tous_ouverts_index = -1
        for i in range(self.filter_statut_combo.count()):
            text = self.filter_statut_combo.itemText(i)
            if text == "Tous Ouverts" or text == self.tr("All Open"):
                tous_ouverts_index = i
                break
        
        if tous_ouverts_index >= 0:
            self.filter_statut_combo.setCurrentIndex(tous_ouverts_index)
        else:
            # Fallback au premier élément si "Tous Ouverts" n'est pas trouvé
            self.filter_statut_combo.setCurrentIndex(0)
            
        self.filter_technicien_combo.setCurrentIndex(0)
        self.filter_priorite_combo.setCurrentIndex(0)  # Remplace filter_urgence_check
        
        logger.debug("Filtres réinitialisés, rafraîchissement des OTs...")
        self.refresh_ots()
        
    @Slot()
    def reset_all_filters(self):
        """ Réinitialise complètement les filtres et force un rafraîchissement complet. """
        logger.debug("Réinitialisation complète des filtres et de la vue OT...")
        
        # Réinitialiser tous les filtres à leur valeur par défaut
        self.filter_machine_combo.setCurrentIndex(0)
        self.filter_type_combo.setCurrentIndex(0)
        
        # Sélectionner "Tous" pour le statut
        tous_index = -1
        for i in range(self.filter_statut_combo.count()):
            text = self.filter_statut_combo.itemText(i)
            if text == "Tous" or text == self.tr("All"):
                tous_index = i
                break
        
        if tous_index >= 0:
            self.filter_statut_combo.setCurrentIndex(tous_index)
        else:
            self.filter_statut_combo.setCurrentIndex(0)
            
        self.filter_technicien_combo.setCurrentIndex(0)
        self.filter_priorite_combo.setCurrentIndex(0)  # Remplace filter_urgence_check
        
        # Forcer un rafraîchissement complet
        logger.info("Forcer un rafraîchissement complet de la liste des OTs...")
        try:
            # Récupérer tous les OT sans filtre
            self.current_ots = self.maintenance_service.get_all_ots()
            self.populate_table(self.current_ots)
            QMessageBox.information(self, self.tr("Rafraîchissement"), 
                                   self.tr("%1 OTs affichés. Tous les filtres ont été réinitialisés.").replace('%1', str(len(self.current_ots))))
            logger.info(f"{len(self.current_ots)} OTs affichés après réinitialisation complète.")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), 
                               self.tr("Impossible de rafraîchir la liste des OTs:\n%1").replace('%1', str(e)))
            logger.exception("Erreur lors du rafraîchissement complet des OTs.")
            # Essayer un rafraîchissement normal comme fallback
            self.refresh_ots()


    # --- Slots Actions CRUD ---
    @Slot()
    def add_ot(self):
         """ Ouvre dialogue pour créer OT. """
         # ... (Code identique) ...
         logger.debug("Ouverture dialogue ajout OT.")
         dialog = OTDialog(
             machine_service=self.machine_service,
             maintenance_service=self.maintenance_service,
             current_user_id=self.current_user_id,
             parent=self)
         if dialog.exec() == QDialog.DialogCode.Accepted: # Import QDialog nécessaire
             ot_data = dialog.get_ot_data()
             try:
                 logger.info(f"Tentative création OT via service...")
                 if ot_data.get("utilisateur_createur_id") is None: # Double check
                      raise BusinessLogicError("ID créateur manquant.")
                 new_ot = self.maintenance_service.create_ot(ot_data)
                 QMessageBox.information(self, "Succès", f"OT '{new_ot.numero_ot or new_ot.id_ot}' créé.")
                 self.refresh_ots()
             except (BusinessLogicError, DatabaseError, NotFoundError) as e: QMessageBox.warning(self, "Erreur", f"{e}"); logger.error(f"{e}")
             except Exception as e: QMessageBox.critical(self, "Erreur", f"{e}"); logger.exception("Err.")

    @Slot()
    def edit_ot(self):
        """ Ouvre dialogue pour modifier OT. """
        # ... (Code identique) ...
        ot_id = self._get_selected_ot_id()
        if ot_id is None:
             if self.sender() == self.edit_button: QMessageBox.information(self, self.tr("Action"), self.tr("Sélectionnez un OT."))
             return
        try:
            ot_to_edit = self.maintenance_service.get_ot_by_id(ot_id)
            if not ot_to_edit: QMessageBox.warning(self, self.tr("Erreur"), self.tr("OT n'existe plus.")); self.refresh_ots(); return
            # Logic pour lecture seule déplacée dans le dialogue

            dialog = OTDialog( # Passe aussi user ID (même si pas modif)
                 machine_service=self.machine_service, maintenance_service=self.maintenance_service,
                 ot=ot_to_edit, current_user_id=self.current_user_id, parent=self,
                 app_language=self.app_language)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                 update_data = dialog.get_ot_data()
                 update_data.pop('id_ot', None); update_data.pop('utilisateur_createur_id', None)
                 try:
                     logger.info(f"Tentative màj OT ID {ot_id}...")
                     updated = self.maintenance_service.update_ot(ot_id, update_data) # Appel service
                     QMessageBox.information(self, "Succès", f"OT '{updated.numero_ot or ot_id}' mis à jour.")
                     self.refresh_ots()
                 except (BusinessLogicError, DatabaseError, NotFoundError) as e: QMessageBox.warning(self, "Erreur", f"{e}"); logger.error(f"{e}"); self.refresh_ots()
                 except Exception as e: QMessageBox.critical(self, "Erreur", f"{e}"); logger.exception(f"Err màj {ot_id}")
        except (BusinessLogicError, NotFoundError) as e: QMessageBox.warning(self, self.tr("Erreur"), str(e)); self.refresh_ots()
        except Exception as e: QMessageBox.critical(self, self.tr("Erreur"), str(e)); logger.exception(f"Err avant édit {ot_id}")

    @Slot()
    def delete_ot(self):
        """ Supprime OT sélectionné (si statut le permet). """
        # ... (Code identique, appelle service delete_ot) ...
        ot_id = self._get_selected_ot_id();
        if ot_id is None: return
        ot = self.maintenance_service.get_ot_by_id(ot_id)
        if ot and ot.statut not in ["Créé", "Planifié", "Annule"]: # Règle d'ici
             QMessageBox.warning(self, self.tr("Impossible"), self.tr("Ne peut supprimer OT '%1'.").replace('%1', str(ot.statut)))
             return
        num = ot.numero_ot if ot else f"ID {ot_id}"
        if QMessageBox.question(self, self.tr("Confirmation"), self.tr("Supprimer OT '%1'?").replace('%1', str(num))) == QMessageBox.StandardButton.Yes:
            try:
                if self.maintenance_service.delete_ot(ot_id):
                     QMessageBox.information(self, self.tr("Succès"), self.tr("OT '%1' supprimé.").replace('%1', str(num))); self.refresh_ots()
            except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), str(e)); logger.error(f"Err delete {ot_id}: {e}"); self.refresh_ots()

    @Slot()
    def cancel_selected_ot(self):
        """ Appelle la fonction pour annuler l'OT sélectionné. """
        ot_id = self._get_selected_ot_id()
        if ot_id is None:
            QMessageBox.warning(self, self.tr("Action"), self.tr("Sélectionnez un OT à annuler."))
            return
        self.change_ot_status(ot_id, "Annule")

    @Slot()
    def handle_srp_button_click(self):
        """ Gère le clic sur le bouton Start/Pause/Resume. """
        ot_id = self._get_selected_ot_id()
        if ot_id is None: QMessageBox.warning(self, self.tr("Action"), self.tr("Sélectionnez un OT.")); return

        ot = next((o for o in self.current_ots if o.id_ot == ot_id), None)
        if not ot: QMessageBox.warning(self, self.tr("Erreur"), self.tr("OT non trouvé.")); return

        current_status = ot.statut
        new_status = None
        if current_status in ["Pret", "Planifié", "Créé"]: new_status = "EnCours" # Action = Démarrer
        elif current_status == "EnCours": new_status = "Suspendu" # Action = Suspendre
        elif current_status == "Suspendu": new_status = "EnCours" # Action = Reprendre

        if new_status:
            self.change_ot_status(ot_id, new_status)
        else:
            logger.warning(f"Aucune action SRP définie pour statut '{current_status}' de l'OT {ot_id}.")


    # --- Méthode pour enregistrer maintenance (INCHANGÉE - Placeholder) ---
    # Dans OTView

    # Dans OTView

    @Slot()
    def record_maintenance_report(self):
        """ Ouvre dialogue pour saisir le rapport de maintenance pour l'OT sélectionné. """
        ot_id = self._get_selected_ot_id()
        if ot_id is None:
            QMessageBox.information(self, "Action Requise", "Sélectionnez un OT pour saisir le rapport.")
            return

        try:
            ot = self.maintenance_service.get_ot_by_id(ot_id)
            if not ot:
                raise NotFoundError(f"OT ID {ot_id} non trouvé pour rapport.")

            # Vérifier si une maintenance existe déjà
            existing_maintenance = self.maintenance_service.get_maintenance_for_ot(ot_id)
            if existing_maintenance:
                # Si un rapport existe, appeler la méthode d'édition dédiée
                logger.debug(f"Rapport existant trouvé (ID: {existing_maintenance.id_maintenance}), ouverture pour modification.")
                self.edit_maintenance_report(existing_maintenance, ot)
                return # Modification gérée par edit_maintenance_report

            # Si aucun rapport n'existe, continuer pour en créer un nouveau
            # REMOVED: Check for OT status - Allow creation regardless of status
            # if ot.statut not in ["EnCours", "Suspendu", "Pret"]:
            #     QMessageBox.warning(self, "Action Impossible", f"Impossible de saisir un rapport pour un OT avec le statut '{ot.statut}'.")
            #     return

            logger.debug(f"Ouverture dialogue pour NOUVEAU rapport maintenance pour OT ID {ot_id}")
            # --- Appel du vrai dialogue ---
            nom_machine_ot = self.machines_map.get(ot.machine_id, "Machine Inconnue")
            report_dialog = MaintenanceReportDialog(
                maintenance_service=self.maintenance_service,
                stock_service=self.stock_service, # <--- VÉRIFIER/AJOUTER CETTE LIGNE
                ordre_travail=ot,
                nom_machine=nom_machine_ot, # <-- Passer le nom de la machine récupéré
                current_user_id=self.current_user_id,
                parent=self
            )

            if report_dialog.exec() == QDialog.DialogCode.Accepted: # <-- Importer QDialog dans OTView si ce n'est fait!
                maintenance_data = report_dialog.get_maintenance_data()
                try:
                    logger.info(f"Tentative enregistrement rapport pour OT {ot_id}")
                    # Appel au service pour enregistrer
                    new_maintenance = self.maintenance_service.record_maintenance(maintenance_data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Rapport de maintenance (ID: %1) enregistré pour l'OT %2.\nStatut de l'OT mis à jour.").replace('%1', str(new_maintenance.id_maintenance)).replace('%2', str(ot_id)))
                    self.refresh_ots() # Rafraîchit la liste (le statut de l'OT a changé)
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                    QMessageBox.warning(self, "Erreur Enregistrement", f"Impossible enregistrer le rapport:\n{e}")
                    logger.error(f"Échec enregistrement rapport OT {ot_id}: {e}")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur Inattendue", f"Erreur lors de l'enregistrement:\n{e}")
                    logger.exception(f"Erreur inattendue enregistrement rapport OT {ot_id}")
            else:
                logger.info(f"Saisie rapport annulée pour OT {ot_id}")

        except (BusinessLogicError, NotFoundError) as e:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de préparer le rapport:\n%1").replace('%1', str(e)))
            logger.error(f"Erreur pré-rapport OT ID {ot_id}: {e}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n%1").replace('%1', str(e)))
            logger.exception(f"Erreur inattendue bouton rapport OT ID {ot_id}.")

    # --- Menu Contextuel ---
    @Slot(QPoint)
    def show_context_menu(self, pos: QPoint):
        item = self.table_widget.itemAt(pos)
        if not item: return
        row_index = item.row()
        if (row_index != self.table_widget.currentRow()): self.table_widget.selectRow(row_index)
        ot_id = self._get_selected_ot_id();
        if ot_id is None: return
        ot = next((o for o in self.current_ots if o.id_ot == ot_id), None)
        if ot is None: return

        menu = QMenu(self)
        current_status = ot.statut

        action_edit = QAction(self.tr("✏️ Modifier Détails..."), self)
        action_duplicate = QAction(self.tr("➕ Dupliquer OT..."), self) # <- Nouvelle Action
        action_start = QAction(self.tr("▶️ Démarrer"), self)
        action_pause = QAction(self.tr("⏸️ Suspendre"), self)
        action_resume = QAction(self.tr("▶️ Reprendre"), self)
        action_report = QAction(self.tr("📝 Saisir Rapport..."), self)
        action_view_report = QAction(self.tr("👁 Voir Rapport..."), self)
        action_cancel = QAction(self.tr("❌ Annuler OT"), self)
        action_delete = QAction(self.tr("🗑️ Supprimer OT"), self)
        action_details = QAction(self.tr("🔍 Détails Maintenance..."), self)
        
        # Actions d'archivage
        action_archive = QAction(self.tr("📁 Archiver"), self)
        action_unarchive = QAction(self.tr("📂 Désarchiver"), self)

        # --- Connexion des Actions ---
        action_edit.triggered.connect(self.edit_ot)
        action_duplicate.triggered.connect(lambda checked=False, otid=ot_id: self.duplicate_ot(otid)) # <- Connexion
        action_start.triggered.connect(lambda checked=False, otid=ot_id: self.change_ot_status(otid, "EnCours"))
        action_pause.triggered.connect(lambda checked=False, otid=ot_id: self.change_ot_status(otid, "Suspendu"))
        action_resume.triggered.connect(lambda checked=False, otid=ot_id: self.change_ot_status(otid, "EnCours")) # Reprendre -> EnCours
        action_report.triggered.connect(self.record_maintenance_report)
        action_view_report.triggered.connect(lambda checked=False, otid=ot_id: self.view_maintenance_report(otid))
        action_cancel.triggered.connect(lambda checked=False, otid=ot_id: self.change_ot_status(otid, "Annule"))
        action_delete.triggered.connect(self.delete_ot)
        action_details.triggered.connect(lambda checked=False, otid=ot_id: self.open_maintenance_details_dialog(otid))
        
        # Connexions des actions d'archivage
        action_archive.triggered.connect(lambda checked=False, otid=ot_id: self.archive_ot(otid))
        action_unarchive.triggered.connect(lambda checked=False, otid=ot_id: self.unarchive_ot(otid))

        # --- Activation/Désactivation des Actions ---
        action_edit.setEnabled(current_status in OT_STATUTS_OUVERT)
        action_duplicate.setEnabled(True) # Toujours possible
        action_start.setEnabled(current_status in ["Pret", "Planifié", "Créé"])
        action_pause.setEnabled(current_status == "EnCours")
        action_resume.setEnabled(current_status == "Suspendu")
        action_report.setEnabled(current_status in ["EnCours", "Suspendu", "Pret"])
        action_view_report.setEnabled(current_status in OT_STATUTS_FERME and current_status != "Annule")
        action_cancel.setEnabled(current_status in OT_STATUTS_OUVERT)
        action_delete.setEnabled(current_status in ["Créé", "Planifié", "Annule"])
        
        # Activation des actions d'archivage
        action_archive.setEnabled(current_status == "Terminé")  # Seuls les OT terminés peuvent être archivés
        action_unarchive.setEnabled(current_status == "Archivé")  # Seuls les OT archivés peuvent être désarchivés

        # --- Ajout des Actions au Menu ---
        menu.addAction(action_edit)
        menu.addAction(action_duplicate) 
        menu.addSeparator()
        menu.addAction(action_start)
        menu.addAction(action_pause)
        menu.addAction(action_resume)
        menu.addSeparator()
        menu.addAction(action_report)
        menu.addAction(action_view_report)
        menu.addSeparator()
        menu.addAction(action_cancel)
        menu.addAction(action_delete)
        menu.addSeparator()
        menu.addAction(action_archive)
        menu.addAction(action_unarchive)
        menu.addSeparator()
        menu.addAction(action_details)

        menu.exec(self.table_widget.mapToGlobal(pos))

    # --- Méthode commune pour changer le statut (appelée par boutons et menu) ---
    @Slot(int, str)
    def change_ot_status(self, ot_id: int, new_status: str):
        """ Appelle le service pour changer le statut de l'OT. """
        logger.info(f"Demande changement statut pour OT {ot_id} vers '{new_status}'")
        try:
            if new_status == "Annule":
                 reply = QMessageBox.question(self, self.tr("Confirmation"), self.tr("Confirmer l'annulation de l'OT %1?").replace('%1', str(ot_id)), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
                 if reply != QMessageBox.StandardButton.Yes: logger.info("Annulation OT annulée."); return

            updated_ot = self.maintenance_service.update_ot_status(ot_id, new_status) # Appelle la méthode du service
            QMessageBox.information(self, "Succès", f"Statut de l'OT {updated_ot.numero_ot or ot_id} mis à jour vers '{new_status}'.")
            self.refresh_ots()
        except (BusinessLogicError, DatabaseError, NotFoundError) as e: QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible changer statut:\n%1").replace('%1', str(e))); logger.error(f"Erreur changement statut OT {ot_id}: {e}"); self.refresh_ots()
        except Exception as e: QMessageBox.critical(self, self.tr("Erreur"), str(e)); logger.exception(f"Erreur changement statut OT {ot_id}.")

    # REMOVED: view_maintenance_report method
    # def view_maintenance_report(self, ot_id: int):
    #     ...

    # Dans la classe OTView

    @Slot(int) # Indiquer que c'est un slot Qt connecté à un signal avec un int
    def sort_table(self, logical_index: int):
        """ Slot appelé quand l'utilisateur clique sur un en-tête de colonne. """
        # Détermine la nouvelle colonne et l'ordre de tri
        if self._sort_column == logical_index:
             # Inverse l'ordre si on clique sur la même colonne
             self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
             # Nouvelle colonne, tri ascendant par défaut
             self._sort_column = logical_index
             self._sort_order = Qt.SortOrder.AscendingOrder

        # Rafraîchir les données pour appliquer le nouveau tri (via service/repo)
        self.refresh_ots()

    def _get_sort_column_name(self) -> str:
        """ Traduit l'index logique de colonne en nom de champ pour le tri DB/Service. """
        # S'assurer que cette map est correcte et correspond aux colonnes
        column_map = {
            1: "numero_ot", 2: "machine_id", 3: "type", 4: "priorite", 5: "statut",
            6: "technicien_assigne_id", 7: "date_prevue", 8: "description"
            # L'ID (col 0) n'est pas triable via UI car caché
        }
        return column_map.get(self._sort_column, "date_prevue") # Défaut date prévue

    # ... (reste de la classe OTView) ...

    # Dans la classe OTView

    # --- Rafraîchissement ---
    @Slot() # Slot car connecté à un signal de bouton
    def refresh_ots(self):
        """ Recharge les OT en appliquant les filtres et le tri actuels. """
        logger.info("Rafraîchissement liste des OTs...")
        
        # Essayer d'obtenir les filtres actuels, avec un fallback sur un dict vide en cas d'erreur
        try:
            filters = self._get_current_filters()
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des filtres: {e}")
            filters = {}
        
        # Essayer d'obtenir la colonne de tri, avec un fallback sur "date_prevue" en cas d'erreur
        try:
            sort_column_name = self._get_sort_column_name()
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération de la colonne de tri: {e}")
            sort_column_name = "date_prevue"
        
        # Déterminer l'ordre de tri
        sort_desc = self._sort_order == Qt.SortOrder.DescendingOrder
        
        logger.debug(f"Filtres appliqués: {filters}, tri: {sort_column_name} ({'DESC' if sort_desc else 'ASC'})")

        # Recharger les maps car elles ont pu changer
        try: 
            self._load_machines_map()
            logger.debug(f"Map machines chargée: {len(self.machines_map)} machines")
        except Exception as e: 
            logger.error(f"Erreur recharge map machines: {e}")
            # Créer un dictionnaire vide si la map n'existe pas encore
            if not hasattr(self, 'machines_map'):
                self.machines_map = {}
        
        try: 
            self._load_techniciens_map()
            logger.debug(f"Map techniciens chargée: {len(self.techniciens_map)} techniciens")
        except Exception as e: 
            logger.error(f"Erreur recharge map techniciens: {e}")
            # Créer un dictionnaire vide si la map n'existe pas encore
            if not hasattr(self, 'techniciens_map'):
                self.techniciens_map = {}

        try:
            # Utiliser get_all avec filtres et tri
            logger.debug("Appel à maintenance_service.get_all_ots()...")
            
            # Essayer d'abord sans aucun filtre si les filtres sont trop complexes
            if len(filters) > 3:  # Si plus de 3 filtres, essayer d'abord sans filtre
                logger.debug("Trop de filtres, essai sans filtre d'abord...")
                try:
                    # Essayer de récupérer tous les OTs sans filtre
                    all_ots = self.maintenance_service.get_all_ots(filters=None, sort_by=sort_column_name, sort_desc=sort_desc)
                    logger.debug(f"Récupération sans filtre réussie: {len(all_ots)} OTs trouvés")
                    
                    # Si la récupération sans filtre a réussi mais n'a retourné aucun OT, continuer avec les filtres
                    if len(all_ots) == 0:
                        logger.debug("Aucun OT trouvé sans filtre, essai avec les filtres...")
                    else:
                        # Si des OTs ont été trouvés sans filtre, utiliser ce résultat
                        self.current_ots = all_ots
                        self.populate_table(self.current_ots)
                        logger.info(f"{len(self.current_ots)} OTs affichés (sans filtre).")
                        return
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération sans filtre: {e}")
                    # Continuer avec les filtres
            
            # Récupérer les OTs avec les filtres
            self.current_ots = self.maintenance_service.get_all_ots(
                filters=filters,
                sort_by=sort_column_name,
                sort_desc=sort_desc
            )
            logger.debug(f"Résultat get_all_ots avec filtres: {len(self.current_ots)} OTs récupérés")
            
            # Si aucun OT n'est trouvé avec les filtres, essayer sans filtre
            if len(self.current_ots) == 0 and filters:
                logger.debug("Aucun OT trouvé avec les filtres, essai sans filtre...")
                self.current_ots = self.maintenance_service.get_all_ots(filters=None, sort_by=sort_column_name, sort_desc=sort_desc)
                logger.debug(f"Récupération sans filtre: {len(self.current_ots)} OTs trouvés")
                
                # Si des OTs sont trouvés sans filtre, afficher un message
                if len(self.current_ots) > 0:
                    QMessageBox.information(self, self.tr("Aucun résultat avec filtres"), 
                                         self.tr("Aucun OT ne correspond aux filtres sélectionnés.\nTous les OTs sont affichés."))
            
            # Appeler fonction séparée pour peupler le tableau
            self.populate_table(self.current_ots)
            logger.info(f"{len(self.current_ots)} OTs affichés.")

        except BusinessLogicError as e:
            logger.error(f"Erreur métier chargement OTs: {e}")
            # Essayer sans filtre en cas d'erreur
            try:
                logger.debug("Essai de récupération sans filtre après erreur...")
                self.current_ots = self.maintenance_service.get_all_ots(filters=None, sort_by="date_prevue", sort_desc=False)
                self.populate_table(self.current_ots)
                logger.info(f"{len(self.current_ots)} OTs affichés après récupération sans filtre.")
                QMessageBox.warning(self, self.tr("Erreur avec filtres"), 
                                 self.tr("Impossible de charger les OTs avec les filtres sélectionnés:\n%1\n\nTous les OTs sont affichés.").replace('%1', str(e)))
            except Exception as e2:
                logger.exception(f"Erreur lors de la récupération sans filtre après erreur: {e2}")
                QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les OTs :\n%1").replace('%1', str(e)))
                # Vider la table en cas d'échec total
                self.current_ots = []
                self.populate_table(self.current_ots)
        except Exception as e:
            logger.exception(f"Erreur inattendue chargement/affichage OTs: {e}")
            # Essayer sans filtre en cas d'erreur
            try:
                logger.debug("Essai de récupération sans filtre après erreur inattendue...")
                self.current_ots = self.maintenance_service.get_all_ots(filters=None, sort_by="date_prevue", sort_desc=False)
                self.populate_table(self.current_ots)
                logger.info(f"{len(self.current_ots)} OTs affichés après récupération sans filtre.")
                QMessageBox.warning(self, self.tr("Erreur inattendue"), 
                                 self.tr("Une erreur est survenue lors du chargement des OTs :\n%1\n\nTous les OTs sont affichés.").replace('%1', str(e)))
            except Exception as e2:
                logger.exception(f"Erreur lors de la récupération sans filtre après erreur inattendue: {e2}")
                QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur :\n%1").replace('%1', str(e)))
                # Vider la table en cas d'échec total
                self.current_ots = []
                self.populate_table(self.current_ots)

    
    # Dans la classe OTView

    def edit_maintenance_report(self, maintenance: Maintenance, ot: OrdreTravail):
        """ Ouvre le dialogue de rapport de maintenance en mode édition. """
        logger.debug(f"Ouverture dialogue modification rapport (ID: {maintenance.id_maintenance}) pour OT ID {ot.id_ot}")
        nom_machine_ot = self.machines_map.get(ot.machine_id, "Machine Inconnue")

        report_dialog = MaintenanceReportDialog(
            maintenance_service=self.maintenance_service,
            stock_service=self.stock_service,
            ordre_travail=ot,
            nom_machine=nom_machine_ot,
            current_user_id=self.current_user_id,
            maintenance_to_edit=maintenance, # Passer l'objet à éditer
            parent=self
        )

        if report_dialog.exec() == QDialog.DialogCode.Accepted:
            maintenance_data = report_dialog.get_maintenance_data()
            try:
                logger.info(f"Tentative de mise à jour du rapport (ID: {maintenance.id_maintenance}) pour OT {ot.id_ot}")
                # Assurez-vous que l'ID de maintenance est inclus pour la mise à jour
                maintenance_data['id_maintenance'] = maintenance.id_maintenance
                # Note: Assuming update_maintenance exists and takes a dict
                updated_maintenance = self.maintenance_service.update_maintenance(maintenance_data)
                QMessageBox.information(self, self.tr("Succès"), self.tr("Rapport de maintenance (ID: %1) mis à jour pour l'OT %2.").replace('%1', str(updated_maintenance.id_maintenance)).replace('%2', str(ot.id_ot)))
                self.refresh_ots() # Rafraîchir pour voir les éventuels changements (ex: statut OT)
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                QMessageBox.warning(self, self.tr("Erreur Mise à Jour"), self.tr("Impossible mettre à jour le rapport:\n%1").replace('%1', str(e)))
                logger.error(f"Échec màj rapport {maintenance.id_maintenance} OT {ot.id_ot}: {e}")
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur lors de la mise à jour:\n%1").replace('%1', str(e)))
                logger.exception(f"Erreur inattendue màj rapport {maintenance.id_maintenance} OT {ot.id_ot}")
        else:
            logger.info(f"Modification rapport {maintenance.id_maintenance} annulée pour OT {ot.id_ot}")

    # ... (reste de la classe OTView) ...

    # Dans la classe OTView

    @Slot()
    def print_ot(self):
        """Génère et imprime le document OT via le template HTML."""
        ot_id = self._get_selected_ot_id()
        if ot_id is None:
            QMessageBox.warning(self, self.tr("Action Requise"), self.tr("Sélectionnez un OT pour l'impression."))
            return
        try:
            ot = self.maintenance_service.get_ot_by_id(ot_id)
            machine = self.machine_service.get_machine_by_id(ot.machine_id) if ot.machine_id else None
            tpl_dir = os.path.join(os.getcwd(), 'app', 'templates')
            env = Environment(loader=FileSystemLoader(tpl_dir))
            template = env.get_template('ot_document_template.html')
            html = template.render(
                ot=ot,
                machine=machine,
                technicien=self.technicians_map.get(ot.technicien_assigne_id) if hasattr(self, 'technicians_map') else None,
                createur=None,
                taches=[],
                pieces=[],
                compteur=None,
                now=datetime.now()
            )
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter()
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QPrintDialog.Accepted:
                doc.print_(printer)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur d'impression"), self.tr("Erreur lors de l'impression : %1").replace('%1', str(e)))
            logger.error(f"Erreur impression OT {ot_id}: {e}")

    def _on_print_maintenance_report(self):
        """Imprime le rapport de maintenance complet pour l'OT sélectionné en utilisant le template HTML."""
        ot_id = self._get_selected_ot_id()
        if ot_id is None:
            QMessageBox.warning(self, self.tr("Action Requise"), self.tr("Sélectionnez un OT pour imprimer le rapport."))
            return
        
        try:
            # 1. Récupérer les données de la maintenance, l'OT et la machine
            maintenance = self.maintenance_service.get_maintenance_for_ot(ot_id)
            if not maintenance:
                QMessageBox.information(self, self.tr("Aucun Rapport"), self.tr("Aucun rapport de maintenance pour l'OT %1.").replace('%1', str(ot_id)))
                return
            
            ot = self.maintenance_service.get_ot_by_id(ot_id)
            machine = self.machine_service.get_machine_by_id(ot.machine_id) if ot.machine_id else None
            technicien = self.maintenance_service.get_technicien_by_id(maintenance.technicien_id) if maintenance.technicien_id else None
            
            # 2. Récupérer les pièces utilisées pour cette maintenance
            pieces_utilisees = []
            try:
                # Récupérer les données des pièces utilisées via InterventionPieceRepository
                intervention_pieces = self.maintenance_service.get_intervention_pieces_by_maintenance_id(maintenance.id_maintenance)
                
                for ip in intervention_pieces:
                    # Pour chaque intervention_piece, récupérer les détails de la pièce
                    piece = self.stock_service.get_piece_by_id(ip.piece_id)
                    if piece:
                        pieces_utilisees.append({
                            'piece_id': ip.piece_id,
                            'piece_ref': piece.reference,
                            'piece_nom': piece.nom,
                            'quantite': ip.quantite,
                            'lot': ip.lot
                        })
            except Exception as e:
                logger.error(f"Erreur récupération pièces utilisées: {e}", exc_info=True)
                # Continuer malgré l'erreur - le rapport pourra être généré sans les pièces
            
            # 2bis. Récupérer les coûts de maintenance
            couts = self.maintenance_service.calculate_maintenance_cost(maintenance.id_maintenance)

            # 3. Générer le rapport HTML avec Jinja2
            env = Environment(
                loader=FileSystemLoader("app/templates"),
                autoescape=select_autoescape(['html', 'xml'])
            )
            template = env.get_template("maintenance_report_template.html")
            
            # 4. Rendre le template avec toutes les données
            html_content = template.render(
                ot=ot,
                machine=machine,
                maintenance=maintenance,
                technicien=technicien,
                pieces_utilisees=pieces_utilisees,
                couts=couts,
                now=datetime.now()
            )
            
            # 5. Configurer l'impression
            printer = QPrinter()
            print_dialog = QPrintDialog(printer, self)
            
            if print_dialog.exec():
                # Si l'utilisateur a confirmé l'impression
                doc = QTextDocument()
                doc.setHtml(html_content)
                doc.print_(printer)
                QMessageBox.information(self, self.tr("Impression"), self.tr("Le rapport d'intervention a été envoyé à l'imprimante."))
            else:
                QMessageBox.information(self, self.tr("Impression annulée"), self.tr("L'impression a été annulée."))
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur lors de l'impression du rapport : %1").replace('%1', str(e)))
            logger.error(f"Erreur impression rapport OT {ot_id}: {e}", exc_info=True)

    def populate_table(self, ots: List[OrdreTravail]):
        """Remplit la table avec la liste des OTs fournie."""
        # Désactiver temporairement le tri pour éviter problèmes/lenteurs
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0)  # Vider avant de remplir
        self.table_widget.setRowCount(len(ots))

        for row_index, ot in enumerate(ots):
            # --- Préparation des données pour affichage ---
            id_item = QTableWidgetItem(str(ot.id_ot))
            id_item.setData(Qt.ItemDataRole.UserRole, ot.id_ot)

            date_prevue_str = ot.date_prevue.strftime('%Y-%m-%d %H:%M') if ot.date_prevue else ""
            # Utiliser les maps chargées dans refresh_ots pour les noms
            machine_nom = self.machines_map.get(ot.machine_id, f"ID:{ot.machine_id}")
            tech_nom = self.techniciens_map.get(ot.technicien_assigne_id, "") if ot.technicien_assigne_id is not None else ""
            # Tronquer description longue
            desc_short = (ot.description[:75] + '...') if ot.description and len(ot.description) > 75 else (ot.description or "")

            # --- Création des QTableWidgetItem ---
            item_id = id_item  # Colonne 0 (cachée)
            item_num = QTableWidgetItem(ot.numero_ot or "")  # Colonne 1
            item_machine = QTableWidgetItem(machine_nom)  # Colonne 2
            
            # Utiliser les fonctions de traduction du module i18n avec la langue configurée
            from app.config import app_config
            type_traduit = translate_type(ot.type, app_config.language) if ot.type else ""
            priorite_traduite = translate_priority(ot.priorite, app_config.language) if ot.priorite else ""
            statut_traduit = translate_status(ot.statut, app_config.language) if ot.statut else ""
            
            item_type = QTableWidgetItem(type_traduit)  # Colonne 3
            item_prio = QTableWidgetItem(priorite_traduite)  # Colonne 4
            item_statut = QTableWidgetItem(statut_traduit)  # Colonne 5
            
            # Stocker la valeur originale pour le tri
            if ot.type:
                item_type.setData(Qt.ItemDataRole.UserRole, ot.type)
            if ot.priorite:
                item_prio.setData(Qt.ItemDataRole.UserRole, ot.priorite)
            if ot.statut:
                item_statut.setData(Qt.ItemDataRole.UserRole, ot.statut)
                
            item_tech = QTableWidgetItem(tech_nom)  # Colonne 6
            item_date = QTableWidgetItem(date_prevue_str)  # Colonne 7
            item_desc = QTableWidgetItem(desc_short)  # Colonne 8

            # --- Remplissage de la ligne du tableau ---
            self.table_widget.setItem(row_index, 0, item_id)
            self.table_widget.setItem(row_index, 1, item_num)
            self.table_widget.setItem(row_index, 2, item_machine)
            self.table_widget.setItem(row_index, 3, item_type)
            self.table_widget.setItem(row_index, 4, item_prio)
            self.table_widget.setItem(row_index, 5, item_statut)
            self.table_widget.setItem(row_index, 6, item_tech)
            self.table_widget.setItem(row_index, 7, item_date)
            self.table_widget.setItem(row_index, 8, item_desc)

            # --- Style conditionnel ---
            if ot.urgence:
                for col in range(1, self.table_widget.columnCount()):  # Commencer à col 1
                    item = self.table_widget.item(row_index, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.yellow)

        # --- Post-remplissage ---
        self._update_button_states()  # Mettre à jour boutons après modif données/sélection
        self.table_widget.setSortingEnabled(True)
        self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)

    @Slot()
    def open_maintenance_details(self):
        """Ouvre la vue détaillée de maintenance pour l'OT sélectionné."""
        ot_id = self._get_selected_ot_id()
        if (ot_id is None):
            QMessageBox.information(self, self.tr("Action Requise"), self.tr("Sélectionnez un OT pour voir les détails de maintenance."))
            return

        try:
            # Vérifier si une maintenance existe pour cet OT
            maintenance = self.maintenance_service.get_maintenance_for_ot(ot_id)

            if not maintenance:
                # Si aucune maintenance n'existe, demander si l'utilisateur veut en créer une
                reply = QMessageBox.question(
                    self,
                    self.tr("Aucune Maintenance"),
                    self.tr("Aucun rapport de maintenance n'existe pour cet OT. Voulez-vous en créer une?"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Rediriger vers la création d'un rapport
                    self.record_maintenance_report()
                    return
                else:
                    return

            # Ouvrir la vue détaillée avec la maintenance existante
            detail_view = MaintenanceDetailView(
                maintenance_service=self.maintenance_service,
                machine_service=self.machine_service,
                stock_service=self.stock_service,
                ot_id=ot_id,
                parent=self
            )

            # Connecter le signal de mise à jour pour rafraîchir la liste des OTs
            detail_view.maintenanceUpdated.connect(lambda: self.refresh_ots())

            # Définir une taille initiale pour la fenêtre
            detail_view.resize(800, 600)
            
            # Afficher la vue comme une fenêtre modale
            detail_view.setWindowModality(Qt.ApplicationModal)
            
            # Afficher la fenêtre d'abord pour qu'elle ait une géométrie valide
            detail_view.show()
            
            # Centrer la fenêtre sur l'écran 
            frameGm = detail_view.frameGeometry()
            screen = self.screen()
            centerPoint = screen.availableGeometry().center()
            frameGm.moveCenter(centerPoint)
            detail_view.move(frameGm.topLeft())
            
            # S'assurer que la fenêtre est bien visible et active
            detail_view.raise_()
            detail_view.activateWindow()

            logger.info(f"Vue détaillée de maintenance ouverte pour OT ID {ot_id}")
        except (BusinessLogicError, NotFoundError) as e:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ouvrir les détails de maintenance:\n%1").replace('%1', str(e)))
            logger.error(f"Erreur ouverture détails maintenance OT ID {ot_id}: {e}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n%1").replace('%1', str(e)))
            logger.exception(f"Erreur inattendue ouverture détails maintenance OT ID {ot_id}")

    # --- Slot pour Dupliquer OT ---
    @Slot(int)
    def duplicate_ot(self, original_ot_id: int):
        """ Ouvre le dialogue de création OT pré-rempli avec les données de l'OT original. """
        logger.info(f"Demande de duplication pour OT ID: {original_ot_id}")
        try:
            # 1. Récupérer les données de l'OT original
            ot_original = self.maintenance_service.get_ot_by_id(original_ot_id)
            if not ot_original:
                raise NotFoundError(f"OT original ID {original_ot_id} non trouvé pour duplication.")

            # 2. Préparer les données pour le nouveau dialogue (mode création)
            #    On réutilise la plupart des infos, mais on reset/adapte certains champs
            new_ot_data_preload = {
                "machine_id": ot_original.machine_id,
                "type": ot_original.type,
                "description": f"(Copie) {ot_original.description}", # Préfixer description
                "priorite": ot_original.priorite or "Moyenne",
                "urgence": ot_original.urgence, # Garder urgence? Ou False? Gardons pour l'instant.
                "gamme_id": ot_original.gamme_id, # Garder le lien gamme si existait
                "duree_prevue_min": ot_original.duree_prevue_min,
                # --- Champs à NE PAS COPIER ou à réinitialiser ---
                # "numero_ot": None, # Sera regénéré
                # "statut": "Créé", # Nouveau statut
                # "date_prevue": None, # Nouvelle planification à faire
                # "technicien_assigne_id": None, # Nouvelle assignation
                # "notes_planification": None # Notes spécifiques au nouvel OT
                # utilisateur_createur_id sera défini par le service à la création
            }

            # 3. Ouvrir OTDialog en mode CREATION, mais en lui passant les données pré-remplies
            logger.debug(f"Ouverture dialogue création OT avec pré-remplissage depuis OT {original_ot_id}")

            dialog = OTDialog(
                machine_service=self.machine_service,
                maintenance_service=self.maintenance_service,
                current_user_id=self.current_user_id,
                initial_data=new_ot_data_preload, # Passer les données pré-remplies
                parent=self,
                app_language=self.app_language
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_ot_data = dialog.get_ot_data() # Récupère les données finales du dialogue
                try:
                    logger.info(f"Tentative création OT dupliqué via service...")
                    logger.debug(f"Données envoyées pour création OT dupliqué: {new_ot_data}")
                    # Vérification défensive des champs obligatoires
                    required_fields = ['machine_id', 'type', 'description', 'utilisateur_createur_id']
                    missing = [f for f in required_fields if not new_ot_data.get(f)]
                    if missing:
                        raise BusinessLogicError(f"Champs obligatoires manquants pour duplication OT: {missing}")
                    created_ot = self.maintenance_service.create_ot(new_ot_data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("OT '%1' créé par duplication.").replace('%1', str(created_ot.numero_ot or created_ot.id_ot)))
                    self.refresh_ots()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                    # Afficher le message d'erreur détaillé à l'utilisateur
                    QMessageBox.warning(self, self.tr("Erreur Création"), self.tr("Impossible de créer l'OT dupliqué :\n%1").replace('%1', str(e)))
                    logger.error(f"Échec création OT dupliqué: {e}")
                except Exception as e:
                    QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur inattendue lors de la création de l'OT dupliqué :\n%1").replace('%1', str(e)))
                    logger.exception("Erreur inattendue création OT dupliqué.")
        except (BusinessLogicError, NotFoundError) as e:
            QMessageBox.warning(self, self.tr("Erreur Duplication"), self.tr("Impossible de préparer la duplication:\n%1").replace('%1', str(e)))
            logger.error(f"Erreur préparation duplication OT {original_ot_id}: {e}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur lors de la duplication:\n%1").replace('%1', str(e)))
            logger.exception(f"Erreur inattendue duplication OT {original_ot_id}.")

    @Slot(int)
    def open_maintenance_details_dialog(self, ot_id: int):
        """Ouvre le dialogue de détails de maintenance pour l'OT donné."""
        try:
            maintenance = self.maintenance_service.get_maintenance_for_ot(ot_id)
            if not maintenance:
                QMessageBox.information(self, self.tr("Aucun Rapport"), self.tr("Aucun rapport de maintenance pour l'OT %1.").replace('%1', str(ot_id)))
                return
            dialog = MaintenanceDetailDialog(
                maintenance_id=maintenance.id_maintenance,
                ot_id=ot_id,
                maintenance_service=self.maintenance_service,
                parent=self
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur lors de l'ouverture des détails de maintenance : %1").replace('%1', str(e)))
            logger.error(f"Erreur ouverture détails maintenance OT {ot_id}: {e}", exc_info=True)

    # --- Méthodes de conversion UI <-> Base de données ---
    
    def _convert_ui_to_db_value(self, ui_value: str, field_type: str) -> Any:
        """
        Convertit une valeur de l'interface utilisateur vers la valeur correspondante en base.
        Args:
            ui_value: Valeur affichée dans l'UI (potentiellement traduite)
            field_type: Type de champ ('type', 'status', 'priority', etc.)
        Returns:
            La valeur correspondante pour la base de données (généralement en français)
        """
        if not ui_value or ui_value in ["Tous", self.tr("All")]:
            return None
            
        try:
            if field_type == "type":
                return reverse_translate_type(ui_value, app_config.language)
                
            elif field_type == "status":
                return reverse_translate_status(ui_value, app_config.language)
                
            elif field_type == "priority":
                return reverse_translate_priority(ui_value, app_config.language)
                
            else:
                # Pour d'autres types, retourner tel quel
                return ui_value
                
        except Exception as e:
            logger.error(f"Erreur conversion UI->DB pour '{ui_value}' (type: {field_type}): {e}")
            return ui_value

    def _convert_db_to_ui_value(self, db_value: str, field_type: str) -> str:
        """
        Convertit une valeur de base de données vers la valeur à afficher dans l'UI.
        Args:
            db_value: Valeur stockée en base (généralement en français)
            field_type: Type de champ ('type', 'status', 'priority', etc.)
        Returns:
            La valeur traduite pour l'affichage dans l'UI
        """
        if not db_value:
            return ""
            
        try:
            if field_type == "type":
                return translate_type(db_value, app_config.language)
            elif field_type == "status":
                return translate_status(db_value, app_config.language)
            elif field_type == "priority":
                return translate_priority(db_value, app_config.language)
            else:
                return db_value
        except Exception as e:
            logger.error(f"Erreur conversion DB->UI pour '{db_value}' (type: {field_type}): {e}")
            return db_value

    # --- Méthodes d'archivage ---
    
    @Slot(int)
    def archive_ot(self, ot_id: int):
        """Archive l'OT sélectionné."""
        try:
            # Vérification préliminaire
            ot = next((o for o in self.current_ots if o.id_ot == ot_id), None)
            if not ot:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("OT non trouvé."))
                return
            
            if ot.statut != "Terminé":
                QMessageBox.warning(self, self.tr("Action impossible"), 
                                  self.tr("Seuls les OT avec le statut 'Terminé' peuvent être archivés."))
                return
            
            # Demande de confirmation
            reply = QMessageBox.question(
                self, 
                self.tr("Confirmation d'archivage"),
                self.tr("Êtes-vous sûr de vouloir archiver l'OT {0} ?\n\nCette action changera son statut vers 'Archivé'.").format(ot.numero_ot or f"ID {ot_id}"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                logger.info(f"Archivage de l'OT {ot_id} annulé par l'utilisateur.")
                return
            
            # Appel du service d'archivage
            logger.info(f"Archivage de l'OT {ot_id}...")
            archived_ot = self.maintenance_service.archive_ot(ot_id, self.current_user_id)
            
            # Message de succès
            QMessageBox.information(
                self, 
                self.tr("Archivage réussi"),
                self.tr("L'OT {0} a été archivé avec succès.").format(archived_ot.numero_ot or f"ID {ot_id}")
            )
            
            # Rafraîchir la liste
            self.refresh_ots()
            logger.info(f"OT {ot_id} archivé avec succès.")
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.tr("Erreur d'archivage"),
                self.tr("Impossible d'archiver l'OT :\n{0}").format(str(e))
            )
            logger.exception(f"Erreur lors de l'archivage de l'OT {ot_id}")

    @Slot(int)
    def unarchive_ot(self, ot_id: int):
        """Désarchive l'OT sélectionné."""
        try:
            # Vérification préliminaire
            ot = next((o for o in self.current_ots if o.id_ot == ot_id), None)
            if not ot:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("OT non trouvé."))
                return
            
            if ot.statut != "Archivé":
                QMessageBox.warning(self, self.tr("Action impossible"), 
                                  self.tr("Seuls les OT avec le statut 'Archivé' peuvent être désarchivés."))
                return
            
            # Demande de confirmation
            reply = QMessageBox.question(
                self, 
                self.tr("Confirmation de désarchivage"),
                self.tr("Êtes-vous sûr de vouloir désarchiver l'OT {0} ?\n\nCette action changera son statut vers 'Terminé'.").format(ot.numero_ot or f"ID {ot_id}"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                logger.info(f"Désarchivage de l'OT {ot_id} annulé par l'utilisateur.")
                return
            
            # Appel du service de désarchivage
            logger.info(f"Désarchivage de l'OT {ot_id}...")
            unarchived_ot = self.maintenance_service.unarchive_ot(ot_id, self.current_user_id)
            
            # Message de succès
            QMessageBox.information(
                self, 
                self.tr("Désarchivage réussi"),
                self.tr("L'OT {0} a été désarchivé avec succès et son statut est maintenant 'Terminé'.").format(unarchived_ot.numero_ot or f"ID {ot_id}")
            )
            
            # Rafraîchir la liste
            self.refresh_ots()
            logger.info(f"OT {ot_id} désarchivé avec succès.")
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.tr("Erreur de désarchivage"),
                self.tr("Impossible de désarchiver l'OT :\n{0}").format(str(e))
            )
            logger.exception(f"Erreur lors du désarchivage de l'OT {ot_id}")