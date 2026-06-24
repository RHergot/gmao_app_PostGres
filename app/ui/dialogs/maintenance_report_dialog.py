# gmao_app/app/ui/dialogs/maintenance_report_dialog.py
"""
Dialogue pour saisir le rapport d'une intervention de maintenance réalisée,
y compris les pièces utilisées.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QTextEdit, QComboBox,
    QDateTimeEdit, QDialogButtonBox, QMessageBox, QLabel, QGroupBox,
    QSpinBox, QPushButton,  # Ajout QPushButton
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, # Ajouts pour table pièces
    QHBoxLayout, QWidget, QSplitter # Ajout pour layout principal et split
)
from app.ui.widgets.maintenance_couts_widget import MaintenanceCoutsWidget
from app.ui.dialogs.intervenant_dialog import IntervenantDialog
from app.ui.dialogs.frais_externe_dialog import FraisExterneDialog

from PySide6.QtCore import Qt, Slot, QDateTime
from typing import Optional, Dict, Any, List

# Importer modèles et services
from app.core.models.ordre_travail import OrdreTravail
from app.core.models.maintenance import Maintenance
from app.core.models.technicien import Technicien
from app.core.models.piece import Piece # <-- Besoin du modèle Pièce
from app.core.models.intervention_piece import InterventionPiece # <-- Modèle pour les lignes
from app.core.services.maintenance_service import MaintenanceService, MAINTENANCE_RESULTATS, OT_TYPES
from app.core.services.stock_service import StockService # <-- Besoin StockService pour liste pièces
from app.ui.dialogs.piece_selection_dialog import PieceSelectionDialog # <-- Add this import
from app.utils.exceptions import BusinessLogicError
from app.utils.pdf_maintenance import render_maintenance_report_pdf
from PySide6.QtWidgets import QFileDialog
import os

logger = logging.getLogger(__name__)

# ... (Constantes EVALUATION_QUALITE_OPTIONS, IMPACT_PRODUCTION_OPTIONS inchangées) ...


class MaintenanceReportDialog(QDialog):
    """Dialogue pour saisir le rapport d'intervention, y compris pièces."""

    # --- Définir les constantes comme attributs de classe ---
    EVALUATION_QUALITE_OPTIONS = ["", "1 - Médiocre", "2 - Insuffisant", "3 - Moyen", "4 - Bon", "5 - Excellent"]
    IMPACT_PRODUCTION_OPTIONS = ["", "Aucun", "Mineur", "Majeur", "Arrêt Production"]

    def __init__(self,
                 maintenance_service: MaintenanceService,
                 stock_service: StockService, # <-- Service ajouté
                 ordre_travail: OrdreTravail,
                 nom_machine: str, # <-- Ajout du paramètre nom_machine
                 current_user_id: Optional[int] = None,
                 maintenance_to_edit: Optional[Maintenance] = None, # <-- ADDED parameter
                 parent=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.stock_service = stock_service # <-- Stocker le service
        self.ot_concerne = ordre_travail
        self.current_user_id = current_user_id
        self.maintenance_to_edit = maintenance_to_edit # <-- STORED parameter
        # Pour gérer la liste des pièces ajoutées dans le dialogue
        self.pieces_utilisees: List[Dict[str, Any]] = [] # Liste de dicts temporaires {'piece_id': ID, 'piece_ref': REF, 'piece_nom': NOM, 'quantite': QTE, 'lot': LOT}

        self.setWindowTitle(self.tr("Rapport Intervention - OT %1").replace("%1", str(ordre_travail.numero_ot or ordre_travail.id_ot)))
        self.setMinimumWidth(600) # Plus large pour la table pièces
        self.setMinimumHeight(650) # Plus haut

        # --- Données ComboBox ---
        self._techniciens: List[Technicien] = []
        self._pieces_disponibles: List[Piece] = [] # Cache pour liste pièces

        # --- Widgets (Partie supérieure inchangée) ---
        # Ajout des QLabel manquants pour les informations de l'OT
        self.label_ot_num = QLabel(str(self.ot_concerne.numero_ot or self.ot_concerne.id_ot), self)
        self.label_machine = QLabel(nom_machine or "N/A", self) # <-- Utilisation du paramètre
        self.label_ot_desc = QLabel(self.ot_concerne.description, self)
        self.label_ot_desc.setWordWrap(True) # Pour un meilleur affichage des longues descriptions

        self.technicien_combo = QComboBox(self)
        self.date_debut_edit = QDateTimeEdit(self)
        self.date_fin_edit = QDateTimeEdit(self)
        self.type_reel_combo = QComboBox(self); self.type_reel_combo.addItems(OT_TYPES)
        self.travaux_edit = QTextEdit(self); self.travaux_edit.setMinimumHeight(80)
        self.resultat_combo = QComboBox(self); self.resultat_combo.addItems([""] + MAINTENANCE_RESULTATS)
        self.evaluation_combo = QComboBox(self); self.evaluation_combo.addItems(MaintenanceReportDialog.EVALUATION_QUALITE_OPTIONS)
        self.impact_combo = QComboBox(self); self.impact_combo.addItems(MaintenanceReportDialog.IMPACT_PRODUCTION_OPTIONS)
        self.notes_edit = QTextEdit(self); self.notes_edit.setMaximumHeight(60)

        # --- NOUVELLE Section Pièces Utilisées ---
        self.pieces_table = QTableWidget()
        self.setup_pieces_table()
        self.add_piece_button = QPushButton(self.tr("Ajouter Pièce"))
        self.remove_piece_button = QPushButton(self.tr("Retirer Pièce"))
        self.remove_piece_button.setEnabled(False) # Désactivé initialement

        # --- Charger données ComboBox (Techniciens) ---
        self._populate_technicien_combo()
        # Préselection technicien assigné
        self._select_combo_item_by_data(self.technicien_combo, ordre_travail.technicien_assigne_id)
        # Préselection type réel
        if ordre_travail.type in OT_TYPES: self.type_reel_combo.setCurrentText(ordre_travail.type)

        # --- Populate fields if editing ---
        if self.maintenance_to_edit:
            self._populate_fields_for_edit()

        # --- Layout principal horizontal ---
        main_h_layout = QHBoxLayout(self)
        # Partie gauche : tous les inputs et infos
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        group_info = QGroupBox(self.tr("Contexte OT")); form_info = QFormLayout(group_info)
        form_info.addRow(self.tr("Numéro OT:"), self.label_ot_num)
        form_info.addRow(self.tr("Machine:"), self.label_machine)
        form_info.addRow(self.tr("Description Initiale:"), self.label_ot_desc)
        left_layout.addWidget(group_info)

        group_details = QGroupBox(self.tr("Détails de l'Intervention Réelle"))
        form_details = QFormLayout(group_details)
        form_details.addRow(self.tr("Responsable Intervention (*):"), self.technicien_combo)
        form_details.addRow(self.tr("Date/Heure Début (*):"), self.date_debut_edit)
        form_details.addRow(self.tr("Date/Heure Fin (*):"), self.date_fin_edit)
        form_details.addRow(self.tr("Type Réel Travaux (*):"), self.type_reel_combo)
        form_details.addRow(self.tr("Travaux Effectués (*):"), self.travaux_edit)
        form_details.addRow(self.tr("Résultat (*):"), self.resultat_combo)
        left_layout.addWidget(group_details)

        # --- Groupe Pièces ---
        group_pieces = QGroupBox(self.tr("Pièces Utilisées"))
        pieces_layout = QVBoxLayout(group_pieces)
        pieces_table_buttons_layout = QHBoxLayout()
        pieces_table_buttons_layout.addWidget(self.add_piece_button)
        pieces_table_buttons_layout.addWidget(self.remove_piece_button)
        pieces_table_buttons_layout.addStretch()
        pieces_layout.addWidget(self.pieces_table)
        pieces_layout.addLayout(pieces_table_buttons_layout)
        left_layout.addWidget(group_pieces)

        # --- Groupe Infos Additionnelles ---
        group_extra = QGroupBox(self.tr("Informations Additionnelles (Optionnel)"))
        form_extra = QFormLayout(group_extra)
        form_extra.addRow(self.tr("Évaluation Qualité:"), self.evaluation_combo)
        form_extra.addRow(self.tr("Impact Production:"), self.impact_combo)
        form_extra.addRow(self.tr("Notes Technicien:"), self.notes_edit)
        left_layout.addWidget(group_extra)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        left_layout.addWidget(self.button_box)

        # Bouton Exporter PDF
        self.export_pdf_button = QPushButton(self.tr("Exporter PDF"), self)
        self.export_pdf_button.setEnabled(False)  # Bouton désactivé pour l’instant
        self.export_pdf_button.clicked.connect(self.export_pdf_report)
        left_layout.addWidget(self.export_pdf_button)

        # Partie droite : Widget des coûts
        self.couts_widget = MaintenanceCoutsWidget(parent=self, maintenance_id=getattr(self.maintenance_to_edit, 'id_maintenance', None), maintenance_service=self.maintenance_service)
        self.couts_widget.coutsModifies.connect(self._on_couts_modifies)

        # --- État initial : coûts désactivés si pas d'id maintenance ---
        if not getattr(self.maintenance_to_edit, 'id_maintenance', None):
            self.couts_widget.setDisabled(True)
        else:
            self.couts_widget.setDisabled(False)

        # --- Bouton de validation des coûts ---
        self.validate_costs_button = QPushButton(self.tr("Valider les coûts"), self)
        self.validate_costs_button.setEnabled(bool(getattr(self.maintenance_to_edit, 'id_maintenance', None)))
        self.validate_costs_button.clicked.connect(self._on_validate_costs)

        # Ajout au layout principal
        main_h_layout.addWidget(left_widget, 2)
        main_h_layout.addWidget(self.couts_widget, 1)
        main_h_layout.addWidget(self.validate_costs_button, 0)
        self.setLayout(main_h_layout)
        self._connect_signals() # Connecter signaux des nouveaux boutons

        logger.debug(f"MaintenanceReportDialog initialisé pour OT ID {ordre_travail.id_ot}")

        # --- Initialisation dates/heures --- #
        if not self.maintenance_to_edit: # Set default dates only for new reports
            self.date_debut_edit.setDateTime(QDateTime.currentDateTime())
            self.date_fin_edit.setDateTime(QDateTime.currentDateTime())

        # Vérification stricte : le service financier doit être injecté
        if not hasattr(self.maintenance_service, '_finance_service') or self.maintenance_service._finance_service is None:
            raise RuntimeError("L'instance de MaintenanceService fournie n'a pas reçu de FinanceService (set_finance_service non appelé). Vérifiez l'initialisation dans main.py.")

    def _on_couts_modifies(self):
        """Callback pour mettre à jour l'affichage ou la validation après modification des coûts."""
        # Ici, on pourrait rafraîchir un label de coût total, ou déclencher une validation
        # Exemple : afficher un message ou activer un bouton
        pass

    def _on_validate_costs(self):
        """Callback pour valider les coûts externes/intervenants (2e bouton OK)."""
        if not getattr(self.maintenance_to_edit, 'id_maintenance', None):
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Vous devez d'abord valider le rapport avant d'ajouter les coûts."))
            return
        # Ici, on pourrait effectuer une validation métier sur les coûts si besoin
        QMessageBox.information(self, self.tr("Coûts validés"), self.tr("Les coûts ont été validés et enregistrés."))
        # Option : fermer le dialogue après validation des coûts
        # self.accept()

    def setup_pieces_table(self):
         """ Configure la table des pièces utilisées. """
         self.pieces_table.setColumnCount(5) # ID Pièce(hid), Réf, Nom Pièce, Quantité, Lot/SN
         self.pieces_table.setHorizontalHeaderLabels([
    self.tr("ID Pièce"),
    self.tr("Référence"),
    self.tr("Nom Pièce"),
    self.tr("Quantité"),
    self.tr("Lot / S/N")
])
         self.pieces_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Non éditable directement
         self.pieces_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
         self.pieces_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
         self.pieces_table.verticalHeader().setVisible(False)
         self.pieces_table.setAlternatingRowColors(True)
         self.pieces_table.setColumnHidden(0, True) # Cacher ID Pièce

         header = self.pieces_table.horizontalHeader()
         header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Réf
         header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Nom
         header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Quantité
         header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Lot


    def _connect_signals(self):
         """ Connecte les signaux pour les boutons pièces. """
         self.add_piece_button.clicked.connect(self.add_piece_utilisee)
         self.remove_piece_button.clicked.connect(self.remove_piece_utilisee)
         self.pieces_table.itemSelectionChanged.connect(
             lambda: self.remove_piece_button.setEnabled(self.pieces_table.currentRow() >= 0)
         )

    # --- Slots pour gérer les pièces utilisées ---
    @Slot()
    def add_piece_utilisee(self):
        """ Ouvre le dialogue de sélection de pièce. """
        logger.debug("Ouverture dialogue sélection pièce...")
        selection_dialog = PieceSelectionDialog(stock_service=self.stock_service, parent=self)
        if selection_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_data = selection_dialog.get_selected_piece()
            if selected_data:
                if isinstance(selected_data, dict):
                    piece_id_to_check = selected_data.get('piece_id')
                elif isinstance(selected_data, tuple) and len(selected_data) > 0:
                    piece_id_to_check = selected_data[0]
                else:
                    logger.error(f"Format inattendu pour selected_data: {selected_data}")
                    piece_id_to_check = None
                if any((item.get('piece_id') if isinstance(item, dict) else item[0] if isinstance(item, tuple) and len(item) > 0 else None) == piece_id_to_check for item in self.pieces_utilisees):
                    logger.warning(f"La pièce ID {piece_id_to_check} est déjà dans la liste.")
                self.pieces_utilisees.append(selected_data)
                self._populate_pieces_table()
                logger.info(f"Pièce ajoutée à la liste: {selected_data}")
        else:
            logger.debug("Sélection de pièce annulée.")

    @Slot()
    def remove_piece_utilisee(self):
        """ Retire la pièce sélectionnée de la liste self.pieces_utilisees. """
        selected_row = self.pieces_table.currentRow()
        if selected_row < 0: return
        try:
            index_item = self.pieces_table.item(selected_row, 0)
            if index_item:
                index_to_remove = index_item.data(Qt.ItemDataRole.UserRole)
                if index_to_remove is not None and 0 <= index_to_remove < len(self.pieces_utilisees):
                    removed_item = self.pieces_utilisees.pop(index_to_remove)
                    logger.info(f"Pièce retirée de la liste: {removed_item}")
                    self._populate_pieces_table()
                else:
                    logger.error(f"Index invalide ({index_to_remove}) pour suppression pièce à la ligne {selected_row}")
            else:
                logger.error(f"Impossible de récupérer l'item index pour suppression pièce à la ligne {selected_row}")
        except Exception as e:
            logger.exception(f"Erreur suppression pièce de la liste: {e}")

    # --- Méthodes auxiliaires internes --- #

    def _populate_technicien_combo(self): #<- Copié depuis ancienne version, garder cette logique
        """ Charge la liste des techniciens actifs. """
        self.technicien_combo.clear()
        self.technicien_combo.addItem(self.tr(""), userData=None) # Doit sélectionner qqn
        try:
            techniciens = self.maintenance_service.get_all_techniciens(include_inactive=False)
            self._techniciens = techniciens
            for tech in techniciens:
                self.technicien_combo.addItem(tech.nom_complet, userData=tech.id_technicien)
        except BusinessLogicError as e:
            logger.error(f"Erreur chargement techniciens pour rapport: {e}")
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible charger liste techniciens."))
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def _select_combo_item_by_data(self, combo: QComboBox, target_id: Optional[int]): #<- Copié depuis ancienne version
        """ Sélectionne item par userData ID. """
        if target_id is None: combo.setCurrentIndex(0); return
        for index in range(combo.count()):
            if combo.itemData(index) == target_id: combo.setCurrentIndex(index); return
        logger.warning(f"ID {target_id} non trouvé dans {combo.objectName()}. Défaut.")
        combo.setCurrentIndex(0)

    def _populate_pieces_table(self):
         """ Remplit la table des pièces utilisées avec self.pieces_utilisees. """
         # Vider la table
         self.pieces_table.setRowCount(0)
         for idx, item in enumerate(self.pieces_utilisees):
             # Extraire champs
             if isinstance(item, dict):
                 pid = item.get('piece_id')
                 ref = item.get('piece_ref', '')
                 name = item.get('piece_nom', '')
                 qte = item.get('quantite', '')
                 lot = item.get('lot', '')
             elif isinstance(item, tuple):
                 pid = item[0] if len(item) > 0 else ''
                 ref = item[1] if len(item) > 1 else ''
                 name = item[2] if len(item) > 2 else ''
                 qte = item[3] if len(item) > 3 else ''
                 lot = item[4] if len(item) > 4 else ''
             else:
                 continue
             # Ajouter ligne
             row = self.pieces_table.rowCount()
             self.pieces_table.insertRow(row)
             # Colonne cachée: ID Pièce pour mapping
             id_item = QTableWidgetItem(str(pid))
             id_item.setData(Qt.ItemDataRole.UserRole, idx)
             self.pieces_table.setItem(row, 0, id_item)
             # Référence
             self.pieces_table.setItem(row, 1, QTableWidgetItem(str(ref)))
             # Nom
             self.pieces_table.setItem(row, 2, QTableWidgetItem(str(name)))
             # Quantité
             self.pieces_table.setItem(row, 3, QTableWidgetItem(str(qte)))
             # Lot/SN
             self.pieces_table.setItem(row, 4, QTableWidgetItem(str(lot)))
         # Activer/désactiver bouton suppression
         self.remove_piece_button.setEnabled(self.pieces_table.currentRow() >= 0)

    # --- Méthodes auxiliaires internes --- #

    def _populate_fields_for_edit(self):
        """ Pré-remplit les champs du dialogue avec les données de la maintenance existante. """
        if not self.maintenance_to_edit:
            return

        logger.debug(f"Population dialogue avec données existantes (ID: {self.maintenance_to_edit.id_maintenance})")

        # Technicien
        self._select_combo_item_by_data(self.technicien_combo, self.maintenance_to_edit.technicien_id)

        # Dates / Heures
        if self.maintenance_to_edit.date_debut_reelle:
            self.date_debut_edit.setDateTime(QDateTime(self.maintenance_to_edit.date_debut_reelle))
        if self.maintenance_to_edit.date_fin_reelle:
            self.date_fin_edit.setDateTime(QDateTime(self.maintenance_to_edit.date_fin_reelle))

        # Type réel
        if self.maintenance_to_edit.type_reel in OT_TYPES:
            self.type_reel_combo.setCurrentText(self.maintenance_to_edit.type_reel)
        else:
            self.type_reel_combo.setCurrentIndex(0) # Default or clear if invalid

        # Travaux effectués
        self.travaux_edit.setText(self.maintenance_to_edit.description_travaux or "")

        # Résultat
        if self.maintenance_to_edit.resultat in MAINTENANCE_RESULTATS:
            self.resultat_combo.setCurrentText(self.maintenance_to_edit.resultat)
        else:
            self.resultat_combo.setCurrentIndex(0) # Default to empty

        # Infos additionnelles
        # Find the text corresponding to the stored integer value
        eval_qualite_str = str(self.maintenance_to_edit.evaluation_qualite)
        eval_text_to_set = next((opt for opt in self.EVALUATION_QUALITE_OPTIONS if opt.startswith(eval_qualite_str)), "")
        self.evaluation_combo.setCurrentText(eval_text_to_set)

        # Impact production is already a string, just handle None
        self.impact_combo.setCurrentText(self.maintenance_to_edit.impact_production or "")
        self.notes_edit.setText(self.maintenance_to_edit.notes_technicien or "")

        # Pièces utilisées
        # ATTENTION: Requires fetching InterventionPiece records and Piece details
        self._populate_pieces_table_for_edit()

    def _populate_pieces_table_for_edit(self):
        """ Remplit la table des pièces à partir des données de maintenance existante. """
        self.pieces_utilisees.clear()
        self.pieces_table.setRowCount(0)

        try:
            # Use the injected InterventionPieceRepository via the service
            intervention_pieces = self.maintenance_service.get_intervention_pieces_by_maintenance_id(self.maintenance_to_edit.id_maintenance)
            if not intervention_pieces:
                logger.debug("Aucune pièce trouvée pour ce rapport existant.")
                return

            all_piece_ids = [ip.piece_id for ip in intervention_pieces]
            # Fetch details for all pieces at once for efficiency
            pieces_details = self.stock_service.get_pieces_by_ids(all_piece_ids)
            
            logger.debug(f"{len(intervention_pieces)} pièces trouvées. Population de la table...")

            for ip in intervention_pieces:
                piece_detail = pieces_details.get(ip.piece_id)
                if not piece_detail:
                    logger.warning(f"Détail pièce ID {ip.piece_id} non trouvé pour rapport existant.")
                    continue

                piece_data = {
                    'piece_id': ip.piece_id,
                    'piece_ref': piece_detail.reference,
                    'piece_nom': piece_detail.nom,
                    'quantite': ip.quantite,  # Changed from quantite_utilisee to quantite
                    'lot': ip.lot or ''       # Changed from lot_ou_sn to lot
                }
                self.pieces_utilisees.append(piece_data)
                
                # Add row to pieces table
                row = self.pieces_table.rowCount()
                self.pieces_table.insertRow(row)
                
                # Store piece data in table
                id_item = QTableWidgetItem(str(piece_data['piece_id']))
                id_item.setData(Qt.ItemDataRole.UserRole, len(self.pieces_utilisees) - 1)
                self.pieces_table.setItem(row, 0, id_item)
                self.pieces_table.setItem(row, 1, QTableWidgetItem(str(piece_data['piece_ref'])))
                self.pieces_table.setItem(row, 2, QTableWidgetItem(str(piece_data['piece_nom'])))
                self.pieces_table.setItem(row, 3, QTableWidgetItem(str(piece_data['quantite'])))
                self.pieces_table.setItem(row, 4, QTableWidgetItem(str(piece_data['lot'])))

        except Exception as e:
            logger.exception(f"Erreur lors de la récupération/population des pièces pour le rapport existant {self.maintenance_to_edit.id_maintenance}")
            QMessageBox.warning(self, self.tr("Erreur Pièces"), self.tr("Impossible de charger les pièces pour ce rapport:\n%1").replace("%1", str(e)))

    def _update_remove_button_state(self):
         """ Active/désactive le bouton Supprimer Pièce basé sur la sélection. """
         # Activer/désactiver bouton suppression
         self.remove_piece_button.setEnabled(self.pieces_table.currentRow() >= 0)

    # --- Méthodes auxiliaires internes --- #

    def _validate_input(self) -> bool: # Version mise à jour
        """ Vérifie champs obligatoires du rapport. """
        if self.technicien_combo.currentData() is None:
             QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Sélectionnez le technicien.")); return False
        # Gérer si date/heure vide est permise (via specialValueText)
        if self.date_debut_edit.dateTime() <= self.date_debut_edit.minimumDateTime():
              QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Date/Heure Début obligatoire.")); return False
        if self.date_fin_edit.dateTime() <= self.date_fin_edit.minimumDateTime():
              QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Date/Heure Fin obligatoire.")); return False
        if self.date_debut_edit.dateTime() >= self.date_fin_edit.dateTime():
             QMessageBox.warning(self, self.tr("Dates Incohérentes"), self.tr("Fin doit être après Début.")); return False
        if not self.type_reel_combo.currentText():
             QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Sélectionnez le type réel.")); return False
        if not self.travaux_edit.toPlainText().strip():
             QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Décrivez les travaux.")); return False
        if not self.resultat_combo.currentText():
             QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Indiquez le résultat.")); return False
        # Optionnel: Valider que quantité pièce > 0? Fait à l'ajout.
        return True

    def accept(self):
        """ Surcharge pour valider avant de fermer (validation du rapport, pas des coûts). """
        if self._validate_input():
            logger.debug("Validation réussie, acceptation du dialogue.")
            # Sauvegarder le rapport et obtenir l'id maintenance
            data = self.get_maintenance_data()
            try:
                if self.maintenance_to_edit:
                    # Edition
                    data["id_maintenance"] = self.maintenance_to_edit.id_maintenance
                    maintenance = self.maintenance_service.update_maintenance(data)
                    maintenance_id = maintenance.id_maintenance if hasattr(maintenance, "id_maintenance") else None
                else:
                    # Création
                    maintenance = self.maintenance_service.record_maintenance(data)
                    maintenance_id = maintenance.id_maintenance if hasattr(maintenance, "id_maintenance") else None
                    self.maintenance_to_edit = maintenance
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de sauvegarder le rapport : %1").replace("%1", str(e)))
                return
            # Activer la section coûts et passer l'id
            self.couts_widget.set_maintenance_id(maintenance_id)
            self.couts_widget.setDisabled(False)
            self.validate_costs_button.setEnabled(True)
            QMessageBox.information(self, self.tr("Rapport validé"), self.tr("Le rapport a été validé. Vous pouvez maintenant ajouter les coûts externes et intervenants."))
            # Option : ne pas fermer le dialogue tout de suite
            # super().accept() # <-- décommenter pour fermer après validation
        else:
            logger.warning("Validation échouée, le dialogue reste ouvert.")

    def get_maintenance_data(self) -> Dict[str, Any]:
        """ Récupère les données du rapport COMPLET pour le service. """
        # ... (inchangé)
        debut_dt = self.date_debut_edit.dateTime().toPython() \
                   if self.date_debut_edit.dateTime() > self.date_debut_edit.minimumDateTime() else None
        fin_dt = self.date_fin_edit.dateTime().toPython() \
                 if self.date_fin_edit.dateTime() > self.date_fin_edit.minimumDateTime() else None

        # Eval/Impact
        eval_text = self.evaluation_combo.currentText()
        # Extract the number part (assuming format 'N - Text')
        eval_val = int(eval_text.split(' - ')[0]) if eval_text and eval_text[0].isdigit() else None
        impact_text = self.impact_combo.currentText(); impact_val = impact_text if impact_text else None

        data = {
            # Include id_maintenance if editing
            "id_maintenance": self.maintenance_to_edit.id_maintenance if self.maintenance_to_edit else None,
            "ot_id": self.ot_concerne.id_ot,
            "machine_id": self.ot_concerne.machine_id,
            "technicien_id": self.technicien_combo.currentData(),
            "date_debut_reelle": debut_dt, # datetime
            "date_fin_reelle": fin_dt,     # datetime
            "type_reel": self.type_reel_combo.currentText(),
            "description_travaux": self.travaux_edit.toPlainText().strip(),
            "resultat": self.resultat_combo.currentText(),
            # Optionnels
            "evaluation_qualite": eval_val, # Store the integer value
            "impact_production": impact_val,
            "notes_technicien": self.notes_edit.toPlainText().strip() or None,
            # --- Inclure la liste des pièces utilisées --- ##
            "pieces_utilisees": self.pieces_utilisees # Liste de dicts
            # --------------------------------------------
        }
        logger.debug(f"Données récupérées du MaintenanceReportDialog: {data}")
        return data

    def export_pdf_report(self):
        """Permet à l'utilisateur d'exporter le rapport de maintenance au format PDF."""
        try:
            # Récupérer toutes les données nécessaires pour le template
            maintenance_data = self.get_maintenance_data()
            ot = self.ot_concerne
            machine = getattr(self, self.tr('label_machine'), None)
            technicien_id = maintenance_data.get(self.tr("technicien_id"))
            technicien = None
            if technicien_id:
                try:
                    technicien = self.maintenance_service.get_technicien_by_id(technicien_id)
                except Exception as e:
                    logger.warning(f"Impossible de charger le technicien pour PDF: {e}")
            pieces_utilisees = maintenance_data.get("pieces_utilisees", [])
            # Récupérer les coûts depuis le widget
            couts = self.couts_widget.get_couts_for_report() if hasattr(self.couts_widget, 'get_couts_for_report') else {}

            # Demander où sauvegarder le PDF
            default_name = f"Rapport_OT_{ot.numero_ot or ot.id_ot}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Exporter le rapport PDF"), default_name, self.tr("PDF Files (*.pdf)"))
            if not file_path:
                return  # Annulé
            # Gérer l'extension
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'

            # Appeler la fonction utilitaire
            render_maintenance_report_pdf(
                maintenance=maintenance_data,
                ot=ot,
                machine=ot.machine if hasattr(ot, 'machine') else None,
                technicien=technicien,
                pieces_utilisees=pieces_utilisees,
                couts=couts,
                output_path=file_path
            )
            QMessageBox.information(self, self.tr("Export PDF"), self.tr("Rapport exporté avec succès :\n%1").replace("%1", str(file_path)))
            # Option: ouvrir le PDF automatiquement
            try:
                if os.name == 'nt':
                    os.startfile(file_path)
                else:
                    import subprocess
                    subprocess.Popen(['xdg-open', file_path])
            except Exception as e:
                logger.info(f"Impossible d'ouvrir le PDF automatiquement: {e}")
        except Exception as e:
            logger.exception(f"Erreur lors de l'export PDF: {e}")
            QMessageBox.critical(self, self.tr("Erreur Export PDF"), self.tr("Impossible d'exporter le PDF :\n%1").replace("%1", str(e)))