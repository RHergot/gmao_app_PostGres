# gmao_app/app/core/services/user_service.py
"""
Service métier pour la gestion des utilisateurs.
"""
import logging
import os
from typing import Optional, List, Dict, Any
from app.data.repositories.user_repository import UserRepository
from app.core.models.utilisateur import Utilisateur
from app.utils.exceptions import BusinessLogicError, DatabaseError, NotFoundError # Ajouter NotFoundError
from app.utils.helpers import hash_password, check_password # Importer helpers
from datetime import datetime

logger = logging.getLogger(__name__)

# TODO: Définir les rôles valides (pourrait venir d'une config ou DB)
VALID_ROLES = ["Admin", "Responsable Maintenance", "Technicien", "Gestionnaire Stock", "Lecteur"]

class UserService:
    """Orchestre les opérations liées aux utilisateurs."""

    def __init__(self, user_repository: UserRepository):
        self._repository = user_repository
        logger.debug("UserService initialisé avec UserRepository.")
        logger.info("UserService initialisé.")

    def ensure_admin_exists(self, default_login=None, default_password=None):
        """ Vérifie si un admin existe, sinon crée le premier avec les identifiants fournis.
        
        Les identifiants par défaut sont lus depuis les variables d'environnement:
        - INITIAL_ADMIN_LOGIN (défaut: "admin")
        - INITIAL_ADMIN_PASSWORD (obligatoire si aucun utilisateur n'existe)
        """
        if default_login is None:
            default_login = os.getenv('INITIAL_ADMIN_LOGIN', 'admin')
        if default_password is None:
            default_password = os.getenv('INITIAL_ADMIN_PASSWORD', '')
        
        try:
            # Vérifie s'il y a DÉJÀ des utilisateurs
            if not self._repository.has_users():
                 if not default_password:
                     logger.error(
                         "Aucun utilisateur trouvé et INITIAL_ADMIN_PASSWORD non défini. "
                         "Impossible de créer l'administrateur initial. "
                         "Définissez INITIAL_ADMIN_PASSWORD dans le fichier .env."
                     )
                     return
                 logger.warning("Aucun utilisateur trouvé. Création de l'administrateur initial...")
                 try:
                     # Appel à create_user qui gère le hashage etc.
                     admin_user = self.create_user(
                         login=default_login,
                         password=default_password,
                         role="Admin", # Assurez-vous que ce rôle est valide/attendu
                         nom_complet="Admin Initial"
                         # email=None, actif=1, etc. si create_user les gère
                     )
                     if admin_user:
                         logger.info(f"Administrateur initial '{default_login}' créé avec succès.")
                     else:
                          logger.error(f"Échec de la création de l'administrateur initial '{default_login}' via create_user.")
                 except Exception as creation_error: # Attrape erreur de create_user
                       logger.error(f"Erreur lors de la tentative de création de l'admin initial: {creation_error}", exc_info=True)
            else:
                 logger.debug("Au moins un utilisateur existe déjà. Pas de création d'admin initial.")

        except DatabaseError as e:
             # Erreur venant de has_users()
             logger.error(f"Impossible de vérifier ou créer l'admin initial (Erreur DB): {e}")
        except Exception as e:
            logger.exception(f"Erreur inattendue dans ensure_admin_exists: {e}")

    def create_user(self, login: str, password: str, role: str, nom_complet: Optional[str] = None, email: Optional[str] = None, actif: bool = True, technicien_id: Optional[int] = None) -> Utilisateur:
        """
        Crée un nouvel utilisateur après validation.
        Retourne l'objet Utilisateur créé. Lève une exception en cas d'erreur.
        """
        logger.info(f"Tentative de création d'utilisateur: login={login}, role={role}")

        # --- Validation métier ---
        if not login or not password or not role:
             raise BusinessLogicError("Login, mot de passe et rôle sont obligatoires.")
        if role not in VALID_ROLES:
             raise BusinessLogicError(f"Rôle invalide: {role}. Rôles valides: {', '.join(VALID_ROLES)}")
        # TODO: Ajouter validation format email, complexité password ?

        # Hasher le mot de passe
        try:
            hashed_pw = hash_password(password)
        except Exception as e:
            # Normalement hash_password gère déjà ça, mais double sécurité
            raise BusinessLogicError(f"Erreur lors du hachage du mot de passe: {e}")

        user_data = Utilisateur(
            login=login,
            nom_complet=nom_complet,
            role=role,
            email=email,
            mot_de_passe_hash=hashed_pw,
            actif=actif,
            technicien_id=technicien_id
        )

        try:
            new_id = self._repository.add(user_data)
            # Si add échoue avec contrainte unique, une DatabaseError est levée par le repo
            if new_id is None:
                 # Cas très improbable si add ne lève pas d'erreur avant
                 raise BusinessLogicError("La création de l'utilisateur a échoué pour une raison inconnue.")

            user_data.id_utilisateur = new_id
            logger.info(f"Utilisateur '{login}' créé avec succès (ID: {new_id}).")
            # Recharger depuis la DB pour avoir created_at/updated_at propres
            created_user = self.get_user_by_id(new_id)
            if created_user is None: # Encore plus improbable
                 raise BusinessLogicError("Utilisateur créé mais impossible de le recharger.")
            return created_user

        except DatabaseError as e:
            logger.error(f"Échec création utilisateur '{login}' (DB): {e}")
            # Renvoyer une erreur métier claire à l'UI
            raise BusinessLogicError(f"Impossible de créer l'utilisateur : {e}") from e
        except Exception as e:
            logger.exception(f"Erreur inattendue création utilisateur '{login}': {e}")
            raise BusinessLogicError(f"Erreur inattendue : {e}") from e

    def get_user_by_id(self, user_id: int) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son ID."""
        logger.debug(f"Recherche utilisateur par ID: {user_id}")
        try:
            user = self._repository.get_by_id(user_id)
            if user is None:
                 logger.warning(f"Utilisateur ID {user_id} non trouvé.")
                 # Optionnel: Lever une NotFoundError ici ? ou laisser UI gérer None?
                 # raise NotFoundError(f"Utilisateur ID {user_id} non trouvé.")
            return user
        except DatabaseError as e:
            logger.error(f"Erreur DB recherche user ID {user_id}: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e # Masquer détails DB à l'UI

    def get_user_by_login(self, login: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son login."""
        logger.debug(f"Recherche utilisateur par login: {login}")
        try:
            user = self._repository.get_by_login(login)
            if user is None:
                 logger.warning(f"Utilisateur login '{login}' non trouvé.")
            return user
        except DatabaseError as e:
            logger.error(f"Erreur DB recherche user login '{login}': {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    def get_all_users(self) -> List[Utilisateur]:
        """Récupère la liste de tous les utilisateurs."""
        logger.debug("Récupération de tous les utilisateurs.")
        try:
            return self._repository.get_all()
        except DatabaseError as e:
            logger.error(f"Erreur DB récupération tous utilisateurs: {e}")
            raise BusinessLogicError(f"Erreur base de données: {e}") from e

    def update_user(self, user_id: int, update_data: dict) -> Utilisateur:
        """
        Met à jour un utilisateur existant.
        'update_data' est un dictionnaire contenant les champs à modifier.
        Le mot de passe doit être explicitement géré (voir change_password).
        """
        logger.info(f"Tentative de mise à jour utilisateur ID: {user_id}")
        user = self.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError(f"Utilisateur ID {user_id} non trouvé pour mise à jour.")

        # Appliquer les modifications depuis update_data
        has_changed = False
        for key, value in update_data.items():
            if hasattr(user, key) and getattr(user, key) != value:
                # Ne pas autoriser la modif du hash de mdp par cette méthode
                if key == 'mot_de_passe_hash':
                    logger.warning(f"Tentative de modification de 'mot_de_passe_hash' via update_user ignorée pour ID {user_id}. Utiliser change_password.")
                    continue
                # Validation (ex: rôle)
                if key == 'role' and value not in VALID_ROLES:
                     raise BusinessLogicError(f"Rôle invalide: {value}")
                # TODO: Valider email, etc.

                setattr(user, key, value)
                has_changed = True
                logger.debug(f"User ID {user_id}: Champ '{key}' modifié.")

        if not has_changed:
            logger.info(f"Aucune modification détectée pour utilisateur ID {user_id}.")
            return user # Retourner l'utilisateur original si rien n'a changé

        # Le champ 'updated_at' sera mis à jour par le trigger DB
        try:
            success = self._repository.update(user)
            if not success:
                 # Devrait être impossible si get_user_by_id a fonctionné, mais sécurité
                 raise BusinessLogicError("La mise à jour a échoué (utilisateur disparu?).")

            logger.info(f"Utilisateur ID {user_id} mis à jour avec succès.")
            # Recharger pour être sûr d'avoir l'état final (surtout updated_at)
            updated_user = self.get_user_by_id(user_id)
            if updated_user is None:
                raise BusinessLogicError("Utilisateur mis à jour mais impossible de le recharger.")
            return updated_user

        except DatabaseError as e:
            logger.error(f"Échec màj utilisateur ID {user_id} (DB): {e}")
            raise BusinessLogicError(f"Impossible de mettre à jour : {e}") from e
        except Exception as e:
            logger.exception(f"Erreur inattendue màj utilisateur ID {user_id}: {e}")
            raise BusinessLogicError(f"Erreur inattendue : {e}") from e

    def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur."""
        logger.warning(f"Tentative de suppression utilisateur ID: {user_id}")
        # Vérifier si l'utilisateur existe avant (évite erreur si ID invalide)
        user = self.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError(f"Utilisateur ID {user_id} non trouvé pour suppression.")

        # TODO: Ajouter logique métier? Ex: Ne pas supprimer le dernier Admin?
        # if user.role == "Admin" and self._repository.count_admins() <= 1:
        #    raise BusinessLogicError("Impossible de supprimer le dernier administrateur.")

        try:
            success = self._repository.delete(user_id)
            if success:
                 logger.info(f"Utilisateur ID {user_id} supprimé avec succès.")
            # else: # Si le repo retourne False sans lever d'erreur (ex: user a disparu entre temps)
            #      raise BusinessLogicError("La suppression a échoué (utilisateur disparu?).")
            return success
        except DatabaseError as e:
            logger.error(f"Échec suppression utilisateur ID {user_id} (DB): {e}")
            raise BusinessLogicError(f"Impossible de supprimer : {e}") from e
        except Exception as e:
            logger.exception(f"Erreur inattendue suppression utilisateur ID {user_id}: {e}")
            raise BusinessLogicError(f"Erreur inattendue : {e}") from e

    # --- Authentification ---
    def authenticate_user(self, login: str, password: str) -> Optional[Utilisateur]:
        """Vérifie les identifiants et retourne l'Utilisateur si succès, None sinon."""
        logger.info(f"Tentative d'authentification pour: {login}")
        user = self.get_user_by_login(login)

        if user is None:
            logger.warning(f"Authentification échouée: Utilisateur '{login}' non trouvé.")
            return None

        if not user.actif:
             logger.warning(f"Authentification échouée: Utilisateur '{login}' inactif.")
             return None

        if user.mot_de_passe_hash is None:
             logger.error(f"Authentification échouée: Utilisateur '{login}' n'a pas de mot de passe défini.")
             return None

        if check_password(password, user.mot_de_passe_hash):
             logger.info(f"Authentification réussie pour: {login}")
             # Mettre à jour derniere_connexion (optionnel ici, mieux dans un flow de login dédié)
             # user.derniere_connexion = datetime.now()
             # self._repository.update(user) # Attention, appelle update complet
             return user
        else:
             logger.warning(f"Authentification échouée: Mot de passe incorrect pour '{login}'.")
             return None

    def change_password(self, user_id: int, old_password: Optional[str], new_password: str) -> bool:
         """
         Change le mot de passe d'un utilisateur.
         Requiert l'ancien mot de passe sauf si initié par un admin (old_password=None).
         """
         # TODO: Ajouter vérification des permissions (seul l'utilisateur lui-même ou un admin peut changer?)
         logger.info(f"Tentative de changement de mot de passe pour user ID: {user_id}")
         user = self.get_user_by_id(user_id)
         if user is None:
             raise NotFoundError(f"Utilisateur ID {user_id} non trouvé pour changement de mot de passe.")

         if user.mot_de_passe_hash and old_password is not None: # Vérifier l'ancien mot de passe si fourni
             if not check_password(old_password, user.mot_de_passe_hash):
                  logger.warning(f"Échec changement mot de passe user ID {user_id}: Ancien mot de passe incorrect.")
                  raise BusinessLogicError("Ancien mot de passe incorrect.")

         # TODO: Valider complexité nouveau mot de passe

         try:
             new_hash = hash_password(new_password)
         except Exception as e:
             raise BusinessLogicError(f"Erreur lors du hachage du nouveau mot de passe: {e}")

         # Mettre à jour uniquement le hash dans l'objet utilisateur
         user.mot_de_passe_hash = new_hash

         try:
             # Appeler update du repo (qui mettra à jour le trigger updated_at)
             success = self._repository.update(user)
             if success:
                 logger.info(f"Mot de passe pour user ID {user_id} changé avec succès.")
             return success
         except DatabaseError as e:
             logger.error(f"Échec changement mdp user ID {user_id} (DB): {e}")
             raise BusinessLogicError(f"Impossible de changer le mot de passe : {e}") from e