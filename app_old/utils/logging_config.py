# gmao_app/app/utils/logging_config.py
"""
Configuration centralisée du logging pour l'application.
"""
import logging
import sys
from config import LOG_LEVEL # Importer le niveau depuis la config

def setup_logging():
    """Configure le système de logging."""
    log_level = getattr(logging, LOG_LEVEL, logging.INFO) # Défaut à INFO si invalide

    log_format = '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configuration du logger racine
    # Enlever les handlers existants pour éviter les doublons si la fonction est appelée plusieurs fois
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(formatter)

    # Ajouter le handler au logger racine
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level) # Définir le niveau global

    logging.info(f"Logging configuré avec le niveau: {LOG_LEVEL}")

    # Optionnel : Rediriger les exceptions non capturées vers le logger
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Ne pas logger KeyboardInterrupt, laisser Python la gérer
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical("Exception non capturée:", exc_info=(exc_type, exc_value, exc_traceback))

    # sys.excepthook = handle_exception # Activer si besoin