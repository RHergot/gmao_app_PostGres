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
    """
    Représente une ligne d'une commande d'achat.
    Cette classe est un "Data Transfer Object" (DTO) qui sert à la fois
    de modèle de données pour l'application et de structure pour la persistance
    en base de données.
    """

    # --- Champs OBLIGATOIRES ---
    # Ces champs doivent être fournis lors de la création d'une ligne de commande.
    commande_id: int          # Clé étrangère (FK) vers la table 'Commande'. Identifie la commande parente.
    piece_id: int             # Clé étrangère (FK) vers la table 'Piece'. Identifie l'article commandé.
    quantite_commandee: int   # La quantité de la pièce qui a été commandée.
    prix_unitaire_ht: float   # Le prix unitaire hors taxes de la pièce au moment de la commande.

    # --- Champs OPTIONNELS ---
    # Ces champs ont des valeurs par défaut et peuvent ne pas être définis initialement.
    description_libre: Optional[str] = None # Permet d'ajouter une description pour une pièce non cataloguée.
    quantite_recue: int = 0                 # La quantité de la pièce qui a déjà été reçue. Initialisée à 0.
    date_reception: Optional[date] = None   # La date de la dernière réception pour cette ligne de commande.
    statut_ligne: str = "Attente"           # Le statut actuel de la ligne (ex: "Attente", "Partielle", "Reçue").
    piece_reference: Optional[str] = None   # La référence du fabricant ou interne de la pièce (dénormalisé pour accès rapide).
    piece_nom: Optional[str] = None         # Le nom de la pièce (dénormalisé pour accès rapide).

    # --- Clé Primaire (PK) ---
    id_ligne: Optional[int] = None          # L'identifiant unique de la ligne de commande, auto-généré par la base de données.
    
    @classmethod
    def from_db_row(cls, row: Optional[Union[Dict[str, Any], Any]]) -> Optional['LigneCommande']:
        """
        Crée une instance de LigneCommande à partir d'une ligne de résultat de base de données.
        Cette méthode de fabrique (factory method) gère la conversion des types de données
        et la gestion des erreurs pour créer un objet robuste.

        Args:
            row: Une ligne de la base de données, généralement un dictionnaire ou un objet similaire.

        Returns:
            Une instance de LigneCommande si la conversion réussit, sinon None.
        """
        if row is None:
            return None
        
        # Utiliser un identifiant pour le logging en cas d'erreur avant que l'ID soit extrait.
        ligne_id_for_log = 'N/A'
        try:
            # L'ID de la ligne est crucial, on le vérifie en premier.
            ligne_id = row['id_ligne']
            if ligne_id is None:
                 logger.error(f"Erreur critique: id_ligne est NULL dans la base de données pour la ligne: {dict(row) if hasattr(row, 'keys') else row}")
                 return None

            # Création de l'instance avec conversion et validation des types.
            instance = cls(
                id_ligne=int(ligne_id),
                commande_id=int(row['commande_id']),
                piece_id=int(row['piece_id']),
                quantite_commandee=int(row['quantite_commandee']),
                prix_unitaire_ht=float(row['prix_unitaire_ht']),
                
                # Gestion des valeurs par défaut pour les champs optionnels.
                quantite_recue=int(row['quantite_recue'] or 0),
                date_reception=parse_iso_date(row['date_reception']), # Utilise un helper pour parser la date.
                statut_ligne=row['statut_ligne'],
                description_libre=row['description_libre'],
                
                # Champs dénormalisés pour affichage.
                piece_reference=row['piece_reference'],
                piece_nom=row['piece_nom']
            )
            logger.debug(f"LigneCommande chargée avec succès depuis la base de données: {instance}")
            return instance

        except KeyError as e:
            # Erreur si une colonne attendue est manquante dans le résultat de la requête.
            logger.error(f"Clé manquante '{e}' lors de la création de LigneCommande depuis la DB (ID log: {ligne_id_for_log}). Colonnes disponibles: {row.keys() if hasattr(row, 'keys') else 'N/A'}")
            return None
        except (ValueError, TypeError) as e:
            # Erreur si la conversion de type échoue (ex: un texte au lieu d'un nombre).
            logger.error(f"Erreur de type/conversion pour LigneCommande ID {ligne_id_for_log} depuis la DB: {e}", exc_info=True)
            return None
        except Exception as e:
            # Capture toutes les autres erreurs inattendues.
            logger.error(f"Erreur inattendue lors de la création de LigneCommande depuis la DB ID {ligne_id_for_log}: {e}", exc_info=True)
            return None

    def to_db_params(self, include_id: bool = False) -> tuple:
         """
         Génère un tuple de paramètres à utiliser pour une requête SQL (INSERT ou UPDATE).
         L'ordre des paramètres doit correspondre à celui des colonnes dans la requête SQL.

         Args:
             include_id: Si True, inclut l'ID de la ligne à la fin du tuple (utile pour les requêtes UPDATE).

         Returns:
             Un tuple contenant les valeurs de l'objet, prêtes à être passées à la base de données.
         """
         params = (
             self.commande_id,
             self.piece_id,
             self.quantite_commandee,
             self.prix_unitaire_ht,
             self.quantite_recue,
             format_iso_date(self.date_reception), # Utilise un helper pour formater la date en ISO string.
             self.statut_ligne,
             self.description_libre,
         )
         if include_id:
             # Pour un UPDATE, on a souvent besoin de l'ID dans la clause WHERE.
             return params + (self.id_ligne,)
         return params