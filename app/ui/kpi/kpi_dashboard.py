#!/usr/bin/env python3
"""
Dashboard principal pour les KPI financiers de la GMAO.
ATTENTION: Ce fichier a été remplacé par kpi_dashboard_clean.py

Pour utiliser le nouveau dashboard, importez depuis kpi_dashboard_clean:
from app.ui.kpi.kpi_dashboard_clean import KPIDashboard
"""

# Import du nouveau dashboard propre
from .kpi_dashboard_clean import KPIDashboard

# Alias pour compatibilité
__all__ = ['KPIDashboard']

if __name__ == "__main__":
    """Lancement du dashboard - redirigé vers la version propre."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Créer et afficher le nouveau dashboard
    dashboard = KPIDashboard()
    dashboard.show()
    dashboard.resize(1400, 900)
    
    sys.exit(app.exec())
