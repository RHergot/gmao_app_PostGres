# KPI UI Module
"""
Module d'interface utilisateur pour les KPI financiers.
Contient les widgets et dialogues pour l'analyse des coûts GMAO.
"""

from .kpi_dashboard import KPIDashboard
from .widgets.machine_kpi_widget import MachineKPIWidget
from .widgets.site_kpi_widget import SiteKPIWidget
from .widgets.equipe_kpi_widget import EquipeKPIWidget
from .widgets.preventif_curatif_widget import PreventifCuratifWidget
from .widgets.global_summary_widget import GlobalSummaryWidget

__all__ = [
    'KPIDashboard',
    'MachineKPIWidget',
    'SiteKPIWidget', 
    'EquipeKPIWidget',
    'PreventifCuratifWidget',
    'GlobalSummaryWidget'
]
