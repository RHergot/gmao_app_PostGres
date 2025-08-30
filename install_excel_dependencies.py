#!/usr/bin/env python3
"""
Script pour installer pandas et openpyxl pour l'export Excel des KPI machines.
"""
import subprocess
import sys
import importlib.util

def check_package(package_name):
    """Vérifie si un package est installé."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """Installe un package via pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {package_name}: {e}")
        return False

def main():
    print("📦 Vérification et installation des dépendances pour l'export Excel...")
    
    packages_to_install = []
    
    # Vérifier pandas
    if not check_package("pandas"):
        print("❌ pandas n'est pas installé")
        packages_to_install.append("pandas")
    else:
        print("✅ pandas est déjà installé")
    
    # Vérifier openpyxl (pour l'export Excel)
    if not check_package("openpyxl"):
        print("❌ openpyxl n'est pas installé")
        packages_to_install.append("openpyxl")
    else:
        print("✅ openpyxl est déjà installé")
    
    if packages_to_install:
        print(f"\n🔄 Installation des packages manquants: {', '.join(packages_to_install)}")
        
        for package in packages_to_install:
            print(f"⏳ Installation de {package}...")
            if install_package(package):
                print(f"✅ {package} installé avec succès")
            else:
                print(f"❌ Échec de l'installation de {package}")
                return False
    
    print("\n🎉 Toutes les dépendances sont maintenant installées !")
    print("   L'export Excel dans machine_kpi_dialog.py devrait maintenant fonctionner.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
