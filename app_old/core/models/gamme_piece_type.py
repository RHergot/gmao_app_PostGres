# gmao_app/app/core/models/gamme_piece_type.py
""" Modèle pour l'entité GammePieceType (lien Gamme <-> Pièce). """
from dataclasses import dataclass
from typing import Any,  Dict,  Union,  Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class GammePieceType:
    """ Représente une pièce typiquement requise pour une gamme. """
    gamme_id: int               # FK vers GammeEntretien
    piece_id: int               # FK vers Piece
    quantite_theorique: int = 1 # Quantité par défaut
    id: Optional[int] = None    # PK

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['GammePieceType']:
        """ Crée une instance depuis une ligne DB. """
        if row is None: return None
        try:
            return cls(
                id=row['id'],
                gamme_id=row['gamme_id'],
                piece_id=row['piece_id'],
                quantite_theorique=int(row['quantite_theorique'] or 1) # Assurer une valeur par défaut
            )
        except KeyError as e: logger.error(f"Clé manquante '{e}' GammePieceType. Keys:{row.keys()}"); return None
        except Exception as e: logger.error(f"Erreur création GammePieceType ID {row.get('id','N/A')}: {e}", exc_info=True); return None
