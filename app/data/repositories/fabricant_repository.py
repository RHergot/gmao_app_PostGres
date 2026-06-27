# gmao_app/app/data/repositories/fabricant_repository.py
""" Repository pour l'entité Fabricant. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.fabricant import Fabricant

logger = logging.getLogger(__name__)

class FabricantRepository:

    def add(self, fabricant: Fabricant) -> Optional[int]:
        """ Ajoute un nouveau fabricant. Retourne son ID. """
        sql = "INSERT INTO FABRICANT (nom, contact, site_web, support_technique) VALUES (%s, %s, %s, %s) RETURNING id_fabricant"
        params = (fabricant.nom, fabricant.contact, fabricant.site_web, fabricant.support_technique)
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_fabricant") if row else None
            logger.info(f"Fabricant '{fabricant.nom}' ajouté avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Impossible d'ajouter fabricant '{fabricant.nom}'. Contrainte unique 'nom': {e}")
            raise DatabaseError(f"Le nom de fabricant '{fabricant.nom}' existe déjà.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout fabricant '{fabricant.nom}': {e}")
            raise

    def get_by_id(self, fabricant_id: int) -> Optional[Fabricant]:
        """ Récupère un fabricant par son ID. """
        sql = "SELECT * FROM FABRICANT WHERE id_fabricant = %s"
        try:
            row = fetch_one(sql, (fabricant_id,))
            return Fabricant.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_id fabricant {fabricant_id}: {e}")
            raise

    def get_by_name(self, name: str) -> Optional[Fabricant]:
        """ Récupère un fabricant par son nom (unique). """
        sql = "SELECT * FROM FABRICANT WHERE nom = %s"
        try:
            row = fetch_one(sql, (name,))
            return Fabricant.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_name fabricant '{name}': {e}")
            raise

    def get_all(self) -> List[Fabricant]:
        """ Récupère tous les fabricants. """
        sql = "SELECT * FROM FABRICANT ORDER BY nom"
        try:
            rows = fetch_all(sql)
            return [Fabricant.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get_all fabricants: {e}")
            raise

    def update(self, fabricant: Fabricant) -> bool:
        """ Met à jour un fabricant existant. """
        if fabricant.id_fabricant is None: return False
        sql = """UPDATE FABRICANT SET nom = %s, contact = %s, site_web = %s, support_technique = %s
                 WHERE id_fabricant = %s"""
        params = (fabricant.nom, fabricant.contact, fabricant.site_web, fabricant.support_technique, fabricant.id_fabricant)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Fabricant ID {fabricant.id_fabricant} mis à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj fabricant ID {fabricant.id_fabricant}. Contrainte unique 'nom': {e}")
            raise DatabaseError(f"Le nom de fabricant '{fabricant.nom}' est déjà utilisé.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update fabricant ID {fabricant.id_fabricant}: {e}")
            raise

    def delete(self, fabricant_id: int) -> bool:
        """ Supprime un fabricant. """
        # La contrainte FK sur MACHINE est ON DELETE RESTRICT
        sql = "DELETE FROM FABRICANT WHERE id_fabricant = %s"
        try:
            cursor = execute_query(sql, (fabricant_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Fabricant ID {fabricant_id} supprimé.")
            return success
        except psycopg2.IntegrityError as e:
            logger.error(f"Impossible de supprimer fabricant ID {fabricant_id}. Des machines y sont liées: {e}")
            raise DatabaseError("Impossible de supprimer ce fabricant car des machines y sont associées.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete fabricant ID {fabricant_id}: {e}")
            raise