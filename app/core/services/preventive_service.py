# gmao_app/app/core/services/preventive_service.py
"""
Service métier pour la gestion de la Maintenance Préventive (Gammes).
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# Models
from app.core.models.gamme_entretien import GammeEntretien, VALID_PERIODICITE_UNITES
from app.core.models.gamme_etape import GammeEtape
from app.core.models.gamme_piece_type import GammePieceType
from app.core.models.ordre_travail import OrdreTravail

# Repositories
from app.data.repositories import (
    GammeEntretienRepository,
    GammeEtapeRepository,
    GammePieceTypeRepository,
    # Besoin d'autres repos pour validation FK ou logique future
    TypeMachineRepository,
    UserRepository,
    PieceRepository,
    OrdreTravailRepository,
    MachineRepository
)

# Exceptions
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class PreventiveMaintenanceService:
    """ Orchestre les opérations liées aux gammes de maintenance préventive. """

    def __init__(self,
                 gamme_repo: GammeEntretienRepository,
                 etape_repo: GammeEtapeRepository,
                 piece_type_repo: GammePieceTypeRepository,
                 # Ajouter autres repos si validation nécessaire
                 type_machine_repo: TypeMachineRepository,
                 user_repo: UserRepository,
                 piece_repo: PieceRepository,
                 ot_repo: OrdreTravailRepository,
                 machine_repo: MachineRepository
                ):
        self._gamme_repo = gamme_repo
        self._etape_repo = etape_repo
        self._piece_type_repo = piece_type_repo
        self._type_machine_repo = type_machine_repo
        self._user_repo = user_repo
        self._piece_repo = piece_repo
        self._ot_repo = ot_repo
        self._machine_repo = machine_repo
        logger.debug("PreventiveMaintenanceService initialisé.")


    # --- CRUD GammeEntretien ---

    def create_gamme(self, data: Dict[str, Any], createur_id: int) -> GammeEntretien:
        """ Crée une nouvelle gamme de maintenance. """
        logger.info(f"Tentative création gamme: {data.get('description')}")
        # Validations
        if not data.get('description'): raise BusinessLogicError("Description gamme obligatoire.")
        p_unit = data.get('periodicite_unite')
        if p_unit and p_unit not in VALID_PERIODICITE_UNITES: raise BusinessLogicError(f"Unité périodicité invalide: {p_unit}")
        p_val = data.get('periodicite_valeur')
        if p_unit and (p_val is None or p_val <= 0): raise BusinessLogicError("Valeur périodicité positive requise si unité définie.")
        # Valider type_machine_id si fourni
        tm_id = data.get('type_machine_id')
        if tm_id and not self._type_machine_repo.get_by_id(tm_id): raise NotFoundError(f"Type Machine ID {tm_id} non trouvé.")
        # Valider createur_id
        if not self._user_repo.get_by_id(createur_id): raise NotFoundError(f"Utilisateur créateur ID {createur_id} non trouvé.")
        # TODO: Valider createur_id, priorite, type_entretien

        # Calculer prochaine date si possible et si non fournie
        prochaine_date = data.get('prochaine_date_calculee')
        if not prochaine_date and data.get('date_derniere_realisation') and p_unit and p_val:
             # On pourrait instancier temporairement pour appeler la méthode de calcul
             temp_gamme = GammeEntretien(description="temp", # Juste pour le calcul
                                         date_derniere_realisation=data['date_derniere_realisation'],
                                         periodicite_valeur=p_val,
                                         periodicite_unite=p_unit)
             prochaine_date = temp_gamme.calculate_next_due_date()

        gamme = GammeEntretien(
            description=data['description'],
            type_entretien=data.get('type_entretien', "Préventif Systématique"),
            periodicite_valeur=p_val,
            periodicite_unite=p_unit,
            instructions=data.get('instructions'),
            date_derniere_realisation=data.get('date_derniere_realisation'),
            prochaine_date_calculee=prochaine_date, # Calculée ou fournie
            active=data.get('active', True),
            type_machine_id=tm_id,
            createur_id=createur_id, # ID utilisateur logué
            duree_estimee_min=data.get('duree_estimee_min'),
            qualification_requise=data.get('qualification_requise'),
            priorite=data.get('priorite', "Moyenne")
        )
        try:
            new_id = self._gamme_repo.add(gamme)
            if not new_id: raise BusinessLogicError("Echec création gamme.")
            logger.info(f"Gamme '{gamme.description}' créée ID: {new_id}.")
            created = self.get_gamme_by_id(new_id)
            if not created: raise BusinessLogicError("Créée mais non retrouvée.")
            return created
        except DatabaseError as e: raise BusinessLogicError(f"Impossible créer: {e}") from e

    def get_gamme_by_id(self, gamme_id: int) -> Optional[GammeEntretien]:
        logger.debug(f"Recherche gamme ID: {gamme_id}")
        try: return self._gamme_repo.get_by_id(gamme_id)
        except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_all_gammes(self, active_only: bool = True) -> List[GammeEntretien]:
        logger.debug(f"Récupération gammes (active_only={active_only}).")
        try: return self._gamme_repo.get_all(active_only=active_only)
        except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def update_gamme(self, gamme_id: int, data: Dict[str, Any]) -> GammeEntretien:
        logger.info(f"Tentative màj gamme ID: {gamme_id}")
        gamme = self.get_gamme_by_id(gamme_id)
        if not gamme: raise NotFoundError(f"Gamme ID {gamme_id} non trouvée.")

        # Validations (similaires à create)
        if 'description' in data and not data.get('description'): raise BusinessLogicError("Desc. obligatoire.")
        # ... autres validations ...

        # Recalculer prochaine date si périodicité ou dernière date change
        recalculate_next = False
        if 'date_derniere_realisation' in data and data['date_derniere_realisation'] != gamme.date_derniere_realisation: recalculate_next = True
        if 'periodicite_valeur' in data and data['periodicite_valeur'] != gamme.periodicite_valeur: recalculate_next = True
        if 'periodicite_unite' in data and data['periodicite_unite'] != gamme.periodicite_unite: recalculate_next = True

        # Appliquer changements
        has_changed = False
        for key, value in data.items():
             # Ignorer 'prochaine_date_calculee' des données d'entrée, on la recalcule
             if key == 'prochaine_date_calculee': continue
             if hasattr(gamme, key) and getattr(gamme, key) != value:
                  # TODO: Gérer conversion dates si elles arrivent en string
                  setattr(gamme, key, value); has_changed = True

        if recalculate_next:
            new_next_date = gamme.calculate_next_due_date()
            if new_next_date != gamme.prochaine_date_calculee:
                gamme.prochaine_date_calculee = new_next_date
                has_changed = True # S'assurer que has_changed est True

        if not has_changed: return gamme

        try:
            if not self._gamme_repo.update(gamme): raise BusinessLogicError("Echec màj.")
            logger.info(f"Gamme ID {gamme_id} mise à jour.")
            updated = self.get_gamme_by_id(gamme_id) # Recharger
            if not updated: raise BusinessLogicError("Màj mais non retrouvée.")
            return updated
        except DatabaseError as e: raise BusinessLogicError(f"Impossible mettre à jour: {e}") from e

    def delete_gamme(self, gamme_id: int) -> bool:
         logger.warning(f"Tentative suppression gamme ID: {gamme_id}")
         if not self.get_gamme_by_id(gamme_id): raise NotFoundError(f"ID {gamme_id} non trouvé.")
         # Le repo supprime en cascade les étapes/pièces liées
         try: return self._gamme_repo.delete(gamme_id)
         except DatabaseError as e: raise BusinessLogicError(f"Impossible supprimer: {e}") from e


    # --- Gestion GammeEtape ---
    def get_etapes_for_gamme(self, gamme_id: int) -> List[GammeEtape]:
         logger.debug(f"Récupération étapes pour gamme ID: {gamme_id}")
         try: return self._etape_repo.get_by_gamme_id(gamme_id)
         except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def save_etapes_for_gamme(self, gamme_id: int, etapes_data: List[Dict[str, Any]]):
        """ Met à jour TOUTES les étapes pour une gamme (supprime anciennes, ajoute nouvelles). """
        logger.info(f"Sauvegarde des étapes pour Gamme ID {gamme_id}")
        if not self.get_gamme_by_id(gamme_id): raise NotFoundError(f"Gamme ID {gamme_id} non trouvée.")
        # TODO: Gérer dans une transaction DB !
        try:
            # 1. Supprimer les étapes existantes
            nb_deleted = self._etape_repo.delete_by_gamme_id(gamme_id)
            logger.debug(f"{nb_deleted} étapes existantes supprimées pour gamme {gamme_id}.")
            # 2. Ajouter les nouvelles étapes (valider ordre et description?)
            ordre_counter = 1
            for etape_data in etapes_data:
                 if not etape_data.get('description'): continue # Ignorer étapes sans description
                 etape = GammeEtape(
                     gamme_id=gamme_id,
                     description=etape_data['description'],
                     ordre=etape_data.get('ordre', ordre_counter), # Utiliser ordre fourni ou compteur
                     instructions_detaillees=etape_data.get('instructions_detaillees'),
                     duree_estimee_min=etape_data.get('duree_estimee_min')
                 )
                 self._etape_repo.add(etape)
                 ordre_counter += 1
            logger.info(f"{ordre_counter - 1} nouvelles étapes ajoutées pour gamme {gamme_id}.")
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la sauvegarde des étapes pour gamme {gamme_id}: {e}")
            # Ici un rollback serait nécessaire si on était dans une transaction
            raise BusinessLogicError(f"Erreur sauvegarde étapes: {e}") from e


    # --- Gestion GammePieceType ---
    def get_pieces_type_for_gamme(self, gamme_id: int) -> List[Dict[str, Any]]:
         """ Récupère les pièces (avec détails) liées à une gamme. """
         logger.debug(f"Récupération pièces type pour gamme ID: {gamme_id}")
         try: return self._piece_type_repo.get_pieces_details_by_gamme_id(gamme_id)
         except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def save_pieces_type_for_gamme(self, gamme_id: int, pieces_data: List[Dict[str, Any]]):
         """ Met à jour TOUTES les pièces types pour une gamme. """
         logger.info(f"Sauvegarde pièces type pour Gamme ID {gamme_id}")
         if not self.get_gamme_by_id(gamme_id): raise NotFoundError(f"Gamme ID {gamme_id} non trouvée.")
         # TODO: Gérer dans une transaction DB !
         try:
             # 1. Supprimer les liens existants
             nb_deleted = self._piece_type_repo.delete_by_gamme_id(gamme_id)
             logger.debug(f"{nb_deleted} liens pièce type existants supprimés pour gamme {gamme_id}.")
             # 2. Ajouter les nouveaux liens
             added_count = 0
             for piece_data in pieces_data:
                  p_id = piece_data.get('piece_id')
                  qte = int(piece_data.get('quantite_theorique', 1) or 1)
                  if p_id is None or qte <= 0: continue
                  # Valider que la pièce existe?
                  if not self._piece_repo.get_by_id(p_id):
                       logger.warning(f"Pièce ID {p_id} non trouvée, ignorée pour gamme {gamme_id}.")
                       continue
                  gpt = GammePieceType(gamme_id=gamme_id, piece_id=p_id, quantite_theorique=qte)
                  try:
                       self._piece_type_repo.add(gpt)
                       added_count += 1
                  except DatabaseError as e_add: # Ex: contrainte unique violée
                       logger.warning(f"Impossible d'ajouter pièce ID {p_id} à gamme {gamme_id}: {e_add}")

             logger.info(f"{added_count} nouveaux liens pièce type ajoutés pour gamme {gamme_id}.")
         except DatabaseError as e:
             logger.error(f"Erreur DB lors de la sauvegarde pièces type pour gamme {gamme_id}: {e}")
             raise BusinessLogicError(f"Erreur sauvegarde pièces: {e}") from e

    # --- Logique de Génération OT Préventif (Base) ---
    # Cette méthode pourrait être appelée périodiquement par un scheduler, ou manuellement
    def generate_preventive_ots(self, due_date: Optional[date] = None) -> List[OrdreTravail]:
        """
        Génère les OT préventifs pour les gammes échues.
        Si due_date n'est pas fournie, utilise la date du jour.
        Retourne la liste des OT créés.
        """
        target_date = due_date if due_date else date.today()
        logger.info(f"Recherche des gammes préventives échues au {target_date}...")
        ots_created: List[OrdreTravail] = []

        try:
            # Récupérer les gammes basées sur date/périodicité (excluant Heures/Cycles ici)
            # Le repo utilise prochaine_date_calculee, il faut s'assurer qu'elle est à jour.
            # Une approche plus robuste est de recalculer ici ou d'appeler une méthode repo plus intelligente.
            # Alternative: Utiliser la méthode repo simple pour l'instant
            gammes_due = self._gamme_repo.get_active_gammes_due(target_date)
            logger.info(f"{len(gammes_due)} gammes basées sur date échues trouvées.")

            # TODO: Gérer les gammes basées sur compteurs (Heures, Cycles)
            # Nécessiterait de lire les valeurs actuelles des compteurs des machines liées
            # et de les comparer aux seuils/intervalles définis dans la gamme (non modélisé encore)

            for gamme in gammes_due:
                # Pour chaque gamme échue, trouver les machines concernées
                machines_to_process: List[Machine] = []
                if gamme.type_machine_id:
                    # TODO: Récupérer les machines de ce type (via MachineService/Repo)
                    # machines_to_process = self._machine_repo.get_all(filters={'type_machine_id': gamme.type_machine_id, 'actif': True?})
                    logger.warning(f"Génération OT pour Gamme {gamme.id_gamme} liée à Type Machine {gamme.type_machine_id} NON IMPLEMENTEE.")
                    continue # Passer à la suivante
                # else: # Si la gamme est liée à une machine spécifique (non modélisé actuellement)
                #     machine = self._machine_repo.get_by_id(gamme.machine_id_directe) # Si lien direct
                #     if machine: machines_to_process.append(machine)
                else:
                    logger.warning(f"Gamme {gamme.id_gamme} non liée à un Type Machine, génération OT ignorée.")
                    continue

                # Check if machines were found for THIS gamme (moved inside the loop)
                if not machines_to_process:
                    logger.info(f"Aucune machine trouvée pour la gamme {gamme.id_gamme} (après tentatives de récupération).")
                    # Continue to the next gamme if no machines were found
                    continue # This is now correctly inside the 'for gamme' loop

                # Process each machine found for the current gamme (moved inside the loop)
                for machine in machines_to_process:
                    # Vérifier si un OT préventif Ouvert existe déjà pour cette Gamme/Machine
                    existing_ots = self._ot_repo.get_all(filters={
                        'machine_id': machine.id_machine,
                        'gamme_id': gamme.id_gamme,
                        'statut__in': OT_STATUTS_OUVERT # Adapter repo pour gérer __in
                    })
                    if existing_ots:
                        logger.info(f"OT préventif ouvert existe déjà pour Gamme {gamme.id_gamme} / Machine {machine.id_machine}. Création ignorée.")
                        continue # This continue skips to the next machine in the inner loop

                    # Créer les données pour le nouvel OT
                    ot_data = {
                        "machine_id": machine.id_machine,
                        "gamme_id": gamme.id_gamme,
                        "type": gamme.type_entretien or "Preventif",
                        "description": f"Préventif: {gamme.description} - {machine.nom}",
                        "priorite": gamme.priorite or "Moyenne",
                        "duree_prevue_min": gamme.duree_estimee_min,
                        "statut": "Planifié", # Ou "Pret" si on a les pièces?
                        "utilisateur_createur_id": 0 # ID Système? Ou passer ID User qui lance génération?
                    }
                    try:
                        # Utiliser MaintenanceService pour créer l'OT? Ou appel direct repo?
                        # Appelons une méthode create_ot qui existe déjà (on suppose qu'elle gère createur_id)
                        # Mais create_ot est dans MaintenanceService... -> Dépendance circulaire?
                        # Mieux: Garder create_ot dans MaintenanceService et l'appeler ici.
                        # --> Il faut injecter MaintenanceService dans PreventiveMaintenanceService
                        # ---> Pour éviter dépendance circulaire, on peut créer l'OT via repo direct ici
                        # ----> Solution temporaire: créer via repo direct
                        temp_ot = OrdreTravail(**ot_data)
                        new_ot_id = self._ot_repo.add(temp_ot) # Utilisation directe repo ot
                        if new_ot_id:
                            created_ot = self._ot_repo.get_by_id(new_ot_id)
                            if created_ot: ots_created.append(created_ot)
                            logger.info(f"OT Préventif ID {new_ot_id} créé pour Gamme {gamme.id_gamme} / Machine {machine.id_machine}")

                        # TODO: Recalculer et stocker la *vraie* prochaine date gamme APRES génération?
                        # Pas ici, plutôt après clôture maintenance.
                    except Exception as e_create:
                        logger.error(f"Erreur création OT pour Gamme {gamme.id_gamme} / Machine {machine.id_machine}: {e_create}")

            logger.info(f"Génération OT préventifs terminée. {len(ots_created)} OTs créés.")
            return ots_created

        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la génération des OT préventifs: {e}")
            raise BusinessLogicError("Erreur lors de la recherche des gammes échues.") from e

    # --- Logique de Mise à Jour Gamme après Maintenance ---
    def update_gamme_post_maintenance(self, maintenance_id: int):
        """ Met à jour date dernière réalisation/prochaine date gamme après clôture maint. """
        logger.info(f"Tentative màj gamme suite à clôture Maintenance ID {maintenance_id}")
        try:
             maint = self._maint_repo.get_by_id(maintenance_id)
             if not maint: raise NotFoundError(f"Maintenance ID {maintenance_id} non trouvée.")

             ot = self._ot_repo.get_by_id(maint.ot_id)
             if not ot: raise NotFoundError(f"OT ID {maint.ot_id} lié à maintenance {maintenance_id} non trouvé.")

             # Vérifier si l'OT vient d'une gamme
             if ot.gamme_id is None:
                  logger.debug(f"OT {ot.id_ot} n'est pas lié à une gamme. Pas de màj gamme.")
                  return

             gamme = self.get_gamme_by_id(ot.gamme_id)
             if not gamme:
                  logger.error(f"Gamme ID {ot.gamme_id} liée à OT {ot.id_ot} non trouvée !")
                  return # Problème de données

             # Mettre à jour la date de dernière réalisation
             last_date = maint.date_fin_reelle.date() # Utiliser date de fin réelle
             gamme.date_derniere_realisation = last_date

             # Recalculer la prochaine date
             gamme.prochaine_date_calculee = gamme.calculate_next_due_date()
             logger.debug(f"Recalcul prochaine date pour gamme {gamme.id_gamme}: {gamme.prochaine_date_calculee}")

             # Sauvegarder la gamme mise à jour
             self._gamme_repo.update(gamme) # Appelle l'update du repo

             logger.info(f"Gamme ID {gamme.id_gamme} mise à jour suite à Maintenance ID {maintenance_id}.")

        except (NotFoundError, BusinessLogicError, DatabaseError) as e:
             logger.error(f"Erreur lors de la màj gamme post-maintenance {maintenance_id}: {e}")
             # Ne pas bloquer l'enregistrement de la maintenance si la màj gamme échoue? Logguer suffit.
        except Exception as e:
             logger.exception(f"Erreur inattendue màj gamme post-maintenance {maintenance_id}: {e}")