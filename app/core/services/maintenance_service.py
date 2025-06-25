# gmao_app/app/core/services/maintenance_service.py
"""
Service métier pour la gestion des Ordres de Travail (OT) and des Maintenances.
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

# Conditional import for type checking to avoid circular dependency
if TYPE_CHECKING:
    from .preventive_service import PreventiveMaintenanceService

# Exceptions
# Correction: Ajout de MaintenanceNotFoundError à l'import
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError, MaintenanceNotFoundError

logger = logging.getLogger(__name__)

# TODO: Définir les statuts/types/priorités possibles (pourrait venir de config/DB)
OT_TYPES = ["Preventif", "Correctif", "Amelioratif", "Demande", "Reglementaire"]
OT_PRIORITES = ["Basse", "Moyenne", "Haute", "Urgente"]
OT_STATUTS_OUVERT = ["Créé", "Planifié", "AttentePieces", "Pret", "EnCours", "Suspendu"]  # Statuts considérés comme ouverts
OT_STATUTS_FERME = ["Realise", "Cloture", "Annule"]
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
        
        # ... (stocker les repos and services injectés SAUF preventive_service) ...
        logger.debug("Repositories assignés dans MaintenanceService") # Log après assignation
        self._preventive_service: Optional[PreventiveMaintenanceService] = None # Initialiser à None

        """Initialises avec les repositories nécessaires."""
        # ... (stocker les repos and services injectés) ...
        
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
        
        logger.debug("MaintenanceService initialisé avec gestion des coûts.")

    # --- Gestion Techniciens / Equipes (placé ici pour cohésion module maintenance) ---
    # Ces méthodes pourraient aussi être dans un "ResourceService" séparé.

    def get_all_techniciens(self, include_inactive: bool = False) -> List[Technicien]:
        logger.debug(f"Récupération techniciens (inactifs inclus: {include_inactive}).")
        try:
            return self._tech_repo.get_all(include_inactive=include_inactive)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_technicien_by_id(self, tech_id: int) -> Optional[Technicien]:
        logger.debug(f"Recherche technicien ID: {tech_id}")
        try:
            return self._tech_repo.get_by_id(tech_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB: {e}") from e

    def create_technicien(self, data: Dict[str, Any]) -> Technicien:
        logger.info(f"Tentative création technicien: {data.get('nom')}")
        if not data.get('nom'): raise BusinessLogicError("Nom technicien obligatoire.")
        if data.get('equipe_id') and not self._equipe_repo.get_by_id(data['equipe_id']):
            raise NotFoundError(f"Equipe ID {data['equipe_id']} non trouvée.")

        tech = Technicien(**data) # Crée l'objet depuis le dict
        try:
            new_id = self._tech_repo.add(tech)
            if not new_id: raise BusinessLogicError("Echec création technicien.")
            logger.info(f"Technicien '{tech.nom_complet}' créé ID: {new_id}.")
            created = self.get_technicien_by_id(new_id)
            if not created: raise BusinessLogicError("Créé mais non retrouvé.")
            return created
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible créer technicien: {e}") from e

    def update_technicien(self, tech_id: int, data: Dict[str, Any]) -> Technicien:
        logger.info(f"Tentative màj technicien ID: {tech_id}")
        tech = self.get_technicien_by_id(tech_id)
        if not tech: raise NotFoundError(f"Technicien ID {tech_id} non trouvé.")
        if 'nom' in data and not data.get('nom'): raise BusinessLogicError("Nom obligatoire.")
        if data.get('equipe_id') and data['equipe_id'] != tech.equipe_id:
             if data['equipe_id'] is not None and not self._equipe_repo.get_by_id(data['equipe_id']):
                  raise NotFoundError(f"Nouvelle Equipe ID {data['equipe_id']} non trouvée.")

        has_changed = False
        for key, value in data.items():
            if hasattr(tech, key) and getattr(tech, key) != value:
                # Convertir cout_horaire en float si besoin
                if key == 'cout_horaire': value = float(value or 0.0)
                setattr(tech, key, value)
                has_changed = True
        if not has_changed: return tech

        try:
            if not self._tech_repo.update(tech): raise BusinessLogicError("Echec màj.")
            logger.info(f"Technicien ID {tech_id} mis à jour.")
            updated = self.get_technicien_by_id(tech_id)
            if not updated: raise BusinessLogicError("Màj mais non retrouvé.")
            return updated
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible mettre à jour: {e}") from e

    # delete_technicien: Attention, le repo peut lever une erreur si lié à MAINTENANCE

    # --- Similaire CRUD pour Equipe ---
    def get_all_equipes(self) -> List[Equipe]:
         # Implémentation similaire à get_all_techniciens
         try: return self._equipe_repo.get_all()
         except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e
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

            # 4. Récupérer l'objet Maintenance complet créé (en dehors de la transaction)
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

    # Ajouter update/delete Maintenance si nécessaire (moins courant)

    # gmao_app/app/core/services/maintenance_service.py
    # (Dans la classe MaintenanceService)

    # --- CRUD Equipe (à ajouter) ---

    def create_equipe(self, data: Dict[str, Any]) -> Equipe:
        logger.info(f"Tentative création equipe: {data.get('nom')}")
        if not data.get('nom'): raise BusinessLogicError("Nom équipe obligatoire.")
        if data.get('responsable_id') and not self.get_technicien_by_id(data['responsable_id']):
            raise NotFoundError(f"Technicien responsable ID {data['responsable_id']} non trouvé.")

        equipe = Equipe(**data)
        try:
            new_id = self._equipe_repo.add(equipe)
            if not new_id: raise BusinessLogicError("Echec création equipe.")
            logger.info(f"Equipe '{equipe.nom}' créée ID: {new_id}.")
            created = self.get_equipe_by_id(new_id) # Doit exister
            if not created: raise BusinessLogicError("Créée mais non retrouvée.")
            return created
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible créer equipe: {e}") from e

    def get_equipe_by_id(self, eq_id: int) -> Optional[Equipe]:
        logger.debug(f"Recherche equipe ID: {eq_id}")
        try: return self._equipe_repo.get_by_id(eq_id)
        except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def update_equipe(self, eq_id: int, data: Dict[str, Any]) -> Equipe:
        logger.info(f"Tentative màj equipe ID: {eq_id}")
        eq = self.get_equipe_by_id(eq_id)
        if not eq: raise NotFoundError(f"Equipe ID {eq_id} non trouvée.")
        if 'nom' in data and not data.get('nom'): raise BusinessLogicError("Nom obligatoire.")
        if data.get('responsable_id') and data['responsable_id'] != eq.responsable_id:
            if data['responsable_id'] is not None and not self.get_technicien_by_id(data['responsable_id']):
                raise NotFoundError(f"Nouveau responsable ID {data['responsable_id']} non trouvé.")

        has_changed = False
        for key, value in data.items():
            if hasattr(eq, key) and getattr(eq, key) != value:
                setattr(eq, key, value); has_changed = True
        if not has_changed: return eq

        try:
            if not self._equipe_repo.update(eq): raise BusinessLogicError("Echec màj.")
            logger.info(f"Equipe ID {eq_id} mise à jour.")
            updated = self.get_equipe_by_id(eq_id)
            if not updated: raise BusinessLogicError("Màj mais non retrouvée.")
            return updated
        except DatabaseError as e:
            raise BusinessLogicError(f"Impossible mettre à jour equipe: {e}") from e

    def delete_equipe(self, eq_id: int) -> bool:
         logger.warning(f"Tentative suppression equipe ID: {eq_id}")
         if not self.get_equipe_by_id(eq_id): raise NotFoundError(f"Equipe ID {eq_id} non trouvée.")
         # Les techniciens liés auront leur equipe_id mis à NULL (SET NULL)
         try: return self._equipe_repo.delete(eq_id)
         except DatabaseError as e: raise BusinessLogicError(f"Impossible supprimer equipe: {e}") from e

    # --- Delete Technicien (à ajouter) ---
    def delete_technicien(self, tech_id: int) -> bool:
        """ Supprime un technicien. """
        logger.warning(f"Tentative suppression technicien ID: {tech_id}")
        if self.get_technicien_by_id(tech_id) is None:
            raise NotFoundError(f"Technicien ID {tech_id} non trouvé pour suppression.")
        # Le repo gèrera l'erreur si lié à MAINTENANCE (RESTRICT)
        try:
            success = self._tech_repo.delete(tech_id)
            if success: logger.info(f"Technicien ID {tech_id} supprimé.")
            return success
        except DatabaseError as e:
            logger.error(f"Échec DB suppression technicien ID {tech_id}: {e}")
            raise BusinessLogicError(f"Impossible de supprimer le technicien: {e}") from e
        

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
                      # Note: update_machine n'est pas fait pour màj partielle facilement ici
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
    

    def set_preventive_service(self, preventive_service: 'PreventiveMaintenanceService'):
         """ Injecte une référence au service préventif pour la màj post-maint. """
         # Utiliser 'PreventiveMaintenanceService' en string pour type hint évite import circulaire
         logger.debug("Injection de PreventiveMaintenanceService dans MaintenanceService.")
         self._preventive_service = preventive_service

    def get_intervention_pieces_by_maintenance_id(self, maintenance_id: int) -> List[InterventionPiece]:
        """Récupère toutes les pièces utilisées pour une intervention de maintenance spécifique."""
        logger.debug(f"Récupération des pièces utilisées pour la maintenance ID: {maintenance_id}")
        try:
            return self._ip_repo.get_by_maintenance_id(maintenance_id)
        except DatabaseError as e:
            raise BusinessLogicError(f"Erreur DB lors de la récupération des pièces utilisées: {e}") from e

    def _calculate_stock_adjustments(self, old_pieces: List[InterventionPiece], new_pieces_data: List[Dict[str, Any]]) -> Dict[int, Dict[str, int]]:
        """ Calcule la différence de quantité pour chaque pièce entre l'ancien and le nouvel état. """
        # Correction: utiliser piece_id and quantite (au lieu de id_piece and quantite_utilisee)
        old_qty = {p.piece_id: p.quantite for p in old_pieces}
        new_qty = {}
        for data in new_pieces_data:
            p_id, qte = None, None
            if isinstance(data, dict):
                p_id = data.get('piece_id')
                qte = data.get('quantite')
            elif isinstance(data, tuple):
                p_id = data[0] if len(data) > 0 else None
                qte = data[3] if len(data) > 3 else 1
            
            if p_id is not None and qte is not None and qte > 0:
                new_qty[p_id] = new_qty.get(p_id, 0) + qte # Agréger si même pièce ajoutée plusieurs fois
        
        adjustments = {}
        all_piece_ids = set(old_qty.keys()) | set(new_qty.keys())
        
        for p_id in all_piece_ids:
            old = old_qty.get(p_id, 0)
            new = new_qty.get(p_id, 0)
            diff = new - old
            if diff != 0:
                adjustments[p_id] = {'old': old, 'new': new, 'diff': diff}
                
        logger.debug(f"Calcul ajustements stock: {adjustments}")
        return adjustments

    def update_maintenance(self, data: Dict[str, Any]) -> Maintenance:
        """ Met à jour un rapport de maintenance existant and ajuste le stock si nécessaire. """
        logger.info(f"Tentative de mise à jour de maintenance ID: {data.get('id_maintenance')}")
        logger.debug(f"[update_maintenance] Données reçues : {data}")
        
        # --- Validations ---
        if not data.get('id_maintenance'): 
            raise BusinessLogicError("ID de maintenance obligatoire pour la mise à jour.")
        
        maint_id = data.get('id_maintenance')
        # Vérifier existence
        existing_maintenance = self.get_maintenance_by_id(maint_id)
        if not existing_maintenance:
            raise NotFoundError(f"Maintenance ID {maint_id} non trouvée.")
            
        technicien_id = data.get('technicien_id')
        if not technicien_id: 
            raise BusinessLogicError("ID Technicien obligatoire.")
        if not self._tech_repo.get_by_id(technicien_id):
            raise NotFoundError(f"Technicien ID {technicien_id} non trouvé.")
            
        ot_id = data.get('ot_id', existing_maintenance.ot_id)
        ot = self.get_ot_by_id(ot_id)
        if not ot:
            raise NotFoundError(f"OT ID {ot_id} non trouvé.")
        
        # Récupérer les pièces existantes and nouvelles
        pieces_utilisees_data = data.get("pieces_utilisees", [])
        logger.debug(f"[update_maintenance] Nouvelles pièces: {pieces_utilisees_data}")
        
        existing_pieces = self.get_intervention_pieces_by_maintenance_id(maint_id)
        logger.debug(f"[update_maintenance] Pièces existantes: {existing_pieces}")
        
        # Calculer les ajustements de stock nécessaires
        adjustments = self._calculate_stock_adjustments(existing_pieces, pieces_utilisees_data)
        logger.debug(f"[update_maintenance] Ajustements de stock à effectuer: {adjustments}")
        
        # --- Logique principale encapsulée dans une transaction ---
        try:
            # === Début de la transaction ===
            with db_cursor():
                # 1. Mettre à jour les données de maintenance
                maint_core_data = {k: v for k, v in data.items() if k != 'pieces_utilisees' and hasattr(existing_maintenance, k)}
                
                # Appliquer les modifications
                for key, value in maint_core_data.items():
                    setattr(existing_maintenance, key, value)
                
                # Sauvegarder les modifications
                self._maint_repo.update(existing_maintenance)
                logger.info(f"Données principales de maintenance {maint_id} mises à jour.")
                
                # 2. Supprimer les anciennes relations pièces-interventions
                self._ip_repo.delete_by_maintenance_id(maint_id)
                logger.info(f"Anciennes relations pièces-intervention pour maintenance {maint_id} supprimées.")
                
                # 3. Ajouter les nouvelles relations pièces-interventions and ajuster le stock
                if pieces_utilisees_data:
                    logger.info(f"Ajout de {len(pieces_utilisees_data)} nouvelles relations pièces-intervention.")
                    for piece_data in pieces_utilisees_data:
                        p_id, qte, lot = None, None, None
                        
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
                            
                        # a. Enregistrer le lien dans INTERVENTION_PIECE
                        ip_obj = InterventionPiece(maintenance_id=maint_id, piece_id=p_id, quantite=qte, lot=lot)
                        self._ip_repo.add(ip_obj)
                        
                # 4. Ajuster le stock en fonction des différences
                for p_id, adj_data in adjustments.items():
                    diff = adj_data['diff']
                    if diff != 0:
                        raison_mouvement = f"Ajustement suite à mise à jour rapport maint. ID {maint_id}"
                        type_mouvement = 'ENTREE' if diff < 0 else 'SORTIE'
                        # Pour ENTREE, diff < 0 car on a utilisé moins que prévu
                        # Pour SORTIE, diff > 0 car on a utilisé plus que prévu
                        qte_mouvement = abs(diff)
                        
                        self._stock_service.enregistrer_mouvement(
                            piece_id=p_id,
                            quantite=qte_mouvement,
                            type_mouvement=type_mouvement,
                            raison=raison_mouvement,
                            ot_id=ot.id_ot,
                            user_id=technicien_id
                        )
                        logger.info(f"Stock ajusté pour pièce ID {p_id}: {type_mouvement} de {qte_mouvement} unités.")
                        
            # === Fin de la transaction ===
            
            # Récupérer l'objet Maintenance mis à jour
            updated_maintenance = self.get_maintenance_by_id(maint_id)
            if not updated_maintenance:
                raise BusinessLogicError("Maintenance mise à jour mais non retrouvée après transaction.")
                
            logger.info(f"Mise à jour maintenance {maint_id} and ajustements de stock terminés avec succès.")
            return updated_maintenance
            
        except Exception as e:
            # Le rollback est géré automatiquement par db_cursor
            logger.error(f"Erreur lors de update_maintenance pour ID {maint_id}: {e}", exc_info=True)
            raise BusinessLogicError(f"Échec mise à jour maintenance ID {maint_id}: {e}") from e

    # --- Nouvelles méthodes pour la gestion des coûts ---

    # --- Gestion des intervenants ---
    
    def add_intervenant(self, intervenant_data: Dict[str, Any]) -> MaintenanceIntervenant:
        """Ajoute un nouvel intervenant à une maintenance."""
        logger.info(f"Ajout d'un intervenant pour maintenance ID: {intervenant_data.get('maintenance_id')}")
        
        # Validation des données
        if not intervenant_data.get('maintenance_id'):
            raise BusinessLogicError("ID de maintenance obligatoire.")
        
        maintenance_id = intervenant_data.get('maintenance_id')
        maintenance = self.get_maintenance_by_id(maintenance_id)
        if not maintenance:
            raise NotFoundError(f"Maintenance ID {maintenance_id} non trouvée.")
        
        # Validation du technicien si présent
        technicien_id = intervenant_data.get('technicien_id')
        if technicien_id and not self.get_technicien_by_id(technicien_id):
            raise NotFoundError(f"Technicien ID {technicien_id} non trouvé.")
        
        # Validation de l'intervenant externe si pas de technicien
        if not technicien_id and not intervenant_data.get('nom_intervenant_externe'):
            raise BusinessLogicError("Nom d'intervenant externe obligatoire si pas de technicien interne.")
        
        # Validation des heures and du coût
        if not intervenant_data.get('heures_travaillees') or float(intervenant_data['heures_travaillees']) <= 0:
            raise BusinessLogicError("Heures travaillées doivent être positives.")
        
        # Si technicien interne and pas de coût fourni, récupérer son coût horaire
        if technicien_id and 'cout_horaire' not in intervenant_data:
            technicien = self.get_technicien_by_id(technicien_id)
            intervenant_data['cout_horaire'] = technicien.cout_horaire
        
        # S'assurer que le coût horaire est fourni pour un intervenant externe
        if not technicien_id and not intervenant_data.get('cout_horaire'):
            raise BusinessLogicError("Coût horaire obligatoire pour un intervenant externe.")
        
        try:
            # Création de l'objet
            intervenant = MaintenanceIntervenant(
                maintenance_id=maintenance_id,
                technicien_id=technicien_id,
                nom_intervenant_externe=intervenant_data.get('nom_intervenant_externe'),
                heures_travaillees=float(intervenant_data.get('heures_travaillees')),
                cout_horaire=float(intervenant_data.get('cout_horaire', 0)),
                notes=intervenant_data.get('notes')
            )
            
            # Enregistrement en base
            new_id = self._mi_repo.add(intervenant)
            if not new_id:
                raise BusinessLogicError("Échec de l'ajout de l'intervenant.")
            
            # Récupération de l'objet créé
            created = self.get_intervenant_by_id(new_id)
            if not created:
                raise BusinessLogicError("Intervenant créé mais non retrouvé.")
                
            logger.info(f"Intervenant ID {new_id} ajouté pour maintenance {maintenance_id}.")
            return created
            
        except DatabaseError as e:
            logger.error(f"Erreur base de données lors de l'ajout d'intervenant: {e}")
            raise BusinessLogicError(f"Impossible d'ajouter l'intervenant: {e}") from e
    
    def get_intervenant_by_id(self, intervenant_id: int) -> Optional[MaintenanceIntervenant]:
        """Récupère un intervenant par son ID."""
        logger.debug(f"Récupération intervenant ID: {intervenant_id}")
        try:
            return self._mi_repo.get_by_id(intervenant_id)
        except DatabaseError as e:
            logger.error(f"Erreur base de données: {e}")
            raise BusinessLogicError(f"Erreur lors de la récupération de l'intervenant: {e}") from e
    
    def get_intervenants_by_maintenance_id(self, maintenance_id: int) -> List[MaintenanceIntervenant]:
        """Récupère tous les intervenants d'une maintenance."""
        logger.debug(f"Récupération des intervenants pour maintenance ID: {maintenance_id}")
        try:
            return self._mi_repo.get_by_maintenance_id(maintenance_id)
        except DatabaseError as e:
            logger.error(f"Erreur base de données: {e}")
            raise BusinessLogicError(f"Erreur lors de la récupération des intervenants: {e}") from e
    
    def update_intervenant(self, intervenant_id: int, data: Dict[str, Any]) -> MaintenanceIntervenant:
        """Met à jour un intervenant existant."""
        logger.info(f"Mise à jour intervenant ID: {intervenant_id}")
        
        # Récupérer l'intervenant existant
        intervenant = self.get_intervenant_by_id(intervenant_id)
        if not intervenant:
            raise NotFoundError(f"Intervenant ID {intervenant_id} non trouvé.")
        
        # Validation des données mises à jour
        if 'technicien_id' in data and data['technicien_id'] and not self.get_technicien_by_id(data['technicien_id']):
            raise NotFoundError(f"Technicien ID {data['technicien_id']} non trouvé.")
        
        # Si on change pour un intervenant externe, vérifier qu'un nom est fourni
        if 'technicien_id' in data and not data['technicien_id'] and not data.get('nom_intervenant_externe') and not intervenant.nom_intervenant_externe:
            raise BusinessLogicError("Nom d'intervenant externe obligatoire si pas de technicien interne.")
        
        # Validation des heures and du coût
        if 'heures_travaillees' in data and (not data['heures_travaillees'] or float(data['heures_travaillees']) <= 0):
            raise BusinessLogicError("Heures travaillées doivent être positives.")
        
        # Appliquer les modifications
        has_changed = False
        for key, value in data.items():
            # Ignorer maintenance_id car il ne doit pas être modifié
            if key == 'maintenance_id':
                continue
                
            if hasattr(intervenant, key) and getattr(intervenant, key) != value:
                # Conversion des types si nécessaire
                if key in ['heures_travaillees', 'cout_horaire']:
                    value = float(value)
                
                setattr(intervenant, key, value)
                has_changed = True
        
        if not has_changed:
            return intervenant
        
        try:
            # Mise à jour en base
            success = self._mi_repo.update(intervenant)
            if not success:
                raise BusinessLogicError("Échec de la mise à jour de l'intervenant.")
            
            # Récupération de l'objet mis à jour
            updated = self.get_intervenant_by_id(intervenant_id)
            if not updated:
                raise BusinessLogicError("Intervenant mis à jour mais non retrouvé.")
                
            logger.info(f"Intervenant ID {intervenant_id} mis à jour.")
            return updated
            
        except DatabaseError as e:
            logger.error(f"Erreur base de données lors de la mise à jour d'intervenant: {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour l'intervenant: {e}") from e
    
    def delete_intervenant(self, intervenant_id: int) -> bool:
        """Supprime un intervenant."""
        logger.warning(f"Suppression intervenant ID: {intervenant_id}")
        
        # Vérifier que l'intervenant existe
        if not self.get_intervenant_by_id(intervenant_id):
            raise NotFoundError(f"Intervenant ID {intervenant_id} non trouvé.")
        
        try:
            success = self._mi_repo.delete(intervenant_id)
            if success:
                logger.info(f"Intervenant ID {intervenant_id} supprimé.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur base de données lors de la suppression d'intervenant: {e}")
            raise BusinessLogicError(f"Impossible de supprimer l'intervenant: {e}") from e
    
    # --- Gestion des frais externes ---
    
    def add_frais_externe(self, frais_data: Dict[str, Any]) -> MaintenanceFraisExterne:
        """Ajoute un nouveau frais externe à une maintenance."""
        logger.info(f"Ajout d'un frais externe pour maintenance ID: {frais_data.get('maintenance_id')}")
        
        # Validation des données
        if not frais_data.get('maintenance_id'):
            raise BusinessLogicError("ID de maintenance obligatoire.")
        
        maintenance_id = frais_data.get('maintenance_id')
        maintenance = self.get_maintenance_by_id(maintenance_id)
        if not maintenance:
            raise NotFoundError(f"Maintenance ID {maintenance_id} non trouvée.")
        
        # Validation du type de frais
        type_frais = frais_data.get('type_frais')
        if not type_frais or type_frais not in VALID_TYPES_FRAIS:
            raise BusinessLogicError(f"Type de frais invalide. Valeurs autorisées: {', '.join(VALID_TYPES_FRAIS)}")
        
        # Validation du montant and de la quantité
        if not frais_data.get('montant') or float(frais_data['montant']) < 0:
            raise BusinessLogicError("Montant doit être fourni and non négatif.")
        
        if 'quantite' in frais_data and (not frais_data['quantite'] or int(frais_data['quantite']) <= 0):
            raise BusinessLogicError("Quantité doit être positive.")
        
        # Validation de la description
        if not frais_data.get('description'):
            raise BusinessLogicError("Description du frais obligatoire.")
        
        try:
            # Création de l'objet
            frais = MaintenanceFraisExterne(
                maintenance_id=maintenance_id,
                type_frais=type_frais,
                description=frais_data.get('description'),
                montant=float(frais_data.get('montant')),
                quantite=int(frais_data.get('quantite', 1)),
                reference_piece=frais_data.get('reference_piece'),
                fournisseur=frais_data.get('fournisseur'),
                facture_reference=frais_data.get('facture_reference')
            )
            
            # Enregistrement en base
            new_id = self._mfe_repo.add(frais)
            if not new_id:
                raise BusinessLogicError("Échec de l'ajout du frais externe.")
            
            # Récupération de l'objet créé
            created = self.get_frais_externe_by_id(new_id)
            if not created:
                raise BusinessLogicError("Frais externe créé mais non retrouvé.")
                
            logger.info(f"Frais externe ID {new_id} ajouté pour maintenance {maintenance_id}.")
            return created
            
        except DatabaseError as e:
            logger.error(f"Erreur base de données lors de l'ajout de frais externe: {e}")
            raise BusinessLogicError(f"Impossible d'ajouter le frais externe: {e}") from e
    
    def get_frais_externe_by_id(self, frais_id: int) -> Optional[MaintenanceFraisExterne]:
        """Récupère un frais externe par son ID."""
        logger.debug(f"Récupération frais externe ID: {frais_id}")
        try:
            return self._mfe_repo.get_by_id(frais_id)
        except DatabaseError as e:
            logger.error(f"Erreur base de données: {e}")
            raise BusinessLogicError(f"Erreur lors de la récupération du frais externe: {e}") from e
    
    def get_frais_externes_by_maintenance_id(self, maintenance_id: int) -> List[MaintenanceFraisExterne]:
        """Récupère tous les frais externes d'une maintenance."""
        logger.debug(f"Récupération des frais externes pour maintenance ID: {maintenance_id}")
        try:
            return self._mfe_repo.get_by_maintenance_id(maintenance_id)
        except DatabaseError as e:
            logger.error(f"Erreur base de données: {e}")
            raise BusinessLogicError(f"Erreur lors de la récupération des frais externes: {e}") from e
    
    def update_frais_externe(self, frais_id: int, data: Dict[str, Any]) -> MaintenanceFraisExterne:
        """Met à jour un frais externe existant."""
        logger.info(f"Mise à jour frais externe ID: {frais_id}")
        
        # Récupérer le frais existant
        frais = self.get_frais_externe_by_id(frais_id)
        if not frais:
            raise NotFoundError(f"Frais externe ID {frais_id} non trouvé.")
        
        # Validation des données mises à jour
        if 'type_frais' in data and data['type_frais'] not in VALID_TYPES_FRAIS:
            raise BusinessLogicError(f"Type de frais invalide. Valeurs autorisées: {', '.join(VALID_TYPES_FRAIS)}")
        
        if 'montant' in data and (not data['montant'] or float(data['montant']) < 0):
            raise BusinessLogicError("Montant doit être non négatif.")
        
        if 'quantite' in data  and  (not data['quantite'] or int(data['quantite']) <= 0):
            raise BusinessLogicError("Quantité doit être positive.")
        
        if 'description' in data  and  not data['description']:
            raise BusinessLogicError("Description du frais obligatoire.")
        
        # Appliquer les modifications
        has_changed = False
        for key, value in data.items():
            if hasattr(frais, key) and getattr(frais, key) != value:
                # Conversion des types si nécessaire
                if key == 'montant':
                    value = float(value)
                elif key == 'quantite':
                    value = int(value)
                
                setattr(frais, key, value)
                has_changed = True
        
        if not has_changed:
            return frais
        
        try:
            # Mise à jour en base
            success = self._mfe_repo.update(frais)
            if not success:
                raise BusinessLogicError("Échec de la mise à jour du frais externe.")
            
            # Récupération de l'objet mis à jour
            updated = self.get_frais_externe_by_id(frais_id)
            if not updated:
                raise BusinessLogicError("Frais externe mis à jour mais non retrouvé.")
                
            logger.info(f"Frais externe ID {frais_id} mis à jour.")
            return updated
            
        except DatabaseError as e:
            logger.error(f"Erreur base de données lors de la mise à jour de frais externe: {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour le frais externe: {e}") from e
    
    def delete_frais_externe(self, frais_id: int) -> bool:
        """Supprime un frais externe."""
        logger.warning(f"Suppression frais externe ID: {frais_id}")
        
        # Vérifier que le frais existe
        if not self.get_frais_externe_by_id(frais_id):
            raise NotFoundError(f"Frais externe ID {frais_id} non trouvé.")
        
        try:
            success = self._mfe_repo.delete(frais_id)
            if success:
                logger.info(f"Frais externe ID {frais_id} supprimé.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur base de données lors de la suppression de frais externe: {e}")
            raise BusinessLogicError(f"Impossible de supprimer le frais externe: {e}") from e
    
    # --- Calcul des coûts ---
    
    def calculate_maintenance_cost(self, maintenance_id: int) -> dict:
        """
        Calcule le coût total d'une maintenance selon la structure métier attendue :
        - Main d'œuvre (tous intervenants)
        - Pièces internes (stock)
        - Pièces externes (frais externes de type 'PIECE_EXTERNE')
        - Autres frais (autres frais externes)
        Retourne un dict détaillé et loggue chaque étape.
        """
        logger.info(f"Calcul du coût pour la maintenance ID: {maintenance_id}")
        if not self._mi_repo or not self._mfe_repo:
            logger.error("Repositories pour intervenants ou frais externes non initialisés.")
            raise RuntimeError("MaintenanceService non configuré pour le calcul des coûts.")

        maintenance = self._maint_repo.get_by_id(maintenance_id)
        if not maintenance:
            raise MaintenanceNotFoundError(f"Maintenance ID {maintenance_id} non trouvée pour calcul coût.")

        # Récupérer l'OT lié pour obtenir le technicien principal
        ot = self._ot_repo.get_by_id(maintenance.ot_id)
        technicien_ot_id = ot.technicien_assigne_id if ot else None
        technicien_ot = self._tech_repo.get_by_id(technicien_ot_id) if technicien_ot_id else None

        # Récupérer tous les intervenants de la maintenance
        intervenants = self._mi_repo.get_by_maintenance_id(maintenance_id)
        intervenant_ids = set()
        cout_main_oeuvre = 0.0

        # 1. Ajouter le technicien OT s'il existe et n'est pas déjà dans les intervenants
        if technicien_ot_id:
            deja_intervenant = any(i.technicien_id == technicien_ot_id for i in intervenants)
            if not deja_intervenant:
                heures = maintenance.duree_intervention_h or 0.0
                taux = technicien_ot.cout_horaire if technicien_ot and technicien_ot.cout_horaire else 0.0
                cout = heures * taux
                cout_main_oeuvre += cout
                intervenant_ids.add(technicien_ot_id)
                logger.info(f"  - MO (Technicien OT): {technicien_ot.nom_complet} | {heures:.2f}h * {taux:.2f}€/h = {cout:.2f}€")

        # 2. Ajouter tous les intervenants (internes/externes), sans doublon
        for intervenant in intervenants:
            heures = intervenant.heures_travaillees or 0.0
            if intervenant.technicien_id:
                if intervenant.technicien_id in intervenant_ids:
                    continue  # déjà compté (évite doublon)
                technicien = self._tech_repo.get_by_id(intervenant.technicien_id)
                taux = technicien.cout_horaire if technicien and technicien.cout_horaire else intervenant.cout_horaire or 0.0
                nom = technicien.nom_complet if technicien else f"Tech {intervenant.technicien_id}"
                intervenant_ids.add(intervenant.technicien_id)
            else:
                taux = intervenant.cout_horaire or 0.0
                nom = intervenant.nom_intervenant_externe or 'Externe'
            cout = heures * taux
            cout_main_oeuvre += cout
            logger.info(f"  - MO: {nom} | {heures:.2f}h * {taux:.2f}€/h = {cout:.2f}€")

        # 3. Pièces internes (stock)
        cout_pieces_internes = 0.0
        try:
            pieces = self._ip_repo.get_by_maintenance_id(maintenance_id)
            for ip in pieces:
                piece_ref = "Réf inconnue"
                try:
                    piece = self._stock_service.get_piece_by_id(ip.piece_id) if self._stock_service else None
                    if piece:
                        piece_ref = piece.reference
                        cout_unitaire = piece.prix_unitaire or 0.0
                    else:
                        cout_unitaire = ip.cout_unitaire_enregistre or 0.0
                except Exception:
                    cout_unitaire = ip.cout_unitaire_enregistre or 0.0
                cout = ip.quantite * cout_unitaire
                cout_pieces_internes += cout
                logger.info(f"  - Pièce interne: {piece_ref} | {ip.quantite} x {cout_unitaire:.2f}€ = {cout:.2f}€")
        except Exception as e:
            logger.error(f"Erreur calcul pièces internes: {e}")

        # 4. Pièces externes & autres frais (frais externes)
        cout_pieces_externes = 0.0
        cout_autres_frais = 0.0
        try:
            frais_externes = self._mfe_repo.get_by_maintenance_id(maintenance_id)
            for frais in frais_externes:
                montant = (frais.montant or 0.0) * (frais.quantite or 1)
                if getattr(frais, 'type_frais', None) == 'PIECE_EXTERNE':
                    cout_pieces_externes += montant
                    logger.info(f"  - Pièce externe: {frais.description or frais.reference_piece or ''} | {montant:.2f}€")
                else:
                    cout_autres_frais += montant
                    logger.info(f"  - Autre frais: {frais.type_frais} | {frais.description or ''} | {montant:.2f}€")
        except Exception as e:
            logger.error(f"Erreur calcul frais externes: {e}")

        cout_total = cout_main_oeuvre + cout_pieces_internes + cout_pieces_externes + cout_autres_frais
        logger.info(f"Coût total maintenance {maintenance_id}: {cout_total:.2f}€ (MO: {cout_main_oeuvre:.2f}€, Pièces internes: {cout_pieces_internes:.2f}€, Pièces externes: {cout_pieces_externes:.2f}€, Autres frais: {cout_autres_frais:.2f}€)")

        # --- Détail intervenants ---
        intervenants_items = []
        intervenant_ids = set()
        # Ajout du technicien principal OT si pas déjà dans la liste
        if technicien_ot_id and technicien_ot:
            deja_intervenant = any(i.technicien_id == technicien_ot_id for i in intervenants)
            if not deja_intervenant:
                heures = maintenance.duree_intervention_h or 0.0
                taux = technicien_ot.cout_horaire or 0.0
                intervenants_items.append({
                    'intervenant_id': f"tech_ot_{technicien_ot_id}",
                    'nom': technicien_ot.nom_complet,
                    'technicien_id': technicien_ot_id,
                    'heures': heures,
                    'cout_horaire': taux,
                    'cout_total': heures * taux
                })
                intervenant_ids.add(technicien_ot_id)
        # Ajout des autres intervenants
        for intervenant in intervenants:
            heures = intervenant.heures_travaillees or 0.0
            if intervenant.technicien_id:
                if intervenant.technicien_id in intervenant_ids:
                    continue
                technicien = self._tech_repo.get_by_id(intervenant.technicien_id)
                taux = technicien.cout_horaire if technicien and technicien.cout_horaire else intervenant.cout_horaire or 0.0
                nom = technicien.nom_complet if technicien else f"Tech {intervenant.technicien_id}"
                intervenant_ids.add(intervenant.technicien_id)
            else:
                taux = intervenant.cout_horaire or 0.0
                nom = intervenant.nom_intervenant_externe or 'Externe'
            intervenants_items.append({
                'intervenant_id': getattr(intervenant, 'id_intervenant', None),
                'nom': nom,
                'technicien_id': getattr(intervenant, 'technicien_id', None),
                'heures': heures,
                'cout_horaire': taux,
                'cout_total': heures * taux
            })
        # --- Détail frais externes ---
        frais_par_type = {}
        for frais in frais_externes:
            type_frais = getattr(frais, 'type_frais', 'AUTRE')
            if type_frais not in frais_par_type:
                frais_par_type[type_frais] = []
            montant_unitaire = frais.montant or 0.0
            quantite = frais.quantite or 1
            total = montant_unitaire * quantite
            frais_par_type[type_frais].append({
                'frais_id': getattr(frais, 'id_frais', None),
                'type_frais': type_frais,
                'description': getattr(frais, 'description', ''),
                'montant': montant_unitaire,
                'quantite': quantite,
                'total': total,
                'fournisseur': getattr(frais, 'fournisseur', ''),
                'reference_piece': getattr(frais, 'reference_piece', None)
            })
        # --- Ventilation des coûts par centre de frais (type de frais) ---
        couts_par_type = {}
        try:
            if self._mfe_repo:
                couts_par_type = self._mfe_repo.get_summary_by_maintenance(maintenance_id) or {}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé par type de frais : {e}")
            couts_par_type = {}

        # Calcul des totaux pour le résumé UI
        pieces_internes_total = cout_pieces_internes
        main_oeuvre_total = cout_main_oeuvre
        frais_externes_total = cout_pieces_externes + cout_autres_frais

        return {
            'maintenance_id': maintenance_id,
            'cout_main_oeuvre': cout_main_oeuvre,
            'cout_pieces_internes': cout_pieces_internes,
            'cout_pieces_externes': cout_pieces_externes,
            'cout_autres_frais': cout_autres_frais,
            'cout_total': cout_total,
            'detail': {
                'main_oeuvre': {
                    'items': intervenants_items,
                    'cout_total': main_oeuvre_total
                },
                'pieces_internes': {
                    'cout_total': pieces_internes_total
                },
                'frais_externes': {
                    'par_type': frais_par_type,
                    'cout_total': frais_externes_total,
                    'ventilation_centre_frais': couts_par_type
                }
            }
        }

    # ... (reste du service) ...
