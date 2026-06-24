# gmao_app/app/ui/dialogs/piece_selection_dialog.py
"""
Dialogue pour sélectionner une pièce détachée et saisir la quantité/lot.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QTableView,
    QDialogButtonBox, QMessageBox, QPushButton, QFormLayout, QWidget
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Slot
from typing import Optional, Dict, Any, List, Tuple

from app.core.models.piece import Piece
from app.core.services.stock_service import StockService # Reçoit le service stock

logger = logging.getLogger(__name__)

class PieceSelectionDialog(QDialog):
    """Dialogue modal pour sélectionner une pièce et définir quantité/lot."""

    def __init__(self, stock_service: StockService, parent=None):
        super().__init__(parent)
        self.stock_service = stock_service
        self.model = None
        self.selected_piece_info: Optional[Tuple[int, str, str]] = None # (id, reference, nom)
        self.available_pieces: List[Piece] = []
        self.selected_piece_data: Optional[Dict[str, Any]] = None

        self.setWindowTitle(self.tr("Sélectionner Pièce Utilisée"))
        self.setMinimumWidth(650)
        self.setMinimumHeight(450)

        # UI construit directement dans __init__, pas besoin de _setup_ui/_load_initial_pieces

        # --- Widgets ---
        self.search_input = QLineEdit(placeholderText=self.tr("Rechercher par Réf ou Nom..."))
        self.table_widget = QTableWidget()
        self.setup_table()

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 9999) # Minimum 1
        self.quantity_spinbox.setValue(1)

        self.lot_input = QLineEdit(placeholderText=self.tr("Optionnel"))

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        # Activer OK seulement si une pièce est sélectionnée et quantité > 0
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        # --- Layout ---
        main_layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Rechercher:"))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        main_layout.addWidget(QLabel("Pièces Disponibles:"))
        main_layout.addWidget(self.table_widget)

        selection_layout = QFormLayout()
        selection_layout.addRow("Quantité (*):", self.quantity_spinbox)
        selection_layout.addRow("Lot / N° Série:", self.lot_input)
        main_layout.addLayout(selection_layout)

        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # --- Connexions & Chargement initial ---
        self.connect_signals()
        self.refresh_available_pieces() # Charger les pièces au démarrage

    def setup_table(self):
        """ Configure la table des pièces disponibles. """
        # ID(0,hid), Ref(1), Nom(2), Unite(3), Stock Actuel(4), Emplacement(5), Categorie(6)
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels([
            "ID", "Référence", "Nom / Description", "Unité", "Stock", "Emplacement", "Catégorie"
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Une seule pièce à la fois
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True) # Permettre tri
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Ref
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Unite
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Stock
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive) # Emplacement
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive) # Catégorie

        # Initialiser tri par nom
        self._sort_column = 2
        self._sort_order = Qt.SortOrder.AscendingOrder
        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)

    def connect_signals(self):
        """ Connecte les signaux. """
        self.search_input.textChanged.connect(self.filter_pieces) # Filtrer en direct
        self.table_widget.itemSelectionChanged.connect(self._update_ok_button_state)
        # Double-clic sur une ligne sélectionne la pièce et ferme OK ?
        self.table_widget.doubleClicked.connect(self.accept_selection)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _update_ok_button_state(self):
        """ Active le bouton OK si une pièce est sélectionnée. """
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(has_selection)

    def _get_selected_piece_info(self) -> Optional[Piece]:
         """ Retourne l'objet Piece correspondant à la ligne sélectionnée. """
         selected_rows = self.table_widget.selectionModel().selectedRows()
         if not selected_rows: return None
         id_item = self.table_widget.item(selected_rows[0].row(), 0) # Colonne ID
         if id_item:
             piece_id = id_item.data(Qt.ItemDataRole.UserRole)
             if piece_id is not None:
                  # Retrouver l'objet pièce dans notre liste chargée
                  # C'est plus sûr que de rappeler le service ici
                  found_piece = next((p for p in self.available_pieces if p.id_piece == piece_id), None)
                  return found_piece
         return None


    @Slot()
    def refresh_available_pieces(self):
        """ Recharge la liste complète des pièces depuis le service. """
        logger.debug("Chargement/Rafraîchissement liste pièces disponibles...")
        try:
            # Peut-être filtrer pour ne prendre que les 'Actif'? Non, pour sélection, tout afficher.
            # Le filtre dans la vue principale PiecView est plus pertinent pour ça.
            self.available_pieces = self.stock_service.get_all_pieces(sort_by="nom") # Tri initial
            self.filter_pieces() # Appliquer le filtre de recherche actuel
            logger.info(f"{len(self.available_pieces)} pièces totales chargées pour sélection.")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), f"Impossible de charger la liste des pièces:\n{e}")
            logger.exception("Erreur chargement pièces pour PieceSelectionDialog.")


    @Slot()
    def filter_pieces(self):
        """ Filtre et affiche les pièces dans la table selon la recherche. """
        search_term = self.search_input.text().strip().lower()
        filtered_list: List[Piece] = []

        if not search_term:
            filtered_list = self.available_pieces # Afficher tout si recherche vide
        else:
            # Recherche simple sur référence ou nom (insensible à la casse)
            for piece in self.available_pieces:
                ref_match = piece.reference and search_term in piece.reference.lower()
                nom_match = piece.nom and search_term in piece.nom.lower()
                if ref_match or nom_match:
                    filtered_list.append(piece)

        # Appliquer le tri actuel sur la liste filtrée
        if filtered_list:
             sort_key = self._get_sort_column_key()
             reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
             try: # Gérer attributs None
                 filtered_list.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)
             except AttributeError:
                  logger.warning(f"Attribut de tri '{sort_key}' non trouvé, tri par défaut.")
                  filtered_list.sort(key=lambda x: x.nom) # Tri par nom si erreur

        self.populate_table(filtered_list)


    def populate_table(self, pieces: List[Piece]):
        """ Remplit la table avec les pièces filtrées/triées. """
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0); self.table_widget.setRowCount(len(pieces))
        for row, p in enumerate(pieces):
            id_item = QTableWidgetItem(str(p.id_piece))
            id_item.setData(Qt.ItemDataRole.UserRole, p.id_piece)
            stock_str = str(p.stock_actuel or 0)

            item_id = id_item
            item_ref = QTableWidgetItem(p.reference or "")
            item_nom = QTableWidgetItem(p.nom or "")
            item_unit = QTableWidgetItem(p.unite or "")
            item_stock = QTableWidgetItem(stock_str); item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_emplace = QTableWidgetItem(p.emplacement_stockage or "")
            item_cat = QTableWidgetItem(p.categorie or "")

            self.table_widget.setItem(row, 0, item_id)
            self.table_widget.setItem(row, 1, item_ref)
            self.table_widget.setItem(row, 2, item_nom)
            self.table_widget.setItem(row, 3, item_unit)
            self.table_widget.setItem(row, 4, item_stock)
            self.table_widget.setItem(row, 5, item_emplace)
            self.table_widget.setItem(row, 6, item_cat)

            # Optionnel : Griser les lignes dont le stock est <= 0 ?
            if p.stock_actuel <= 0:
                 for col in range(1, self.table_widget.columnCount()):
                     item = self.table_widget.item(row, col)
                     if item: item.setForeground(Qt.GlobalColor.gray)

        self.table_widget.setSortingEnabled(True)
        self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)
        self._update_ok_button_state() # Mettre à jour bouton OK après remplissage


    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Tri la table (sur les données actuellement filtrées). """
        if self._sort_column == logical_index: self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else: self._sort_column = logical_index; self._sort_order = Qt.SortOrder.AscendingOrder
        # Rappeler filter_pieces pour retrier la liste filtrée et repeupler
        self.filter_pieces()

    def _get_sort_column_key(self) -> str:
        """ Nom attribut pour tri. """
        column_map = { 1: "reference", 2: "nom", 3: "unite", 4: "stock_actuel", 5: "emplacement_stockage", 6: "categorie"}
        return column_map.get(self._sort_column, "nom")


    @Slot()
    def accept_selection(self):
        """ Accepte la sélection si OK (double-clic). """
        if self.button_box.button(QDialogButtonBox.StandardButton.Ok).isEnabled():
             self.accept()

    @Slot()
    def accept(self):
        """ Valide la sélection et stocke les données avant de fermer. """
        selected_piece = self._get_selected_piece_info()
        if not selected_piece:
            QMessageBox.warning(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner une pièce dans la liste."))
            return

        quantity = self.quantity_spinbox.value()
        if quantity <= 0:
            QMessageBox.warning(self, self.tr("Quantité Invalide"), self.tr("La quantité doit être supérieure à zéro."))
            return

        # Vérifier stock suffisant? Optionnel ici, le service le fera lors de la consommation.
        # Mais un avertissement peut être utile.
        if selected_piece.stock_actuel < quantity:
             reply = QMessageBox.warning(self, "Stock Insuffisant",
                                        f"Le stock actuel ({selected_piece.stock_actuel}) pour '{selected_piece.nom}' "
                                        f"est inférieur à la quantité demandée ({quantity}).\n\n"
                                        "Continuer quand même (le stock deviendra négatif) ?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                        QMessageBox.StandardButton.Cancel)
             if reply == QMessageBox.StandardButton.Cancel:
                 return

        # Stocker les données sélectionnées pour récupération par l'appelant
        self.selected_piece_data = {
            'piece_id': selected_piece.id_piece,
            'piece_ref': selected_piece.reference,
            'piece_nom': selected_piece.nom,
            'quantite': quantity,
            'lot': self.lot_input.text().strip() or None
        }
        logger.info(f"Pièce sélectionnée: {self.selected_piece_data}")
        super().accept() # Fermer le dialogue avec statut Accepté

    def get_selected_piece(self) -> Optional[Dict[str, Any]]:
        """ Retourne les informations de la pièce sélectionnée (ID, Ref, Nom, Qt, Lot). """
        return self.selected_piece_data
