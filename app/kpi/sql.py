-- ===================================================================
-- VUES MÉTIER POUR KPI FINANCIERS PAR CENTRE DE FRAIS
-- ===================================================================
-- Date: 30/06/2025
-- Phase: 1.2 - Architecture Base de Données
-- Objectif: Créer les vues optimisées pour calculs KPI

-- ===================================================================
-- 1. VUE CONSOLIDÉE DES COÛTS PAR MAINTENANCE
-- ===================================================================
-- Vue principale qui agrège toutes les informations nécessaires pour les KPI

CREATE OR REPLACE VIEW v_maintenance_couts_detaille AS
SELECT 
    -- Informations maintenance
    m.id_maintenance,
    m.ot_id,
    m.date_debut_reelle,
    m.date_fin_reelle,
    m.duree_intervention_h,
    m.type_reel,
    m.description_travaux,
    m.resultat,
    
    -- Coûts détaillés
    COALESCE(m.cout_main_oeuvre, 0) AS cout_main_oeuvre,
    COALESCE(m.cout_pieces_internes, 0) AS cout_pieces_internes,
    COALESCE(m.cout_pieces_externes, 0) AS cout_pieces_externes,
    COALESCE(m.cout_autres_frais, 0) AS cout_autres_frais,
    COALESCE(m.cout_total, 0) AS cout_total,
    
    -- Informations machine
    mach.id_machine,
    mach.nom AS machine_nom,
    mach.serial AS machine_serial,
    mach.etat AS machine_etat,
    mach.criticite AS machine_criticite,
    mach.localisation AS machine_localisation,
    mach.date_installation,
    
    -- Informations site
    s.id_site,
    s.nom AS site_nom,
    s.ville AS site_ville,
    s.pays AS site_pays,
    
    -- Informations type machine
    tm.id_type_machine,
    tm.categorie AS type_categorie,
    tm.nom AS type_nom,
    tm.description AS type_description,
    
    -- Informations fabricant
    f.id_fabricant,
    f.nom AS fabricant_nom,
    
    -- Informations technicien responsable
    t.id_technicien,
    t.nom AS technicien_nom,
    t.prenom AS technicien_prenom,
    CONCAT(COALESCE(t.prenom, ''), ' ', t.nom) AS technicien_nom_complet,
    t.qualification AS technicien_qualification,
    t.cout_horaire AS technicien_cout_horaire,
    
    -- Informations équipe
    e.id_equipe,
    e.nom AS equipe_nom,
    e.domaine_expertise AS equipe_domaine,
    
    -- Calculs dérivés
    EXTRACT(YEAR FROM m.date_fin_reelle::date) AS annee,
    EXTRACT(MONTH FROM m.date_fin_reelle::date) AS mois,
    TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM') AS periode_mois,
    TO_CHAR(m.date_fin_reelle::date, 'YYYY-Q') AS periode_trimestre,
    
    -- Ratios
    CASE 
        WHEN m.duree_intervention_h > 0 THEN m.cout_total / m.duree_intervention_h 
        ELSE 0 
    END AS cout_par_heure,
    
    CASE 
        WHEN m.cout_total > 0 THEN (m.cout_main_oeuvre / m.cout_total) * 100 
        ELSE 0 
    END AS pourcentage_mod,
    
    CASE 
        WHEN m.cout_total > 0 THEN (m.cout_pieces_internes / m.cout_total) * 100 
        ELSE 0 
    END AS pourcentage_pieces,
    
    CASE 
        WHEN m.cout_total > 0 THEN ((m.cout_pieces_externes + m.cout_autres_frais) / m.cout_total) * 100 
        ELSE 0 
    END AS pourcentage_frais_externes

FROM MAINTENANCE m
LEFT JOIN MACHINE mach ON m.machine_id = mach.id_machine
LEFT JOIN SITE s ON mach.site_id = s.id_site
LEFT JOIN TYPE_MACHINE tm ON mach.type_machine_id = tm.id_type_machine
LEFT JOIN FABRICANT f ON mach.fabricant_id = f.id_fabricant
LEFT JOIN TECHNICIEN t ON m.technicien_id = t.id_technicien
LEFT JOIN EQUIPE e ON t.equipe_id = e.id_equipe
WHERE m.date_fin_reelle IS NOT NULL 
  AND m.cout_total IS NOT NULL;

-- ===================================================================
-- 2. VUE AGRÉGÉE PAR MACHINE ET PÉRIODE
-- ===================================================================
-- KPI par machine avec agrégation mensuelle

