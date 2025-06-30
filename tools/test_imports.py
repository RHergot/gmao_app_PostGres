#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les problèmes d'imports après la migration.
"""

import sys
import os

# Configuration du chemin pour permettre les imports depuis le répertoire parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Test des imports ===")
print(f"Répertoire courant: {os.getcwd()}")
print(f"Chemin du script: {os.path.abspath(__file__)}")
print(f"Répertoire parent ajouté au sys.path: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
print(f"sys.path: {sys.path[:3]}...")  # Affiche les 3 premiers éléments

try:
    print("\n1. Test import clean_project...")
    import clean_project
    print("✓ clean_project importé avec succès")
except Exception as e:
    print(f"✗ Erreur import clean_project: {e}")

try:
    print("\n2. Test import config...")
    import config
    print("✓ config importé avec succès")
    print(f"  DATABASE_TYPE: {config.DATABASE_TYPE}")
    print(f"  POSTGRES_HOST: {config.POSTGRES_HOST}")
except Exception as e:
    print(f"✗ Erreur import config: {e}")

try:
    print("\n3. Test import app.ui.main_window...")
    from app.ui.main_window import MainWindow
    print("✓ MainWindow importé avec succès")
except Exception as e:
    print(f"✗ Erreur import MainWindow: {e}")

try:
    print("\n4. Test import app.core.services...")
    from app.core.services.maintenance_service import MaintenanceService
    print("✓ MaintenanceService importé avec succès")
except Exception as e:
    print(f"✗ Erreur import MaintenanceService: {e}")

print("\n=== Fin des tests ===")
