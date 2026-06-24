# gmao_app/app/core/services/machine_service.py
"""
Service métier pour la gestion des équipements (Machines, Sites, Fabricants, Types).
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import date

# Import des modèles
from app.core.models.machine import Machine
from app.core.models.site import Site
from app.core.models.fabricant import Fabricant
from app.core.models.type_machine import TypeMachine

# Import des repositories
from app.data.repositories import ( # Utilise l'import depuis __init__.py
    MachineRepository,
    SiteRepository,
    FabricantRepository,
    TypeMachineRepository
)

# Import des exceptions personnalisées
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class MachineService:
    """Orchestre les opérations liées aux équipements."""

    def __init__(self,
                 machine_repository: MachineRepository,
                 site_repository: SiteRepository,
                 fabricant_repository: FabricantRepository,
                 type_machine_repository: TypeMachineRepository):
        """Initialise le service avec les repositories nécessaires."""
        self._machine_repo = machine_repository
        self._site_repo = site_repository
        self._fab_repo = fabricant_repository
        self._type_repo = type_machine_repository
        logger.debug("MachineService initialisé avec ses repositories.")

    # --- Méthodes pour les entités de référence (Sites, Fabricants, Types) ---
    # Ces méthodes sont souvent nécessaires pour peupler les listes déroulantes dans l'UI

    def get_all_sites(self) -> List[Site]:
        logger.debug("Récupération de tous les sites.")
        try:
            return self._site_repo.get_all()
        except DatabaseError as e:
            logger.error(f"Erreur DB récupération tous sites: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    def get_all_fabricants(self) -> List[Fabricant]:
        logger.debug("Récupération de tous les fabricants.")
        try:
            return self._fab_repo.get_all()
        except DatabaseError as e:
            logger.error(f"Erreur DB récupération tous fabricants: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    def get_all_type_machines(self) -> List[TypeMachine]:
        logger.debug("Récupération de tous les types de machine.")
        try:
            return self._type_repo.get_all()
        except DatabaseError as e:
            logger.error(f"Erreur DB récupération tous types machine: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e
        
    
# gmao_app/app/core/services/machine_service.py
# (Dans la classe MachineService)

    # --- CRUD pour Site ---

    def create_site(self, data: Dict[str, Any]) -> Site:
        """ Crée un nouveau site. """
        logger.info(f"Tentative création site: {data.get('nom')}")
        if not data.get('nom'):
            raise BusinessLogicError("Le nom du site est obligatoire.")

        # Créer l'objet modèle
        site_data = Site(
            nom=data['nom'],
            adresse=data.get('adresse'),
            ville=data.get('ville'),
            pays=data.get('pays'),
            contact_principal=data.get('contact_principal')
        )
        try:
            new_id = self._site_repo.add(site_data)
            if new_id is None: raise BusinessLogicError("Échec création site.")
            logger.info(f"Site '{site_data.nom}' créé ID: {new_id}.")
            created_site = self.get_site_by_id(new_id) # Pour avoir l'objet complet
            if not created_site: raise BusinessLogicError("Site créé mais non retrouvé.")
            return created_site
        except DatabaseError as e:
            logger.error(f"Échec DB création site: {e}")
            raise BusinessLogicError(f"Impossible de créer le site: {e}") from e

    def get_site_by_id(self, site_id: int) -> Optional[Site]:
        """ Récupère un site par ID. """
        logger.debug(f"Recherche site ID: {site_id}")
        try:
            return self._site_repo.get_by_id(site_id)
        except DatabaseError as e:
            logger.error(f"Erreur DB get site ID {site_id}: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    # get_all_sites existe déjà

    def update_site(self, site_id: int, update_data: Dict[str, Any]) -> Site:
        """ Met à jour un site existant. """
        logger.info(f"Tentative màj site ID: {site_id}")
        site = self.get_site_by_id(site_id)
        if site is None:
            raise NotFoundError(f"Site ID {site_id} non trouvé pour màj.")

        # Validation nom obligatoire
        if 'nom' in update_data and not update_data.get('nom'):
             raise BusinessLogicError("Le nom du site ne peut pas être vide.")

        # Appliquer les modifications
        has_changed = False
        for key, value in update_data.items():
            if hasattr(site, key) and getattr(site, key) != value:
                setattr(site, key, value)
                has_changed = True
                logger.debug(f"Site ID {site_id}: Champ '{key}' modifié.")

        if not has_changed: return site

        try:
            success = self._site_repo.update(site)
            if not success: raise BusinessLogicError("Échec màj site (non trouvé?).")
            logger.info(f"Site ID {site_id} mis à jour.")
            updated_site = self.get_site_by_id(site_id) # Recharger
            if not updated_site: raise BusinessLogicError("Site màj mais non retrouvé.")
            return updated_site
        except DatabaseError as e:
            logger.error(f"Échec DB màj site ID {site_id}: {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour le site: {e}") from e

    def delete_site(self, site_id: int) -> bool:
        """ Supprime un site. """
        logger.warning(f"Tentative suppression site ID: {site_id}")
        if self.get_site_by_id(site_id) is None:
            raise NotFoundError(f"Site ID {site_id} non trouvé pour suppression.")
        # Le repo gèrera l'erreur si des machines sont liées (ON DELETE RESTRICT)
        try:
            success = self._site_repo.delete(site_id)
            if success: logger.info(f"Site ID {site_id} supprimé.")
            return success
        except DatabaseError as e:
             logger.error(f"Échec DB suppression site ID {site_id}: {e}")
             raise BusinessLogicError(f"Impossible de supprimer le site: {e}") from e # Erreur métier claire

    # On pourrait ajouter ici des méthodes CRUD complètes pour Site/Fabricant/Type
    # si l'application doit permettre de les gérer via une interface dédiée.
    # Pour l'instant, on suppose qu'ils sont gérés autrement ou via des CRUD simples.
    # Exemple:
    # def create_site(self, nom: str, ...) -> Site: ...
    # def update_site(self, site_id: int, data: dict) -> Site: ...
    # def delete_site(self, site_id: int) -> bool: ...
    # gmao_app/app/core/services/machine_service.py
    # (Dans la classe MachineService)

    # --- CRUD pour Fabricant ---

    def create_fabricant(self, data: Dict[str, Any]) -> Fabricant:
        """ Crée un nouveau fabricant. """
        logger.info(f"Tentative création fabricant: {data.get('nom')}")
        if not data.get('nom'):
            raise BusinessLogicError("Le nom du fabricant est obligatoire.")

        fab_data = Fabricant(
            nom=data['nom'],
            contact=data.get('contact'),
            site_web=data.get('site_web'),
            support_technique=data.get('support_technique')
        )
        try:
            new_id = self._fab_repo.add(fab_data)
            if new_id is None: raise BusinessLogicError("Échec création fabricant.")
            logger.info(f"Fabricant '{fab_data.nom}' créé ID: {new_id}.")
            created_fab = self.get_fabricant_by_id(new_id)
            if not created_fab: raise BusinessLogicError("Fabricant créé mais non retrouvé.")
            return created_fab
        except DatabaseError as e:
            logger.error(f"Échec DB création fabricant: {e}")
            raise BusinessLogicError(f"Impossible de créer le fabricant: {e}") from e

    def get_fabricant_by_id(self, fabricant_id: int) -> Optional[Fabricant]:
        """ Récupère un fabricant par ID. """
        logger.debug(f"Recherche fabricant ID: {fabricant_id}")
        try:
            return self._fab_repo.get_by_id(fabricant_id)
        except DatabaseError as e:
            logger.error(f"Erreur DB get fabricant ID {fabricant_id}: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    # get_all_fabricants existe déjà

    def update_fabricant(self, fabricant_id: int, update_data: Dict[str, Any]) -> Fabricant:
        """ Met à jour un fabricant existant. """
        logger.info(f"Tentative màj fabricant ID: {fabricant_id}")
        fab = self.get_fabricant_by_id(fabricant_id)
        if fab is None:
            raise NotFoundError(f"Fabricant ID {fabricant_id} non trouvé pour màj.")

        if 'nom' in update_data and not update_data.get('nom'):
             raise BusinessLogicError("Le nom du fabricant ne peut pas être vide.")

        has_changed = False
        for key, value in update_data.items():
            if hasattr(fab, key) and getattr(fab, key) != value:
                setattr(fab, key, value)
                has_changed = True
                logger.debug(f"Fabricant ID {fabricant_id}: Champ '{key}' modifié.")

        if not has_changed: return fab

        try:
            success = self._fab_repo.update(fab)
            if not success: raise BusinessLogicError("Échec màj fabricant (non trouvé?).")
            logger.info(f"Fabricant ID {fabricant_id} mis à jour.")
            updated_fab = self.get_fabricant_by_id(fabricant_id)
            if not updated_fab: raise BusinessLogicError("Fabricant màj mais non retrouvé.")
            return updated_fab
        except DatabaseError as e:
            logger.error(f"Échec DB màj fabricant ID {fabricant_id}: {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour le fabricant: {e}") from e

    def delete_fabricant(self, fabricant_id: int) -> bool:
        """ Supprime un fabricant. """
        logger.warning(f"Tentative suppression fabricant ID: {fabricant_id}")
        if self.get_fabricant_by_id(fabricant_id) is None:
            raise NotFoundError(f"Fabricant ID {fabricant_id} non trouvé pour suppression.")
        try:
            success = self._fab_repo.delete(fabricant_id)
            if success: logger.info(f"Fabricant ID {fabricant_id} supprimé.")
            return success
        except DatabaseError as e: # Gère l'erreur si des machines sont liées
             logger.error(f"Échec DB suppression fabricant ID {fabricant_id}: {e}")
             raise BusinessLogicError(f"Impossible de supprimer le fabricant: {e}") from e
        


     # gmao_app/app/core/services/machine_service.py
# (Dans la classe MachineService)

    # --- CRUD pour TypeMachine ---

    def create_type_machine(self, data: Dict[str, Any]) -> TypeMachine:
        """ Crée un nouveau type de machine. """
        logger.info(f"Tentative création type machine: {data.get('nom')}")
        if not data.get('nom'):
            raise BusinessLogicError("Le nom du type de machine est obligatoire.")

        tm_data = TypeMachine(
            nom=data['nom'],
            description=data.get('description'),
            categorie=data.get('categorie')
        )
        try:
            new_id = self._type_repo.add(tm_data)
            if new_id is None: raise BusinessLogicError("Échec création type machine.")
            logger.info(f"Type machine '{tm_data.nom}' créé ID: {new_id}.")
            created_tm = self.get_type_machine_by_id(new_id)
            if not created_tm: raise BusinessLogicError("Type machine créé mais non retrouvé.")
            return created_tm
        except DatabaseError as e:
            logger.error(f"Échec DB création type machine: {e}")
            raise BusinessLogicError(f"Impossible de créer le type machine: {e}") from e

    def get_type_machine_by_id(self, tm_id: int) -> Optional[TypeMachine]:
        """ Récupère un type machine par ID. """
        logger.debug(f"Recherche type machine ID: {tm_id}")
        try:
            return self._type_repo.get_by_id(tm_id)
        except DatabaseError as e:
            logger.error(f"Erreur DB get type machine ID {tm_id}: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    # get_all_type_machines existe déjà

    def update_type_machine(self, tm_id: int, update_data: Dict[str, Any]) -> TypeMachine:
        """ Met à jour un type machine existant. """
        logger.info(f"Tentative màj type machine ID: {tm_id}")
        tm = self.get_type_machine_by_id(tm_id)
        if tm is None:
            raise NotFoundError(f"Type machine ID {tm_id} non trouvé pour màj.")

        if 'nom' in update_data and not update_data.get('nom'):
             raise BusinessLogicError("Le nom du type machine ne peut pas être vide.")

        has_changed = False
        for key, value in update_data.items():
            if hasattr(tm, key) and getattr(tm, key) != value:
                setattr(tm, key, value)
                has_changed = True
                logger.debug(f"TypeMachine ID {tm_id}: Champ '{key}' modifié.")

        if not has_changed: return tm

        try:
            success = self._type_repo.update(tm)
            if not success: raise BusinessLogicError("Échec màj type machine (non trouvé?).")
            logger.info(f"Type machine ID {tm_id} mis à jour.")
            updated_tm = self.get_type_machine_by_id(tm_id)
            if not updated_tm: raise BusinessLogicError("Type machine màj mais non retrouvé.")
            return updated_tm
        except DatabaseError as e:
            logger.error(f"Échec DB màj type machine ID {tm_id}: {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour le type: {e}") from e

    def delete_type_machine(self, tm_id: int) -> bool:
        """ Supprime un type de machine. """
        logger.warning(f"Tentative suppression type machine ID: {tm_id}")
        if self.get_type_machine_by_id(tm_id) is None:
            raise NotFoundError(f"Type machine ID {tm_id} non trouvé.")
        try:
            success = self._type_repo.delete(tm_id)
            if success: logger.info(f"Type machine ID {tm_id} supprimé.")
            return success
        except DatabaseError as e: # Gère ON DELETE RESTRICT
             logger.error(f"Échec DB suppression type machine ID {tm_id}: {e}")
             raise BusinessLogicError(f"Impossible de supprimer le type: {e}") from e
           
    # --- Méthodes pour la gestion des Machines ---

    def create_machine(self, data: Dict[str, Any]) -> Machine:
        """
        Crée une nouvelle machine après validation.
        'data' est un dictionnaire contenant les attributs de la machine.
        Lève une exception en cas d'erreur.
        """
        logger.info(f"Tentative de création de machine: {data.get('nom')}")

        # --- Validation métier ---
        if not data.get('nom') or not data.get('type_machine_id') or \
           not data.get('site_id') or not data.get('fabricant_id'):
            raise BusinessLogicError("Nom, Type, Site et Fabricant sont obligatoires.")

        # Vérifier l'existence des entités liées (clés étrangères)
        if not self._type_repo.get_by_id(data['type_machine_id']):
             raise NotFoundError(f"Type de machine ID {data['type_machine_id']} non trouvé.")
        if not self._site_repo.get_by_id(data['site_id']):
             raise NotFoundError(f"Site ID {data['site_id']} non trouvé.")
        if not self._fab_repo.get_by_id(data['fabricant_id']):
             raise NotFoundError(f"Fabricant ID {data['fabricant_id']} non trouvé.")
        if data.get('parent_machine_id') and not self.get_machine_by_id(data['parent_machine_id']):
             # Vérifier le parent seulement s'il est fourni
             raise NotFoundError(f"Machine parente ID {data['parent_machine_id']} non trouvée.")

        # TODO: Ajouter d'autres validations (format serial?, dates cohérentes?)

        # Créer l'objet modèle Machine
        # Utiliser .get pour gérer les champs optionnels
        machine_data = Machine(
            nom=data['nom'],
            type_machine_id=data['type_machine_id'],
            site_id=data['site_id'],
            fabricant_id=data['fabricant_id'],
            serial=data.get('serial'),
            modele=data.get('modele'),
            date_installation=data.get('date_installation'), # Doit être objet date ou None
            localisation=data.get('localisation'),
            etat=data.get('etat', 'Inconnu'), # Etat par défaut
            informations_techniques=data.get('informations_techniques'),
            parent_machine_id=data.get('parent_machine_id'),
            criticite=data.get('criticite'),
            garantie_fin=data.get('garantie_fin') # Doit être objet date ou None
            # Les ID, created_at, updated_at sont gérés par la DB/Repo
        )

        try:
            new_id = self._machine_repo.add(machine_data)
            # Le repo lève DatabaseError si contrainte unique (serial) violée
            if new_id is None:
                 raise BusinessLogicError("La création de la machine a échoué pour une raison inconnue.")

            logger.info(f"Machine '{machine_data.nom}' créée avec succès (ID: {new_id}).")
            # Recharger pour avoir l'objet complet avec ID et timestamps
            created_machine = self.get_machine_by_id(new_id)
            if created_machine is None:
                raise BusinessLogicError("Machine créée mais impossible de la recharger.")
            return created_machine

        except DatabaseError as e:
            logger.error(f"Échec création machine '{machine_data.nom}' (DB): {e}")
            raise BusinessLogicError(f"Impossible de créer la machine : {e}") from e
        except Exception as e:
            logger.exception(f"Erreur inattendue création machine '{machine_data.nom}': {e}")
            raise BusinessLogicError(f"Erreur inattendue lors de la création : {e}") from e

    def get_machine_by_id(self, machine_id: int) -> Optional[Machine]:
        """Récupère une machine par son ID."""
        logger.debug(f"Recherche machine par ID: {machine_id}")
        try:
            machine = self._machine_repo.get_by_id(machine_id)
            if machine is None:
                 logger.warning(f"Machine ID {machine_id} non trouvée.")
            return machine
        except DatabaseError as e:
            logger.error(f"Erreur DB recherche machine ID {machine_id}: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    def get_all_machines(self, filters: Optional[Dict[str, Any]] = None,
                         sort_by: str = "nom", sort_desc: bool = False) -> List[Machine]:
        """
        Récupère la liste des machines avec filtres et tri.
        Transmet les options au repository.
        """
        logger.debug(f"Récupération de machines (filters={filters}, sort={sort_by}{' DESC' if sort_desc else ''}).")
        try:
            return self._machine_repo.get_all(filters=filters, sort_by=sort_by, sort_desc=sort_desc)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_all machines: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    def update_machine(self, machine_id: int, update_data: Dict[str, Any]) -> Machine:
        """
        Met à jour une machine existante.
        'update_data' contient les champs à modifier.
        Lève NotFoundError si la machine n'existe pas, BusinessLogicError si erreur.
        """
        logger.info(f"Tentative de mise à jour machine ID: {machine_id}")
        machine = self.get_machine_by_id(machine_id)
        if machine is None:
            raise NotFoundError(f"Machine ID {machine_id} non trouvée pour mise à jour.")

        # --- Validation des clés étrangères si elles sont modifiées ---
        if 'type_machine_id' in update_data and update_data['type_machine_id'] != machine.type_machine_id:
             if not self._type_repo.get_by_id(update_data['type_machine_id']):
                  raise NotFoundError(f"Nouveau Type machine ID {update_data['type_machine_id']} non trouvé.")
        if 'site_id' in update_data and update_data['site_id'] != machine.site_id:
             if not self._site_repo.get_by_id(update_data['site_id']):
                  raise NotFoundError(f"Nouveau Site ID {update_data['site_id']} non trouvé.")
        if 'fabricant_id' in update_data and update_data['fabricant_id'] != machine.fabricant_id:
             if not self._fab_repo.get_by_id(update_data['fabricant_id']):
                  raise NotFoundError(f"Nouveau Fabricant ID {update_data['fabricant_id']} non trouvé.")
        if 'parent_machine_id' in update_data and update_data['parent_machine_id'] != machine.parent_machine_id:
            if update_data['parent_machine_id'] is not None: # Si le nouveau parent n'est pas None
                if update_data['parent_machine_id'] == machine_id: # Auto-référence interdite
                    raise BusinessLogicError("Une machine ne peut pas être son propre parent.")
                if not self.get_machine_by_id(update_data['parent_machine_id']):
                    raise NotFoundError(f"Nouvelle Machine parente ID {update_data['parent_machine_id']} non trouvée.")
                # TODO: Vérifier boucle de dépendance (A est parent B, B est parent A) -> plus complexe

        # Appliquer les modifications à l'objet machine existant
        has_changed = False
        for key, value in update_data.items():
            if hasattr(machine, key) and getattr(machine, key) != value:
                 # Gérer les dates qui peuvent arriver comme string depuis une UI?
                 # Pour l'instant, on assume qu'elles sont des objets 'date' ou None
                setattr(machine, key, value)
                has_changed = True
                logger.debug(f"Machine ID {machine_id}: Champ '{key}' modifié.")

        if not has_changed:
            logger.info(f"Aucune modification détectée pour machine ID {machine_id}.")
            return machine # Pas besoin d'appeler le repo si rien n'a changé

        # Appel au repository pour persister les changements
        # updated_at sera géré par trigger
        try:
            success = self._machine_repo.update(machine)
            if not success:
                 # Peu probable si get_by_id a fonctionné avant
                 raise BusinessLogicError("La mise à jour a échoué (machine disparue?).")

            logger.info(f"Machine ID {machine_id} mise à jour avec succès.")
            # Recharger pour être sûr d'avoir l'état DB final (avec updated_at)
            updated_machine = self.get_machine_by_id(machine_id)
            if updated_machine is None: # Improbable
                raise BusinessLogicError("Machine mise à jour mais impossible de la recharger.")
            return updated_machine

        except DatabaseError as e:
            logger.error(f"Échec màj machine ID {machine_id} (DB): {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour la machine : {e}") from e
        except Exception as e:
            logger.exception(f"Erreur inattendue màj machine ID {machine_id}: {e}")
            raise BusinessLogicError(f"Erreur inattendue lors de la mise à jour : {e}") from e

    def delete_machine(self, machine_id: int) -> bool:
        """
        Supprime une machine.
        Lève NotFoundError si non trouvée, BusinessLogicError si erreur.
        Retourne True si succès.
        """
        logger.warning(f"Tentative de suppression machine ID: {machine_id}")
        machine = self.get_machine_by_id(machine_id)
        if machine is None:
            raise NotFoundError(f"Machine ID {machine_id} non trouvée pour suppression.")

        # --- Logique métier avant suppression (optionnel) ---
        # Ex: Vérifier s'il y a des OT en cours? Ou la contrainte DB suffit?
        # La contrainte ON DELETE RESTRICT sur les FK dans OT/Maintenance devrait lever
        # une DatabaseError (convertie en BusinessLogicError) si la machine est référencée.

        try:
            success = self._machine_repo.delete(machine_id)
            if success:
                 logger.info(f"Machine ID {machine_id} supprimée avec succès.")
            # else: # Le repo lèvera une erreur si non supprimé ou contrainte violée
                 # raise BusinessLogicError("La suppression a échoué.")
            return success
        except DatabaseError as e:
            logger.error(f"Échec suppression machine ID {machine_id} (DB): {e}")
            # Erreur métier claire pour l'UI
            raise BusinessLogicError(f"Impossible de supprimer la machine: {e}") from e
        except Exception as e:
            logger.exception(f"Erreur inattendue suppression machine ID {machine_id}: {e}")
            raise BusinessLogicError(f"Erreur inattendue lors de la suppression: {e}") from e