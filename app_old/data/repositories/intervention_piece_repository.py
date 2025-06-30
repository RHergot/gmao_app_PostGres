# gmao_app/app/data/repositories/intervention_piece_repository.py
""" Repository pour l'entité InterventionPiece. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.intervention_piece import InterventionPiece

logger = logging.getLogger(__name__)

class InterventionPieceRepository:

    def add(self, ip: InterventionPiece) -> Optional[int]:
        """ Ajoute un enregistrement de pièce utilisée lors d'une maintenance. """
        sql = """INSERT INTO INTERVENTION_PIECE (maintenance_id, piece_id, quantite, lot)
                 VALUES (%s, %s, %s, %s) RETURNING id"""
        params = (ip.maintenance_id, ip.piece_id, ip.quantite, ip.lot)
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
            new_id = row['id'] if row else None
            logger.info(f"Lien Pièce {ip.piece_id} (Qt: {ip.quantite}) ajouté pour Maint ID {ip.maintenance_id}. ID Lien: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.error(f"Échec ajout lien Pièce {ip.piece_id} / Maint {ip.maintenance_id}. FK invalide? {e}")
            raise DatabaseError("Référence Maintenance ou Pièce invalide.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout lien pièce/maint: {e}")
            raise

    def get_by_maintenance_id(self, maintenance_id: int) -> List[InterventionPiece]:
        """ Récupère toutes les pièces utilisées pour une maintenance donnée. """
        sql = "SELECT * FROM INTERVENTION_PIECE WHERE maintenance_id = %s ORDER BY id"
        try:
            rows = fetch_all(sql, (maintenance_id,))
            return [InterventionPiece.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get pièces pour maint ID {maintenance_id}: {e}")
            raise

    def get_by_piece_id(self, piece_id: int) -> List[InterventionPiece]:
        """ Récupère toutes les interventions où une pièce donnée a été utilisée. """
        sql = "SELECT * FROM INTERVENTION_PIECE WHERE piece_id = %s ORDER BY id DESC" # Plus récentes d'abord?
        try:
            rows = fetch_all(sql, (piece_id,))
            return [InterventionPiece.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get interventions pour pièce ID {piece_id}: {e}")
            raise

    def delete_by_maintenance_id(self, maintenance_id: int) -> int:
        """ Supprime tous les liens pièce pour une maintenance donnée. Retourne le nb supprimé. """
        # Utile si on doit annuler/modifier un rapport de maintenance?
        sql = "DELETE FROM INTERVENTION_PIECE WHERE maintenance_id = %s"
        try:
            cursor = execute_query(sql, (maintenance_id,))
            count = cursor.rowcount
            if count > 0: logger.info(f"{count} liens pièce/maint supprimés pour Maint ID {maintenance_id}.")
            return count
        except DatabaseError as e:
            logger.error(f"Erreur DB delete liens pièce/maint pour Maint ID {maintenance_id}: {e}")
            raise

    # Pas d'update typiquement nécessaire pour cette table de liaison simple.
    # Si on change la quantité, on supprime l'ancienne ligne et on en crée une nouvelle?
    # Ou on ajoute une méthode update_quantity(id, new_quantity)?
    # Pour l'instant, on garde simple : ajout et récupération/suppression groupée.