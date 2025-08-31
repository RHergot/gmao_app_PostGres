# gmao_app/app/core/models/utilisateur.py
"""
Modèle de données pour l'entité Utilisateur.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

@dataclass
class Utilisateur:
    """Représente un utilisateur du système."""
    login: str
    role: str # TODO: Utiliser un Enum plus tard
    nom_complet: Optional[str] = None
    email: Optional[str] = None # Ajout
    mot_de_passe_hash: Optional[str] = None # Ajout - Le hash sera stocké ici
    actif: bool = True
    derniere_connexion: Optional[datetime] = None # Ajout
    id_utilisateur: Optional[int] = None # Généré par la DB
    created_at: Optional[datetime] = None # Généré par la DB
    updated_at: Optional[datetime] = None # Généré par la DB
    technicien_id: Optional[int] = None # Ajout lien optionnel

    # La méthode __post_init__ pourrait être utilisée pour valider des données si besoin
    
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Utilisateur']:
         """Crée un objet Utilisateur à partir d'une ligne de base de données."""
         if row is None:
             return None
         # Convertir les timestamps ISO string en datetime objets
         created_at_dt = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
         updated_at_dt = datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
         derniere_connexion_dt = datetime.fromisoformat(row['derniere_connexion']) if row['derniere_connexion'] else None

         return cls(
             id_utilisateur=row['id_utilisateur'],
             login=row['login'],
             nom_complet=row['nom_complet'],
             role=row['role'],
             email=row['email'],
             mot_de_passe_hash=row['mot_de_passe_hash'],
             actif=bool(row['actif']), # Convertir 0/1 en bool
             derniere_connexion=derniere_connexion_dt,
             created_at=created_at_dt,
             updated_at=updated_at_dt,
             technicien_id=row['technicien_id'],
         )