# gmao_app/app/service_container.py
"""
Conteneur d'injection de dépendances pour l'application GMAO.
Factorise l'instanciation de tous les repositories et services (refactoring H14).

Ce module encapsule la création manuelle de 25+ dépendances actuellement
disséminée dans main.py, rendant l'injection plus lisible et maintenable.

Utilisation prévue dans main.py:
    from app.service_container import create_service_container

    container = create_service_container()
    # Accès aux services:
    container.services.user_service
    container.services.machine_service
    # etc.

NE PAS modifier main.py pour l'instant. Juste créer ce fichier pour utilisation future.
"""
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ServiceContainer:
    """
    Conteneur regroupant tous les services métier instanciés.

    Attributes:
        user_service: Service de gestion des utilisateurs.
        machine_service: Service de gestion des machines/équipements.
        maintenance_service: Service de gestion des interventions (OT, maintenance, techniciens, équipes).
        stock_service: Service de gestion des stocks et pièces.
        preventive_service: Service de maintenance préventive (gammes).
        achat_service: Service de gestion des achats et commandes.
        compteur_service: Service de gestion des compteurs machines.
        finance_service: Service de gestion financière.
    """
    user_service: Optional[object] = None
    machine_service: Optional[object] = None
    maintenance_service: Optional[object] = None
    stock_service: Optional[object] = None
    preventive_service: Optional[object] = None
    achat_service: Optional[object] = None
    compteur_service: Optional[object] = None
    finance_service: Optional[object] = None

    # Repositories (exposés pour les vues/dialogs qui en ont besoin directement)
    user_repo: Optional[object] = None
    site_repo: Optional[object] = None
    fab_repo: Optional[object] = None
    type_repo: Optional[object] = None
    machine_repo: Optional[object] = None
    equipe_repo: Optional[object] = None
    tech_repo: Optional[object] = None
    ot_repo: Optional[object] = None
    maint_repo: Optional[object] = None
    fours_repo: Optional[object] = None
    piece_repo: Optional[object] = None
    ip_repo: Optional[object] = None
    mvt_stock_repo: Optional[object] = None
    gamme_repo: Optional[object] = None
    etape_repo: Optional[object] = None
    gpt_repo: Optional[object] = None
    commande_repo: Optional[object] = None
    ligne_commande_repo: Optional[object] = None
    compteur_repo: Optional[object] = None
    historique_compteur_repo: Optional[object] = None
    maintenance_intervenant_repo: Optional[object] = None
    maintenance_frais_externe_repo: Optional[object] = None


