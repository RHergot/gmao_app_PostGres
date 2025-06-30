# gmao_app/app/data/database.py
"""
Gère la connexion à la base de données PostgreSQL.
"""
import psycopg2
import psycopg2.extras
import logging
import os
from contextlib import contextmanager
from config import (
    DATABASE_TYPE,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
)
from app.utils.exceptions import DatabaseError, ConfigurationError
from app.data.schemas import TABLES, TRIGGERS, ALTER_TABLES

logger = logging.getLogger(__name__)

# Variable globale pour la connexion (simple pour commencer)
_connection = None

def _get_db_path() -> str:
    """Retourne le chemin absolu de la DB et crée les répertoires parents si besoin."""
    abs_path = os.path.abspath(DATABASE_PATH)
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        return abs_path
    except OSError as e:
        logger.error(f"Erreur lors de la création des répertoires pour la DB {abs_path}: {e}")
        raise DatabaseError(f"Impossible de créer les répertoires pour la DB: {e}") from e

def get_connection():  # type: ignore
    """
    Retourne l'instance de connexion globale à la base de données.
    Établit la connexion si elle n'existe pas.
    """
    global _connection
    if _connection is None:
        # La validation du DATABASE_TYPE est déjà faite dans config.py, on peut donc se connecter directement.
        try:
            # --- DEBUG: Affichage des paramètres de connexion ---
            print("\n" + "="*50)
            print("DEBUG: Paramètres de connexion passés à psycopg2.connect:")
            print(f"  - dbname: {POSTGRES_DB}")
            print(f"  - user: {POSTGRES_USER}")
            print(f"  - password: {'*'*len(POSTGRES_PASSWORD) if POSTGRES_PASSWORD else 'None'}")
            print(f"  - host: {POSTGRES_HOST}")
            print(f"  - port: {POSTGRES_PORT}")
            print("="*50 + "\n")
            # --- Fin DEBUG ---

            logger.info(f"Tentative de connexion à la base PostgreSQL sur {POSTGRES_HOST}:{POSTGRES_PORT}...")
            _connection = psycopg2.connect(
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.info("Connexion à la base PostgreSQL réussie.")
        except psycopg2.Error as e:
            logger.exception(f"Erreur de connexion à la base PostgreSQL: {e}")
            raise DatabaseError(f"Erreur de connexion PostgreSQL: {e}") from e
    return _connection

def close_connection():
    """Ferme la connexion globale à la base de données si elle est ouverte."""
    global _connection
    if _connection:
        try:
            _connection.close()
            _connection = None
            logger.info("Connexion à la base de données fermée.")
        except psycopg2.Error as e:
            logger.error(f"Erreur lors de la fermeture de la connexion PostgreSQL: {e}")
            # Ne pas lever d'exception ici généralement

@contextmanager
def db_cursor():
    """
    Fournit un curseur PostgreSQL dans un contexte managé
    (gère commit/rollback et fermeture curseur).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
        logger.debug("Transaction PostgreSQL commitée avec succès.")
    except psycopg2.Error as e:
        logger.error(f"Erreur durant la transaction PostgreSQL. Rollback effectué: {e}")
        try:
            conn.rollback()
        except psycopg2.Error as rb_err:
            logger.error(f"Erreur pendant le rollback PostgreSQL: {rb_err}")
        raise DatabaseError(f"Erreur de transaction PostgreSQL: {e}") from e
    except Exception as e:
        logger.error(f"Erreur non-PostgreSQL durant la transaction DB. Rollback effectué: {e}")
        try:
            conn.rollback()
        except psycopg2.Error as rb_err:
            logger.error(f"Erreur pendant le rollback PostgreSQL: {rb_err}")
        raise
    finally:
        if cursor:
            cursor.close()

def execute_query(query: str, params: tuple = ()):
    """Exécute une requête SANS fetch."""
    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor  # Le commit est fait par db_cursor

def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Exécute une requête et retourne une seule ligne sous forme de dict."""
    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()

def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Exécute une requête et retourne toutes les lignes sous forme de liste de dict."""
    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()

def initialize_database():
    """
    Crée toutes les tables et triggers définis dans schemas.py s'ils n'existent pas.
    Doit être appelée après l'établissement de la connexion.
    """
    logger.info("Vérification et initialisation du schéma de la base de données...")
    # Création des tables
    for table_name, create_sql in TABLES.items():
        try:
            logger.debug(f"Vérification/Création de la table: {table_name}")
            execute_query(create_sql)
        except DatabaseError as e:
            logger.warning(f"Erreur création table {table_name}: {e}")

    # Application des ALTER TABLE (clés étrangères circulaires)
    for alter_sql in ALTER_TABLES:
        try:
            logger.debug(f"Application ALTER TABLE: {alter_sql}")
            execute_query(alter_sql)
        except DatabaseError as e:
            logger.warning(f"ALTER TABLE erreur ou déjà existant : {e}")

    # Création des triggers (si adaptés à PostgreSQL)
    for trigger_name, create_sql in TRIGGERS.items():
        # Extract trigger actual name from the CREATE TRIGGER statement
        import re
        match = re.search(r'CREATE TRIGGER (\w+)', create_sql, re.IGNORECASE)
        if not match:
            logger.warning(f"Impossible de trouver le nom du trigger dans le SQL pour {trigger_name}")
            continue
        actual_trigger_name = match.group(1)
        # Check if trigger exists
        exists_sql = "SELECT 1 FROM pg_trigger WHERE tgname = %s;"
        try:
            res = fetch_one(exists_sql, (actual_trigger_name,))
            if res:
                logger.info(f"Trigger {actual_trigger_name} déjà existant, création ignorée.")
                continue
            logger.debug(f"Trigger {trigger_name}: création")
            execute_query(create_sql)
        except DatabaseError as e:
            logger.warning(f"Trigger {trigger_name} : erreur création ou déjà existant : {e}")

    logger.info("Schéma de la base de données initialisé/vérifié avec succès.")