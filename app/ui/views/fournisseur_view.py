# gmao_app/app/ui/views/fournisseur_view.py
"""
Widget pour afficher et gérer la liste des Fournisseurs.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QDialog, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional

# Importer modèle, service et dialogue
from app.core.models.fournisseur import Fournisseur
from app.core.services.stock_service import StockService # Service dédié
from app.ui.dialogs.fournisseur_dialog import FournisseurDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class FournisseurView(QWidget):
    """Vue pour la gestion des Fournisseurs."""

    def __init__(self, stock_service: StockService, parent=None):
        super().__init__(parent)
        self.stock_service = stock_service
        self.current_fournisseurs: List[Fournisseur] = []

        logger.debug("Initialisation de FournisseurView...")

        # Widgets (similaire aux vues de référence)
        self.table_widget = QTableWidget(self)
        self.setup_table()
        self.add_button = QPushButton(self.tr("Ajouter Fournisseur"))
        self.edit_button = QPushButton(self.tr("Modifier Fournisseur"))
        self.delete_button = QPushButton(self.tr("Supprimer Fournisseur"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button); button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button); button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.table_widget); main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Connexions & Init
        self.connect_signals()
        self._update_button_states()
        self.refresh_fournisseurs()
        logger.debug("FournisseurView initialisée.")

    def setup_table(self):
        """Configure la table."""
        # ID(0,hid), Nom(1), Contact(2), Tel(3), Email(4), Delai(5), Note(6)
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Email"), self.tr("Délai Livr. (j)"), self.tr("Note Qualité (/5)")
        ])
        # Configs standard
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1; self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_fournisseur)
        self.edit_button.clicked.connect(self.edit_fournisseur)
        self.delete_button.clicked.connect(self.delete_fournisseur)
        self.refresh_button.clicked.connect(self.refresh_fournisseurs)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_fournisseur)

    def _update_button_states(self):
        has_selection = self.table_widget.selectionModel().hasSelection()
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_fours_id(self) -> Optional[int]:
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0)
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def refresh_data(self): self.refresh_fournisseurs()

    @Slot()
    def refresh_fournisseurs(self):
        """ Recharge la liste. """
        logger.info("Rafraîchissement liste fournisseurs...")
        try:
            self.current_fournisseurs = self.stock_service.get_all_fournisseurs()
             # Tri client
            if self.current_fournisseurs:
                 sort_key = self._get_sort_column_key()
                 reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
                 # Gérer note / délai None lors du tri
                 self.current_fournisseurs.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)
            self.populate_table(self.current_fournisseurs)
            logger.info(f"{len(self.current_fournisseurs)} fournisseurs affichés.")
        except Exception as e: # Attrape tout pour affichage
             QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les fournisseurs :\n{err}").format(err=e))
             logger.exception("Erreur chargement/affichage fournisseurs.")


    def populate_table(self, fournisseurs: List[Fournisseur]):
         """ Remplit la table. """
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(0); self.table_widget.setRowCount(len(fournisseurs))
         for row, f in enumerate(fournisseurs):
             id_item = QTableWidgetItem(str(f.id_fournisseur)); id_item.setData(Qt.ItemDataRole.UserRole, f.id_fournisseur)
             delai_str = str(f.delai_livraison_moyen_j) if f.delai_livraison_moyen_j is not None else ""
             note_str = f"{f.note_qualite:.1f}" if f.note_qualite is not None else ""

             self.table_widget.setItem(row, 0, id_item) # ID
             self.table_widget.setItem(row, 1, QTableWidgetItem(f.nom or "")) # Nom
             self.table_widget.setItem(row, 2, QTableWidgetItem(f.contact or ""))
             self.table_widget.setItem(row, 3, QTableWidgetItem(f.telephone or ""))
             self.table_widget.setItem(row, 4, QTableWidgetItem(f.email or ""))
             self.table_widget.setItem(row, 5, QTableWidgetItem(delai_str))
             self.table_widget.setItem(row, 6, QTableWidgetItem(note_str))
             # Centrer délai et note?
             item_d = self.table_widget.item(row, 5); item_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
             item_n = self.table_widget.item(row, 6); item_n.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

         self._update_button_states()
         self.table_widget.setSortingEnabled(True)
         self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)


    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Tri la table. """
        if self._sort_column == logical_index: self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else: self._sort_column = logical_index; self._sort_order = Qt.SortOrder.AscendingOrder
        self.refresh_fournisseurs() # Tri client

    def _get_sort_column_key(self) -> str:
         """ Nom attribut pour tri. """
         column_map = { 1: "nom", 2: "contact", 3: "telephone", 4: "email", 5: "delai_livraison_moyen_j", 6: "note_qualite"}
         return column_map.get(self._sort_column, "nom")


    # --- Slots CRUD ---
    @Slot()
    def add_fournisseur(self):
        logger.debug("Ouv. dialogue ajout fournisseur.")
        dialog = FournisseurDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_fournisseur_data()
            try:
                self.stock_service.create_fournisseur(data)
                QMessageBox.information(self, self.tr("Succès"), self.tr("Fournisseur '{nom}' créé.").format(nom=data.get('nom')))
                self.refresh_fournisseurs()
            except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), self.tr("{e}").format(e=e)); logger.error(f"{e}")

    @Slot()
    def edit_fournisseur(self):
        f_id = self._get_selected_fours_id();
        if f_id is None: return
        try:
            f_edit = self.stock_service.get_fournisseur_by_id(f_id)
            if not f_edit: QMessageBox.warning(self, self.tr("Erreur"), self.tr("Fourn. n'existe plus.")); self.refresh_fournisseurs(); return

            dialog = FournisseurDialog(fournisseur=f_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_fournisseur_data()
                try:
                    updated = self.stock_service.update_fournisseur(f_id, data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Fournisseur '{nom}' mis à jour.").format(nom=updated.nom))
                    self.refresh_fournisseurs()
                except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), self.tr("{e}").format(e=e)); logger.error(f"{e}"); self.refresh_fournisseurs()
        except Exception as e: QMessageBox.critical(self, self.tr("Erreur"), self.tr("{e}").format(e=e)); logger.exception(f"Err édit {f_id}")

    @Slot()
    def delete_fournisseur(self):
        f_id = self._get_selected_fours_id();
        if f_id is None: return
        f = self.stock_service.get_fournisseur_by_id(f_id)
        nom = f.nom if f else f"ID {f_id}"

        if QMessageBox.question(self, self.tr("Confirmer"), self.tr("Supprimer fournisseur '{nom}'?").format(nom=nom)) == QMessageBox.StandardButton.Yes:
            try:
                if self.stock_service.delete_fournisseur(f_id):
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Fournisseur '{nom}' supprimé.").format(nom=nom))
                    self.refresh_fournisseurs()
            except Exception as e: QMessageBox.warning(self, self.tr("Erreur"), self.tr("{e}").format(e=e)); logger.error(f"{e}"); self.refresh_fournisseurs()