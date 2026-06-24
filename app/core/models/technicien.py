# gmao_app/app/core/models/technicien.py
""" Modèle pour l'entité Technicien. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

# Importer Equipe si on veut typer l'attribut equipe (pas crucial ici)
# from .equipe import Equipe

@dataclass
class Technicien:
    nom: str
    prenom: Optional[str] = None
    qualification: Optional[str] = None
    contact: Optional[str] = None
    cout_horaire: Optional[float] = 0.0 # Utiliser float pour decimal
    equipe_id: Optional[int] = None # FK vers Equipe (nullable si pas d'équipe)
    actif: bool = True
    id_technicien: Optional[int] = None # PK
    # Note : Un technicien peut aussi être un utilisateur (lien dans UTILISATEUR)

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Technicien']:
        if row is None: return None
        return cls(
            id_technicien=row['id_technicien'],
            nom=row['nom'],
            prenom=row['prenom'],
            qualification=row['qualification'],
            contact=row['contact'],
            cout_horaire=float(row['cout_horaire']) if row['cout_horaire'] is not None else 0.0,
            equipe_id=row['equipe_id'],
            actif=bool(row['actif'])
        )

    # Propriété pour affichage facile du nom complet
    @property
    def nom_complet(self) -> str:
        return f"{self.prenom or ''} {self.nom}".strip()