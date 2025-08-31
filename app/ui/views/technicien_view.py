# gmao_app/app/ui/views/technicien_view.py
"""
Widget pour afficher et gérer la liste des Techniciens.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QCheckBox, QDialog # Ajout QCheckBox pour filtre actif
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional, Dict

from app.core.models.technicien import Technicien
from app.core.models.equipe import Equipe # Besoin pour afficher nom équipe
from app.core.services.maintenance_service import MaintenanceService
from app.ui.dialogs.technicien_dialog import TechnicienDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class TechnicienView(QWidget):
    """Vue pour la gestion des Techniciens."""

    def __init__(self, maintenance_service: MaintenanceService, parent=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.current_techniciens: List[Technicien] = []
        self.equipes_map: Dict[int, str] = {} # Cache pour noms équipes

        logger.debug("Initialisation de TechnicienView...")

        # Widgets
        self.table_widget = QTableWidget(self)
        self.setup_table()
        self.add_button = QPushButton(self.tr("Add Technician"))
        self.edit_button = QPushButton(self.tr("Edit Technician"))
        self.delete_button = QPushButton(self.tr("Delete Technician"))
        self.refresh_button = QPushButton(self.tr("Refresh"))
        self.show_inactive_checkbox = QCheckBox(self.tr("Show Inactive"))

        # Layouts
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.show_inactive_checkbox)
        filter_layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.table_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Connexions
        self.connect_signals()

        # Init
        self._update_button_states()
        self.refresh_techniciens()
        logger.debug("TechnicienView initialisée.")

    def setup_table(self):
        """Configure la table."""
        self.table_widget.setColumnCount(7) # ID, Nom, Prénom, Qualification, Equipe, Coût/h, Actif
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Last Name"), self.tr("First Name"), self.tr("Qualification"), self.tr("Team"), self.tr("Hourly Rate"), self.tr("Active")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Prénom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Qualification
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Equipe
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Coût
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Actif

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1 # Nom par défaut
        self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_technicien)
        self.edit_button.clicked.connect(self.edit_technicien)
        self.delete_button.clicked.connect(self.delete_technicien)
        self.refresh_button.clicked.connect(self.refresh_techniciens)
        self.show_inactive_checkbox.stateChanged.connect(self.refresh_techniciens) # Rafraîchit si case cochée/décochée
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_technicien)

    def _update_button_states(self):
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_technicien_id(self) -> Optional[int]:
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0)
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def _load_equipes_map(self):
         try:
             equipes = self.maintenance_service.get_all_equipes()
             self.equipes_map = {eq.id_equipe: eq.nom for eq in equipes}
         except BusinessLogicError as e:
             logger.error(f"Erreur chargement map equipes: {e}")
             self.equipes_map = {}

    def refresh_data(self):
         self.refresh_techniciens()

    @Slot()
    def refresh_techniciens(self):
        """Recharge la liste des techniciens."""
        logger.info("Rafraîchissement liste techniciens...")
        self._load_equipes_map()
        include_inactive = self.show_inactive_checkbox.isChecked()
        try:
            self.current_techniciens = self.maintenance_service.get_all_techniciens(include_inactive=include_inactive)
            # Tri client
            if self.current_techniciens:
                 sort_key = self._get_sort_column_key()
                 reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
                 if sort_key == 'equipe_id':
                      self.current_techniciens.sort(key=lambda x: self.equipes_map.get(x.equipe_id, ""), reverse=reverse)
                 elif sort_key == 'nom_complet': # Tri spécial sur nom + prénom
                     self.current_techniciens.sort(key=lambda x: x.nom_complet, reverse=reverse)
                 else:
                      self.current_techniciens.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)

            self.populate_table(self.current_techniciens)
            logger.info(f"{len(self.current_techniciens)} techniciens affichés.")
        except BusinessLogicError as e:
             QMessageBox.critical(self, self.tr("Load Error"), self.tr(f"Unable to load:\n{e}"))
             logger.error(f"Erreur métier chargement techniciens: {e}")
        except Exception as e:
             QMessageBox.critical(self, self.tr("Unexpected Error"), self.tr(f"Error:\n{e}"))
             logger.exception("Erreur inattendue chargement/affichage techniciens.")

    def populate_table(self, techniciens: List[Technicien]):
         """ Remplit la table. """
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(len(techniciens))
         for row, tech in enumerate(techniciens):
             id_item = QTableWidgetItem(str(tech.id_technicien))
             id_item.setData(Qt.ItemDataRole.UserRole, tech.id_technicien)
             # Format coût horaire
             cost_str = f"{tech.cout_horaire:.2f} €" if tech.cout_horaire is not None else ""

             self.table_widget.setItem(row, 0, id_item) # ID
             self.table_widget.setItem(row, 1, QTableWidgetItem(tech.nom or "")) # Nom
             self.table_widget.setItem(row, 2, QTableWidgetItem(tech.prenom or "")) # Prénom
             self.table_widget.setItem(row, 3, QTableWidgetItem(tech.qualification or ""))
             # Afficher nom équipe
             eq_nom = self.equipes_map.get(tech.equipe_id, self.tr("N/A")) if tech.equipe_id else ""
             self.table_widget.setItem(row, 4, QTableWidgetItem(eq_nom))
             self.table_widget.setItem(row, 5, QTableWidgetItem(cost_str))
             self.table_widget.setItem(row, 6, QTableWidgetItem(self.tr("Yes") if tech.actif else self.tr("No")))
         self._update_button_states()
         self.table_widget.setSortingEnabled(True)
         self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)

    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Tri la table. """
        if logical_index == 1 or logical_index == 2 : # Nom ou Prénom
             # Si on trie sur nom ou prénom, utiliser la clé spéciale 'nom_complet'
             sort_col_key_temp = 'nom_complet'
             if self._sort_column != 1 and self._sort_column != 2 : # Si on vient d'une autre colonne
                 self._sort_order = Qt.SortOrder.AscendingOrder
                 self._sort_column = logical_index # Stocker l'index cliqué visuellement
             else: # On re-clique sur nom ou prénom
                 self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
                 self._sort_column = logical_index
        else: # Tri normal pour les autres colonnes
            if self._sort_column == logical_index:
                 self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
            else:
                 self._sort_column = logical_index
                 self._sort_order = Qt.SortOrder.AscendingOrder
        self.refresh_techniciens()

    def _get_sort_column_key(self) -> str:
         """ Nom attribut pour tri. """
         if self._sort_column == 1 or self._sort_column == 2: return "nom_complet"
         column_map = { 3: "qualification", 4: "equipe_id", 5: "cout_horaire", 6: "actif" }
         return column_map.get(self._sort_column, "nom")


    # --- Slots boutons Add/Edit/Delete ---
    @Slot()
    def add_technicien(self):
        logger.debug("Ouverture dialogue ajout technicien.")
        # Le dialogue a besoin du service pour la liste des équipes
        dialog = TechnicienDialog(maintenance_service=self.maintenance_service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tech_data = dialog.get_technicien_data()
            try:
                logger.info(f"Tentative création technicien via service: {tech_data.get('nom')}")
                # Utiliser la méthode du service
                self.maintenance_service.create_technicien(tech_data)
                QMessageBox.information(self, self.tr("Success"), self.tr(f"Technician '{tech_data.get('nom')}' created."))
                self.refresh_techniciens()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Creation Error"), self.tr(f"Unable to create:\n{e}"))
                 logger.error(f"Échec création technicien: {e}")
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Unexpected Error"), self.tr(f"Error:\n{e}"))
                 logger.exception("Erreur inattendue création technicien.")

    @Slot()
    def edit_technicien(self):
        tech_id = self._get_selected_technicien_id()
        if tech_id is None: return
        try:
            tech_to_edit = self.maintenance_service.get_technicien_by_id(tech_id)
            if not tech_to_edit:
                 QMessageBox.warning(self, self.tr("Error"), self.tr("Technician no longer exists.")); self.refresh_techniciens(); return

            logger.debug(f"Ouverture dialogue édition technicien ID: {tech_id}")
            dialog = TechnicienDialog(maintenance_service=self.maintenance_service, technicien=tech_to_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_technicien_data()
                try:
                    logger.info(f"Tentative màj technicien ID {tech_id} via service.")
                    updated = self.maintenance_service.update_technicien(tech_id, update_data)
                    QMessageBox.information(self, self.tr("Success"), self.tr(f"Technician '{updated.nom_complet}' updated."))
                    self.refresh_techniciens()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Update Error"), self.tr(f"Unable to update:\n{e}"))
                     logger.error(f"Échec màj technicien ID {tech_id}: {e}"); self.refresh_techniciens()
                except Exception as e:
                     QMessageBox.critical(self, self.tr("Unexpected Error"), self.tr(f"Error:\n{e}")); logger.exception(f"Erreur màj tech ID {tech_id}.")
        except (BusinessLogicError, NotFoundError) as e:
             QMessageBox.warning(self, self.tr("Error"), self.tr(f"Unable to load technician:\n{e}")); self.refresh_techniciens()
        except Exception as e:
             QMessageBox.critical(self, self.tr("Unexpected Error"), self.tr(f"Error:\n{e}")); logger.exception(f"Erreur avant dialogue édition tech ID {tech_id}.")

    @Slot()
    def delete_technicien(self):
        tech_id = self._get_selected_technicien_id()
        if tech_id is None: return

        tech = self.maintenance_service.get_technicien_by_id(tech_id)
        nom = tech.nom_complet if tech else f"ID {tech_id}"

        reply = QMessageBox.question(
            self,
            self.tr("Delete Confirmation"),
            self.tr(f"Delete technician '{nom}'?\n(Not possible if they have performed maintenance.)"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative suppression technicien ID {tech_id} via service.")
                 # Supposer une méthode delete_technicien dans le service
                success = self.maintenance_service.delete_technicien(tech_id) # <-- A AJOUTER DANS MaintenanceService
                if success:
                    QMessageBox.information(self, self.tr("Success"), self.tr(f"Technician '{nom}' deleted."))
                    self.refresh_techniciens()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Delete Error"), self.tr(f"Unable to delete:\n{e}"))
                 logger.error(f"Échec suppression tech ID {tech_id}: {e}"); self.refresh_techniciens()
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Unexpected Error"), self.tr(f"Error:\n{e}")); logger.exception(f"Erreur suppression tech ID {tech_id}.")