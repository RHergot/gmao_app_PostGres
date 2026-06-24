# gmao_app/app/core/models/gamme_etape.py
""" Modèle pour l'entité GammeEtape. """
from dataclasses import dataclass, field
from typing import Any,  Dict,  Union,  Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class GammeEtape:
    """ Représente une étape d'une gamme de maintenance. """
    gamme_id: int           # FK vers GammeEntretien
    description: str
    ordre: int              # Numéro d'ordre de l'étape
    instructions_detaillees: Optional[str] = None
    duree_estimee_min: Optional[int] = None
    id_etape: Optional[int] = None # PK

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['GammeEtape']:
        """ Crée une instance depuis une ligne DB. """
        if row is None: return None
        try:
            return cls(
                id_etape=row['id_etape'],
                gamme_id=row['gamme_id'],
                description=row['description'],
                ordre=int(row['ordre']),
                instructions_detaillees=row['instructions_detaillees'],
                duree_estimee_min=row['duree_estimee_min']
            )
        except KeyError as e: logger.error(f"Clé manquante '{e}' GammeEtape. Keys:{row.keys()}"); return None
        except Exception as e: logger.error(f"Erreur création GammeEtape ID {row.get('id_etape','N/A')}: {e}", exc_info=True); return None
