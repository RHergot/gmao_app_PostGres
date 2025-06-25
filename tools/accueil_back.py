from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout
from PySide6.QtGui import QFont
import sys

# Association langue <-> clavier par défaut
LANG_KEYBOARD = {
    "Français": "AZERTY",
    "Anglais": "QWERTY",
    "Allemand": "QWERTZ",
    "Espagnol": "QWERTY",
    "Italien": "QWERTY"
}

class AccueilWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Page d'accueil - Services")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()

        titre = QLabel("Bienvenue")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: #1A237E; margin-bottom: 16px;")
        layout.addWidget(titre)

        sous_titre = QLabel("Veuillez choisir un service :")
        sous_titre.setStyleSheet("color: #607d8b; margin-bottom: 24px;")
        layout.addWidget(sous_titre)

        # 1. Choix de la langue (le clavier est associé automatiquement)
        lang_layout = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Français", "Anglais", "Allemand", "Espagnol", "Italien"])
        self.lang_combo.currentTextChanged.connect(self.update_keyboard)
        lang_layout.addWidget(QLabel("Langue :"))
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addWidget(QLabel("Clavier :"))
        self.kb_label = QLabel()
        lang_layout.addWidget(self.kb_label)
        layout.addLayout(lang_layout)
        self.update_keyboard(self.lang_combo.currentText())

        layout.addSpacing(20)

        # 2. Bouton Démarrage GMAO
        self.btn_gmao = QPushButton("Démarrer la GMAO")
        self.btn_gmao.setStyleSheet("background:#3f51b5; color:white; font-size:16px; padding:10px; border-radius:8px;")
        layout.addWidget(self.btn_gmao)
        self.btn_gmao.clicked.connect(self.start_gmao)

        # 3. Bouton Démarrage Gestion des stocks
        self.btn_stock = QPushButton("Démarrer la gestion des stocks")
        self.btn_stock.setStyleSheet("background:#3f51b5; color:white; font-size:16px; padding:10px; border-radius:8px;")
        layout.addWidget(self.btn_stock)

        self.setLayout(layout)

    def update_keyboard(self, lang):
        clavier = LANG_KEYBOARD.get(lang, "QWERTY")
        self.kb_label.setText(clavier)

    def get_selected_language(self):
        return self.lang_combo.currentText()

    def start_gmao(self):
        # Cette méthode sera connectée dynamiquement par main.py
        if hasattr(self, '_on_start_gmao_callback'):
            self._on_start_gmao_callback()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccueilWindow()
    window.show()
    sys.exit(app.exec())
