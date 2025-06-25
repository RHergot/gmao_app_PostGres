from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt

class DBConnectionDialog(QDialog):
    """Boîte de dialogue pour saisir/modifier les paramètres de connexion PostgreSQL."""

    def __init__(self, current_config: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Connexion à la base de données"))
        self.setMinimumWidth(400)

        # Pré-remplir avec les valeurs actuelles si fournies
        current_config = current_config or {}
        self.db_input = QLineEdit(self)
        self.db_input.setText(current_config.get("POSTGRES_DB", ""))
        self.user_input = QLineEdit(self)
        self.user_input.setText(current_config.get("POSTGRES_USER", ""))
        self.pw_input = QLineEdit(self)
        self.pw_input.setText(current_config.get("POSTGRES_PASSWORD", ""))
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.host_input = QLineEdit(self)
        self.host_input.setText(current_config.get("POSTGRES_HOST", ""))
        self.port_input = QLineEdit(self)
        self.port_input.setText(str(current_config.get("POSTGRES_PORT", "")))

        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Base de données :"), self.db_input)
        form_layout.addRow(self.tr("Utilisateur :"), self.user_input)
        form_layout.addRow(self.tr("Mot de passe :"), self.pw_input)
        form_layout.addRow(self.tr("Hôte :"), self.host_input)
        form_layout.addRow(self.tr("Port :"), self.port_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def get_config(self) -> dict:
        return {
            "POSTGRES_DB": self.db_input.text().strip(),
            "POSTGRES_USER": self.user_input.text().strip(),
            "POSTGRES_PASSWORD": self.pw_input.text().strip(),
            "POSTGRES_HOST": self.host_input.text().strip(),
            "POSTGRES_PORT": self.port_input.text().strip(),
        }

