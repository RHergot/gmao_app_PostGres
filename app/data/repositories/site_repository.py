# gmao_app/app/data/repositories/site_repository.py
""" Repository pour l'entité Site. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.site import Site

logger = logging.getLogger(__name__)

class SiteRepository:

    def add(self, site: Site) -> Optional[int]:
        """ Ajoute un nouveau site. Retourne son ID. """
        sql = "INSERT INTO SITE (nom, adresse, ville, pays, contact_principal) VALUES (%s, %s, %s, %s, %s) RETURNING id_site"
        params = (site.nom, site.adresse, site.ville, site.pays, site.contact_principal)
        try:
            row = fetch_one(sql, params)
            new_id = row['id_site'] if row else None
            logger.info(f"Site '{site.nom}' ajouté avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Impossible d'ajouter le site '{site.nom}'. Contrainte unique 'nom' violée: {e}")
            raise DatabaseError(f"Le nom de site '{site.nom}' existe déjà.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout site '{site.nom}': {e}")
            raise

    def get_by_id(self, site_id: int) -> Optional[Site]:
        """ Récupère un site par son ID. """
        sql = "SELECT * FROM SITE WHERE id_site = %s"
        try:
            row = fetch_one(sql, (site_id,))
            return Site.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_id site {site_id}: {e}")
            raise

    def get_by_name(self, name: str) -> Optional[Site]:
        """ Récupère un site par son nom (unique). """
        sql = "SELECT * FROM SITE WHERE nom = %s"
        try:
            row = fetch_one(sql, (name,))
            return Site.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get_by_name site '{name}': {e}")
            raise

    def get_all(self) -> List[Site]:
        """ Récupère tous les sites. """
        sql = "SELECT * FROM SITE ORDER BY nom"
        try:
            rows = fetch_all(sql)
            return [Site.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get_all sites: {e}")
            raise

    def update(self, site: Site) -> bool:
        """ Met à jour un site existant. """
        if site.id_site is None: return False
        sql = """UPDATE SITE SET nom = %s, adresse = %s, ville = %s, pays = %s, contact_principal = %s
                 WHERE id_site = %s"""
        params = (site.nom, site.adresse, site.ville, site.pays, site.contact_principal, site.id_site)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Site ID {site.id_site} mis à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj site ID {site.id_site}. Contrainte unique 'nom' violée: {e}")
            raise DatabaseError(f"Le nom de site '{site.nom}' est déjà utilisé par un autre site.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update site ID {site.id_site}: {e}")
            raise

    def delete(self, site_id: int) -> bool:
        """ Supprime un site. """
        # Attention: vérifier les contraintes (machines liées) avant de supprimer
        # La contrainte FOREIGN KEY sur MACHINE est ON DELETE RESTRICT par défaut dans notre schéma,
        # donc la suppression échouera si des machines sont liées.
        sql = "DELETE FROM SITE WHERE id_site = %s"
        try:
            cursor = execute_query(sql, (site_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Site ID {site_id} supprimé.")
            return success
        except psycopg2.IntegrityError as e:
            logger.error(f"Impossible de supprimer le site ID {site_id}. Des machines y sont probablement liées: {e}")
            raise DatabaseError(f"Impossible de supprimer ce site car des machines y sont associées.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete site ID {site_id}: {e}")
            raise