@echo off
REM Script d'installation des dépendances pour la nouvelle interface Machine KPI (Windows)

echo 🚀 Installation des dépendances pour Machine KPI Dialog v2...

REM Vérifier que pip est disponible
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip n'est pas installé. Veuillez installer Python et pip d'abord.
    pause
    exit /b 1
)

echo 📦 Installation de PySide6...
pip install PySide6

echo 📊 Installation de pandas pour l'export Excel...
pip install pandas openpyxl

echo 📈 Installation de matplotlib pour les graphiques (optionnel)...
pip install matplotlib

echo ✅ Installation terminée !
echo.
echo 🎯 Pour tester la nouvelle interface :
echo    python test_machine_kpi_dialog.py
echo.
echo 📚 Documentation disponible dans :
echo    docs/MACHINE_KPI_DIALOG_V2.md

pause
