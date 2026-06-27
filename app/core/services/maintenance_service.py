# gmao_app/app/core/services/maintenance_service.py
"""
Service métier pour la gestion des Ordres de Travail (OT) and des Maintenances.
Suite au refactoring H11 (God Object), les méthodes CRUD Technicien/Equipe
délèguent vers TechnicienService et EquipeService (pattern FACADE).
"""
import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING # <-- Add TYPE_CHECKING
from datetime import datetime, timedelta

# Models
from app.core.models.ordre_travail import OrdreTravail
from app.core.models.maintenance import Maintenance
from app.core.models.technicien import Technicien
from app.core.models.equipe import Equipe
from app.core.models.machine import Machine # Besoin pour infos machine
from app.core.models.intervention_piece import InterventionPiece
from app.core.models.maintenance_intervenant import MaintenanceIntervenant
from app.core.models.maintenance_frais_externe import MaintenanceFraisExterne, VALID_TYPES_FRAIS


# Repositories
from app.data.repositories import (
    OrdreTravailRepository,
    MaintenanceRepository,
    TechnicienRepository,
    EquipeRepository,
    MachineRepository, # Potentiellement nécessaire pour valider la machine
    InterventionPieceRepository, # Pour pièces/interv
    MaintenanceIntervenantRepository, # Pour intervenants
    MaintenanceFraisExterneRepository # Pour frais externes
)


# Services (on importe StockService maintenant)
from .stock_service import StockService # <-- AJOUTER CET IMPORT
from app.data.database import db_cursor # <-- AJOUTER CET IMPORT

# Services extraits (refactoring H11 - God Object Facade)
from .technicien_service import TechnicienService
from .equipe_service import EquipeService

# Conditional import for type checking to avoid circular dependency
if TYPE_CHECKING:
    from .preventive_service import PreventiveMaintenanceService

# Exceptions
# Correction: Ajout de MaintenanceNotFoundError à l'import
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError, MaintenanceNotFoundError

logger = logging.getLogger(__name__)

# TODO: Définir les statuts/types/priorités possibles (pourrait venir de config/DB)
OT_TYPES = ["Preventif", "Correctif", "Amelioratif", "Demande", "Reglementaire"]
OT_PRIORITES = ["Basse", "Normale", "Moyenne", "Haute", "Urgente"]
OT_STATUTS_OUVERT = ["Créé", "Planifié", "AttentePieces", "Pret", "EnCours", "Suspendu"]  # Statuts considérés comme ouverts
OT_STATUTS_FERME = ["Terminé", "Archivé"]  # Inclure "Archivé" dans les statuts fermés
MAINTENANCE_RESULTATS = ["OK", "OK avec reserve", "NOK", "A suivre"]


