#!/bin/bash
# Script d'installation des dépendances pour la nouvelle interface Machine KPI

echo "🚀 Installation des dépendances pour Machine KPI Dialog v2..."

# Vérifier que pip est disponible
if ! command -v pip &> /dev/null; then
    echo "❌ pip n'est pas installé. Veuillez installer Python et pip d'abord."
    exit 1
fi

echo "📦 Installation de PySide6..."
pip install PySide6

echo "📊 Installation de pandas pour l'export Excel..."
pip install pandas openpyxl

echo "📈 Installation de matplotlib pour les graphiques (optionnel)..."
pip install matplotlib

echo "✅ Installation terminée !"
echo ""
echo "🎯 Pour tester la nouvelle interface :"
echo "   python test_machine_kpi_dialog.py"
echo ""
echo "📚 Documentation disponible dans :"
echo "   docs/MACHINE_KPI_DIALOG_V2.md"
