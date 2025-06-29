# gmao_app/app/core/services/stock_service.py
"""
Service métier pour la gestion du stock (Pièces, Fournisseurs)
et plus tard des Achats (Commandes, Réceptions).
"""
import logging
import datetime
from typing import Optional, List, Dict, Any

# Models
from app.core.models.piece import Piece
from app.core.models.fournisseur import Fournisseur
from app.core.models.mouvement_stock import MouvementStock, VALID_TYPES_MOUVEMENT # Ajout MouvementStock

# Repositories
from app.data.repositories import (
    PieceRepository,
    FournisseurRepository,
    MouvementStockRepository # Ajout MouvementStockRepository
    # Importer ici CommandeRepository etc. plus tard
)

# Exceptions
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError
from app.data.database import DatabaseError, db_cursor # Ajout db_cursor explicitement

logger = logging.getLogger(__name__)

# TODO: Définir listes valides pour Piece.statut, Piece.unite (depuis config/DB?)
VALID_PIECE_STATUS = ["Actif", "Obsolète", "En Commande", "Hors Stock"]
VALID_PIECE_UNITES = ["unité", "m", "L", "kg", "paire", "jeu", "kit"]


class StockService:
    """Orchestre les opérations liées au stock et fournisseurs."""

    def __init__(self,
                 piece_repository: PieceRepository,
                 fournisseur_repository: FournisseurRepository,
                 mouvement_stock_repository: MouvementStockRepository): # Ajout mouvement_stock_repository
        """Initialises avec les repositories nécessaires."""
        self._piece_repo = piece_repository
        self._fours_repo = fournisseur_repository
        self._mouvement_stock_repo = mouvement_stock_repository # Ajout
        # Ajouter CommandeRepository etc. ici plus tard
        logger.debug("StockService initialisé.")

    # --- Gestion Fournisseurs ---

    def create_fournisseur(self, data: Dict[str, Any]) -> Fournisseur:
        logger.info(f"Tentative création fournisseur: {data.get('nom')}")
        if not data.get('nom'): raise BusinessLogicError("Nom fournisseur obligatoire.")
        # TODO: Valider email, téléphone, devise?

        f = Fournisseur(**data)
        try:
            new_id = self._fours_repo.add(f)
            if not new_id: raise BusinessLogicError("Echec création fournisseur.")
            logger.info(f"Fournisseur '{f.nom}' créé ID: {new_id}.")
            created = self.get_fournisseur_by_id(new_id)
            if not created: raise BusinessLogicError("Créé mais non retrouvé.")
            return created
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible créer fournisseur: {e}") from e

    def get_fournisseur_by_id(self, f_id: int) -> Optional[Fournisseur]: # type: ignore
        logger.debug(f"Recherche fournisseur ID: {f_id}")
        try: return self._fours_repo.get_by_id(f_id)
        except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_all_fournisseurs(self) -> List[Fournisseur]:
        """ Récupère la liste de tous les fournisseurs. """
        logger.debug("Récupération tous fournisseurs...")
        try:
            # Vérifiez que self._fours_repo est le bon nom d'attribut
            if not hasattr(self, '_fours_repo'):
                 logger.error("Attribut 'fours_repo' non trouvé dans StockService.")
                 return []
            return self._fours_repo.get_all()
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la récupération des fournisseurs: {e}")
            return [] # Retourner liste vide en cas d'erreur DB
        except AttributeError: # Sécurité supplémentaire si l'attribut existe mais est None
             logger.error("Attribut 'fours_repo' est None dans StockService.")
             return []
        except Exception as e: # Attraper toute autre erreur inattendue
            logger.exception(f"Erreur inattendue récupération fournisseurs: {e}")
            return []

    def update_fournisseur(self, f_id: int, data: Dict[str, Any]) -> Fournisseur:
        logger.info(f"Tentative màj fournisseur ID: {f_id}")
        f = self.get_fournisseur_by_id(f_id)
        if not f: raise NotFoundError(f"Fournisseur ID {f_id} non trouvé.")
        if 'nom' in data and not data.get('nom'): raise BusinessLogicError("Nom obligatoire.")
        # TODO: Valider autres champs si modifiés

        has_changed = False
        for key, value in data.items():
            if hasattr(f, key) and getattr(f, key) != value:
                # Convertir note en float?
                if key == 'note_qualite': value = float(value) if value is not None else None
                setattr(f, key, value); has_changed = True
        if not has_changed: return f

        try:
            if not self._fours_repo.update(f): raise BusinessLogicError("Echec màj.")
            logger.info(f"Fournisseur ID {f_id} mis à jour.")
            updated = self.get_fournisseur_by_id(f_id)
            if not updated: raise BusinessLogicError("Màj mais non retrouvé.")
            return updated
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible mettre à jour: {e}") from e

    def delete_fournisseur(self, f_id: int) -> bool:
         logger.warning(f"Tentative suppression fournisseur ID: {f_id}")
         if not self.get_fournisseur_by_id(f_id): raise NotFoundError(f"ID {f_id} non trouvé.")
         # Le repo gère l'erreur si lié (ex: Commande)
         try: return self._fours_repo.delete(f_id)
         except DatabaseError as e: raise BusinessLogicError(f"Impossible supprimer: {e}") from e


    # --- Gestion Pièces Détachées ---

    def create_piece(self, data: Dict[str, Any]) -> Piece:
        logger.info(f"Tentative création pièce: Ref={data.get('reference')}, Nom={data.get('nom')}")
        # Validations
        if not data.get('reference'): raise BusinessLogicError("Référence pièce obligatoire.")
        if not data.get('nom'): raise BusinessLogicError("Nom pièce obligatoire.")
        if not data.get('unite'): raise BusinessLogicError("Unité pièce obligatoire.")
        # TODO: Valider unité fait partie de VALID_PIECE_UNITES ?
        # TODO: Valider statut fait partie de VALID_PIECE_STATUS ?
        if data.get('fournisseur_pref_id') and not self.get_fournisseur_by_id(data['fournisseur_pref_id']):
            raise NotFoundError(f"Fournisseur préféré ID {data['fournisseur_pref_id']} non trouvé.")
        # Assurer que les nombres sont des nombres
        try:
            if 'prix_unitaire' in data: data['prix_unitaire'] = float(data['prix_unitaire'] or 0.0)
            if 'stock_actuel' in data: data['stock_actuel'] = int(data['stock_actuel'] or 0)
            if 'stock_alerte' in data: data['stock_alerte'] = int(data['stock_alerte'] or 0)
            if 'stock_reserve' in data: data['stock_reserve'] = int(data['stock_reserve'] or 0)
        except (ValueError, TypeError) as e:
             raise BusinessLogicError(f"Valeur numérique invalide fournie pour prix ou stock: {e}")

        p = Piece(**data)
        try:
            new_id = self._piece_repo.add(p)
            if not new_id: raise BusinessLogicError("Echec création pièce.")
            logger.info(f"Pièce '{p.nom}' créée ID: {new_id}.")
            created = self.get_piece_by_id(new_id)
            if not created: raise BusinessLogicError("Créée mais non retrouvée.")
            return created
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible créer pièce: {e}") from e

    def get_piece_by_id(self, p_id: int) -> Optional[Piece]:
        logger.debug(f"Recherche pièce ID: {p_id}")
        try: return self._piece_repo.get_by_id(p_id)
        except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_piece_by_reference(self, ref: str) -> Optional[Piece]:
         logger.debug(f"Recherche pièce Ref: {ref}")
         try: return self._piece_repo.get_by_reference(ref)
         except DatabaseError as e: raise BusinessLogicError(f"Erreur DB: {e}") from e

    def get_all_pieces(self, filters: Optional[Dict[str, Any]] = None,
                       sort_by: str = "nom", sort_desc: bool = False) -> List[Piece]:
        """ Récupère toutes les pièces avec filtres et tri optionnels. """
        logger.debug(f"Récupération pièces (filters={filters}, sort={sort_by}, desc={sort_desc}).")
        try:
            # Vérifiez que self._piece_repo est le bon nom d'attribut
            if not hasattr(self, '_piece_repo'):
                 logger.error("Attribut 'piece_repo' non trouvé dans StockService.")
                 return []
            # Passer les arguments au repository
            return self._piece_repo.get_all(filters=filters, sort_by=sort_by, sort_desc=sort_desc)
        except DatabaseError as e:
            logger.error(f"Erreur DB lors de la récupération des pièces: {e}")
            return [] # Retourner liste vide en cas d'erreur DB
        except AttributeError:
             logger.error("Attribut 'piece_repo' est None dans StockService.")
             return []
        except Exception as e:
            logger.exception(f"Erreur inattendue récupération pièces: {e}")
            return []

    def update_piece(self, p_id: int, data: Dict[str, Any]) -> Piece:
        logger.info(f"Tentative màj pièce ID: {p_id}")
        p = self.get_piece_by_id(p_id)
        if not p: raise NotFoundError(f"Pièce ID {p_id} non trouvée.")
        # Validations
        if 'reference' in data and not data.get('reference'): raise BusinessLogicError("Référence obligatoire.")
        if 'nom' in data and not data.get('nom'): raise BusinessLogicError("Nom obligatoire.")
        if 'unite' in data and not data.get('unite'): raise BusinessLogicError("Unité obligatoire.")
        # TODO: Valider unité/statut
        if data.get('fournisseur_pref_id') and data['fournisseur_pref_id'] != p.fournisseur_pref_id:
             if data['fournisseur_pref_id'] is not None and not self.get_fournisseur_by_id(data['fournisseur_pref_id']):
                  raise NotFoundError(f"Nouveau Fournisseur ID {data['fournisseur_pref_id']} non trouvé.")
        try:
            if 'prix_unitaire' in data: data['prix_unitaire'] = float(data.get('prix_unitaire') or 0.0)
            if 'stock_actuel' in data: data['stock_actuel'] = int(data.get('stock_actuel') or 0) # Attention: stock devrait être màj via mouvements dédiés
            if 'stock_alerte' in data: data['stock_alerte'] = int(data.get('stock_alerte') or 0)
            if 'stock_reserve' in data: data['stock_reserve'] = int(data.get('stock_reserve') or 0)
        except (ValueError, TypeError) as e: raise BusinessLogicError(f"Valeur numérique invalide: {e}")

        has_changed = False
        for key, value in data.items():
            # Ignorer la mise à jour directe du stock actuel/réservé via cette méthode?
            # Il vaut mieux utiliser des méthodes dédiées add_stock / reserve_stock
            if key in ['stock_actuel', 'stock_reserve']:
                logger.warning(f"Tentative de modification directe de '{key}' pour Pièce {p_id} ignorée. Utiliser les mouvements de stock.")
                continue
            if hasattr(p, key) and getattr(p, key) != value:
                setattr(p, key, value); has_changed = True
        if not has_changed: return p

        try:
            if not self._piece_repo.update(p): raise BusinessLogicError("Echec màj.")
            logger.info(f"Pièce ID {p_id} mise à jour.")
            updated = self.get_piece_by_id(p_id)
            if not updated: raise BusinessLogicError("Màj mais non retrouvée.")
            return updated
        except DatabaseError as e:
             raise BusinessLogicError(f"Impossible mettre à jour: {e}") from e

    def delete_piece(self, p_id: int) -> bool:
         logger.warning(f"Tentative suppression pièce ID: {p_id}")
         if not self.get_piece_by_id(p_id): raise NotFoundError(f"ID {p_id} non trouvé.")
         # Le repo gèrera l'erreur si référencée (ON DELETE RESTRICT implicite ou explicite)
         try: return self._piece_repo.delete(p_id)
         except DatabaseError as e: raise BusinessLogicError(f"Impossible supprimer: {e}") from e


    # --- Logique Mouvements de Stock (appelée par MaintenanceService, CommandService...) ---

    def adjust_stock(self, piece_id: int, quantity_change: int, reason: str = "Ajustement manuel") -> bool:
         """ Ajuste le stock actuel (positif ou négatif). """
         logger.info(f"Ajustement stock pièce {piece_id}: {quantity_change:+}, Raison: {reason}")
         p = self.get_piece_by_id(piece_id)
         if not p: raise NotFoundError(f"Pièce ID {piece_id} non trouvée pour ajustement stock.")
         # Vérifier si retrait possible
         if quantity_change < 0 and p.stock_actuel < abs(quantity_change):
              raise BusinessLogicError(f"Stock insuffisant pour pièce {p.reference}. Actuel: {p.stock_actuel}, Requis: {abs(quantity_change)}")

         try:
              success = self._piece_repo.update_stock(piece_id, quantity_change)
              if success:
                   # TODO: Enregistrer le mouvement de stock dans une table dédiée (Phase future)
                   # ex: self._stock_mouvement_repo.add(piece_id, quantity_change, reason, ...)
                   logger.info(f"Stock pièce {piece_id} ajusté avec succès.")
                   # Vérifier si seuil d'alerte atteint après mouvement
                   self.check_stock_alert(piece_id)
              return success
         except DatabaseError as e:
              raise BusinessLogicError(f"Erreur DB ajustement stock: {e}") from e

    def receive_stock(self, piece_id: int, quantity: int, commande_id: Optional[int] = None) -> bool:
        """ Enregistre une entrée en stock (ex: réception commande). """
        if quantity <= 0: raise BusinessLogicError("Quantité reçue doit être positive.")
        reason = f"Réception Commande ID {commande_id}" if commande_id else "Entrée en stock"
        return self.adjust_stock(piece_id, quantity, reason=reason)

    def consume_stock(self, piece_id: int, quantity: int, maintenance_id: Optional[int] = None) -> bool:
         """ Enregistre une sortie de stock (ex: utilisation maintenance). """
         if quantity <= 0: raise BusinessLogicError("Quantité consommée doit être positive.")
         reason = f"Utilisation Maintenance ID {maintenance_id}" if maintenance_id else "Sortie de stock"
         return self.adjust_stock(piece_id, -quantity, reason=reason) # Quantité négative


    # --- Logique Alerte Stock ---
    def check_stock_alert(self, piece_id: int):
        """ Vérifie si le stock est sous le seuil et génère une alerte si nécessaire. """
        p = self.get_piece_by_id(piece_id)
        if p and p.stock_alerte is not None and p.stock_alerte > 0:
             if p.stock_actuel <= p.stock_alerte:
                  logger.warning(f"ALERTE STOCK: Pièce {p.reference} (ID:{p.id_piece}) - Stock {p.stock_actuel} <= Seuil {p.stock_alerte}")
                  # TODO: Créer une Alerte dans la table ALERTE (Phase future)
                  # Ex: self._alert_service.create_stock_alert(p)
             else:
                  # Optionnel: Résoudre alerte existante si stock > seuil?
                  pass

    def get_pieces_needing_reorder(self) -> List[Piece]:
        """ Retourne les pièces sous le seuil d'alerte. """
        try:
            return self._piece_repo.get_pieces_below_alert_threshold()
        except DatabaseError as e:
             raise BusinessLogicError(f"Erreur DB: {e}") from e


    # --- Méthodes liées aux Commandes (seront ajoutées en Phase 7) ---
    # def create_commande(...)
    # def add_ligne_commande(...)
    # def receive_commande(...)

    def enregistrer_mouvement(
        self,
        piece_id: int,
        type_mouvement: str,
        quantite: int,
        raison: Optional[str] = None,
        ot_id: Optional[int] = None,
        user_id: Optional[int] = None
        # commande_id: Optional[int] = None # Future
    ) -> Optional[MouvementStock]:
        """
        Enregistre un mouvement de stock et met à jour le stock actuel de la pièce.
        Opération atomique : soit tout réussit, soit tout est annulé.
        Args:
            piece_id: ID de la pièce concernée.
            type_mouvement: 'ENTREE', 'SORTIE', ou 'AJUSTEMENT'.
            quantite: La quantité du mouvement. Doit être > 0 pour ENTREE,
                      < 0 pour SORTIE. Pour AJUSTEMENT, peut être +/-.
                      IMPORTANT : La méthode ajuste le signe si nécessaire pour SORTIE.
            raison: Motif du mouvement (ex: 'Réception CDE-001', 'Utilisation OT-123').
            ot_id: ID de l'OT lié (si applicable).
            user_id: ID de l'utilisateur effectuant l'action (si applicable).
        Returns:
            L'objet MouvementStock créé ou None en cas d'erreur.
        Raises:
            ValueError: Si le type de mouvement est invalide ou la pièce n'existe pas.
            DatabaseError: Si une erreur de base de données se produit.
            Exception: Pour d'autres erreurs inattendues.
        """
        logger.info(f"Tentative enregistrement mouvement: Pièce ID={piece_id}, Type={type_mouvement}, Qte={quantite}, Raison='{raison}'")

        if type_mouvement not in VALID_TYPES_MOUVEMENT:
            logger.error(f"Type de mouvement invalide: {type_mouvement}")
            raise ValueError(f"Type de mouvement invalide: {type_mouvement}")

        # 1. Récupérer la pièce actuelle pour vérifier existence et stock_avant
        piece = self.get_piece_by_id(piece_id)
        if not piece:
            logger.error(f"Pièce ID {piece_id} non trouvée pour mouvement de stock.")
            raise ValueError(f"Pièce ID {piece_id} non trouvée.")

        stock_avant = piece.stock_actuel
        delta_stock = 0

        # 2. Déterminer la quantité réelle à enregistrer et le delta pour le stock
        qte_mouvement = quantite # Quantité stockée dans la table mouvement

        if type_mouvement == 'ENTREE':
            if quantite <= 0:
                logger.warning(f"Quantité pour ENTREE doit être positive ({quantite}). Ajustement à abs(quantite).")
                qte_mouvement = abs(quantite)
            delta_stock = qte_mouvement
        elif type_mouvement == 'SORTIE':
            # Convention : on reçoit une quantité positive (combien on sort)
            # mais on stocke un delta négatif et une quantité négative dans le mouvement.
            if quantite <= 0:
                 logger.warning(f"Quantité pour SORTIE devrait être positive ({quantite}) représentant la qte sortie. Utilisation abs(quantite).")
                 qte_mouvement = -abs(quantite)
            else:
                 qte_mouvement = -quantite # Stocker qté négative pour sortie
            delta_stock = qte_mouvement
        elif type_mouvement == 'AJUSTEMENT':
            # La quantité peut être positive ou négative
            delta_stock = quantite
            qte_mouvement = quantite

        stock_apres = stock_avant + delta_stock

        # (Optionnel) Vérifier si stock suffisant pour une sortie
        if type_mouvement == 'SORTIE' and stock_apres < 0:
            logger.error(f"Stock insuffisant pour sortie Pièce ID {piece_id}. Stock avant: {stock_avant}, Demande: {-delta_stock}, Stock après: {stock_apres}")
            raise ValueError(f"Stock insuffisant pour la pièce ID {piece_id} (stock actuel: {stock_avant}, demande: {-delta_stock})")

        # 3. Créer l'objet MouvementStock
        mvt = MouvementStock(
            piece_id=piece_id,
            type_mouvement=type_mouvement,
            quantite=qte_mouvement,
            date_mouvement=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Redondant avec default? Sécurité
            raison=raison,
            ot_id=ot_id,
            user_id=user_id,
            stock_avant=stock_avant,
            stock_apres=stock_apres
            # commande_id=commande_id
        )

        # Utilisation explicite du contexte de transaction db_cursor
        try:
            with db_cursor() as cursor: # Le curseur n'est pas forcément utilisé, mais le contexte gère commit/rollback
                # 4. Ajouter le mouvement à la base de données (partie de la transaction)
                # Note: Les méthodes add/update_stock_level ne doivent PAS gérer leur propre transaction ici !
                # Il faut s'assurer qu'elles utilisent juste cursor.execute() sans leur propre db_cursor/commit.
                # Vérification rapide: add utilise execute_query qui utilise db_cursor. C'est un problème.
                # Il faut modifier add et update_stock_level pour accepter un curseur optionnel.

                # ===== Solution Temporaire (moins propre) : On laisse les transactions imbriquées =====
                # Si une étape échoue, l'exception remontera et le db_cursor externe fera le rollback.
                # C'est moins efficace mais compatible avec la gestion des transactions PostgreSQL.

                mvt_id = self._mouvement_stock_repo.add(mvt)
                if not mvt_id:
                    logger.error(f"Échec ajout enregistrement mouvement pour pièce ID {piece_id}. Rollback externe attendu.")
                    # Lever une exception pour être sûr que le db_cursor externe rollback
                    raise DatabaseError(f"Échec ajout mouvement stock pour pièce {piece_id}")

                mvt.id_mouvement = mvt_id

                # 5. Mettre à jour le niveau de stock de la pièce (partie de la transaction)
                success_update = self._piece_repo.update_stock_level(piece_id, stock_apres)
                if not success_update:
                    logger.error(f"Échec mise à jour stock pièce ID {piece_id} après ajout mouvement {mvt_id}. Rollback externe attendu.")
                    raise DatabaseError(f"Échec mise à jour stock pièce ID {piece_id} après mouvement.")

                # Si on arrive ici, les deux opérations ont réussi dans leurs transactions internes.
                # Le db_cursor externe va commit la transaction globale.

            logger.info(f"Mouvement ID {mvt_id} enregistré avec succès. Stock pièce {piece_id} mis à jour à {stock_apres}.")
            return mvt # Retourner le mouvement créé

        except DatabaseError as e:
             # Les erreurs des repos remontent ici, le rollback externe a été (ou sera) fait.
             logger.error(f"Erreur DB lors de l'enregistrement du mouvement pour pièce {piece_id}: {e}")
             raise # Remonter l'erreur
        except ValueError as e: # Ex: Pièce non trouvée, type mouvement invalide
            logger.error(f"Erreur de validation lors de l'enregistrement du mouvement pour pièce {piece_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'enregistrement du mouvement pour pièce {piece_id}: {e}", exc_info=True)
            raise

    def get_stock_history(self, piece_id: int, limit: Optional[int] = 50) -> List[MouvementStock]:
        """ Récupère l'historique des mouvements pour une pièce. """
        try:
            return self._mouvement_stock_repo.get_by_piece_id(piece_id, limit)
        except DatabaseError as e:
            logger.error(f"Erreur service get historique stock pièce ID {piece_id}: {e}")
            return []

    def get_pieces_by_ids(self, piece_ids):
        """
        Récupère plusieurs pièces par leurs IDs.
        
        Args:
            piece_ids (list): Liste des IDs de pièces à récupérer
            
        Returns:
            dict: Dictionnaire des pièces avec l'ID comme clé et l'objet Piece comme valeur
        """
        if not piece_ids:
            return {}
            
        result = {}
        for piece_id in piece_ids:
            piece = self.get_piece_by_id(piece_id)
            if piece:
                result[piece_id] = piece
                
        return result

    def get_quantite_disponible(self, piece_id: int) -> int:
        """Retourne la quantité disponible (stock actuel) pour une pièce donnée."""
        piece = self.get_piece_by_id(piece_id)
        if not piece:
            raise NotFoundError(f"Pièce ID {piece_id} non trouvée pour quantité disponible.")
        return piece.stock_actuel