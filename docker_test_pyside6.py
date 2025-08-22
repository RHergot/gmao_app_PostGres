# docker_test_pyside6.py
"""
Script de test minimal pour vérifier l'environnement graphique Qt/PySide6 dans le conteneur.
Affiche un message d'erreur explicite si la fenêtre ne peut pas s'ouvrir.
"""
import sys
try:
    from PySide6.QtWidgets import QApplication, QLabel
    app = QApplication([])
    label = QLabel("Test PySide6 OK : environnement graphique Qt/X11 fonctionnel !")
    label.show()
    app.processEvents()  # Force l'initialisation graphique
    print("[INFO] Test PySide6 réussi : Qt/X11 disponible.")
    app.quit()
except Exception as e:
    print(f"[ERREUR] Test PySide6/Qt/X11 échoué : {e}", file=sys.stderr)
    sys.exit(1)
