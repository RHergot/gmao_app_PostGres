# gmao_app/app/data/repositories/mouvement_stock_repository.py
""" Repository pour l'entité MouvementStock. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.mouvement_stock import MouvementStock
from app.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class MouvementStockRepository:

    # Mapping des types de mouvements textuels vers les IDs numériques
    TYPE_MOUVEMENT_MAPPING = {
        'ENTREE': 1,
        'SORTIE': 2,
        'AJUSTEMENT': 3,
        'INVENTAIRE': 4
    }

    def add(self, mvt: MouvementStock) -> Optional[int]:
        """ Ajoute un nouveau mouvement de stock à la base de données. """
        
        # Convertir le type de mouvement textuel en ID numérique
        type_mouvement_id = self.TYPE_MOUVEMENT_MAPPING.get(mvt.type_mouvement)
        if type_mouvement_id is None:
            raise ValueError(f"Type de mouvement invalide: {mvt.type_mouvement}. Types valides: {list(self.TYPE_MOUVEMENT_MAPPING.keys())}")
        
        sql = """INSERT INTO MOUVEMENT_STOCK (piece_id, type_mouvement_id, quantite,
                                             date_mouvement, commentaire, utilisateur_id,
                                             stock_avant, stock_apres, valide, statut_mouvement)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
        params = (
            mvt.piece_id,
            type_mouvement_id,  # Utiliser l'ID numérique au lieu de la chaîne
            mvt.quantite,
            mvt.date_mouvement,
            mvt.raison,  # Sera mappé vers commentaire
            mvt.user_id,  # Sera mappé vers utilisateur_id
            mvt.stock_avant,
            mvt.stock_apres,
            True,  # valide par défaut
            'CONFIRME'  # statut_mouvement par défaut
        )
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql + " RETURNING id", params)
                row = cursor.fetchone()
            new_id = row['id'] if row else None
            logger.info(f"Mouvement de stock ID {new_id} ajouté pour pièce ID {mvt.piece_id} (Type: {mvt.type_mouvement}, Qte: {mvt.quantite}).")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.error(f"Erreur d'intégrité ajout mouvement stock pour pièce ID {mvt.piece_id}: {e}. Vérifier FK (piece_id, utilisateur_id)%s")
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
    # - get_by_utilisateur_id
    # - get_by_date_range
    # - ... etc.
