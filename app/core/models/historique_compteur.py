# gmao_app/app/core/models/historique_compteur.py
""" Modèle pour l'entité Historique des relevés de compteur. """
from dataclasses import dataclass, field
from typing import Any,  Dict,  Union,  Optional
import logging
from datetime import datetime

# Importez vos helpers de date/datetime si vous en avez
# from app.utils.helpers import parse_iso_datetime, format_iso_datetime

logger = logging.getLogger(__name__)

@dataclass
class HistoriqueCompteur:
    """ Enregistre un relevé ponctuel de compteur. """

    # --- Champs OBLIGATOIRES ---
    compteur_id: int       # FK vers COMPTEUR
    date_releve: datetime  # Timestamp précis du relevé
    valeur: float          # Valeur enregistrée

    # --- Champs OPTIONNELS ---
    utilisateur_id: Optional[int] = None # Qui a fait le relevé?
    maintenance_id: Optional[int] = None # Si relevé fait pendant une maintenance?

    # --- Clé Primaire (PK) ---
    id_historique: Optional[int] = None

    # --- Méthode Factory depuis une ligne DB ---
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['HistoriqueCompteur']:
        """ Crée une instance de HistoriqueCompteur depuis une ligne de base de données. """
        if row is None:
            return None

        hist_id_for_log = 'N/A'
        try:
             if 'id_historique' in row.keys():
                 hist_id_for_log = row['id_historique']
        except Exception: pass

        try:
            hist_id = row['id_historique']
            if hist_id is None:
                 logger.error(f"Erreur critique: id_historique est NULL dans DB pour ligne: {dict(row) if hasattr(row, "keys") else row}")
                 return None

            # Conversion du timestamp
            date_releve_obj = None
            if row['date_releve']:
                 # Utilisez votre helper parse_iso_datetime
                 try: date_releve_obj = datetime.fromisoformat(row['date_releve'])
                 except (ValueError, TypeError):
                       logger.warning(f"Impossible de parser date_releve '{row['date_releve']}' pour historique ID {hist_id_for_log}")


            instance = cls(
                id_historique=int(hist_id),
                compteur_id=int(row['compteur_id']),
                date_releve=date_releve_obj, # Assignez l'objet datetime
                valeur=float(row['valeur']),
                utilisateur_id=row['utilisateur_id'], # Optional int
                maintenance_id=row['maintenance_id'] # Optional int
            )
            # logger.debug(f"HistoriqueCompteur chargé depuis DB: {instance}")
            return instance

        except KeyError as e:
             logger.error(f"Clé manquante '{e}' lors création HistoriqueCompteur (ID log: {hist_id_for_log}). Colonnes: {row.keys() if hasattr(row, "keys") else 'N/A'}")
             return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur type/conversion création HistoriqueCompteur ID {hist_id_for_log} depuis DB: {e}", exc_info=True)
            return None
        except Exception as e:
             logger.error(f"Erreur inattendue création HistoriqueCompteur depuis DB ID {hist_id_for_log}: {e}", exc_info=True)
             return None

    # --- Méthode pour préparer les paramètres ---
    def to_db_params(self, include_id: bool = False) -> tuple:
         """ Génère un tuple de paramètres pour INSERT ou UPDATE. """
         params = (
             self.compteur_id,
             # Utilisez votre helper format_iso_datetime
             self.date_releve.isoformat() if self.date_releve else None, # timestamp format standard ISO
             self.valeur,
             self.utilisateur_id,
             self.maintenance_id,
         )
         if include_id:
             if self.id_historique is None:
                 raise ValueError("ID de l'historique manquant pour les paramètres UPDATE.")
             return params + (self.id_historique,)
         return params
