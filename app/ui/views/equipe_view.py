# gmao_app/app/ui/views/equipe_view.py
"""
Widget pour afficher et gérer la liste des Equipes.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QDialog, QLabel
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional

# Importer modèle, service et dialogue
from app.core.models.equipe import Equipe
from app.core.models.technicien import Technicien # Besoin pour afficher nom responsable
from app.core.services.maintenance_service import MaintenanceService
from app.ui.dialogs.equipe_dialog import EquipeDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class EquipeView(QWidget):
    """Vue pour la gestion des Equipes."""

    def __init__(self, maintenance_service: MaintenanceService, parent=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.current_equipes: List[Equipe] = []
        self.techniciens_map: Dict[int, str] = {} # Cache pour noms techniciens

        logger.debug("Initialisation de EquipeView...")

        # Widgets
        self.table_widget = QTableWidget(self)
        self.setup_table()
        self.add_button = QPushButton("➕ " + self.tr("Ajouter Équipe"))
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
        self.refresh_equipes()
        logger.debug("EquipeView initialisée.")
        print(self.tr("Ajouter Équipe"))

    def setup_table(self):
        """Configure la table des equipes."""
        self.table_widget.setColumnCount(4) # ID, Nom, Domaine, Responsable
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom Équipe"), self.tr("Domaine Expertise"), self.tr("Responsable")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Domaine
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Responsable

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1 # Nom par défaut
        self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_equipe)
        self.edit_button.clicked.connect(self.edit_equipe)
        self.delete_button.clicked.connect(self.delete_equipe)
        self.refresh_button.clicked.connect(self.refresh_equipes)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_equipe)

    def _update_button_states(self):
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_equipe_id(self) -> Optional[int]:
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0) # Colonne ID
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def _load_techniciens_map(self):
        """ Charge un mapping ID -> Nom complet pour l'affichage du responsable. """
        try:
            techniciens = self.maintenance_service.get_all_techniciens(include_inactive=True) # Inclure inactifs au cas où
            self.techniciens_map = {tech.id_technicien: tech.nom_complet for tech in techniciens}
        except BusinessLogicError as e:
             logger.error(f"Erreur chargement map techniciens: {e}")
             self.techniciens_map = {} # Reset en cas d'erreur

    def refresh_data(self):
         self.refresh_equipes()

    @Slot()
    def refresh_equipes(self):
        """Recharge et affiche la liste des equipes."""
        logger.info("Rafraîchissement de la liste des equipes...")
        self._load_techniciens_map() # Recharger les noms des techniciens
        try:
            self.current_equipes = self.maintenance_service.get_all_equipes()
            # Tri client
            if self.current_equipes:
                 sort_key = self._get_sort_column_key()
                 reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
                 # Gérer tri sur responsable_id en triant sur le nom correspondant
                 if sort_key == 'responsable_id':
                     self.current_equipes.sort(key=lambda x: self.techniciens_map.get(x.responsable_id, "") , reverse=reverse)
                 else:
                     self.current_equipes.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)

            self.populate_table(self.current_equipes)
            logger.info(f"{len(self.current_equipes)} equipes affichées.")
            if not self.current_equipes:
                self.info_label.setText(self.tr("Aucune équipe à afficher."))
        except BusinessLogicError as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr(f"Impossible charger equipes:\n{e}"))
            logger.error(f"Erreur métier chargement equipes: {e}")
            self.info_label.setText(self.tr("Erreur chargement."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Erreur:\n{e}"))
            logger.exception("Erreur inattendue chargement/affichage equipes.")
            self.info_label.setText(self.tr("Erreur chargement."))

    def populate_table(self, equipes: List[Equipe]):
         """ Remplit la table. """
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(len(equipes))

         for row, eq in enumerate(equipes):
             id_item = QTableWidgetItem(str(eq.id_equipe))
             id_item.setData(Qt.ItemDataRole.UserRole, eq.id_equipe)
             self.table_widget.setItem(row, 0, id_item) # ID
             self.table_widget.setItem(row, 1, QTableWidgetItem(eq.nom or "")) # Nom
             self.table_widget.setItem(row, 2, QTableWidgetItem(eq.domaine_expertise or ""))
             # Afficher nom du responsable depuis la map
             resp_nom = self.techniciens_map.get(eq.responsable_id, "N/A") if eq.responsable_id else ""
             self.table_widget.setItem(row, 3, QTableWidgetItem(resp_nom))

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
        self.refresh_equipes() # Applique tri client

    def _get_sort_column_key(self) -> str:
         """ Nom attribut pour tri. """
         column_map = { 1: "nom", 2: "domaine_expertise", 3: "responsable_id" }
         return column_map.get(self._sort_column, "nom")

    # --- Slots boutons Add/Edit/Delete ---
    @Slot()
    def add_equipe(self):
        logger.debug("Ouverture dialogue ajout equipe.")
        # Le dialogue a besoin du service pour la liste des responsables
        dialog = EquipeDialog(maintenance_service=self.maintenance_service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            eq_data = dialog.get_equipe_data()
            try:
                logger.info(f"Tentative création equipe via service: {eq_data.get('nom')}")
                # Utiliser la méthode du service dédiée (supposée exister)
                # Si les méthodes CRUD sont dans MaintenanceService :
                self.maintenance_service.create_equipe(eq_data) # <-- A AJOUTER DANS MaintenanceService
                QMessageBox.information(self, self.tr("Succès"), self.tr("Équipe '%1' créée.").replace('%1', eq_data.get('nom')))
                self.refresh_equipes()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e: # Ajouter NotFoundError si applicable
                 QMessageBox.warning(self, self.tr("Erreur Création"), self.tr("Impossible de créer:\n%1").replace('%1', str(e)))
                 logger.error(f"Échec création equipe: {e}")
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Erreur:\n{e}"))
                 logger.exception("Erreur inattendue création equipe.")

    @Slot()
    def edit_equipe(self):
        eq_id = self._get_selected_equipe_id()
        if eq_id is None: return
        try:
            # Utiliser get_equipe_by_id (à ajouter dans service)
            eq_to_edit = self.maintenance_service.get_equipe_by_id(eq_id) # <-- A AJOUTER DANS MaintenanceService
            if not eq_to_edit:
                 QMessageBox.warning(self, self.tr("Erreur"), self.tr("Équipe n'existe plus.")); self.refresh_equipes(); return

            logger.debug(f"Ouverture dialogue édition equipe ID: {eq_id}")
            dialog = EquipeDialog(maintenance_service=self.maintenance_service, equipe=eq_to_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_equipe_data()
                try:
                    logger.info(f"Tentative màj equipe ID {eq_id} via service.")
                    updated = self.maintenance_service.update_equipe(eq_id, update_data) # <-- A AJOUTER DANS MaintenanceService
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Équipe '%1' mise à jour.").replace('%1', updated.nom))
                    self.refresh_equipes()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Erreur Mise à Jour"), self.tr("Impossible màj:\n%1").replace('%1', str(e)))
                     logger.error(f"Échec màj equipe ID {eq_id}: {e}"); self.refresh_equipes()
                except Exception as e:
                     QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Erreur:\n{e}")); logger.exception(f"Erreur màj equipe ID {eq_id}.")
        except (BusinessLogicError, NotFoundError) as e:
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible charger equipe:\n%1").replace('%1', str(e))); self.refresh_equipes()
        except Exception as e:
             QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les équipes:\n{}".format(e))); logger.exception(f"Erreur avant dialogue édition equipe ID {eq_id}.")

    @Slot()
    def delete_equipe(self):
        eq_id = self._get_selected_equipe_id()
        if eq_id is None: return

        eq = self.maintenance_service.get_equipe_by_id(eq_id)
        nom = eq.nom if eq else f"ID {eq_id}"

        reply = QMessageBox.question(self, self.tr("Confirmation Suppression"), self.tr("Supprimer l'équipe '%1'?").replace('%1', nom),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative suppression equipe ID {eq_id} via service.")
                success = self.maintenance_service.delete_equipe(eq_id) # <-- A AJOUTER DANS MaintenanceService
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Équipe '%1' supprimée.").replace('%1', nom))
                    self.refresh_equipes()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Suppression"), self.tr("Impossible supprimer:\n%1").replace('%1', str(e)))
                 logger.error(f"Échec suppression equipe ID {eq_id}: {e}"); self.refresh_equipes()
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Erreur:\n{e}")); logger.exception(f"Erreur suppression equipe ID {eq_id}.")