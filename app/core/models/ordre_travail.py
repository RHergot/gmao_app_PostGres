# gmao_app/app/core/models/ordre_travail.py
""" Modèle pour l'entité OrdreTravail (OT). """
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any,  Dict,  Union,  Optional

@dataclass
class OrdreTravail:
    machine_id: int      # FK vers Machine
    type: str            # Enum: Preventif, Correctif, Demande...
    description: str
    priorite: str        # Enum: Haute, Moyenne, Basse
    statut: str          # Enum: Créé, Planifié, AttentePieces...
    utilisateur_createur_id: int # FK vers Utilisateur
    numero_ot: Optional[str] = None # Optionnel, peut être généré
    gamme_id: Optional[int] = None # FK vers GammeEntretien (Nullable, Union, Dict, Any)
    date_creation: datetime = field(default_factory=datetime.now)
    date_prevue: Optional[datetime] = None # Timestamp prévu début
    duree_prevue_min: Optional[int] = None
    urgence: bool = False
    technicien_assigne_id: Optional[int] = None # FK vers Technicien (Nullable)
    notes_planification: Optional[str] = None
    id_ot: Optional[int] = None # PK
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['OrdreTravail']:
        if row is None: return None
        # Conversion timestamps et date
        date_creation_dt = datetime.fromisoformat(row['date_creation']) if row['date_creation'] else datetime.now()
        date_prevue_dt = datetime.fromisoformat(row['date_prevue']) if row['date_prevue'] else None
        created_at_dt = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        updated_at_dt = datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None

        return cls(
            id_ot=row['id_ot'],
            numero_ot=row['numero_ot'],
            machine_id=row['machine_id'],
            gamme_id=row['gamme_id'],
            type=row['type'],
            description=row['description'],
            date_creation=date_creation_dt,
            date_prevue=date_prevue_dt,
            duree_prevue_min=row['duree_prevue_min'],
            priorite=row['priorite'],
            urgence=bool(row['urgence']),
            statut=row['statut'],
            technicien_assigne_id=row['technicien_assigne_id'],
            utilisateur_createur_id=row['utilisateur_createur_id'],
            notes_planification=row['notes_planification'],
            created_at=created_at_dt,
            updated_at=updated_at_dt
        )
