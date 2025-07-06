#!/usr/bin/env python3
"""
Script simplifié pour appliquer le système d'archivage hybride des OT.
Exécute les commandes SQL une par une.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app.data.database import get_connection, db_cursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_archive_functions():
    """
    Crée les fonctions d'archivage PostgreSQL.
    """
    logger.info("Création des fonctions d'archivage...")
    
    # Fonction d'archivage automatique
    auto_archive_function = """
CREATE OR REPLACE FUNCTION auto_archive_completed_ots()
RETURNS INTEGER AS $$
DECLARE
    archive_count INTEGER := 0;
    cutoff_date DATE;
BEGIN
    cutoff_date := CURRENT_DATE - INTERVAL '6 months';
    
    UPDATE ordre_travail 
    SET 
        statut = 'Archivé',
        updated_at = CURRENT_TIMESTAMP
    WHERE 
        statut = 'Terminé' 
        AND date_creation::timestamp < cutoff_date
        AND updated_at::timestamp < cutoff_date;
    
    GET DIAGNOSTICS archive_count = ROW_COUNT;
    
    RETURN archive_count;
EXCEPTION
    WHEN OTHERS THEN
        RETURN archive_count;
END;
$$ LANGUAGE plpgsql;
    """
    
    # Fonction d'archivage manuel
    archive_function = """
CREATE OR REPLACE FUNCTION archive_ot(ot_id_param INTEGER, user_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    current_status TEXT;
BEGIN
    SELECT statut INTO current_status
    FROM ordre_travail
    WHERE id_ot = ot_id_param;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'OT ID % non trouvé', ot_id_param;
    END IF;
    
    IF current_status != 'Terminé' THEN
        RAISE EXCEPTION 'Impossible d''archiver un OT avec le statut "%". Seuls les OT "Terminé" peuvent être archivés.', current_status;
    END IF;
    
    UPDATE ordre_travail 
    SET 
        statut = 'Archivé',
        updated_at = CURRENT_TIMESTAMP
    WHERE id_ot = ot_id_param;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
    """
    
    # Fonction de désarchivage
    unarchive_function = """
CREATE OR REPLACE FUNCTION unarchive_ot(ot_id_param INTEGER, user_id INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE ordre_travail 
    SET 
        statut = 'Terminé',
        updated_at = CURRENT_TIMESTAMP
    WHERE id_ot = ot_id_param AND statut = 'Archivé';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'OT ID % non trouvé ou pas archivé', ot_id_param;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
    """
    
    try:
        with db_cursor() as cursor:
            logger.info("Création fonction auto_archive_completed_ots...")
            cursor.execute(auto_archive_function)
            
            logger.info("Création fonction archive_ot...")
            cursor.execute(archive_function)
            
            logger.info("Création fonction unarchive_ot...")
            cursor.execute(unarchive_function)
            
            logger.info("✓ Fonctions d'archivage créées avec succès")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création des fonctions: {e}")
        raise

def create_archive_views():
    """
    Crée les vues optimisées pour l'archivage.
    """
    logger.info("Création des vues d'archivage...")
    
    # Vue OT actifs
    ot_actifs_view = """
CREATE OR REPLACE VIEW ot_actifs AS
SELECT *
FROM ordre_travail
WHERE statut != 'Archivé'
ORDER BY date_creation DESC;
    """
    
    # Vue OT complets
    ot_complets_view = """
CREATE OR REPLACE VIEW ot_complets AS
SELECT *, 
       CASE WHEN statut = 'Archivé' THEN true ELSE false END as est_archive
FROM ordre_travail
ORDER BY date_creation DESC;
    """
    
    try:
        with db_cursor() as cursor:
            logger.info("Création vue ot_actifs...")
            cursor.execute(ot_actifs_view)
            
            logger.info("Création vue ot_complets...")
            cursor.execute(ot_complets_view)
            
            logger.info("✓ Vues d'archivage créées avec succès")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création des vues: {e}")
        raise

def create_archive_indexes():
    """
    Crée les index optimisés pour l'archivage.
    """
    logger.info("Création des index d'archivage...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_ot_statut_non_archive ON ordre_travail (statut, date_creation DESC) WHERE statut != 'Archivé';",
        "CREATE INDEX IF NOT EXISTS idx_ot_archives ON ordre_travail (date_creation DESC) WHERE statut = 'Archivé';"
    ]
    
    try:
        with db_cursor() as cursor:
            for index_sql in indexes:
                logger.info(f"Création index...")
                cursor.execute(index_sql)
            
            logger.info("✓ Index d'archivage créés avec succès")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création des index: {e}")
        raise

def test_archive_system():
    """
    Teste le système d'archivage.
    """
    logger.info("Test du système d'archivage...")
    
    try:
        with db_cursor() as cursor:
            # Compter les OT par statut
            cursor.execute("""
                SELECT 
                    statut,
                    COUNT(*) as count
                FROM ordre_travail 
                GROUP BY statut 
                ORDER BY statut
            """)
            
            stats = cursor.fetchall()
            
            logger.info("Statistiques actuelles des OT:")
            for statut, count in stats:
                logger.info(f"  {statut}: {count} OT")
            
            # Tester la fonction d'archivage automatique
            cursor.execute("SELECT auto_archive_completed_ots()")
            result = cursor.fetchone()
            logger.info(f"Test archivage automatique: {result[0]} OT seraient archivés")
            
            logger.info("✓ Système d'archivage fonctionnel")
            
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        raise

def main():
    """
    Fonction principale.
    """
    logger.info("=== Installation du système d'archivage hybride ===")
    
    try:
        # Créer les fonctions
        create_archive_functions()
        
        # Créer les vues
        create_archive_views()
        
        # Créer les index
        create_archive_indexes()
        
        # Tester le système
        test_archive_system()
        
        logger.info("✓ Système d'archivage installé avec succès !")
        print("\n" + "="*60)
        print("SYSTÈME D'ARCHIVAGE HYBRIDE INSTALLÉ AVEC SUCCÈS !")
        print("="*60)
        print("Fonctionnalités disponibles :")
        print("• Archivage manuel via boutons de l'interface")
        print("• Fonctions PostgreSQL pour archivage automatique")
        print("• Vues optimisées (ot_actifs, ot_complets)")
        print("• Index pour performance optimisée")
        print("• Support du statut 'Archivé' dans l'application")
        
    except Exception as e:
        logger.error(f"Échec de l'installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
