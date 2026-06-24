# gmao_app/app/core/models/compteur.py
""" Modèle pour l'entité Compteur Machine. """
from dataclasses import dataclass, field
from typing import Any, Dict, Union, Optional
import logging
from datetime import date
from app.utils.helpers import format_iso_date, parse_iso_date

logger = logging.getLogger(__name__)

@dataclass
class Compteur:
    """ Représente un compteur (Ex: heures, cycles) associé à une machine. """

    # --- Champs OBLIGATOIRES ---
    machine_id: int # FK vers MACHINE
    nom: str        # Nom du compteur (Ex: "Heures Moteur", "Nombre de Cycles")
    unite: str      # Unité (Ex: "heures", "cycles", "km", "°C")

    # --- Champs OPTIONNELS (avec valeur par défaut ou Optional) ---
    valeur_actuelle: float = 0.0 # Dernière valeur connue
    date_dernier_releve: Optional[date] = None # Date du dernier relevé (juste la date)
    seuil_alerte: Optional[float] = None     # Seuil pour alerte simple
    seuil_prev_ot: Optional[float] = None    # Seuil pour déclencher un OT préventif (CBM)
    actif: bool = True # Marquer un compteur comme inactif? (Pas dans l'ERD, mais utile)

    # --- Clé Primaire (PK) ---
    id_compteur: Optional[int] = None

    # --- Méthode Factory pour créer depuis une ligne DB ---
    @classmethod
    def from_db_row(cls, row: Optional[dict]) -> Optional['Compteur']:
        """
        Crée une instance de Compteur à partir d'une ligne dict (PostgreSQL).
        """
        if row is None:
            return None

        compteur_id = row.get('id_compteur')
        if compteur_id is None:
            logger.error(f"Erreur critique: id_compteur est NULL dans DB pour ligne: {row}")
            return None

        valeur_act = float(row.get('valeur_actuelle', 0.0) if row.get('valeur_actuelle') is not None else 0.0)
        date_der_releve = None
        if row.get('date_dernier_releve'):
            try:
                date_der_releve = date.fromisoformat(row.get('date_dernier_releve'))
            except (ValueError, TypeError):
                logger.warning(f"Impossible de parser date_dernier_releve '{row.get('date_dernier_releve')}' pour compteur ID {compteur_id}")

        seuil_al = float(row.get('seuil_alerte')) if row.get('seuil_alerte') is not None else None
        seuil_prev = float(row.get('seuil_prev_ot')) if row.get('seuil_prev_ot') is not None else None

        return cls(
            id_compteur=compteur_id,
            machine_id=row.get('machine_id'),
            nom=row.get('nom'),
            unite=row.get('unite'),
            valeur_actuelle=valeur_act,
            date_dernier_releve=date_der_releve,
            seuil_alerte=seuil_al,
            seuil_prev_ot=seuil_prev,
            actif=row.get('actif', True) if 'actif' in row else True
        )

    # --- Méthode pour préparer les paramètres pour la DB ---
    def to_db_params(self, include_id: bool = False) -> tuple:
         """ Génère un tuple de paramètres pour INSERT ou UPDATE. """
         params = (
             self.machine_id,
             self.nom,
             self.unite,
             self.valeur_actuelle,
             # date_dernier_releve sera mis à jour par le service/repo
             format_iso_date(self.date_dernier_releve), # Utilisez votre helper
             self.seuil_alerte,
             self.seuil_prev_ot,
             # self.actif # Si champ actif ajouté en DB (convertir bool to int 0/1)
         )
         if include_id:
             # Assurez-vous que l'ID est valide pour update
             if self.id_compteur is None:
                  raise ValueError("ID du compteur manquant pour les paramètres UPDATE.")
             return params + (self.id_compteur,)
         return params
