# gmao_app/app/core/models/mouvement_stock.py
""" Modèle pour l'entité MouvementStock. """
from dataclasses import dataclass, field
from typing import Any,  Dict,  Union,  Optional
import datetime
import logging

logger = logging.getLogger(__name__)

VALID_TYPES_MOUVEMENT = ['ENTREE', 'SORTIE', 'AJUSTEMENT']

@dataclass
class MouvementStock:
    """ Représente un mouvement de stock dans le système GMAO. """

    # --- Champs Obligatoires (sans valeur par défaut) ---
    piece_id: int
    type_mouvement: str # 'ENTREE', 'SORTIE', 'AJUSTEMENT'
    quantite: int      # Positive ou négative selon le type

    # --- Clé Primaire (avec valeur par défaut) ---
    id_mouvement: Optional[int] = None

    # --- Clés Étrangères Optionnelles (avec valeur par défaut) ---
    ot_id: Optional[int] = None
    user_id: Optional[int] = None
    # commande_id: Optional[int] = None # Pour plus tard

    # --- Champs Optionnels / Auto-générés (avec valeur par défaut) ---
    date_mouvement: str = field(default_factory=lambda: datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    raison: Optional[str] = None
    stock_avant: Optional[int] = None # Valeur informative
    stock_apres: Optional[int] = None # Valeur informative
    updated_at: Optional[str] = None  # Mis à jour par trigger DB

    # --- Méthode Factory pour créer depuis une ligne DB --- TODO
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['MouvementStock']:
        """
        Crée une instance de MouvementStock à partir d\'une ligne de base de données.
        Retourne None si la ligne est None.
        """
        if row is None:
            return None

        try:
            # TODO: Implémenter la conversion des champs
            instance = cls(
                piece_id=row['piece_id'],
                type_mouvement=row['type_mouvement'],
                quantite=row['quantite'],
                id_mouvement=row.get('id_mouvement'), 
                ot_id=row.get('ot_id'), # Utiliser get pour les optionnels
                user_id=row.get('user_id'),
                date_mouvement=row['date_mouvement'],
                raison=row.get('raison'),
                stock_avant=row.get('stock_avant'),
                stock_apres=row.get('stock_apres'),
                updated_at=row.get('updated_at')
                # commande_id=row.get('commande_id')
            )
            if instance.type_mouvement not in VALID_TYPES_MOUVEMENT:
                logger.warning(f"Type de mouvement invalide '{instance.type_mouvement}' chargé depuis DB pour ID {instance.id_mouvement}")
                # Peut-être lever une erreur ou retourner None ? Pour l'instant, on logge.

            logger.debug(f"MouvementStock chargé depuis DB: {instance}")
            return instance

        except KeyError as e:
             logger.error(f"Clé manquante '{e}' lors création MouvementStock depuis DB. Colonnes: {row.keys()}")
             return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur type/conversion création MouvementStock ID {row.get('id_mouvement','N/A')} depuis DB: {e}", exc_info=True)
            return None
        except Exception as e:
             logger.error(f"Erreur inattendue création MouvementStock depuis DB ID {row.get('id_mouvement','N/A')}: {e}", exc_info=True)
             return None

    def __post_init__(self):
        """ Validations après initialisation. """
        if self.type_mouvement not in VALID_TYPES_MOUVEMENT:
            raise ValueError(f"Type de mouvement '{self.type_mouvement}' invalide. Doit être un de {VALID_TYPES_MOUVEMENT}")
        # On pourrait ajouter ici une validation pour s'assurer que piece_id est bien défini
        # if self.piece_id is None:
        #    raise ValueError("piece_id ne peut pas être None pour un MouvementStock")

        # On pourrait vérifier la cohérence de la quantité avec le type ici
        # Exemple: si type_mouvement == 'SORTIE', quantite devrait être négative (ou positive et on la change ?)
        # Pour l'instant, on suppose que la logique d'appel gère le signe correctement.

