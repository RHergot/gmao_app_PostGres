# gmao_app/app/ui/views/gamme_view.py
"""
Widget pour afficher et gérer la liste des Gammes d'Entretien.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QCheckBox, QLabel, QDialog
)
from PySide6.QtCore import Qt, Slot
from typing import List, Optional, Dict, Any
from datetime import date
from app.config import Language

# Importer Modèles, Services, Dialogue
from app.core.models.gamme_entretien import GammeEntretien
from app.core.models.type_machine import TypeMachine # Pour afficher nom type
from app.core.services.preventive_service import PreventiveMaintenanceService
from app.core.services.machine_service import MachineService # Pour liste types machine
from app.core.services.stock_service import StockService   # Pour liste pièces (dans dialogue)
from app.ui.dialogs.gamme_dialog import GammeDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class GammeView(QWidget):
    """Vue pour la gestion des Gammes d'Entretien."""

    def __init__(self,
                 preventive_service: PreventiveMaintenanceService,
                 machine_service: MachineService,
                 stock_service: StockService,
                 current_user_id: int,
                 parent=None,
                 app_language=None):
        try:
            from main import APP_LANGUAGE
        except ImportError:
            APP_LANGUAGE = None
        from app.config import app_config, Language
        self.app_language = app_language if app_language is not None else (APP_LANGUAGE if APP_LANGUAGE is not None else getattr(app_config, 'language', Language.FRENCH))
        super().__init__(parent)
        self.preventive_service = preventive_service
        self.machine_service = machine_service # Nécessaire pour GammeDialog et map types
        self.stock_service = stock_service     # Nécessaire pour GammeDialog
        self.current_user_id = current_user_id
        self.current_gammes: List[GammeEntretien] = []
        self.type_machine_map: Dict[int, str] = {} # Cache pour noms types machine

        logger.debug("Initialisation de GammeView...")

        # Widgets
        self.show_inactive_checkbox = QCheckBox(self.tr("Afficher Gammes Inactives"))
        self.table_widget = QTableWidget(self)
        self.setup_table()
        self.add_button = QPushButton(self.tr("Ajouter Gamme"))
        self.edit_button = QPushButton(self.tr("Modifier Gamme"))
        self.delete_button = QPushButton(self.tr("Supprimer Gamme"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))
        # Bouton pour génération manuelle des OT (temporaire ou permanent?)
        self.generate_ot_button = QPushButton(self.tr("Générer OT Préventifs Échus"))

        # Layouts
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.show_inactive_checkbox)
        top_layout.addStretch()
        top_layout.addWidget(self.generate_ot_button) # Placé en haut à droite

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button); button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button); button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table_widget); main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Connexions & Init
        self.connect_signals()
        self._update_button_states()
        self.refresh_gammes()
        logger.debug("GammeView initialisée.")

    def setup_table(self):
        """Configure la table des gammes."""
        # ID(0,hid), Desc(1), TypeMach(2), TypeEntr(3), Periodicite(4), Derniere(5), Prochaine(6), Active(7)
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Description / Code"), self.tr("Type Machine"), self.tr("Type Entretien"),
            self.tr("Périodicité"), self.tr("Dernière Réal."), self.tr("Prochaine Échéance"), self.tr("Active")
        ])
        # Configs standard...
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Type Machine
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Type Entretien
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Périodicité
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Dernière
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Prochaine
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Active

        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1; self._sort_order = Qt.SortOrder.AscendingOrder

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_gamme)
        self.edit_button.clicked.connect(self.edit_gamme)
        self.delete_button.clicked.connect(self.delete_gamme)
        self.refresh_button.clicked.connect(self.refresh_gammes)
        if hasattr(self, 'generate_ots') and callable(getattr(self, 'generate_ots')):
            self.generate_ot_button.clicked.connect(self.generate_ots)
        else:
            logging.error("La méthode generate_ots est manquante dans GammeView. Bouton désactivé.")
            self.generate_ot_button.setEnabled(False)
        self.show_inactive_checkbox.stateChanged.connect(self.refresh_gammes)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_gamme)

    def _update_button_states(self):
         has_selection = self.table_widget.selectionModel().hasSelection()
         self.edit_button.setEnabled(has_selection)
         self.delete_button.setEnabled(has_selection)
         # Bouton Génération OT toujours actif? Ou basé sur date? Gardons actif.
         self.generate_ot_button.setEnabled(True)

    def _get_selected_gamme_id(self) -> Optional[int]:
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0)
        if id_item:
            try: return int(id_item.data(Qt.ItemDataRole.UserRole))
            except: return None
        return None

    def _load_type_machine_map(self):
         try:
             types = self.machine_service.get_all_type_machines()
             self.type_machine_map = {tm.id_type_machine: (f"{tm.categorie} - {tm.nom}" if tm.categorie else tm.nom)
                                      for tm in types if tm.id_type_machine is not None}
         except Exception as e: logger.error(f"Err load TypeMachine map: {e}"); self.type_machine_map={}

    def refresh_data(self): self.refresh_gammes()

    @Slot()
    def refresh_gammes(self):
        """ Recharge la liste des gammes. """
        logger.info("Rafraîchissement liste des gammes...")
        active_only = not self.show_inactive_checkbox.isChecked()
        sort_col_name = self._get_sort_column_name()
        sort_desc = self._sort_order == Qt.SortOrder.DescendingOrder
        # Charger map types machine pour affichage
        try: self._load_type_machine_map()
        except Exception as e: logger.error(f"Err reload TypeMachine map: {e}")

        try:
            # TODO: Adapter service/repo pour tri serveur? Pour l'instant tri client.
            self.current_gammes = self.preventive_service.get_all_gammes(active_only=active_only)
             # Tri client
            if self.current_gammes:
                 sort_key = sort_col_name # Utiliser directement nom attribut
                 reverse = sort_desc
                 # Gérer tri sur type_machine_id via la map
                 if sort_key == 'type_machine_id':
                      self.current_gammes.sort(key=lambda x: self.type_machine_map.get(x.type_machine_id, ""), reverse=reverse)
                 # Gérer tri sur périodicité composite? Ou trier sur une des colonnes seulement
                 elif sort_key == 'periodicite_valeur':
                      self.current_gammes.sort(key=lambda x: (x.periodicite_valeur is not None, x.periodicite_valeur), reverse=reverse)
                 else: # Tri standard
                      self.current_gammes.sort(key=lambda x: (getattr(x, sort_key, None) is not None, getattr(x, sort_key, None)), reverse=reverse)

            self.populate_table(self.current_gammes)
            logger.info(f"{len(self.current_gammes)} gammes affichées.")
        except Exception as e: QMessageBox.critical(self, self.tr("Erreur"), self.tr(f"{e}")); logger.exception("Err refresh gammes")

    def populate_table(self, gammes: List[GammeEntretien]):
        """ Remplit la table gammes. """
        self.table_widget.setSortingEnabled(False)
        self.table_widget.setRowCount(0); self.table_widget.setRowCount(len(gammes))
        for row, g in enumerate(gammes):
            id_item = QTableWidgetItem(str(g.id_gamme))
            id_item.setData(Qt.ItemDataRole.UserRole, g.id_gamme)
            tm_nom = self.type_machine_map.get(g.type_machine_id, self.tr("Générique")) if g.type_machine_id else self.tr("Générique")
            periodicite_str = ""
            if g.periodicite_valeur and g.periodicite_unite:
                periodicite_str = f"{g.periodicite_valeur} {g.periodicite_unite}"
            last_date_str = g.date_derniere_realisation.strftime('%Y-%m-%d') if g.date_derniere_realisation else self.tr("N/A")
            next_date_str = g.prochaine_date_calculee.strftime('%Y-%m-%d') if g.prochaine_date_calculee else self.tr("N/A")  # Ou recalculer ici?
            active_str = self.tr("Oui") if g.active else self.tr("Non")

            # Créer items
            item_id = id_item
            item_desc = QTableWidgetItem(g.description or "")
            item_tm = QTableWidgetItem(tm_nom)
            item_type = QTableWidgetItem(g.type_entretien or "")
            item_period = QTableWidgetItem(periodicite_str)
            item_period.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_last = QTableWidgetItem(last_date_str)
            item_last.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_next = QTableWidgetItem(next_date_str)
            item_next.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_active = QTableWidgetItem(active_str)
            item_active.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Remplir ligne
            self.table_widget.setItem(row, 0, item_id)
            self.table_widget.setItem(row, 1, item_desc)
            self.table_widget.setItem(row, 2, item_tm)
            self.table_widget.setItem(row, 3, item_type)
            self.table_widget.setItem(row, 4, item_period)
            self.table_widget.setItem(row, 5, item_last)
            self.table_widget.setItem(row, 6, item_next)
            self.table_widget.setItem(row, 7, item_active)

        self._update_button_states(); self.table_widget.setSortingEnabled(True)
        self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)

    @Slot(int)
    def sort_table(self, logical_index: int):
        if self._sort_column == logical_index: self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else: self._sort_column = logical_index; self._sort_order = Qt.SortOrder.AscendingOrder
        self.refresh_gammes() # Applique tri client

    def _get_sort_column_name(self) -> str:
         # Tri sur type_machine via ID (mappé dans refresh pour affichage/tri)
         # Tri sur periodicité via valeur?
         column_map = { 1: "description", 2: "type_machine_id", 3: "type_entretien",
                       4: "periodicite_valeur", 5: "date_derniere_realisation",
                       6: "prochaine_date_calculee", 7: "active" }
         return column_map.get(self._sort_column, "description")

    # --- Slots CRUD ---
    @Slot()
    def add_gamme(self):
        logger.debug("Ouv. dialogue ajout gamme.")
        dialog = GammeDialog(preventive_service=self.preventive_service,
                             machine_service=self.machine_service,
                             stock_service=self.stock_service,
                             current_user_id=self.current_user_id,
                             parent=self,
                             app_language=self.app_language)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_gamme_data()
            etapes = data.pop("etapes", [])
            pieces = data.pop("pieces_types", [])
            try:
                new_gamme = self.preventive_service.create_gamme(data, self.current_user_id)
                self.preventive_service.save_etapes_for_gamme(new_gamme.id_gamme, etapes)
                self.preventive_service.save_pieces_type_for_gamme(new_gamme.id_gamme, pieces)
                QMessageBox.information(self, self.tr("Succès"), self.tr(f"Gamme '{new_gamme.description}' créée."))
                self.refresh_gammes()
            except Exception as e:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr(f"{e}"))
                logger.error(f"{e}", exc_info=True)

    @Slot()
    def edit_gamme(self):
        g_id = self._get_selected_gamme_id()
        if g_id is None:
            return
        try:
            g_edit = self.preventive_service.get_gamme_by_id(g_id)
            if not g_edit:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Gamme n'existe plus."))
                self.refresh_gammes()
                return
            dialog = GammeDialog(preventive_service=self.preventive_service,
                                 machine_service=self.machine_service,
                                 stock_service=self.stock_service,
                                 gamme=g_edit,
                                 current_user_id=self.current_user_id,
                                 parent=self,
                                 app_language=self.app_language)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_gamme_data()
                etapes = data.pop("etapes", [])
                pieces = data.pop("pieces_types", [])
                try:
                    updated = self.preventive_service.update_gamme(g_id, data)
                    self.preventive_service.save_etapes_for_gamme(g_id, etapes)
                    self.preventive_service.save_pieces_type_for_gamme(g_id, pieces)
                    QMessageBox.information(self, self.tr("Succès"), self.tr(f"Gamme '{updated.description}' mise à jour."))
                    self.refresh_gammes()
                except Exception as e:
                    QMessageBox.warning(self, self.tr("Erreur"), self.tr(f"{e}"))
                    logger.error(f"{e}", exc_info=True)
                    self.refresh_gammes()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr(f"{e}"))
            logger.exception(f"Err édit {g_id}")

    @Slot()
    def delete_gamme(self):
        g_id = self._get_selected_gamme_id()
        if g_id is None:
            return
        g = self.preventive_service.get_gamme_by_id(g_id)
        desc = g.description if g else f"ID {g_id}"
        if QMessageBox.question(self, self.tr("Confirmer"), self.tr(f"Supprimer gamme '{desc}' et toutes ses étapes/pièces liées?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                if self.preventive_service.delete_gamme(g_id):
                    QMessageBox.information(self, self.tr("Succès"), self.tr(f"Gamme '{desc}' supprimée."))
                    self.refresh_gammes()
            except Exception as e:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr(f"{e}"))
                logger.error(f"{e}")
                self.refresh_gammes()

    @Slot()
    def generate_ots(self):
        """ Lance la génération des OT préventifs échus (à date du jour). """
        logger.info("Lancement manuel génération OT préventifs...")
        reply = QMessageBox.information(
            self, self.tr("Génération OT"),
            self.tr("Lancement de la recherche des gammes échues et création des OT correspondants.\n    Ceci peut prendre quelques instants..."),
            QMessageBox.StandardButton.Ok
        )
        try:
            # Appel au service pour générer les OT jusqu'à aujourd'hui
            created_ots = self.preventive_service.generate_preventive_ots(due_date=date.today())
            msg = self.tr("{len(created_ots)} OT préventifs ont été générés.").format(**{"len(created_ots)": len(created_ots)})
            if len(created_ots) > 0:
                msg += self.tr("\n    Rafraîchissez la vue des Ordres de Travail pour les voir.")
            QMessageBox.information(self, self.tr("Génération Terminée"), msg)
            # Rafraîchir aussi cette vue pour voir les dates mises à jour?
            self.refresh_gammes()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Génération"), self.tr("Une erreur est survenue:\n    {e}").format(e=e))
            logger.exception("Erreur lors de la génération manuelle des OT préventifs.")