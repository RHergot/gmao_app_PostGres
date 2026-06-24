# gmao_app/app/data/repositories/equipe_repository.py
""" Repository pour l'entité Equipe. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.equipe import Equipe

logger = logging.getLogger(__name__)

class EquipeRepository:

    def add(self, equipe: Equipe) -> Optional[int]:
        sql = "INSERT INTO EQUIPE (nom, domaine_expertise, responsable_id) VALUES (%s, %s, %s) RETURNING id_equipe"
        params = (equipe.nom, equipe.domaine_expertise, equipe.responsable_id)
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_equipe") if row else None
            logger.info(f"Equipe '{equipe.nom}' ajoutée ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout equipe '{equipe.nom}'. Nom unique%s FK resp.%s {e}")
            if 'EQUIPE.nom' in str(e):
                 raise DatabaseError(f"Nom équipe '{equipe.nom}' existe déjà.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Responsable {equipe.responsable_id} invalide.") from e
            else:
                 raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout equipe '{equipe.nom}': {e}")
            raise

    def get_by_id(self, equipe_id: int) -> Optional[Equipe]:
        sql = "SELECT * FROM EQUIPE WHERE id_equipe = %s"
        try:
            row = fetch_one(sql, (equipe_id,))
            return Equipe.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get equipe ID {equipe_id}: {e}")
            raise

    def get_all(self) -> List[Equipe]:
        sql = "SELECT * FROM EQUIPE ORDER BY nom"
        try:
            rows = fetch_all(sql)
            return [Equipe.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get all equipes: {e}")
            raise

    def update(self, equipe: Equipe) -> bool:
        if equipe.id_equipe is None: return False
        sql = "UPDATE EQUIPE SET nom = %s, domaine_expertise = %s, responsable_id = %s WHERE id_equipe = %s RETURNING id_equipe"
        params = (equipe.nom, equipe.domaine_expertise, equipe.responsable_id, equipe.id_equipe)
        try:
            row = fetch_one(sql, params)
            success = row is not None
            if success: logger.info(f"Equipe ID {equipe.id_equipe} mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj equipe ID {equipe.id_equipe}. Nom unique%s FK resp.%s {e}")
            if 'EQUIPE.nom' in str(e):
                 raise DatabaseError(f"Nom équipe '{equipe.nom}' déjà utilisé.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Responsable {equipe.responsable_id} invalide.") from e
            else:
                 raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update equipe ID {equipe.id_equipe}: {e}")
            raise

    def delete(self, equipe_id: int) -> bool:
        # La FK dans TECHNICIEN est ON DELETE SET NULL, donc la suppression devrait fonctionner
        # mais les techniciens liés n'auront plus d'équipe.
        sql = "DELETE FROM EQUIPE WHERE id_equipe = %s"
        try:
            cursor = execute_query(sql, (equipe_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Equipe ID {equipe_id} supprimée.")
            return success
        except DatabaseError as e: # Peu probable ici sauf erreur DB générale
            logger.error(f"Erreur DB delete equipe ID {equipe_id}: {e}")
            raise