class MaintenanceService:
    def get_monthly_completed_costs_and_counts(self, months: int = 12) -> list:
        """
        Retourne une liste de dicts : [{"month": "YYYY-MM", "cost": float, "count": int}],
        pour les 12 derniers mois (hors mois en cours).
        """
        return self._maint_repo.get_monthly_completed_costs_and_counts(months)

    def get_open_ots_count(self) -> int:
        """Retourne le nombre d'OTs dont le statut est ouvert (non réalisés/clos)."""
        try:
            open_ots = self._ot_repo.get_all(filters={"statut__in": OT_STATUTS_OUVERT})
            count = len(open_ots)
            return count
        except Exception as e:
            logger.error(f"Erreur lors du comptage des OT ouverts : {e}")
            return 0

    def get_in_progress_ots_count(self) -> int:
        """Retourne le nombre d'OTs dont le statut est 'EnCours'."""
        try:
            ots = self._ot_repo.get_all(filters={"statut": "EnCours"})
            return len(ots)
        except Exception as e:
            logger.error(f"Erreur lors du comptage des OT en cours : {e}")
            return 0

    """Orchestre les opérations liées aux OT and Maintenances."""

    def create_intervention_request_ot(self, machine_id: int, description: str, urgence: int, utilisateur_createur_id: int) -> OrdreTravail:
        """
        Crée un OT à partir d'une demande d'intervention (production ou externe).
        Type = 'Demande', Statut = 'Créé', clé = OTyyyymmddHHMM
        Urgence: 0=Faible, 1=Normal, 2=Urgent
        """
        from datetime import datetime
        now = datetime.now()
        numero_ot = f"OT{now.strftime('%Y%m%d%H%M')}"
        # Mapping urgence (int) vers texte ou booléen selon modèle OT
        urgence_bool = urgence == 2  # Si la classe OT attend un booléen
        ot_data = {
            "machine_id": machine_id,
            "type": "Demande",
            "description": description,
            "utilisateur_createur_id": utilisateur_createur_id,
            "numero_ot": numero_ot,
            "date_creation": now,
            "statut": "Créé",
            "urgence": urgence_bool,
            "priorite": "Moyenne"
        }
        return self.create_ot(ot_data)

    def __init__(self,
                 ot_repo: OrdreTravailRepository,
                 maint_repo: MaintenanceRepository,
                 tech_repo: TechnicienRepository,
                 equipe_repo: EquipeRepository,
                 machine_repo: MachineRepository,
                 ip_repo: InterventionPieceRepository, # Repo pour pièces/interv
                 stock_service: StockService,           # Service stock
                 mi_repo: MaintenanceIntervenantRepository = None,  # Repo pour intervenants 
                 mfe_repo: MaintenanceFraisExterneRepository = None # Repo pour frais externes
                 ):
        """Initialise avec les repositories nécessaires."""
        self._ot_repo = ot_repo
        self._maint_repo = maint_repo
        self._tech_repo = tech_repo
        self._equipe_repo = equipe_repo
        self._machine_repo = machine_repo # Pour vérifications
        self._ip_repo = ip_repo           # Repo pour pièces/interv
        self._stock_service = stock_service # Service pour gérer le stock de pièces
        
        # Nouveaux repositories pour la gestion des coûts
        self._mi_repo = mi_repo
        self._mfe_repo = mfe_repo
        
        # Services injectés par setter après instanciation
        self._finance_service = None
        self._preventive_service = None

        # Services extraits (refactoring H11 - God Object Facade)
        self._technicien_service = TechnicienService(self._tech_repo, self._equipe_repo)
        self._equipe_service = EquipeService(self._equipe_repo, self._tech_repo)

        logger.debug("MaintenanceService initialisé avec gestion des coûts.")

    # --- Gestion Techniciens / Equipes (placé ici pour cohésion module maintenance) ---
    # Ces méthodes pourraient aussi être dans un "ResourceService" séparé.

    def get_all_techniciens(self, include_inactive: bool = False) -> List[Technicien]:
        """Délègue au TechnicienService (refactoring H11 - Facade)."""
        return self._technicien_service.get_all_techniciens(include_inactive=include_inactive)

    def get_technicien_by_id(self, tech_id: int) -> Optional[Technicien]:
        """Délègue au TechnicienService (refactoring H11 - Facade)."""
        return self._technicien_service.get_technicien_by_id(tech_id)

    def create_technicien(self, data: Dict[str, Any]) -> Technicien:
        """Délègue au TechnicienService (refactoring H11 - Facade)."""
        return self._technicien_service.create_technicien(data)

    def update_technicien(self, tech_id: int, data: Dict[str, Any]) -> Technicien:
        """Délègue au TechnicienService (refactoring H11 - Facade)."""
        return self._technicien_service.update_technicien(tech_id, data)

    # delete_technicien: Attention, le repo peut lever une erreur si lié à MAINTENANCE

    # --- Similaire CRUD pour Equipe ---
    def get_all_equipes(self) -> List[Equipe]:
        """Délègue au EquipeService (refactoring H11 - Facade)."""
        return self._equipe_service.get_all_equipes()
    # ... Ajouter create/update/delete Equipe si nécessaire ...


    # --- Gestion des Ordres de Travail (OT) ---

    def create_ot(self, data: Dict[str, Any]) -> OrdreTravail:
        """ Crée un nouvel OT (souvent correctif or demande initiale). """
        logger.info(f"Tentative création OT pour machine ID: {data.get('machine_id')}")
        # Validations essentielles
        if not data.get('machine_id'): raise BusinessLogicError("ID Machine obligatoire.")
        if not data.get('type'): raise BusinessLogicError("Type d'OT obligatoire.")
        if data['type'] not in OT_TYPES: raise BusinessLogicError(f"Type OT invalide: {data['type']}.")
        if not data.get('description'): raise BusinessLogicError("Description obligatoire.")
        if not data.get('utilisateur_createur_id'): raise BusinessLogicError("ID Utilisateur créateur obligatoire.")
        # Valider l'existence de la machine
        machine = self._machine_repo.get_by_id(data['machine_id'])
        if not machine: raise NotFoundError(f"Machine ID {data['machine_id']} non trouvée.")
        # TODO: Valider existence createur, technicien assigné, gamme si fournis

        # Logique spécifique? Ex: Générer numero_ot automatique
        if not data.get('numero_ot'):
            # Format simple : OT-YYYYMMDD-ID (mais ID pas encore connu)
            # Mieux : le générer après insertion or séquence DB si supporté
            data['numero_ot'] = f"OT-{datetime.now().strftime('%Y%m%d%H%M%S')}" # Simple numéro temporaire unique

        # Définir statut initial
        data['statut'] = data.get('statut', "Créé")
        if data['statut'] not in OT_STATUTS_OUVERT + OT_STATUTS_FERME:
             raise BusinessLogicError(f"Statut OT invalide: {data['statut']}.")

        # Préparer l'objet modèle
        ot_data = OrdreTravail(
            machine_id=data['machine_id'],
            type=data['type'],
            description=data['description'],
            utilisateur_createur_id=data['utilisateur_createur_id'],
            numero_ot=data.get('numero_ot'),
            gamme_id=data.get('gamme_id'),
            # date_creation géré par défaut mais peut être surchargé
            date_creation=data.get('date_creation', datetime.now()),
            date_prevue=data.get('date_prevue'), # Attendu comme datetime or None
            duree_prevue_min=data.get('duree_prevue_min'),
            priorite=data.get('priorite', 'Moyenne'),
            urgence=data.get('urgence', False),
            statut=data['statut'],
            technicien_assigne_id=data.get('technicien_assigne_id'),
            notes_planification=data.get('notes_planification')
        )

        try:
            new_id = self._ot_repo.add(ot_data)
            if not new_id: raise BusinessLogicError("Echec création OT.")
            logger.info(f"OT ID {new_id} créé ({ot_data.type}).")
            created = self.get_ot_by_id(new_id)
            if not created: raise BusinessLogicError("OT créé mais non retrouvé.")
            # Logique post-création? Mettre à jour état machine? (Plutôt lors de la réalisation)
            if created.type == "Correctif" and created.urgence:
                # Si OT correctif urgent, changer état machine?
                if machine.etat != "En panne":  # Évite màj inutile
                    logger.info(f"Mise à jour état machine {machine.id_machine} à 'En panne' suite à OT urgent {new_id}")
                    # Correction : on modifie l'objet existant puis on le met à jour
                    machine_modifie = Machine(
                        nom=machine.nom,
                        type_machine_id=machine.type_machine_id,
                        site_id=machine.site_id,
                        fabricant_id=machine.fabricant_id,
                        serial=machine.serial,
                        modele=machine.modele,
                        date_installation=machine.date_installation,
                        localisation=machine.localisation,
                        etat="En panne",
                        informations_techniques=machine.informations_techniques,
                        parent_machine_id=machine.parent_machine_id,
                        criticite=machine.criticite,
                        garantie_fin=machine.garantie_fin,
                        id_machine=machine.id_machine,
                        created_at=machine.created_at,
                        updated_at=machine.updated_at
                    )
                    self._machine_repo.update(machine_modifie)
                    # ou : machine.etat = "En panne"; self._machine_repo.update(machine) # Mais màj tous les champs

            return created
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible de créer l'OT: {e}") from e

    def get_ot_by_id(self, ot_id: int) -> Optional[OrdreTravail]:
        logger.debug(f"Recherche OT ID: {ot_id}")
        try:
            ot = self._ot_repo.get_by_id(ot_id)
            if not ot: logger.warning(f"OT ID {ot_id} non trouvé.")
            return ot
        except DatabaseError as e:
             raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_all_ots(self, filters: Optional[Dict[str, Any]] = None,
                     sort_by: str = "date_prevue", sort_desc: bool = False) -> List[OrdreTravail]:
        logger.debug(f"Récupération OTs (filters={filters}, sort={sort_by}).")
        try:
            return self._ot_repo.get_all(filters=filters, sort_by=sort_by, sort_desc=sort_desc)
        except DatabaseError as e:
             raise BusinessLogicError(f"Erreur DB: {e}") from e

    def update_ot(self, ot_id: int, data: Dict[str, Any]) -> OrdreTravail:
        logger.info(f"Tentative màj OT ID: {ot_id}")
        ot = self.get_ot_by_id(ot_id)
        if not ot: raise NotFoundError(f"OT ID {ot_id} non trouvé.")

        # Validations si des champs clés sont modifiés
        if 'machine_id' in data and data['machine_id'] != ot.machine_id:
            if not self._machine_repo.get_by_id(data['machine_id']): raise NotFoundError(f"Nouvelle Machine ID {data['machine_id']} non trouvée.")
        if 'technicien_assigne_id' in data and data['technicien_assigne_id'] != ot.technicien_assigne_id:
             if data['technicien_assigne_id'] is not None and not self._tech_repo.get_by_id(data['technicien_assigne_id']): raise NotFoundError(f"Nouveau Technicien ID {data['technicien_assigne_id']} non trouvé.")
        if 'type' in data and data['type'] != ot.type:
             if data['type'] not in OT_TYPES: raise BusinessLogicError(f"Type OT invalide: {data['type']}.")
        if 'statut' in data and data['statut'] != ot.statut:
            if data['statut'] not in OT_STATUTS_OUVERT + OT_STATUTS_FERME: raise BusinessLogicError(f"Statut OT invalide: {data['statut']}.")
            # Logique de transition de statut? Ex: on ne peut pas repasser de Cloturé à EnCours?

        # Appliquer modifications
        has_changed = False
        for key, value in data.items():
             if hasattr(ot, key) and getattr(ot, key) != value:
                  # Gérer booléen urgence
                  if key == 'urgence': value = bool(value)
                  setattr(ot, key, value)
                  has_changed = True
        if not has_changed: return ot

        try:
            if not self._ot_repo.update(ot): raise BusinessLogicError("Echec màj OT.")
            logger.info(f"OT ID {ot_id} mis à jour.")
            updated = self.get_ot_by_id(ot_id)
            if not updated: raise BusinessLogicError("OT màj mais non retrouvé.")
            return updated
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible màj OT: {e}") from e

    def delete_ot(self, ot_id: int) -> bool:
        logger.warning(f"Tentative suppression OT ID: {ot_id}")
        if not self.get_ot_by_id(ot_id): raise NotFoundError(f"OT ID {ot_id} non trouvé.")
        # La suppression de l'OT va supprimer la Maintenance liée (CASCADE)
        try:
            return self._ot_repo.delete(ot_id)
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible supprimer OT: {e}") from e


    # --- Gestion de la Réalisation (Maintenance) ---

    def record_maintenance(self, data: Dict[str, Any]) -> Maintenance:
        """ Enregistre une intervention de maintenance réalisée pour un OT. """
        logger.info(f"Tentative enregistrement maintenance pour OT ID: {data.get('ot_id')}")
        logger.debug(f"[record_maintenance] Données reçues : {data}")
        # --- Validations (inchangées) ---
        if not data.get('ot_id'): raise BusinessLogicError("ID OT obligatoire.")
        technicien_id = data.get('technicien_id')
        if not technicien_id: raise BusinessLogicError("ID Technicien obligatoire.")
        # ... (autres validations: dates, travaux, resultat, type_reel) ...
        ot = self.get_ot_by_id(data['ot_id'])
        if not ot: raise NotFoundError(f"OT ID {data['ot_id']} non trouvé.")
        if ot.statut in OT_STATUTS_FERME: raise BusinessLogicError(f"OT {ot.id_ot} déjà '{ot.statut}'.")
        # Vérifier le technicien APRÈS avoir récupéré son ID
        if not self._tech_repo.get_by_id(technicien_id): raise NotFoundError(f"Tech ID {technicien_id} non trouvé.")

        # Récupérer la liste des pièces
        pieces_utilisees_data = data.get("pieces_utilisees", []) # Liste de dicts
        logger.debug(f"[record_maintenance] pieces_utilisees_data : {pieces_utilisees_data}")

        # --- Logique principale encapsulée dans une transaction --- 
        created_maintenance = None
        new_maint_id = None # Défini ici pour être accessible dans le except
        try:
            # === Début de la transaction ===
            with db_cursor():
                # 1. Créer l'enregistrement Maintenance
                maint_core_data = {k: v for k, v in data.items() if k != 'pieces_utilisees'}
                maint_obj = Maintenance(**maint_core_data)
                new_maint_id = self._maint_repo.add(maint_obj)
                logger.debug(f"[record_maintenance] new_maint_id obtenu : {new_maint_id}")
                if not new_maint_id: raise BusinessLogicError("Echec création enregistrement Maintenance.")
                logger.info(f"Maintenance ID {new_maint_id} enregistrée pour OT {ot.id_ot}.")

                # 2. Enregistrer les pièces utilisées and décrémenter le stock
                if pieces_utilisees_data:
                    logger.info(f"Enregistrement de {len(pieces_utilisees_data)} type(s) de pièce(s) utilisée(s).")
                    for piece_data in pieces_utilisees_data:
                        logger.debug(f"[record_maintenance] Traitement pièce utilisée : {piece_data}")
                        # Support tuple or dict
                        if isinstance(piece_data, dict):
                            p_id = piece_data.get('piece_id')
                            qte = piece_data.get('quantite')
                            lot = piece_data.get('lot')
                        elif isinstance(piece_data, tuple):
                            p_id = piece_data[0] if len(piece_data) > 0 else None
                            # tuple may be (id, ref, nom) or (id, ref, nom, qte, lot)
                            qte = piece_data[3] if len(piece_data) > 3 else 1
                            lot = piece_data[4] if len(piece_data) > 4 else None
                        else:
                            logger.warning(f"Format inattendu pour pièce utilisée: {piece_data}")
                            continue

                        if p_id is None or qte is None or qte <= 0:
                             logger.warning(f"Donnée pièce utilisée invalide ignorée: {piece_data}")
                             continue

                        # a. Enregistrer le lien dans INTERVENTION_PIECE
                        ip_obj = InterventionPiece(maintenance_id=new_maint_id, piece_id=p_id, quantite=qte, lot=lot)
                        self._ip_repo.add(ip_obj)

                        # b. Décrémenter le stock via StockService.enregistrer_mouvement
                        raison_mvt = f"Utilisation OT {ot.id_ot}"
                        mvt_enregistre = self._stock_service.enregistrer_mouvement(
                            piece_id=p_id,
                            quantite=qte,
                            type_mouvement='SORTIE',
                            raison=raison_mvt,
                            ot_id=ot.id_ot,
                            user_id=technicien_id
                        )
                        logger.info(f"Mouvement de sortie enregistré pour Pièce ID {p_id} (Qt: {qte}).")

                # 3. Mettre à jour statut OT -> "Realise"
                self.update_ot_status(ot.id_ot, "Realise")

            # === Fin de la transaction (Commit implicite par db_cursor) ===

            # 4. Recalculer et mettre à jour les coûts financiers
            self.recalculer_et_maj_couts(new_maint_id)

            # 5. Récupérer l'objet Maintenance complet créé (en dehors de la transaction)
            created_maintenance = self.get_maintenance_by_id(new_maint_id)
            logger.debug(f"[record_maintenance] created_maintenance récupéré : {created_maintenance}")
            if not created_maintenance: raise BusinessLogicError("Maintenance créée mais non retrouvée après transaction.")
            logger.info(f"Enregistrement maintenance {new_maint_id} and MàJ stock/OT terminés avec succès.")
            return created_maintenance

        except Exception as e:
             # --- Gestion d'erreur / Rollback --- 
             # Le rollback est géré automatiquement par db_cursor si l'exception survient dans le bloc 'with'
             logger.error(f"Erreur majeure lors de record_maintenance pour OT {data.get('ot_id')}: {e}", exc_info=True)
             # Remonter l'exception
             raise BusinessLogicError(f"Echec enregistrement maintenance pour OT {data.get('ot_id')}: {e}") from e

    def get_maintenance_by_id(self, maint_id: int) -> Optional[Maintenance]:
        logger.debug(f"Recherche maintenance ID: {maint_id}")
        try: return self._maint_repo.get_by_id(maint_id)
        except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_maintenance_for_ot(self, ot_id: int) -> Optional[Maintenance]:
         logger.debug(f"Recherche maintenance pour OT ID: {ot_id}")
         try: return self._maint_repo.get_by_ot_id(ot_id)
         except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_intervention_pieces_by_maintenance_id(self, maintenance_id: int) -> List[InterventionPiece]:
        """
        Récupère toutes les pièces utilisées pour une maintenance donnée.
        """
        logger.debug(f"Recherche intervention pieces pour maintenance ID: {maintenance_id}")
        try:
            return self._ip_repo.get_by_maintenance_id(maintenance_id)
        except DatabaseError as e:
            logger.error(f"Erreur récupération intervention pieces pour maintenance {maintenance_id}: {e}")
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def calculate_maintenance_cost(self, maintenance_id: int) -> dict:
        """
        Calcule les coûts d'une maintenance en déléguant au FinanceService.
        Méthode de compatibilité pour les widgets qui l'utilisent.
        """
        logger.debug(f"Calcul des coûts pour maintenance ID: {maintenance_id}")
        
        if not self._finance_service:
            raise BusinessLogicError("FinanceService non injecté dans MaintenanceService. Vérifiez l'initialisation.")
        
        try:
            # Utiliser la méthode qui retourne le format détaillé pour le widget
            return self._finance_service.get_detailed_costs_for_widget(maintenance_id)
        except Exception as e:
            logger.error(f"Erreur calcul coûts maintenance {maintenance_id}: {e}")
            raise BusinessLogicError(f"Erreur calcul coûts: {e}") from e

    def update_maintenance(self, data: Dict[str, Any]) -> Maintenance:
        """
        Met à jour une maintenance existante.
        """
        maintenance_id = data.get('id_maintenance')
        if not maintenance_id:
            raise BusinessLogicError("ID maintenance obligatoire pour la mise à jour.")
        
        logger.info(f"Tentative mise à jour maintenance ID: {maintenance_id}")
        
        # Récupérer la maintenance existante
        existing_maintenance = self.get_maintenance_by_id(maintenance_id)
        if not existing_maintenance:
            raise NotFoundError(f"Maintenance ID {maintenance_id} non trouvée.")
        
        # Validations similaires à record_maintenance
        if data.get('technicien_id') and not self._tech_repo.get_by_id(data['technicien_id']):
            raise NotFoundError(f"Technicien ID {data['technicien_id']} non trouvé.")
        
        # Récupérer les pièces utilisées
        pieces_utilisees_data = data.get("pieces_utilisees", [])
        
        try:
            with db_cursor():
                # 1. Mettre à jour les données de base de la maintenance
                maintenance_data = {k: v for k, v in data.items() if k not in ['pieces_utilisees', 'id_maintenance']}
                
                # Appliquer les modifications à l'objet existant
                for key, value in maintenance_data.items():
                    if hasattr(existing_maintenance, key):
                        setattr(existing_maintenance, key, value)
                
                # Sauvegarder la maintenance
                if not self._maint_repo.update(existing_maintenance):
                    raise BusinessLogicError("Échec mise à jour maintenance.")
                
                # 2. Gérer les pièces utilisées - Supprimer les anciennes et ajouter les nouvelles
                # Supprimer les anciennes liaisons intervention_piece
                try:
                    # Récupérer les anciennes pièces pour restaurer le stock
                    old_pieces = self._ip_repo.get_by_maintenance_id(maintenance_id)
                    
                    # Restaurer le stock des anciennes pièces
                    for old_piece in old_pieces:
                        raison_restauration = f"Restauration stock - Modification OT {existing_maintenance.ot_id}"
                        self._stock_service.enregistrer_mouvement(
                            piece_id=old_piece.piece_id,
                            quantite=old_piece.quantite,
                            type_mouvement='ENTREE',
                            raison=raison_restauration,
                            ot_id=existing_maintenance.ot_id,
                            user_id=data.get('technicien_id', 1)
                        )
                    
                    # Supprimer les anciennes liaisons
                    self._ip_repo.delete_by_maintenance_id(maintenance_id)
                    
                except Exception as e:
                    logger.warning(f"Erreur lors de la restauration du stock pour maintenance {maintenance_id}: {e}")
                
                # 3. Ajouter les nouvelles pièces
                if pieces_utilisees_data:
                    logger.info(f"Mise à jour de {len(pieces_utilisees_data)} type(s) de pièce(s) utilisée(s).")
                    for piece_data in pieces_utilisees_data:
                        # Support tuple or dict
                        if isinstance(piece_data, dict):
                            p_id = piece_data.get('piece_id')
                            qte = piece_data.get('quantite')
                            lot = piece_data.get('lot')
                        elif isinstance(piece_data, tuple):
                            p_id = piece_data[0] if len(piece_data) > 0 else None
                            qte = piece_data[3] if len(piece_data) > 3 else 1
                            lot = piece_data[4] if len(piece_data) > 4 else None
                        else:
                            logger.warning(f"Format inattendu pour pièce utilisée: {piece_data}")
                            continue

                        if p_id is None or qte is None or qte <= 0:
                            logger.warning(f"Donnée pièce utilisée invalide ignorée: {piece_data}")
                            continue

                        # Ajouter la nouvelle liaison
                        ip_obj = InterventionPiece(maintenance_id=maintenance_id, piece_id=p_id, quantite=qte, lot=lot)
                        self._ip_repo.add(ip_obj)

                        # Décrémenter le stock
                        raison_mvt = f"Utilisation OT {existing_maintenance.ot_id} (modification)"
                        self._stock_service.enregistrer_mouvement(
                            piece_id=p_id,
                            quantite=qte,
                            type_mouvement='SORTIE',
                            raison=raison_mvt,
                            ot_id=existing_maintenance.ot_id,
                            user_id=data.get('technicien_id', 1)
                        )
                        logger.info(f"Mouvement de sortie enregistré pour Pièce ID {p_id} (Qt: {qte}).")
            
            # 4. Recalculer les coûts financiers
            if hasattr(self, 'recalculer_et_maj_couts'):
                self.recalculer_et_maj_couts(maintenance_id)
            
            # 5. Récupérer la maintenance mise à jour
            updated_maintenance = self.get_maintenance_by_id(maintenance_id)
            if not updated_maintenance:
                raise BusinessLogicError("Maintenance mise à jour mais non retrouvée.")
            
            logger.info(f"Maintenance {maintenance_id} mise à jour avec succès.")
            return updated_maintenance
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour maintenance {maintenance_id}: {e}", exc_info=True)
            raise BusinessLogicError(f"Échec mise à jour maintenance {maintenance_id}: {e}") from e

    def recalculer_et_maj_couts(self, maintenance_id: int):
        """
        Recalcule et met à jour les coûts financiers d'une maintenance.
        """
        logger.debug(f"Recalcul des coûts pour maintenance ID: {maintenance_id}")
        
        if not self._finance_service:
            raise RuntimeError(
                "FinanceService non injecté dans MaintenanceService. "
                "Appelez set_finance_service() avant d'utiliser recalculer_et_maj_couts()."
            )
        
        try:
            # Déléguer au FinanceService pour recalculer les coûts
            self._finance_service.recalculer_couts_maintenance(maintenance_id)
            logger.info(f"Coûts recalculés pour maintenance {maintenance_id}")
        except Exception as e:
            logger.error(f"Erreur lors du recalcul des coûts pour maintenance {maintenance_id}: {e}")
            # Ne pas faire échouer la transaction pour une erreur de calcul de coûts
    
    # Ajouter update/delete Maintenance si nécessaire (moins courant)

    # gmao_app/app/core/services/maintenance_service.py
    # (Dans la classe MaintenanceService)

    # --- CRUD Equipe (à ajouter) ---

    def create_equipe(self, data: Dict[str, Any]) -> Equipe:
        """Délègue au EquipeService (refactoring H11 - Facade)."""
        return self._equipe_service.create_equipe(data)

    def get_equipe_by_id(self, eq_id: int) -> Optional[Equipe]:
        """Délègue au EquipeService (refactoring H11 - Facade)."""
        return self._equipe_service.get_equipe_by_id(eq_id)

    def update_equipe(self, eq_id: int, data: Dict[str, Any]) -> Equipe:
        """Délègue au EquipeService (refactoring H11 - Facade)."""
        return self._equipe_service.update_equipe(eq_id, data)

    def delete_equipe(self, eq_id: int) -> bool:
        """Délègue au EquipeService (refactoring H11 - Facade)."""
        return self._equipe_service.delete_equipe(eq_id)

    # --- Delete Technicien (à ajouter) ---
    def delete_technicien(self, tech_id: int) -> bool:
        """Délègue au TechnicienService (refactoring H11 - Facade)."""
        return self._technicien_service.delete_technicien(tech_id)
        

    # gmao_app/app/core/services/maintenance_service.py
