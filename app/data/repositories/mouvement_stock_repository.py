# gmao_app/app/data/repositories/mouvement_stock_repository.py
""" Repository pour l'entité MouvementStock. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.mouvement_stock import MouvementStock

logger = logging.getLogger(__name__)

class MouvementStockRepository:

    def add(self, mvt: MouvementStock) -> Optional[int]:
        """ Ajoute un nouveau mouvement de stock à la base de données. """
        sql = """INSERT INTO MOUVEMENT_STOCK (piece_id, type_mouvement, quantite,
                                            date_mouvement, raison, ot_id, user_id,
                                            stock_avant, stock_apres)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) """
        params = (
            mvt.piece_id,
            mvt.type_mouvement,
            mvt.quantite,
            mvt.date_mouvement,
            mvt.raison,
            mvt.ot_id,
            mvt.user_id,
            mvt.stock_avant,
            mvt.stock_apres
        )
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql + " RETURNING id_mouvement", params)
                row = cursor.fetchone()
            new_id = row['id_mouvement'] if row else None
            logger.info(f"Mouvement de stock ID {new_id} ajouté pour pièce ID {mvt.piece_id} (Type: {mvt.type_mouvement}, Qte: {mvt.quantite}).")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.error(f"Erreur d'intégrité ajout mouvement stock pour pièce ID {mvt.piece_id}: {e}. Vérifier FK (piece_id, ot_id, user_id)%s")
            # Remonter une erreur spécifique si possible
            raise DatabaseError(f"Erreur d'intégrité: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout mouvement stock: {e}")
            raise

    def get_by_id(self, mvt_id: int) -> Optional[MouvementStock]:
        """ Récupère un mouvement de stock par son ID. """
        sql = "SELECT * FROM MOUVEMENT_STOCK WHERE id_mouvement = %s"
        try:
            row = fetch_one(sql, (mvt_id,))
            return MouvementStock.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get mouvement stock ID {mvt_id}: {e}")
            raise

    def get_by_piece_id(self, piece_id: int, limit: Optional[int] = None) -> List[MouvementStock]:
        """ Récupère les mouvements de stock pour une pièce donnée, triés par date décroissante. """
        sql = "SELECT * FROM MOUVEMENT_STOCK WHERE piece_id = %s ORDER BY date_mouvement DESC"
        params = (piece_id,)
        if limit:
            sql += " LIMIT %s"
            params += (limit,)

        try:
            rows = fetch_all(sql, params)
            return [MouvementStock.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get mouvements stock pour pièce ID {piece_id}: {e}")
            raise

    # --- D'autres méthodes pourraient être utiles ---
    # - get_all (potentiellement très grand, attention)
    # - get_by_ot_id
    # - get_by_date_range
    # - ... etc.
