# gmao_app/app/ui/dialogs/login_dialog.py
import logging
from typing import Optional, TYPE_CHECKING

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QMessageBox, QLabel, QDialogButtonBox, QWidget)
from PySide6.QtCore import Slot, Qt
# Import seulement pour le type hinting si nécessaire, évite import circulaire complet
if TYPE_CHECKING:
     from app.core.services.user_service import UserService
     from app.core.models.utilisateur import Utilisateur

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    """ Dialogue de connexion utilisateur. """

    def __init__(self, user_service: "UserService", parent: Optional[QWidget] = None):
         super().__init__(parent)
         # Import QWidget ici si vous gardez le parent optionnel
         from PySide6.QtWidgets import QWidget

         self.user_service = user_service
         self.authenticated_user: Optional["Utilisateur"] = None

         self.setWindowTitle(self.tr("Connexion - GMAO App"))
         self.setModal(True) # Bloque les autres fenêtres
         self.setMinimumWidth(350)

         self._setup_ui()

    def _setup_ui(self):
        """ Configure l'interface utilisateur du dialogue. """
        self.layout = QVBoxLayout(self)

        # Message d'erreur potentiel
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setVisible(False) # Caché au départ
        self.layout.addWidget(self.error_label)

        # Formulaire
        form_layout = QFormLayout()
        self.login_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password) # Masquer mot de passe

        form_layout.addRow(self.tr("Nom d'utilisateur:"), self.login_edit)
        form_layout.addRow(self.tr("Mot de passe:"), self.password_edit)
        self.layout.addLayout(form_layout)

        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("Connexion")) # Renommer OK
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Annuler"))
        self.layout.addWidget(self.button_box)

        # Connecter signaux
        self.button_box.accepted.connect(self._attempt_login) # Connecter OK à attempt_login
        self.button_box.rejected.connect(self.reject) # Cancel -> reject()
        # Permettre connexion avec Entrée sur les champs
        self.login_edit.returnPressed.connect(self._attempt_login)
        self.password_edit.returnPressed.connect(self._attempt_login)

        # Focus initial
        self.login_edit.setFocus()

    @Slot() # type: ignore
    def _attempt_login(self):
        """ Tente de connecter l'utilisateur avec les identifiants saisis. """
        login = self.login_edit.text().strip()
        password = self.password_edit.text() # Pas de strip() sur le mot de passe

        if not login or not password:
            self._show_error(self.tr("Veuillez entrer un nom d'utilisateur et un mot de passe."))
            return

        # Cacher l'erreur précédente
        self.error_label.setVisible(False)
        # Désactiver boutons pendant vérification (optionnel)
        self.button_box.setEnabled(False)

        try:
            user = self.user_service.authenticate_user(login, password)

            if user:
                 logger.info(f"Connexion réussie pour l'utilisateur ID {user.id_utilisateur} ({user.login}).")
                 self.authenticated_user = user
                 self.accept() # Ferme le dialogue avec succès
            else:
                 logger.warning(f"Échec de connexion pour l'utilisateur '{login}'.")
                 self._show_error(self.tr("Nom d'utilisateur ou mot de passe incorrect."))
                 self.password_edit.clear() # Vider seulement le mdp
                 self.login_edit.selectAll()
                 self.login_edit.setFocus()
                 self.button_box.setEnabled(True) # Réactiver boutons

        except Exception as e:
             # Gérer erreurs potentielles du service (ex: DB inaccessible)
             logger.exception(f"Erreur lors de la tentative de connexion pour '{login}': {e}")
             self._show_error(self.tr(f"Erreur de connexion: {e}"))
             self.button_box.setEnabled(True)


    def _show_error(self, message: str):
        """ Affiche un message d'erreur dans le label dédié. """
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def get_authenticated_user(self) -> Optional["Utilisateur"]:
        """ Retourne l'objet Utilisateur si l'authentification a réussi. """
        return self.authenticated_user