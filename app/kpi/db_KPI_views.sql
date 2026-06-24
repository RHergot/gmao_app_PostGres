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

    TO_CHAR(m.date_fin_reelle::date, 'YYYY-MM-DD') AS jour, -- nouvelle colonne
    
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
-- KPI par machine avec agrégation journalière

CREATE OR REPLACE VIEW v_kpi_machine_jour AS
SELECT 
    id_machine,
    machine_nom,
    machine_serial,
    machine_criticite,
    site_nom,
    type_nom,
    type_categorie,
    equipe_nom,  -- AJOUT ICI
    jour, -- nouvelle colonne
    EXTRACT(YEAR FROM jour::date) AS annee,
    EXTRACT(MONTH FROM jour::date) AS mois,
    COUNT(*) AS nb_interventions,
    COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END) AS nb_preventif,
    COUNT(CASE WHEN type_reel = 'Correctif' THEN 1 END) AS nb_correctif,
    COUNT(CASE WHEN type_reel = 'Urgence' THEN 1 END) AS nb_urgence,
    SUM(cout_total) AS cout_total_jour,
    SUM(cout_main_oeuvre) AS cout_mod_jour,
    SUM(cout_pieces_internes) AS cout_pieces_jour,
    SUM(cout_pieces_externes + cout_autres_frais) AS cout_frais_externes_jour,
    AVG(cout_total) AS cout_moyen_intervention,
    SUM(duree_intervention_h) AS duree_totale,  -- Durée totale des interventions
    AVG(duree_intervention_h) AS duree_moyenne_h,
    AVG(cout_par_heure) AS cout_moyen_par_heure,
    MIN(cout_total) AS cout_min,
    MAX(cout_total) AS cout_max,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cout_total) AS cout_median,
    AVG(pourcentage_mod) AS pourcentage_moyen_mod,
    AVG(pourcentage_pieces) AS pourcentage_moyen_pieces,
    AVG(pourcentage_frais_externes) AS pourcentage_moyen_frais_externes,
    CASE 
        WHEN COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END) > 0 
        THEN COUNT(CASE WHEN type_reel = 'Preventif' THEN 1 END)::float / 
             COUNT(CASE WHEN type_reel IN ('Correctif', 'Urgence') THEN 1 END)::float
        ELSE 0 
    END AS ratio_preventif_curatif
FROM v_maintenance_couts_detaille
GROUP BY id_machine, machine_nom, machine_serial, machine_criticite, site_nom, type_nom, type_categorie, equipe_nom, jour
ORDER BY jour DESC, cout_total_jour DESC;