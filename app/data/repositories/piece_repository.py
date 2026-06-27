# gmao_app/app/data/repositories/piece_repository.py
""" Repository pour l'entité Pièce. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.piece import Piece

logger = logging.getLogger(__name__)

class PieceRepository:

    def add(self, p: Piece) -> Optional[int]:
        sql = """INSERT INTO PIECE (reference, nom, fournisseur_pref_id, prix_unitaire,
                                 stock_alerte, stock_actuel, stock_reserve, unite,
                                 categorie, emplacement_stockage, statut)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                  p.stock_alerte, p.stock_actuel, p.stock_reserve, p.unite,
                  p.categorie, p.emplacement_stockage, p.statut)
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql + " RETURNING id_piece", params)
                row = cursor.fetchone()
            new_id = row['id_piece'] if row else None
            logger.info(f"Pièce '{p.nom}' (Ref:{p.reference}) ajoutée ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout pièce '{p.nom}'. Ref unique, FK Fournisseur: {e}")
            if 'PIECE.reference' in str(e):
                raise DatabaseError(f"Référence pièce '{p.reference}' existe déjà.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Fournisseur préféré {p.fournisseur_pref_id} invalide.") from e
            else:
                 raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout pièce '{p.nom}': {e}")
            raise

    def get_by_id(self, p_id: int) -> Optional[Piece]:
        sql = "SELECT * FROM PIECE WHERE id_piece = %s"
        try:
            row = fetch_one(sql, (p_id,))
            return Piece.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get pièce ID {p_id}: {e}")
            raise

    def get_by_reference(self, reference: str) -> Optional[Piece]:
        """ Récupère une pièce par sa référence (unique). """
        sql = "SELECT * FROM PIECE WHERE reference = %s"
        try:
            row = fetch_one(sql, (reference,))
            return Piece.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get pièce ref '{reference}': {e}")
            raise

    def get_by_ids(self, ids: List[int]) -> List[Piece]:
        """ Récupère plusieurs pièces par leurs IDs en une seule requête. """
        if not ids:
            return []
        sql = "SELECT * FROM PIECE WHERE id_piece = ANY(%s)"
        try:
            rows = fetch_all(sql, (ids,))
            return [Piece.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get pièces par IDs {ids}: {e}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None,
                 sort_by: str = "nom", sort_desc: bool = False) -> List[Piece]:
        """ Récupère toutes les pièces avec filtres/tri. """
        sql = "SELECT p.* FROM PIECE p " # Alias pour futures jointures (ex: nom fournisseur)
        where_clauses = []
        params = []
        # TODO: Implémenter la logique de filtres (categorie, statut, fournisseur_pref_id...)
        # ... (similaire à MachineRepository)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # Tri
        valid_sort = ['id_piece', 'reference', 'nom', 'prix_unitaire', 'stock_actuel', 'unite', 'categorie', 'statut']
        sort_col = sort_by if sort_by in valid_sort else 'nom'
        order = "DESC" if sort_desc else "ASC"
        sql += f" ORDER BY p.{sort_col} {order}"

        try:
            rows = fetch_all(sql, tuple(params))
            return [Piece.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get all pieces: {e}")
            raise

    def update(self, p: Piece) -> bool:
        """ Met à jour une pièce existante. """
        if p.id_piece is None: return False
        sql = """UPDATE PIECE SET reference=%s, nom=%s, fournisseur_pref_id=%s, prix_unitaire=%s,
                                stock_alerte=%s, stock_actuel=%s, stock_reserve=%s, unite=%s,
                                categorie=%s, emplacement_stockage=%s, statut=%s
                 WHERE id_piece = %s"""
        params = (p.reference, p.nom, p.fournisseur_pref_id, p.prix_unitaire,
                  p.stock_alerte, p.stock_actuel, p.stock_reserve, p.unite,
                  p.categorie, p.emplacement_stockage, p.statut, p.id_piece)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Pièce ID {p.id_piece} mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
             logger.warning(f"Échec màj pièce ID {p.id_piece}. Ref unique, FK Fournisseur: {e}")
             if 'PIECE.reference' in str(e):
                 raise DatabaseError(f"Référence pièce '{p.reference}' déjà utilisée.") from e
             elif 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Fournisseur préféré {p.fournisseur_pref_id} invalide.") from e
             else:
                 raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update pièce ID {p.id_piece}: {e}")
            raise

    def update_stock_level(self, piece_id: int, new_stock_actuel: int, cursor=None) -> bool:
        """ Met à jour uniquement le stock actuel et la date de mise à jour d'une pièce.
        Args:
            piece_id: ID de la pièce.
            new_stock_actuel: Nouveau niveau de stock.
            cursor: Curseur de transaction optionnel. Si fourni, utilisé sans commit/rollback.
        """
        sql = "UPDATE PIECE SET stock_actuel = %s, updated_at = CURRENT_TIMESTAMP WHERE id_piece = %s"
        params = (new_stock_actuel, piece_id)
        try:
            if cursor is not None:
                cursor.execute(sql, params)
            else:
                execute_query(sql, params)
            logger.info(f"Niveau de stock mis à jour pour pièce ID {piece_id} à {new_stock_actuel}.")
            return True
        except DatabaseError as e:
            logger.error(f"Erreur DB mise à jour stock pour pièce ID {piece_id}: {e}")
            return False

    def delete(self, p_id: int) -> bool:
        """ Supprime une pièce par son ID. """
        # Attention: échouera si la pièce est dans LIGNE_COMMANDE (future)
        # ou INTERVENTION_PIECE (future) à cause des contraintes RESTRICT probables.
        sql = "DELETE FROM PIECE WHERE id_piece = %s"
        try:
            cursor = execute_query(sql, (p_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Pièce ID {p_id} supprimée.")
            return success
        except psycopg2.IntegrityError as e:
             logger.error(f"Impossible supprimer Pièce ID {p_id}. Référencée (Cmd/Intervention): {e}")
             raise DatabaseError("Impossible de supprimer cette pièce car elle est référencée (commandes, interventions...).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete pièce ID {p_id}: {e}")
            raise

    # --- Méthodes spécifiques au stock (seront appelées par le StockService) ---

    def update_stock(self, piece_id: int, change_quantity: int) -> bool:
        """
        Met à jour le stock actuel d'une pièce.
        Utilise une requête atomique pour éviter les problèmes de concurrence.
        'change_quantity' peut être positif (ajout) ou négatif (retrait).
        Retourne True si la mise à jour a réussi (stock suffisant si retrait).
        """
        logger.info(f"Tentative màj stock pour Pièce ID {piece_id}, changement: {change_quantity}")
        if change_quantity == 0: return True # Rien à faire

        sql_update = """
            UPDATE PIECE
            SET stock_actuel = stock_actuel + %s
            WHERE id_piece = %s
        """
        # Si c'est un retrait, s'assurer que le stock ne devient pas négatif
        # (on pourrait ajouter une contrainte CHECK(stock_actuel >= 0) dans le schéma)
        if change_quantity < 0:
            sql_update += " AND stock_actuel >= %s" # Vérifier stock suffisant
            params = (change_quantity, piece_id, abs(change_quantity))
        else:
             params = (change_quantity, piece_id)

        try:
            cursor = execute_query(sql_update, params)
            if cursor.rowcount > 0:
                logger.info(f"Stock pour Pièce ID {piece_id} mis à jour avec succès ({change_quantity:+}).")
                return True
            else:
                # Si rowcount == 0 pour un retrait, c'est que le stock était insuffisant
                if change_quantity < 0:
                    logger.warning(f"Stock insuffisant pour Pièce ID {piece_id} (retrait demandé: {abs(change_quantity)}).")
                else: # Si rowcount == 0 pour un ajout, c'est que l'ID n'existe pas
                     logger.warning(f"Pièce ID {piece_id} non trouvée pour mise à jour de stock.")
                return False
        except DatabaseError as e:
             logger.error(f"Erreur DB màj stock pièce ID {piece_id}: {e}")
             # Remonter l'erreur pourrait être mieux ici
             return False

    def get_pieces_below_alert_threshold(self) -> List[Piece]:
         """ Récupère les pièces dont le stock actuel est <= au seuil d'alerte. """
         sql = "SELECT * FROM PIECE WHERE stock_actuel <= stock_alerte AND stock_alerte > 0 ORDER BY nom"
         try:
             rows = fetch_all(sql)
             return [Piece.from_db_row(row) for row in rows if row]
         except DatabaseError as e:
             logger.error(f"Erreur DB get pièces en alerte: {e}")
             raise