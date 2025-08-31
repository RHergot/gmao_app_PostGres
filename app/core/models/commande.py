# gmao_app/app/core/models/commande.py
""" Modèle pour l'entité Commande d'achat. """
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any
import logging
from datetime import date, datetime
from app.utils.helpers import parse_iso_date, parse_iso_datetime, format_iso_date # Assurez-vous que ces helpers existent

logger = logging.getLogger(__name__)

@dataclass
class Commande:
    """ Représente une commande d'achat. """

    # --- Champs OBLIGATOIRES ---
    fournisseur_id: int      # FK vers Fournisseur
    utilisateur_createur_id: int # FK vers Utilisateur
    date_commande: date      # Date de création de la commande
    statut: str = "Brouillon" # Enum: Brouillon, Validee, Envoyee, Partielle, Livree, Annulee

    # --- Champs OPTIONNELS ---
    numero_commande: Optional[str] = None # Numéro unique lisible (peut être généré ou saisi)
    date_livraison_prevue: Optional[date] = None
    date_livraison_reelle: Optional[date] = None # Dernière date de livraison enregistrée
    reference_fournisseur: Optional[str] = None # Numéro de commande chez le fournisseur
    mode_paiement: Optional[str] = None
    notes_commande: Optional[str] = None
    nom_fournisseur: Optional[str] = None # Nom du fournisseur (pour affichage)
    total_ht: float = 0.0         # Calculé à partir des lignes (peut être stocké pour perf)
    frais_port: float = 0.0
    # total_ttc: Optional[float] = None # Optionnel, dépend si TVA gérée

    # --- Timestamps & PK ---
    created_at: Optional[datetime] = field(default_factory=datetime.now) # Initialisé en Python
    updated_at: Optional[datetime] = field(default_factory=datetime.now) # Initialisé en Python
    id_commande: Optional[int] = None  # PK    
    
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Commande']:
        """ Crée une instance de Commande à partir d'une ligne de base de données. """
        if row is None:
            return None

        try:
            cmd_id = row['id_commande']
            if cmd_id is None:
                 logger.error(f"Erreur critique: id_commande est NULL dans DB pour ligne: {dict(row)}")
                 return None
            
            nom_fourn = row['nom_fournisseur'] if 'nom_fournisseur' in row.keys() else None

            instance = cls(
                id_commande=int(cmd_id),
                numero_commande=row['numero_commande'],
                fournisseur_id=int(row['fournisseur_id']),
                utilisateur_createur_id=int(row['createur_id']), # Note: nom colonne différent
                date_commande=parse_iso_date(row['date_commande']), # Utilise helper
                date_livraison_prevue=parse_iso_date(row['date_livraison_prevue']), # Utilise helper
                date_livraison_reelle=parse_iso_date(row['date_livraison_reelle']), # Utilise helper
                statut=row['statut'],
                total_ht=float(row['total_ht'] or 0.0),
                frais_port=float(row['frais_port'] or 0.0),
                # total_ttc=float(row['total_ttc']) if row['total_ttc'] is not None else None,
                reference_fournisseur=row['reference_fournisseur'],
                mode_paiement=row['mode_paiement'],
                notes_commande=row['notes_commande'],
                created_at=parse_iso_datetime(row['created_at']), # Utilise helper
                updated_at=parse_iso_datetime(row['updated_at']), # Utilise helper
                # --- Assigner le nom fournisseur ---
                nom_fournisseur=nom_fourn
            )
            logger.debug(f"Commande chargée depuis DB: {instance}")
            return instance

        except KeyError as e:
            logger.error(f"Clé manquante '{e}' lors création Commande depuis DB. Colonnes: {row.keys()}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur type/conversion création Commande ID {row.get('id_commande','N/A')} depuis DB: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue création Commande depuis DB ID {row.get('id_commande','N/A')}: {e}", exc_info=True)
            return None

    def to_db_params(self, include_id: bool = False) -> tuple:
         """ Génère un tuple de paramètres pour INSERT ou UPDATE (sans l'ID par défaut). """
         params = (
             self.numero_commande,
             self.fournisseur_id,
             self.utilisateur_createur_id,
             format_iso_date(self.date_commande), # Helper inverse
             format_iso_date(self.date_livraison_prevue), # Helper inverse
             format_iso_date(self.date_livraison_reelle), # Helper inverse
             self.statut,
             self.total_ht,
             self.frais_port,
             self.reference_fournisseur,
             self.mode_paiement,
             self.notes_commande,
             # created_at est géré par défaut DB ou Trigger
             # updated_at est géré par Trigger
         )
         if include_id:
             return params + (self.id_commande,)
         return params