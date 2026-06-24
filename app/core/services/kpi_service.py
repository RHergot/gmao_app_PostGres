# gmao_app/app/core/services/kpi_service.py
"""
Service pour la gestion des KPI financiers par centre de frais.
Implémente la Phase 1 du plan KPI (plan_kpi_finance_ia.md).
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from decimal import Decimal

from app.data.database import fetch_all, fetch_one, DatabaseError
from app.core.services.kpi_query_builder import KPIQueryBuilder

logger = logging.getLogger(__name__)

class KPIService:
    """
    Service dédié aux calculs de KPI financiers par centre de frais.
    
    Fonctionnalités:
    - KPI par machine (coûts, interventions, tendances)
    - KPI par site (agrégation géographique)
    - KPI par équipe (performance MOD)
    - KPI par type de machine (analyse par famille)
    - Comparaisons préventif vs curatif
    - Évolution temporelle et tendances
    """

    def __init__(self):
        """Initialise le service KPI"""
        logger.debug("KPIService initialisé")

    # ===================================================================
    # MÉTHODES KPI PAR MACHINE
    # ===================================================================

    def get_couts_par_machine(self, periode_debut: Union[str, date], periode_fin: Union[str, date],
                             machine_ids: Optional[List[int]] = None, type_machine: Optional[str] = None,
                             site_id: Optional[int] = None, equipe_nom: Optional[str] = None,
                             limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère les coûts agrégés par machine sur une période.

        Args:
            periode_debut: Date de début (format 'YYYY-MM-DD' ou objet date)
            periode_fin: Date de fin (format 'YYYY-MM-DD' ou objet date)
            machine_ids: Filtre par une liste d'IDs de machine (optionnel)
            type_machine: Filtre par type de machine (optionnel)
            site_id: Filtre par ID de site (optionnel)
            equipe_nom: Filtre par nom d'équipe (optionnel)
            limite: Nombre max de résultats (optionnel)

        Returns:
            Liste des machines avec leurs KPI financiers
        """
        try:
            # Utilisation du query builder pour générer la requête SQL
            sql_query, params = KPIQueryBuilder.build_machine_kpi_query(
                periode_debut=periode_debut,
                periode_fin=periode_fin,
                machine_ids=machine_ids,
                type_machine=type_machine,
                site_id=site_id,
                equipe_id=equipe_nom,
                limite=limite
            )

            logger.debug(f"Exécution requête KPI machines - Période: {periode_debut} à {periode_fin}")

            rows = fetch_all(sql_query, params)

            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal en float pour la sérialisation JSON
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)

            logger.info(f"KPI machines récupérés: {len(results)} machines sur période {periode_debut}-{periode_fin}")
            return results

        except DatabaseError as e:
            logger.error(f"Erreur récupération KPI machines: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue KPI machines: {e}")
            raise

    def get_top_machines_couteuses(self, limite: int = 10, periode_mois: int = 12) -> List[Dict[str, Any]]:
        """
        Récupère le top des machines les plus coûteuses.
        
        Args:
            limite: Nombre de machines à retourner
            periode_mois: Période d'analyse en mois (défaut 12)
            
        Returns:
            Liste des machines les plus coûteuses avec tendances
        """
        try:
            sql = """
                SELECT 
                    id_machine,
                    machine_nom,
                    machine_serial,
                    site_nom,
                    type_nom,
                    machine_criticite,
                    nb_interventions_12m,
                    cout_total_12m,
                    cout_moyen_12m,
                    cout_max_12m,
                    cout_mod_12m,
                    cout_pieces_12m,
                    cout_frais_externes_12m,
                    cout_6m_recents,
                    cout_6m_precedents,
                    tendance_cout_pourcentage,
                    
                    -- Calcul du rang
                    ROW_NUMBER() OVER (ORDER BY cout_total_12m DESC) AS rang
                    
                FROM v_top_machines_couteuses
                WHERE cout_total_12m > 0
                ORDER BY cout_total_12m DESC
                LIMIT %s
            """
            
            logger.debug(f"Récupération top {limite} machines coûteuses")
            rows = fetch_all(sql, [limite])
            
            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal en float
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)
            
            logger.info(f"Top machines coûteuses récupéré: {len(results)} machines")
            return results
            
        except DatabaseError as e:
            logger.error(f"Erreur récupération top machines: {e}")
            raise

    def get_tendances_machine(self, machine_id: int, nb_periodes: int = 12) -> Dict[str, Any]:
        """
        Récupère les tendances d'une machine sur plusieurs périodes.
        
        Args:
            machine_id: ID de la machine
            nb_periodes: Nombre de mois à analyser
            
        Returns:
            Dictionnaire avec les données temporelles de la machine
        """
        try:
            # Utilisation du query builder pour générer la requête SQL
            sql, params = KPIQueryBuilder.build_machine_trends_query(machine_id, nb_periodes)
            
            logger.debug(f"Récupération tendances machine {machine_id} sur {nb_periodes} mois")
            rows = fetch_all(sql, params)
            
            # Organisation des données
            periodes = []
            for row in rows:
                periode = dict(row)
                # Conversion des Decimal
                for key, value in periode.items():
                    if isinstance(value, Decimal):
                        periode[key] = float(value)
                periodes.append(periode)
            
            # Calculs de tendances
            result = {
                'machine_id': machine_id,
                'nb_periodes': len(periodes),
                'periodes': list(reversed(periodes)),  # Ordre chronologique
                'tendances': self._calculer_tendances(periodes)
            }
            
            logger.info(f"Tendances machine {machine_id} calculées sur {len(periodes)} périodes")
            return result
            
        except DatabaseError as e:
            logger.error(f"Erreur récupération tendances machine {machine_id}: {e}")
            raise

    # ===================================================================
    # MÉTHODES KPI PAR SITE
    # ===================================================================

    def get_couts_par_site(self, periode_debut: Union[str, date], periode_fin: Union[str, date]) -> List[Dict[str, Any]]:
        """
        Récupère les coûts agrégés par site sur une période.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            
        Returns:
            Liste des sites avec leurs KPI financiers
        """
        try:
            sql = """
                SELECT 
                    id_site,
                    site_nom,
                    site_ville,
                    site_pays,
                    
                    -- Compteurs totaux
                    SUM(nb_machines) AS nb_machines_total,
                    SUM(nb_interventions) AS nb_interventions_total,
                    SUM(nb_preventif) AS nb_preventif,
                    SUM(nb_correctif) AS nb_correctif,
                    SUM(nb_urgence) AS nb_urgence,
                    
                    -- Coûts totaux
                    SUM(cout_total_periode) AS cout_total,
                    SUM(cout_mod_periode) AS cout_main_oeuvre,
                    SUM(cout_pieces_periode) AS cout_pieces_internes,
                    SUM(cout_frais_externes_periode) AS cout_frais_externes,
                    
                    -- Moyennes
                    AVG(cout_moyen_intervention) AS cout_moyen_intervention,
                    AVG(cout_moyen_par_machine) AS cout_moyen_par_machine,
                    AVG(ratio_preventif_curatif) AS ratio_preventif_curatif,
                    
                    -- Pourcentages
                    AVG(pourcentage_moyen_mod) AS pourcentage_mod,
                    AVG(pourcentage_moyen_pieces) AS pourcentage_pieces,
                    AVG(pourcentage_moyen_frais_externes) AS pourcentage_frais_externes
                    
                FROM v_kpi_site_mensuel
                WHERE periode_mois >= %s AND periode_mois <= %s
                GROUP BY id_site, site_nom, site_ville, site_pays
                ORDER BY cout_total DESC
            """
            
            params = [str(periode_debut)[:7], str(periode_fin)[:7]]
            
            logger.debug(f"Récupération KPI sites - Période: {periode_debut} à {periode_fin}")
            rows = fetch_all(sql, params)
            
            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)
            
            logger.info(f"KPI sites récupérés: {len(results)} sites")
            return results
            
        except DatabaseError as e:
            logger.error(f"Erreur récupération KPI sites: {e}")
            raise

    # ===================================================================
    # MÉTHODES KPI PAR ÉQUIPE
    # ===================================================================

    def get_couts_par_equipe(self, periode_debut: Union[str, date], periode_fin: Union[str, date], 
                            equipe_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère les coûts agrégés par équipe sur une période.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            equipe_id: Filtre par équipe spécifique (optionnel)
            
        Returns:
            Liste des équipes avec leurs KPI financiers
        """
        try:
            # Construction de la requête avec filtre optionnel
            where_conditions = ["periode_mois >= %s", "periode_mois <= %s"]
            params = [self._convert_date_to_string(periode_debut), self._convert_date_to_string(periode_fin)]
            
            if equipe_id:
                where_conditions.append("id_equipe = %s")
                params.append(equipe_id)
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f"""
                SELECT 
                    id_equipe,
                    equipe_nom,
                    equipe_domaine,
                    
                    -- Compteurs
                    AVG(nb_techniciens_actifs) AS nb_techniciens_moyen,
                    SUM(nb_interventions) AS nb_interventions_total,
                    SUM(nb_preventif) AS nb_preventif,
                    SUM(nb_correctif) AS nb_correctif,
                    SUM(nb_urgence) AS nb_urgence,
                    
                    -- Coûts
                    SUM(cout_total_periode) AS cout_total,
                    SUM(cout_mod_periode) AS cout_main_oeuvre,
                    SUM(cout_pieces_periode) AS cout_pieces_internes,
                    SUM(cout_frais_externes_periode) AS cout_frais_externes,
                    
                    -- Productivité
                    AVG(cout_moyen_intervention) AS cout_moyen_intervention,
                    AVG(cout_moyen_par_technicien) AS cout_moyen_par_technicien,
                    SUM(heures_totales) AS heures_totales,
                    AVG(cout_par_heure_equipe) AS cout_par_heure,
                    AVG(interventions_par_technicien) AS interventions_par_technicien
                    
                FROM v_kpi_equipe_mensuel
                WHERE {where_clause}
                GROUP BY id_equipe, equipe_nom, equipe_domaine
                ORDER BY cout_total DESC
            """
            
            logger.debug(f"Récupération KPI équipes - Période: {periode_debut} à {periode_fin}")
            rows = fetch_all(sql, params)
            
            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)
            
            logger.info(f"KPI équipes récupérés: {len(results)} équipes")
            return results
            
        except DatabaseError as e:
            logger.error(f"Erreur récupération KPI équipes: {e}")
            raise

    # ===================================================================
    # MÉTHODES COMPARAISON PRÉVENTIF/CURATIF
    # ===================================================================

    def get_ratio_preventif_curatif(self, periode_debut: Union[str, date], periode_fin: Union[str, date],
                                   centre_frais: Optional[str] = None, 
                                   centre_frais_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calcule les ratios préventif/curatif pour un centre de frais ou global.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            centre_frais: Type de centre ('machine', 'site', 'equipe', 'type_machine')
            centre_frais_id: ID du centre de frais spécifique
            
        Returns:
            Dictionnaire avec les ratios et statistiques
        """
        try:
            if centre_frais is None:
                # Analyse globale
                sql = """
                    SELECT 
                        SUM(nb_preventif) AS nb_preventif,
                        SUM(nb_curatif) AS nb_curatif,
                        SUM(nb_urgence) AS nb_urgence,
                        SUM(nb_total) AS nb_total,
                        SUM(cout_preventif) AS cout_preventif,
                        SUM(cout_curatif) AS cout_curatif,
                        SUM(cout_urgence) AS cout_urgence,
                        SUM(cout_total) AS cout_total,
                        AVG(ratio_preventif_curatif) AS ratio_preventif_curatif,
                        AVG(pourcentage_preventif) AS pourcentage_preventif,
                        AVG(pourcentage_curatif) AS pourcentage_curatif
                    FROM v_kpi_preventif_curatif
                    WHERE periode_mois >= %s AND periode_mois <= %s
                """
                params = [str(periode_debut)[:7], str(periode_fin)[:7]]
                
            else:
                # Analyse par centre de frais spécifique
                # TODO: Implémenter selon le type de centre
                raise NotImplementedError(f"Analyse par centre de frais '{centre_frais}' pas encore implémentée")
            
            logger.debug(f"Calcul ratio préventif/curatif - Période: {periode_debut} à {periode_fin}")
            row = fetch_one(sql, params)
            
            if row:
                result = dict(row)
                # Conversion des Decimal
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                
                # Calculs additionnels
                if result['nb_total'] > 0:
                    result['pourcentage_preventif_calc'] = (result['nb_preventif'] / result['nb_total']) * 100
                    result['pourcentage_curatif_calc'] = (result['nb_curatif'] / result['nb_total']) * 100
                    result['pourcentage_urgence'] = (result['nb_urgence'] / result['nb_total']) * 100
                
                if result['cout_total'] > 0:
                    result['pourcentage_cout_preventif'] = (result['cout_preventif'] / result['cout_total']) * 100
                    result['pourcentage_cout_curatif'] = (result['cout_curatif'] / result['cout_total']) * 100
                
                logger.info(f"Ratio préventif/curatif calculé: {result.get('ratio_preventif_curatif', 0):.2f}")
                return result
            else:
                return {}
                
        except DatabaseError as e:
            logger.error(f"Erreur calcul ratio préventif/curatif: {e}")
            raise

    # ===================================================================
    # MÉTHODES KPI PRÉVENTIF VS CURATIF
    # ===================================================================
    
    def get_preventif_vs_curatif(self, periode_debut: Union[str, date], periode_fin: Union[str, date],
                                site_id: Optional[int] = None, machine_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyse comparative entre maintenance préventive et curative.
        
        Args:
            periode_debut: Date de début de l'analyse
            periode_fin: Date de fin de l'analyse  
            site_id: Filtre par site (optionnel)
            machine_id: Filtre par machine (optionnel)
            
        Returns:
            Dictionnaire avec les métriques préventif vs curatif
        """
        try:
            # Convertir les dates
            debut_str = self._convert_date_to_string(periode_debut)
            fin_str = self._convert_date_to_string(periode_fin)
            
            logger.debug(f"Analyse préventif vs curatif - Période: {debut_str} à {fin_str}")
            
            # Construction de la requête avec filtres optionnels
            where_conditions = ["m.date_fin_reelle BETWEEN %s AND %s"]
            params = [debut_str, fin_str]
            
            if site_id:
                where_conditions.append("mach.site_id = %s")
                params.append(site_id)
                
            if machine_id:
                where_conditions.append("mach.id_machine = %s")
                params.append(machine_id)
            
            where_clause = " AND ".join(where_conditions)
            
            # Requête pour les métriques par type de maintenance
            query = f"""
            SELECT 
                m.type_reel as type_intervention,
                COUNT(*) as nb_interventions,
                SUM(COALESCE(m.cout_total, 0)) as cout_total,
                AVG(COALESCE(m.cout_total, 0)) as cout_moyen,
                SUM(COALESCE(m.duree_intervention_h, 0)) as duree_totale,
                AVG(COALESCE(m.duree_intervention_h, 0)) as duree_moyenne
            FROM MAINTENANCE m
            JOIN MACHINE mach ON m.machine_id = mach.id_machine
            WHERE {where_clause}
            GROUP BY m.type_reel
            ORDER BY m.type_reel
            """
            
            resultats = fetch_all(query, params)
            
            # Organiser les résultats
            data = {
                'preventif': {'nb_interventions': 0, 'cout_total': 0, 'cout_moyen': 0, 'duree_totale': 0, 'duree_moyenne': 0},
                'curatif': {'nb_interventions': 0, 'cout_total': 0, 'cout_moyen': 0, 'duree_totale': 0, 'duree_moyenne': 0},
                'total': {'nb_interventions': 0, 'cout_total': 0, 'cout_moyen': 0, 'duree_totale': 0, 'duree_moyenne': 0}
            }
            
            for row in resultats:
                type_intervention = row['type_intervention'].lower() if row['type_intervention'] else 'curatif'
                
                if 'preventif' in type_intervention or 'préventif' in type_intervention:
                    category = 'preventif'
                else:
                    category = 'curatif'
                
                data[category] = {
                    'nb_interventions': row['nb_interventions'] or 0,
                    'cout_total': float(row['cout_total'] or 0),
                    'cout_moyen': float(row['cout_moyen'] or 0),
                    'duree_totale': float(row['duree_totale'] or 0),
                    'duree_moyenne': float(row['duree_moyenne'] or 0)
                }
                
                # Mise à jour des totaux
                data['total']['nb_interventions'] += data[category]['nb_interventions']
                data['total']['cout_total'] += data[category]['cout_total']
                data['total']['duree_totale'] += data[category]['duree_totale']
            
            # Calcul des moyennes totales
            if data['total']['nb_interventions'] > 0:
                data['total']['cout_moyen'] = data['total']['cout_total'] / data['total']['nb_interventions']
                data['total']['duree_moyenne'] = data['total']['duree_totale'] / data['total']['nb_interventions']
            
            # Calcul des ratios
            data['ratios'] = {}
            if data['total']['cout_total'] > 0:
                data['ratios']['cout_preventif_pct'] = (data['preventif']['cout_total'] / data['total']['cout_total']) * 100
                data['ratios']['cout_curatif_pct'] = (data['curatif']['cout_total'] / data['total']['cout_total']) * 100
            else:
                data['ratios']['cout_preventif_pct'] = 0
                data['ratios']['cout_curatif_pct'] = 0
                
            if data['total']['nb_interventions'] > 0:
                data['ratios']['nb_preventif_pct'] = (data['preventif']['nb_interventions'] / data['total']['nb_interventions']) * 100
                data['ratios']['nb_curatif_pct'] = (data['curatif']['nb_interventions'] / data['total']['nb_interventions']) * 100
            else:
                data['ratios']['nb_preventif_pct'] = 0
                data['ratios']['nb_curatif_pct'] = 0
            
            logger.info(f"Analyse préventif vs curatif terminée - Interventions: {data['total']['nb_interventions']}")
            return data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse préventif vs curatif: {e}")
            raise DatabaseError(f"Impossible de récupérer l'analyse préventif vs curatif: {e}")
    
    # ===================================================================
    # MÉTHODES UTILITAIRES
    # ===================================================================

    def _calculer_tendances(self, periodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les tendances à partir d'une série de périodes.
        
        Args:
            periodes: Liste des données par période (ordre décroissant chronologique)
            
        Returns:
            Dictionnaire avec les tendances calculées
        """
        if len(periodes) < 2:
            return {'tendance_cout': 0, 'tendance_interventions': 0}
        
        # Prendre les 6 derniers vs 6 précédents (si assez de données)
        nb_periodes = len(periodes)
        milieu = nb_periodes // 2
        
        recentes = periodes[:milieu] if milieu > 0 else periodes
        precedentes = periodes[milieu:] if milieu > 0 else []
        
        cout_recent = sum(p.get('cout_total_periode', 0) for p in recentes)
        cout_precedent = sum(p.get('cout_total_periode', 0) for p in precedentes)
        
        interventions_recentes = sum(p.get('nb_interventions', 0) for p in recentes)
        interventions_precedentes = sum(p.get('nb_interventions', 0) for p in precedentes)
        
        # Calcul des tendances en pourcentage
        tendance_cout = 0
        if cout_precedent > 0:
            tendance_cout = ((cout_recent - cout_precedent) / cout_precedent) * 100
        
        tendance_interventions = 0
        if interventions_precedentes > 0:
            tendance_interventions = ((interventions_recentes - interventions_precedentes) / interventions_precedentes) * 100
        
        return {
            'tendance_cout': round(tendance_cout, 2),
            'tendance_interventions': round(tendance_interventions, 2),
            'cout_recent': cout_recent,
            'cout_precedent': cout_precedent,
            'interventions_recentes': interventions_recentes,
            'interventions_precedentes': interventions_precedentes
        }

    def get_resume_global(self, periode_debut: Union[str, date], periode_fin: Union[str, date]) -> Dict[str, Any]:
        """
        Récupère un résumé global des KPI sur une période.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            
        Returns:
            Dictionnaire avec le résumé global des KPI
        """
        try:
            # Récupération des KPI globaux depuis la vue détaillée
            sql = """
                SELECT 
                    COUNT(DISTINCT id_machine) AS nb_machines,
                    COUNT(DISTINCT id_site) AS nb_sites,
                    COUNT(DISTINCT id_equipe) AS nb_equipes,
                    COUNT(DISTINCT id_type_machine) AS nb_types_machines,
                    COUNT(*) AS nb_interventions_total,
                    
                    -- Répartition par type
                    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
                    COUNT(CASE WHEN type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
                    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
                    
                    -- Coûts totaux
                    SUM(cout_total) AS cout_total_global,
                    SUM(cout_main_oeuvre) AS cout_mod_global,
                    SUM(cout_pieces_internes) AS cout_pieces_global,
                    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_global,
                    
                    -- Moyennes
                    AVG(cout_total) AS cout_moyen_intervention,
                    AVG(duree_intervention_h) AS duree_moyenne_intervention,
                    
                    -- Extremes
                    MIN(cout_total) AS cout_min,
                    MAX(cout_total) AS cout_max
                    
                FROM v_maintenance_couts_detaille
                WHERE date_fin_reelle >= %s AND date_fin_reelle <= %s
            """
            
            params = [str(periode_debut), str(periode_fin)]
            
            logger.debug(f"Récupération résumé global - Période: {periode_debut} à {periode_fin}")
            row = fetch_one(sql, params)
            
            if row:
                result = dict(row)
                # Conversion des Decimal
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                
                # Calculs de pourcentages
                if result['nb_interventions_total'] > 0:
                    result['pourcentage_preventif'] = (result['nb_preventif'] / result['nb_interventions_total']) * 100
                    result['pourcentage_correctif'] = (result['nb_correctif'] / result['nb_interventions_total']) * 100
                    result['pourcentage_urgence'] = (result['nb_urgence'] / result['nb_interventions_total']) * 100
                
                if result['cout_total_global'] > 0:
                    result['pourcentage_cout_mod'] = (result['cout_mod_global'] / result['cout_total_global']) * 100
                    result['pourcentage_cout_pieces'] = (result['cout_pieces_global'] / result['cout_total_global']) * 100
                    result['pourcentage_cout_frais_externes'] = (result['cout_frais_externes_global'] / result['cout_total_global']) * 100
                
                # Calcul du ratio préventif/curatif
                if (result['nb_correctif'] + result['nb_urgence']) > 0:
                    result['ratio_preventif_curatif'] = result['nb_preventif'] / (result['nb_correctif'] + result['nb_urgence'])
                else:
                    result['ratio_preventif_curatif'] = 0
                
                result['periode_debut'] = str(periode_debut)
                result['periode_fin'] = str(periode_fin)
                
                logger.info(f"Résumé global calculé: {result['nb_interventions_total']} interventions, coût total: {result['cout_total_global']:.2f}€")
                return result
            else:
                return {}
                
        except DatabaseError as e:
            logger.error(f"Erreur récupération résumé global: {e}")
            raise

    # ===================================================================
    # MÉTHODES D'EXPORT
    # ===================================================================

    def export_kpi_excel(self, type_kpi: str, periode_debut: Union[str, date], 
                        periode_fin: Union[str, date], **kwargs) -> bytes:
        """
        Exporte les KPI au format Excel.
        
        Args:
            type_kpi: Type de KPI ('machine', 'site', 'equipe', 'global')
            periode_debut: Date de début
            periode_fin: Date de fin
            **kwargs: Paramètres supplémentaires selon le type
            
        Returns:
            Contenu du fichier Excel en bytes
        """
        # TODO: Implémenter l'export Excel avec openpyxl ou xlsxwriter
        raise NotImplementedError("Export Excel pas encore implémenté")

    def export_kpi_csv(self, type_kpi: str, periode_debut: Union[str, date], 
                      periode_fin: Union[str, date], **kwargs) -> str:
        """
        Exporte les KPI au format CSV.
        
        Args:
            type_kpi: Type de KPI ('machine', 'site', 'equipe', 'global')
            periode_debut: Date de début
            periode_fin: Date de fin
            **kwargs: Paramètres supplémentaires selon le type
            
        Returns:
            Contenu du fichier CSV
        """
        # TODO: Implémenter l'export CSV
        raise NotImplementedError("Export CSV pas encore implémenté")

    # ===================================================================
    # MÉTHODES UTILITAIRES
    # ===================================================================

    def _convert_date_to_string(self, date_value: Union[str, date]) -> str:
        """
        Convertit une date en chaîne de caractères au format YYYY-MM-DD.
        
        Args:
            date_value: Date à convertir (str ou date)
            
        Returns:
            Date au format string YYYY-MM-DD
        """
        if isinstance(date_value, str):
            return date_value
        elif isinstance(date_value, date):
            return date_value.strftime('%Y-%m-%d')
        else:
            raise ValueError(f"Type de date non supporté: {type(date_value)}")
    
    # ===================================================================
    # MÉTHODES UTILITAIRES SUPPLÉMENTAIRES
    # ===================================================================
    
    def get_kpi_summary_global(self, periode_debut: Union[str, date], periode_fin: Union[str, date]) -> Dict[str, Any]:
        """
        Résumé global de tous les KPI pour la période.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            
        Returns:
            Dictionnaire avec résumé global
        """
        try:
            # Récupérer tous les KPI
            machines_data = self.get_couts_par_machine(periode_debut, periode_fin)
            sites_data = self.get_couts_par_site(periode_debut, periode_fin)
            equipes_data = self.get_couts_par_equipe(periode_debut, periode_fin)
            preventif_data = self.get_preventif_vs_curatif(periode_debut, periode_fin)
            
            # Calculer les totaux
            total_cout = sum(machine.get('cout_total', 0) for machine in machines_data)
            total_interventions = sum(machine.get('nb_interventions_total', 0) for machine in machines_data)
            
            summary = {
                'periode': {
                    'debut': self._convert_date_to_string(periode_debut),
                    'fin': self._convert_date_to_string(periode_fin)
                },
                'totaux': {
                    'cout_total': total_cout,
                    'nb_interventions': total_interventions,
                    'nb_machines': len(machines_data),
                    'nb_sites': len(sites_data),
                    'nb_equipes': len(equipes_data),
                    'cout_moyen_intervention': total_cout / total_interventions if total_interventions > 0 else 0
                },
                'preventif_curatif': preventif_data,
                'top_machines': sorted(machines_data, key=lambda x: x.get('cout_total', 0), reverse=True)[:5],
                'top_sites': sorted(sites_data, key=lambda x: x.get('cout_total', 0), reverse=True)[:3],
                'machines': machines_data,
                'sites': sites_data,
                'equipes': equipes_data
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du résumé global: {e}")
            return {'error': str(e)}
        
    # ===================================================================
    # MÉTHODES INTERVENTIONS ET COÛTS PAR PÉRIODE
    # ===================================================================
    
    def get_interventions_by_period(self, machine_ids: List[int], start_date: Union[str, date], 
                                   end_date: Union[str, date], period_type: str) -> List[Dict[str, Any]]:
        """
        Récupère les interventions regroupées par période pour des machines spécifiques.
        
        Args:
            machine_ids: Liste des IDs de machines à analyser
            start_date: Date de début
            end_date: Date de fin
            period_type: Type de regroupement ('daily', 'weekly', 'monthly')
            
        Returns:
            Liste des interventions par période
        """
        try:
            debut_str = self._convert_date_to_string(start_date)
            fin_str = self._convert_date_to_string(end_date)
            
            # Construire la clause WHERE pour les machines
            machine_ids_str = ','.join(str(id) for id in machine_ids if id)
            if not machine_ids_str:
                return []
            
            # Définir le format de regroupement selon le type de période
            if period_type == 'daily':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM-DD')"
            elif period_type == 'weekly':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-\"W\"WW')"
            elif period_type == 'monthly':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM')"
            else:
                raise ValueError(f"Type de période non supporté: {period_type}")
            
            sql = f"""
                SELECT 
                    {date_format} AS period_key,
                    COUNT(*) AS intervention_count,
                    COUNT(CASE WHEN m.type_reel = 'Preventif' THEN 1 END) AS preventif_count,
                    COUNT(CASE WHEN m.type_reel = 'Correctif' THEN 1 END) AS correctif_count,
                    COUNT(CASE WHEN m.type_reel = 'Urgence' THEN 1 END) AS urgence_count,
                    SUM(COALESCE(m.duree_intervention_h, 0)) AS total_duration_hours,
                    AVG(COALESCE(m.duree_intervention_h, 0)) AS avg_duration_per_intervention
                FROM MAINTENANCE m
                WHERE m.machine_id IN ({machine_ids_str})
                    AND m.date_fin_reelle >= %s
                    AND m.date_fin_reelle <= %s
                    AND m.date_fin_reelle IS NOT NULL
                GROUP BY {date_format}
                ORDER BY {date_format}
            """
            
            params = [debut_str, fin_str]
            
            logger.debug(f"Récupération interventions par période - Machines: {machine_ids}, Période: {debut_str} à {fin_str}, Type: {period_type}")
            rows = fetch_all(sql, params)
            
            results = []
            for row in rows:
                result = dict(row)
                results.append(result)
            
            logger.info(f"Interventions par période récupérées: {len(results)} périodes")
            return results
            
        except Exception as e:
            logger.error(f"Erreur récupération interventions par période: {e}")
            return []
    
    def get_costs_by_period(self, machine_ids: List[int], start_date: Union[str, date], 
                           end_date: Union[str, date], period_type: str) -> List[Dict[str, Any]]:
        """
        Récupère les coûts regroupés par période pour des machines spécifiques.
        
        Args:
            machine_ids: Liste des IDs de machines à analyser
            start_date: Date de début
            end_date: Date de fin
            period_type: Type de regroupement ('daily', 'weekly', 'monthly')
            
        Returns:
            Liste des coûts par période
        """
        try:
            debut_str = self._convert_date_to_string(start_date)
            fin_str = self._convert_date_to_string(end_date)
            
            # Construire la clause WHERE pour les machines
            machine_ids_str = ','.join(str(id) for id in machine_ids if id)
            if not machine_ids_str:
                return []
            
            # Définir le format de regroupement selon le type de période
            if period_type == 'daily':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM-DD')"
            elif period_type == 'weekly':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-\"W\"WW')"
            elif period_type == 'monthly':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM')"
            else:
                raise ValueError(f"Type de période non supporté: {period_type}")
            
            sql = f"""
                SELECT 
                    {date_format} AS period_key,
                    SUM(COALESCE(m.cout_total, 0)) AS total_cost,
                    SUM(COALESCE(m.cout_main_oeuvre, 0)) AS labor_cost,
                    SUM(COALESCE(m.cout_pieces_internes, 0)) AS parts_cost,
                    SUM(COALESCE(m.cout_pieces_externes, 0)) AS external_parts_cost,
                    SUM(COALESCE(m.cout_autres_frais, 0)) AS other_costs,
                    COUNT(*) AS intervention_count,
                    AVG(COALESCE(m.cout_total, 0)) AS avg_cost_per_intervention,
                    SUM(COALESCE(m.duree_intervention_h, 0)) AS total_duration_hours,
                    AVG(COALESCE(m.duree_intervention_h, 0)) AS avg_duration_per_intervention
                FROM MAINTENANCE m
                WHERE m.machine_id IN ({machine_ids_str})
                    AND m.date_fin_reelle >= %s
                    AND m.date_fin_reelle <= %s
                    AND m.date_fin_reelle IS NOT NULL
                GROUP BY {date_format}
                ORDER BY {date_format}
            """
            
            params = [debut_str, fin_str]
            
            logger.debug(f"Récupération coûts par période - Machines: {machine_ids}, Période: {debut_str} à {fin_str}, Type: {period_type}")
            rows = fetch_all(sql, params)
            
            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)
            
            logger.info(f"Coûts par période récupérés: {len(results)} périodes")
            return results
            
        except Exception as e:
            logger.error(f"Erreur récupération coûts par période: {e}")
            return []
    
    def get_site_costs_by_period(self, site_ids: List[int], start_date: Union[str, date], 
                                end_date: Union[str, date], period_type: str) -> List[Dict[str, Any]]:
        """
        Récupère les coûts et interventions regroupés par période pour des sites spécifiques.
        
        Args:
            site_ids: Liste des IDs de sites à analyser (vide = tous les sites)
            start_date: Date de début
            end_date: Date de fin
            period_type: Type de regroupement ('daily', 'weekly', 'monthly')
            
        Returns:
            Liste des coûts et interventions par période
        """
        try:
            debut_str = self._convert_date_to_string(start_date)
            fin_str = self._convert_date_to_string(end_date)
            
            # Construire la clause WHERE pour les sites
            site_filter = ""
            if site_ids:
                site_ids_str = ','.join(str(id) for id in site_ids if id)
                if site_ids_str:
                    site_filter = f"AND ma.site_id IN ({site_ids_str})"
            
            # Définir le format de regroupement selon le type de période
            if period_type == 'daily':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM-DD')"
            elif period_type == 'weekly':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-\"W\"WW')"
            elif period_type == 'monthly':
                date_format = "TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM')"
            else:
                raise ValueError(f"Type de période non supporté: {period_type}")
            
            sql = f"""
                SELECT 
                    {date_format} AS period_key,
                    SUM(COALESCE(m.cout_total, 0)) AS total_cost,
                    SUM(COALESCE(m.cout_main_oeuvre, 0)) AS labor_cost,
                    SUM(COALESCE(m.cout_pieces_internes, 0)) AS parts_cost,
                    SUM(COALESCE(m.cout_pieces_externes, 0)) AS external_parts_cost,
                    SUM(COALESCE(m.cout_autres_frais, 0)) AS other_costs,
                    COUNT(DISTINCT m.id_maintenance) AS intervention_count,
                    CASE 
                        WHEN COUNT(DISTINCT m.id_maintenance) > 0 
                        THEN SUM(COALESCE(m.cout_total, 0)) / COUNT(DISTINCT m.id_maintenance)
                        ELSE 0 
                    END AS avg_cost_per_intervention,
                    SUM(COALESCE(m.duree_intervention_h, 0)) AS total_duration_hours,
                    CASE 
                        WHEN COUNT(DISTINCT m.id_maintenance) > 0 
                        THEN SUM(COALESCE(m.duree_intervention_h, 0)) / COUNT(DISTINCT m.id_maintenance)
                        ELSE 0 
                    END AS avg_duration_per_intervention,
                    COUNT(DISTINCT m.machine_id) AS machines_involved
                FROM MAINTENANCE m
                LEFT JOIN MACHINE ma ON m.machine_id = ma.id_machine
                WHERE m.date_fin_reelle >= %s
                    AND m.date_fin_reelle <= %s
                    AND m.date_fin_reelle IS NOT NULL
                    AND m.machine_id IS NOT NULL
                    {site_filter}
                GROUP BY {date_format}
                ORDER BY {date_format}
            """
            
            params = [debut_str, fin_str]
            
            logger.debug(f"Récupération coûts sites par période - Sites: {site_ids}, Période: {debut_str} à {fin_str}, Type: {period_type}")
            rows = fetch_all(sql, params)
            
            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)
            
            logger.info(f"Coûts sites par période récupérés: {len(results)} périodes")
            return results
            
        except Exception as e:
            logger.error(f"Erreur récupération coûts sites par période: {e}")
            return []
    
    def get_all_sites(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les sites disponibles dans la base de données.
        
        Returns:
            Liste des sites avec leurs informations de base
        """
        try:
            sql = """
                SELECT 
                    id_site,
                    nom AS site_nom,
                    ville,
                    pays,
                    adresse,
                    contact_principal
                FROM SITE
                ORDER BY nom
            """
            
            logger.debug("Récupération de tous les sites")
            rows = fetch_all(sql, [])
            
            results = []
            for row in rows:
                results.append(dict(row))
            
            logger.info(f"Sites récupérés: {len(results)} sites")
            return results
            
        except Exception as e:
            logger.error(f"Erreur récupération sites: {e}")
            raise
    
    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les équipes disponibles dans la base de données.
        
        Returns:
            Liste des équipes avec leurs informations de base
        """
        try:
            sql = """
                SELECT DISTINCT
                    e.id_equipe,
                    e.nom as equipe_nom,
                    e.domaine_expertise
                FROM equipe e
                WHERE e.nom IS NOT NULL
                ORDER BY e.nom
            """
            
            logger.debug("Récupération de toutes les équipes")
            rows = fetch_all(sql, [])
            
            results = []
            for row in rows:
                results.append(dict(row))
            
            logger.info(f"Équipes récupérées: {len(results)} équipes")
            return results
            
        except Exception as e:
            logger.error(f"Erreur récupération équipes: {e}")
            raise

    def get_teams_with_data(self, periode_debut: Union[str, date], periode_fin: Union[str, date]) -> List[Dict[str, Any]]:
        """
        Récupère toutes les équipes ayant des données d'interventions sur la période donnée.
        Cette méthode permet de s'assurer qu'aucune équipe (comme shift01) n'est oubliée.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            
        Returns:
            Liste des équipes avec leurs KPI de base sur la période
        """
        try:
            # Utilisation du query builder pour générer la requête SQL
            sql_query, params = KPIQueryBuilder.build_all_teams_with_data_query(
                periode_debut=periode_debut,
                periode_fin=periode_fin
            )

            logger.debug(f"Récupération équipes avec données - Période: {periode_debut} à {periode_fin}")
            rows = fetch_all(sql_query, params)

            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal en float pour la sérialisation JSON
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)

            logger.info(f"Équipes avec données récupérées: {len(results)} équipes sur période {periode_debut}-{periode_fin}")
            return results

        except DatabaseError as e:
            logger.error(f"Erreur récupération équipes avec données: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue équipes avec données: {e}")
            raise

    def get_couts_par_machine_toutes_equipes(self, periode_debut: Union[str, date], periode_fin: Union[str, date],
                                            machine_ids: Optional[List[int]] = None, type_machine: Optional[str] = None,
                                            site_id: Optional[int] = None, equipe_id: Optional[int] = None,
                                            limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Version alternative de get_couts_par_machine qui retourne toutes les équipes,
        même les moins actives comme shift01. Peut retourner plusieurs lignes par machine.
        
        Args:
            periode_debut: Date de début
            periode_fin: Date de fin
            machine_ids: Filtre par une liste d'IDs de machine (optionnel)
            type_machine: Filtre par type de machine (optionnel)
            site_id: Filtre par ID de site (optionnel)
            equipe_id: Filtre par équipe (optionnel)
            limite: Nombre max de résultats (optionnel)

        Returns:
            Liste des machines avec leurs KPI financiers par équipe
        """
        try:
            # Utilisation du query builder pour générer la requête SQL
            sql_query, params = KPIQueryBuilder.build_machine_kpi_query_all_teams(
                periode_debut=periode_debut,
                periode_fin=periode_fin,
                machine_ids=machine_ids,
                type_machine=type_machine,
                site_id=site_id,
                equipe_id=equipe_id,
                limite=limite
            )

            logger.debug(f"Exécution requête KPI machines toutes équipes - Période: {periode_debut} à {periode_fin}")
            rows = fetch_all(sql_query, params)

            results = []
            for row in rows:
                result = dict(row)
                # Conversion des Decimal en float pour la sérialisation JSON
                for key, value in result.items():
                    if isinstance(value, Decimal):
                        result[key] = float(value)
                results.append(result)

            logger.info(f"KPI machines toutes équipes récupérés: {len(results)} résultats sur période {periode_debut}-{periode_fin}")
            return results

        except DatabaseError as e:
            logger.error(f"Erreur récupération KPI machines toutes équipes: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue KPI machines toutes équipes: {e}")
            raise
