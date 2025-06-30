import os
import shutil
import datetime

# Toujours dans la racine du projet (là où se trouve gmao_data.db)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'BU_DB')
BACKUP_RETENTION_DAYS = 30

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    return BACKUP_DIR

def get_backup_filename(db_path, dt=None):
    if dt is None:
        dt = datetime.datetime.now()
    base = os.path.basename(db_path)
    name, ext = os.path.splitext(base)
    date_str = dt.strftime('%Y-%m-%d')
    return os.path.join(BACKUP_DIR, f"{name}_{date_str}{ext}")

def backup_database(db_path):
    """
    Effectue une sauvegarde de la base de données dans BU_DB.
    Écrase le backup du même jour/heure si existant.
    Nettoie les backups de plus de BACKUP_RETENTION_DAYS.
    Retourne le chemin du backup créé.
    """
    ensure_backup_dir()
    backup_path = get_backup_filename(db_path)
    # Si un backup existe déjà pour ce timestamp, on l'écrase
    shutil.copy2(db_path, backup_path)
    cleanup_old_backups()
    return backup_path

def cleanup_old_backups():
    """
    Supprime les backups de plus de BACKUP_RETENTION_DAYS dans BU_DB.
    """
    now = datetime.datetime.now()
    for fname in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            # Cherche le timestamp dans le nom du fichier
            parts = fname.split('_')
            if len(parts) < 2:
                continue
            date_str = parts[-1].split('.')[0]  # ex: 2024-04-24_162300
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d_%H%M%S')
            if (now - dt).days > BACKUP_RETENTION_DAYS:
                os.remove(fpath)
        except Exception:
            continue
