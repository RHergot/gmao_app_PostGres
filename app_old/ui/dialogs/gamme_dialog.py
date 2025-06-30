# gmao_app/app/ui/dialogs/gamme_dialog.py
"""
Dialogue complexe pour ajouter/modifier une Gamme d'Entretien,
incluant la gestion des étapes et des pièces types.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QCheckBox, QDialogButtonBox, QMessageBox, QLabel, QGroupBox,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QPushButton, QDateEdit,
    QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Slot, QDate, Qt
from typing import Optional, Dict, Any, List
from datetime import date

# Models
from app.core.models.gamme_entretien import (
    GammeEntretien, VALID_PERIODICITE_UNITES, VALID_ENTRETIEN_TYPES, VALID_PRIORITES_GAMME
)
from app.core.models.gamme_etape import GammeEtape
from app.core.models.gamme_piece_type import GammePieceType # Liaison
from app.core.models.piece import Piece # Pour liste pièces
from app.core.models.type_machine import TypeMachine # Pour liste types

# Services
from app.core.services.preventive_service import PreventiveMaintenanceService
from app.core.services.machine_service import MachineService # Pour types machines
from app.core.services.stock_service import StockService # Pour liste pièces

# Dialogue Sélection Pièce (réutilisé?) -> Non, besoin d'un sélecteur multi-pièces ou table
# from .piece_selection_dialog import PieceSelectionDialog # Peut-être pour ajouter ligne pièce type

# Dialogue pour ajouter/modifier une étape (simple)
from .gamme_etape_dialog import GammeEtapeDialog # À CRÉER

# Dialogue pour ajouter/modifier une pièce type (simple)
from .gamme_piece_dialog import GammePieceDialog # À CRÉER


from app.utils.exceptions import BusinessLogicError
from app.utils.i18n import ENTRETIEN_TYPE_LABELS, PRIORITE_LABELS, get_label_multi, get_key_multi
import locale

logger = logging.getLogger(__name__)

from app.config import Language

class GammeDialog(QDialog):
    """Dialogue pour créer ou éditer une Gamme d'Entretien."""

    def __init__(self,
                 preventive_service: PreventiveMaintenanceService,
                 machine_service: MachineService,
                 stock_service: StockService,
                 gamme: Optional[GammeEntretien] = None,
                 current_user_id: Optional[int] = None, # Qui crée/modifie?
                 parent=None,
                 app_language: Language = Language.FRENCH):
        super().__init__(parent)
        self.preventive_service = preventive_service
        self.machine_service = machine_service
        self.stock_service = stock_service
        self.gamme_original = gamme
        self.is_edit_mode = gamme is not None
        self.current_user_id = current_user_id

        # Listes locales pour gérer les étapes et pièces dans l'UI avant sauvegarde
        # Charger depuis service si mode édition
        self.etapes_ui: List[GammeEtape] = []
        self.pieces_type_ui: List[Dict[str, Any]] = [] # Liste de dict {'piece_id':..., 'nom':..., 'ref':..., 'qte':...}

        self.setWindowTitle(self.tr("Ajouter Gamme d'Entretien") if not self.is_edit_mode else self.tr(f"Modifier Gamme {gamme.id_gamme}"))
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        # --- Données ComboBox ---
        self._types_machine: List[TypeMachine] = []

        # --- Widgets Onglet Principal ---
        self.description_input = QLineEdit()
        self.type_entretien_combo = QComboBox()
        self.priorite_combo = QComboBox()

        # Détection de la langue et ajout des valeurs traduites dans les combos
        # Utilise la langue passée par l'application (objet Language)
        self._lang = app_language
        # Remplir les combos avec labels traduits mais stocker la clé (libellé DB) en userData
        self.type_entretien_combo.clear()
        self.type_entretien_combo.addItem(self.tr(""), "")
        for t in VALID_ENTRETIEN_TYPES:
            self.type_entretien_combo.addItem(get_label_multi(ENTRETIEN_TYPE_LABELS, t, self._lang), t)

        self.priorite_combo.clear()
        self.priorite_combo.addItem(self.tr(""), "")
        for p in VALID_PRIORITES_GAMME:
            self.priorite_combo.addItem(get_label_multi(PRIORITE_LABELS, p, self._lang), p)
        # Sélection par défaut
        idx = self.priorite_combo.findData("Moyenne")
        if idx >= 0:
            self.priorite_combo.setCurrentIndex(idx)


        self.type_machine_combo = QComboBox() # Lié à un type de machine?
        self.periodicite_valeur_spin = QSpinBox(); self.periodicite_valeur_spin.setRange(0, 999); self.periodicite_valeur_spin.setSpecialValueText(self.tr("Non périodique"))
        self.periodicite_unite_combo = QComboBox(); self.periodicite_unite_combo.addItems([self.tr("")] + [self.tr(u) for u in VALID_PERIODICITE_UNITES])
        self.duree_estimee_spin = QSpinBox(); self.duree_estimee_spin.setRange(0, 9999); self.duree_estimee_spin.setSuffix(self.tr(" min")); self.duree_estimee_spin.setSpecialValueText(self.tr("N/A"))
        self.qualification_input = QLineEdit()
        self.instructions_edit = QTextEdit()
        self.active_check = QCheckBox(self.tr("Gamme Active (génère des OT)")); self.active_check.setChecked(True)
        self.date_derniere_input = QDateEdit(); self.date_derniere_input.setCalendarPopup(True); self.date_derniere_input.setDisplayFormat("yyyy-MM-dd"); self.date_derniere_input.setSpecialValueText(self.tr("Jamais réalisée"))

        self._load_type_machine_combo()

        # --- Widgets Onglet Étapes ---
        self.etapes_table = QTableWidget()
        self.setup_etapes_table()
        self.add_etape_button = QPushButton(self.tr("Ajouter Étape"))
        self.edit_etape_button = QPushButton(self.tr("Modifier Étape"))
        self.remove_etape_button = QPushButton(self.tr("Supprimer Étape"))
        self.move_etape_up_button = QPushButton(self.tr("Monter"))
        self.move_etape_down_button = QPushButton(self.tr("Descendre"))

        # --- Widgets Onglet Pièces Types ---
        self.pieces_table = QTableWidget()
        self.setup_pieces_table()
        self.add_piece_button = QPushButton(self.tr("Ajouter Pièce Type"))
        self.edit_piece_button = QPushButton(self.tr("Modifier Quantité")) # Ou juste modifier?
        self.remove_piece_button = QPushButton(self.tr("Retirer Pièce Type"))


        # --- Layout Principal avec Onglets ---
        self.tab_widget = QTabWidget()
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

        # Créer les onglets
        self.setup_main_tab()
        self.setup_etapes_tab()
        self.setup_pieces_tab()

        # Boutons OK/Cancel en bas
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # --- Pré-remplissage & Chargement initial ---
        if self.is_edit_mode and self.gamme_original:
            self._populate_fields()
            self._load_etapes_and_pieces() # Charger étapes/pièces liées

        self._update_etape_button_states()
        self._update_piece_button_states()
        logger.debug(f"GammeDialog initialisé mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _populate_fields(self):
        """Remplit les champs du formulaire avec les données de self.gamme_original."""
        g = self.gamme_original
        if not g:
            logger.warning("Appel à _populate_fields sans gamme_original.")
            return
        self.description_input.setText(g.description or "")
        # Type entretien
        if g.type_entretien:
            label = get_label_multi(ENTRETIEN_TYPE_LABELS, g.type_entretien, self._lang)
            idx = self.type_entretien_combo.findText(label)
            self.type_entretien_combo.setCurrentIndex(idx if idx != -1 else 0)
        # Type machine
        if g.type_machine_id:
            # On suppose que le combo a déjà été rempli
            idx = self.type_machine_combo.findData(g.type_machine_id)
            self.type_machine_combo.setCurrentIndex(idx if idx != -1 else 0)
        # Périodicité
        if g.periodicite_valeur is not None:
            self.periodicite_valeur_spin.setValue(g.periodicite_valeur)
        if g.periodicite_unite:
            idx = self.periodicite_unite_combo.findText(self.tr(g.periodicite_unite))
            self.periodicite_unite_combo.setCurrentIndex(idx if idx != -1 else 0)
        # Dernière réalisation
        if g.date_derniere_realisation:
            self.date_derniere_input.setDate(QDate(g.date_derniere_realisation.year, g.date_derniere_realisation.month, g.date_derniere_realisation.day))
        # Priorité
        if g.priorite:
            label = get_label_multi(PRIORITE_LABELS, g.priorite, self._lang)
            idx = self.priorite_combo.findText(label)
            self.priorite_combo.setCurrentIndex(idx if idx != -1 else 0)
        # Durée estimée
        if g.duree_estimee_min is not None:
            self.duree_estimee_spin.setValue(g.duree_estimee_min)
        # Qualification
        self.qualification_input.setText(g.qualification_requise or "")
        # Instructions
        self.instructions_edit.setText(g.instructions or "")
        # Active
        self.active_check.setChecked(bool(g.active))

    def _load_type_machine_combo(self):
        """Charge la liste des types de machine dans la comboBox."""
        try:
            self._types_machine = self.machine_service.get_all_type_machines()
            self.type_machine_combo.clear()
            self.type_machine_combo.addItem(self.tr(""), userData=None)  # Option vide
            for tm in self._types_machine:
                self.type_machine_combo.addItem(str(tm.nom), userData=tm.id_type_machine)
            logger.debug(f"{len(self._types_machine)} types de machine chargés dans la comboBox.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des types de machine : {e}")
            QMessageBox.warning(self, self.tr("Erreur de Chargement"), self.tr("Impossible de charger la liste des types de machine.\nDétail : {e}").format(e=e))
            self.type_machine_combo.clear()
            self.type_machine_combo.addItem(self.tr("Erreur de chargement"), userData=None)


    def setup_main_tab(self):
        """ Configure l'onglet principal 'Informations Générales'. """
        main_tab = QWidget()
        layout = QFormLayout(main_tab)

        layout.addRow(self.tr("Description / Code (*)"), self.description_input)
        layout.addRow(self.tr("Type Entretien:"), self.type_entretien_combo)
        layout.addRow(self.tr("Liée au Type Machine:"), self.type_machine_combo)
        # Périodicité sur une ligne
        periodicite_layout = QHBoxLayout()
        periodicite_layout.addWidget(self.periodicite_valeur_spin)
        periodicite_layout.addWidget(self.periodicite_unite_combo)
        layout.addRow(self.tr("Périodicité:"), periodicite_layout)
        layout.addRow(self.tr("Dernière Réalisation:"), self.date_derniere_input)
        layout.addRow(self.tr("Priorité OT par Défaut:"), self.priorite_combo)
        layout.addRow(self.tr("Durée Estimée Totale:"), self.duree_estimee_spin)
        layout.addRow(self.tr("Qualification Requise:"), self.qualification_input)
        layout.addRow(self.tr("Instructions Générales:"), self.instructions_edit)
        layout.addRow(self.active_check)

        self.tab_widget.addTab(main_tab, self.tr("Général"))


    def setup_etapes_table(self):
        """ Configure la table des étapes. """
        self.etapes_table.setColumnCount(4) # ID(hid), Ordre, Description, Durée Est.
        self.etapes_table.setHorizontalHeaderLabels([
            self.tr("ID"),
            self.tr("Ordre"),
            self.tr("Description Tâche"),
            self.tr("Durée Est. (min)")
        ])
        # Configs standard...
        self.etapes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.etapes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.etapes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.etapes_table.verticalHeader().setVisible(False)
        self.etapes_table.setAlternatingRowColors(True)
        # self.etapes_table.setSortingEnabled(True) # Tri par ordre géré manuellement
        self.etapes_table.setColumnHidden(0, True)

        header = self.etapes_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Ordre
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Desc
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Durée

    def setup_etapes_tab(self):
        """ Configure l'onglet 'Étapes'. """
        etapes_tab = QWidget()
        layout = QVBoxLayout(etapes_tab)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_etape_button)
        buttons_layout.addWidget(self.edit_etape_button)
        buttons_layout.addWidget(self.remove_etape_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.move_etape_up_button)
        buttons_layout.addWidget(self.move_etape_down_button)

        layout.addWidget(self.etapes_table)
        layout.addLayout(buttons_layout)
        self.tab_widget.addTab(etapes_tab, self.tr("Étapes"))

        # Connecter signaux boutons étapes
        self.add_etape_button.clicked.connect(self.add_etape)
        self.edit_etape_button.clicked.connect(self.edit_etape)
        self.remove_etape_button.clicked.connect(self.remove_etape)
        self.move_etape_up_button.clicked.connect(lambda: self.move_etape(-1))
        self.move_etape_down_button.clicked.connect(lambda: self.move_etape(1))
        self.etapes_table.itemSelectionChanged.connect(self._update_etape_button_states)
    def setup_pieces_table(self):
         """ Configure la table des pièces types. """
         self.pieces_table.setColumnCount(4) # piece_id(hid), Ref, Nom, Qté Théorique
         self.pieces_table.setHorizontalHeaderLabels([
             self.tr("ID Pièce"),
             self.tr("Référence"),
             self.tr("Nom Pièce"),
             self.tr("Qté Théorique")
         ])
         # Configs standard...
         self.pieces_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
         self.pieces_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
         self.pieces_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
         self.pieces_table.verticalHeader().setVisible(False)
         self.pieces_table.setAlternatingRowColors(True)
         self.pieces_table.setSortingEnabled(True) # Tri possible
         self.pieces_table.setColumnHidden(0, True)
         header = self.pieces_table.horizontalHeader()
         header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
         header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
         header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)


    def setup_pieces_tab(self):
        """ Configure l'onglet 'Pièces Types Requises'. """
        pieces_tab = QWidget()
        layout = QVBoxLayout(pieces_tab)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_piece_button)
        buttons_layout.addWidget(self.edit_piece_button) # Modifier quantité via Add/Remove? Ou double clic?
        buttons_layout.addWidget(self.remove_piece_button)
        buttons_layout.addStretch()

        layout.addWidget(self.pieces_table)
        layout.addLayout(buttons_layout)
        self.tab_widget.addTab(pieces_tab, self.tr("Pièces Types"))
        # Connecter les boutons d'ajout, modification et suppression de pièce type
        self.add_piece_button.clicked.connect(self.add_piece_type)
        self.edit_piece_button.clicked.connect(self.edit_piece_type)
        self.remove_piece_button.clicked.connect(self.remove_piece_type)
        # Connecter la sélection de la table pour activer/désactiver les boutons
        self.pieces_table.itemSelectionChanged.connect(self._update_piece_button_states)


    def _load_etapes_and_pieces(self):
         """ Charge étapes et pièces liées depuis service si mode édition. """
         if not self.is_edit_mode or not self.gamme_original or self.gamme_original.id_gamme is None:
             return
         gamme_id = self.gamme_original.id_gamme
         logger.debug(f"Chargement étapes et pièces pour Gamme ID {gamme_id}")
         try:
             self.etapes_ui = self.preventive_service.get_etapes_for_gamme(gamme_id)
             # get_pieces_details_by_gamme_id retourne une liste de dicts
             self.pieces_type_ui = self.preventive_service.get_pieces_type_for_gamme(gamme_id)
             # Ajuster format pièces si besoin pour correspondre à ce qu'on stocke
             self.pieces_type_ui = [
                 {'piece_id': p['piece_id'],
                  'piece_ref': p['reference'],
                  'piece_nom': p['piece_nom'],
                  'quantite': p['quantite_theorique'],
                  'lot': None} # Pas de lot pour pièces types
                 for p in self.pieces_type_ui
             ]

             self._populate_etapes_table()
             self._populate_pieces_table()
             logger.debug(f"{len(self.etapes_ui)} étapes et {len(self.pieces_type_ui)} pièces types chargées.")
         except Exception as e:
              logger.exception(f"Erreur chargement étapes/pièces pour gamme {gamme_id}")
              QMessageBox.warning(self, self.tr("Erreur"), self.tr(f"Impossible de charger les étapes ou pièces liées:\n{e}"))


    def _populate_etapes_table(self):
        """ Remplit table étapes avec self.etapes_ui. """
        self.etapes_table.setSortingEnabled(False)
        self.etapes_table.setRowCount(0); self.etapes_table.setRowCount(len(self.etapes_ui))
        # S'assurer que les étapes sont triées par ordre avant affichage
        self.etapes_ui.sort(key=lambda x: x.ordre)
        for row, etape in enumerate(self.etapes_ui):
             # Assigner l'ordre correct ici si nécessaire (si pas déjà fait)
             etape.ordre = row + 1 # S'assurer que l'ordre est 1, 2, 3...
             id_item = QTableWidgetItem(str(etape.id_etape or self.tr("Nouveau"))); id_item.setData(Qt.ItemDataRole.UserRole, row) # Stocker index liste
             order_item = QTableWidgetItem(str(etape.ordre)); order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
             desc_item = QTableWidgetItem(self.tr(etape.description))
             duree_str = str(etape.duree_estimee_min) if etape.duree_estimee_min is not None else ""
             duree_item = QTableWidgetItem(duree_str); duree_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

             self.etapes_table.setItem(row, 0, id_item)
             self.etapes_table.setItem(row, 1, order_item)
             self.etapes_table.setItem(row, 2, desc_item)
             self.etapes_table.setItem(row, 3, duree_item)
        # self.etapes_table.setSortingEnabled(True) # Tri manuel via boutons plutôt


    def _populate_pieces_table(self):
         """ Remplit table pièces types avec self.pieces_type_ui. """
         self.pieces_table.setSortingEnabled(False)
         self.pieces_table.setRowCount(0); self.pieces_table.setRowCount(len(self.pieces_type_ui))
         for row, p_data in enumerate(self.pieces_type_ui):
             id_item = QTableWidgetItem(str(p_data.get('piece_id', self.tr('N/A')))); id_item.setData(Qt.ItemDataRole.UserRole, row) # Index liste
             ref_item = QTableWidgetItem(self.tr(p_data.get('piece_ref', 'N/A')))
             nom_item = QTableWidgetItem(self.tr(p_data.get('piece_nom', 'N/A')))
             qte_item = QTableWidgetItem(str(p_data.get('quantite', 1))); qte_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

             self.pieces_table.setItem(row, 0, id_item)
             self.pieces_table.setItem(row, 1, ref_item)
             self.pieces_table.setItem(row, 2, nom_item)
             self.pieces_table.setItem(row, 3, qte_item)
         # self.pieces_table.setSortingEnabled(True) # OK ici

    def _update_etape_button_states(self):
         """ Met à jour boutons étapes selon sélection et position. """
         selected_row = self.etapes_table.currentRow()
         has_selection = selected_row >= 0
         is_not_first = has_selection and selected_row > 0
         is_not_last = has_selection and selected_row < self.etapes_table.rowCount() - 1

         self.edit_etape_button.setEnabled(has_selection)
         self.remove_etape_button.setEnabled(has_selection)
         self.move_etape_up_button.setEnabled(is_not_first)
         self.move_etape_down_button.setEnabled(is_not_last)

    def _update_piece_button_states(self):
         """ Met à jour boutons pièces. """
         has_selection = self.pieces_table.currentRow() >= 0
         self.remove_piece_button.setEnabled(has_selection)
         self.edit_piece_button.setEnabled(has_selection)


    def _select_combo_item_by_data(self, combo: QComboBox, target_id: Optional[int]):
        """ Sélectionne item ComboBox par ID (userData). """
        # ... (Identique aux autres dialogues) ...
        if target_id is None: combo.setCurrentIndex(0); return
        for index in range(combo.count()):
             if combo.itemData(index) == target_id: combo.setCurrentIndex(index); return
        logger.warning(f"ID {target_id} non trouvé {combo.objectName()}. Défaut.")
        combo.setCurrentIndex(0)


    # --- Slots Onglet Étapes ---
    @Slot()
    def add_etape(self):
        logger.debug("Ajout étape demandé.")
        # Ouvre un dialogue simple pour saisir description et durée
        etape_dialog = GammeEtapeDialog(parent=self) # Le nouveau dialogue à créer
        if etape_dialog.exec() == QDialog.DialogCode.Accepted:
             etape_data = etape_dialog.get_etape_data()
             # Créer objet GammeEtape temporaire (sans ID étape, avec ID gamme si édition)
             new_etape = GammeEtape(
                 gamme_id=self.gamme_original.id_gamme if self.is_edit_mode else 0, # Temporaire si création gamme
                 description=etape_data['description'],
                 ordre=len(self.etapes_ui) + 1, # Ajoute à la fin
                 instructions_detaillees=etape_data.get('instructions_detaillees'),
                 duree_estimee_min=etape_data.get('duree_estimee_min')
             )
             self.etapes_ui.append(new_etape)
             self._reorder_etapes() # Met à jour les numéros d'ordre
             self._populate_etapes_table()
             logger.info("Étape ajoutée à la liste UI.")

    @Slot()
    def edit_etape(self):
        selected_row = self.etapes_table.currentRow()
        if selected_row < 0: return
        index_to_edit = self.etapes_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        if index_to_edit is None or not (0 <= index_to_edit < len(self.etapes_ui)): return

        etape_to_edit = self.etapes_ui[index_to_edit]
        logger.debug(f"Édition étape index {index_to_edit} demandée.")
        # GammeEtapeDialog attend un dict, pas un objet GammeEtape
        etape_data_dict = vars(etape_to_edit) if hasattr(etape_to_edit, '__dict__') else etape_to_edit
        etape_dialog = GammeEtapeDialog(etape_data=etape_data_dict, parent=self)
        if etape_dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = etape_dialog.get_etape_data()
            # Mettre à jour l'objet dans la liste self.etapes_ui
            etape_to_edit.description = updated_data['description']
            etape_to_edit.instructions_detaillees = updated_data.get('instructions_detaillees')
            etape_to_edit.duree_estimee_min = updated_data.get('duree_estimee_min')
            # L'ordre ne change pas ici
            self._populate_etapes_table()
            logger.info(f"Étape index {index_to_edit} mise à jour dans la liste UI.")

    @Slot()
    def remove_etape(self):
        selected_row = self.etapes_table.currentRow()
        if selected_row < 0: return
        index_to_remove = self.etapes_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        if index_to_remove is None or not (0 <= index_to_remove < len(self.etapes_ui)): return

        etape_desc = self.etapes_ui[index_to_remove].description[:30]
        reply = QMessageBox.question(self, self.tr("Confirmation"), self.tr(f"Supprimer étape '{etape_desc}...'?") ,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
             del self.etapes_ui[index_to_remove]
             self._reorder_etapes()
             self._populate_etapes_table()
             logger.info(f"Étape index {index_to_remove} supprimée de la liste UI.")


    def move_etape(self, direction: int):
        """ Déplace l'étape sélectionnée vers le haut (-1) ou le bas (+1). """
        selected_row = self.etapes_table.currentRow()
        if selected_row < 0: return
        index_to_move = self.etapes_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        if index_to_move is None or not (0 <= index_to_move < len(self.etapes_ui)): return

        new_index = index_to_move + direction
        if 0 <= new_index < len(self.etapes_ui):
            # Swap elements
            self.etapes_ui[index_to_move], self.etapes_ui[new_index] = self.etapes_ui[new_index], self.etapes_ui[index_to_move]
            self._reorder_etapes() # Met à jour les numéros d'ordre
            self._populate_etapes_table()
            # Resélectionner l'item déplacé
            self.etapes_table.selectRow(new_index)
            logger.debug(f"Étape déplacée de {index_to_move} vers {new_index}.")


    def _reorder_etapes(self):
        """ Met à jour le champ 'ordre' des étapes dans la liste self.etapes_ui. """
        for i, etape in enumerate(self.etapes_ui):
            etape.ordre = i + 1


    # --- Slots Onglet Pièces Types ---
    @Slot()
    def add_piece_type(self):
        logger.debug("Ajout pièce type demandé.")
        # Ouvre un dialogue pour sélectionner une pièce et la quantité
        piece_dialog = GammePieceDialog(stock_service=self.stock_service, parent=self) # Nouveau dialogue
        if piece_dialog.exec() == QDialog.DialogCode.Accepted:
             piece_data = piece_dialog.get_piece_data()
             if piece_data:
                 # Vérifier si pièce déjà présente
                 piece_id_to_add = piece_data['piece_id']
                 existing_index = -1
                 for i, item in enumerate(self.pieces_type_ui):
                      if item['piece_id'] == piece_id_to_add:
                           existing_index = i
                           break
                 if existing_index != -1:
                      # Mettre à jour quantité existante
                      self.pieces_type_ui[existing_index]['quantite'] = piece_data['quantite']
                      logger.info(f"Quantité pièce type ID {piece_id_to_add} mise à jour.")
                 else:
                      # Ajouter nouvelle pièce
                      self.pieces_type_ui.append(piece_data)
                      logger.info(f"Pièce type ajoutée à la liste UI: {piece_data}")

                 self._populate_pieces_table()


    @Slot()
    def edit_piece_type(self):
        selected_row = self.pieces_table.currentRow()
        if selected_row < 0:
            return
        index_to_edit = self.pieces_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        if index_to_edit is None or not (0 <= index_to_edit < len(self.pieces_type_ui)):
            return
        # Récupérer les infos de la pièce sélectionnée
        piece_data = self.pieces_type_ui[index_to_edit]
        piece_id = piece_data.get('piece_id')
        quantite = piece_data.get('quantite', 1)
        # Ouvrir le dialogue en mode édition
        piece_dialog = GammePieceDialog(stock_service=self.stock_service, current_piece_id=piece_id, current_quantite=quantite, parent=self)
        if piece_dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = piece_dialog.get_piece_data()
            if new_data:
                # Mettre à jour la quantité uniquement
                self.pieces_type_ui[index_to_edit]['quantite'] = new_data['quantite']
                self._populate_pieces_table()
                logger.info(f"Quantité pièce type ID {piece_id} modifiée à {new_data['quantite']}.")

    @Slot()
    def remove_piece_type(self):
        selected_row = self.pieces_table.currentRow()
        if selected_row < 0: return
        index_to_remove = self.pieces_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        if index_to_remove is None or not (0 <= index_to_remove < len(self.pieces_type_ui)): return

        piece_nom = self.pieces_type_ui[index_to_remove].get('piece_nom', self.tr('N/A'))
        reply = QMessageBox.question(self, self.tr("Confirmation"), self.tr(f"Retirer pièce type '{piece_nom}' de la gamme?"),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
             del self.pieces_type_ui[index_to_remove]
             self._populate_pieces_table() # Rafraîchir aussi les index stockés dans UserRole
             logger.info(f"Pièce type index {index_to_remove} supprimée de la liste UI.")

    # --- Validation & Récupération Données Finales ---
    def _validate_input(self) -> bool:
        """ Valide les champs de l'onglet principal. """
        if not self.description_input.text().strip():
             QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Description gamme obligatoire.")); self.tab_widget.setCurrentIndex(0); self.description_input.setFocus(); return False
        # Valider périodicité cohérente
        unit = self.periodicite_unite_combo.currentText()
        val = self.periodicite_valeur_spin.value()
        if unit and val <= 0:
             QMessageBox.warning(self, self.tr("Valeur Incorrecte"), self.tr("Valeur de périodicité doit être > 0 si unité définie.")); self.tab_widget.setCurrentIndex(0); self.periodicite_valeur_spin.setFocus(); return False
        if not unit and val > 0:
             QMessageBox.warning(self, self.tr("Valeur Incorrecte"), self.tr("Unité de périodicité requise si valeur définie.")); self.tab_widget.setCurrentIndex(0); self.periodicite_unite_combo.setFocus(); return False

        # Valider que les étapes ont une description
        for i, etape in enumerate(self.etapes_ui):
            if not etape.description:
                 QMessageBox.warning(self, self.tr("Étape Incomplète"), self.tr(f"L'étape {i+1} doit avoir une description.")); self.tab_widget.setCurrentIndex(1); self.etapes_table.selectRow(i); return False
        return True

    @Slot()
    def accept(self):
        if self._validate_input(): super().accept()

    def get_gamme_data(self) -> Dict[str, Any]:
        """ Récupère toutes les données (Général + Etapes + Pièces) pour le service. """
        # Onglet Général
        p_val = self.periodicite_valeur_spin.value()
        periodicite_val = p_val if p_val > self.periodicite_valeur_spin.minimum() else None
        last_real = self.date_derniere_input.date().toPython() if not self.date_derniere_input.date().isNull() else None
        duree_est = self.duree_estimee_spin.value()
        duree_est_final = duree_est if duree_est > self.duree_estimee_spin.minimum() else None

        data = {
            "description": self.description_input.text().strip(),
            "type_entretien": get_key_multi(ENTRETIEN_TYPE_LABELS, self.type_entretien_combo.currentText(), self._lang) or None,
            "type_machine_id": self.type_machine_combo.currentData(), # Peut être None
            "periodicite_valeur": periodicite_val,
            "periodicite_unite": self.periodicite_unite_combo.currentText() or None,
            "date_derniere_realisation": last_real,
            "priorite": get_key_multi(PRIORITE_LABELS, self.priorite_combo.currentText(), self._lang) or None,
            "duree_estimee_min": duree_est_final,
            "qualification_requise": self.qualification_input.text().strip() or None,
            "instructions": self.instructions_edit.toPlainText().strip() or None,
            "active": self.active_check.isChecked(),
            # createur_id et prochaine_date_calculee gérés par service
        }
        if self.is_edit_mode and self.gamme_original:
             data["id_gamme"] = self.gamme_original.id_gamme
             data["createur_id"] = self.gamme_original.createur_id # Conserver créateur original

        # Ajouter Étapes et Pièces (listes d'objets/dicts préparés)
        data["etapes"] = [etape.__dict__ for etape in self.etapes_ui] # Convertir dataclass en dict simple
        data["pieces_types"] = self.pieces_type_ui # C'est déjà une liste de dicts

        logger.debug(f"Données récupérées du GammeDialog: {data}")
        return data