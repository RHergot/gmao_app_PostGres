# gmao_app/app/ui/dialogs/user_dialog.py
"""
Fenêtre de dialogue pour ajouter ou modifier les informations d'un utilisateur.
"""
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Slot
from typing import Optional, Dict, Any

# Importer le modèle Utilisateur
from app.core.models.utilisateur import Utilisateur
# Importer les rôles valides depuis le service (ou une config)
from app.core.services.user_service import VALID_ROLES

logger = logging.getLogger(__name__)

class UserDialog(QDialog):
    """Dialogue pour créer ou éditer un utilisateur."""

    def __init__(self, user: Optional[Utilisateur] = None, parent=None):
        """
        Initialise le dialogue.

        Args:
            user (Optional[Utilisateur]): L'objet Utilisateur à éditer.
                                            Si None, le dialogue est en mode création.
            parent: Le widget parent.
        """
        super().__init__(parent)

        self.user_original = user # Garde une référence si en mode édition
        self.is_edit_mode = user is not None

        self.setWindowTitle(self.tr("Ajouter un Utilisateur") if not self.is_edit_mode else self.tr("Modifier l'Utilisateur"))
        self.setMinimumWidth(400)

        # --- Widgets du Formulaire ---
        self.login_input = QLineEdit(self)
        self.nom_complet_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.role_combo = QComboBox(self)
        self.role_combo.addItems(VALID_ROLES) # Remplir avec les rôles valides

        self.actif_checkbox = QCheckBox(self.tr("Utilisateur Actif"), self)
        self.actif_checkbox.setChecked(True) # Actif par défaut

        # Champs mot de passe (visibles seulement en mode création ou si on veut changer)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input = QLineEdit(self)
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Login (*):"), self.login_input)
        form_layout.addRow(self.tr("Nom Complet :"), self.nom_complet_input)
        form_layout.addRow(self.tr("Email :"), self.email_input)
        form_layout.addRow(self.tr("Rôle (*):"), self.role_combo)
        form_layout.addRow(self.actif_checkbox) # Checkbox peut prendre toute la largeur

        # Étiquette et champs mot de passe
        form_layout.addRow(self.tr("--- Mot de Passe ---"), None) # Simple séparateur visuel
        if self.is_edit_mode:
            # En édition, on ne demande pas le mdp sauf si changement explicite (plus complexe, pas ici)
            # Pour simplifier, on ne permet le changement de mdp que via une action séparée
            self.password_input.setPlaceholderText(self.tr("Laisser vide pour ne pas changer"))
            self.password_confirm_input.setPlaceholderText(self.tr("Laisser vide pour ne pas changer"))
            form_layout.addRow(self.tr("Nouveau Mdp :"), self.password_input)
            form_layout.addRow(self.tr("Confirmer Mdp :"), self.password_confirm_input)
        else:
            # En création, le mot de passe est requis
            form_layout.addRow(self.tr("Mot de Passe (*):"), self.password_input)
            form_layout.addRow(self.tr("Confirmer Mdp (*):"), self.password_confirm_input)


        # Boutons OK / Annuler
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # --- Pré-remplir les champs si en mode édition ---
        if self.is_edit_mode and self.user_original:
            self._populate_fields()
            # Le login ne devrait pas être modifiable une fois créé
            self.login_input.setReadOnly(True)
            self.login_input.setStyleSheet("background-color: #eee;") # Indiquer visuellement

        logger.debug(f"UserDialog initialisé en mode {'Édition' if self.is_edit_mode else 'Création'}")

    def _populate_fields(self):
        """Remplit les champs du formulaire avec les données de self.user_original."""
        self.login_input.setText(self.user_original.login or "")
        self.nom_complet_input.setText(self.user_original.nom_complet or "")
        self.email_input.setText(self.user_original.email or "")
        # Sélectionner le bon rôle dans le ComboBox
        if self.user_original.role in VALID_ROLES:
            self.role_combo.setCurrentText(self.user_original.role)
        else:
             logger.warning(f"Rôle '{self.user_original.role}' non trouvé dans les rôles valides pour l'utilisateur {self.user_original.login}.")
             # Que faire ? Laisser vide ? Ajouter temporairement?
             # Pour l'instant on laisse vide (ou sur le premier item par défaut)
        self.actif_checkbox.setChecked(self.user_original.actif)
        # Ne pas remplir les champs mot de passe en mode édition

    def _validate_input(self) -> bool:
        """Vérifie si les champs obligatoires sont remplis et cohérents."""
        login = self.login_input.text().strip()
        role = self.role_combo.currentText()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()

        if not login:
            QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le champ 'Login' est obligatoire."))
            self.login_input.setFocus()
            return False
        if not role:
             QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le champ 'Rôle' est obligatoire."))
             self.role_combo.setFocus()
             return False

        if not self.is_edit_mode: # Validation mot de passe seulement en création
            if not password:
                 QMessageBox.warning(self, self.tr("Champ manquant"), self.tr("Le champ 'Mot de Passe' est obligatoire."))
                 self.password_input.setFocus()
                 return False
            if password != password_confirm:
                 QMessageBox.warning(self, self.tr("Mot de Passe"), self.tr("Les mots de passe ne correspondent pas."))
                 self.password_confirm_input.setFocus()
                 return False
            # TODO: Ajouter validation complexité mot de passe ?
        elif password: # Si un nouveau mdp est saisi en mode édition
             if password != password_confirm:
                  QMessageBox.warning(self, self.tr("Mot de Passe"), self.tr("Les nouveaux mots de passe ne correspondent pas."))
                  self.password_confirm_input.setFocus()
                  return False

        # TODO: Ajouter validation format email ?

        return True

    @Slot()
    def accept(self):
        """Valide les données avant de fermer le dialogue."""
        if self._validate_input():
            logger.debug("Validation UserDialog réussie.")
            super().accept()
        else:
            logger.warning("Validation UserDialog échouée.")
            # Le dialogue reste ouvert

    def get_user_data(self) -> Dict[str, Any]:
        """
        Récupère les données saisies dans le formulaire sous forme de dictionnaire.
        Inclut le mot de passe seulement s'il a été saisi.
        """
        data = {
            "login": self.login_input.text().strip(), # Login non modifiable si edit_mode
            "nom_complet": self.nom_complet_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "role": self.role_combo.currentText(),
            "actif": self.actif_checkbox.isChecked(),
            # Ne pas inclure technicien_id ici, à gérer séparément si besoin
        }
        # Ajouter le mot de passe seulement s'il a été saisi (nouveau ou changement)
        password = self.password_input.text()
        if password:
            data["password"] = password # Le service se chargera du hachage

        # Si en mode édition, on retourne aussi l'ID original
        if self.is_edit_mode and self.user_original:
             data["id_utilisateur"] = self.user_original.id_utilisateur

        logger.debug(f"Données récupérées du UserDialog: { {k: v for k, v in data.items() if k != 'password'} }") # Log sans le mdp
        return data