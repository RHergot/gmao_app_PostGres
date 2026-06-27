# gmao_app/app/data/repositories/compteur_repository.py
""" Repository pour l'entité Compteur. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from datetime import date

from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.compteur import Compteur # Import du modèle
from app.utils.helpers import format_iso_date # Pour formater les dates si nécessaire

logger = logging.getLogger(__name__)

class CompteurRepository:
    """ Repository pour les opérations d'accès aux données des compteurs. """

    def __init__(self):
        # Aucune dépendance immédiate des autres repos dans __init__
        logger.debug("CompteurRepository initialisé.")
        pass

    def add(self, compteur: Compteur) -> Optional[int]:
        """ Ajoute un nouveau compteur à la base de données. """
        logger.debug(f"Tentative ajout compteur: {compteur.nom} pour machine ID {compteur.machine_id}")
        sql = """INSERT INTO COMPTEUR (machine_id, nom, unite, valeur_actuelle,
                                     date_dernier_releve, seuil_alerte, seuil_prev_ot)
                 VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_compteur"""
        params = (compteur.machine_id, compteur.nom, compteur.unite, compteur.valeur_actuelle,
                  format_iso_date(compteur.date_dernier_releve),
                  compteur.seuil_alerte, compteur.seuil_prev_ot)

        try:
            row = fetch_one(sql, params)
            new_id = row['id_compteur'] if row else None
            if new_id is not None:
                 logger.info(f"Compteur '{compteur.nom}' ajouté pour machine ID {compteur.machine_id}, ID: {new_id}")
                 return new_id
            else:
                 logger.error(f"Échec ajout compteur '{compteur.nom}' (machine ID {compteur.machine_id}), ID non retourné.")
                 return None
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout compteur '{compteur.nom}' (machine ID {compteur.machine_id}). Contrainte violée: {e}")
            # Gérer spécifiquement l'erreur d'unicité sur (machine_id, nom)
            if 'UNIQUE constraint failed: COMPTEUR.machine_id, COMPTEUR.nom' in str(e):
                raise DatabaseError(f"Un compteur nommé '{compteur.nom}' existe déjà pour cette machine.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"ID Machine {compteur.machine_id} invalide.") from e
            else:
                 raise DatabaseError(f"Contrainte d'intégrité violée lors ajout compteur: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout compteur '{compteur.nom}' (machine ID {compteur.machine_id}): {e}")
            raise
        except Exception as e:
             logger.exception(f"Erreur inattendue ajout compteur '{compteur.nom}' (machine ID {compteur.machine_id}): {e}")
             raise DatabaseError("Erreur serveur lors de l'ajout du compteur.") from e


    def get_by_id(self, compteur_id: int) -> Optional[Compteur]:
        """ Récupère un compteur par son ID. """
        sql = "SELECT * FROM COMPTEUR WHERE id_compteur = %s"
        try:
            row = fetch_one(sql, (compteur_id,))
            # Utilisez la méthode from_db_row du modèle
            return Compteur.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get compteur ID {compteur_id}: {e}")
            raise
        except Exception as e:
             logger.exception(f"Erreur inattendue get compteur ID {compteur_id}: {e}")
             raise DatabaseError(f"Erreur serveur lors de la récupération du compteur {compteur_id}.") from e

    def get_by_machine_id(self, machine_id: int) -> List[Compteur]:
         """ Récupère tous les compteurs associés à une machine par son ID. """
         logger.debug(f"Récupération compteurs pour machine ID {machine_id}")
         sql = "SELECT * FROM COMPTEUR WHERE machine_id = %s ORDER BY nom"
         try:
             rows = fetch_all(sql, (machine_id,))
             return [Compteur.from_db_row(row) for row in rows if row] # Convertir en modèles
         except DatabaseError as e:
             logger.error(f"Erreur DB get compteurs pour machine ID {machine_id}: {e}")
             return [] # Retourner liste vide en cas d'erreur DB
         except Exception as e:
             logger.exception(f"Erreur inattendue get compteurs pour machine ID {machine_id}: {e}")
             return [] # Retourner liste vide


    def get_by_machine_id_and_name(self, machine_id: int, nom: str) -> Optional[Compteur]:
         """ Récupère un compteur par sa machine et son nom (qui doit être unique pour la machine). """
         logger.debug(f"Récupération compteur nom '{nom}' pour machine ID {machine_id}")
         sql = "SELECT * FROM COMPTEUR WHERE machine_id = %s AND nom = %s"
         try:
             row = fetch_one(sql, (machine_id, nom))
             return Compteur.from_db_row(row) # Convertir en modèle
         except DatabaseError as e:
             logger.error(f"Erreur DB get compteur nom '{nom}' pour machine ID {machine_id}: {e}")
             raise
         except Exception as e:
             logger.exception(f"Erreur inattendue get compteur nom '{nom}' pour machine ID {machine_id}: {e}")
             raise DatabaseError(f"Erreur serveur lors de la récupération du compteur '{nom}' pour machine {machine_id}.")


    def update(self, compteur: Compteur) -> bool:
        """ Met à jour un compteur existant (sauf la valeur actuelle et date, gérées séparément). """
        if compteur.id_compteur is None:
             logger.warning("Tentative de màj compteur sans ID.")
             return False

        # NOTE: Ne met pas à jour valeur_actuelle ou date_dernier_releve ici
        # Ces champs devraient être mis à jour uniquement lors de l'enregistrement d'un HISTORIQUE_COMPTEUR
        sql = """UPDATE COMPTEUR SET machine_id=%s, nom=%s, unite=%s,
                                     seuil_alerte=%s, seuil_prev_ot=%s
                 WHERE id_compteur = %s"""
        params = (compteur.machine_id, compteur.nom, compteur.unite,
                  compteur.seuil_alerte, compteur.seuil_prev_ot,
                  compteur.id_compteur)

        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Compteur ID {compteur.id_compteur} mis à jour (paramètres).")
            else:
                 logger.warning(f"Aucun compteur trouvé avec ID {compteur.id_compteur} pour mise à jour (paramètres).")
            return success
        except psycopg2.IntegrityError as e:
             logger.warning(f"Échec màj compteur ID {compteur.id_compteur}. Contrainte violée: {e}")
             if 'UNIQUE constraint failed: COMPTEUR.machine_id, COMPTEUR.nom' in str(e):
                 raise DatabaseError(f"Un compteur nommé '{compteur.nom}' existe déjà pour cette machine.") from e
             elif 'FOREIGN KEY constraint failed' in str(e):
                  raise DatabaseError(f"ID Machine {compteur.machine_id} invalide.") from e
             else:
                  raise DatabaseError(f"Contrainte d'intégrité violée lors màj compteur {compteur.id_compteur}: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update compteur ID {compteur.id_compteur}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Erreur inattendue update compteur ID {compteur.id_compteur}: {e}")
            raise DatabaseError(f"Erreur serveur lors de la mise à jour du compteur {compteur.id_compteur}.")


    def update_current_value(self, compteur_id: int, nouvelle_valeur: float, date_releve: date) -> bool:
         """ Met à jour uniquement la valeur actuelle et la date du dernier relevé du compteur. """
         if compteur_id is None: return False
         sql = """UPDATE COMPTEUR SET valeur_actuelle = %s, date_dernier_releve = %s, updated_at = CURRENT_TIMESTAMP
                  WHERE id_compteur = %s"""
         params = (nouvelle_valeur, format_iso_date(date_releve), compteur_id)
         try:
             cursor = execute_query(sql, params)
             success = cursor.rowcount > 0
             if success:
                 logger.info(f"Valeur actuelle compteur ID {compteur_id} mise à jour à {nouvelle_valeur} ({format_iso_date(date_releve)}).")
             return success
         except DatabaseError as e:
              logger.error(f"Erreur DB màj valeur compteur ID {compteur_id}: {e}")
              # Ici, on peut juste logguer et retourner False, ou lever selon la criticité
              return False
         except Exception as e:
             logger.exception(f"Erreur inattendue màj valeur compteur ID {compteur_id}: {e}")
             return False # Logguer et retourner False


    def delete(self, compteur_id: int) -> bool:
        """ Supprime un compteur par son ID (entraînera la suppression des historiques par CASCADE). """
        sql = "DELETE FROM COMPTEUR WHERE id_compteur = %s"
        try:
            cursor = execute_query(sql, (compteur_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Compteur ID {compteur_id} supprimé (et historiques associés).")
            else:
                logger.warning(f"Aucun compteur trouvé avec ID {compteur_id} pour suppression.")
            return success
        # IntegrityError ne devrait pas arriver ici à cause du CASCADE sur HISTORIQUE_COMPTEUR,
        # mais peut arriver si d'autres tables référencent COMPTEUR directement.
        except DatabaseError as e:
            logger.error(f"Erreur DB delete compteur ID {compteur_id}: {e}")
            # Identifier si une autre FK pose problème %s Plus tard.
            raise DatabaseError("Impossible de supprimer ce compteur car il est référencé.") from e
        except Exception as e:
             logger.exception(f"Erreur inattendue delete compteur ID {compteur_id}: {e}")
             raise DatabaseError(f"Erreur serveur lors de la suppression du compteur {compteur_id}.")