# gmao_app/app/ui/views/fabricant_view.py
"""
Widget pour afficher et gérer la liste des Fabricants.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QDialog, QLabel
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional

from app.core.models.fabricant import Fabricant
from app.core.services.machine_service import MachineService # Réutilise MachineService
from app.ui.dialogs.fabricant_dialog import FabricantDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.ui.main_window import MainWindow
from app.core.models.utilisateur import Utilisateur # Pour les permissions (via main_window)

logger = logging.getLogger(__name__)

class FabricantView(QWidget):
    """Vue pour la gestion des Fabricants."""

    def __init__(self, machine_service: MachineService, main_window: "MainWindow"):
        super().__init__(main_window)
        self.machine_service = machine_service
        self.main_window = main_window
        self.current_fabricants: List[Fabricant] = []

        logger.debug("Initialisation de FabricantView...")

        # Widgets (similaire à SiteView)
        self.table_widget = QTableWidget(self)
        self.setup_table()
        self.add_button = QPushButton("➕ " + self.tr("Ajouter Fabricant"))
        self.edit_button = QPushButton("✏️ " + self.tr("Modifier"))
        self.delete_button = QPushButton("🗑️ " + self.tr("Supprimer"))
        self.refresh_button = QPushButton("🔄 " + self.tr("Rafraîchir"))
        self.info_label = QLabel(self.tr("Chargement..."))

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
        main_layout.addWidget(self.info_label)
        self.setLayout(main_layout)

        # Connexions
        self.connect_signals()

        # Init
        self._update_button_states()
        self.refresh_fabricants()
        logger.debug("FabricantView initialisée.")

    def setup_table(self):
        """Configure la table."""
        self.table_widget.setColumnCount(5) # ID, Nom, Contact, Site Web, Support
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom"), self.tr("Contact"), self.tr("Site Web"), self.tr("Support Technique")
        ])
        # Mêmes configurations que SiteView pour EditTriggers, Selection, Headers...
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
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Support

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1 # Nom par défaut
        self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        """Connecte les signaux."""
        self.add_button.clicked.connect(self.add_fabricant)
        self.edit_button.clicked.connect(self.edit_fabricant)
        self.delete_button.clicked.connect(self.delete_fabricant)
        self.refresh_button.clicked.connect(self.refresh_fabricants)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_fabricant)

    def _update_button_states(self):
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_fabricant_id(self) -> Optional[int]:
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0)
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def refresh_data(self):
         self.refresh_fabricants()

    @Slot()
    def refresh_fabricants(self):
        """Recharge la liste des fabricants."""
        logger.info("Rafraîchissement liste fabricants...")
        try:
            self.current_fabricants = self.machine_service.get_all_fabricants()
            # Tri côté client
            if self.current_fabricants:
                 sort_key = self._get_sort_column_key()
                 reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
                 self.current_fabricants.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)
            self.populate_table(self.current_fabricants)
            logger.info(f"{len(self.current_fabricants)} fabricants affichés.")
            if not self.current_fabricants:
                self.info_label.setText(self.tr("Aucun fabricant à afficher."))
        except BusinessLogicError as e:
             QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible charger:\n{0}").format(e))
             logger.error(f"Erreur métier chargement fabricants: {e}")
             self.info_label.setText(self.tr("Erreur chargement."))
        except Exception as e:
             QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n{0}").format(e))
             logger.exception("Erreur inattendue chargement/affichage fabricants.")

    def populate_table(self, fabricants: List[Fabricant]):
         """ Remplit la table. """
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(len(fabricants))
         for row, fab in enumerate(fabricants):
             id_item = QTableWidgetItem(str(fab.id_fabricant))
             id_item.setData(Qt.ItemDataRole.UserRole, fab.id_fabricant)
             self.table_widget.setItem(row, 0, id_item) # ID
             self.table_widget.setItem(row, 1, QTableWidgetItem(fab.nom or "")) # Nom
             self.table_widget.setItem(row, 2, QTableWidgetItem(fab.contact or ""))
             self.table_widget.setItem(row, 3, QTableWidgetItem(fab.site_web or ""))
             self.table_widget.setItem(row, 4, QTableWidgetItem(fab.support_technique or ""))
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
        self.refresh_fabricants()

    def _get_sort_column_key(self) -> str:
         """ Nom de l'attribut pour tri. """
         column_map = { 1: "nom", 2: "contact", 3: "site_web", 4: "support_technique" }
         return column_map.get(self._sort_column, "nom")

    # --- Slots pour boutons Add/Edit/Delete (très similaires à SiteView) ---
    @Slot()
    def add_fabricant(self):
        logger.debug("Ouverture dialogue ajout fabricant.")
        dialog = FabricantDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fab_data = dialog.get_fabricant_data()
            try:
                logger.info(f"Tentative création fabricant via service: {fab_data.get('nom')}")
                self.machine_service.create_fabricant(fab_data)
                QMessageBox.information(self, self.tr("Succès"), self.tr("Fabricant '{0}' créé.").format(fab_data.get('nom')))
                self.refresh_fabricants()
            except (BusinessLogicError, DatabaseError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Création"), self.tr("Impossible de créer:\n{0}").format(e))
                 logger.error(f"Échec création fabricant: {e}")
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n{0}").format(e))
                 logger.exception("Erreur inattendue création fabricant.")

    @Slot()
    def edit_fabricant(self):
        fab_id = self._get_selected_fabricant_id()
        if fab_id is None: return
        try:
            fab_to_edit = self.machine_service.get_fabricant_by_id(fab_id)
            if not fab_to_edit:
                 QMessageBox.warning(self, self.tr("Erreur"), self.tr("Fabricant n'existe plus."))
                 self.refresh_fabricants(); return

            logger.debug(f"Ouverture dialogue édition fabricant ID: {fab_id}")
            dialog = FabricantDialog(fabricant=fab_to_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_fabricant_data()
                try:
                    logger.info(f"Tentative màj fabricant ID {fab_id} via service.")
                    updated = self.machine_service.update_fabricant(fab_id, update_data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Fabricant '{0}' mis à jour.").format(updated.nom))
                    self.refresh_fabricants()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Erreur Mise à Jour"), self.tr("Impossible de mettre à jour:\n{0}").format(e))
                     logger.error(f"Échec màj fabricant ID {fab_id}: {e}")
                     self.refresh_fabricants()
                except Exception as e:
                     QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n{0}").format(e))
                     logger.exception(f"Erreur inattendue màj fabricant ID {fab_id}.")
        except (BusinessLogicError, NotFoundError) as e:
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger les fabricants:\n{0}").format(e))
             self.info_label.setText(self.tr("Erreur chargement."))
             self.refresh_fabricants()
        except Exception as e:
             QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n{0}").format(e))
             logger.exception(f"Erreur inattendue avant dialogue édition fabricant ID {fab_id}.")

    @Slot()
    def delete_fabricant(self):
        fab_id = self._get_selected_fabricant_id()
        if fab_id is None: return

        fab = self.machine_service.get_fabricant_by_id(fab_id)
        nom = fab.nom if fab else f"ID {fab_id}"

        reply = QMessageBox.question(
            self, self.tr("Confirmation Suppression"),
            self.tr("Supprimer le fabricant '{0}'?\n(Impossible si des machines y sont associées).").format(nom),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative suppression fabricant ID {fab_id} via service.")
                success = self.machine_service.delete_fabricant(fab_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Fabricant '{0}' supprimé.").format(nom))
                    self.refresh_fabricants()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Suppression"), self.tr("Impossible de supprimer:\n{0}").format(e))
                 logger.error(f"Échec suppression fabricant ID {fab_id}: {e}")
                 self.refresh_fabricants()
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Erreur:\n{0}").format(e))
                 logger.exception(f"Erreur inattendue suppression fabricant ID {fab_id}.")