def create_service_container() -> ServiceContainer:
    """
    Crée et configure tous les repositories et services métier.

    Cette fonction centralise l'injection de dépendances actuellement
    disséminée dans main.py (lignes ~226-370).

    Flux:
        1. Instanciation de tous les repositories
        2. Instanciation des services avec injection des repositories
        3. Résolution des dépendances circulaires (setters)
        4. Retour du conteneur complet

    Returns:
        ServiceContainer: Conteneur avec tous les services et repositories.
    """
    # Imports locaux pour éviter les imports circulaires au niveau module
    from app.data.repositories.user_repository import UserRepository
    from app.data.repositories.site_repository import SiteRepository
    from app.data.repositories.fabricant_repository import FabricantRepository
    from app.data.repositories.type_machine_repository import TypeMachineRepository
    from app.data.repositories.machine_repository import MachineRepository
    from app.data.repositories.equipe_repository import EquipeRepository
    from app.data.repositories.technicien_repository import TechnicienRepository
    from app.data.repositories.ordre_travail_repository import OrdreTravailRepository
    from app.data.repositories.maintenance_repository import MaintenanceRepository
    from app.data.repositories.fournisseur_repository import FournisseurRepository
    from app.data.repositories.piece_repository import PieceRepository
    from app.data.repositories.intervention_piece_repository import InterventionPieceRepository
    from app.data.repositories.mouvement_stock_repository import MouvementStockRepository
    from app.data.repositories.gamme_entretien_repository import GammeEntretienRepository
    from app.data.repositories.gamme_etape_repository import GammeEtapeRepository
    from app.data.repositories.gamme_piece_type_repository import GammePieceTypeRepository
    from app.data.repositories.commande_repository import CommandeRepository
    from app.data.repositories.ligne_commande_repository import LigneCommandeRepository
    from app.data.repositories.compteur_repository import CompteurRepository
    from app.data.repositories.historique_compteur_repository import HistoriqueCompteurRepository
    from app.data.repositories.maintenance_intervenant_repository import MaintenanceIntervenantRepository
    from app.data.repositories.maintenance_frais_externe_repository import MaintenanceFraisExterneRepository

    from app.core.services.machine_service import MachineService
    from app.core.services.maintenance_service import MaintenanceService
    from app.core.services.stock_service import StockService
    from app.core.services.preventive_service import PreventiveMaintenanceService
    from app.core.services.achat_service import AchatService
    from app.core.services.user_service import UserService
    from app.core.services.compteur_service import CompteurService
    from app.core.services.finance_service import FinanceService

    container = ServiceContainer()
    logger.info("--- Création du conteneur de services ---")

    # === Étape 1: Instanciation des repositories ===
    logger.debug("Instanciation des Repositories...")

    container.user_repo = UserRepository()
    container.site_repo = SiteRepository()
    container.fab_repo = FabricantRepository()
    container.type_repo = TypeMachineRepository()
    container.machine_repo = MachineRepository()
    container.equipe_repo = EquipeRepository()
    container.tech_repo = TechnicienRepository()

    container.ot_repo = OrdreTravailRepository()
    container.maint_repo = MaintenanceRepository()

    container.fours_repo = FournisseurRepository()
    container.piece_repo = PieceRepository()
    container.ip_repo = InterventionPieceRepository()
    container.mvt_stock_repo = MouvementStockRepository()

    container.gamme_repo = GammeEntretienRepository()
    container.etape_repo = GammeEtapeRepository()
    container.gpt_repo = GammePieceTypeRepository()

    container.commande_repo = CommandeRepository()
    container.ligne_commande_repo = LigneCommandeRepository()
    container.compteur_repo = CompteurRepository()
    container.historique_compteur_repo = HistoriqueCompteurRepository()

    container.maintenance_intervenant_repo = MaintenanceIntervenantRepository()
    container.maintenance_frais_externe_repo = MaintenanceFraisExterneRepository()

    logger.debug("Repositories instanciés avec succès.")

    # === Étape 2: Instanciation des services ===
    logger.debug("Instanciation des Services...")

    # Service de gestion du stock
    container.stock_service = StockService(
        piece_repository=container.piece_repo,
        fournisseur_repository=container.fours_repo,
        mouvement_stock_repository=container.mvt_stock_repo,
    )

    # Service de gestion des utilisateurs
    container.user_service = UserService(container.user_repo)

    # Service de gestion des machines
    container.machine_service = MachineService(
        machine_repository=container.machine_repo,
        site_repository=container.site_repo,
        fabricant_repository=container.fab_repo,
        type_machine_repository=container.type_repo,
    )

    # Service d'achat
    container.achat_service = AchatService(
        commande_repo=container.commande_repo,
        ligne_commande_repo=container.ligne_commande_repo,
        piece_repo=container.piece_repo,
        mouvement_stock_repo=container.mvt_stock_repo,
    )

    # --- Vérification admin initial ---
    logger.debug("Vérification de l'existence de l'admin initial...")
    container.user_service.ensure_admin_exists()

    # Service de maintenance curative
    container.maintenance_service = MaintenanceService(
        ot_repo=container.ot_repo,
        maint_repo=container.maint_repo,
        tech_repo=container.tech_repo,
        equipe_repo=container.equipe_repo,
        machine_repo=container.machine_repo,
        ip_repo=container.ip_repo,
        stock_service=container.stock_service,
        mi_repo=container.maintenance_intervenant_repo,
        mfe_repo=container.maintenance_frais_externe_repo,
    )

    # Service de maintenance préventive
    container.preventive_service = PreventiveMaintenanceService(
        gamme_repo=container.gamme_repo,
        etape_repo=container.etape_repo,
        piece_type_repo=container.gpt_repo,
        type_machine_repo=container.type_repo,
        user_repo=container.user_repo,
        piece_repo=container.piece_repo,
        ot_repo=container.ot_repo,
        machine_repo=container.machine_repo,
    )

    # Service de gestion des compteurs
    container.compteur_service = CompteurService(
        compteur_repo=container.compteur_repo,
        historique_compteur_repo=container.historique_compteur_repo,
        machine_repo=container.machine_repo,
        user_repo=container.user_repo,
        maintenance_service=container.maintenance_service,
    )

    # Service de gestion financière
    container.finance_service = FinanceService(
        maintenance_repo=container.maint_repo,
        intervenant_repo=container.maintenance_intervenant_repo,
        frais_repo=container.maintenance_frais_externe_repo,
        intervention_piece_repo=container.ip_repo,
        piece_repo=container.piece_repo,
    )

    # === Étape 3: Résolution des dépendances circulaires ===
    container.maintenance_service.set_finance_service(container.finance_service)
    container.maintenance_service.set_preventive_service(container.preventive_service)

    logger.debug("Services métier instanciés et prêts.")
    logger.info("--- Conteneur de services créé avec succès ---")

    return container
