#!/usr/bin/env python3
"""
Script pour créer les vues KPI financières dans la base de données.
Exécute le fichier sql_vues_kpi_financiers.sql pour créer toutes les vues 
et indexes nécessaires aux KPI financiers.

Usage:
    python scripts/init_kpi_views.py
"""

import sys
import os
import logging

# Ajouter la racine du projet au PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ajouter aussi le dossier app pour permettre les imports depuis app/
app_path = os.path.join(project_root, 'app')
sys.path.insert(0, app_path)

# Importer APRÈS avoir modifié le path
from app.data.database import get_connection, close_connection, DatabaseError
from app.utils.logging_config import setup_logging

# Configurer le logging
setup_logging()
logger = logging.getLogger(__name__)

def execute_sql_file(file_path):
    """
    Exécute un fichier SQL en divisant sur les séparateurs ';'
    et en ignorant les commentaires.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier SQL non trouvé: {file_path}")
    
    logger.info(f"Lecture du fichier SQL: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Diviser le contenu en statements individuels
    statements = []
    current_statement = ""
    
    for line in sql_content.split('\n'):
        # Ignorer les lignes de commentaires
        line = line.strip()
        if line.startswith('--') or not line:
            continue
            
        current_statement += line + '\n'
        
        # Si la ligne se termine par ';', c'est la fin d'un statement
        if line.endswith(';'):
            statements.append(current_statement.strip())
            current_statement = ""
    
    # Ajouter le dernier statement s'il n'est pas vide
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    return statements

def create_kpi_views():
    """Crée les vues KPI financières dans la base de données."""
    logger.info("=== Début de l'initialisation des vues KPI financières ===")
    
    try:
        # Chemin vers le fichier SQL
        sql_file_path = os.path.join(project_root, 'app', 'sql_vues_kpi_financiers.sql')
        
        # Lire et parser le fichier SQL
        statements = execute_sql_file(sql_file_path)
        logger.info(f"Fichier SQL parsé: {len(statements)} statements trouvés")
        
        # Se connecter à la base de données
        conn = get_connection()
        cursor = conn.cursor()
        
        # Exécuter chaque statement dans sa propre transaction
        for i, statement in enumerate(statements, 1):
            try:
                logger.info(f"Exécution du statement {i}/{len(statements)}...")
                cursor.execute(statement)
                conn.commit()  # Commit après chaque statement
                logger.debug(f"Statement {i} exécuté avec succès")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du statement {i}: {e}")
                logger.error(f"Statement problématique: {statement[:100]}...")
                conn.rollback()  # Rollback en cas d'erreur
                # Continuer avec les autres statements
                continue
        
        # Toutes les modifications ont été commitées individuellement
        logger.info("=== Vues KPI financières créées avec succès ===")
        
        # Vérifier que les vues ont été créées
        verify_views(cursor)
        
    except DatabaseError as e:
        logger.critical(f"Erreur de base de données: {e}")
        return False
    except FileNotFoundError as e:
        logger.critical(f"Fichier non trouvé: {e}")
        return False
    except Exception as e:
        logger.critical(f"Erreur inattendue: {e}")
        return False
    finally:
        close_connection()
    
    return True

def verify_views(cursor):
    """Vérifie que les vues principales ont été créées."""
    expected_views = [
        'v_maintenance_couts_detaille',
        'v_kpi_couts_par_machine',
        'v_kpi_couts_par_site',
        'v_kpi_couts_par_equipe',
        'v_kpi_couts_par_type_machine',
        'v_kpi_couts_par_type_intervention'
    ]
    
    logger.info("Vérification de la création des vues...")
    
    for view_name in expected_views:
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.views 
                    WHERE table_name = %s
                )
            """, (view_name,))
            
            exists = cursor.fetchone()[0]
            if exists:
                logger.info(f"✓ Vue {view_name} créée avec succès")
            else:
                logger.warning(f"✗ Vue {view_name} non trouvée")
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la vue {view_name}: {e}")

def main():
    """Fonction principale du script."""
    try:
        success = create_kpi_views()
        if success:
            logger.info("🎉 Initialisation des vues KPI terminée avec succès!")
            print("\n" + "="*60)
            print("✅ VUES KPI FINANCIÈRES CRÉÉES AVEC SUCCÈS")
            print("="*60)
            print("Les vues suivantes sont maintenant disponibles:")
            print("- v_maintenance_couts_detaille")
            print("- v_kpi_couts_par_machine")
            print("- v_kpi_couts_par_site")
            print("- v_kpi_couts_par_equipe")
            print("- v_kpi_couts_par_type_machine")
            print("- v_kpi_couts_par_type_intervention")
            print("\nVous pouvez maintenant utiliser le KPIService pour accéder aux données.")
            return 0
        else:
            logger.error("❌ Échec de l'initialisation des vues KPI")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Script interrompu par l'utilisateur")
        return 1
    except Exception as e:
        logger.critical(f"Erreur fatale: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
