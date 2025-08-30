import logging
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')

# Crée le dossier logs si besoin
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Nettoie le fichier log à chaque démarrage
with open(LOG_FILE, 'w') as f:
    pass  # Vide le fichier

logging.basicConfig(
    level=logging.INFO,  # Changez en WARNING ou ERROR pour moins de bruit
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        # logging.StreamHandler()  # Ajoutez ceci si vous voulez aussi la console
    ]
)
