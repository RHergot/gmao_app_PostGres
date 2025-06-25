# gmao_app/app/core/models/ligne_commande.py
""" Modèle pour l'entité Ligne de Commande d'achat. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any
import logging
from datetime import date, datetime
from app.utils.helpers import parse_iso_date, format_iso_date # Assurez-vous que ces helpers existent

logger = logging.getLogger(__name__)

@dataclass
class LigneCommande:
    """ Représente une ligne d'une commande d'achat. """

    # --- Champs OBLIGATOIRES ---
    commande_id: int          # FK vers Commande
    piece_id: int             # FK vers Pièce
    quantite_commandee: int
    prix_unitaire_ht: float   # Prix unitaire au moment de la commande

    # --- Champs OPTIONNELS ---
    description_libre: Optional[str] = None # Si pièce non cataloguée (pas idéal, mais prévu ERD)
    quantite_recue: int = 0
    date_reception: Optional[date] = None   # Date de la dernière réception pour cette ligne
    statut_ligne: str = "Attente" # Enum: Attente, Partielle, Recue
    piece_reference: Optional[str] = None   # Reference de la pièce (si cataloguée)
    piece_nom: Optional[str] = None        # Nom de la pièce (si cataloguée)

    # --- Clé Primaire (PK) ---
    id_ligne: Optional[int] = None
    
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['LigneCommande']:
        """ Crée une instance de LigneCommande à partir d'une ligne de base de données. """
        if row is None:
            return None
        ligne_id_for_log = 'N/A'
        try:
            ligne_id = row['id_ligne']
            if ligne_id is None:
                 logger.error(f"Erreur critique: id_ligne est NULL dans DB pour ligne: {dict(row) if hasattr(row, 'keys') else row}")
                 return None

            instance = cls(
                id_ligne=int(ligne_id),
                commande_id=int(row['commande_id']),
                piece_id=int(row['piece_id']),
                quantite_commandee=int(row['quantite_commandee']),
                prix_unitaire_ht=float(row['prix_unitaire_ht']),
                quantite_recue=int(row['quantite_recue'] or 0),
                date_reception=parse_iso_date(row['date_reception']), # Utilise helper
                statut_ligne=row['statut_ligne'],
                description_libre=row['description_libre'],
                piece_reference=row['piece_reference'],
                piece_nom=row['piece_nom']            )
            logger.debug(f"LigneCommande chargée depuis DB: {instance}")
            return instance

        except KeyError as e:
            logger.error(f"Clé manquante '{e}' lors création LigneCommande depuis DB (ID log: {ligne_id_for_log}). Colonnes: {row.keys() if hasattr(row, 'keys') else 'N/A'}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur type/conversion création LigneCommande ID {ligne_id_for_log} depuis DB: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue création LigneCommande depuis DB ID {ligne_id_for_log}: {e}", exc_info=True)
            return None

    def to_db_params(self, include_id: bool = False) -> tuple:
         """ Génère un tuple de paramètres pour INSERT ou UPDATE (sans l'ID par défaut). """
         params = (
             self.commande_id,
             self.piece_id,
             self.quantite_commandee,
             self.prix_unitaire_ht,
             self.quantite_recue,
             format_iso_date(self.date_reception), # Helper inverse
             self.statut_ligne,
             self.description_libre,
         )
         if include_id:
             return params + (self.id_ligne,)
         return params