# gmao_app/app/core/models/fournisseur.py
""" Modèle pour l'entité Fournisseur. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

@dataclass
class Fournisseur:
    nom: str
    contact: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    delai_livraison_moyen_j: Optional[int] = None # En jours
    devise: Optional[str] = "EUR" # Défaut
    note_qualite: Optional[float] = None # Note 1-5?
    id_fournisseur: Optional[int] = None # PK    
    
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Fournisseur']:
        if row is None: return None
        return cls(
            id_fournisseur=row['id_fournisseur'],
            nom=row['nom'],
            contact=row['contact'],
            adresse=row['adresse'],
            telephone=row['telephone'],
            email=row['email'],
            delai_livraison_moyen_j=row['delai_livraison_moyen_j'],
            devise=row['devise'],
            note_qualite=float(row['note_qualite']) if row['note_qualite'] is not None else None,
        )