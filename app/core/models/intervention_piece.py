# gmao_app/app/core/models/intervention_piece.py
""" Modèle pour l'entité InterventionPiece (lien N-N Maintenance <-> Pièce). """
from dataclasses import dataclass
from typing import Any, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class InterventionPiece:
    """ Représente une pièce utilisée lors d'une intervention de maintenance. """
    maintenance_id: int # FK vers Maintenance
    piece_id: int       # FK vers Piece
    quantite: int       # Quantité utilisée (doit être > 0)
    lot: Optional[str] = None # Numéro de lot/série utilisé (traçabilité)
    id: Optional[int] = None # PK

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['InterventionPiece']:
        """ Crée une instance depuis une ligne de DB. """
        if row is None:
            return None
        try:
            instance = cls(
                id=row['id'],
                maintenance_id=row['maintenance_id'],
                piece_id=row['piece_id'],
                quantite=int(row['quantite']), # Assurer int
                lot=row['lot']
            )
            # logger.debug(f"InterventionPiece chargée depuis DB: {instance}") # Log si besoin
            return instance
        except KeyError as e:
             logger.error(f"Clé manquante '{e}' création InterventionPiece. Colonnes: {row.keys()}")
             return None
        except (ValueError, TypeError) as e:
             logger.error(f"Erreur type/conv. InterventionPiece ID {row.get('id','N/A')}: {e}", exc_info=True)
             return None
        except Exception as e:
             logger.error(f"Erreur inatt. création InterventionPiece ID {row.get('id','N/A')}: {e}", exc_info=True)
             return None
