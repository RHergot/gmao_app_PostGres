# gmao_app/app/core/models/type_machine.py
""" Modèle de données pour l'entité TypeMachine. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

@dataclass
class TypeMachine:
    nom: str
    description: Optional[str] = None
    categorie: Optional[str] = None # Ex: Mécanique, Electrique, Hydraulique
    id_type_machine: Optional[int] = None # PK

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['TypeMachine']:
        if row is None: return None
        return cls(
            id_type_machine=row['id_type_machine'],
            nom=row['nom'],
            description=row['description'],
            categorie=row['categorie']
        )