# gmao_app/app/data/repositories/technicien_repository.py
""" Repository pour l'entité Technicien. """
import logging
import psycopg2
from typing import Optional, List
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.technicien import Technicien

logger = logging.getLogger(__name__)

class TechnicienRepository:

    def add(self, tech: Technicien) -> Optional[int]:
        sql = """INSERT INTO TECHNICIEN (nom, prenom, qualification, contact, cout_horaire, equipe_id, actif)
                 VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_technicien"""
        params = (tech.nom, tech.prenom, tech.qualification, tech.contact, tech.cout_horaire, tech.equipe_id, 1 if tech.actif else 0)
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_technicien") if row else None
            logger.info(f"Technicien '{tech.nom_complet}' ajouté ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout technicien '{tech.nom_complet}'. FK equipe%s {e}")
            if 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Equipe {tech.equipe_id} invalide.") from e
            else:
                 raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout technicien '{tech.nom_complet}': {e}")
            raise

    def get_by_id(self, tech_id: int) -> Optional[Technicien]:
        sql = "SELECT * FROM TECHNICIEN WHERE id_technicien = %s"
        try:
            row = fetch_one(sql, (tech_id,))
            return Technicien.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get technicien ID {tech_id}: {e}")
            raise

    def get_all(self, include_inactive: bool = False) -> List[Technicien]:
        sql = "SELECT * FROM TECHNICIEN"
        params = []
        if not include_inactive:
            sql += " WHERE actif = 1"
            # params.append(1) # Pas besoin de param si valeur fixe
        sql += " ORDER BY nom, prenom"
        try:
            rows = fetch_all(sql) # fetch_all accepte params vide
            return [Technicien.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get all techniciens: {e}")
            raise

    def get_all_active(self) -> List[Technicien]:
        """Retourne la liste des techniciens actifs uniquement."""
        return self.get_all(include_inactive=False)

    def update(self, tech: Technicien) -> bool:
        if tech.id_technicien is None: return False
        sql = """UPDATE TECHNICIEN SET nom=%s, prenom=%s, qualification=%s, contact=%s, cout_horaire=%s, equipe_id=%s, actif=%s
                 WHERE id_technicien = %s"""
        params = (tech.nom, tech.prenom, tech.qualification, tech.contact, tech.cout_horaire, tech.equipe_id, 1 if tech.actif else 0, tech.id_technicien)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Technicien ID {tech.id_technicien} mis à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj tech ID {tech.id_technicien}. FK equipe%s {e}")
            if 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Equipe {tech.equipe_id} invalide.") from e
            else:
                 raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update tech ID {tech.id_technicien}: {e}")
            raise

    def delete(self, tech_id: int) -> bool:
        # ATTENTION: La suppression échouera si le technicien est référencé par :
        # - EQUIPE.responsable_id (mais FK est ON DELETE SET NULL, donc OK)
        # - UTILISATEUR.technicien_id (mais FK est ON DELETE SET NULL, donc OK)
        # - ORDRE_TRAVAIL.technicien_assigne_id (mais FK est ON DELETE SET NULL, donc OK)
        # - MAINTENANCE.technicien_id (FK est ON DELETE RESTRICT, bloquera ici!)
        sql = "DELETE FROM TECHNICIEN WHERE id_technicien = %s"
        try:
            cursor = execute_query(sql, (tech_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Technicien ID {tech_id} supprimé.")
            return success
        except psycopg2.IntegrityError as e:
             logger.error(f"Impossible de supprimer Technicien ID {tech_id}. Référencé dans MAINTENANCE%s {e}")
             raise DatabaseError("Impossible de supprimer ce technicien car il est référencé dans l'historique des maintenances.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB delete technicien ID {tech_id}: {e}")
            raise