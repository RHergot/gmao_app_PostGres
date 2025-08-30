# gmao_app/scripts/init_db.py
"""
Script pour initialiser la base de données en créant les tables
définies dans app/data/schemas.py.
A exécuter manuellement une seule fois ou si la DB est supprimée.
"""
import sys
import os
import logging

# Ajouter la racine du projet au PYTHONPATH pour pouvoir importer les modules de l'app
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Importer APRÈS avoir modifié le path
from app.data.database import get_connection, close_connection, DatabaseError
from app.data.schemas import TABLES, TRIGGERS
from app.utils.logging_config import setup_logging

# Configurer le logging pour le script
setup_logging()
logger = logging.getLogger(__name__)

def create_schema():
    """Crée les tables et triggers définis dans schemas.py."""
    logger.info("Début de l'initialisation du schéma de la base de données...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Créer les tables
        for table_name, create_sql in TABLES.items():
            logger.info(f"Création de la table {table_name}...")
            try:
                cursor.execute(create_sql)
                logger.info(f"Table {table_name} créée avec succès (ou existait déjà).")
            except Exception as e:
                logger.error(f"Erreur lors de la création de la table {table_name}: {e}")
                raise # Remonter l'erreur pour arrêter le script

        # Créer les triggers
        for trigger_name, create_sql in TRIGGERS.items():
            logger.info(f"Création du trigger {trigger_name}...")
            try:
                cursor.execute(create_sql)
                logger.info(f"Trigger {trigger_name} créé avec succès (ou existait déjà).")
            except Exception as e:
                logger.error(f"Erreur lors de la création du trigger {trigger_name}: {e}")
                # Ne pas forcément arrêter pour un trigger, juste logguer
                # raise

        conn.commit()
        logger.info("Schéma de la base de données initialisé avec succès.")

    except DatabaseError as e:
        logger.critical(f"Erreur de base de données lors de l'initialisation: {e}")
    except Exception as e:
        logger.critical(f"Erreur inattendue lors de l'initialisation: {e}")
    finally:
        close_connection()

if __name__ == "__main__":
    # Exécuter la fonction si le script est lancé directement
    create_schema()