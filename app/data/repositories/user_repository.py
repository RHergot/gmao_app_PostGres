# gmao_app/app/data/repositories/user_repository.py
"""
Repository pour gérer les opérations CRUD sur l'entité Utilisateur.
"""
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.utilisateur import Utilisateur

logger = logging.getLogger(__name__)

class UserRepository:
    """Gère la persistance des utilisateurs."""

    def has_users(self) -> bool:
        """ Vérifie s'il existe au moins un utilisateur dans la table. """
        sql = "SELECT COUNT(*) AS count FROM UTILISATEUR"
        try:
            result = fetch_one(sql)
            logger.debug(f"Résultat brut de has_users: {result}")
            if result is None:
                return False
            # Si result est un dict (avec DictCursor)
            if isinstance(result, dict):
                count = result.get('count')
                if count is None:
                    # Prend la première valeur si la clé 'count' n'existe pas
                    count = next(iter(result.values()))
                return count > 0
            # Si result est un tuple ou une liste
            if isinstance(result, (list, tuple)):
                return result[0] > 0
            # Sinon, cas inattendu
            logger.error(f"Type de résultat inattendu dans has_users: {type(result)}")
            return False
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la vérification de l'existence d'utilisateurs: {e}")
            raise DatabaseError("Impossible de vérifier l'existence des utilisateurs.") from e
        except Exception as e:
             logger.exception(f"Erreur inattendue dans has_users: {e}")
             raise DatabaseError("Erreur serveur lors de la vérification des utilisateurs.") from e

    def add(self, user: Utilisateur) -> Optional[int]:
        """
        Ajoute un nouvel utilisateur à la base de données.
        Nécessite que user.mot_de_passe_hash soit déjà défini (haché).
        Retourne l'ID du nouvel utilisateur ou None si échec.
        """
        if not user.mot_de_passe_hash:
             logger.error(f"Tentative d'ajout de l'utilisateur {user.login} sans mot de passe haché.")
             raise ValueError("Le hash du mot de passe est requis pour ajouter un utilisateur.")

        sql = """
            INSERT INTO UTILISATEUR (login, nom_complet, role, email, mot_de_passe_hash, actif, technicien_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_utilisateur
        """
        params = (
            user.login,
            user.nom_complet,
            user.role,
            user.email,
            user.mot_de_passe_hash,
            1 if user.actif else 0,
            user.technicien_id
        )
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_utilisateur") if row else None
            logger.info(f"Utilisateur '{user.login}' ajouté avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
             logger.warning(f"Impossible d'ajouter l'utilisateur '{user.login}'. Contrainte d'intégrité violée (login/email unique%s): {e}")
             # Analyser l'erreur pour être plus précis %s
             if 'UTILISATEUR.login' in str(e):
                 raise DatabaseError(f"Le login '{user.login}' existe déjà.") from e
             elif 'UTILISATEUR.email' in str(e):
                 raise DatabaseError(f"L'email '{user.email}' existe déjà.") from e
             else:
                 raise DatabaseError(f"Contrainte d'intégrité violée lors de l'ajout.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de l'ajout de l'utilisateur '{user.login}': {e}")
            raise
        except Exception as e:
             logger.exception(f"Erreur inattendue lors de l'ajout de l'utilisateur {user.login}: {e}")
             raise DatabaseError(f"Erreur inattendue lors de l'ajout: {e}") from e

    def get_by_id(self, user_id: int) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son ID."""
        sql = "SELECT * FROM UTILISATEUR WHERE id_utilisateur = %s"
        try:
            row = fetch_one(sql, (user_id,))
            user = Utilisateur.from_db_row(row)
            if user:
                logger.debug(f"Utilisateur ID {user_id} trouvé.")
            else:
                logger.debug(f"Utilisateur ID {user_id} non trouvé.")
            return user
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_id user {user_id}: {e}")
            raise

    def get_by_login(self, login: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son login."""
        sql = "SELECT * FROM UTILISATEUR WHERE login = %s"
        try:
            row = fetch_one(sql, (login,))
            user = Utilisateur.from_db_row(row)
            if user:
                 logger.debug(f"Utilisateur login '{login}' trouvé.")
            else:
                 logger.debug(f"Utilisateur login '{login}' non trouvé.")
            return user
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_login '{login}': {e}")
            raise

    def get_all(self, limit: int = -1, offset: int = 0) -> List[Utilisateur]:
        """Récupère tous les utilisateurs (avec pagination optionnelle)."""
        sql = "SELECT * FROM UTILISATEUR ORDER BY nom_complet, login"
        params = []
        if limit > 0:
            sql += " LIMIT %s"
            params.append(limit)
        if offset > 0:
            sql += " OFFSET %s"
            params.append(offset)

        try:
            rows = fetch_all(sql, tuple(params))
            users = [Utilisateur.from_db_row(row) for row in rows if row]
            logger.debug(f"{len(users)} utilisateurs récupérés.")
            return users
        except DatabaseError as e:
            logger.error(f"Erreur DB get_all users: {e}")
            raise

    def update(self, user: Utilisateur) -> bool:
        """Met à jour un utilisateur existant (identifié par user.id_utilisateur)."""
        if user.id_utilisateur is None:
            logger.error("Tentative de mise à jour d'un utilisateur sans ID.")
            return False

        sql = """
            UPDATE UTILISATEUR SET
                login = %s, nom_complet = %s, role = %s, email = %s,
                mot_de_passe_hash = %s, actif = %s, derniere_connexion = %s, technicien_id = %s
                -- Ne met pas à jour created_at, updated_at est géré par trigger
            WHERE id_utilisateur = %s
        """
        params = (
            user.login,
            user.nom_complet,
            user.role,
            user.email,
            user.mot_de_passe_hash,
            1 if user.actif else 0,
            user.derniere_connexion.isoformat() if user.derniere_connexion else None,
            user.technicien_id,
            user.id_utilisateur
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0 # rowcount indique si une ligne a été affectée
            if success:
                logger.info(f"Utilisateur ID {user.id_utilisateur} ('{user.login}') mis à jour.")
            else:
                logger.warning(f"Aucun utilisateur trouvé avec ID {user.id_utilisateur} pour la mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
             logger.warning(f"Échec mise à jour utilisateur '{user.login}'. Contrainte d'intégrité (login/email unique%s): {e}")
             # Adapter le message d'erreur basé sur l'erreur exacte
             if 'UTILISATEUR.login' in str(e):
                 raise DatabaseError(f"Le login '{user.login}' est déjà utilisé par un autre utilisateur.") from e
             elif 'UTILISATEUR.email' in str(e):
                 raise DatabaseError(f"L'email '{user.email}' est déjà utilisé par un autre utilisateur.") from e
             else:
                 raise DatabaseError("Contrainte d'intégrité violée lors de la mise à jour.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la mise à jour user ID {user.id_utilisateur}: {e}")
            raise

    def delete(self, user_id: int) -> bool:
        """Supprime un utilisateur par son ID."""
        sql = "DELETE FROM UTILISATEUR WHERE id_utilisateur = %s"
        try:
            cursor = execute_query(sql, (user_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Utilisateur ID {user_id} supprimé.")
            else:
                logger.warning(f"Aucun utilisateur trouvé avec ID {user_id} pour la suppression.")
            return success
        except psycopg2.IntegrityError as e:
            # Si l'utilisateur est référencé par une clé étrangère (ex: createur_id dans OT)
            # et qu'il n'y a pas de ON DELETE SET NULL/CASCADE, la suppression échouera.
             logger.error(f"Impossible de supprimer l'utilisateur ID {user_id}. Il est probablement référencé ailleurs: {e}")
             raise DatabaseError(f"Impossible de supprimer l'utilisateur {user_id} car il est référencé par d'autres enregistrements.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la suppression user ID {user_id}: {e}")
            raise