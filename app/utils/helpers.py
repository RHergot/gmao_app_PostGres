# gmao_app/app/utils/helpers.py
"""
Fonctions utilitaires diverses utilisées à travers l'application.
"""
import bcrypt
import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)

# --- Gestion des mots de passe ---

def hash_password(password: str) -> str:
    """Hashe un mot de passe en utilisant bcrypt."""
    if not password:
        raise ValueError("Le mot de passe ne peut pas être vide.")
    try:
        # Génère un salt et hashe le mot de passe
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_bytes.decode('utf-8') # Retourne le hash sous forme de chaîne
    except Exception as e:
        logger.exception("Erreur lors du hachage du mot de passe.")
        raise RuntimeError("Impossible de hacher le mot de passe") from e

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si un mot de passe en clair correspond à un hash bcrypt."""
    if not plain_password or not hashed_password:
        return False
    try:
        # bcrypt compare le mot de passe encodé avec le hash (qui contient le salt)
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        # Peut arriver si le hash est malformé
        logger.warning("Tentative de vérification d'un hash de mot de passe invalide.")
        return False
    except Exception as e:
        logger.exception("Erreur lors de la vérification du mot de passe.")
        return False


def parse_iso_date(date_str: Optional[str]) -> Optional[date]:
    """
    Convertit une chaîne de date ISO (YYYY-MM-DD) en objet date.
    Retourne None si l'entrée est None, vide, ou invalide.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError) as e:
        logger.warning(f"Impossible de parser la date '{date_str}': {e}")
        return None

def parse_iso_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """
    Convertit une chaîne de datetime ISO (YYYY-MM-DD HH:MM:SS ou formats similaires) en objet datetime.
    Gère les formats avec ou sans millisecondes.
    Retourne None si l'entrée est None, vide, ou invalide.
    """
    if not datetime_str:
        return None
    # Essayer plusieurs formats courants que la base de données pourrait renvoyer
    formats_to_try = [
        '%Y-%m-%d %H:%M:%S.%f',  # Avec millisecondes
        '%Y-%m-%d %H:%M:%S',    # Sans millisecondes
        '%Y-%m-%dT%H:%M:%S.%f', # Format ISO T avec millisecondes
        '%Y-%m-%dT%H:%M:%S',   # Format ISO T sans millisecondes
    ]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(datetime_str, fmt)
        except (ValueError, TypeError):
            continue # Essayer le format suivant

    # Si aucun format n'a fonctionné
    logger.warning(f"Impossible de parser le datetime '{datetime_str}' avec les formats attendus.")
    # Tentative avec fromisoformat pour plus de flexibilité (peut échouer si espace au lieu de T)
    try:
        return datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError):
        logger.warning(f"Échec de la tentative de parsing avec fromisoformat pour '{datetime_str}'.")
        return None


def format_iso_date(date_obj: Optional[date]) -> Optional[str]:
    """
    Convertit un objet date en chaîne ISO (YYYY-MM-DD).
    Retourne None si l'entrée est None.
    """
    if date_obj is None:
        return None
    try:
        return date_obj.strftime('%Y-%m-%d')
    except AttributeError:
         logger.warning(f"Tentative de formater un objet qui n'est pas une date: {date_obj}")
         return None

def format_iso_datetime(datetime_obj: Optional[datetime]) -> Optional[str]:
     """
     Convertit un objet datetime en chaîne ISO (YYYY-MM-DD HH:MM:SS).
     Retourne None si l'entrée est None.
     """
     if datetime_obj is None:
         return None
     try:
          # Utiliser un format standard pour PostgreSQL
         return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
     except AttributeError:
          logger.warning(f"Tentative de formater un objet qui n'est pas un datetime: {datetime_obj}")
          return None

    # --- AUTRES HELPERS ---
    # ...