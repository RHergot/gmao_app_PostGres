# gmao_app/app/ui/views/piece_view.py
"""
Widget pour afficher et gérer la liste des Pièces détachées.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QLabel, QLineEdit, QComboBox, QDialog # Ajouts filtres
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional, Dict, Any

from app.core.models.piece import Piece
from app.core.models.fournisseur import Fournisseur # Pour map filtre
from app.core.services.stock_service import StockService, VALID_PIECE_STATUS # Service et constantes
from app.ui.dialogs.piece_dialog import PieceDialog
from app.ui.dialogs.stock_adjustment_dialog import StockAdjustmentDialog # <-- Importer le nouveau dialogue
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class PieceView(QWidget):
    """Vue pour la gestion des Pièces."""

    def __init__(self, stock_service: StockService, parent=None):
        super().__init__(parent)
        self.stock_service = stock_service
        self.current_pieces: List[Piece] = []
        self.fournisseurs_map: Dict[int, str] = {} # Cache noms fournisseurs

        logger.debug("Initialisation de PieceView...")

        # --- Filtres ---
        self.filter_ref_nom_input = QLineEdit(placeholderText=self.tr("Filtrer par Réf/Nom..."))
        self.filter_categorie_input = QLineEdit(placeholderText=self.tr("Catégorie..."))
        self.filter_statut_combo = QComboBox()
        self.filter_fours_combo = QComboBox()
        self.clear_filters_button = QPushButton(self.tr("Effacer Filtres"))
        self._populate_filter_combos()

        filter_layout1 = QHBoxLayout()
        filter_layout1.addWidget(QLabel(self.tr("Filtres:")))
        filter_layout1.addWidget(self.filter_ref_nom_input, 1)
        filter_layout1.addWidget(QLabel(self.tr("Catégorie:")))
        filter_layout1.addWidget(self.filter_categorie_input)

        filter_layout2 = QHBoxLayout()
        filter_layout2.addWidget(QLabel(self.tr("Statut:")))
        filter_layout2.addWidget(self.filter_statut_combo)
        filter_layout2.addWidget(QLabel(self.tr("Fourn. Préf.:")))
        filter_layout2.addWidget(self.filter_fours_combo)
        filter_layout2.addStretch()
        filter_layout2.addWidget(self.clear_filters_button)

        # --- Table ---
        self.table_widget = QTableWidget(self)
        self.setup_table()

        # --- Boutons ---
        self.add_button = QPushButton(self.tr("Ajouter Pièce"))
        self.edit_button = QPushButton(self.tr("Modifier Pièce"))
        self.delete_button = QPushButton(self.tr("Supprimer Pièce"))
        self.adjust_stock_button = QPushButton(self.tr("Ajuster Stock")) # <-- Nouveau bouton
        # TODO: Bouton "Mouvement Stock" ou "Ajustement" plus tard # <-- TODO peut être retiré
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))

        # --- Layouts ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.adjust_stock_button) # <-- Ajouter le bouton au layout
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(filter_layout1); main_layout.addLayout(filter_layout2)
        main_layout.addWidget(self.table_widget); main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- Connexions & Init ---
        self.connect_signals()
        self._update_button_states()
        self.refresh_pieces()
        logger.debug("PieceView initialisée.")

    def setup_table(self):
        """ Configure la table. """
        # ID(0,hid), Ref(1), Nom(2), Unite(3), Cat(4), Stock(5), Alerte(6), Prix(7), Statut(8), Fours(9)
        self.table_widget.setColumnCount(10)
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Référence"), self.tr("Nom / Description"), self.tr("Unité"), self.tr("Catégorie"),
            self.tr("Stock Actuel"), self.tr("Seuil Alerte"), self.tr("Prix Unit."), self.tr("Statut"), self.tr("Fourn. Préf.")
        ])
        # Config standard
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Ref
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Unite
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Cat
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Stock
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Alerte
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Prix
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Statut
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Interactive) # Fourn

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 2; self._sort_order = Qt.SortOrder.AscendingOrder # Nom par défaut


    def _populate_filter_combos(self):
        """ Remplit combobox Statut et Fournisseur. """
        try: self._load_fournisseurs_map()
        except Exception as e: logger.error(f"{e}"); QMessageBox.warning(self, self.tr("Erreur"), str(e))

        self.filter_statut_combo.clear(); self.filter_statut_combo.addItem(self.tr("Tous"))
        self.filter_statut_combo.addItems(VALID_PIECE_STATUS)

        self.filter_fours_combo.clear(); self.filter_fours_combo.addItem(self.tr("Tous"), None)
        sorted_f = sorted(self.fournisseurs_map.items(), key=lambda item: item[1])
        for f_id, f_nom in sorted_f: self.filter_fours_combo.addItem(f_nom, f_id)

    def _load_fournisseurs_map(self):
         try:
             fours = self.stock_service.get_all_fournisseurs()
             self.fournisseurs_map = {f.id_fournisseur: f.nom for f in fours if f.id_fournisseur}
         except Exception as e: logger.error(f"Err load Fours map: {e}"); self.fournisseurs_map={}; raise BusinessLogicError(f"{e}")

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_piece)
        self.edit_button.clicked.connect(self.edit_piece)
        self.delete_button.clicked.connect(self.delete_piece)
        self.refresh_button.clicked.connect(self.refresh_pieces)
        self.adjust_stock_button.clicked.connect(self.adjust_stock) # <-- Connecter le nouveau bouton
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_piece)
        # Filtres
        self.filter_ref_nom_input.textChanged.connect(self.apply_filters)
        self.filter_categorie_input.textChanged.connect(self.apply_filters)
        self.filter_statut_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_fours_combo.currentIndexChanged.connect(self.apply_filters)
        self.clear_filters_button.clicked.connect(self.clear_filters)

    def _update_button_states(self):
         has_selection = self.table_widget.selectionModel().hasSelection()
         self.edit_button.setEnabled(has_selection)
         self.delete_button.setEnabled(has_selection)
         self.adjust_stock_button.setEnabled(has_selection) # <-- Gérer l'état du nouveau bouton

    # Dans PieceView
    # Dans PieceView

       # Dans PieceView

    # Dans PieceView

    def _get_selected_piece_id(self) -> Optional[int]:
        """Retourne l'ID de la pièce sélectionnée ou None."""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            logger.debug("_get_selected_piece_id: Aucune ligne sélectionnée.")
            return None

        first_row_index = selected_rows[0].row()
        # Essayer de récupérer l'item de la colonne 0
        id_item = self.table_widget.item(first_row_index, 0)
        # --- CODE COMPLET SUGGÉRÉ PAR VSCODE (et correct) ---
        if id_item:
            # Essayer de récupérer la donnée UserRole
            item_data = id_item.data(Qt.ItemDataRole.UserRole)
            # Vérifier si la donnée existe ET peut être convertie en int
            if item_data is not None:
                try:
                    piece_id = int(item_data)
                    logger.debug(f"_get_selected_piece_id: ID récupéré: {piece_id}")
                    return piece_id
                except (ValueError, TypeError) as e:
                        logger.error(f"_get_selected_piece_id: Erreur conversion ID en int pour data '{item_data}' ligne {first_row_index}: {e}")
                        # return None # Retourner None si conversion échoue implicitement à la fin
            else:
                    logger.warning(f"_get_selected_piece_id: Aucune donnée UserRole trouvée pour l'item ID ligne {first_row_index}.")
                    # Vérifions ce que contient l'item textuellement pour aider au debug
                    logger.warning(f"_get_selected_piece_id: Texte de l'item: '{id_item.text()}'")
                    # return None # Implicite
        else:
                logger.warning(f"_get_selected_piece_id: Impossible de récupérer l'item de la cellule (L:{first_row_index}, C:0).")
                # return None # Implicite

        # Si on arrive ici, c'est qu'on n'a pas pu récupérer l'ID
        return None
        # --- FIN CODE COMPLET ---
            
    def refresh_data(self): self.refresh_pieces()

    @Slot()
    def refresh_pieces(self):
        """ Recharge la liste des pièces. """
        logger.info("Rafraîchissement liste pièces...")
        filters = self._get_current_filters()
        sort_col_name = self._get_sort_column_name()
        sort_desc = self._sort_order == Qt.SortOrder.DescendingOrder
        # Recharger map fournisseurs
        try: self._load_fournisseurs_map()
        except Exception as e: logger.error(f"Err reload Fours map: {e}")

        try:
            self.current_pieces = self.stock_service.get_all_pieces(
                filters=filters, sort_by=sort_col_name, sort_desc=sort_desc)
            self.populate_table(self.current_pieces)
            logger.info(f"{len(self.current_pieces)} pièces affichées.")
        except Exception as e: QMessageBox.critical(self,"Erreur",f"{e}"); logger.exception("Err refresh pieces")

    def populate_table(self, pieces: List[Piece]):
        """ Remplit la table pièces. """
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0); self.table_widget.setRowCount(len(pieces))
        for row, p in enumerate(pieces):
            id_item = QTableWidgetItem(str(p.id_piece)); id_item.setData(Qt.ItemDataRole.UserRole, p.id_piece)
            stock_str = str(p.stock_actuel or 0)
            alert_str = str(p.stock_alerte or 0)
            prix_str = f"{p.prix_unitaire:.2f}" if p.prix_unitaire is not None else ""
            fours_nom = self.fournisseurs_map.get(p.fournisseur_pref_id, "") if p.fournisseur_pref_id else ""

            # Créer items
            item_id = id_item
            item_ref = QTableWidgetItem(p.reference or ""); item_nom = QTableWidgetItem(p.nom or "")
            item_unit = QTableWidgetItem(p.unite or ""); item_cat = QTableWidgetItem(p.categorie or "")
            item_stock = QTableWidgetItem(stock_str); item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_alert = QTableWidgetItem(alert_str); item_alert.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_prix = QTableWidgetItem(prix_str); item_prix.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_statut = QTableWidgetItem(p.statut or ""); item_statut.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_fours = QTableWidgetItem(fours_nom)

            # Remplir ligne
            self.table_widget.setItem(row, 0, item_id); self.table_widget.setItem(row, 1, item_ref)
            self.table_widget.setItem(row, 2, item_nom); self.table_widget.setItem(row, 3, item_unit)
            self.table_widget.setItem(row, 4, item_cat); self.table_widget.setItem(row, 5, item_stock)
            self.table_widget.setItem(row, 6, item_alert); self.table_widget.setItem(row, 7, item_prix)
            self.table_widget.setItem(row, 8, item_statut); self.table_widget.setItem(row, 9, item_fours)

            # Style si stock bas
            if p.stock_alerte is not None and p.stock_alerte > 0 and p.stock_actuel <= p.stock_alerte:
                for col in range(1, self.table_widget.columnCount()):
                     item = self.table_widget.item(row, col);
                     if item: item.setBackground(Qt.GlobalColor.yellow) # Ou rouge pâle?

        self._update_button_states(); self.table_widget.setSortingEnabled(True)
        self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)


    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Tri la table. """
        if self._sort_column == logical_index: self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else: self._sort_column = logical_index; self._sort_order = Qt.SortOrder.AscendingOrder
        self.refresh_pieces()

    def _get_sort_column_name(self) -> str:
         """ Nom attribut/colonne DB pour tri. """
         # Attention: tri sur Fournisseur Nom pas direct sur ID
         column_map = { 1: "reference", 2: "nom", 3: "unite", 4: "categorie", 5: "stock_actuel", 6: "stock_alerte", 7: "prix_unitaire", 8: "statut", 9: "fournisseur_pref_id" }
         return column_map.get(self._sort_column, "nom")

    @Slot()
    def apply_filters(self): self.refresh_pieces()

    def _get_current_filters(self) -> Dict[str, Any]:
        """ Construit le dict de filtres pour le service. """
        filters = {}
        ref_nom = self.filter_ref_nom_input.text().strip()
        if ref_nom: filters['ref_nom'] = f"%{ref_nom}%" # Clé spéciale pour recherche multi-champs? Adapter repo
        cat = self.filter_categorie_input.text().strip()
        if cat: filters['categorie'] = f"%{cat}%" # LIKE
        statut = self.filter_statut_combo.currentText()
        if statut != "Tous": filters['statut'] = statut
        fours_id = self.filter_fours_combo.currentData()
        if fours_id is not None: filters['fournisseur_pref_id'] = fours_id
        return filters

    @Slot()
    def clear_filters(self):
        """ Réinitialise les filtres. """
        self.filter_ref_nom_input.clear(); self.filter_categorie_input.clear()
        self.filter_statut_combo.setCurrentIndex(0); self.filter_fours_combo.setCurrentIndex(0)
        self.refresh_pieces()

    # --- Slots CRUD ---
    @Slot()
    def add_piece(self):
        logger.debug("Ouv. dialogue ajout pièce.")
        dialog = PieceDialog(stock_service=self.stock_service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_piece_data()
            try:
                self.stock_service.create_piece(data)
                QMessageBox.information(self, self.tr("Succès"), f"Pièce '{data['nom']}' créée.")
                self.refresh_pieces()
            except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), f"{e}"); logger.error(f"{e}")

    @Slot()
    def edit_piece(self):
        p_id = self._get_selected_piece_id()
        if p_id is None: return
        try:
            p_edit = self.stock_service.get_piece_by_id(p_id)
            if not p_edit: QMessageBox.warning(self, self.tr("Erreur"), "Pièce n'existe plus."); self.refresh_pieces(); return

            dialog = PieceDialog(stock_service=self.stock_service, piece=p_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_piece_data()
                try:
                    updated = self.stock_service.update_piece(p_id, data)
                    QMessageBox.information(self, self.tr("Succès"), f"Pièce '{updated.nom}' mise à jour.")
                    self.refresh_pieces()
                except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), f"{e}"); logger.error(f"{e}"); self.refresh_pieces()
        except Exception as e: QMessageBox.critical(self,self.tr("Erreur"),f"{e}"); logger.exception(f"Err édit {p_id}")

    @Slot()
    def adjust_stock(self):
        """Ouvre le dialogue pour ajuster le stock de la pièce sélectionnée."""
        selected_id = self._get_selected_piece_id()
        if selected_id is None:
            QMessageBox.warning(self, self.tr("Aucune sélection"), "Veuillez sélectionner une pièce pour ajuster son stock.")
            return

        try:
            piece = self.stock_service.get_piece_by_id(selected_id)
            if not piece:
                # Ne devrait pas arriver si l'ID est valide, mais sécurité
                raise NotFoundError(f"Pièce avec ID {selected_id} non trouvée alors qu'elle était sélectionnée.")

            dialog = StockAdjustmentDialog(piece, self.stock_service, self)
            if dialog.exec() == QDialog.Accepted:
                logger.info(f"Ajustement de stock réussi pour pièce ID {selected_id}. Rafraîchissement.")
                self.refresh_pieces() # Recharge la liste pour voir le nouveau stock
            else:
                logger.info("Dialogue d'ajustement de stock annulé.")

        except NotFoundError as e:
            logger.error(f"Erreur adjust_stock: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), f"Impossible de trouver la pièce sélectionnée: {e}")
            self.refresh_pieces() # Rafraîchir au cas où la pièce ait été supprimée entre temps
        except (DatabaseError, BusinessLogicError) as e:
            logger.error(f"Erreur DB/métier dans adjust_stock: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), f"Une erreur est survenue: {e}")
        except Exception as e:
            logger.critical(f"Erreur inattendue dans adjust_stock: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), f"Une erreur inattendue est survenue: {e}")

    @Slot()
    def delete_piece(self):
        p_id = self._get_selected_piece_id()
        if p_id is None: return
        p = self.stock_service.get_piece_by_id(p_id)
        nom = p.nom if p else f"ID {p_id}"
        if QMessageBox.question(self,self.tr("Confirmer"),self.tr(f"Supprimer pièce '{nom}'?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                if self.stock_service.delete_piece(p_id):
                    QMessageBox.information(self, self.tr("Succès"), self.tr(f"Pièce '{nom}' supprimée."))
                    self.refresh_pieces()
            except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), self.tr(f"{e}")); logger.error(f"{e}"); self.refresh_pieces()