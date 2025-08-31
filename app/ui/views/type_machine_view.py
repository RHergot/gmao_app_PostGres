# gmao_app/app/ui/views/type_machine_view.py
"""
Widget pour afficher et gérer la liste des Types de Machine.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional

from app.core.models.type_machine import TypeMachine
from app.core.services.machine_service import MachineService # Réutilise MachineService
from app.ui.dialogs.type_machine_dialog import TypeMachineDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class TypeMachineView(QWidget):
    """Vue pour la gestion des Types de Machine."""

    def __init__(self, machine_service: MachineService, parent=None):
        super().__init__(parent)
        self.machine_service = machine_service
        self.current_types: List[TypeMachine] = []

        logger.debug("Initialisation de TypeMachineView...")

        # Widgets (similaire aux autres vues de référence)
        self.table_widget = QTableWidget(self)
        self.setup_table()
        self.add_button = QPushButton(self.tr("Ajouter Type"))
        self.edit_button = QPushButton(self.tr("Modifier Type"))
        self.delete_button = QPushButton(self.tr("Supprimer Type"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.table_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Connexions
        self.connect_signals()

        # Init
        self._update_button_states()
        self.refresh_types()
        logger.debug("TypeMachineView initialisée.")

    def setup_table(self):
        """Configure la table."""
        self.table_widget.setColumnCount(4) # ID, Catégorie, Nom, Description
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Catégorie"), self.tr("Nom"), self.tr("Description")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Catégorie
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Nom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Description

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 2 # Nom par défaut
        self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        """Connecte les signaux."""
        self.add_button.clicked.connect(self.add_type)
        self.edit_button.clicked.connect(self.edit_type)
        self.delete_button.clicked.connect(self.delete_type)
        self.refresh_button.clicked.connect(self.refresh_types)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_type)

    def _update_button_states(self):
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_type_id(self) -> Optional[int]:
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0)
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def refresh_data(self):
         self.refresh_types()

    @Slot()
    def refresh_types(self):
        """Recharge la liste des types."""
        logger.info("Rafraîchissement liste types machine...")
        try:
            self.current_types = self.machine_service.get_all_type_machines()
            # Tri côté client
            if self.current_types:
                 sort_key = self._get_sort_column_key()
                 reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
                 self.current_types.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)
            self.populate_table(self.current_types)
            logger.info(f"{len(self.current_types)} types machine affichés.")
        except BusinessLogicError as e:
             QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr(f"Impossible charger:\n{e}"))
             logger.error(f"Erreur métier chargement types machine: {e}")
        except Exception as e:
             QMessageBox.critical(self, "Erreur Inattendue", f"Erreur:\n{e}")
             logger.exception("Erreur inattendue chargement/affichage types machine.")

    def populate_table(self, types: List[TypeMachine]):
         """ Remplit la table. """
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(len(types))
         for row, tm in enumerate(types):
             id_item = QTableWidgetItem(str(tm.id_type_machine))
             id_item.setData(Qt.ItemDataRole.UserRole, tm.id_type_machine)
             self.table_widget.setItem(row, 0, id_item) # ID
             self.table_widget.setItem(row, 1, QTableWidgetItem(tm.categorie or "")) # Catégorie
             self.table_widget.setItem(row, 2, QTableWidgetItem(tm.nom or "")) # Nom
             self.table_widget.setItem(row, 3, QTableWidgetItem(tm.description or "")) # Desc
         self._update_button_states()
         self.table_widget.setSortingEnabled(True)
         self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)

    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Tri la table. """
        if self._sort_column == logical_index:
             self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
             self._sort_column = logical_index
             self._sort_order = Qt.SortOrder.AscendingOrder
        self.refresh_types()

    def _get_sort_column_key(self) -> str:
         """ Nom attribut pour tri. """
         column_map = { 1: "categorie", 2: "nom", 3: "description" }
         return column_map.get(self._sort_column, "nom")

    # --- Slots boutons Add/Edit/Delete (très similaires aux autres vues ref) ---
    @Slot()
    def add_type(self):
        logger.debug("Ouverture dialogue ajout type machine.")
        dialog = TypeMachineDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tm_data = dialog.get_type_machine_data()
            try:
                logger.info(f"Tentative création type via service: {tm_data.get('nom')}")
                self.machine_service.create_type_machine(tm_data)
                QMessageBox.information(self, self.tr("Succès"), self.tr(f"Type '{tm_data.get('nom')}' créé."))
                self.refresh_types()
            except (BusinessLogicError, DatabaseError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Création"), self.tr(f"Impossible de créer:\n{e}"))
                 logger.error(f"Échec création type: {e}")
            except Exception as e:
                 QMessageBox.critical(self, "Erreur Inattendue", f"Erreur:\n{e}")
                 logger.exception("Erreur inattendue création type.")

    @Slot()
    def edit_type(self):
        tm_id = self._get_selected_type_id()
        if tm_id is None: return
        try:
            tm_to_edit = self.machine_service.get_type_machine_by_id(tm_id)
            if not tm_to_edit:
                 QMessageBox.warning(self, self.tr("Erreur"), self.tr("Type n'existe plus."))
                 self.refresh_types(); return

            logger.debug(f"Ouverture dialogue édition type ID: {tm_id}")
            dialog = TypeMachineDialog(type_machine=tm_to_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_type_machine_data()
                try:
                    logger.info(f"Tentative màj type ID {tm_id} via service.")
                    updated = self.machine_service.update_type_machine(tm_id, update_data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr(f"Type '{updated.nom}' mis à jour."))
                    self.refresh_types()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Erreur Mise à Jour"), self.tr("Impossible màj:\n{e}").format(e=e))
                     logger.error(f"Échec màj type ID {tm_id}: {e}")
                     self.refresh_types()
                except Exception as e:
                     QMessageBox.critical(self, "Erreur Inattendue", f"Erreur:\n{e}")
                     logger.exception(f"Erreur inattendue màj type ID {tm_id}.")
        except (BusinessLogicError, NotFoundError) as e:
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible charger type:\n{e}").format(e=e))
             self.refresh_types()
        except Exception as e:
             QMessageBox.critical(self, "Erreur Inattendue", f"Erreur:\n{e}")
             logger.exception(f"Erreur inattendue avant dialogue édition type ID {tm_id}.")

    @Slot()
    def delete_type(self):
        tm_id = self._get_selected_type_id()
        if tm_id is None: return

        tm = self.machine_service.get_type_machine_by_id(tm_id)
        nom = tm.nom if tm else f"ID {tm_id}"

        reply = QMessageBox.question(
            self, self.tr("Confirmation Suppression"),
            self.tr("Supprimer le type '{nom}'?\n(Impossible si des machines/gammes y sont associées).").format(nom=nom),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative suppression type ID {tm_id} via service.")
                success = self.machine_service.delete_type_machine(tm_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Type '{nom}' supprimé.").format(nom=nom))
                    self.refresh_types()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Suppression"), self.tr("Impossible de supprimer:\n{e}").format(e=e))
                 logger.error(f"Échec suppression type ID {tm_id}: {e}")
                 self.refresh_types()
            except Exception as e:
                 QMessageBox.critical(self, "Erreur Inattendue", f"Erreur:\n{e}")
                 logger.exception(f"Erreur inattendue suppression type ID {tm_id}.")