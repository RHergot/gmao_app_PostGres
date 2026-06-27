# gmao_app/app/data/repositories/ordre_travail_repository.py
""" Repository pour l'entité OrdreTravail. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.ordre_travail import OrdreTravail

logger = logging.getLogger(__name__)

class OrdreTravailRepository:

    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat(sep=' ', timespec='seconds') if dt else None

    def add(self, ot: OrdreTravail) -> Optional[int]:
        # Gérer numero_ot unique%s Pour l'instant, on le laisse nullable ou non unique
        sql = """INSERT INTO ORDRE_TRAVAIL (
                     numero_ot, machine_id, gamme_id, type, description, date_creation,
                     date_prevue, duree_prevue_min, priorite, urgence, statut,
                     technicien_assigne_id, utilisateur_createur_id, notes_planification
                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 RETURNING id_ot"""
        params = (
            ot.numero_ot, ot.machine_id, ot.gamme_id, ot.type, ot.description,
            self._format_datetime(ot.date_creation), self._format_datetime(ot.date_prevue),
            ot.duree_prevue_min, ot.priorite, 1 if ot.urgence else 0, ot.statut,
            ot.technicien_assigne_id, ot.utilisateur_createur_id, ot.notes_planification
        )
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_ot") if row else None
            logger.info(f"Ordre Travail (Type '{ot.type}') ajouté ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
             logger.error(f"Échec ajout OT. FK invalide (Machine/Gamme/Tech/User)%s {e}")
             # Donner un message plus précis serait bien mais complexe sans analyser str(e)
             raise DatabaseError("Contrainte d'intégrité violée (Référence Machine/Utilisateur invalide%s).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout OT type '{ot.type}': {e}")
            raise

    def get_by_id(self, ot_id: int) -> Optional[OrdreTravail]:
        sql = "SELECT * FROM ORDRE_TRAVAIL WHERE id_ot = %s"
        try:
            row = fetch_one(sql, (ot_id,))
            return OrdreTravail.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get OT ID {ot_id}: {e}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None,
                 sort_by: str = "date_prevue", sort_desc: bool = False) -> List[OrdreTravail]:
        sql = "SELECT * FROM ORDRE_TRAVAIL"
        where_clauses = []
        params = []
        
        logger.debug(f"OrdreTravailRepository.get_all appelé avec filters={filters}, sort_by={sort_by}, sort_desc={sort_desc}")
        
        if filters:
             # Liste blanche stricte de toutes les clés de filtre autorisées
             ALLOWED_FILTER_KEYS = {
                 'statut__in', 'statut__ne', 'technicien_assigne_id',
                 'machine_id', 'gamme_id', 'type', 'priorite', 'statut',
                 'utilisateur_createur_id', 'urgence'
             }
             invalid_keys = set(filters.keys()) - ALLOWED_FILTER_KEYS
             if invalid_keys:
                 logger.error(f"Clés de filtre non autorisées: {invalid_keys}")
                 raise ValueError(f"Clés de filtre non autorisées: {invalid_keys}")
             
             # Ajouter la logique de filtrage similaire à MachineRepository
             for key, value in filters.items():
                  # Support du filtre 'statut__in' pour les statuts multiples
                  if key == 'statut__in' and value:
                       placeholders = ','.join(['%s'] * len(value))
                       where_clauses.append(f"statut IN ({placeholders})")
                       params.extend(value)
                       logger.debug(f"Ajout filtre statut__in: {value}")
                  # Support du filtre 'statut__ne' pour exclure un statut
                  elif key == 'statut__ne' and value is not None:
                       where_clauses.append(f"statut != %s")
                       params.append(value)
                       logger.debug(f"Ajout filtre statut__ne: {value}")
                  elif key == 'technicien_assigne_id' and value is None:
                       # Cas spécial pour technicien non assigné (NULL)
                       where_clauses.append(f"{key} IS NULL")
                       logger.debug(f"Ajout filtre technicien_assigne_id IS NULL")
                  elif key in ['machine_id', 'gamme_id', 'type', 'priorite', 'statut', 'technicien_assigne_id', 'utilisateur_createur_id', 'urgence'] and value is not None:
                       # Gérer le boolean urgence
                       if key == 'urgence':
                            where_clauses.append(f"{key} = %s")
                            params.append(1 if value else 0)
                            logger.debug(f"Ajout filtre urgence: {1 if value else 0}")
                       else:
                            where_clauses.append(f"{key} = %s")
                            params.append(value)
                            logger.debug(f"Ajout filtre {key}: {value}")
                  # Ajouter filtres de date%s (ex: date_prevue >= %s)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # Tri
        valid_sort = ['id_ot', 'numero_ot', 'machine_id', 'type', 'date_creation', 'date_prevue', 'priorite', 'statut']
        sort_col = sort_by if sort_by in valid_sort else 'date_prevue'
        order = "DESC" if sort_desc else "ASC"
        sql += f" ORDER BY {sort_col} {order}"
        
        logger.debug(f"SQL généré: {sql}")
        logger.debug(f"Paramètres: {params}")

        try:
            rows = fetch_all(sql, tuple(params))
            result = [OrdreTravail.from_db_row(row) for row in rows if row]
            logger.debug(f"Résultat get_all: {len(result)} OTs trouvés")
            return result
        except DatabaseError as e:
            logger.error(f"Erreur DB get all OT: {e}")
            raise

    def update(self, ot: OrdreTravail) -> bool:
        if ot.id_ot is None: return False
        sql = """UPDATE ORDRE_TRAVAIL SET
                    numero_ot=%s, machine_id=%s, gamme_id=%s, type=%s, description=%s, date_creation=%s,
                    date_prevue=%s, duree_prevue_min=%s, priorite=%s, urgence=%s, statut=%s,
                    technicien_assigne_id=%s, utilisateur_createur_id=%s, notes_planification=%s
                 WHERE id_ot = %s"""
        params = (
            ot.numero_ot, ot.machine_id, ot.gamme_id, ot.type, ot.description,
            self._format_datetime(ot.date_creation), self._format_datetime(ot.date_prevue),
            ot.duree_prevue_min, ot.priorite, 1 if ot.urgence else 0, ot.statut,
            ot.technicien_assigne_id, ot.utilisateur_createur_id, ot.notes_planification,
            ot.id_ot
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"OT ID {ot.id_ot} mis à jour.")
            return success
        except psycopg2.IntegrityError as e:
             logger.error(f"Échec màj OT ID {ot.id_ot}. FK invalide%s {e}")
             raise DatabaseError("Contrainte d'intégrité violée (Référence invalide%s).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update OT ID {ot.id_ot}: {e}")
            raise

    def delete(self, ot_id: int) -> bool:
        # La FK dans MAINTENANCE est ON DELETE CASCADE, donc la maintenance liée sera aussi supprimée.
        sql = "DELETE FROM ORDRE_TRAVAIL WHERE id_ot = %s"
        try:
            cursor = execute_query(sql, (ot_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"OT ID {ot_id} supprimé (et Maintenance liée si existante).")
            return success
        except DatabaseError as e: # Peu probable ici sauf erreur générale
            logger.error(f"Erreur DB delete OT ID {ot_id}: {e}")
            raise