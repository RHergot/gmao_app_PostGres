"""
Dialogs KPI pour les analyses spécialisées.

Ce module contient tous les dialogs modaux pour les analyses KPI spécialisées :
- MachineKPIDialog : Analyse par machine
- SiteKPIDialog : Analyse par site  
- TeamKPIDialog : Analyse par équipe
- PreventiveKPIDialog : Analyse préventif vs curatif
- AdvancedKPIDialog : Analyses avancées et prédictives
"""

from .base_kpi_dialog import BaseKPIDialog
from .machine_kpi_dialog import MachineKPIDialog
from .site_kpi_dialog import SiteKPIDialog
from .team_kpi_dialog import TeamKPIDialog
from .preventive_kpi_dialog import PreventiveKPIDialog
from .advanced_kpi_dialog import AdvancedKPIDialog

__all__ = [
    'BaseKPIDialog',
    'MachineKPIDialog',
    'SiteKPIDialog', 
    'TeamKPIDialog',
    'PreventiveKPIDialog',
    'AdvancedKPIDialog'
]
