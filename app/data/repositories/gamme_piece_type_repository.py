# gmao_app/app/data/repositories/gamme_piece_type_repository.py
""" Repository pour l'entité GammePieceType (lien Gamme <-> Pièce). """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.gamme_piece_type import GammePieceType
from app.core.models.piece import Piece # Pour retourner infos pièce jointes?

logger = logging.getLogger(__name__)

class GammePieceTypeRepository:

    def add(self, gpt: GammePieceType) -> Optional[int]:
        sql = "INSERT INTO GAMME_PIECE_TYPE (gamme_id, piece_id, quantite_theorique) VALUES (%s, %s, %s) RETURNING id"
        params = (gpt.gamme_id, gpt.piece_id, gpt.quantite_theorique)
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
            new_id = row['id'] if row else None
            logger.info(f"Lien Pièce {gpt.piece_id} / Gamme {gpt.gamme_id} ajouté (ID lien: {new_id}).")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout lien G={gpt.gamme_id}/P={gpt.piece_id}. Unique? FK? {e}")
            if 'UNIQUE constraint failed' in str(e):
                raise DatabaseError("Cette pièce est déjà liée à cette gamme.") from e
            else:
                 raise DatabaseError("Référence Gamme ou Pièce invalide.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout lien Gamme/Pièce: {e}")
            raise

    # Pas de get_by_id sur cette table (l'ID autoincrémenté est peu utile)

    def get_by_gamme_id(self, gamme_id: int) -> List[GammePieceType]:
        """ Récupère toutes les pièces liées à une gamme. """
        sql = "SELECT * FROM GAMME_PIECE_TYPE WHERE gamme_id = %s"
        try:
            rows = fetch_all(sql, (gamme_id,))
            return [GammePieceType.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get pièces pour gamme {gamme_id}: {e}")
            raise

    # Optionnel: Récupérer aussi les détails de la pièce (nom, réf) via jointure
    def get_pieces_details_by_gamme_id(self, gamme_id: int) -> List[Dict[str, Any]]:
        """ Récupère pièces liées à une gamme AVEC détails de la pièce. """
        sql = """
            SELECT gpt.*, p.reference, p.nom as piece_nom, p.unite
            FROM GAMME_PIECE_TYPE gpt
            JOIN PIECE p ON gpt.piece_id = p.id_piece
            WHERE gpt.gamme_id = %s
            ORDER BY p.nom
        """
        try:
            rows = fetch_all(sql, (gamme_id,))
            # Retourner une liste de dictionnaires pour flexibilité UI
            return [dict(row) for row in rows]
        except DatabaseError as e:
            logger.error(f"Erreur DB get details pièces pour gamme {gamme_id}: {e}")
            raise

    def update_quantity(self, gamme_id: int, piece_id: int, quantite: int) -> bool:
         """ Met à jour la quantité pour un lien existant. """
         if quantite <= 0: quantite = 1 # Assurer quantité positive? Ou supprimer si 0?
         sql = "UPDATE GAMME_PIECE_TYPE SET quantite_theorique = %s WHERE gamme_id = %s AND piece_id = ?"
         try:
             cursor = execute_query(sql, (quantite, gamme_id, piece_id))
             success = cursor.rowcount > 0
             if success: logger.info(f"Qté mise à jour pour G={gamme_id}/P={piece_id}.")
             return success
         except DatabaseError as e:
             logger.error(f"Erreur DB màj qté Gamme/Pièce: {e}")
             raise

    def delete(self, gamme_id: int, piece_id: int) -> bool:
        """ Supprime un lien spécifique Gamme/Pièce. """
        sql = "DELETE FROM GAMME_PIECE_TYPE WHERE gamme_id = %s AND piece_id = ?"
        try:
            cursor = execute_query(sql, (gamme_id, piece_id))
            success = cursor.rowcount > 0
            if success: logger.info(f"Lien supprimé pour G={gamme_id}/P={piece_id}.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB delete lien Gamme/Pièce: {e}")
            raise

    def delete_by_gamme_id(self, gamme_id: int) -> int:
        """ Supprime tous les liens pièce pour une gamme. """
        sql = "DELETE FROM GAMME_PIECE_TYPE WHERE gamme_id = %s"
        try:
            cursor = execute_query(sql, (gamme_id,))
            count = cursor.rowcount
            if count > 0: logger.info(f"{count} liens pièce supprimés pour Gamme ID {gamme_id}.")
            return count
        except DatabaseError as e:
            logger.error(f"Erreur DB delete liens pièce pour Gamme ID {gamme_id}: {e}")
            raise