# gmao_app/app/ui/views/site_view.py
"""
Widget pour afficher et gérer la liste des Sites.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional

# Importer modèle, service et dialogue
from app.core.models.site import Site
from app.core.services.machine_service import MachineService # On réutilise MachineService
from app.ui.dialogs.site_dialog import SiteDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class SiteView(QWidget):
    """Vue pour la gestion des Sites."""

    def __init__(self, machine_service: MachineService, parent=None):
        super().__init__(parent)
        self.machine_service = machine_service
        self.current_sites: List[Site] = []

        logger.debug("Initialisation de SiteView...")

        # --- Widgets ---
        self.table_widget = QTableWidget(self)
        self.setup_table()

        self.add_button = QPushButton(self.tr("Ajouter Site"))
        self.edit_button = QPushButton(self.tr("Modifier Site"))
        self.delete_button = QPushButton(self.tr("Supprimer Site"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))

        # --- Layouts ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        main_layout = QVBoxLayout(self)
        # Pas de filtres pour l'instant pour cette vue simple
        main_layout.addWidget(self.table_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- Connexions ---
        self.connect_signals()

        # --- État initial & chargement ---
        self._update_button_states()
        self.refresh_sites()

        logger.debug("SiteView initialisée.")

    def setup_table(self):
        """Configure la table des sites."""
        self.table_widget.setColumnCount(6) # ID, Nom, Adresse, Ville, Pays, Contact
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom"), self.tr("Adresse"), self.tr("Ville"), self.tr("Pays"), self.tr("Contact Principal")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)

        self.table_widget.setColumnHidden(0, True) # Cacher ID

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Adresse
        # Autres colonnes en mode interactif ou contenu
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1 # Nom par défaut
        self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        """Connecte les signaux."""
        self.add_button.clicked.connect(self.add_site)
        self.edit_button.clicked.connect(self.edit_site)
        self.delete_button.clicked.connect(self.delete_site)
        self.refresh_button.clicked.connect(self.refresh_sites)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_site)

    def _update_button_states(self):
        """Met à jour état Modifier/Supprimer."""
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_site_id(self) -> Optional[int]:
        """Retourne l'ID du site sélectionné."""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0) # Colonne ID
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def refresh_data(self):
         """Méthode générique pour rafraîchir (peut être appelée par MainWindow)."""
         self.refresh_sites()

    @Slot()
    def refresh_sites(self):
        """Recharge et affiche la liste des sites."""
        logger.info("Rafraîchissement de la liste des sites...")
        # TODO: Ajouter gestion du tri dans le service/repo si besoin performance
        # Pour l'instant, on trie côté client après récupération.
        try:
            self.current_sites = self.machine_service.get_all_sites()
            # Tri côté client (simple pour peu de données)
            if self.current_sites:
                 sort_key = self._get_sort_column_key()
                 reverse = (self._sort_order == Qt.SortOrder.DescendingOrder)
                 # Gérer le cas où l'attribut est None
                 self.current_sites.sort(key=lambda x: (getattr(x, sort_key) is not None, getattr(x, sort_key)), reverse=reverse)

            self.populate_table(self.current_sites)
            logger.info(f"{len(self.current_sites)} sites affichés.")

        except BusinessLogicError as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger la liste des sites.") + f":\n{e}")
            logger.error(f"Erreur métier chargement sites: {e}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur est survenue.") + f":\n{e}")
            logger.exception("Erreur inattendue chargement/affichage sites.")

    def populate_table(self, sites: List[Site]):
         """ Remplit la table avec la liste de sites. """
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(len(sites))

         for row, site in enumerate(sites):
             id_item = QTableWidgetItem(str(site.id_site))
             id_item.setData(Qt.ItemDataRole.UserRole, site.id_site)
             self.table_widget.setItem(row, 0, id_item) # ID
             self.table_widget.setItem(row, 1, QTableWidgetItem(site.nom or "")) # Nom
             self.table_widget.setItem(row, 2, QTableWidgetItem(site.adresse or ""))
             self.table_widget.setItem(row, 3, QTableWidgetItem(site.ville or ""))
             self.table_widget.setItem(row, 4, QTableWidgetItem(site.pays or ""))
             self.table_widget.setItem(row, 5, QTableWidgetItem(site.contact_principal or ""))

         self._update_button_states()
         self.table_widget.setSortingEnabled(True)
         self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)

    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Tri la table quand un en-tête est cliqué. """
        if self._sort_column == logical_index:
             self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
             self._sort_column = logical_index
             self._sort_order = Qt.SortOrder.AscendingOrder
        # Rafraîchir pour appliquer le tri côté client
        self.refresh_sites()

    def _get_sort_column_key(self) -> str:
         """ Retourne le nom de l'attribut modèle pour le tri. """
         column_map = { 1: "nom", 2: "adresse", 3: "ville", 4: "pays", 5: "contact_principal" }
         return column_map.get(self._sort_column, "nom")

    @Slot()
    def add_site(self):
        """ Ouvre le dialogue pour ajouter un site. """
        logger.debug("Ouverture dialogue ajout site.")
        dialog = SiteDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            site_data = dialog.get_site_data()
            try:
                logger.info(f"Tentative création site via service: {site_data.get('nom')}")
                self.machine_service.create_site(site_data)
                QMessageBox.information(self, self.tr("Succès"), self.tr("Site créé avec succès.") + f": {site_data.get('nom')}")
                self.refresh_sites()
            except (BusinessLogicError, DatabaseError) as e:
                 QMessageBox.warning(self, self.tr("Erreur de validation"), str(e))
                 logger.error(f"Échec création site: {e}")
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue.") + f":\n{e}")
                 logger.exception("Erreur inattendue création site.")

    @Slot()
    def edit_site(self):
        """ Ouvre le dialogue pour modifier le site sélectionné. """
        site_id = self._get_selected_site_id()
        if site_id is None: return
        try:
            site_to_edit = self.machine_service.get_site_by_id(site_id)
            if not site_to_edit:
                 QMessageBox.warning(self, self.tr("Erreur"), self.tr("Le site n'existe plus."))
                 self.refresh_sites(); return

            logger.debug(f"Ouverture dialogue édition site ID: {site_id}")
            dialog = SiteDialog(site=site_to_edit, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_site_data()
                try:
                    logger.info(f"Tentative màj site ID {site_id} via service.")
                    updated = self.machine_service.update_site(site_id, update_data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Site mis à jour avec succès: {nom}").format(nom=updated.nom))
                    self.refresh_sites()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Erreur de base de données"), self.tr("Impossible de mettre à jour le site.\n{e}").format(e=e))
                     logger.error(f"Échec màj site ID {site_id}: {e}")
                     self.refresh_sites()
                except Exception as e:
                     QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue.") + f":\n{e}")
                     logger.exception(f"Erreur inattendue màj site ID {site_id}.")
        except (BusinessLogicError, NotFoundError) as e:
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger le site.\n{e}").format(e=e))
             self.refresh_sites()
        except Exception as e:
             QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur est survenue.") + f":\n{e}")
             logger.exception(f"Erreur inattendue avant dialogue édition site ID {site_id}.")

    @Slot()
    def delete_site(self):
        """ Supprime le site sélectionné. """
        site_id = self._get_selected_site_id()
        if site_id is None: return

        site = self.machine_service.get_site_by_id(site_id)
        nom = site.nom if site else f"ID {site_id}"

        reply = QMessageBox.question(
            self, self.tr("Confirmer la suppression"),
            self.tr("Êtes-vous sûr de vouloir supprimer le site '{nom}' ?").format(nom=nom),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative suppression site ID {site_id} via service.")
                success = self.machine_service.delete_site(site_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Le site a été supprimé avec succès."))
                    self.refresh_sites()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                msg = str(e)
                if "violates foreign key constraint" in msg or "clé étrangère" in msg:
                    user_msg = self.tr("Impossible de supprimer le site car des machines y sont encore associées.")
                else:
                    user_msg = self.tr("Impossible de supprimer le site.\n{e}").format(e=msg)
                QMessageBox.warning(self, self.tr("Erreur de base de données"), user_msg)
                logger.error(f"Échec suppression site ID {site_id}: {e}")
                self.refresh_sites()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue.") + f":\n{e}")
                logger.exception(f"Erreur inattendue suppression site ID {site_id}.")