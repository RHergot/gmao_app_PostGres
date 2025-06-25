# gmao_app/app/data/repositories/fournisseur_repository.py
""" Repository pour l'entité Fournisseur. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.fournisseur import Fournisseur

logger = logging.getLogger(__name__)

class FournisseurRepository:

    def add(self, f: Fournisseur) -> Optional[int]:
        sql = """INSERT INTO FOURNISSEUR (nom, contact, adresse, telephone, email,
                                    delai_livraison_moyen_j, devise, note_qualite)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        params = (f.nom, f.contact, f.adresse, f.telephone, f.email,
                  f.delai_livraison_moyen_j, f.devise, f.note_qualite)
        try:
            from app.data.database import db_cursor
            with db_cursor() as cursor:
                cursor.execute(sql + " RETURNING id_fournisseur", params)
                row = cursor.fetchone()
            new_id = row['id_fournisseur'] if row else None
            logger.info(f"Fournisseur '{f.nom}' ajouté ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout fournisseur '{f.nom}'. Nom unique? {e}")
            raise DatabaseError(f"Nom fournisseur '{f.nom}' existe déjà.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout fournisseur '{f.nom}': {e}")
            raise

    def get_by_id(self, f_id: int) -> Optional[Fournisseur]:
        sql = "SELECT * FROM FOURNISSEUR WHERE id_fournisseur = %s"
        try:
            row = fetch_one(sql, (f_id,))
            return Fournisseur.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get fournisseur ID {f_id}: {e}")
            raise

    def get_all(self) -> List[Fournisseur]:
        sql = "SELECT * FROM FOURNISSEUR ORDER BY nom"
        try:
            rows = fetch_all(sql)
            return [Fournisseur.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get all fournisseurs: {e}")
            raise

    def update(self, f: Fournisseur) -> bool:
        if f.id_fournisseur is None: return False
        sql = """UPDATE FOURNISSEUR SET nom=%s, contact=%s, adresse=%s, telephone=%s, email=%s,
                                     delai_livraison_moyen_j=%s, devise=%s, note_qualite=%s
                 WHERE id_fournisseur = %s"""
        params = (f.nom, f.contact, f.adresse, f.telephone, f.email,
                  f.delai_livraison_moyen_j, f.devise, f.note_qualite, f.id_fournisseur)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Fournisseur ID {f.id_fournisseur} mis à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj fournisseur ID {f.id_fournisseur}. Nom unique? {e}")
            raise DatabaseError(f"Nom fournisseur '{f.nom}' déjà utilisé.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update fournisseur ID {f.id_fournisseur}: {e}")
            raise

    def delete(self, f_id: int) -> bool:
        # FK dans PIECE est ON DELETE SET NULL, la suppression est possible
        # FK dans COMMANDE (future) sera probablement RESTRICT ou SET NULL
        sql = "DELETE FROM FOURNISSEUR WHERE id_fournisseur = %s"
        try:
            # Vérifier si des commandes ouvertes existent pour ce fournisseur? (Logique service)
            cursor = execute_query(sql, (f_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Fournisseur ID {f_id} supprimé.")
            return success
        except psycopg2.IntegrityError as e:
            # Arrive si une FK (ex: Commande) est RESTRICT
             logger.error(f"Impossible supprimer Fournisseur ID {f_id}. Référencé ailleurs (Commandes?): {e}")
             raise DatabaseError("Impossible de supprimer ce fournisseur car il est référencé (ex: par des commandes).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete fournisseur ID {f_id}: {e}")
            raise