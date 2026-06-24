# gmao_app/app/core/models/fabricant.py
""" Modèle de données pour l'entité Fabricant. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

@dataclass
class Fabricant:
    nom: str
    contact: Optional[str] = None
    site_web: Optional[str] = None
    support_technique: Optional[str] = None
    id_fabricant: Optional[int] = None # PK

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Fabricant']:
        if row is None: return None
        return cls(
            id_fabricant=row['id_fabricant'],
            nom=row['nom'],
            contact=row['contact'],
            site_web=row['site_web'],
            support_technique=row['support_technique']
        )