CREATE OR REPLACE VIEW v_kpi_machine_mensuel AS
SELECT 
    -- Identifiants
    id_machine,
    machine_nom,
    machine_serial,
    machine_criticite,
    site_nom,
    type_nom,
    type_categorie,
    periode_mois,
    annee,
    mois,
    
    -- Compteurs
    COUNT(*) AS nb_interventions,
    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
    COUNT(CASE WHEN type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
    
    -- Coûts totaux
    SUM(cout_total) AS cout_total_periode,
    SUM(cout_main_oeuvre) AS cout_mod_periode,
    SUM(cout_pieces_internes) AS cout_pieces_periode,
    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_periode,
    
    -- Moyennes
    AVG(cout_total) AS cout_moyen_intervention,
    AVG(duree_intervention_h) AS duree_moyenne_h,
    AVG(cout_par_heure) AS cout_moyen_par_heure,
    
    -- Médianes et extremes
    MIN(cout_total) AS cout_min,
    MAX(cout_total) AS cout_max,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cout_total) AS cout_median,
    
    -- Ratios
    AVG(pourcentage_mod) AS pourcentage_moyen_mod,
    AVG(pourcentage_pieces) AS pourcentage_moyen_pieces,
    AVG(pourcentage_frais_externes) AS pourcentage_moyen_frais_externes,
    
    -- Ratio préventif/curatif
    CASE 
        WHEN COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END) > 0 
        THEN COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END)::float / 
             COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END)::float
        ELSE 0 
    END AS ratio_preventif_curatif

FROM v_maintenance_couts_detaille
GROUP BY 
    id_machine, machine_nom, machine_serial, machine_criticite,
    site_nom, type_nom, type_categorie,
    periode_mois, annee, mois
ORDER BY annee DESC, mois DESC, cout_total_periode DESC;

-- ===================================================================
-- 3. VUE AGRÉGÉE PAR SITE ET PÉRIODE
-- ===================================================================

CREATE OR REPLACE VIEW v_kpi_site_mensuel AS
SELECT 
    -- Identifiants
    id_site,
    site_nom,
    site_ville,
    site_pays,
    periode_mois,
    annee,
    mois,
    
    -- Compteurs
    COUNT(DISTINCT id_machine) AS nb_machines,
    COUNT(*) AS nb_interventions,
    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
    COUNT(CASE WHEN type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
    
    -- Coûts totaux
    SUM(cout_total) AS cout_total_periode,
    SUM(cout_main_oeuvre) AS cout_mod_periode,
    SUM(cout_pieces_internes) AS cout_pieces_periode,
    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_periode,
    
    -- Moyennes
    AVG(cout_total) AS cout_moyen_intervention,
    SUM(cout_total) / COUNT(DISTINCT id_machine) AS cout_moyen_par_machine,
    
    -- Ratios
    AVG(pourcentage_mod) AS pourcentage_moyen_mod,
    AVG(pourcentage_pieces) AS pourcentage_moyen_pieces,
    AVG(pourcentage_frais_externes) AS pourcentage_moyen_frais_externes,
    
    -- Ratio préventif/curatif
    CASE 
        WHEN COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END) > 0 
        THEN COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END)::float / 
             COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END)::float
        ELSE 0 
    END AS ratio_preventif_curatif

FROM v_maintenance_couts_detaille
GROUP BY 
    id_site, site_nom, site_ville, site_pays,
    periode_mois, annee, mois
ORDER BY annee DESC, mois DESC, cout_total_periode DESC;

-- ===================================================================
-- 4. VUE AGRÉGÉE PAR ÉQUIPE ET PÉRIODE
-- ===================================================================

