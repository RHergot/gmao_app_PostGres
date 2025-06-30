# gmao_app/app/core/services/__init__.py
# Expose les classes principales pour faciliter l'import

from .user_service import UserService
from .machine_service import MachineService
from .maintenance_service import MaintenanceService
from .stock_service import StockService
from .preventive_service import PreventiveMaintenanceService
from .achat_service import AchatService
from .compteur_service import CompteurService

# Nouveau service financier (Phase 11)
from .finance_service import FinanceService

# __all__ définit ce qui est importé avec "from app.core.services import *"
__all__ = [
    'UserService',
    'MachineService',
    'MaintenanceService',
    'StockService',
    'PreventiveMaintenanceService',
    'AchatService',
    'CompteurService',
    # Nouveau service financier
    'FinanceService'
]