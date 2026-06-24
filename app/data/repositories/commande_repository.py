# gmao_app/app/data/repositories/commande_repository.py
""" Repository pour l'entité Commande. """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.commande import Commande
from app.utils.helpers import format_iso_date # Assurez-vous que cet helper existe

logger = logging.getLogger(__name__)

class CommandeRepository:

    def add(self, commande: Commande) -> Optional[int]:
        """ Ajoute une nouvelle commande à la base de données. """
        sql = """INSERT INTO COMMANDE (numero_commande, fournisseur_id, createur_id, date_commande,
                                     date_livraison_prevue, date_livraison_reelle, statut,
                                     total_ht, frais_port, reference_fournisseur,
                                     mode_paiement, notes_commande)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 RETURNING id_commande"""
        # Note: created_at et updated_at utilisent CURRENT_TIMESTAMP par défaut ou trigger
        params = (
            commande.numero_commande,
            commande.fournisseur_id,
            commande.utilisateur_createur_id,
            format_iso_date(commande.date_commande),
            format_iso_date(commande.date_livraison_prevue),
            format_iso_date(commande.date_livraison_reelle),
            commande.statut,
            commande.total_ht,
            commande.frais_port,
            commande.reference_fournisseur,
            commande.mode_paiement,
            commande.notes_commande
        )
        try:
            result = fetch_one(sql, params)
            if result and 'id_commande' in result:
                new_id = result['id_commande']
                logger.info(f"Commande (Num:{commande.numero_commande}, ID:{new_id}) ajoutée pour fournisseur ID {commande.fournisseur_id}.")
                return new_id
            else:
                logger.error(f"Erreur lors de la récupération de l'ID pour la commande Num:{commande.numero_commande}")
                return None
        except psycopg2.IntegrityError as e:
            logger.warning(f"Échec ajout commande Num:{commande.numero_commande}. Contrainte violée: {e}")
            if 'COMMANDE.numero_commande' in str(e):
                raise DatabaseError(f"Numéro de commande '{commande.numero_commande}' existe déjà.") from e
            elif 'FOREIGN KEY constraint failed' in str(e):
                # Vérifier quelle FK a échoué (plus complexe, nécessite analyse message d'erreur)
                # Pour l'instant, message générique
                 raise DatabaseError(f"ID Fournisseur ({commande.fournisseur_id}) ou Créateur ({commande.utilisateur_createur_id}) invalide.") from e
            else:
                 raise DatabaseError(f"Contrainte d'intégrité violée lors de l'ajout de la commande: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout commande Num:{commande.numero_commande}: {e}")
            raise

    def get_by_id(self, commande_id: int) -> Optional[Commande]:
        """ Récupère une commande par son ID. """
        sql = "SELECT * FROM COMMANDE WHERE id_commande = %s"
        try:
            row = fetch_one(sql, (commande_id,))
            return Commande.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get commande ID {commande_id}: {e}")
            raise # Remonter l'erreur pour que le service/UI puisse la gérer

    def get_by_numero(self, numero_commande: str) -> Optional[Commande]:
        """ Récupère une commande par son numéro unique. """
        sql = "SELECT * FROM COMMANDE WHERE numero_commande = %s"
        try:
            row = fetch_one(sql, (numero_commande,))
            return Commande.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get commande Num:{numero_commande}: {e}")
            raise

    # --- AJOUTER CETTE MÉTHODE ---
    def get_all(self, filters: Optional[Dict[str, Any]] = None,
                 sort_by: str = "date_commande", sort_desc: bool = True) -> List[dict]: # Retourne des Rows
        """ Récupère toutes les commandes avec nom fournisseur, filtres et tri. """
        logger.debug(f"Récupération de toutes les commandes (filters={filters}, sort={sort_by}, desc={sort_desc})")
        sql = """SELECT c.*, f.nom AS nom_fournisseur
                 FROM COMMANDE c
                 LEFT JOIN FOURNISSEUR f ON c.fournisseur_id = f.id_fournisseur
              """
        where_clauses = []
        params = []

        if filters:
            if 'fournisseur_id' in filters and filters['fournisseur_id']:
                where_clauses.append("c.fournisseur_id = %s")
                params.append(filters['fournisseur_id'])
            if 'statut' in filters and filters['statut']:
                where_clauses.append("c.statut = %s")
                params.append(filters['statut'])
            if 'date_debut' in filters and filters['date_debut']:
                where_clauses.append("c.date_commande >= %s")
                params.append(filters['date_debut'])
            if 'date_fin' in filters and filters['date_fin']:
                 where_clauses.append("c.date_commande <= %s")
                 params.append(filters['date_fin'])
            if 'nom_fournisseur_like' in filters and filters['nom_fournisseur_like']:
                 where_clauses.append("f.nom LIKE %s")
                 params.append(f"%{filters['nom_fournisseur_like']}%")
            # Ajouter filtre sur numero_commande%s
            if 'numero_commande_like' in filters and filters['numero_commande_like']:
                 where_clauses.append("c.numero_commande LIKE %s")
                 params.append(f"%{filters['numero_commande_like']}%")

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # Tri (préciser alias)
        valid_sort = ['id_commande', 'numero_commande', 'date_commande', 'statut', 'total_ht', 'fournisseur_id', 'updated_at', 'nom_fournisseur']
        sort_col_sql = sort_by if sort_by in valid_sort else 'date_commande'
        # Déterminer l'alias correct
        sort_col_prefix = 'f.' if sort_col_sql == 'nom_fournisseur' else 'c.'
        order = "DESC" if sort_desc else "ASC"
        sql += f" ORDER BY {sort_col_prefix}{sort_col_sql} {order}"

        try:
            # fetch_all retourne directement la liste des dictionnaires
            rows = fetch_all(sql, tuple(params))
            logger.debug(f"{len(rows)} lignes de commande récupérées de la DB.")
            return rows
        except DatabaseError as e:
            logger.error(f"Erreur DB get all commandes avec fournisseur: {e}")
            raise # Propager l'erreur pour que le service la gère
        except Exception as e:
            logger.exception(f"Erreur inattendue dans CommandeRepository.get_all: {e}")
            raise DatabaseError("Erreur serveur lors récupération commandes.") from e

    # ... (autres méthodes du repository) ...


    def update(self, commande: Commande) -> bool:
        """ Met à jour une commande existante. """
        if commande.id_commande is None:
             logger.warning("Tentative de mise à jour d'une commande sans ID.")
             return False

        sql = """UPDATE COMMANDE SET
                    numero_commande=%s, fournisseur_id=%s, createur_id=%s, date_commande=%s,
                    date_livraison_prevue=%s, date_livraison_reelle=%s, statut=%s,
                    total_ht=%s, frais_port=%s, reference_fournisseur=%s,
                    mode_paiement=%s, notes_commande=%s
                 WHERE id_commande = %s"""
        # updated_at sera géré par le trigger
        params = (
            commande.numero_commande,
            commande.fournisseur_id,
            commande.utilisateur_createur_id,
            format_iso_date(commande.date_commande),
            format_iso_date(commande.date_livraison_prevue),
            format_iso_date(commande.date_livraison_reelle),
            commande.statut,
            commande.total_ht,
            commande.frais_port,
            commande.reference_fournisseur,
            commande.mode_paiement,
            commande.notes_commande,
            commande.id_commande # Pour le WHERE
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Commande ID {commande.id_commande} mise à jour.")
            else:
                 logger.warning(f"Aucune commande trouvée avec ID {commande.id_commande} pour mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
             logger.warning(f"Échec màj commande ID {commande.id_commande}. Contrainte violée: {e}")
             # Gérer erreurs spécifiques comme pour add()
             if 'COMMANDE.numero_commande' in str(e):
                 raise DatabaseError(f"Numéro de commande '{commande.numero_commande}' existe déjà.") from e
             elif 'FOREIGN KEY constraint failed' in str(e):
                  raise DatabaseError(f"ID Fournisseur ({commande.fournisseur_id}) ou Créateur ({commande.utilisateur_createur_id}) invalide.") from e
             else:
                  raise DatabaseError(f"Contrainte d'intégrité violée lors màj commande ID {commande.id_commande}: {e}") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update commande ID {commande.id_commande}: {e}")
            raise

    def update_statut(self, commande_id: int, new_statut: str) -> bool:
        """ Met à jour uniquement le statut d'une commande. """
        sql = "UPDATE COMMANDE SET statut = %s WHERE id_commande = %s"
        params = (new_statut, commande_id)
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Statut de la commande ID {commande_id} mis à jour à '{new_statut}'.")
            else:
                 logger.warning(f"Aucune commande trouvée avec ID {commande_id} pour màj statut.")
            return success
        except DatabaseError as e:
             logger.error(f"Erreur DB màj statut commande ID {commande_id}: {e}")
             raise

    def delete(self, commande_id: int) -> bool:
        """
        Supprime une commande par son ID.
        Attention: Cela supprimera aussi les lignes de commande associées (ON DELETE CASCADE).
        """
        sql = "DELETE FROM COMMANDE WHERE id_commande = %s"
        try:
            cursor = execute_query(sql, (commande_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Commande ID {commande_id} et ses lignes supprimées.")
            else:
                logger.warning(f"Aucune commande trouvée avec ID {commande_id} pour suppression.")
            return success
        # IntegrityError ne devrait pas se produire ici à cause du CASCADE,
        # sauf si COMMANDE est elle-même référencée ailleurs (ex: HISTORIQUE_FINANCIER plus tard%s)
        except DatabaseError as e:
            logger.error(f"Erreur DB delete commande ID {commande_id}: {e}")
            raise

    def calculate_total_ht(self, commande_id: int) -> Optional[float]:
        """ Calcule le total HT d'une commande à partir de ses lignes. """
        sql = """SELECT SUM(quantite_commandee * prix_unitaire_ht) AS total_ht
                 FROM LIGNE_COMMANDE
                 WHERE commande_id = %s"""
        try:
            result = fetch_one(sql, (commande_id,))
            if result and (result.get('total_ht') is not None):
                return float(result['total_ht'])
            else:
                return 0.0 # Retourne 0 si pas de lignes ou erreur
        except DatabaseError as e:
            logger.error(f"Erreur DB calcul total HT pour commande ID {commande_id}: {e}")
            return None # Indiquer une erreur

    def update_total_ht(self, commande_id: int, total_ht: float) -> bool:
        """ Met à jour le champ total_ht de la commande. """
        sql = "UPDATE COMMANDE SET total_ht = %s WHERE id_commande = %s"
        try:
            cursor = execute_query(sql, (total_ht, commande_id))
            return cursor.rowcount > 0
        except DatabaseError as e:
            logger.error(f"Erreur DB màj total HT commande ID {commande_id}: {e}")
            return False