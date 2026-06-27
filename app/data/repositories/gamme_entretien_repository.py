# gmao_app/app/data/repositories/gamme_entretien_repository.py
""" Repository pour l'entité GammeEntretien. """
import logging
import psycopg2
from app.data.database import db_cursor
from typing import Optional, List
from datetime import date, datetime
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.gamme_entretien import GammeEntretien

logger = logging.getLogger(__name__)

class GammeEntretienRepository:

    def _format_date(self, d: Optional[date]) -> Optional[str]:
        """ Formate date en string ISO ou None. """
        return d.isoformat() if d else None

    def add(self, gamme: GammeEntretien) -> Optional[int]:
        """ Ajoute une nouvelle gamme. """
        sql = """INSERT INTO GAMME_ENTRETIEN (
                     description, type_entretien, periodicite_valeur, periodicite_unite,
                     instructions, date_derniere_realisation, prochaine_date_calculee, active,
                     type_machine_id, createur_id, duree_estimee_min, qualification_requise, priorite
                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 RETURNING id_gamme"""
        params = (
            gamme.description, gamme.type_entretien, gamme.periodicite_valeur, gamme.periodicite_unite,
            gamme.instructions, self._format_date(gamme.date_derniere_realisation),
            self._format_date(gamme.prochaine_date_calculee), 1 if gamme.active else 0,
            gamme.type_machine_id, gamme.createur_id, gamme.duree_estimee_min,
            gamme.qualification_requise, gamme.priorite
        )
        try:
            with db_cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
            new_id = row['id_gamme'] if row else None
            logger.info(f"GammeEntretien '{gamme.description}' ajoutée ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout Gamme '{gamme.description}'. Desc unique, FK: {e}")
            if 'GAMME_ENTRETIEN.description' in str(e):
                raise DatabaseError(f"Description gamme '{gamme.description}' existe déjà.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError("Référence Type Machine ou Créateur invalide.") from e
            else: raise DatabaseError("Contrainte intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout Gamme '{gamme.description}': {e}")
            raise

    def get_by_id(self, gamme_id: int) -> Optional[GammeEntretien]:
        sql = "SELECT * FROM GAMME_ENTRETIEN WHERE id_gamme = %s"
        try:
            row = fetch_one(sql, (gamme_id,))
            return GammeEntretien.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get gamme ID {gamme_id}: {e}")
            raise

    def get_all(self, active_only: bool = True) -> List[GammeEntretien]:
        sql = "SELECT * FROM GAMME_ENTRETIEN"
        params = []
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY description"
        try:
            rows = fetch_all(sql) # params est vide ici
            return [GammeEntretien.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get all gammes (active_only={active_only}): {e}")
            raise

    def update(self, gamme: GammeEntretien) -> bool:
        if gamme.id_gamme is None: return False
        sql = """UPDATE GAMME_ENTRETIEN SET
                     description=%s, type_entretien=%s, periodicite_valeur=%s, periodicite_unite=%s,
                     instructions=%s, date_derniere_realisation=%s, prochaine_date_calculee=%s, active=%s,
                     type_machine_id=%s, createur_id=%s, duree_estimee_min=%s, qualification_requise=%s, priorite=%s,
                     updated_at = CURRENT_TIMESTAMP
                 WHERE id_gamme = %s"""
        params = (
            gamme.description, gamme.type_entretien, gamme.periodicite_valeur, gamme.periodicite_unite,
            gamme.instructions, self._format_date(gamme.date_derniere_realisation),
            self._format_date(gamme.prochaine_date_calculee), 1 if gamme.active else 0,
            gamme.type_machine_id, gamme.createur_id, gamme.duree_estimee_min,
            gamme.qualification_requise, gamme.priorite,
            gamme.id_gamme
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Gamme ID {gamme.id_gamme} mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec màj Gamme ID {gamme.id_gamme}. Desc unique, FK: {e}")
            # ... (gestion erreurs intégrité comme dans add) ...
            raise DatabaseError("Contrainte d'intégrité violée.") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update Gamme ID {gamme.id_gamme}: {e}")
            raise

    def delete(self, gamme_id: int) -> bool:
        # Supprimer une gamme supprime aussi ses étapes et pièces types (ON DELETE CASCADE)
        # et met à NULL le lien dans ORDRE_TRAVAIL (ON DELETE SET NULL)
        sql = "DELETE FROM GAMME_ENTRETIEN WHERE id_gamme = %s"
        try:
            cursor = execute_query(sql, (gamme_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Gamme ID {gamme_id} (et ses étapes/pièces) supprimée.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB delete Gamme ID {gamme_id}: {e}")
            raise

    # --- Méthodes spécifiques pour la génération d'OT ---
    def get_active_gammes_due(self, due_date: date) -> List[GammeEntretien]:
        """ Récupère les gammes actives dont la prochaine date est <= due_date. """
        # Ce calcul peut être complexe si basé sur Heures/Cycles.
        # Pour l'instant, basé sur 'prochaine_date_calculee' (si on la stocke)
        # ou 'date_derniere_realisation' + périodicité (si on ne stocke pas la prochaine date)

        # Version simple si prochaine_date_calculee est stockée et à jour:
        sql = """SELECT * FROM GAMME_ENTRETIEN
                 WHERE active = 1
                   AND prochaine_date_calculee IS NOT NULL
                   AND prochaine_date_calculee <= %s
                   AND periodicite_unite NOT IN ('Heures', 'Cycles') -- Exclure ce qui dépend des compteurs
                 ORDER BY prochaine_date_calculee, priorite"""
        try:
            rows = fetch_all(sql, (self._format_date(due_date),))
            gammes = [GammeEntretien.from_db_row(row) for row in rows if row]
            logger.info(f"Trouvé {len(gammes)} gammes échues avant {due_date}.")
            return gammes
        except DatabaseError as e:
            logger.error(f"Erreur DB get gammes échues: {e}")
            raise

    def update_last_realisation(self, gamme_id: int, last_date: date) -> bool:
         """ Met à jour seulement la date de dernière réalisation d'une gamme. """
         # Utilisé après clôture d'un OT préventif lié
         # Recalcul prochaine_date peut se faire dans le service qui appelle ceci
         sql = "UPDATE GAMME_ENTRETIEN SET date_derniere_realisation = %s WHERE id_gamme = %s"
         try:
            cursor = execute_query(sql, (self._format_date(last_date), gamme_id))
            success = cursor.rowcount > 0
            if success: logger.info(f"Date dernière réalisation mise à jour pour Gamme ID {gamme_id}.")
            return success
         except DatabaseError as e:
              logger.error(f"Erreur DB update date realisation Gamme ID {gamme_id}: {e}")
              raise