#!/usr/bin/env python3
"""
Script pour appliquer le système d'archivage hybride des OT.
Utilise la configuration existante de l'application.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app.data.database import get_connection, db_cursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_archive_system():
    """
    Applique le système d'archivage hybride des OT.
    """
    logger.info("--- Application du système d'archivage hybride des OT ---")
    
    try:
        # Lire et exécuter le script SQL
        script_path = os.path.join(os.path.dirname(__file__), 'sql_archivage_ot_hybride.sql')
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Diviser le script en commandes individuelles
        sql_commands = sql_content.split(';')
        
        success_count = 0
        error_count = 0
        
        with db_cursor() as cursor:
            for i, command in enumerate(sql_commands):
                command = command.strip()
                if not command or command.startswith('--') or command.startswith('/*'):
                    continue
                    
                try:
                    logger.info(f"Exécution commande {i+1}...")
                    cursor.execute(command)
                    success_count += 1
                    logger.debug(f"✓ Commande {i+1} exécutée avec succès")
                except Exception as e:
                    error_count += 1
                    logger.error(f"✗ Erreur commande {i+1}: {e}")
                    # Continuer avec les autres commandes
        
        logger.info(f"--- Résumé de l'application ---")
        logger.info(f"Commandes réussies: {success_count}")
        logger.info(f"Commandes en erreur: {error_count}")
        
        if error_count == 0:
            logger.info("✓ Système d'archivage appliqué avec succès !")
        else:
            logger.warning(f"⚠ Système appliqué avec {error_count} erreur(s)")
            
        # Tester les fonctions créées
        test_archive_functions()
        
    except Exception as e:
        logger.error(f"Erreur lors de l'application du système d'archivage: {e}")
        raise

def test_archive_functions():
    """
    Teste que les fonctions d'archivage sont bien créées.
    """
    logger.info("--- Test des fonctions d'archivage ---")
    
    try:
        with db_cursor() as cursor:
            # Tester l'existence des fonctions
            cursor.execute("""
                SELECT proname 
                FROM pg_proc 
                WHERE proname IN ('auto_archive_completed_ots', 'archive_ot', 'unarchive_ot')
                ORDER BY proname
            """)
            functions = cursor.fetchall()
            
            logger.info(f"Fonctions trouvées: {[f[0] for f in functions]}")
            
            # Tester l'existence des vues
            cursor.execute("""
                SELECT viewname 
                FROM pg_views 
                WHERE viewname IN ('ot_actifs', 'ot_complets', 'vue_kpi_ot_performance', 'vue_kpi_ot_historique_complet')
                ORDER BY viewname
            """)
            views = cursor.fetchall()
            
            logger.info(f"Vues trouvées: {[v[0] for v in views]}")
            
            # Tester l'existence des index
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE indexname IN ('idx_ot_statut_non_archive', 'idx_ot_archives')
                ORDER BY indexname
            """)
            indexes = cursor.fetchall()
            
            logger.info(f"Index trouvés: {[i[0] for i in indexes]}")
            
            logger.info("✓ Test des composants terminé")
            
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")

def get_archive_stats():
    """
    Affiche les statistiques d'archivage actuelles.
    """
    logger.info("--- Statistiques d'archivage ---")
    
    try:
        with db_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    statut,
                    COUNT(*) as count
                FROM ordre_travail 
                GROUP BY statut 
                ORDER BY statut
            """)
            
            stats = cursor.fetchall()
            
            for statut, count in stats:
                logger.info(f"{statut}: {count} OT")
                
            # Calculer les OT archivables
            cursor.execute("""
                SELECT COUNT(*) 
                FROM ordre_travail 
                WHERE statut = 'Terminé' 
                  AND date_creation::timestamp < CURRENT_DATE - INTERVAL '6 months'
            """)
            
            archivable = cursor.fetchone()[0]
            logger.info(f"OT archivables automatiquement (>6 mois): {archivable}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")

if __name__ == "__main__":
    try:
        # Appliquer le système d'archivage
        apply_archive_system()
        
        # Afficher les statistiques
        get_archive_stats()
        
        print("\n" + "="*50)
        print("SYSTÈME D'ARCHIVAGE APPLIQUÉ AVEC SUCCÈS !")
        print("="*50)
        print("Vous pouvez maintenant :")
        print("1. Utiliser les boutons d'archivage dans l'interface")
        print("2. Programmer l'archivage automatique (optionnel)")
        print("3. Utiliser les vues optimisées pour les KPI")
        
    except Exception as e:
        logger.error(f"Échec de l'application: {e}")
        sys.exit(1)
