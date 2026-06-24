# gmao_app/app/core/services/kpi_query_builder.py
"""
Constructeur de requêtes SQL pour les KPI.
Centralise et factorise les requêtes communes.
"""
from typing import Dict, List, Optional, Union, Any
from datetime import date


class KPIQueryBuilder:
    """
    Classe utilitaire pour construire les requêtes SQL des KPI.
    Évite la duplication de code et centralise la logique SQL.
    """

    @staticmethod
    def build_machine_kpi_query(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date],
        machine_ids: Optional[List[int]] = None,
        type_machine: Optional[str] = None,
        site_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        limite: Optional[int] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Construit la requête pour les KPI par machine.
        
        Returns:
            Tuple (requête SQL, paramètres)
        """
        params = {
            'start_date': periode_debut,
            'end_date': periode_fin,
            'machine_ids': machine_ids,
            'type_machine': type_machine,
            'site_id': site_id,
            'equipe_id': equipe_id
        }

        sql_query = """
            WITH MachineKPI AS (
                SELECT
                    m.machine_id,
                    COUNT(*) as nb_interventions_total,
                    COUNT(CASE WHEN m.type_reel = 'Preventif' THEN 1 END) as nb_preventif,
                    COUNT(CASE WHEN m.type_reel = 'Correctif' THEN 1 END) as nb_correctif,
                    COUNT(CASE WHEN m.type_reel = 'Urgence' THEN 1 END) as nb_urgence,
                    COALESCE(SUM(m.cout_total), 0) as cout_total_periode,
                    COALESCE(SUM(m.cout_main_oeuvre), 0) as cout_mo_periode,
                    COALESCE(SUM(m.cout_pieces_internes), 0) as cout_pieces_periode,
                    COALESCE(SUM(m.cout_pieces_externes + m.cout_autres_frais), 0) as cout_externes_periode,
                    COALESCE(SUM(m.duree_intervention_h), 0) as duree_totale
                FROM
                    maintenance m
                WHERE
                    m.date_debut_reelle::date BETWEEN %(start_date)s AND %(end_date)s
                    AND m.machine_id IS NOT NULL
                GROUP BY
                    m.machine_id
            )
            SELECT
                m.id_machine AS machine_id,
                m.nom AS machine_nom,
                m.serial AS machine_serial,
                tm.nom AS type_nom,
                m.criticite AS machine_criticite,
                s.nom AS site_nom,
                e_ranked.equipe_nom AS equipe_nom,
                COALESCE(kpi.cout_total_periode, 0) AS cout_total,
                COALESCE(kpi.nb_interventions_total, 0) AS nb_interventions_total,
                COALESCE(kpi.nb_preventif, 0) AS nb_preventif,
                COALESCE(kpi.nb_correctif, 0) AS nb_correctif,
                COALESCE(kpi.nb_urgence, 0) AS nb_urgence,
                CASE
                    WHEN COALESCE(kpi.nb_interventions_total, 0) > 0 THEN
                        COALESCE(kpi.cout_total_periode, 0) / kpi.nb_interventions_total
                    ELSE 0
                END AS cout_moyen_intervention,
                COALESCE(kpi.cout_mo_periode, 0) AS cout_main_oeuvre,
                COALESCE(kpi.cout_pieces_periode, 0) AS cout_pieces_internes,
                COALESCE(kpi.cout_externes_periode, 0) AS cout_frais_externes,
                CASE
                    WHEN COALESCE(kpi.nb_correctif, 0) > 0 THEN
                        COALESCE(kpi.nb_preventif, 0)::FLOAT / kpi.nb_correctif
                    ELSE 0
                END AS ratio_preventif_curatif,
                CASE
                    WHEN COALESCE(kpi.cout_total_periode, 0) > 0 THEN
                        COALESCE(kpi.cout_mo_periode, 0) * 100.0 / kpi.cout_total_periode
                    ELSE 0
                END AS pourcentage_mod,
                CASE
                    WHEN COALESCE(kpi.cout_total_periode, 0) > 0 THEN
                        COALESCE(kpi.cout_pieces_periode, 0) * 100.0 / kpi.cout_total_periode
                    ELSE 0
                END AS pourcentage_pieces,
                CASE
                    WHEN COALESCE(kpi.cout_total_periode, 0) > 0 THEN
                        COALESCE(kpi.cout_externes_periode, 0) * 100.0 / kpi.cout_total_periode
                    ELSE 0
                END AS pourcentage_frais_externes,
                COALESCE(kpi.duree_totale, 0) AS duree_intervention_totale,
                CASE
                    WHEN COALESCE(kpi.nb_interventions_total, 0) > 0 THEN
                        COALESCE(kpi.duree_totale, 0) / kpi.nb_interventions_total
                    ELSE 0
                END AS duree_intervention_moyenne
            FROM
                machine m
            LEFT JOIN
                type_machine tm ON m.type_machine_id = tm.id_type_machine
            LEFT JOIN
                site s ON m.site_id = s.id_site
            LEFT JOIN
                MachineKPI kpi ON m.id_machine = kpi.machine_id
            LEFT JOIN (
                SELECT 
                    m2.machine_id,
                    e.nom as equipe_nom,
                    COUNT(*) as nb_interventions_equipe,
                    ROW_NUMBER() OVER (PARTITION BY m2.machine_id ORDER BY COUNT(*) DESC, MAX(m2.date_debut_reelle) DESC) as rn
                FROM maintenance m2
                LEFT JOIN technicien t ON m2.technicien_id = t.id_technicien
                LEFT JOIN equipe e ON t.equipe_id = e.id_equipe
                WHERE m2.date_debut_reelle::date BETWEEN %(start_date)s AND %(end_date)s
                  AND e.nom IS NOT NULL
                GROUP BY m2.machine_id, e.nom
            ) e_ranked ON m.id_machine = e_ranked.machine_id AND e_ranked.rn = 1
            WHERE
                (%(machine_ids)s IS NULL OR m.id_machine = ANY(%(machine_ids)s))
                AND (%(type_machine)s IS NULL OR tm.nom = %(type_machine)s)
                AND (%(site_id)s IS NULL OR m.site_id = %(site_id)s)
                AND (%(equipe_id)s IS NULL OR e_ranked.equipe_nom = %(equipe_id)s)
            ORDER BY
                COALESCE(kpi.cout_total_periode, 0) DESC
        """

        if limite:
            sql_query += " LIMIT %(limite)s"
            params['limite'] = limite

        return sql_query, params

    @staticmethod
    def build_site_kpi_query(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date]
    ) -> tuple[str, List[Any]]:
        """
        Construit la requête pour les KPI par site (sans vues).
        """
        sql = """
            WITH SiteKPI AS (
                SELECT
                    s.id_site,
                    s.nom as site_nom,
                    s.ville as site_ville,
                    s.pays as site_pays,
                    COUNT(DISTINCT m.id_machine) as nb_machines,
                    COUNT(*) as nb_interventions_total,
                    COUNT(CASE WHEN maint.type_reel = 'Preventif' THEN 1 END) as nb_preventif,
                    COUNT(CASE WHEN maint.type_reel = 'Correctif' THEN 1 END) as nb_correctif,
                    COUNT(CASE WHEN maint.type_reel = 'Urgence' THEN 1 END) as nb_urgence,
                    COALESCE(SUM(maint.cout_total), 0) as cout_total,
                    COALESCE(SUM(maint.cout_main_oeuvre), 0) as cout_main_oeuvre,
                    COALESCE(SUM(maint.cout_pieces_internes), 0) as cout_pieces_internes,
                    COALESCE(SUM(maint.cout_pieces_externes + maint.cout_autres_frais), 0) as cout_frais_externes,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            COALESCE(SUM(maint.cout_total), 0) / COUNT(*)
                        ELSE 0
                    END as cout_moyen_intervention,
                    CASE
                        WHEN COUNT(DISTINCT m.id_machine) > 0 THEN
                            COALESCE(SUM(maint.cout_total), 0) / COUNT(DISTINCT m.id_machine)
                        ELSE 0
                    END as cout_moyen_par_machine,
                    CASE
                        WHEN COUNT(CASE WHEN maint.type_reel = 'Correctif' THEN 1 END) > 0 THEN
                            COUNT(CASE WHEN maint.type_reel = 'Preventif' THEN 1 END)::FLOAT / 
                            COUNT(CASE WHEN maint.type_reel = 'Correctif' THEN 1 END)
                        ELSE 0
                    END as ratio_preventif_curatif
                FROM
                    site s
                LEFT JOIN
                    machine m ON s.id_site = m.site_id
                LEFT JOIN
                    maintenance maint ON m.id_machine = maint.machine_id
                WHERE
                    maint.date_debut_reelle::date BETWEEN %s AND %s
                    OR maint.date_debut_reelle IS NULL
                GROUP BY
                    s.id_site, s.nom, s.ville, s.pays
            )
            SELECT * FROM SiteKPI
            WHERE cout_total > 0 OR nb_machines > 0
            ORDER BY cout_total DESC
        """
        
        params = [periode_debut, periode_fin]
        return sql, params

    @staticmethod
    def build_equipe_kpi_query(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date],
        equipe_id: Optional[int] = None
    ) -> tuple[str, List[Any]]:
        """
        Construit la requête pour les KPI par équipe (sans vues).
        """
        where_conditions = ["maint.date_debut_reelle::date BETWEEN %s AND %s"]
        params = [periode_debut, periode_fin]
        
        if equipe_id:
            where_conditions.append("e.id_equipe = %s")
            params.append(equipe_id)
        
        where_clause = " AND ".join(where_conditions)
        
        sql = f"""
            WITH EquipeKPI AS (
                SELECT
                    e.id_equipe,
                    e.nom as equipe_nom,
                    e.domaine_expertise as equipe_domaine,
                    COUNT(DISTINCT t.id_technicien) as nb_techniciens_actifs,
                    COUNT(*) as nb_interventions_total,
                    COUNT(CASE WHEN maint.type_reel = 'Preventif' THEN 1 END) as nb_preventif,
                    COUNT(CASE WHEN maint.type_reel = 'Correctif' THEN 1 END) as nb_correctif,
                    COUNT(CASE WHEN maint.type_reel = 'Urgence' THEN 1 END) as nb_urgence,
                    COALESCE(SUM(maint.cout_total), 0) as cout_total,
                    COALESCE(SUM(maint.cout_main_oeuvre), 0) as cout_main_oeuvre,
                    COALESCE(SUM(maint.cout_pieces_internes), 0) as cout_pieces_internes,
                    COALESCE(SUM(maint.cout_pieces_externes + maint.cout_autres_frais), 0) as cout_frais_externes,
                    COALESCE(SUM(maint.duree_intervention_h), 0) as heures_totales,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            COALESCE(SUM(maint.cout_total), 0) / COUNT(*)
                        ELSE 0
                    END as cout_moyen_intervention,
                    CASE
                        WHEN COUNT(DISTINCT t.id_technicien) > 0 THEN
                            COALESCE(SUM(maint.cout_total), 0) / COUNT(DISTINCT t.id_technicien)
                        ELSE 0
                    END as cout_moyen_par_technicien,
                    CASE
                        WHEN COALESCE(SUM(maint.duree_intervention_h), 0) > 0 THEN
                            COALESCE(SUM(maint.cout_total), 0) / SUM(maint.duree_intervention_h)
                        ELSE 0
                    END as cout_par_heure,
                    CASE
                        WHEN COUNT(DISTINCT t.id_technicien) > 0 THEN
                            COUNT(*)::FLOAT / COUNT(DISTINCT t.id_technicien)
                        ELSE 0
                    END as interventions_par_technicien
                FROM
                    equipe e
                LEFT JOIN
                    technicien t ON e.id_equipe = t.equipe_id
                LEFT JOIN
                    maintenance maint ON t.id_technicien = maint.technicien_id
                WHERE
                    {where_clause}
                    OR maint.date_debut_reelle IS NULL
                GROUP BY
                    e.id_equipe, e.nom, e.domaine_expertise
            )
            SELECT * FROM EquipeKPI
            WHERE cout_total > 0 OR nb_techniciens_actifs > 0
            ORDER BY cout_total DESC
        """
        
        return sql, params

    @staticmethod
    def build_preventif_curatif_query(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date],
        site_id: Optional[int] = None,
        machine_id: Optional[int] = None
    ) -> tuple[str, List[Any]]:
        """
        Construit la requête pour l'analyse préventif vs curatif.
        """
        where_conditions = ["m.date_fin_reelle BETWEEN %s AND %s"]
        params = [periode_debut, periode_fin]
        
        if site_id:
            where_conditions.append("mach.site_id = %s")
            params.append(site_id)
            
        if machine_id:
            where_conditions.append("mach.id_machine = %s")
            params.append(machine_id)
        
        where_clause = " AND ".join(where_conditions)
        
        sql = f"""
            SELECT 
                m.type_reel as type_intervention,
                COUNT(*) as nb_interventions,
                SUM(COALESCE(m.cout_total, 0)) as cout_total,
                AVG(COALESCE(m.cout_total, 0)) as cout_moyen,
                SUM(COALESCE(m.duree_intervention_h, 0)) as duree_totale,
                AVG(COALESCE(m.duree_intervention_h, 0)) as duree_moyenne
            FROM maintenance m
            JOIN machine mach ON m.machine_id = mach.id_machine
            WHERE {where_clause}
            GROUP BY m.type_reel
            ORDER BY m.type_reel
        """
        
        return sql, params

    @staticmethod
    def build_resume_global_query(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date]
    ) -> tuple[str, List[Any]]:
        """
        Construit la requête pour le résumé global (sans vues).
        """
        sql = """
            SELECT 
                COUNT(DISTINCT m.machine_id) AS nb_machines,
                COUNT(DISTINCT ma.site_id) AS nb_sites,
                COUNT(DISTINCT t.equipe_id) AS nb_equipes,
                COUNT(DISTINCT ma.type_machine_id) AS nb_types_machines,
                COUNT(*) AS nb_interventions_total,
                
                -- Répartition par type
                COUNT(CASE WHEN m.type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
                COUNT(CASE WHEN m.type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
                COUNT(CASE WHEN m.type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
                
                -- Coûts totaux
                SUM(m.cout_total) AS cout_total_global,
                SUM(m.cout_main_oeuvre) AS cout_mod_global,
                SUM(m.cout_pieces_internes) AS cout_pieces_global,
                SUM(m.cout_pieces_externes + m.cout_autres_frais) AS cout_frais_externes_global,
                
                -- Moyennes
                AVG(m.cout_total) AS cout_moyen_intervention,
                AVG(m.duree_intervention_h) AS duree_moyenne_intervention,
                
                -- Extremes
                MIN(m.cout_total) AS cout_min,
                MAX(m.cout_total) AS cout_max
                
            FROM maintenance m
            LEFT JOIN machine ma ON m.machine_id = ma.id_machine
            LEFT JOIN technicien t ON m.technicien_id = t.id_technicien
            WHERE m.date_fin_reelle >= %s AND m.date_fin_reelle <= %s
        """
        
        params = [periode_debut, periode_fin]
        return sql, params

    @staticmethod
    def build_machine_trends_query(machine_id: int, nb_periodes: int = 12) -> tuple[str, List]:
        """
        Construit la requête pour les tendances d'une machine sur plusieurs périodes.
        
        Args:
            machine_id: ID de la machine
            nb_periodes: Nombre de mois à analyser
            
        Returns:
            Tuple (requête SQL, paramètres)
        """
        sql = """
            WITH MoisPeriodes AS (
                SELECT 
                    generate_series(
                        date_trunc('month', CURRENT_DATE) - interval '%s months',
                        date_trunc('month', CURRENT_DATE),
                        interval '1 month'
                    )::date as periode_debut
            ),
            KPIMensuel AS (
                SELECT 
                    date_trunc('month', m.date_debut_reelle::date) as periode_debut,
                    EXTRACT(year FROM m.date_debut_reelle::date) as annee,
                    EXTRACT(month FROM m.date_debut_reelle::date) as mois,
                    COUNT(*) as nb_interventions,
                    COUNT(CASE WHEN ot.type = 'Preventif' THEN 1 END) as nb_preventif,
                    COUNT(CASE WHEN ot.type = 'Correctif' THEN 1 END) as nb_correctif,
                    COUNT(CASE WHEN ot.urgence > 3 THEN 1 END) as nb_urgence,
                    COALESCE(SUM(m.cout_total), 0) as cout_total_periode,
                    COALESCE(SUM(m.cout_main_oeuvre), 0) as cout_mod_periode,
                    COALESCE(SUM(m.cout_pieces_internes), 0) as cout_pieces_periode,
                    COALESCE(SUM(m.cout_pieces_externes + m.cout_autres_frais), 0) as cout_frais_externes_periode,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            COALESCE(SUM(m.cout_total), 0) / COUNT(*)
                        ELSE 0
                    END as cout_moyen_intervention,
                    CASE
                        WHEN COUNT(CASE WHEN ot.type = 'Correctif' THEN 1 END) > 0 THEN
                            COUNT(CASE WHEN ot.type = 'Preventif' THEN 1 END)::FLOAT / 
                            COUNT(CASE WHEN ot.type = 'Correctif' THEN 1 END)
                        ELSE 0
                    END as ratio_preventif_curatif
                FROM
                    maintenance m
                INNER JOIN
                    ordre_travail ot ON m.ot_id = ot.id_ot
                WHERE
                    m.machine_id = %s
                    AND m.date_debut_reelle::date >= (CURRENT_DATE - interval '%s months')
                GROUP BY
                    date_trunc('month', m.date_debut_reelle::date),
                    EXTRACT(year FROM m.date_debut_reelle::date),
                    EXTRACT(month FROM m.date_debut_reelle::date)
            )
            SELECT 
                to_char(mp.periode_debut, 'YYYY-MM') as periode_mois,
                EXTRACT(year FROM mp.periode_debut) as annee,
                EXTRACT(month FROM mp.periode_debut) as mois,
                COALESCE(kpi.nb_interventions, 0) as nb_interventions,
                COALESCE(kpi.nb_preventif, 0) as nb_preventif,
                COALESCE(kpi.nb_correctif, 0) as nb_correctif,
                COALESCE(kpi.nb_urgence, 0) as nb_urgence,
                COALESCE(kpi.cout_total_periode, 0) as cout_total_periode,
                COALESCE(kpi.cout_mod_periode, 0) as cout_mod_periode,
                COALESCE(kpi.cout_pieces_periode, 0) as cout_pieces_periode,
                COALESCE(kpi.cout_frais_externes_periode, 0) as cout_frais_externes_periode,
                COALESCE(kpi.cout_moyen_intervention, 0) as cout_moyen_intervention,
                COALESCE(kpi.ratio_preventif_curatif, 0) as ratio_preventif_curatif
            FROM MoisPeriodes mp
            LEFT JOIN KPIMensuel kpi ON mp.periode_debut = kpi.periode_debut
            ORDER BY mp.periode_debut DESC
            LIMIT %s
        """
        
        params = [nb_periodes - 1, machine_id, nb_periodes - 1, nb_periodes]
        return sql, params

    @staticmethod
    def build_all_teams_with_data_query(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date]
    ) -> tuple[str, List[Any]]:
        """
        Construit la requête pour récupérer toutes les équipes ayant des données 
        d'interventions sur la période, incluant celles moins actives comme shift01.
        """
        sql = """
            SELECT DISTINCT
                e.id_equipe,
                e.nom as equipe_nom,
                e.domaine_expertise,
                COUNT(m.id_maintenance) as nb_interventions_periode,
                COALESCE(SUM(m.cout_total), 0) as cout_total_periode
            FROM equipe e
            LEFT JOIN technicien t ON e.id_equipe = t.equipe_id
            LEFT JOIN maintenance m ON t.id_technicien = m.technicien_id
            WHERE (m.date_debut_reelle::date BETWEEN %s AND %s OR m.date_debut_reelle IS NULL)
                AND e.nom IS NOT NULL
            GROUP BY e.id_equipe, e.nom, e.domaine_expertise
            HAVING COUNT(m.id_maintenance) > 0 OR e.nom IS NOT NULL
            ORDER BY e.nom
        """
        
        params = [periode_debut, periode_fin]
        return sql, params

    @staticmethod
    def build_machine_kpi_query_all_teams(
        periode_debut: Union[str, date], 
        periode_fin: Union[str, date],
        machine_ids: Optional[List[int]] = None,
        type_machine: Optional[str] = None,
        site_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        limite: Optional[int] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Version alternative qui retourne plusieurs lignes par machine si elle a été 
        maintenue par plusieurs équipes. Utile pour ne pas perdre les équipes moins actives.
        """
        params = {
            'start_date': periode_debut,
            'end_date': periode_fin,
            'machine_ids': machine_ids,
            'type_machine': type_machine,
            'site_id': site_id,
            'equipe_id': equipe_id
        }

        sql_query = """
            WITH MachineEquipeKPI AS (
                SELECT
                    m.machine_id,
                    e.nom as equipe_nom,
                    COUNT(*) as nb_interventions_total,
                    COUNT(CASE WHEN m.type_reel = 'Preventif' THEN 1 END) as nb_preventif,
                    COUNT(CASE WHEN m.type_reel = 'Correctif' THEN 1 END) as nb_correctif,
                    COUNT(CASE WHEN m.type_reel = 'Urgence' THEN 1 END) as nb_urgence,
                    COALESCE(SUM(m.cout_total), 0) as cout_total_periode,
                    COALESCE(SUM(m.cout_main_oeuvre), 0) as cout_mo_periode,
                    COALESCE(SUM(m.cout_pieces_internes), 0) as cout_pieces_periode,
                    COALESCE(SUM(m.cout_pieces_externes + m.cout_autres_frais), 0) as cout_externes_periode,
                    COALESCE(SUM(m.duree_intervention_h), 0) as duree_totale
                FROM maintenance m
                LEFT JOIN technicien t ON m.technicien_id = t.id_technicien
                LEFT JOIN equipe e ON t.equipe_id = e.id_equipe
                WHERE
                    m.date_debut_reelle::date BETWEEN %(start_date)s AND %(end_date)s
                    AND m.machine_id IS NOT NULL
                    AND e.nom IS NOT NULL
                GROUP BY
                    m.machine_id, e.nom
            )
            SELECT
                ma.id_machine AS machine_id,
                ma.nom AS machine_nom,
                ma.serial AS machine_serial,
                tm.nom AS type_nom,
                ma.criticite AS machine_criticite,
                s.nom AS site_nom,
                kpi.equipe_nom AS equipe_nom,
                COALESCE(kpi.cout_total_periode, 0) AS cout_total,
                COALESCE(kpi.nb_interventions_total, 0) AS nb_interventions_total,
                COALESCE(kpi.nb_preventif, 0) AS nb_preventif,
                COALESCE(kpi.nb_correctif, 0) AS nb_correctif,
                COALESCE(kpi.nb_urgence, 0) AS nb_urgence,
                CASE
                    WHEN COALESCE(kpi.nb_interventions_total, 0) > 0 THEN
                        COALESCE(kpi.cout_total_periode, 0) / kpi.nb_interventions_total
                    ELSE 0
                END AS cout_moyen_intervention,
                COALESCE(kpi.cout_mo_periode, 0) AS cout_main_oeuvre,
                COALESCE(kpi.cout_pieces_periode, 0) AS cout_pieces_internes,
                COALESCE(kpi.cout_externes_periode, 0) AS cout_frais_externes,
                CASE
                    WHEN COALESCE(kpi.nb_correctif, 0) > 0 THEN
                        COALESCE(kpi.nb_preventif, 0)::FLOAT / kpi.nb_correctif
                    ELSE 0
                END AS ratio_preventif_curatif,
                CASE
                    WHEN COALESCE(kpi.cout_total_periode, 0) > 0 THEN
                        COALESCE(kpi.cout_mo_periode, 0) * 100.0 / kpi.cout_total_periode
                    ELSE 0
                END AS pourcentage_mod,
                CASE
                    WHEN COALESCE(kpi.cout_total_periode, 0) > 0 THEN
                        COALESCE(kpi.cout_pieces_periode, 0) * 100.0 / kpi.cout_total_periode
                    ELSE 0
                END AS pourcentage_pieces,
                CASE
                    WHEN COALESCE(kpi.cout_total_periode, 0) > 0 THEN
                        COALESCE(kpi.cout_externes_periode, 0) * 100.0 / kpi.cout_total_periode
                    ELSE 0
                END AS pourcentage_frais_externes,
                COALESCE(kpi.duree_totale, 0) AS duree_intervention_totale,
                CASE
                    WHEN COALESCE(kpi.nb_interventions_total, 0) > 0 THEN
                        COALESCE(kpi.duree_totale, 0) / kpi.nb_interventions_total
                    ELSE 0
                END AS duree_intervention_moyenne
            FROM machine ma
            LEFT JOIN type_machine tm ON ma.type_machine_id = tm.id_type_machine
            LEFT JOIN site s ON ma.site_id = s.id_site
            INNER JOIN MachineEquipeKPI kpi ON ma.id_machine = kpi.machine_id
            WHERE
                (%(machine_ids)s IS NULL OR ma.id_machine = ANY(%(machine_ids)s))
                AND (%(type_machine)s IS NULL OR tm.nom = %(type_machine)s)
                AND (%(site_id)s IS NULL OR ma.site_id = %(site_id)s)
                AND (%(equipe_id)s IS NULL OR kpi.equipe_nom = %(equipe_id)s)
            ORDER BY
                COALESCE(kpi.cout_total_periode, 0) DESC, ma.nom, kpi.equipe_nom
        """

        if limite:
            sql_query += " LIMIT %(limite)s"
            params['limite'] = limite

        return sql_query, params
