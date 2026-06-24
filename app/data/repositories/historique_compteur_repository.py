# gmao_app/app/data/repositories/historique_compteur_repository.py
""" Repository pour l'entité HistoriqueCompteur. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.historique_compteur import HistoriqueCompteur # Import du modèle
# Importez vos helpers de date/datetime
from app.utils.helpers import format_iso_datetime

logger = logging.getLogger(__name__)

class HistoriqueCompteurRepository:
    """ Repository pour les opérations d'accès aux données de l'historique des compteurs. """

    def __init__(self):
        logger.debug("HistoriqueCompteurRepository initialisé.")
        pass

    def add(self, historique: HistoriqueCompteur) -> Optional[int]:
        """ Ajoute un nouveau relevé historique à la base de données. """
        logger.debug(f"Tentative ajout historique compteur ID {historique.compteur_id}: valeur {historique.valeur}")
        sql = """INSERT INTO HISTORIQUE_COMPTEUR (compteur_id, date_releve, valeur,
                                                 utilisateur_id, maintenance_id)
                 VALUES (%s, %s, %s, %s, %s)"""
        # Utilisez la méthode to_db_params du modèle
        # Assurez-vous que to_db_params retourne le tuple dans le bon ordre sans l'ID
        params = (historique.compteur_id,
                  format_iso_datetime(historique.date_releve), # Utiliser helper
                  historique.valeur, historique.utilisateur_id, historique.maintenance_id)

        try:
            cursor = execute_query(sql, params)
            new_id = cursor.lastrowid
            if new_id is not None:
                 logger.info(f"Historique compteur ajouté ID {historique.compteur_id}, valeur {historique.valeur}, Relevé ID: {new_id}")
                 return new_id
            else:
                 logger.error(f"Échec ajout historique compteur ID {historique.compteur_id}, valeur {historique.valeur}, ID non retourné.")
                 return None
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout historique compteur ID {historique.compteur_id}. Contrainte violée: {e}")
            # Gérer FKs si nécessaire
            if 'FOREIGN KEY constraint failed' in str(e):
                 raise DatabaseError(f"FK invalide pour historique compteur {historique.compteur_id}. Compteur/Utilisateur/Maintenance ID%s") from e
            else:
                 raise DatabaseError(f"Contrainte d'intégrité violée lors ajout historique compteur: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout historique compteur ID {historique.compteur_id}: {e}")
            raise
        except Exception as e:
             logger.exception(f"Erreur inattendue ajout historique compteur ID {historique.compteur_id}: {e}")
             raise DatabaseError("Erreur serveur lors de l'ajout de l'historique compteur.") from e

    def get_by_id(self, historique_id: int) -> Optional[HistoriqueCompteur]:
        """ Récupère un relevé historique par son ID. """
        sql = "SELECT * FROM HISTORIQUE_COMPTEUR WHERE id_historique = %s"
        try:
            row = fetch_one(sql, (historique_id,))
            return HistoriqueCompteur.from_db_row(row) # Convertir en modèle
        except DatabaseError as e:
            logger.error(f"Erreur DB get historique compteur ID {historique_id}: {e}")
            raise
        except Exception as e:
             logger.exception(f"Erreur inattendue get historique compteur ID {historique_id}: {e}")
             raise DatabaseError(f"Erreur serveur lors de la récupération de l'historique compteur {historique_id}.")


    def get_by_compteur_id(self, compteur_id: int, limit: Optional[int] = None) -> List[HistoriqueCompteur]:
         """ Récupère l'historique des relevés pour un compteur donné, triés par date décroissante. """
         logger.debug(f"Récupération historique pour compteur ID {compteur_id}. Limit: {limit}")
         sql = "SELECT * FROM HISTORIQUE_COMPTEUR WHERE compteur_id = %s ORDER BY date_releve DESC"
         params = (compteur_id,)
         if limit is not None and limit > 0:
             sql += f" LIMIT %s"
             params += (limit,)

         try:
             rows = fetch_all(sql, params)
             return [HistoriqueCompteur.from_db_row(row) for row in rows if row] # Convertir
         except DatabaseError as e:
             logger.error(f"Erreur DB get historique pour compteur ID {compteur_id}: {e}")
             return [] # Retourner liste vide
         except Exception as e:
             logger.exception(f"Erreur inattendue get historique pour compteur ID {compteur_id}: {e}")
             return [] # Retourner liste vide

    # Pas de méthodes update/delete pour l'historique a priori.