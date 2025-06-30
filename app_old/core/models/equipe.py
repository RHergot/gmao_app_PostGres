# gmao_app/app/core/models/equipe.py
""" Modèle pour l'entité Equipe. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

@dataclass
class Equipe:
    nom: str
    domaine_expertise: Optional[str] = None
    responsable_id: Optional[int] = None # FK vers Technicien (nullable si pas de resp.)
    id_equipe: Optional[int] = None # PK

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Equipe']:
        if row is None: return None
        return cls(
            id_equipe=row['id_equipe'],
            nom=row['nom'],
            domaine_expertise=row['domaine_expertise'],
            responsable_id=row['responsable_id']
        )