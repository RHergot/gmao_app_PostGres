# gmao_app/app/data/repositories/gamme_etape_repository.py
""" Repository pour l'entité GammeEtape. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.gamme_etape import GammeEtape

logger = logging.getLogger(__name__)

class GammeEtapeRepository:

    def add(self, etape: GammeEtape) -> Optional[int]:
        sql = """INSERT INTO GAMME_ETAPE (gamme_id, description, ordre,
                                        instructions_detaillees, duree_estimee_min)
                 VALUES (%s, %s, %s, %s, %s)"""
        params = (etape.gamme_id, etape.description, etape.ordre,
                  etape.instructions_detaillees, etape.duree_estimee_min)
        try:
            cursor = execute_query(sql, params)
            new_id = cursor.lastrowid
            logger.info(f"Étape {etape.ordre} ajoutée à Gamme ID {etape.gamme_id} (ID Etape: {new_id}).")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.error(f"Échec ajout étape gamme {etape.gamme_id}. FK Gamme, Ordre unique: {e}")
            raise DatabaseError("Référence Gamme invalide ou Ordre déjà utilisé.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout étape gamme {etape.gamme_id}: {e}")
            raise

    def get_by_id(self, etape_id: int) -> Optional[GammeEtape]:
        sql = "SELECT * FROM GAMME_ETAPE WHERE id_etape = %s"
        try:
            row = fetch_one(sql, (etape_id,))
            return GammeEtape.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get étape ID {etape_id}: {e}")
            raise

    def get_by_gamme_id(self, gamme_id: int) -> List[GammeEtape]:
        """ Récupère toutes les étapes d'une gamme, triées par ordre. """
        sql = "SELECT * FROM GAMME_ETAPE WHERE gamme_id = %s ORDER BY ordre"
        try:
            rows = fetch_all(sql, (gamme_id,))
            return [GammeEtape.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get étapes pour gamme ID {gamme_id}: {e}")
            raise

    def update(self, etape: GammeEtape) -> bool:
        if etape.id_etape is None: return False
        sql = """UPDATE GAMME_ETAPE SET gamme_id=%s, description=%s, ordre=%s,
                                      instructions_detaillees=%s, duree_estimee_min=%s
                 WHERE id_etape = %s"""
        params = (etape.gamme_id, etape.description, etape.ordre,
                  etape.instructions_detaillees, etape.duree_estimee_min, etape.id_etape)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Étape ID {etape.id_etape} mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.error(f"Échec màj étape ID {etape.id_etape}. FK Gamme, Ordre unique: {e}")
            raise DatabaseError("Contrainte intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update étape ID {etape.id_etape}: {e}")
            raise

    def delete(self, etape_id: int) -> bool:
        sql = "DELETE FROM GAMME_ETAPE WHERE id_etape = %s"
        try:
            cursor = execute_query(sql, (etape_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Étape ID {etape_id} supprimée.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB delete étape ID {etape_id}: {e}")
            raise

    def delete_by_gamme_id(self, gamme_id: int) -> int:
        """ Supprime toutes les étapes d'une gamme. """
        sql = "DELETE FROM GAMME_ETAPE WHERE gamme_id = %s"
        try:
            cursor = execute_query(sql, (gamme_id,))
            count = cursor.rowcount
            if count > 0: logger.info(f"{count} étapes supprimées pour Gamme ID {gamme_id}.")
            return count
        except DatabaseError as e:
            logger.error(f"Erreur DB delete étapes pour Gamme ID {gamme_id}: {e}")
            raise