@echo off
title Machine KPI Dialog - Test Interface

echo.
echo ==========================================
echo    Machine KPI Dialog - Version 2.0
echo ==========================================
echo.
echo 🏭 Interface modernisée pour l'analyse KPI
echo 📊 Cartes visuelles et graphiques intégrés
echo 🔍 Filtres avancés et recherche
echo 📤 Export multiple (Excel, CSV)
echo.

REM Changer vers le répertoire du projet
cd /d "%~dp0"

echo 🚀 Lancement de l'interface de test...
echo.

python test_machine_kpi_dialog.py

if errorlevel 1 (
    echo.
    echo ❌ Erreur lors du lancement !
    echo.
    echo 🔧 Solutions possibles :
    echo    1. Installer les dépendances : install_machine_kpi_deps.bat
    echo    2. Vérifier Python est installé : python --version
    echo    3. Vérifier PySide6 : pip show PySide6
    echo.
    pause
) else (
    echo.
    echo ✅ Interface fermée avec succès
)

pause
