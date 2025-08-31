# gmao_app/app/core/models/piece.py
""" Modèle pour l'entité Pièce détachée. """
from dataclasses import dataclass
from typing import Any, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class Piece:
    """ Représente une pièce détachée dans le système GMAO. """

    # --- Champs OBLIGATOIRES (sans valeur par défaut) ---
    reference: str  # Référence unique (UK dans DB)
    nom: str        # Description
    unite: str      # Ex: "unité", "m", "L", "kg"

    # --- Champs OPTIONNELS (avec valeur par défaut ou Optional) ---
    prix_unitaire: float = 0.0
    stock_actuel: int = 0
    fournisseur_pref_id: Optional[int] = None # FK vers Fournisseur (Nullable)
    stock_alerte: Optional[int] = 0           # Seuil pour alerte (peut être 0 ou None)
    stock_reserve: int = 0                    # Stock réservé (commence à 0)
    categorie: Optional[str] = None           # Ex: Filtre, Roulement, Visserie
    emplacement_stockage: Optional[str] = None  # Code emplacement
    statut: Optional[str] = "Actif"           # Ex: Actif, Obsolete...

    # --- Clé Primaire (PK) ---
    # Déclaré comme optionnel, sera None avant insertion, et un int après lecture DB
    id_piece: Optional[int] = None

    # --- Méthode Factory pour créer depuis une ligne DB ---
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['Piece']:
        """
        Crée une instance de Piece à partir d\'une ligne de base de données.
        Retourne None si la ligne est None.
        """
        if row is None:
            return None

        try:
            # Extrait et convertit les valeurs, gérant les None de la DB
            # et les assignant aux bons types attendus par la dataclass
            piece_id = row['id_piece'] # Peut être None si erreur DB? Normalement non pour PK
            if piece_id is None:
                logger.error(f"Erreur critique: id_piece est NULL dans la base de données pour la ligne: {dict(row)}")
                # On pourrait lever une erreur ou retourner None pour ignorer la ligne
                return None

            prix_unit = float(row['prix_unitaire']) if row['prix_unitaire'] is not None else 0.0
            stock_act = int(row['stock_actuel'] or 0)
            # Pour les champs Optional[int], on garde None si c'est NULL en DB
            fourn_id = row['fournisseur_pref_id'] # Déjà Optional[int] ou None
            stock_alert = int(row['stock_alerte']) if row['stock_alerte'] is not None else None # Garder None si NULL

            stock_res = int(row['stock_reserve'] or 0) # Mettre 0 si NULL/non défini

            # Création de l'instance via le constructeur généré par @dataclass
            instance = cls(
                 id_piece=int(piece_id), # Assurer que l'ID est un int
                 reference=row['reference'],
                 nom=row['nom'],
                 unite=row['unite'],
                 fournisseur_pref_id=fourn_id,
                 prix_unitaire=prix_unit,
                 stock_actuel=stock_act,
                 stock_alerte=stock_alert,
                 stock_reserve=stock_res,
                 categorie=row['categorie'], # Déjà Optional[str] ou None
                 emplacement_stockage=row['emplacement_stockage'], # Déjà Optional[str] ou None
                 statut=row['statut'] or "Actif", # Défaut si NULL
            )
            logger.debug(f"Pièce chargée depuis DB: {instance}")
            return instance

        except KeyError as e:
             logger.error(f"Clé manquante '{e}' lors création Piece depuis DB. Colonnes: {row.keys()}")
             return None
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur type/conversion création Piece ID {row.get('id_piece','N/A')} depuis DB: {e}", exc_info=True)
            return None
        except Exception as e:
             logger.error(f"Erreur inattendue création Piece depuis DB ID {row.get('id_piece','N/A')}: {e}", exc_info=True)
             return None
