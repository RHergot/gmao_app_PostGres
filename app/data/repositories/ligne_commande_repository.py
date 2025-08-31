# gmao_app/app/data/repositories/ligne_commande_repository.py
""" Repository pour l'entité Ligne de Commande. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.ligne_commande import LigneCommande
from datetime import date
from app.utils.helpers import format_iso_date # Assurez-vous que cet helper existe


logger = logging.getLogger(__name__)

class LigneCommandeRepository:

    def add(self, ligne: LigneCommande) -> Optional[int]:
        """ Ajoute une nouvelle ligne de commande à la base de données. """
        sql = """INSERT INTO LIGNE_COMMANDE (commande_id, piece_id, description_libre,
                                           quantite_commandee, prix_unitaire_ht,
                                           quantite_recue, date_reception, statut_ligne)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_ligne"""
        params = (
            ligne.commande_id,
            ligne.piece_id,
            ligne.description_libre,
            ligne.quantite_commandee,
            ligne.prix_unitaire_ht,
            ligne.quantite_recue,
            format_iso_date(ligne.date_reception),
            ligne.statut_ligne
        )
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
            new_id = row['id_ligne'] if row else None
            if new_id is not None:
                 logger.info(f"Ligne de commande (ID:{new_id}) ajoutée à commande ID {ligne.commande_id} pour pièce ID {ligne.piece_id}.")
                 return new_id
            else:
                 logger.error(f"Erreur lors récupération ID ligne commande pour Cmd ID {ligne.commande_id}, Pièce ID {ligne.piece_id}")
                 return None
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout ligne commande pour Cmd ID {ligne.commande_id}. Contrainte violée: {e}")
            if 'FOREIGN KEY constraint failed' in str(e):
                 # Identifier quelle clé a échoué peut être complexe
                 raise DatabaseError(f"ID Commande ({ligne.commande_id}) ou Pièce ({ligne.piece_id}) invalide.") from e
            # Gérer contrainte UNIQUE(commande_id, piece_id) si ajoutée
            # elif 'UNIQUE constraint failed: LIGNE_COMMANDE.commande_id, LIGNE_COMMANDE.piece_id' in str(e):
            #     raise DatabaseError(f"La pièce ID {ligne.piece_id} existe déjà sur la commande ID {ligne.commande_id}.") from e
            else:
                 raise DatabaseError(f"Contrainte d'intégrité violée lors ajout ligne commande: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout ligne commande pour Cmd ID {ligne.commande_id}: {e}")
            raise

    def get_by_id(self, ligne_id: int) -> Optional[LigneCommande]:
        """ Récupère une ligne de commande par son ID, avec infos pièce. """
        sql = (
            "SELECT lc.*, p.reference AS piece_reference, p.nom AS piece_nom "
            "FROM LIGNE_COMMANDE lc "
            "LEFT JOIN PIECE p ON lc.piece_id = p.id_piece "
            "WHERE lc.id_ligne = %s"
        )
        try:
            row = fetch_one(sql, (ligne_id,))
            return LigneCommande.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get ligne commande ID {ligne_id}: {e}")
            raise

    def get_by_commande_id(self, commande_id: int) -> List[dict]: # Retourne des Rows
        """ Récupère toutes les lignes d'une commande spécifique, avec infos pièce. """
        logger.debug(f"Récupération lignes pour commande ID {commande_id} avec infos pièce...")
        sql = """SELECT lc.*, p.reference AS piece_reference, p.nom AS piece_nom
                 FROM LIGNE_COMMANDE lc
                 LEFT JOIN PIECE p ON lc.piece_id = p.id_piece
                 WHERE lc.commande_id = %s
                 ORDER BY lc.id_ligne
              """
        try:
            rows = fetch_all(sql, (commande_id,))
            logger.debug(f"{len(rows)} lignes récupérées pour commande ID {commande_id}.")
            return rows # Retourner les lignes brutes enrichies
        except DatabaseError as e:
            logger.error(f"Erreur DB get lignes pour commande ID {commande_id}: {e}")
            raise # Propager
        except Exception as e:
             logger.exception(f"Erreur inattendue get lignes commande ID {commande_id}: {e}")
             raise DatabaseError("Erreur serveur récupération lignes commande.") from e

    def update(self, ligne: LigneCommande) -> bool:
        """ Met à jour une ligne de commande existante. """
        if ligne.id_ligne is None:
             logger.warning("Tentative de mise à jour d'une ligne de commande sans ID.")
             return False

        sql = """UPDATE LIGNE_COMMANDE SET
                    commande_id=%s, piece_id=%s, description_libre=%s,
                    quantite_commandee=%s, prix_unitaire_ht=%s, quantite_recue=%s,
                    date_reception=%s, statut_ligne=%s
                 WHERE id_ligne = %s"""
        params = (
            ligne.commande_id,
            ligne.piece_id,
            ligne.description_libre,
            ligne.quantite_commandee,
            ligne.prix_unitaire_ht,
            ligne.quantite_recue,
            format_iso_date(ligne.date_reception),
            ligne.statut_ligne,
            ligne.id_ligne # Pour le WHERE
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success:
                 logger.info(f"Ligne de commande ID {ligne.id_ligne} mise à jour.")
            else:
                 logger.warning(f"Aucune ligne de commande trouvée avec ID {ligne.id_ligne} pour mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
             logger.warning(f"Échec màj ligne commande ID {ligne.id_ligne}. Contrainte violée: {e}")
             if 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Commande ({ligne.commande_id}) ou Pièce ({ligne.piece_id}) invalide.") from e
             # Gérer contrainte UNIQUE(commande_id, piece_id) si ajoutée
             else:
                 raise DatabaseError(f"Contrainte d'intégrité violée lors màj ligne commande ID {ligne.id_ligne}: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update ligne commande ID {ligne.id_ligne}: {e}")
            raise

    def update_reception(self, ligne_id: int, quantite_recue_ajout: int, date_reception: date) -> bool:
         """
         Met à jour la quantité reçue et la date de dernière réception pour une ligne.
         NOTE: La mise à jour du statut_ligne (Partielle/Recue) est laissée au Service,
               car il a besoin de connaître quantite_commandee vs nouvelle quantite_recue totale.
         """
         if quantite_recue_ajout <= 0:
             logger.warning(f"Tentative de réception d'une quantité nulle ou négative ({quantite_recue_ajout}) pour ligne ID {ligne_id}.")
             return False # Ou lever une erreur?

         sql = """UPDATE LIGNE_COMMANDE
                  SET quantite_recue = quantite_recue + %s,
                      date_reception = %s
                  WHERE id_ligne = %s"""
         params = (quantite_recue_ajout, format_iso_date(date_reception), ligne_id)

         try:
             cursor = execute_query(sql, params)
             success = cursor.rowcount > 0
             if success:
                 logger.info(f"{quantite_recue_ajout} unités reçues pour ligne ID {ligne_id} à la date {format_iso_date(date_reception)}.")
             else:
                  logger.warning(f"Aucune ligne de commande trouvée avec ID {ligne_id} pour màj réception.")
             return success
         except psycopg2.IntegrityError as e:
             # Pourrait arriver si on ajoute une contrainte CHECK(quantite_recue <= quantite_commandee)? Peu probable.
             logger.error(f"Erreur d'intégrité lors de la réception pour ligne ID {ligne_id}: {e}")
             raise DatabaseError(f"Erreur d'intégrité lors de la réception pour ligne ID {ligne_id}") from e
         except DatabaseError as e:
             logger.error(f"Erreur DB update réception ligne ID {ligne_id}: {e}")
             raise

    def update_ligne_statut(self, ligne_id: int, new_statut: str) -> bool:
        """ Met à jour uniquement le statut d'une ligne. """
        sql = "UPDATE LIGNE_COMMANDE SET statut_ligne = %s WHERE id_ligne = %s"
        params = (new_statut, ligne_id)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success:
                 logger.info(f"Statut de la ligne ID {ligne_id} mis à jour à '{new_statut}'.")
            else:
                 logger.warning(f"Aucune ligne trouvée avec ID {ligne_id} pour màj statut.")
            return success
        except DatabaseError as e:
             logger.error(f"Erreur DB màj statut ligne ID {ligne_id}: {e}")
             raise

    def delete(self, ligne_id: int) -> bool:
        """ Supprime une ligne de commande par son ID. """
        sql = "DELETE FROM LIGNE_COMMANDE WHERE id_ligne = %s"
        try:
            cursor = execute_query(sql, (ligne_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Ligne de commande ID {ligne_id} supprimée.")
            else:
                logger.warning(f"Aucune ligne de commande trouvée avec ID {ligne_id} pour suppression.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB delete ligne commande ID {ligne_id}: {e}")
            raise

    def delete_by_commande_id(self, commande_id: int) -> int:
         """ Supprime toutes les lignes associées à une commande et retourne le nombre de lignes supprimées. """
         sql = "DELETE FROM LIGNE_COMMANDE WHERE commande_id = %s"
         try:
             cursor = execute_query(sql, (commande_id,))
             count = cursor.rowcount
             if count > 0:
                 logger.info(f"{count} lignes supprimées pour commande ID {commande_id}.")
             return count
         except DatabaseError as e:
             logger.error(f"Erreur DB delete lignes pour commande ID {commande_id}: {e}")
             raise