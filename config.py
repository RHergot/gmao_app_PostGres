# Configuration rapide pour résoudre les imports
# Copie du fichier app/config.py à la racine

import os
from dotenv import load_dotenv, find_dotenv

# Charger le .env
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path, override=True)

# --- Paramètres Base de Données ---
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgres')
DATABASE_PATH = os.getenv('DATABASE_PATH', './gmao_default.db')

# Paramètres PostgreSQL
POSTGRES_DB = os.getenv('POSTGRES_DB', 'gmao_industrie_data')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'gmao_app_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mot_de_passe_fort')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

# --- Paramètres UI ---
WINDOW_SIZE = (1400, 900)
WINDOW_TITLE = "GMAO - Gestion de Maintenance Assistée par Ordinateur"

# --- Paramètres Application ---
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
