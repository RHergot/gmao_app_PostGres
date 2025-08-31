# gmao_app/app/ui/views/user_view.py
"""
Widget pour afficher et gérer la liste des utilisateurs.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, Slot

# Importer modèles, services et dialogue
from app.core.models.utilisateur import Utilisateur
from app.core.services.user_service import UserService
from app.ui.dialogs.user_dialog import UserDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class UserView(QWidget):
    """Vue pour la gestion des utilisateurs."""

    def __init__(self, user_service: UserService, parent=None):
        """
        Initialise la vue.

        Args:
            user_service (UserService): L'instance du service utilisateur.
            parent: Le widget parent.
        """
        super().__init__(parent)
        self.user_service = user_service
        self.current_users: list[Utilisateur] = [] # Garder une copie locale

        logger.debug("Initialisation de UserView...")

        # --- Widgets ---
        self.table_widget = QTableWidget(self)
        self.setup_table()

        self.add_button = QPushButton(self.tr("Ajouter Utilisateur"))
        self.edit_button = QPushButton(self.tr("Modifier Utilisateur"))
        self.delete_button = QPushButton(self.tr("Supprimer Utilisateur"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))

        # --- Layouts ---
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

        # --- État initial & chargement des données ---
        self._update_button_states()
        self.refresh_users() # Charger les utilisateurs au démarrage de la vue

        logger.debug("UserView initialisée.")

    def setup_table(self):
        """Configure le QTableWidget."""
        self.table_widget.setColumnCount(6) # ID, Login, Nom, Email, Rôle, Actif
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Login"), self.tr("Nom Complet"), self.tr("Email"), self.tr("Rôle"), self.tr("Actif")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False) # Cacher numéros de ligne
        # Ajuster colonnes
        self.table_widget.setColumnHidden(0, True) # Cacher ID technique
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Login
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Email
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Role
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Actif

    def connect_signals(self):
        """Connecte les signaux aux slots."""
        self.add_button.clicked.connect(self.add_user)
        self.edit_button.clicked.connect(self.edit_user)
        self.delete_button.clicked.connect(self.delete_user)
        self.refresh_button.clicked.connect(self.refresh_users)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_user) # Double-clic pour éditer

    def _update_button_states(self):
        """Met à jour l'état activé/désactivé des boutons Modifier/Supprimer."""
        has_selection = len(self.table_widget.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _get_selected_user_id(self) -> Optional[int]:
        """Retourne l'ID de l'utilisateur sélectionné dans la table, ou None."""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows:
            return None
        first_row_index = selected_rows[0].row()
        id_item = self.table_widget.item(first_row_index, 0) # Colonne 0 = ID
        if id_item:
            try:
                return int(id_item.data(Qt.ItemDataRole.UserRole)) # Récupère l'ID stocké
            except (ValueError, TypeError):
                 logger.error(f"Donnée ID invalide dans la table ligne {first_row_index}")
                 return None
        return None


    @Slot()
    def refresh_users(self):
        """Recharge et affiche la liste des utilisateurs depuis le service."""
        logger.info("Rafraîchissement de la liste des utilisateurs...")
        try:
            self.current_users = self.user_service.get_all_users()
            self.table_widget.setRowCount(len(self.current_users))

            for row_index, user in enumerate(self.current_users):
                # ID (stocké dans UserRole)
                id_item = QTableWidgetItem(str(user.id_utilisateur))
                id_item.setData(Qt.ItemDataRole.UserRole, user.id_utilisateur)
                self.table_widget.setItem(row_index, 0, id_item)

                # Autres colonnes
                self.table_widget.setItem(row_index, 1, QTableWidgetItem(user.login))
                self.table_widget.setItem(row_index, 2, QTableWidgetItem(user.nom_complet or ""))
                self.table_widget.setItem(row_index, 3, QTableWidgetItem(user.email or ""))
                self.table_widget.setItem(row_index, 4, QTableWidgetItem(user.role))

                # Affichage 'Actif' (Oui/Non)
                actif_text = self.tr("Oui") if user.actif else self.tr("Non")
                actif_item = QTableWidgetItem(actif_text)
                # Optionnel : Centrer le texte
                actif_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row_index, 5, actif_item)

            self._update_button_states() # Mettre à jour si la sélection a changé (ou disparu)
            logger.info(f"{len(self.current_users)} utilisateurs affichés.")

        except BusinessLogicError as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"), self.tr(f"Impossible de charger les utilisateurs:\n{e}"))
            logger.error(f"Erreur métier lors du chargement des users: {e}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Une erreur est survenue:\n{e}"))
            logger.exception("Erreur inattendue lors du chargement/affichage des users.")


    @Slot()
    def add_user(self):
        """Ouvre le dialogue pour ajouter un nouvel utilisateur."""
        logger.debug("Ouverture dialogue ajout utilisateur.")
        dialog = UserDialog(parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_user_data()
            # Extraire le mot de passe pour le passer séparément au service
            password = user_data.pop("password", None)
            if not password: # Devrait être validé par le dialogue, mais sécurité
                 QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le mot de passe est requis pour la création."))
                 return

            try:
                logger.info(f"Tentative de création utilisateur via service: {user_data['login']}")
                # Passer les arguments au service par nom pour clarté
                self.user_service.create_user(
                    login=user_data['login'],
                    password=password,
                    role=user_data['role'],
                    nom_complet=user_data.get('nom_complet'),
                    email=user_data.get('email'),
                    actif=user_data.get('actif', True),
                    # technicien_id=user_data.get('technicien_id') # A gérer plus tard
                )
                QMessageBox.information(self, self.tr("Succès"), self.tr(f"Utilisateur '{user_data['login']}' créé avec succès."))
                self.refresh_users() # Mettre à jour la liste
            except (BusinessLogicError, DatabaseError) as e:
                 QMessageBox.warning(self, self.tr("Erreur de Création"), self.tr(f"Impossible de créer l'utilisateur:\n{e}"))
                 logger.error(f"Échec création user '{user_data['login']}': {e}")
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Une erreur est survenue:\n{e}"))
                 logger.exception(f"Erreur inattendue création user '{user_data['login']}'.")

    @Slot()
    def edit_user(self):
        """Ouvre le dialogue pour modifier l'utilisateur sélectionné."""
        user_id = self._get_selected_user_id()
        if user_id is None:
             # Normalement les boutons sont désactivés, mais sécurité
             QMessageBox.warning(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un utilisateur à modifier."))
             return

        try:
            # Récupérer l'objet utilisateur complet pour pré-remplir le dialogue
            user_to_edit = self.user_service.get_user_by_id(user_id)
            if not user_to_edit:
                # Cas où l'utilisateur a été supprimé entre temps
                 QMessageBox.warning(self, self.tr("Erreur"), self.tr("L'utilisateur sélectionné n'existe plus."))
                 self.refresh_users()
                 return

            logger.debug(f"Ouverture dialogue édition pour user ID: {user_id}")
            dialog = UserDialog(user=user_to_edit, parent=self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_user_data()
                new_password = update_data.pop("password", None) # Gérer changement mdp séparément

                try:
                    logger.info(f"Tentative de mise à jour utilisateur ID {user_id} via service.")
                    # Mettre à jour les infos de base
                    updated_user = self.user_service.update_user(user_id, update_data)

                    # Si un nouveau mot de passe a été saisi, le changer
                    if new_password:
                        logger.info(f"Tentative de changement de mot de passe pour user ID {user_id}.")
                        # Ici on ne demande pas l'ancien mdp, on assume modif par Admin (à affiner avec permissions)
                        self.user_service.change_password(user_id, old_password=None, new_password=new_password)

                    QMessageBox.information(self, self.tr("Succès"), self.tr(f"Utilisateur '{updated_user.login}' mis à jour avec succès."))
                    self.refresh_users()

                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Erreur de Mise à Jour"), self.tr(f"Impossible de mettre à jour l'utilisateur:\n{e}"))
                     logger.error(f"Échec màj user ID {user_id}: {e}")
                     self.refresh_users() # Rafraîchir au cas où l'erreur est due à une suppression concurente
                except Exception as e:
                     QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Une erreur est survenue:\n{e}"))
                     logger.exception(f"Erreur inattendue màj user ID {user_id}'.")

        except (BusinessLogicError, NotFoundError) as e:
             # Erreur lors de la récupération initiale de l'utilisateur
             QMessageBox.warning(self, self.tr("Erreur"), self.tr(f"Impossible de charger l'utilisateur pour modification:\n{e}"))
             self.refresh_users()
        except Exception as e:
             QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Une erreur est survenue:\n{e}"))
             logger.exception(f"Erreur inattendue avant ouverture dialogue édition user ID {user_id}'.")


    @Slot()
    def delete_user(self):
        """Supprime l'utilisateur sélectionné après confirmation."""
        user_id = self._get_selected_user_id()
        if user_id is None:
             QMessageBox.warning(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner un utilisateur à supprimer."))
             return

        # Récupérer le login pour le message de confirmation
        user = self.user_service.get_user_by_id(user_id) # Peut être None si déjà supprimé
        login = user.login if user else f"ID {user_id}"

        confirmation_text = self.tr("Êtes-vous sûr de vouloir supprimer l'utilisateur '{login}'?\nCette action est irréversible.").format(login=login)
        reply = QMessageBox.question(
            self,
            self.tr("Confirmation de Suppression"),
            confirmation_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative de suppression utilisateur ID {user_id} via service.")
                success = self.user_service.delete_user(user_id)
                if success:
                    info_text = self.tr("Utilisateur '{login}' supprimé.").format(login=login)
                QMessageBox.information(self, self.tr("Succès"), info_text)
                self.refresh_users()
                # else: # Si delete retourne False sans exception (peu probable avec notre logique)
                #    QMessageBox.warning(self, "Échec", "La suppression a échoué (utilisateur non trouvé?).")
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                error_text = self.tr("Impossible de supprimer l'utilisateur:\n{e}").format(e=e)
                QMessageBox.warning(self, self.tr("Erreur de Suppression"), error_text)
                logger.error(f"Échec suppression user ID {user_id}: {e}")
                self.refresh_users() # Pour voir s'il existe encore
            except Exception as e:
                critical_text = self.tr("Une erreur est survenue:\n{e}").format(e=e)
                QMessageBox.critical(self, self.tr("Erreur Inattendue"), critical_text)
                logger.exception(f"Erreur inattendue suppression user ID {user_id}'.")