# (À l'intérieur de la classe MaintenanceService)

    # ... (après les autres méthodes comme delete_ot, or avant record_maintenance)

    def update_ot_status(self, ot_id: int, new_status: str) -> OrdreTravail:
        """ Met à jour uniquement le statut d'un OT après validation de la transition. """
        logger.info(f"Tentative changement statut OT ID {ot_id} -> {new_status}")

        # 1. Récupérer l'OT pour vérifications
        ot = self.get_ot_by_id(ot_id) # Utilise la méthode existante
        if not ot:
            raise NotFoundError(f"OT ID {ot_id} non trouvé pour changement de statut.")

        # 2. Valider la transition de statut (Exemple simple, à affiner)
        current_status = ot.statut
        valid_transitions = {
            "Créé": ["Planifié", "Pret", "EnCours", "Annule"],
            "Planifié": ["Pret", "EnCours", "Annule"],
            "AttentePieces": ["Pret", "Annule"],
            "Pret": ["EnCours", "Annule"],
            "EnCours": ["Suspendu", "Realise", "Annule"], # Realise se fait via record_maintenance
            "Suspendu": ["EnCours", "Annule"],
        }

        if new_status not in (OT_STATUTS_OUVERT + OT_STATUTS_FERME):
             raise BusinessLogicError(f"Nouveau statut invalide fourni: {new_status}")

        allowed_next_statuses = valid_transitions.get(current_status, [])
        # Cas spécial: le passage à 'Realise' est géré par record_maintenance
        if new_status == "Realise" and current_status != "EnCours":
             # On pourrait vouloir forcer le passage par record_maintenance
             pass # Pour l'instant, on laisse update_ot le gérer si appelé directement

        if new_status != current_status and new_status not in allowed_next_statuses :
            # Permettre de réappliquer le même statut n'est pas une erreur
            logger.warning(f"Transition de statut invalide de '{current_status}' vers '{new_status}' pour OT {ot_id}.")
            raise BusinessLogicError(f"Transition de statut non autorisée de '{current_status}' vers '{new_status}'.")

        # Si la transition est valide (ou statut inchangé), mettre à jour l'OT
        # Note: On utilise update_ot qui gère déjà la màj partielle and la sauvegarde
    
        # C'est moins direct mais réutilise le code existant.
        # Alternative: Avoir une méthode dédiée dans le repo pour juste màj le statut.
        update_data = {"statut": new_status}
        updated_ot = self.update_ot(ot_id, update_data)

        # 4. Logique post-changement de statut (machine state, etc.)
        try:
            # S'assurer qu'updated_ot est bien l'objet mis à jour
            if not updated_ot: # Si update_ot a retourné None or erreur
                 raise BusinessLogicError("Erreur interne lors de la mise à jour de l'OT pour le statut.")

            if new_status == "EnCours":
                 machine = self._machine_repo.get_by_id(updated_ot.machine_id)
                 if machine and machine.etat not in ["En maintenance", "En panne"]:
                      logger.info(f"Màj état machine {machine.id_machine} -> 'En maintenance'")
                      # Note: update_machine n'est pas fait pour màd partielle facilement ici
                      # Faudrait adapter MachineService or MachineRepository
                      # Pour l'instant, on fait la màj complète (pas idéal)
                      machine.etat = "En maintenance"
                      self._machine_repo.update(machine) # Pas update_machine du service! Appel direct repo ici

            elif new_status in ["Annule", "Realise", "Cloture"]:
                 # Attention: "Realise" and "Cloture" sont normalement mis par record_maintenance,
                 # mais on garde la logique ici au cas où update_ot_status est appelé directement.
                 machine = self._machine_repo.get_by_id(updated_ot.machine_id)
                 if machine and machine.etat == "En maintenance":
                     logger.info(f"Màj état machine {machine.id_machine} -> 'En service'")
                     machine.etat = "En service"
                     self._machine_repo.update(machine) # Idem: appel direct repo

        except Exception as e:
             logger.error(f"Erreur (non bloquante) maj état machine suite à statut OT {ot_id}: {e}")

        return updated_ot # Renvoyer l'OT mis à jour

    # --- Méthodes d'injection de dépendances ---
    
    def set_finance_service(self, finance_service):
        """
        Injecte le service financier pour résoudre les dépendances circulaires.
        Cette méthode doit être appelée après l'instanciation.
        """
        self._finance_service = finance_service
        logger.debug("Service financier injecté dans MaintenanceService.")
    
    def set_preventive_service(self, preventive_service):
        """
        Injecte le service de maintenance préventive pour résoudre les dépendances circulaires.
        Cette méthode doit être appelée après l'instanciation.
        """
        self._preventive_service = preventive_service
        logger.debug("Service de maintenance préventive injecté dans MaintenanceService.")
    
    # --- Méthodes d'archivage ---
    
    def archive_ot(self, ot_id: int, user_id: int) -> OrdreTravail:
        """
        Archive un OT manuellement.
        Seuls les OT avec statut "Terminé" peuvent être archivés.
        """
        logger.info(f"Tentative d'archivage manuel OT ID {ot_id} par utilisateur {user_id}")
        
        # Récupérer l'OT pour vérifications
        ot = self.get_ot_by_id(ot_id)
        if not ot:
            raise NotFoundError(f"OT ID {ot_id} non trouvé pour archivage.")
        
        # Vérifier que l'OT peut être archivé
        if ot.statut != "Terminé":
            raise BusinessLogicError(f"Impossible d'archiver un OT avec le statut '{ot.statut}'. Seuls les OT 'Terminé' peuvent être archivés.")
        
        # Archiver l'OT via fonction PostgreSQL
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT archive_ot(%s, %s)", (ot_id, user_id))
                result = cursor.fetchone()
                # Gérer à la fois les tuples et les dictionnaires
                if hasattr(result, 'keys'):
                    # C'est un dictionnaire (RealDictCursor)
                    success = result.get('archive_ot', False) or list(result.values())[0] if result else False
                else:
                    # C'est un tuple
                    success = result[0] if result else False
                    
                if not success:
                    raise DatabaseError("Échec de l'archivage via la fonction PostgreSQL")
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'archivage OT {ot_id}: {e}")
            raise DatabaseError(f"Erreur d'archivage: {e}")
        
        # Retourner l'OT mis à jour
        return self.get_ot_by_id(ot_id)
    
    def unarchive_ot(self, ot_id: int, user_id: int) -> OrdreTravail:
        """
        Désarchive un OT (le remet au statut "Terminé").
        """
        logger.info(f"Tentative de désarchivage OT ID {ot_id} par utilisateur {user_id}")
        
        # Vérifier que l'OT existe et est archivé
        ot = self.get_ot_by_id(ot_id)
        if not ot:
            raise NotFoundError(f"OT ID {ot_id} non trouvé pour désarchivage.")
        
        if ot.statut != "Archivé":
            raise BusinessLogicError(f"L'OT n'est pas archivé (statut actuel: '{ot.statut}').")
        
        # Désarchiver via fonction PostgreSQL
        try:
            with db_cursor() as cursor:
                cursor.execute("SELECT unarchive_ot(%s, %s)", (ot_id, user_id))
                result = cursor.fetchone()
                # Gérer à la fois les tuples et les dictionnaires
                if hasattr(result, 'keys'):
                    # C'est un dictionnaire (RealDictCursor)
                    success = result.get('unarchive_ot', False) or list(result.values())[0] if result else False
                else:
                    # C'est un tuple
                    success = result[0] if result else False
                    
                if not success:
                    raise DatabaseError("Échec du désarchivage via la fonction PostgreSQL")
                    
        except Exception as e:
            logger.error(f"Erreur lors du désarchivage OT {ot_id}: {e}")
            raise DatabaseError(f"Erreur de désarchivage: {e}")
        
        # Retourner l'OT mis à jour
        return self.get_ot_by_id(ot_id)
    
    def get_archive_statistics(self) -> dict:
        """
        Retourne des statistiques sur les archives.
        """
        try:
            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE statut = 'Archivé') as archives_count,
                        COUNT(*) FILTER (WHERE statut = 'Terminé' AND date_creation::timestamp < CURRENT_DATE - INTERVAL '6 months') as archivable_count,
                        COUNT(*) FILTER (WHERE statut NOT IN ('Archivé')) as actifs_count
                    FROM ordre_travail
                """)
                result = cursor.fetchone()
                if hasattr(result, 'keys'):
                    # C'est un dictionnaire (RealDictCursor)
                    return {
                        'archives_count': result.get('archives_count', 0) or 0,
                        'archivable_count': result.get('archivable_count', 0) or 0,
                        'actifs_count': result.get('actifs_count', 0) or 0
                    }
                else:
                    # C'est un tuple
                    return {
                        'archives_count': result[0] or 0,
                        'archivable_count': result[1] or 0,
                        'actifs_count': result[2] or 0
                    }
        except Exception as e:
            logger.error(f"Erreur récupération statistiques archives: {e}")
            return {'archives_count': 0, 'archivable_count': 0, 'actifs_count': 0}
