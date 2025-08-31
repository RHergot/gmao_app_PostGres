# gmao_app/app/core/models/machine.py
""" Modèle de données pour l'entité Machine. """
from dataclasses import dataclass, field
from datetime import datetime, date # Ajout de 'date'
from typing import Optional

# Importer les types liés si utilisés comme attributs (pas nécessaire ici, Union, Dict, Any)
# from .site import Site
# from .fabricant import Fabricant
# from .type_machine import TypeMachine

@dataclass
class Machine:
    nom: str
    type_machine_id: int # FK vers TypeMachine
    site_id: int         # FK vers Site
    fabricant_id: int    # FK vers Fabricant
    serial: Optional[str] = None
    modele: Optional[str] = None
    date_installation: Optional[date] = None # Utiliser 'date' de datetime
    localisation: Optional[str] = None # Localisation précise dans le site
    etat: Optional[str] = "Inconnu" # Enum: En service, Panne, Maintenance...
    informations_techniques: Optional[str] = None
    parent_machine_id: Optional[int] = None # FK pour Hierarchie
    criticite: Optional[str] = None # Ex: A, B, C ou 1-5
    garantie_fin: Optional[date] = None # Utiliser 'date' de datetime
    id_machine: Optional[int] = None # PK
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # 'date_derniere_maintenance' n'est pas un champ direct du modèle ici,
    # ce sera une info calculée/récupérée via les maintenances liées.

    @classmethod
    def from_db_row(cls, row: Optional[dict]) -> Optional['Machine']:
        if row is None: return None
        # Conversion des dates/timestamps
        date_install_dt = date.fromisoformat(row.get('date_installation')) if row.get('date_installation') else None
        garantie_fin_dt = date.fromisoformat(row.get('garantie_fin')) if row.get('garantie_fin') else None
        created_at_dt = datetime.fromisoformat(row.get('created_at')) if row.get('created_at') else None
        updated_at_dt = datetime.fromisoformat(row.get('updated_at')) if row.get('updated_at') else None

        return cls(
            id_machine=row.get('id_machine'),
            nom=row.get('nom'),
            serial=row.get('serial'),
            modele=row.get('modele'),
            date_installation=date_install_dt,
            localisation=row.get('localisation'),
            etat=row.get('etat'),
            informations_techniques=row.get('informations_techniques'),
            type_machine_id=row.get('type_machine_id'),
            site_id=row.get('site_id'),
            fabricant_id=row.get('fabricant_id'),
            parent_machine_id=row.get('parent_machine_id'),
            criticite=row.get('criticite'),
            garantie_fin=garantie_fin_dt,
            created_at=created_at_dt,
            updated_at=updated_at_dt
        )