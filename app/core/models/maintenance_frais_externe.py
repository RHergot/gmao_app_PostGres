# gmao_app/app/core/models/maintenance_frais_externe.py
""" 
Modèle pour l'entité MaintenanceFraisExterne - gestion des frais additionnels 
(pièces externes, déplacements, sous-traitance, etc.) liés à une maintenance.
"""
from dataclasses import dataclass
from typing import Any,  Dict,  Union,  Optional, Literal
import logging

logger = logging.getLogger(__name__)

# Types valides de frais externes
VALID_TYPES_FRAIS = ['PIECE_EXTERNE', 'DEPLACEMENT', 'SOUS_TRAITANCE', 'AUTRE']
TypeFrais = Literal['PIECE_EXTERNE', 'DEPLACEMENT', 'SOUS_TRAITANCE', 'AUTRE']

@dataclass
class MaintenanceFraisExterne:
    """ 
    Représente un frais externe (pièce hors stock, déplacement, sous-traitance, etc.)
    associé à une maintenance.
    """
    maintenance_id: int          # FK vers Maintenance
    type_frais: str              # Type de frais (enum: PIECE_EXTERNE, DEPLACEMENT, etc.)
    description: str             # Description du frais
    montant: float               # Montant unitaire du frais
    quantite: int = 1            # Quantité (par défaut 1)
    reference_piece: Optional[str] = None  # Référence de la pièce externe
    fournisseur: Optional[str] = None      # Nom du fournisseur
    facture_reference: Optional[str] = None  # Référence de facture
    id_frais: Optional[int] = None        # PK
    created_at: Optional[str] = None      # Date de création

    def __post_init__(self):
        """Validation après initialisation"""
        if self.type_frais not in VALID_TYPES_FRAIS:
            raise ValueError(f"Type de frais invalide. Valeurs autorisées: {', '.join(VALID_TYPES_FRAIS)}")
        if self.montant < 0:
            raise ValueError("Le montant ne peut pas être négatif")
        if self.quantite <= 0:
            raise ValueError("La quantité doit être positive")
        # Si c'est une pièce externe, on devrait avoir une référence
        if self.type_frais == 'PIECE_EXTERNE' and not self.reference_piece:
            logger.warning("Un frais de type PIECE_EXTERNE devrait avoir une référence")

    @property
    def montant_total(self) -> float:
        """Calcule le montant total de ce frais"""
        return self.montant * self.quantite

    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['MaintenanceFraisExterne']:
        """Crée une instance à partir d'une ligne de base de données"""
        if row is None:
            return None
        try:
            return cls(
                id_frais=row['id_frais'],
                maintenance_id=row['maintenance_id'],
                type_frais=row['type_frais'],
                description=row['description'],
                montant=float(row['montant']),
                quantite=int(row['quantite']),
                reference_piece=row['reference_piece'],
                fournisseur=row['fournisseur'],
                facture_reference=row['facture_reference'],
                created_at=row['created_at']
            )
        except KeyError as e:
            logger.error(f"Clé manquante '{e}' dans MaintenanceFraisExterne. Keys: {row.keys()}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur de conversion de type dans MaintenanceFraisExterne ID {row.get('id_frais', 'N/A')}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la création de MaintenanceFraisExterne ID {row.get('id_frais', 'N/A')}: {e}", exc_info=True)
            return None
