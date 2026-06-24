# Fichier d'initialisation pour le package app.data.repositories
# Expose les classes principales pour faciliter l'import

from .user_repository import UserRepository
from .site_repository import SiteRepository
from .fabricant_repository import FabricantRepository
from .type_machine_repository import TypeMachineRepository
from .machine_repository import MachineRepository
from .equipe_repository import EquipeRepository
from .technicien_repository import TechnicienRepository
from .ordre_travail_repository import OrdreTravailRepository
from .maintenance_repository import MaintenanceRepository
from .fournisseur_repository import FournisseurRepository
from .piece_repository import PieceRepository
from .intervention_piece_repository import InterventionPieceRepository
from .mouvement_stock_repository import MouvementStockRepository
from .gamme_entretien_repository import GammeEntretienRepository
from .gamme_etape_repository import GammeEtapeRepository
from .gamme_piece_type_repository import GammePieceTypeRepository
from .commande_repository import CommandeRepository
from .ligne_commande_repository import LigneCommandeRepository
from .compteur_repository import CompteurRepository
from .historique_compteur_repository import HistoriqueCompteurRepository

# Ajout des nouveaux repositories pour la gestion financière (Phase 11)
from .maintenance_frais_externe_repository import MaintenanceFraisExterneRepository
from .maintenance_intervenant_repository import MaintenanceIntervenantRepository

# __all__ définit ce qui est importé avec "from app.data.repositories import *"
__all__ = [
    'UserRepository',
    'SiteRepository',
    'FabricantRepository',
    'TypeMachineRepository',
    'MachineRepository',
    'EquipeRepository',
    'TechnicienRepository',
    'OrdreTravailRepository',
    'MaintenanceRepository',
    'FournisseurRepository',
    'PieceRepository',
    'InterventionPieceRepository',
    'MouvementStockRepository',
    'GammeEntretienRepository',
    'GammeEtapeRepository',
    'GammePieceTypeRepository',
    'CommandeRepository',
    'LigneCommandeRepository',
    'CompteurRepository',
    'HistoriqueCompteurRepository',
    # Ajout des repositories de la Phase 11
    'MaintenanceFraisExterneRepository',
    'MaintenanceIntervenantRepository'
]