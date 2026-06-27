# gmao_app/app/ui/views/base_crud_view.py
"""
Classe de base abstraite pour les vues CRUD.
Factorise le pattern commun à toutes les vues (SiteView, TechnicienView, EquipeView, etc.).

Refactoring M11 — Créé comme base pour les futures migrations des vues existantes.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, TypeVar, Generic, Type

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox, QDialog,
)
from PySide6.QtCore import Qt, Slot

from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type du modèle (ex: Site, Technicien, Equipe)


class BaseCrudView(QWidget, Generic[T], ABC):
    """
    Classe abstraite pour les vues CRUD avec QTableWidget.

    Encapsule:
      - Configuration de la QTableWidget (setup)
      - Boutons standard: Ajouter, Modifier, Supprimer, Rafraîchir
      - Gestion de la sélection et des états des boutons
      - Signaux connectés automatiquement

    Les sous-classes doivent implémenter:
      - setup_table() : configurer les colonnes et en-têtes
      - populate_table(data: List[T]) : remplir la table avec les données
      - refresh() : recharger les données depuis le service
      - get_dialog_class() : retourner la classe de dialogue pour add/edit
      - get_service() : retourner le service métier
    """

    def __init__(self, parent=None):
        """Initialise la vue CRUD avec les widgets standard."""
        super().__init__(parent)

        # --- Widgets standard ---
        self.table_widget = QTableWidget(self)
        self.add_button = QPushButton(self.tr("Ajouter"))
        self.edit_button = QPushButton(self.tr("Modifier"))
        self.delete_button = QPushButton(self.tr("Supprimer"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))

        # --- Configuration de la table (à faire par les sous-classes) ---
        self.setup_table()

        # --- Layout standard ---
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

        # --- Connexions ---
        self.connect_signals()

        # --- État initial ---
        self._update_button_states()

        logger.debug(f"{self.__class__.__name__} initialisée avec BaseCrudView.")

    # ==================================================================
    # Méthodes abstraites (à implémenter par les sous-classes)
    # ==================================================================

    @abstractmethod
    def setup_table(self):
        """
        Configure la QTableWidget: nombre de colonnes, en-têtes, comportement.
        Exemple:
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["ID", "Nom", "Description"])
        """
        ...

    @abstractmethod
    def populate_table(self, data: List[T]):
        """
        Remplit la table avec la liste de modèles.
        Chaque ligne doit avoir un QTableWidgetItem avec UserRole contenant l'ID.
        Exemple:
            id_item = QTableWidgetItem(str(obj.id))
            id_item.setData(Qt.ItemDataRole.UserRole, obj.id)
            self.table_widget.setItem(row, 0, id_item)
        """
        ...

    @abstractmethod
    def refresh(self):
        """
        Recharge les données depuis le service et met à jour la table.
        Appelé par le bouton Rafraîchir et après chaque opération CRUD.
        """
        ...

    @abstractmethod
    def get_dialog_class(self):
        """
        Retourne la classe de dialogue utilisée pour ajouter/modifier.
        Exemple: return SiteDialog
        """
        ...

    @abstractmethod
    def get_service(self):
        """
        Retourne le service métier associé à cette vue.
        Exemple: return self.machine_service
        """
        ...

    # ==================================================================
    # Méthodes concrètes (communes à toutes les vues CRUD)
    # ==================================================================

    def connect_signals(self):
        """Connecte les signaux des boutons et de la table."""
        self.add_button.clicked.connect(self.on_add)
        self.edit_button.clicked.connect(self.on_edit)
        self.delete_button.clicked.connect(self.on_delete)
        self.refresh_button.clicked.connect(self.refresh)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.on_edit)

    def _update_button_states(self):
        """Active/désactive les boutons Modifier/Supprimer selon la sélection."""
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_id(self) -> Optional[int]:
        """
        Retourne l'ID de l'élément sélectionné (colonne 0, UserRole).

        Returns:
            int ou None si aucune sélection.
        """
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0)
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    def _get_selected_object(self) -> Optional[T]:
        """
        Retourne l'objet modèle correspondant à la ligne sélectionnée.
        Utilise get_service().get_by_id().

        Returns:
            Le modèle ou None.
        """
        obj_id = self._get_selected_id()
        if obj_id is None:
            return None
        try:
            return self.get_service().get_by_id(obj_id)
        except Exception as e:
            logger.error(f"Erreur récupération objet ID {obj_id}: {e}")
            return None

    def refresh_data(self):
        """
        Méthode générique de rafraîchissement (peut être appelée par MainWindow).
        Par défaut, délègue à self.refresh().
        """
        self.refresh()

    # ==================================================================
    # Slots CRUD standard
    # ==================================================================

    @Slot()
    def on_add(self):
        """Ouvre le dialogue pour ajouter un nouvel élément."""
        logger.debug(f"{self.__class__.__name__}: Ouverture dialogue ajout.")
        dialog_class = self.get_dialog_class()
        dialog = dialog_class(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()  # Convention: le dialogue expose get_data()
            try:
                logger.info(f"{self.__class__.__name__}: Création via service.")
                self.get_service().create(data)
                QMessageBox.information(self, self.tr("Succès"), self.tr("Élément créé avec succès."))
                self.refresh()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                QMessageBox.warning(self, self.tr("Erreur"), str(e))
                logger.error(f"Échec création: {e}")
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur"), str(e))
                logger.exception("Erreur inattendue lors de la création.")

    @Slot()
    def on_edit(self):
        """Ouvre le dialogue pour modifier l'élément sélectionné."""
        obj_id = self._get_selected_id()
        if obj_id is None:
            return
        try:
            existing = self._get_selected_object()
            if not existing:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("L'élément n'existe plus."))
                self.refresh()
                return

            logger.debug(f"{self.__class__.__name__}: Ouverture dialogue édition ID: {obj_id}.")
            dialog_class = self.get_dialog_class()
            dialog = dialog_class(existing=existing, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                try:
                    logger.info(f"{self.__class__.__name__}: Màj ID {obj_id} via service.")
                    self.get_service().update(obj_id, data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Élément mis à jour."))
                    self.refresh()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                    QMessageBox.warning(self, self.tr("Erreur"), str(e))
                    logger.error(f"Échec màj ID {obj_id}: {e}")
                    self.refresh()
                except Exception as e:
                    QMessageBox.critical(self, self.tr("Erreur"), str(e))
                    logger.exception(f"Erreur inattendue màj ID {obj_id}.")
        except (BusinessLogicError, NotFoundError) as e:
            QMessageBox.warning(self, self.tr("Erreur"), str(e))
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur"), str(e))
            logger.exception(f"Erreur inattendue avant dialogue édition ID {obj_id}.")

    @Slot()
    def on_delete(self):
        """Supprime l'élément sélectionné après confirmation."""
        obj_id = self._get_selected_id()
        if obj_id is None:
            return

        existing = self._get_selected_object()
        name = getattr(existing, 'nom', str(obj_id)) if existing else f"ID {obj_id}"

        reply = QMessageBox.question(
            self,
            self.tr("Confirmer la suppression"),
            self.tr(f"Êtes-vous sûr de vouloir supprimer '{name}' ?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"{self.__class__.__name__}: Suppression ID {obj_id} via service.")
                success = self.get_service().delete(obj_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Élément supprimé."))
                    self.refresh()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                msg = str(e)
                if "foreign key constraint" in msg.lower() or "clé étrangère" in msg.lower():
                    user_msg = self.tr("Impossible de supprimer car d'autres éléments y sont encore associés.")
                else:
                    user_msg = str(e)
                QMessageBox.warning(self, self.tr("Erreur"), user_msg)
                logger.error(f"Échec suppression ID {obj_id}: {e}")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Erreur"), str(e))
                logger.exception(f"Erreur inattendue suppression ID {obj_id}.")
