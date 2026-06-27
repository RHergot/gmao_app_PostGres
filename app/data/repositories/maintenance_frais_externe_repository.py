# gmao_app/app/data/repositories/maintenance_frais_externe_repository.py
""" Repository pour l'entité MaintenanceFraisExterne. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any

from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.maintenance_frais_externe import MaintenanceFraisExterne

logger = logging.getLogger(__name__)

class MaintenanceFraisExterneRepository:
    """Repository pour gérer les frais externes (pièces hors stock, déplacements, etc.) liés à une maintenance."""

    def add(self, frais: MaintenanceFraisExterne) -> Optional[int]:
        """Ajoute un nouveau frais externe pour une maintenance. Retourne l'ID généré si succès."""
        sql = """
            INSERT INTO MAINTENANCE_FRAIS_EXTERNE (
                maintenance_id, type_frais, description, montant, quantite,
                reference_piece, fournisseur, facture_reference
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_frais
        """
        params = (
            frais.maintenance_id,
            frais.type_frais,
            frais.description,
            frais.montant,
            frais.quantite,
            frais.reference_piece,
            frais.fournisseur,
            frais.facture_reference
        )
        try:
            row = fetch_one(sql, params)
            new_id = row['id_frais'] if row else None
            logger.info(f"Frais externe ajouté pour maintenance ID {frais.maintenance_id}. ID frais: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.error(f"Échec ajout frais pour maintenance {frais.maintenance_id}. FK invalide: {e}")
            raise DatabaseError("Référence maintenance invalide ou contrainte violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout frais externe: {e}")
            raise

    def get_by_id(self, id_frais: int) -> Optional[MaintenanceFraisExterne]:
        """Récupère un frais externe par son ID."""
        sql = "SELECT * FROM MAINTENANCE_FRAIS_EXTERNE WHERE id_frais = %s"
        try:
            row = fetch_one(sql, (id_frais,))
            return MaintenanceFraisExterne.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get frais ID {id_frais}: {e}")
            raise

    def get_by_maintenance_id(self, maintenance_id: int) -> List[MaintenanceFraisExterne]:
        """Récupère tous les frais externes pour une maintenance donnée."""
        sql = "SELECT * FROM MAINTENANCE_FRAIS_EXTERNE WHERE maintenance_id = %s ORDER BY id_frais"
        try:
            rows = fetch_all(sql, (maintenance_id,))
            return [MaintenanceFraisExterne.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get frais pour maintenance ID {maintenance_id}: {e}")
            raise

    def get_by_type(self, type_frais: str) -> List[MaintenanceFraisExterne]:
        """Récupère tous les frais d'un type donné."""
        sql = "SELECT * FROM MAINTENANCE_FRAIS_EXTERNE WHERE type_frais = %s ORDER BY maintenance_id DESC"
        try:
            rows = fetch_all(sql, (type_frais,))
            return [MaintenanceFraisExterne.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get frais de type {type_frais}: {e}")
            raise

    def get_summary_by_maintenance(self, maintenance_id: int) -> Dict[str, float]:
        """Récupère un résumé des frais par type pour une maintenance donnée."""
        sql = """
            SELECT type_frais, SUM(montant * quantite) as total
            FROM MAINTENANCE_FRAIS_EXTERNE 
            WHERE maintenance_id = %s 
            GROUP BY type_frais
        """
        try:
            rows = fetch_all(sql, (maintenance_id,))
            return {row['type_frais']: float(row['total']) for row in rows if row}
        except DatabaseError as e:
            logger.error(f"Erreur DB get résumé frais pour maintenance ID {maintenance_id}: {e}")
            raise

    def update(self, frais: MaintenanceFraisExterne) -> bool:
        """Met à jour un frais externe. Retourne True si succès."""
        if not frais.id_frais:
            logger.error("Tentative de mise à jour d'un frais sans ID")
            return False

        sql = """
            UPDATE MAINTENANCE_FRAIS_EXTERNE SET 
                type_frais = %s, 
                description = %s, 
                montant = %s, 
                quantite = %s, 
                reference_piece = %s,
                fournisseur = %s,
                facture_reference = %s
            WHERE id_frais = %s
        """
        params = (
            frais.type_frais,
            frais.description,
            frais.montant,
            frais.quantite,
            frais.reference_piece,
            frais.fournisseur,
            frais.facture_reference,
            frais.id_frais
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Frais ID {frais.id_frais} mis à jour avec succès")
            else:
                logger.warning(f"Aucun frais trouvé avec l'ID {frais.id_frais} pour mise à jour")
            return success
        except psycopg2.IntegrityError as e:
            logger.error(f"Échec mise à jour frais ID {frais.id_frais}. Contrainte violée: {e}")
            raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB mise à jour frais: {e}")
            raise

    def delete(self, id_frais: int) -> bool:
        """Supprime un frais externe. Retourne True si succès."""
        sql = "DELETE FROM MAINTENANCE_FRAIS_EXTERNE WHERE id_frais = %s"
        try:
            cursor = execute_query(sql, (id_frais,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Frais ID {id_frais} supprimé avec succès")
            else:
                logger.warning(f"Aucun frais trouvé avec l'ID {id_frais} pour suppression")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB suppression frais ID {id_frais}: {e}")
            raise

    def delete_by_maintenance_id(self, maintenance_id: int) -> int:
        """Supprime tous les frais d'une maintenance. Retourne le nombre supprimé."""
        sql = "DELETE FROM MAINTENANCE_FRAIS_EXTERNE WHERE maintenance_id = %s"
        try:
            cursor = execute_query(sql, (maintenance_id,))
            count = cursor.rowcount
            logger.info(f"{count} frais supprimés pour maintenance ID {maintenance_id}")
            return count
        except DatabaseError as e:
            logger.error(f"Erreur DB suppression frais pour maintenance ID {maintenance_id}: {e}")
            raise