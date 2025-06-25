# gmao_app/app/core/models/gamme_entretien.py
""" Modèle pour l'entité GammeEntretien. """
from dataclasses import dataclass, field
from typing import Any,  Dict,  Union,  Optional, List
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # Pour calculs dates précis
import logging

logger = logging.getLogger(__name__)

# TODO: Externaliser ces listes dans config ou DB
VALID_PERIODICITE_UNITES = ["Jours", "Semaines", "Mois", "Années", "Heures", "Cycles"]
VALID_ENTRETIEN_TYPES = ["Préventif Systématique", "Préventif Conditionnel", "Contrôle Réglementaire", "Nettoyage", "Lubrification", "Remplacement"]
VALID_PRIORITES_GAMME = ["Basse", "Moyenne", "Haute"] # Priorité par défaut des OT générés

@dataclass
class GammeEntretien:
    """ Représente une gamme ou un plan de maintenance préventive. """
    description: str       # Nom/Code unique de la gamme
    periodicite_valeur: Optional[int] = None # Ex: 3 (pour 3 mois)
    periodicite_unite: Optional[str] = None # Ex: "Mois" (parmi VALID_PERIODICITE_UNITES)
    type_machine_id: Optional[int] = None # Optionnel: Applicable à un type de machine
    type_entretien: Optional[str] = "Préventif Systématique" # Type par défaut
    instructions: Optional[str] = None    # Instructions générales
    date_derniere_realisation: Optional[date] = None # Date de la dernière maintenance basée sur cette gamme
    active: bool = True                   # Si la gamme doit générer des OT
    duree_estimee_min: Optional[int] = None # Durée estimée totale en minutes
    qualification_requise: Optional[str] = None # Compétence nécessaire
    priorite: Optional[str] = "Moyenne"   # Priorité par défaut des OT générés

    # Champs gérés par le système/DB
    id_gamme: Optional[int] = None         # PK
    createur_id: Optional[int] = None      # FK Utilisateur qui a créé
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    prochaine_date_calculee: Optional[date] = None # Stockée pour info, recalculée par service

    def calculate_next_due_date(self) -> Optional[date]:
        """
        Calcule la prochaine date d'échéance basée sur la dernière réalisation
        et la périodicité. Retourne None si infos manquantes.
        """
        if not self.date_derniere_realisation or \
           self.periodicite_valeur is None or self.periodicite_valeur <= 0 or \
           not self.periodicite_unite or self.periodicite_unite not in VALID_PERIODICITE_UNITES:
            logger.debug(f"Infos manquantes pour calculer prochaine date gamme {self.id_gamme or self.description}")
            return None

        last_date = self.date_derniere_realisation
        value = self.periodicite_valeur
        unit = self.periodicite_unite

        try:
            next_date: Optional[date] = None
            if unit == "Jours":
                next_date = last_date + timedelta(days=value)
            elif unit == "Semaines":
                next_date = last_date + timedelta(weeks=value)
            elif unit == "Mois":
                next_date = last_date + relativedelta(months=value)
            elif unit == "Années":
                next_date = last_date + relativedelta(years=value)
            # Note: "Heures" et "Cycles" ne peuvent pas être calculés juste avec une date.
            # Ils nécessitent une valeur de compteur. La génération d'OT pour ces types
            # devra utiliser la table COMPTEUR. Ici on retourne None pour ces unités.
            elif unit in ["Heures", "Cycles"]:
                 logger.debug(f"Calcul prochaine date impossible pour unité '{unit}' pour gamme {self.id_gamme}")
                 return None

            logger.debug(f"Calcul prochaine date pour gamme {self.id_gamme}: {last_date} + {value} {unit} = {next_date}")
            return next_date
        except Exception as e:
            logger.error(f"Erreur calcul prochaine date pour gamme {self.id_gamme}: {e}", exc_info=True)
            return None


    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['GammeEntretien']:
        """ Crée une instance depuis une ligne DB. """
        if row is None: return None
        try:
            last_date_dt = date.fromisoformat(row['date_derniere_realisation']) if row['date_derniere_realisation'] else None
            next_calc_dt = date.fromisoformat(row['prochaine_date_calculee']) if row['prochaine_date_calculee'] else None
            created_at_dt = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            updated_at_dt = datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None

            return cls(
                id_gamme=row['id_gamme'],
                description=row['description'],
                type_entretien=row['type_entretien'],
                periodicite_valeur=row['periodicite_valeur'],
                periodicite_unite=row['periodicite_unite'],
                instructions=row['instructions'],
                date_derniere_realisation=last_date_dt,
                prochaine_date_calculee=next_calc_dt, # Sera recalculé par service au besoin
                active=bool(row['active']),
                type_machine_id=row['type_machine_id'],
                createur_id=row['createur_id'],
                created_at=created_at_dt,
                updated_at=updated_at_dt,
                duree_estimee_min=row['duree_estimee_min'],
                qualification_requise=row['qualification_requise'],
                priorite=row['priorite']
            )
        except KeyError as e: logger.error(f"Clé manquante '{e}' GammeEntretien. Keys:{row.keys()}"); return None
        except Exception as e: logger.error(f"Erreur création Gamme ID {row.get('id_gamme','N/A')}: {e}", exc_info=True); return None
