# gmao_app/app/ui/dialogs/commande_dialog.py
""" Dialogue pour créer ou modifier une commande d'achat et ses lignes. """
import logging
from typing import Optional, List, TYPE_CHECKING
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QMessageBox, QDateEdit,
                               QComboBox, QDoubleSpinBox, QTableWidget,
                               QTableWidgetItem, QAbstractItemView, QHeaderView,
                               QLabel, QDialogButtonBox, QTextEdit, QGroupBox, QWidget)
from PySide6.QtCore import Qt, QDate, Slot # <-- AJOUTER Slot ICI
from datetime import date, datetime
from app.utils.exceptions import DatabaseError

from app.core.services.achat_service import AchatService
from app.core.services.stock_service import StockService # Pour récupérer listes pièces/fournisseurs
from app.core.models.commande import Commande
from app.core.models.ligne_commande import LigneCommande
from app.core.models.fournisseur import Fournisseur # Pour ComboBox
from app.core.models.piece import Piece # Pour lookup
from app.core.models.utilisateur import Utilisateur
from app.utils.helpers import parse_iso_date, format_iso_date # Nos helpers
from app.utils.exceptions import GmaoPermissionError # Assurez-vous d'avoir cet import aussi
from app.utils.i18n import reverse_translate_purchase_order_status, translate_status # Pour mapper les statuts traduits vers français
# --- Dialogue de sélection ---
from app.ui.dialogs.piece_selection_dialog import PieceSelectionDialog

# Pour la sélection de pièce (à créer)
# from app.ui.dialogs.piece_selection_dialog import PieceSelectionDialog

if TYPE_CHECKING:
     from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)

