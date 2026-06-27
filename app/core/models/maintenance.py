# gmao_app/app/core/models/maintenance.py
""" Modèle pour l'entité Maintenance (intervention réalisée). """
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any,  Dict,  Union,  Optional

@dataclass
class Maintenance:
    ot_id: int              # FK vers OrdreTravail (Obligatoire pour lier)
    technicien_id: int      # FK vers Technicien (Qui a fait)
    date_debut_reelle: datetime
    date_fin_reelle: datetime
    type_reel: str          # Enum: Preventif, Correctif...
    description_travaux: str
    resultat: str           # Enum: OK, OK Réserve, NOK...
    machine_id: Optional[int] = None # Redondant si ot_id présent, mais peut être utile
    duree_intervention_h: Optional[float] = None # Calculé
    cout_manuel_v1: Optional[float] = None
    # Nouveaux champs pour la gestion financière - Phase 11
    cout_main_oeuvre: Optional[float] = None  # Somme des coûts intervenants
    cout_pieces_internes: Optional[float] = None  # Somme des coûts pièces du stock
    cout_pieces_externes: Optional[float] = None  # Somme des frais externes type PIECE_EXTERNE
    cout_autres_frais: Optional[float] = None  # Autres frais (déplacements, sous-traitance)
    cout_total: Optional[float] = None  # Somme de tous les coûts
    evaluation_qualite: Optional[int] = None # Note 1-5?
    impact_production: Optional[str] = None # Enum: Aucun, Mineur...
    notes_technicien: Optional[str] = None
    id_maintenance: Optional[int] = None # PK
    created_at: Optional[datetime] = None # Date de saisie

    def __post_init__(self):
        # Calculer durée si début et fin sont présents
        if self.date_debut_reelle and self.date_fin_reelle:
            delta = self.date_fin_reelle - self.date_debut_reelle
            self.duree_intervention_h = round(delta.total_seconds() / 3600, 2)
        else:
            self.duree_intervention_h = 0.0

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Maintenance']:
        if row is None: return None
        # Conversion timestamps
        date_debut_dt = datetime.fromisoformat(row['date_debut_reelle']) if row['date_debut_reelle'] else None
        date_fin_dt = datetime.fromisoformat(row['date_fin_reelle']) if row['date_fin_reelle'] else None
        created_at_dt = datetime.fromisoformat(row['created_at']) if row['created_at'] else None

        # Instancier sans la durée calculée pour l'instant
        instance = cls(
            id_maintenance=row['id_maintenance'],
            ot_id=row['ot_id'],
            machine_id=row['machine_id'], # Récupérer depuis DB
            technicien_id=row['technicien_id'],
            date_debut_reelle=date_debut_dt,
            date_fin_reelle=date_fin_dt,
            type_reel=row['type_reel'],
            description_travaux=row['description_travaux'],
            resultat=row['resultat'],
            cout_manuel_v1=float(row['cout_manuel_v1']) if row['cout_manuel_v1'] is not None else None,
            # Nouveaux champs financiers - Correction de l'accès
            cout_main_oeuvre=float(row['cout_main_oeuvre']) if row['cout_main_oeuvre'] is not None else None,
            cout_pieces_internes=float(row['cout_pieces_internes']) if row['cout_pieces_internes'] is not None else None,
            cout_pieces_externes=float(row['cout_pieces_externes']) if row['cout_pieces_externes'] is not None else None,
            cout_autres_frais=float(row['cout_autres_frais']) if row['cout_autres_frais'] is not None else None,
            cout_total=float(row['cout_total']) if row['cout_total'] is not None else None,
            evaluation_qualite=row['evaluation_qualite'],
            impact_production=row['impact_production'],
            notes_technicien=row['notes_technicien'],
            created_at=created_at_dt,
            # Ne pas passer duree_intervention_h ici, il sera recalculé par __post_init__
        )
        # La durée est recalculée dans __post_init__ appelé après l'init de base de @dataclass
        # Alternative: Lire row['duree_intervention_h'] s'il est stocké
        # instance.duree_intervention_h = float(row['duree_intervention_h']) if row['duree_intervention_h'] is not None else 0.0
        return instance
        
    def calculer_cout_total(self):
        """Calcule et met à jour le coût total à partir des différentes sources de coûts"""
        # Initialiser les coûts à 0 s'ils sont None
        self.cout_main_oeuvre = self.cout_main_oeuvre or 0.0
        self.cout_pieces_internes = self.cout_pieces_internes or 0.0
        self.cout_pieces_externes = self.cout_pieces_externes or 0.0
        self.cout_autres_frais = self.cout_autres_frais or 0.0
        
        # Calculer le coût total
        self.cout_total = (
            self.cout_main_oeuvre +
            self.cout_pieces_internes +
            self.cout_pieces_externes +
            self.cout_autres_frais
        )
        
        return self.cout_total
