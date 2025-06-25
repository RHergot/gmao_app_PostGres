from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QHBoxLayout
from PySide6.QtGui import QFont
import sys
import os

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
        self.resize(900, 600)  # Largeur x Hauteur
        self.setMinimumSize(900, 600)
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
        self.btn_stock.clicked.connect(self.start_stock)

        # 3. Bouton Démarrage Gestion des achats
        self.btn_purchase = QPushButton("Démarrer les Achats")
        self.btn_purchase.setStyleSheet("background:#3f51b5; color:white; font-size:16px; padding:10px; border-radius:8px;")
        layout.addWidget(self.btn_purchase)
        self.btn_purchase.clicked.connect(self.start_purchase)

        # Séparateur visuel avant le bouton Exit
        layout.addSpacing(30)
        layout.addStretch()
        # 4. Bouton Exit pour fermer la session
        self.btn_exit = QPushButton("Quitter la session")
        self.btn_exit.setStyleSheet("background:#d32f2f; color:white; font-size:16px; padding:10px; border-radius:8px;")
        layout.addWidget(self.btn_exit)
        self.btn_exit.clicked.connect(QApplication.quit)

        self.setLayout(layout)
        # Centrer la fenêtre à l'écran
        self.center_on_screen()


    def center_on_screen(self):
        # Centre la fenêtre sur l'écran principal
        screen = self.screen() if hasattr(self, 'screen') else None
        if screen is None:
            # Compatibilité PyQt5/PySide6
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        x = geometry.x() + (geometry.width() - self.width()) // 2
        y = geometry.y() + (geometry.height() - self.height()) // 2
        self.move(x, y)

    def update_keyboard(self, lang):
        clavier = LANG_KEYBOARD.get(lang, "QWERTY")
        self.kb_label.setText(clavier)

    def get_selected_language(self):
        return self.lang_combo.currentText()

    def _start_application(self, app_name, base_path, main_script_path, python_exe_name="python"):
        import subprocess
        from PySide6.QtWidgets import QMessageBox
        lang = self.get_selected_language()

        # Sur Windows, l'exécutable est python.exe, même si on demande python3
        if sys.platform == "win32":
            python_exe_name = "python.exe"

        # Construction de chemins relatifs et multi-plateformes
        # Le script doit être lancé depuis le répertoire parent (ex: G:/Mon Drive/Projets)
        python_executable_path = os.path.join(base_path, ".venv", "Scripts" if sys.platform == "win32" else "bin", python_exe_name)
        main_script_full_path = os.path.join(base_path, main_script_path)

        command = [python_executable_path, main_script_full_path, "--lang", lang]
        
        kwargs = {}
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            kwargs['creationflags'] = DETACHED_PROCESS
        else:
            kwargs['preexec_fn'] = os.setsid

        try:
            # On vérifie que le CWD est correct pour que les chemins relatifs fonctionnent
            if not os.path.isdir(base_path):
                 QMessageBox.warning(self, "Attention", f"Le répertoire '{base_path}' n'a pas été trouvé. Veuillez lancer ce script depuis le répertoire contenant les applications (ex: 'Projets').")
                 return

            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        except FileNotFoundError:
             QMessageBox.critical(self, "Erreur de chemin", f"Impossible de trouver un fichier nécessaire pour lancer {app_name}.\nVérifiez que l'application est correctement installée et que vous lancez le programme depuis le bon répertoire.\nChemin Python: {python_executable_path}\nChemin Script: {main_script_full_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur inattendue est survenue en lançant {app_name} : {e}")

    def start_gmao(self):
        # Lance l'application GMAO dans un nouveau processus
        self._start_application(
            app_name="la GMAO",
            base_path="G:\Mon Drive\Projets\gmao_app_PostGres",
            main_script_path="main.py"
        )

    def start_stock(self):
        # Lance l'application Gestion de stock dans un nouveau processus
        self._start_application(
            app_name="la gestion de stock",
            base_path="Gestion_Stock_app_Postgres",
            main_script_path=os.path.join("APP", "main.py")
        )

    def start_purchase(self):
        # Lance l'application Achats dans un nouveau processus
        self._start_application(
            app_name="les Achats",
            base_path="Purchasing_desk",
            main_script_path="main.py",
            python_exe_name="python3"
        )



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccueilWindow()
    window.show()
    sys.exit(app.exec())
