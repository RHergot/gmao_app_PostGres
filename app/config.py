# gmao_app/config.py
"""
Charge et fournit les paramètres de configuration de l'application.
Utilise python-dotenv pour charger depuis un fichier .env.
"""

# Configuration du chemin pour permettre les imports depuis le répertoire parent
import sys
import os
# Ajouter le répertoire parent au sys.path pour résoudre les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv, find_dotenv

# Utiliser find_dotenv() pour localiser le fichier .env de manière robuste.
# Cette méthode cherche dans le répertoire courant et les répertoires parents.
dotenv_path = find_dotenv()

if dotenv_path:
    print(f"INFO: Fichier .env trouvé. Forçage du chargement depuis : {dotenv_path}")
    # override=True force l'utilisation des valeurs du .env sur les variables système existantes.
    load_dotenv(dotenv_path=dotenv_path, override=True)
    # --- DIAGNOSTIC ---
    print(f"DIAGNOSTIC: Valeur de POSTGRES_HOST dans os.environ: {os.environ.get('POSTGRES_HOST')}")
    # --- FIN DIAGNOSTIC ---
else:
    print("WARNING: Fichier .env non trouvé. Utilisation des variables d'environnement système ou des valeurs par défaut.")

# --- Paramètres Base de Données ---
# Utilise la variable d'environnement ou une valeur par défaut
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgres')  # 'sqlite' ou 'postgres'
DATABASE_PATH = os.getenv('DATABASE_PATH', './gmao_default.db')  # Utilisé seulement pour sqlite
# Paramètres PostgreSQL
POSTGRES_DB = os.getenv('POSTGRES_DB', 'gmao_industrie_data')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'gmao_app_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mot_de_passe_fort')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')


# --- Paramètres Logging ---
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# --- Autres Paramètres (Exemples) ---
APP_VERSION = "0.1.0-alpha"
APP_NAME = "GMAO Industrielle"

# --- Déclenchement automatique des OT basé sur compteur ---
AUTO_OT_ENABLED = os.getenv('AUTO_OT_ENABLED', 'True').lower() in ('true', '1', 'yes')


# Optionnel: Validation simple des configurations
if DATABASE_TYPE not in ['postgres', 'postgresql']:
    raise ValueError(f"Type de base de données non supporté: {DATABASE_TYPE}")

# --- Affichage de la configuration pour le débogage ---
if DATABASE_TYPE in ['postgres', 'postgresql']:
    print(f"Configuration finale : DB=PostgreSQL ({POSTGRES_DB}) sur {POSTGRES_HOST}:{POSTGRES_PORT}, LOG_LEVEL={LOG_LEVEL}")
else:
    print(f"Configuration finale : DB={DATABASE_TYPE} à {DATABASE_PATH}, LOG_LEVEL={LOG_LEVEL}")

# --- Énumération des langues supportées ---
from enum import Enum

class Language(Enum):
    """Énumération des langues supportées par l'application."""
    FRENCH = "fr"
    ENGLISH = "en"
    GERMAN = "de"
    SPANISH = "es"
    ITALIAN = "it"
    PORTUGUESE = "pt"

# --- Configuration globale de l'application ---
class AppConfig:
    """Configuration globale de l'application."""
    def __init__(self):
        self.language = Language.FRENCH  # Langue par défaut
        self.version = APP_VERSION
        self.name = APP_NAME

# Instance globale de configuration
app_config = AppConfig()