class CommandeDialog(QDialog):
    """ Dialogue pour la gestion d'une commande et de ses lignes. """

    def _on_print_commande(self):
        """Slot appelé lors du clic sur le bouton Imprimer."""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            from PySide6.QtGui import QTextDocument
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            import os
            from datetime import datetime

            # Charger les données nécessaires
            commande = self.current_commande
            lignes = self.current_lignes
            fournisseur = None
            if commande and self.fournisseurs:
                fournisseur = next((f for f in self.fournisseurs if f.id_fournisseur == commande.fournisseur_id), None)

            # Préparer le moteur Jinja2
            template_dir = os.path.join(os.path.dirname(__file__), '../../templates')
            env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(['html', 'xml'])
            )
            template = env.get_template('commande_document_template.html')

            html_content = template.render(
                commande=commande,
                lignes=lignes,
                fournisseur=fournisseur,
                now=datetime.now()
            )

            # Aperçu avant impression
            doc = QTextDocument()
            doc.setHtml(html_content)
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimer le Bon de Commande")
            if dialog.exec() == QPrintDialog.Accepted:
                doc.print_(printer)
                QMessageBox.information(self, "Impression", "Le bon de commande a été envoyé à l'imprimante.")
            else:
                QMessageBox.information(self, "Impression annulée", "L'impression a été annulée.")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Erreur impression commande: {e}")
            QMessageBox.critical(self, "Erreur Impression", f"Impossible d'imprimer le bon de commande :\n{e}")

    def __init__(self, achat_service: AchatService, stock_service: StockService,
                 commande_id: Optional[int], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.achat_service = achat_service
        self.stock_service = stock_service # Pour lister fournisseurs/pièces
        self.commande_id = commande_id
        self.current_commande: Optional[Commande] = None
        self.current_lignes: List[LigneCommande] = []
        self.fournisseurs: List[Fournisseur] = [] # Cache pour ComboBox

        self.is_new_commande = self.commande_id is None
        self.setWindowTitle(self.tr("Nouvelle Commande") if self.is_new_commande else self.tr("Modifier Commande"))
        self.setMinimumSize(800, 600) # Taille minimale

        self._load_data()
        self._setup_ui()
        self._populate_fields()

        logger.info(f"CommandeDialog ouvert pour commande ID: {self.commande_id}")

    def _load_data(self):
        """ Charge les données nécessaires (commande, lignes, fournisseurs). """
        try:
            self.fournisseurs = self.stock_service.get_all_fournisseurs() # Fonction à ajouter/vérifier dans StockService
            if not self.fournisseurs:
                 logger.warning("Aucun fournisseur trouvé dans la base.")
                 # Peut-être afficher un message à l'utilisateur ?

            if not self.is_new_commande:
                details = self.achat_service.get_commande_details(self.commande_id)
                if details:
                    self.current_commande = details['commande']
                    self.current_lignes = details['lignes']
                else:
                    logger.error(f"Impossible de charger la commande ID {self.commande_id}")
                    # Gérer l'erreur (ex: fermer dialogue, afficher message)
                    QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger la commande ID {}.").format(self.commande_id))
                    # On pourrait appeler reject() ici pour fermer, mais setup_ui plantera peut-être avant
                    self.current_commande = None # Assurer que c'est None

        except Exception as e:
             logger.exception(f"Erreur lors du chargement des données pour CommandeDialog: {e}")
             QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Une erreur est survenue:\n{}" ).format(e))
             self.reject() # Fermer le dialogue en cas d'erreur critique


    def _setup_ui(self):
        """ Configure l'interface utilisateur du dialogue. """
        self.layout = QVBoxLayout(self)

        # --- Groupe Informations Commande ---
        commande_group = QGroupBox(self.tr("Informations Commande"))
        form_layout = QFormLayout()
        self.num_commande_edit = QLineEdit()
        self.fournisseur_combo = QComboBox()
        self.date_commande_edit = QDateEdit(date.today()) # Date du jour par défaut
        self.date_commande_edit.setCalendarPopup(True)
        self.date_commande_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_liv_prev_edit = QDateEdit()
        self.date_liv_prev_edit.setCalendarPopup(True)
        self.date_liv_prev_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_liv_prev_edit.setSpecialValueText(" ") # Afficher vide si pas de date
        self.date_liv_prev_edit.setDate(QDate()) # Date nulle au départ
        self.statut_combo = QComboBox() # Sera rempli et potentiellement ReadOnly
        self.ref_fournisseur_edit = QLineEdit()
        self.frais_port_spin = QDoubleSpinBox()
        self.frais_port_spin.setDecimals(2)
        self.frais_port_spin.setMaximum(99999.99)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80) # Limiter hauteur

        # Remplir ComboBox Fournisseur
        self.fournisseur_combo.addItem(self.tr("Sélectionnez..."), -1) # Placeholder
        for f in self.fournisseurs:
             self.fournisseur_combo.addItem(f.nom, f.id_fournisseur)

        # Remplir ComboBox Statut
        self.statut_combo.addItems([
            self.tr('Brouillon'), self.tr('Validee'), self.tr('Envoyee'),
            self.tr('Partielle'), self.tr('Livree'), self.tr('Annulee')
        ])

        form_layout.addRow(self.tr("Numéro Commande:"), self.num_commande_edit)
        form_layout.addRow(self.tr("Fournisseur:"), self.fournisseur_combo)
        form_layout.addRow(self.tr("Date Commande:"), self.date_commande_edit)
        form_layout.addRow(self.tr("Date Livraison Prévue:"), self.date_liv_prev_edit)
        form_layout.addRow(self.tr("Statut:"), self.statut_combo)
        form_layout.addRow(self.tr("Référence Fournisseur:"), self.ref_fournisseur_edit)
        form_layout.addRow(self.tr("Frais de Port:"), self.frais_port_spin)
        form_layout.addRow(self.tr("Notes:"), self.notes_edit)
        commande_group.setLayout(form_layout)
        self.layout.addWidget(commande_group)

        # --- Groupe Lignes de Commande ---
        lignes_group = QGroupBox(self.tr("Lignes de Commande"))
        lignes_layout = QVBoxLayout()
        # Barre d'actions pour les lignes
        lignes_action_layout = QHBoxLayout()
        self.add_ligne_button = QPushButton(self.tr("➕ Ajouter Pièce"))
        self.edit_ligne_button = QPushButton(self.tr("✏️ Modifier Ligne"))
        self.remove_ligne_button = QPushButton(self.tr("🗑️ Retirer Ligne"))
        self.print_button = QPushButton(self.tr("🖨️ Imprimer"))
        lignes_action_layout.addWidget(self.add_ligne_button)
        lignes_action_layout.addWidget(self.edit_ligne_button)
        lignes_action_layout.addWidget(self.remove_ligne_button)
        lignes_action_layout.addWidget(self.print_button)
        lignes_action_layout.addStretch()
        lignes_layout.addLayout(lignes_action_layout)

        # Table des lignes
        self.lignes_table = QTableWidget()
        self.lignes_table.setColumnCount(6) # ID_LIGNE(caché), PIECE_ID(caché), Réf. Pièce, Nom Pièce, Qté Cmd, PU HT
        self.lignes_table.setHorizontalHeaderLabels([
            self.tr("ID_LIGNE"), self.tr("PIECE_ID"), self.tr("Réf. Pièce"),
            self.tr("Désignation"), self.tr("Qté Cmd"), self.tr("PU HT")
        ])
        self.lignes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lignes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lignes_table.verticalHeader().setVisible(False)
        self.lignes_table.setColumnHidden(0, True) # Cacher ID Ligne
        self.lignes_table.setColumnHidden(1, True) # Cacher ID Pièce
        self.lignes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Nom pièce
        lignes_layout.addWidget(self.lignes_table)
        lignes_group.setLayout(lignes_layout)
        self.layout.addWidget(lignes_group)

        # --- Total Commande ---
        total_layout = QHBoxLayout()
        self.total_label = QLabel(self.tr("Total HT Commande: 0.00"))
        self.total_label.setStyleSheet("font-weight: bold;")
        total_layout.addStretch()
        total_layout.addWidget(self.total_label)
        self.layout.addLayout(total_layout)

        # --- Boutons OK / Annuler ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.button_box)

        # --- Connecter Signaux ---
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

        self.add_ligne_button.clicked.connect(self._on_add_ligne)
        self.edit_ligne_button.clicked.connect(self._on_edit_ligne)
        self.remove_ligne_button.clicked.connect(self._on_remove_ligne)
        self.print_button.clicked.connect(self._on_print_commande)
        self.lignes_table.itemSelectionChanged.connect(self._update_ligne_button_states)
        self.lignes_table.doubleClicked.connect(self._on_edit_ligne)

        # Désactiver boutons lignes au départ
        self._update_ligne_button_states()

        # Gérer l'état éditable en fonction du statut
        self._update_edit_state()

    def _populate_fields(self):
        """ Remplit les champs avec les données de la commande actuelle (si modification). """
        if self.current_commande:
            self.num_commande_edit.setText(self.current_commande.numero_commande or "")
            self.date_commande_edit.setDate(QDate(self.current_commande.date_commande))
            if self.current_commande.date_livraison_prevue:
                 self.date_liv_prev_edit.setDate(QDate(self.current_commande.date_livraison_prevue))
            else:
                 self.date_liv_prev_edit.setDate(QDate()) # Date nulle
            self.frais_port_spin.setValue(self.current_commande.frais_port)
            self.ref_fournisseur_edit.setText(self.current_commande.reference_fournisseur or "")
            self.notes_edit.setText(self.current_commande.notes_commande or "")

            # Sélectionner le fournisseur
            fourn_index = self.fournisseur_combo.findData(self.current_commande.fournisseur_id)
            if fourn_index != -1:
                 self.fournisseur_combo.setCurrentIndex(fourn_index)

             # Sélectionner le statut - traduire la valeur DB vers la langue courante
            statut_translated = translate_status(self.current_commande.statut)
            self.statut_combo.setCurrentText(statut_translated)

            # Remplir la table des lignes
            self.lignes_table.setRowCount(0) # Effacer d'abord
            piece_cache = {} # Cache pour éviter N requêtes get_piece_by_id
            for ligne in self.current_lignes:
                 row_position = self.lignes_table.rowCount()
                 self.lignes_table.insertRow(row_position)

                 # Récupérer info pièce (optimisé avec cache)
                 piece = piece_cache.get(ligne.piece_id)
                 if not piece:
                     try:
                         piece = self.stock_service.get_piece_by_id(ligne.piece_id) # Fonction à vérifier/ajouter dans StockService
                         if piece: piece_cache[ligne.piece_id] = piece
                     except Exception: # Ignorer si pièce non trouvée pour l'instant
                          piece = None

                 ref_piece = piece.reference if piece else "???"
                 nom_piece = piece.nom if piece else "Pièce Inconnue"

                 id_ligne_item = QTableWidgetItem(str(ligne.id_ligne))
                 id_ligne_item.setData(Qt.ItemDataRole.UserRole, ligne.id_ligne) # Stocker l'ID
                 id_piece_item = QTableWidgetItem(str(ligne.piece_id)) # Stocker ID pièce aussi

                 self.lignes_table.setItem(row_position, 0, id_ligne_item)
                 self.lignes_table.setItem(row_position, 1, id_piece_item)
                 self.lignes_table.setItem(row_position, 2, QTableWidgetItem(ref_piece))
                 self.lignes_table.setItem(row_position, 3, QTableWidgetItem(nom_piece))
                 self.lignes_table.setItem(row_position, 4, QTableWidgetItem(str(ligne.quantite_commandee)))
                 self.lignes_table.setItem(row_position, 5, QTableWidgetItem(f"{ligne.prix_unitaire_ht:.2f}"))

            self._update_total_label()
        else:
             # Nouvelle commande, champs par défaut - traduire le statut par défaut
             default_status_translated = translate_status("Brouillon")
             self.statut_combo.setCurrentText(default_status_translated)
             self.date_liv_prev_edit.setDate(QDate()) # Date nulle
             self._update_total_label()

    def _update_edit_state(self):
        """ Active/désactive les champs et boutons selon le statut de la commande. """
        is_editable = self.is_new_commande or (self.current_commande and self.current_commande.statut == 'Brouillon')

        # Champs commande
        self.num_commande_edit.setReadOnly(not is_editable)
        self.fournisseur_combo.setEnabled(is_editable)
        self.date_commande_edit.setReadOnly(not is_editable)
        self.date_liv_prev_edit.setReadOnly(not is_editable)
        self.ref_fournisseur_edit.setReadOnly(not is_editable)
        self.frais_port_spin.setReadOnly(not is_editable)
        self.notes_edit.setReadOnly(not is_editable)

        # Statut : Jamais directement modifiable ici? Sauf admin?
        # Pour l'instant, on le laisse modifiable mais le service pourrait le bloquer
        # self.statut_combo.setEnabled(is_editable) # Ou False?

        # Boutons lignes
        self.add_ligne_button.setEnabled(is_editable)
        # Les boutons edit/remove dépendent aussi de la sélection et de is_editable
        self._update_ligne_button_states() # Appelle cette fonction qui prendra en compte is_editable

        # Bouton OK
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True) # Toujours actif, la logique est dans _on_accept

    def _update_ligne_button_states(self):
        """ Active/désactive les boutons de gestion des lignes. """
        is_editable = self.is_new_commande or (self.current_commande and self.current_commande.statut == 'Brouillon')
        has_selection = bool(self.lignes_table.selectedItems()) # Vérifie s'il y a une sélection

        self.edit_ligne_button.setEnabled(is_editable and has_selection)
        self.remove_ligne_button.setEnabled(is_editable and has_selection)
        # add_ligne_button est déjà géré par _update_edit_state

    def _update_total_label(self):
         """ Met à jour le label affichant le total HT. """
         total = 0.0
         for row in range(self.lignes_table.rowCount()):
             try:
                 qte_item = self.lignes_table.item(row, 4)
                 pu_item = self.lignes_table.item(row, 5)
                 if qte_item and pu_item:
                     total += int(qte_item.text()) * float(pu_item.text())
             except (ValueError, TypeError):
                  logger.warning(self.tr("Erreur calcul total sur ligne {}").format(row))
                  continue # Ignorer ligne si erreur
         self.total_label.setText(self.tr("Total HT Commande: {}").format(f"{total:.2f}"))


    @Slot() # type: ignore
    def _on_add_ligne(self):
        """ Ouvre un dialogue pour sélectionner une référence de pièce, quantité et lot, puis ajoute la ligne à la commande. """
        logger.debug(self.tr("Action: Ajouter Ligne via PieceReferenceDialog"))
        from app.ui.dialogs.piece_reference_dialog import PieceReferenceDialog
        dialog = PieceReferenceDialog(self.stock_service, parent=self)
        if dialog.exec():
            piece_data = dialog.selected_piece_data
            if not piece_data:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Aucune pièce sélectionnée."))
                return
            piece_id = piece_data.get('id_piece')
            reference = piece_data.get('reference')
            nom = piece_data.get('nom')
            unite = piece_data.get('unite')
            categorie = piece_data.get('categorie')
            pu = piece_data.get('prix_unitaire', 0.0)
            quantite = piece_data.get('quantite')
            lot = piece_data.get('lot')
            # Vérifier si pièce déjà dans table
            for row in range(self.lignes_table.rowCount()):
                if self.lignes_table.item(row, 1).text() == str(piece_id):
                    QMessageBox.warning(self, self.tr("Doublon"), self.tr("La pièce '{}' est déjà dans la commande.").format(nom))
                    return
            # Ajouter à la table UI
            row_position = self.lignes_table.rowCount()
            self.lignes_table.insertRow(row_position)
            id_ligne_item = QTableWidgetItem("") # Pas d'ID tant que pas sauvegardé
            id_ligne_item.setData(Qt.ItemDataRole.UserRole, None) # Marquer comme nouvelle ligne
            id_piece_item = QTableWidgetItem(str(piece_id))
            self.lignes_table.setItem(row_position, 0, id_ligne_item)
            self.lignes_table.setItem(row_position, 1, id_piece_item)
            self.lignes_table.setItem(row_position, 2, QTableWidgetItem(reference))
            self.lignes_table.setItem(row_position, 3, QTableWidgetItem(nom))
            self.lignes_table.setItem(row_position, 4, QTableWidgetItem(str(quantite)))
            self.lignes_table.setItem(row_position, 5, QTableWidgetItem(f"{pu:.2f}"))
            # Ajout colonne lot si nécessaire ou stockage dans UserRole
            if self.lignes_table.columnCount() < 7:
                self.lignes_table.insertColumn(6)
                self.lignes_table.setHorizontalHeaderItem(6, QTableWidgetItem(self.tr("Lot")))
            self.lignes_table.setItem(row_position, 6, QTableWidgetItem(lot if lot else ""))
            self._update_total_label()


    @Slot() # type: ignore
    def _on_edit_ligne(self):
        """ Modifie la quantité/PU de la ligne sélectionnée. """
        selected_row = self.lignes_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("Sélection requise"), self.tr("Veuillez sélectionner une ligne à modifier."))
            return

        # Récupérer les infos actuelles depuis la table
        id_ligne = self.lignes_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole) # Peut être None si nouvelle ligne
        piece_id = int(self.lignes_table.item(selected_row, 1).text())
        nom_piece = self.lignes_table.item(selected_row, 3).text()
        current_qte = int(self.lignes_table.item(selected_row, 4).text())
        current_pu = float(self.lignes_table.item(selected_row, 5).text())

        logger.debug(self.tr("Action: Modifier Ligne (UI row {} , ID Ligne {}, Piece ID {})" ).format(selected_row, id_ligne, piece_id))

        # Dialogue simple pour modifier qté/PU (similaire à add)
        from PySide6.QtWidgets import QInputDialog, QFormLayout, QSpinBox, QDoubleSpinBox
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Modifier Ligne - {}").format(nom_piece))
        layout = QFormLayout(dialog)
        qte_spin = QSpinBox()
        qte_spin.setMinimum(1)
        qte_spin.setMaximum(9999)
        qte_spin.setValue(current_qte)
        pu_spin = QDoubleSpinBox()
        pu_spin.setDecimals(2)
        pu_spin.setMaximum(99999.99)
        pu_spin.setValue(current_pu)
        layout.addRow(self.tr("Quantité:"), qte_spin)
        layout.addRow(self.tr("Prix Unitaire HT:"), pu_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec():
             new_qte = qte_spin.value()
             new_pu = pu_spin.value()
             # Mettre à jour la table UI
             self.lignes_table.item(selected_row, 4).setText(str(new_qte))
             self.lignes_table.item(selected_row, 5).setText(f"{new_pu:.2f}")
             self._update_total_label()
             logger.info(f"Ligne (UI row {selected_row}) modifiée dans l'interface.")


    @Slot() # type: ignore
    def _on_remove_ligne(self):
        """ Supprime la ligne sélectionnée de la table UI. """
        selected_row = self.lignes_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("Sélection requise"), self.tr("Veuillez sélectionner une ligne à retirer."))
            return

        id_ligne = self.lignes_table.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        nom_piece = self.lignes_table.item(selected_row, 3).text()
        logger.debug(f"Action: Retirer Ligne (UI row {selected_row}, ID Ligne {id_ligne})")

        reply = QMessageBox.question(self, self.tr("Confirmation"), self.tr("Retirer la ligne pour '{}' de la commande ?").format(nom_piece),
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
             self.lignes_table.removeRow(selected_row)
             self._update_total_label()
             # La suppression réelle en DB se fera lors du _on_accept

    # --- AJOUT: Méthode pour récupérer ID utilisateur (à adapter) ---
    # --- Utiliser ce code pour la méthode de récupération ---
    def _get_current_user_object(self) -> Optional[Utilisateur]:
        """ Récupère l'objet Utilisateur connecté depuis MainWindow. """
        # Vérification que parent est bien MainWindow et a l'attribut current_user
        main_window = self.parent()
        logger.debug(f"Parent de CommandeDialog pour user object: {main_window} (type: {type(main_window)})")

        if hasattr(main_window, 'current_user') and isinstance(main_window.current_user, Utilisateur):
             user_obj = main_window.current_user
             logger.debug(f"Objet utilisateur courant récupéré: {user_obj}")
             return user_obj
        else:
             has_attr = hasattr(main_window, 'current_user')
             attr_type = type(getattr(main_window, 'current_user', None)) if main_window else 'Parent None'
             logger.error(f"Impossible de récupérer l'objet current_user depuis {main_window}. hasattr={has_attr}, type={attr_type}")
             return None
    
    
    # --- Méthode _on_accept refactorisée ---
    @Slot() # type: ignore
    def _on_accept(self):
        """ Sauvegarde la commande et ses lignes après validation. """
        logger.info(self.tr("Attempting to save order ID: {}.").format(self.commande_id or self.tr('New')))
        # Désactiver bouton OK pour éviter double-clic
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(False)

        # Récupérer l'utilisateur courant d'abord
        current_user_obj = self._get_current_user_object()
        if not current_user_obj:
             QMessageBox.critical(self, self.tr("Critical Error"), self.tr("Unable to identify the current user."))
             ok_button.setEnabled(True) # Réactiver
             return

        # 1. Récupérer et Valider les données de l'en-tête depuis l'UI
        try:
            numero_commande = self.num_commande_edit.text().strip() or None
            fournisseur_id = self.fournisseur_combo.currentData()
            date_commande = self.date_commande_edit.date().toPython()
            qdate_liv = self.date_liv_prev_edit.date()
            date_livraison_prevue = qdate_liv.toPython() if qdate_liv.isValid() and not qdate_liv.isNull() else None
            # Convert translated status back to French for database
            statut_translated = self.statut_combo.currentText()
            statut = reverse_translate_purchase_order_status(statut_translated)
            frais_port = self.frais_port_spin.value()
            reference_fournisseur = self.ref_fournisseur_edit.text().strip() or None
            notes_commande = self.notes_edit.toPlainText().strip() or None

            if fournisseur_id == -1:
                 raise ValueError(self.tr("Please select a supplier."))
            if date_commande > date.today():
                 raise ValueError(self.tr("The order date cannot be in the future."))

        except ValueError as ve: # Attrape les erreurs de validation UI
             QMessageBox.warning(self, self.tr("Invalid Data"), str(ve))
             ok_button.setEnabled(True)
             return
        except Exception as e:
             logger.error(self.tr("Error retrieving header data: {}.").format(e))
             QMessageBox.critical(self, self.tr("Internal Error"), self.tr("Error reading fields:\n{}" ).format(e))
             ok_button.setEnabled(True)
             return

        # 2. Récupérer les données des lignes depuis la QTableWidget UI
        lignes_ui = []
        try:
            for row in range(self.lignes_table.rowCount()):
                 ligne_ui_data = {
                     'id_ligne': self.lignes_table.item(row, 0).data(Qt.ItemDataRole.UserRole),
                     'piece_id': int(self.lignes_table.item(row, 1).text()),
                     'quantite_commandee': int(self.lignes_table.item(row, 4).text()),
                     'prix_unitaire_ht': float(self.lignes_table.item(row, 5).text())
                 }
                 if ligne_ui_data['quantite_commandee'] <= 0 or ligne_ui_data['prix_unitaire_ht'] < 0:
                      raise ValueError(f"Quantité ou PU invalide à la ligne {row + 1}.")
                 lignes_ui.append(ligne_ui_data)
        except (ValueError, TypeError, AttributeError, IndexError) as e:
             logger.error(self.tr("Error retrieving line data from UI: {}.").format(e))
             QMessageBox.critical(self, self.tr("Line Data Error"), self.tr("Error reading table lines:\n{}" ).format(e))
             ok_button.setEnabled(True)
             return

        # --- Logique de Sauvegarde ---
        errors_occurred = [] # Pour lister les erreurs non bloquantes sur les lignes
        saved_commande_id = self.commande_id # Garder une trace

        try:
            if self.is_new_commande:
                # --- CRÉATION ---
                logger.info(self.tr("Creating a new order by {}...").format(current_user_obj.login))
                commande_data_for_service = {
                     'numero_commande': numero_commande, 'fournisseur_id': fournisseur_id,
                     'date_commande': date_commande, 'date_livraison_prevue': date_livraison_prevue,
                     'statut': statut, 'frais_port': frais_port,
                     'reference_fournisseur': reference_fournisseur, 'notes_commande': notes_commande
                 }
                # Appel au service avec l'objet utilisateur
                created_commande = self.achat_service.create_commande(
    commande_data_for_service,
    current_user_obj.id_utilisateur,
    current_user_obj.role
)

                if not created_commande or not created_commande.id_commande:
                     raise ValueError(self.tr("Unable to create order header (ID not returned).")) # Le service devrait lever DatabaseError normalement

                saved_commande_id = created_commande.id_commande
                logger.info(self.tr("Order header created with ID: {}.").format(saved_commande_id))

                # Ajouter les lignes
                for ligne_data in lignes_ui:
                     ligne_data_for_service = {
                         'commande_id': saved_commande_id, 'piece_id': ligne_data['piece_id'],
                         'quantite_commandee': ligne_data['quantite_commandee'], 'prix_unitaire_ht': ligne_data['prix_unitaire_ht']
                     }
                     try:
                         self.achat_service.add_ligne_commande(ligne_data_for_service)
                     except Exception as e_ligne:
                          msg = self.tr("Error adding line for part ID {}: {}" ).format(ligne_data['piece_id'], e_ligne)
                          logger.error(msg)
                          errors_occurred.append(msg)

            else: # --- MISE À JOUR ---
                 logger.info(self.tr("Updating order ID: {} by {}...").format(saved_commande_id, current_user_obj.login))
                 if not self.current_commande:
                     raise ValueError(self.tr("Reference to current order (self.current_commande) lost."))

                 # 1. Mettre à jour l'objet self.current_commande avec les données de l'UI
                 self.current_commande.numero_commande = numero_commande
                 self.current_commande.fournisseur_id = fournisseur_id
                 self.current_commande.date_commande = date_commande
                 self.current_commande.date_livraison_prevue = date_livraison_prevue
                 self.current_commande.statut = statut
                 self.current_commande.frais_port = frais_port
                 self.current_commande.reference_fournisseur = reference_fournisseur
                 self.current_commande.notes_commande = notes_commande

                 # 2. Appeler le service pour mettre à jour l'en-tête (passe l'utilisateur pour les droits)
                 success_header = self.achat_service.update_commande(self.current_commande, current_user_obj)
                 if not success_header:
                      # Si update_commande retourne False sans lever d'erreur (peu probable avec notre implémentation)
                      raise ValueError("La mise à jour de l'en-tête a échoué sans erreur spécifique.")
                 logger.info(self.tr("Order header ID {} updated.").format(saved_commande_id))

                 # 3. Synchroniser les lignes
                 ids_lignes_ui = {l['id_ligne'] for l in lignes_ui if l['id_ligne'] is not None}
                 ids_lignes_db = {l.id_ligne for l in self.current_lignes if l.id_ligne is not None}

                 lignes_a_supprimer = ids_lignes_db - ids_lignes_ui
                 lignes_a_ajouter_ui = [l for l in lignes_ui if l['id_ligne'] is None]
                 lignes_a_verifier_maj_ui = {l['id_ligne']: l for l in lignes_ui if l['id_ligne'] is not None}

                 # Suppression
                 for ligne_id_to_delete in lignes_a_supprimer:
                      try:
                          # remove_ligne_commande a-t-il besoin de l'utilisateur pour les droits? Si oui, ajouter l'appelant
                          self.achat_service.remove_ligne_commande(ligne_id_to_delete)
                          logger.info(self.tr("Line ID {} deleted.").format(ligne_id_to_delete))
                      except Exception as e_ligne:
                           msg = self.tr("Error deleting line ID {}: {}" ).format(ligne_id_to_delete, e_ligne)
                           logger.error(msg)
                           errors_occurred.append(msg)

                 # Ajout
                 for ligne_add_data in lignes_a_ajouter_ui:
                      ligne_data_for_service = {
                         'commande_id': saved_commande_id, 'piece_id': ligne_add_data['piece_id'],
                         'quantite_commandee': ligne_add_data['quantite_commandee'], 'prix_unitaire_ht': ligne_add_data['prix_unitaire_ht']
                      }
                      try:
                          # add_ligne_commande a-t-il besoin de l'utilisateur pour les droits? Si oui, ajouter l'appelant
                           self.achat_service.add_ligne_commande(ligne_data_for_service)
                      except Exception as e_ligne:
                           msg = self.tr("Error adding line for part ID {}: {}" ).format(ligne_add_data['piece_id'], e_ligne)
                           logger.error(msg)
                           errors_occurred.append(msg)

                 # Mise à jour (comparaison qté/PU)
                 for ligne_db in self.current_lignes:
                      if ligne_db.id_ligne in lignes_a_verifier_maj_ui:
                          ligne_ui = lignes_a_verifier_maj_ui[ligne_db.id_ligne]
                          if ligne_db.quantite_commandee != ligne_ui['quantite_commandee'] or \
                             abs(ligne_db.prix_unitaire_ht - ligne_ui['prix_unitaire_ht']) > 0.001:
                               logger.debug(self.tr("Update detected for line ID {}.").format(ligne_db.id_ligne))
                               try:
                                   data_to_update = {
                                       'quantite_commandee': ligne_ui['quantite_commandee'],
                                       'prix_unitaire_ht': ligne_ui['prix_unitaire_ht']
                                   }
                                   # update_ligne_commande a-t-il besoin de l'utilisateur pour les droits? Si oui, ajouter l'appelant
                                   self.achat_service.update_ligne_commande(ligne_db.id_ligne, data_to_update)
                               except Exception as e_ligne:
                                    msg = self.tr("Error updating line ID {}: {}" ).format(ligne_db.id_ligne, e_ligne)
                                    logger.error(msg)
                                    errors_occurred.append(msg)

            # --- Fin Création / Mise à jour ---

            # Message final et fermeture si succès (même partiel)
            if errors_occurred:
                 error_details = "\n - ".join(errors_occurred)
                 QMessageBox.warning(self, self.tr("Partial Save"), self.tr("Order saved, but errors occurred on some lines:\n - {}" ).format(error_details))
            else:
                 QMessageBox.information(self, self.tr("Success"), self.tr("Order saved successfully."))

            self.accept() # Fermer le dialogue

        except GmaoPermissionError as pe: # Attraper l'erreur de permission spécifiquement
             logger.warning(self.tr("Permission denied when saving order ID {}: {}" ).format(saved_commande_id or self.tr('New'), pe))
             QMessageBox.warning(self, self.tr("Access Denied"), str(pe))
             ok_button.setEnabled(True) # Réactiver bouton
        except (DatabaseError, ValueError, NotImplementedError) as e: # Attraper autres erreurs attendues
             logger.error(self.tr("Failed to save order ID {}: {}" ).format(saved_commande_id or self.tr('New'), e))
             QMessageBox.critical(self, self.tr("Save Error"), self.tr("Unable to save order:\n{}" ).format(e))
             ok_button.setEnabled(True) # Réactiver bouton
        except Exception as e: # Attraper toute autre erreur inattendue
             logger.exception(self.tr("Unexpected error saving order ID {}: {}" ).format(saved_commande_id or self.tr('New'), e))
             QMessageBox.critical(self, self.tr("Unexpected Error"), self.tr("A server error occurred:\n{}" ).format(e))
             ok_button.setEnabled(True) # Réactiver bouton

    # ... (le reste de CommandeDialog: _on_add_ligne, _on_edit_ligne, _on_remove_ligne, etc.) ...