CREATE OR REPLACE VIEW v_kpi_equipe_mensuel AS
SELECT 
    -- Identifiants
    id_equipe,
    equipe_nom,
    equipe_domaine,
    periode_mois,
    annee,
    mois,
    
    -- Compteurs
    COUNT(DISTINCT id_technicien) AS nb_techniciens_actifs,
    COUNT(*) AS nb_interventions,
    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
    COUNT(CASE WHEN type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
    
    -- Coûts totaux
    SUM(cout_total) AS cout_total_periode,
    SUM(cout_main_oeuvre) AS cout_mod_periode,
    SUM(cout_pieces_internes) AS cout_pieces_periode,
    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_periode,
    
    -- Moyennes
    AVG(cout_total) AS cout_moyen_intervention,
    SUM(cout_total) / COUNT(DISTINCT id_technicien) AS cout_moyen_par_technicien,
    
    -- Heures et productivité
    SUM(duree_intervention_h) AS heures_totales,
    AVG(duree_intervention_h) AS duree_moyenne_intervention,
    SUM(cout_total) / NULLIF(SUM(duree_intervention_h), 0) AS cout_par_heure_equipe,
    
    -- Efficacité équipe
    COUNT(*) / COUNT(DISTINCT id_technicien) AS interventions_par_technicien

FROM v_maintenance_couts_detaille
WHERE id_equipe IS NOT NULL
GROUP BY 
    id_equipe, equipe_nom, equipe_domaine,
    periode_mois, annee, mois
ORDER BY annee DESC, mois DESC, cout_total_periode DESC;

-- ===================================================================
-- 5. VUE AGRÉGÉE PAR TYPE DE MACHINE ET PÉRIODE
-- ===================================================================

CREATE OR REPLACE VIEW v_kpi_type_machine_mensuel AS
SELECT 
    -- Identifiants
    id_type_machine,
    type_categorie,
    type_nom,
    periode_mois,
    annee,
    mois,
    
    -- Compteurs
    COUNT(DISTINCT id_machine) AS nb_machines,
    COUNT(*) AS nb_interventions,
    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
    COUNT(CASE WHEN type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
    
    -- Coûts totaux
    SUM(cout_total) AS cout_total_periode,
    SUM(cout_main_oeuvre) AS cout_mod_periode,
    SUM(cout_pieces_internes) AS cout_pieces_periode,
    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_periode,
    
    -- Moyennes
    AVG(cout_total) AS cout_moyen_intervention,
    SUM(cout_total) / COUNT(DISTINCT id_machine) AS cout_moyen_par_machine,
    
    -- Ratios
    AVG(pourcentage_mod) AS pourcentage_moyen_mod,
    AVG(pourcentage_pieces) AS pourcentage_moyen_pieces,
    AVG(pourcentage_frais_externes) AS pourcentage_moyen_frais_externes

FROM v_maintenance_couts_detaille
GROUP BY 
    id_type_machine, type_categorie, type_nom,
    periode_mois, annee, mois
ORDER BY annee DESC, mois DESC, cout_total_periode DESC;

-- ===================================================================
-- 6. VUE COMPARATIVE PRÉVENTIF VS CURATIF
-- ===================================================================

CREATE OR REPLACE VIEW v_kpi_preventif_curatif AS
SELECT 
    periode_mois,
    annee,
    mois,
    
    -- Préventif
    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
    SUM(CASE WHEN type_reel = 'Preventif' THEN cout_total ELSE 0 END) AS cout_preventif,
    AVG(CASE WHEN type_reel = 'Preventif' THEN cout_total END) AS cout_moyen_preventif,
    
    -- Curatif (Correctif + Urgence)
    COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END) AS nb_curatif,
    SUM(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN cout_total ELSE 0 END) AS cout_curatif,
    AVG(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN cout_total END) AS cout_moyen_curatif,
    
    -- Urgence seule
    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
    SUM(CASE WHEN type_reel = 'Urgence' THEN cout_total ELSE 0 END) AS cout_urgence,
    AVG(CASE WHEN type_reel = 'Urgence' THEN cout_total END) AS cout_moyen_urgence,
    
    -- Totaux
    COUNT(*) AS nb_total,
    SUM(cout_total) AS cout_total,
    
    -- Ratios
    CASE 
        WHEN COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END) > 0 
        THEN COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END)::float / 
             COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END)::float
        ELSE 0 
    END AS ratio_preventif_curatif,
    
    -- Pourcentages
    (COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END)::float / COUNT(*)::float) * 100 AS pourcentage_preventif,
    (COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END)::float / COUNT(*)::float) * 100 AS pourcentage_curatif

FROM v_maintenance_couts_detaille
GROUP BY periode_mois, annee, mois
ORDER BY annee DESC, mois DESC;

-- ===================================================================
-- 7. VUE TOP MACHINES COÛTEUSES
-- ===================================================================

