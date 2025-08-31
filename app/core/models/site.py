# gmao_app/app/core/models/site.py
""" Modèle de données pour l'entité Site. """
from dataclasses import dataclass, field
from typing import Any,  Dict,  Union,  Optional

@dataclass
class Site:
    nom: str
    adresse: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    contact_principal: Optional[str] = None
    id_site: Optional[int] = None # PK
    
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Site']:
        if row is None: return None
        return cls(
            id_site=row.get('id_site'),
            nom=row.get('nom'),
            adresse=row.get('adresse'),
            ville=row.get('ville'),
            pays=row.get('pays'),
            contact_principal=row.get('contact_principal')
        )
