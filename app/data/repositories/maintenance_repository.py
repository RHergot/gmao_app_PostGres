# gmao_app/app/data/repositories/maintenance_repository.py
""" Repository pour l'entité Maintenance (intervention réalisée). """
import logging
import psycopg2
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.data.database import execute_query, fetch_one, fetch_all, DatabaseError
from app.core.models.maintenance import Maintenance

logger = logging.getLogger(__name__)

class MaintenanceRepository:

    @staticmethod
    def _generate_month_list(start_current_month, months: int) -> list:
        """
        Génère la liste triée des mois au format 'YYYY-MM' pour les N derniers mois
        (hors mois courant), du plus récent au plus ancien.
        """
        from datetime import timedelta
        months_list = []
        for i in range(months):
            m = (start_current_month - timedelta(days=1)).replace(day=1) - timedelta(days=30*i)
            months_list.append(m.strftime('%Y-%m'))
        return list(reversed(sorted(months_list)))

    def get_monthly_completed_costs_and_counts(self, months: int = 12) -> list:
        """
        Retourne une liste de dicts : [{"month": "YYYY-MM", "cost": float, "count": int}],
        pour les 12 derniers mois (hors mois en cours).
        """
        from datetime import datetime, timedelta
        now = datetime.now()
        # Premier jour du mois en cours
        start_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Premier jour du mois de début (12 mois avant, hors mois courant)
        start_period = (start_current_month - timedelta(days=1)).replace(day=1)
        # Format SQL pour dates
        start_period_str = start_period.strftime('%Y-%m-%d')
        end_period_str = start_current_month.strftime('%Y-%m-%d')
        # Récupérer toutes les maintenances clôturées sur la période
        sql = """
            SELECT SUBSTRING(date_fin_reelle, 1, 7) as month,
                   SUM(cout_total) as total_cost,
                   COUNT(*) as count
            FROM MAINTENANCE
            WHERE date_fin_reelle >= %s AND date_fin_reelle < %s
                  AND (resultat IS NOT NULL AND resultat != '')
                  AND cout_total IS NOT NULL
            GROUP BY month
            ORDER BY month DESC
            LIMIT %s
        """
        try:
            logger.debug(f"Exécution requête SQL pour coûts mensuels: {sql}")
            logger.debug(f"Paramètres: start={start_period_str}, end={end_period_str}, limit={months}")
            
            rows = fetch_all(sql, (start_period_str, end_period_str, months))
            logger.debug(f"Résultat requête: {len(rows)} lignes")
            
            # Compléter les mois manquants à 0
            results = []
            months_list = MaintenanceRepository._generate_month_list(start_current_month, months)
            
            logger.debug(f"Liste des mois à inclure: {months_list}")
            rows_dict = {row['month']: row for row in rows if row.get('month')}
            logger.debug(f"Mois trouvés dans la base: {list(rows_dict.keys())}")
            
            for m in months_list:
                data = rows_dict.get(m)
                cost = 0.0
                count = 0
                
                if data:
                    try:
                        if data.get('total_cost') is not None:
                            cost = float(data['total_cost'])
                        if data.get('count') is not None:
                            count = int(data['count'])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Erreur de conversion des données pour le mois {m}: {e}")
                
                results.append({
                    'month': m,
                    'cost': cost,
                    'count': count
                })
            
            logger.debug(f"Résultats finaux: {len(results)} mois")
            return results
        except Exception as e:
            logger.exception(f"Erreur lors de l'agrégation des coûts mensuels: {e}")
            # Retourner une liste vide mais avec les mois attendus pour éviter les erreurs d'affichage
            try:
                empty_results = []
                months_list = MaintenanceRepository._generate_month_list(start_current_month, months)
                for m in months_list:
                    empty_results.append({
                        'month': m,
                        'cost': 0.0,
                        'count': 0
                    })
                return empty_results
            except Exception:
                logger.exception("Erreur lors de la création des résultats vides")
                return []

    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat(sep=' ', timespec='seconds') if dt else None

    def add(self, maint: Maintenance) -> Optional[int]:
        """ Ajoute un nouvel enregistrement de maintenance. """
        sql = """INSERT INTO MAINTENANCE (
                     ot_id, machine_id, technicien_id, date_debut_reelle, date_fin_reelle,
                     duree_intervention_h, type_reel, description_travaux, resultat,
                     cout_manuel_v1, cout_main_oeuvre, cout_pieces_internes, 
                     cout_pieces_externes, cout_autres_frais, cout_total,
                     evaluation_qualite, impact_production, notes_technicien
                     -- created_at est géré par défaut/trigger
                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_maintenance"""
        params = (
            maint.ot_id, maint.machine_id, maint.technicien_id,
            self._format_datetime(maint.date_debut_reelle), self._format_datetime(maint.date_fin_reelle),
            maint.duree_intervention_h, maint.type_reel, maint.description_travaux, maint.resultat,
            maint.cout_manuel_v1, maint.cout_main_oeuvre, maint.cout_pieces_internes,
            maint.cout_pieces_externes, maint.cout_autres_frais, maint.cout_total,
            maint.evaluation_qualite, maint.impact_production, maint.notes_technicien
        )
        try:
            row = fetch_one(sql, params)
            new_id = row.get("id_maintenance") if row else None
            logger.info(f"Maintenance pour OT ID {maint.ot_id} ajoutée avec ID: {new_id}")
            return new_id
        except psycopg2.IntegrityError as e:
             logger.error(f"Échec ajout Maintenance OT ID {maint.ot_id}. FK (OT/Machine/Tech), OT unique: {e}")
             if 'MAINTENANCE.ot_id' in str(e) and 'UNIQUE' in str(e):
                 raise DatabaseError(f"Une maintenance existe déjà pour l'OT ID {maint.ot_id}.") from e
             else:
                 raise DatabaseError("Contrainte d'intégrité violée (Référence OT/Machine/Technicien invalide).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB ajout Maintenance OT ID {maint.ot_id}: {e}")
            raise

    def get_by_id(self, maint_id: int) -> Optional[Maintenance]:
        sql = "SELECT * FROM MAINTENANCE WHERE id_maintenance = %s"
        try:
            row = fetch_one(sql, (maint_id,))
            return Maintenance.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get maintenance ID {maint_id}: {e}")
            raise

    def get_by_ot_id(self, ot_id: int) -> Optional[Maintenance]:
        """ Récupère la maintenance associée à un OT (devrait être unique). """
        sql = "SELECT * FROM MAINTENANCE WHERE ot_id = %s"
        try:
            row = fetch_one(sql, (ot_id,))
            return Maintenance.from_db_row(row)
        except DatabaseError as e:
            logger.error(f"Erreur DB get maintenance pour OT ID {ot_id}: {e}")
            raise

    def get_all_for_machine(self, machine_id: int, limit: int = 50) -> List[Maintenance]:
        """ Récupère les dernières maintenances pour une machine. """
        sql = "SELECT * FROM MAINTENANCE WHERE machine_id = %s ORDER BY date_fin_reelle DESC LIMIT %s"
        try:
            rows = fetch_all(sql, (machine_id, limit))
            return [Maintenance.from_db_row(row) for row in rows if row]
        except DatabaseError as e:
            logger.error(f"Erreur DB get maintenances pour machine ID {machine_id}: {e}")
            raise

    def update(self, maint: Maintenance) -> bool:
        """ Met à jour une maintenance (moins courant car historique, mais possible pour corriger saisie). """
        if maint.id_maintenance is None: return False
        sql = """UPDATE MAINTENANCE SET
                    ot_id=%s, machine_id=%s, technicien_id=%s, date_debut_reelle=%s, date_fin_reelle=%s,
                    duree_intervention_h=%s, type_reel=%s, description_travaux=%s, resultat=%s,
                    cout_manuel_v1=%s, cout_main_oeuvre=%s, cout_pieces_internes=%s,
                    cout_pieces_externes=%s, cout_autres_frais=%s, cout_total=%s,
                    evaluation_qualite=%s, impact_production=%s, notes_technicien=%s
                 WHERE id_maintenance = %s"""
        params = (
            maint.ot_id, maint.machine_id, maint.technicien_id,
            self._format_datetime(maint.date_debut_reelle), self._format_datetime(maint.date_fin_reelle),
            maint.duree_intervention_h, maint.type_reel, maint.description_travaux, maint.resultat,
            maint.cout_manuel_v1, maint.cout_main_oeuvre, maint.cout_pieces_internes,
            maint.cout_pieces_externes, maint.cout_autres_frais, maint.cout_total,
            maint.evaluation_qualite, maint.impact_production, maint.notes_technicien,
            maint.id_maintenance
        )
        try:
            cursor = execute_query(sql, params)
            success = cursor.rowcount > 0
            if success: logger.info(f"Maintenance ID {maint.id_maintenance} mise à jour.")
            return success
        except psycopg2.IntegrityError as e:
             logger.error(f"Échec màj Maintenance ID {maint.id_maintenance}. FK, OT unique: {e}")
             if 'MAINTENANCE.ot_id' in str(e) and 'UNIQUE' in str(e):
                  raise DatabaseError(f"L'OT ID {maint.ot_id} est déjà lié à une autre maintenance.") from e
             else:
                 raise DatabaseError("Contrainte d'intégrité violée (Référence OT/Machine/Technicien invalide).") from e
        except DatabaseError as e:
            logger.error(f"Erreur DB update Maintenance ID {maint.id_maintenance}: {e}")
            raise

    def update_financial_data(self, maint_id: int, financial_data: Dict[str, float]) -> bool:
        """ Met à jour uniquement les données financières d'une maintenance. """
        if not maint_id: return False
        
        # Liste blanche des colonnes financières autorisées (protection contre injection SQL)
        ALLOWED_FINANCIAL_FIELDS = {
            'cout_main_oeuvre', 'cout_pieces_internes', 'cout_pieces_externes',
            'cout_autres_frais', 'cout_total'
        }
        
        # Valider toutes les clés contre la liste blanche
        invalid_keys = set(financial_data.keys()) - ALLOWED_FINANCIAL_FIELDS
        if invalid_keys:
            logger.error(f"Tentative de mise à jour avec des champs non autorisés: {invalid_keys}")
            raise ValueError(f"Champs financiers non autorisés: {invalid_keys}")
        
        # Construit dynamiquement la requête SQL à partir des clés validées
        fields = ", ".join([f"{key}=%s" for key in financial_data.keys()])
        sql = f"UPDATE MAINTENANCE SET {fields} WHERE id_maintenance = %s"
        
        # Prépare les paramètres et ajoute l'ID à la fin
        params = list(financial_data.values())
        params.append(maint_id)
        
        try:
            cursor = execute_query(sql, tuple(params))
            success = cursor.rowcount > 0
            if success: 
                logger.info(f"Données financières de la Maintenance ID {maint_id} mises à jour: {financial_data}")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB mise à jour données financières Maintenance ID {maint_id}: {e}")
            raise

    def delete(self, maint_id: int) -> bool:
        """ Supprime un enregistrement de maintenance (peu courant, admin). """
        # La suppression n'est pas bloquée par d'autres FK par défaut
        sql = "DELETE FROM MAINTENANCE WHERE id_maintenance = %s"
        try:
            cursor = execute_query(sql, (maint_id,))
            success = cursor.rowcount > 0
            if success: logger.info(f"Maintenance ID {maint_id} supprimée.")
            return success
        except DatabaseError as e:
            logger.error(f"Erreur DB delete maintenance ID {maint_id}: {e}")
            raise