CREATE OR REPLACE VIEW v_top_machines_couteuses AS
SELECT 
    id_machine,
    machine_nom,
    machine_serial,
    site_nom,
    type_nom,
    machine_criticite,
    
    -- Coûts des 12 derniers mois
    COUNT(*) AS nb_interventions_12m,
    SUM(cout_total) AS cout_total_12m,
    AVG(cout_total) AS cout_moyen_12m,
    MAX(cout_total) AS cout_max_12m,
    
    -- Répartition des coûts
    SUM(cout_main_oeuvre) AS cout_mod_12m,
    SUM(cout_pieces_internes) AS cout_pieces_12m,
    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_12m,
    
    -- Tendance (ratio 6 derniers mois vs 6 précédents)
    SUM(CASE WHEN date_fin_reelle::timestamp >= CURRENT_DATE - INTERVAL '6 months' THEN cout_total ELSE 0 END) AS cout_6m_recents,
    SUM(CASE WHEN date_fin_reelle::timestamp >= CURRENT_DATE - INTERVAL '12 months' 
                  AND date_fin_reelle::timestamp < CURRENT_DATE - INTERVAL '6 months' 
             THEN cout_total ELSE 0 END) AS cout_6m_precedents,
    
    CASE 
        WHEN SUM(CASE WHEN date_fin_reelle::timestamp >= CURRENT_DATE - INTERVAL '12 months' 
                          AND date_fin_reelle::timestamp < CURRENT_DATE - INTERVAL '6 months' 
                     THEN cout_total ELSE 0 END) > 0
        THEN (SUM(CASE WHEN date_fin_reelle::timestamp >= CURRENT_DATE - INTERVAL '6 months' THEN cout_total ELSE 0 END) / 
              SUM(CASE WHEN date_fin_reelle::timestamp >= CURRENT_DATE - INTERVAL '12 months' 
                          AND date_fin_reelle::timestamp < CURRENT_DATE - INTERVAL '6 months' 
                     THEN cout_total ELSE 0 END)) - 1
        ELSE 0
    END AS tendance_cout_pourcentage

FROM v_maintenance_couts_detaille
WHERE date_fin_reelle::timestamp >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 
    id_machine, machine_nom, machine_serial, 
    site_nom, type_nom, machine_criticite
HAVING SUM(cout_total) > 0
ORDER BY cout_total_12m DESC;

-- ===================================================================
-- 8. INDEX OPTIMISÉS POUR LES VUES
-- ===================================================================

-- Index composites pour améliorer les performances des vues
CREATE INDEX IF NOT EXISTS idx_maintenance_date_machine ON MAINTENANCE(date_fin_reelle, machine_id) WHERE cout_total IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_maintenance_date_type ON MAINTENANCE(date_fin_reelle, type_reel) WHERE cout_total IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_maintenance_cout_date ON MAINTENANCE(cout_total, date_fin_reelle) WHERE cout_total IS NOT NULL;

-- Index pour les jointures fréquentes
CREATE INDEX IF NOT EXISTS idx_machine_site_type ON MACHINE(site_id, type_machine_id);
CREATE INDEX IF NOT EXISTS idx_technicien_equipe_actif ON TECHNICIEN(equipe_id, actif) WHERE actif = 1;

-- Index pour les dates (extraction année/mois)
CREATE INDEX IF NOT EXISTS idx_maintenance_date_extract ON MAINTENANCE(EXTRACT(YEAR FROM date_fin_reelle::date), EXTRACT(MONTH FROM date_fin_reelle::date)) WHERE cout_total IS NOT NULL;

-- ===================================================================
-- COMMENTAIRES ET DOCUMENTATION
-- ===================================================================

COMMENT ON VIEW v_maintenance_couts_detaille IS 'Vue consolidée avec tous les détails financiers et contextuels des maintenances pour calculs KPI';
COMMENT ON VIEW v_kpi_machine_mensuel IS 'KPI financiers agrégés par machine et par mois';
COMMENT ON VIEW v_kpi_site_mensuel IS 'KPI financiers agrégés par site et par mois';
COMMENT ON VIEW v_kpi_equipe_mensuel IS 'KPI financiers agrégés par équipe et par mois';
COMMENT ON VIEW v_kpi_type_machine_mensuel IS 'KPI financiers agrégés par type de machine et par mois';
COMMENT ON VIEW v_kpi_preventif_curatif IS 'Comparaison des coûts préventif vs curatif par période';
COMMENT ON VIEW v_top_machines_couteuses IS 'Classement des machines les plus coûteuses sur 12 mois avec tendances';

-- ===================================================================
-- FIN DU SCRIPT
-- ===================================================================
