# gmao_app/app/core/services/achat_service.py
""" Service pour la gestion des Commandes d'Achat et des Réceptions. """
import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any

# Import des modèles et repositories nécessaires
from app.core.models.commande import Commande
from app.core.models.ligne_commande import LigneCommande
from app.core.models.utilisateur import Utilisateur
from app.core.models.mouvement_stock import MouvementStock # Important pour tracer
from app.data.repositories.commande_repository import CommandeRepository
from app.data.repositories.ligne_commande_repository import LigneCommandeRepository
from app.data.repositories.piece_repository import PieceRepository
from app.data.repositories.mouvement_stock_repository import MouvementStockRepository
from app.utils.exceptions import GmaoPermissionError, DatabaseError, BusinessLogicError


# Optionnel: Repos pour validation FK (si non géré uniquement par DB)
from app.data.repositories.fournisseur_repository import FournisseurRepository
from app.data.repositories.user_repository import UserRepository

from app.data.database import DatabaseError # Pour remonter les erreurs DB

logger = logging.getLogger(__name__)

class AchatService:
    """ Gère la logique métier liée aux commandes d'achat et aux réceptions. """

    def __init__(self,
                 commande_repo: CommandeRepository,
                 ligne_commande_repo: LigneCommandeRepository,
                 piece_repo: PieceRepository,
                 mouvement_stock_repo: MouvementStockRepository):
                 # fournisseur_repo: FournisseurRepository, # Optionnel
                 # user_repo: UserRepository):              # Optionnel
        """ Initialise le service avec les repositories requis. """
        self.commande_repo = commande_repo
        self.ligne_commande_repo = ligne_commande_repo
        self.piece_repo = piece_repo
        self.mouvement_stock_repo = mouvement_stock_repo
        # self.fournisseur_repo = fournisseur_repo # Optionnel
        # self.user_repo = user_repo             # Optionnel
        logger.info("AchatService initialisé.")

    # --- Gestion des Commandes ---

    def create_commande(self, commande_data: Dict[str, Any], createur_id: int, createur_role: str) -> Optional[Commande]:
        """
        Crée une nouvelle commande d'achat.
        Args:
            commande_data: Dictionnaire contenant les données de base de la commande
                           (numero_commande, fournisseur_id, date_commande, etc.).
            createur_id: ID de l'utilisateur créant la commande.
        Returns:
            L'objet Commande créé avec son ID, ou None si erreur.
        Raises:
            DatabaseError: Si une contrainte DB est violée (ex: FK invalide).
            ValueError: Si des données nécessaires sont manquantes ou invalides.
        """

         # --- Vérification de Permission ---
        allowed_roles = ['Admin', 'GestionStock'] # Rôles autorisés à créer
        if createur_role not in allowed_roles:
            logger.warning(f"Tentative non autorisée de création commande par utilisateur ID {createur_id} (rôle {createur_role})")
            raise GmaoPermissionError("Vous n'avez pas les droits suffisants pour créer une commande.")
        # ----------------------------------

        logger.info(f"Création commande demandée par utilisateur ID {createur_id} (rôle {createur_role})")
        try:
            # Validation minimale (peut être étendue)
            if not all(k in commande_data for k in ['fournisseur_id', 'date_commande']):
                 raise ValueError("ID Fournisseur et Date de commande sont requis.")

            # Préparation de l'objet Commande
            commande = Commande(
                numero_commande=commande_data.get('numero_commande'), # Peut être généré plus tard si None
                fournisseur_id=int(commande_data['fournisseur_id']),
                utilisateur_createur_id=createur_id,
                date_commande=commande_data['date_commande'], # Devrait déjà être un objet date
                date_livraison_prevue=commande_data.get('date_livraison_prevue'), # objet date ou None
                statut=commande_data.get('statut', 'Brouillon'), # Défaut 'Brouillon'
                frais_port=float(commande_data.get('frais_port', 0.0)),
                reference_fournisseur=commande_data.get('reference_fournisseur'),
                mode_paiement=commande_data.get('mode_paiement'),
                notes_commande=commande_data.get('notes_commande'),
                # total_ht sera calculé/mis à jour par les lignes
            )

            # TODO: Optionnel - Valider existence fournisseur_id et createur_id via leurs repos ici

            new_id = self.commande_repo.add(commande)
            if new_id:
                commande.id_commande = new_id
                # Si numero_commande n'était pas fourni, on pourrait le générer ici et faire un update
                # ex: commande.numero_commande = f"CMD-{datetime.now().year}-{new_id:05d}"
                #     self.commande_repo.update(commande)
                logger.info(f"Nouvelle commande créée ID: {new_id}")
                return commande
            else:
                 logger.error("Erreur lors de la création de la commande, ID non retourné.")
                 return None
        except (DatabaseError, ValueError) as e:
             logger.error(f"Erreur création commande: {e}")
             raise # Remonter l'erreur pour l'UI
        except Exception as e:
             logger.exception(f"Erreur inattendue lors de la création de commande: {e}")
             raise DatabaseError("Erreur serveur lors de la création de la commande.") from e


    def get_commande_details(self, commande_id: int) -> Optional[Dict[str, Any]]:
         """ Récupère une commande et ses lignes enrichies (avec infos pièce). """
         try:
             commande = self.commande_repo.get_by_id(commande_id) # Repo commande retourne l'objet direct
             if not commande:
                 return None

             # Récupérer les lignes brutes enrichies du repo ligne
             rows_lignes = self.ligne_commande_repo.get_by_commande_id(commande_id)
             # Convertir en objets LigneCommande enrichis
             lignes_enrichies = [LigneCommande.from_db_row(row) for row in rows_lignes if row]
             lignes_valides = [l for l in lignes_enrichies if l is not None]

             # Récupérer nom fournisseur pour l'objet commande (si pas déjà fait)
             # Si Commande.from_db_row ne le fait pas déjà via get_by_id
             if commande.nom_fournisseur is None and commande.fournisseur_id:
                  # Ajouter une méthode get_fournisseur_nom(id) à StockService ou AchatService?
                  # Ou modifier CommandeRepository.get_by_id pour faire le JOIN?
                  # Pour l'instant, on laisse nom_fournisseur potentiellement None ici.
                  pass

             return {"commande": commande, "lignes": lignes_valides}
         except Exception as e:
              logger.exception(f"Erreur récupération détails commande ID {commande_id}: {e}")
              return None # Ou lever ? Pour l'UI, None est souvent gérable.

    def get_all_commandes(self, filters: Optional[Dict[str, Any]] = None,
                           sort_by: str = "date_commande", sort_desc: bool = True) -> List[Commande]:
        """ Récupère la liste des commandes (objets Commande) selon filtres/tri. """
        try:
             # 1. Récupérer les lignes brutes (incluant nom fournisseur) depuis le repo
             rows = self.commande_repo.get_all(filters=filters, sort_by=sort_by, sort_desc=sort_desc)

             # 2. Convertir chaque ligne en objet Commande via la méthode from_db_row
             commandes = [Commande.from_db_row(row) for row in rows if row]

             # 3. Filtrer les éventuels None si from_db_row a échoué pour une ligne
             commandes_valides = [cmd for cmd in commandes if cmd is not None]

             logger.debug(f"{len(commandes_valides)} objets Commande retournés par le service.")
             return commandes_valides

        except DatabaseError as e:
             logger.error(f"Erreur service get toutes commandes: {e}")
             return [] # Retourner liste vide en cas d'erreur DB
        except Exception as e:
            logger.exception(f"Erreur inattendue dans get_all_commandes service: {e}")
            return []

    def update_commande(self, commande: Commande, current_user: Utilisateur) -> bool: # Ajouter current_user
        """ Met à jour l'en-tête d'une commande existante, avec vérification des droits. """
        if not commande.id_commande:
             logger.error("Tentative de màj commande sans ID.")
             # Lever une erreur est peut-être mieux que juste retourner False
             raise ValueError("ID de commande manquant pour la mise à jour.")

        # --- Vérification de Permission ---
        # Uniquement si commande est 'Brouillon' ? Ou certains champs modifiables par d'autres rôles?
        # Exemple simple : seuls Admin/GestionStock peuvent modifier un Brouillon
        allowed_roles_edit = ['Admin', 'GestionStock']
        can_edit = False
        if commande.statut == 'Brouillon' and current_user.role in allowed_roles_edit:
             can_edit = True
        # Ajouter d'autres conditions si nécessaire (ex: un admin peut modifier même si 'Envoyee'?)

        if not can_edit:
            logger.warning(f"Tentative non autorisée de modification commande ID {commande.id_commande} (statut: {commande.statut}) par {current_user.login} (rôle: {current_user.role}).")
            raise GmaoPermissionError(f"Vous ne pouvez pas modifier cette commande (statut: {commande.statut}).")
        # ----------------------------------

        logger.info(f"Mise à jour commande ID {commande.id_commande} demandée par {current_user.login}...")
        try:
            # TODO: Ajouter validation métier si nécessaire avant update DB
            # (ex: vérifier que le nouveau fournisseur existe, etc.)

            success = self.commande_repo.update(commande) # Appel au repository
            if success:
                 logger.info(f"En-tête commande ID {commande.id_commande} mis à jour avec succès.")
                 # Recalculer total après màj (au cas où frais port changent?)
                 self._update_commande_total_ht(commande.id_commande)
            else:
                 # Le repo devrait logguer si rowcount == 0
                 logger.warning(f"La mise à jour DB n'a affecté aucune ligne pour commande ID {commande.id_commande}.")
                 # Retourner False ici, ce n'est pas une exception critique
            return success

        except (DatabaseError, ValueError) as e: # Attraper aussi ValueError si validation ajoutée
             logger.error(f"Erreur DB/Validation màj commande ID {commande.id_commande}: {e}")
             raise # Remonter pour l'UI
        except Exception as e:
              logger.exception(f"Erreur inattendue màj commande ID {commande.id_commande}: {e}")
              raise DatabaseError(f"Erreur serveur màj commande {commande.id_commande}") from e

    # ... (autres méthodes : add_ligne, update_ligne, remove_ligne, _update_commande_total_ht, etc.) ...

    def update_commande_statut(self, commande_id: int, new_statut: str) -> bool:
         """ Met à jour le statut d'une commande. """
         # TODO: Ajouter logique de validation si nécessaire (ex: ne peut pas passer de Livree à Brouillon)
         allowed_statuses = ['Brouillon', 'Validee', 'Envoyee', 'Partielle', 'Livree', 'Annulee']
         if new_statut not in allowed_statuses:
             logger.warning(f"Tentative de mise à jour vers un statut invalide '{new_statut}' pour commande ID {commande_id}")
             return False

         try:
             return self.commande_repo.update_statut(commande_id, new_statut)
         except DatabaseError as e:
              logger.error(f"Erreur DB màj statut commande ID {commande_id}: {e}")
              raise


    def delete_commande(self, commande_id: int) -> bool:
         """ Supprime une commande et ses lignes. """
         # TODO: Ajouter validation (ex: ne peut supprimer que si statut 'Brouillon' ou 'Annulee'?)
         commande = self.commande_repo.get_by_id(commande_id)
         if not commande: return False
         # if commande.statut not in ['Brouillon', 'Annulee']:
         #    logger.warning(f"Tentative de suppression commande ID {commande_id} avec statut {commande.statut}.")
         #    return False
         try:
             # La suppression des lignes est gérée par ON DELETE CASCADE
             return self.commande_repo.delete(commande_id)
         except DatabaseError as e:
             logger.error(f"Erreur DB suppression commande ID {commande_id}: {e}")
             raise


    # --- Gestion des Lignes de Commande ---

    def add_ligne_commande(self, ligne_data: Dict[str, Any]) -> Optional[LigneCommande]:
         """
         Ajoute une ligne à une commande existante.
         Args:
             ligne_data: Dictionnaire contenant les données de la ligne
                         (commande_id, piece_id, quantite_commandee, prix_unitaire_ht, etc.).
         Returns:
             L'objet LigneCommande créé avec son ID, ou None si erreur.
         Raises:
             DatabaseError, ValueError
         """
         try:
             # Validation
             if not all(k in ligne_data for k in ['commande_id', 'piece_id', 'quantite_commandee', 'prix_unitaire_ht']):
                 raise ValueError("commande_id, piece_id, quantite_commandee, prix_unitaire_ht sont requis.")

             commande_id = int(ligne_data['commande_id'])
             # Vérifier que la commande parente existe et est modifiable (ex: 'Brouillon')
             commande = self.commande_repo.get_by_id(commande_id)
             if not commande:
                  raise ValueError(f"Commande ID {commande_id} non trouvée.")
             if commande.statut != 'Brouillon':
                  raise ValueError(f"Impossible d'ajouter une ligne à la commande ID {commande_id} (statut: {commande.statut}).")

             # TODO: Optionnel - Valider existence piece_id

             ligne = LigneCommande(
                 commande_id=commande_id,
                 piece_id=int(ligne_data['piece_id']),
                 quantite_commandee=int(ligne_data['quantite_commandee']),
                 prix_unitaire_ht=float(ligne_data['prix_unitaire_ht']),
                 description_libre=ligne_data.get('description_libre'),
                 statut_ligne=ligne_data.get('statut_ligne', 'Attente') # Défaut
                 # quantite_recue commence à 0 par défaut dans le modèle
             )
             if ligne.quantite_commandee <= 0:
                 raise ValueError("La quantité commandée doit être positive.")
             if ligne.prix_unitaire_ht < 0:
                 raise ValueError("Le prix unitaire ne peut pas être négatif.")


             new_id = self.ligne_commande_repo.add(ligne)
             if new_id:
                 ligne.id_ligne = new_id
                 logger.info(f"Nouvelle ligne ID {new_id} ajoutée à commande ID {commande_id}")
                 # Recalculer le total de la commande après ajout
                 self._update_commande_total_ht(commande_id)
                 return ligne
             else:
                  logger.error("Erreur ajout ligne, ID non retourné.")
                  return None
         except (DatabaseError, ValueError) as e:
              logger.error(f"Erreur ajout ligne à commande ID {ligne_data.get('commande_id', 'N/A')}: {e}")
              raise
         except Exception as e:
              logger.exception(f"Erreur inattendue ajout ligne commande: {e}")
              raise DatabaseError("Erreur serveur lors ajout ligne commande.") from e

    def update_ligne_commande(self, ligne_id: int, update_data: Dict[str, Any]) -> Optional[LigneCommande]:
        """ Met à jour les données d'une ligne de commande. """
        ligne = self.ligne_commande_repo.get_by_id(ligne_id)
        if not ligne:
            raise ValueError(f"Ligne de commande ID {ligne_id} non trouvée.")

        commande = self.commande_repo.get_by_id(ligne.commande_id)
        if not commande or commande.statut != 'Brouillon':
             raise ValueError(f"Impossible de modifier la ligne ID {ligne_id} (commande statut: {commande.statut if commande else 'inconnue'}).")

        # Mettre à jour les champs modifiables
        updated = False
        if 'quantite_commandee' in update_data:
            new_qty = int(update_data['quantite_commandee'])
            if new_qty <= 0: raise ValueError("Quantité commandée doit être positive.")
            ligne.quantite_commandee = new_qty
            updated = True
        if 'prix_unitaire_ht' in update_data:
            new_price = float(update_data['prix_unitaire_ht'])
            if new_price < 0: raise ValueError("Prix unitaire ne peut être négatif.")
            ligne.prix_unitaire_ht = new_price
            updated = True
        if 'description_libre' in update_data:
            ligne.description_libre = update_data['description_libre']
            updated = True
        # Mettre à jour d'autres champs si nécessaire (piece_id?)

        if updated:
            try:
                success = self.ligne_commande_repo.update(ligne)
                if success:
                     logger.info(f"Ligne commande ID {ligne_id} mise à jour.")
                     # Recalculer le total
                     self._update_commande_total_ht(ligne.commande_id)
                     return ligne
                else:
                     # Ne devrait pas arriver si l'ID est correct
                     logger.error(f"Échec màj DB pour ligne ID {ligne_id} bien qu'elle existe.")
                     return None
            except (DatabaseError, ValueError) as e:
                 logger.error(f"Erreur màj ligne commande ID {ligne_id}: {e}")
                 raise
        else:
            logger.debug(f"Aucune donnée modifiée pour ligne ID {ligne_id}.")
            return ligne # Retourne l'original non modifié

    def remove_ligne_commande(self, ligne_id: int) -> bool:
         """ Supprime une ligne de commande. """
         ligne = self.ligne_commande_repo.get_by_id(ligne_id)
         if not ligne: return False # Ou lever erreur?

         commande = self.commande_repo.get_by_id(ligne.commande_id)
         if not commande or commande.statut != 'Brouillon':
              logger.warning(f"Tentative suppression ligne ID {ligne_id} d'une commande non modifiable (statut: {commande.statut if commande else 'inconnue'}).")
              return False

         try:
             success = self.ligne_commande_repo.delete(ligne_id)
             if success:
                  # Recalculer le total après suppression
                  self._update_commande_total_ht(ligne.commande_id)
             return success
         except DatabaseError as e:
              logger.error(f"Erreur DB suppression ligne ID {ligne_id}: {e}")
              raise


    # --- Gestion de la Réception ---

    def receive_ligne_commande(self, ligne_id: int, quantite_recue_ajout: int, date_reception: date, utilisateur_id: Optional[int] = None) -> bool:
        """
        Enregistre la réception d'une quantité pour une ligne de commande.
        Met à jour le stock de la pièce et les statuts.
        Args:
            ligne_id: ID de la ligne de commande concernée.
            quantite_recue_ajout: Quantité *nouvellement* reçue (doit être > 0).
            date_reception: Date de cette réception.
            utilisateur_id: ID de l'utilisateur effectuant l'action (pour MouvementStock).
        Returns:
            True si la réception et les mises à jour ont réussi, False sinon.
        Raises:
             ValueError: Si données invalides ou ligne non trouvée/non recevable.
             DatabaseError: Si erreur DB.
        """
        if quantite_recue_ajout <= 0:
            raise ValueError("La quantité reçue ajoutée doit être positive.")

        # 1. Récupérer la ligne
        ligne = self.ligne_commande_repo.get_by_id(ligne_id)
        if not ligne:
            raise ValueError(f"Ligne de commande ID {ligne_id} non trouvée.")

        # 2. Vérifier si la réception est possible (statut commande, etc.)
        commande = self.commande_repo.get_by_id(ligne.commande_id)
        if not commande:
             # Ne devrait pas arriver si la ligne existe
             raise DatabaseError(f"Commande ID {ligne.commande_id} associée à ligne ID {ligne_id} non trouvée.")
        if commande.statut not in ['Envoyee', 'Partielle']:
             raise ValueError(f"Impossible de réceptionner la ligne ID {ligne_id} (commande statut: {commande.statut}).")

        # 3. Vérifier si on ne dépasse pas la quantité commandée
        new_total_recu = ligne.quantite_recue + quantite_recue_ajout
        if new_total_recu > ligne.quantite_commandee:
             raise ValueError(f"Réception impossible pour ligne ID {ligne_id}: quantité totale reçue ({new_total_recu}) dépasserait quantité commandée ({ligne.quantite_commandee}).")

        try:
            # --- Transaction implicite via les helpers DB si bien faits, sinon gérer explicitement ---
            # NOTE: Pour une robustesse maximale, toutes ces opérations devraient être dans une transaction DB

            # 4. Mettre à jour la quantité reçue et date sur la ligne
            success_ligne = self.ligne_commande_repo.update_reception(ligne_id, quantite_recue_ajout, date_reception)
            if not success_ligne:
                 # Ne devrait pas arriver si l'ID est bon
                 raise DatabaseError(f"Échec de la mise à jour de la réception pour ligne ID {ligne_id}.")

            # 5. Mettre à jour le stock de la pièce
            success_stock = self.piece_repo.update_stock(ligne.piece_id, quantite_recue_ajout)
            if not success_stock:
                # Ceci est plus probable (ex: pièce supprimée entre-temps?)
                # TODO: Que faire? Annuler la réception sur la ligne (rollback)? Logguer erreur grave?
                logger.error(f"Échec mise à jour stock pour pièce ID {ligne.piece_id} après réception ligne {ligne_id}. Transaction incomplète!")
                raise DatabaseError(f"Échec mise à jour stock pour pièce ID {ligne.piece_id}.")


            # 6. Enregistrer le mouvement de stock
            mvt = MouvementStock(
                 piece_id=ligne.piece_id,
                 type_mouvement='ENTREE',
                 quantite=quantite_recue_ajout,
                 date_mouvement=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Ou utiliser la date de réception? Préférable datetime.now() pour audit
                 raison=f"Réception Commande ID {ligne.commande_id}, Ligne ID {ligne_id}",
                 user_id=utilisateur_id
                 # stock_avant/apres pourraient être récupérés/calculés si nécessaire
            )
            mvt_id = self.mouvement_stock_repo.add(mvt)
            if not mvt_id:
                 logger.warning(f"Échec enregistrement mouvement stock pour réception ligne ID {ligne_id}. Continuer quand même...")
                 # Décision: Est-ce bloquant? Probablement pas, mais à surveiller.

            # 7. Mettre à jour le statut de la ligne
            new_statut_ligne = 'Recue' if new_total_recu == ligne.quantite_commandee else 'Partielle'
            if new_statut_ligne != ligne.statut_ligne:
                 self.ligne_commande_repo.update_ligne_statut(ligne_id, new_statut_ligne)

            # 8. Vérifier et mettre à jour le statut de la commande globale
            self._check_and_update_commande_statut(ligne.commande_id)

            # --- Fin de la "transaction" implicite ---
            logger.info(f"Réception de {quantite_recue_ajout} unités pour Ligne ID {ligne_id} terminée avec succès.")
            return True

        except (DatabaseError, ValueError) as e:
             logger.error(f"Erreur lors de la réception pour ligne ID {ligne_id}: {e}")
             # TODO: Implémenter un rollback si transaction explicite
             raise # Remonter l'erreur

        except (GmaoPermissionError, ValueError, DatabaseError, BusinessLogicError) as e: # ValueError est utilisé directement
             logger.error(f"Échec réception ligne ID {ligne_id}: {e}")
             raise # Remonter l'erreur gérée

    # --- Méthodes privées d'aide ---

    def _update_commande_total_ht(self, commande_id: int):
         """ Recalcule et met à jour le total HT de la commande basé sur ses lignes. """
         try:
             total_ht = self.commande_repo.calculate_total_ht(commande_id)
             if total_ht is not None:
                 self.commande_repo.update_total_ht(commande_id, total_ht)
                 logger.debug(f"Total HT de commande ID {commande_id} mis à jour à {total_ht:.2f}")
             else:
                 logger.warning(f"Impossible de calculer le total HT pour commande ID {commande_id}.")
         except DatabaseError as e:
              # Ne pas bloquer l'opération principale pour une erreur de calcul de total
              logger.error(f"Erreur lors de la mise à jour du total HT pour commande ID {commande_id}: {e}")

    def _check_and_update_commande_statut(self, commande_id: int):
         """ Vérifie si toutes les lignes sont reçues et met à jour le statut de la commande. """
         try:
             rows = self.ligne_commande_repo.get_by_commande_id(commande_id)
             lignes = [LigneCommande.from_db_row(row) for row in rows if row]
             if not lignes: # Si pas de lignes, la commande ne devrait pas être 'Envoyee'/'Partielle', mais vérifions
                 # self.commande_repo.update_statut(commande_id, 'Validee') # Ou autre statut?
                 return

             all_received = all(l.statut_ligne == 'Recue' for l in lignes)

             if all_received:
                 logger.info(f"Toutes les lignes de la commande ID {commande_id} sont reçues. Passage au statut 'Livree'.")
                 self.commande_repo.update_statut(commande_id, 'Livree')
             else:
                  # Si au moins une ligne est reçue (même partiellement), le statut global est 'Partielle'
                  any_received = any(l.statut_ligne in ['Partielle', 'Recue'] for l in lignes)
                  if any_received:
                       commande = self.commande_repo.get_by_id(commande_id)
                       # Mettre à jour seulement si ce n'est pas déjà 'Partielle' ou 'Livree'/'Annulee'
                       if commande and commande.statut not in ['Partielle', 'Livree', 'Annulee']:
                           logger.info(f"Au moins une ligne reçue pour commande ID {commande_id}. Passage au statut 'Partielle'.")
                           self.commande_repo.update_statut(commande_id, 'Partielle')
                  # Sinon (aucune réception du tout), on reste en 'Envoyee'
         except DatabaseError as e:
              logger.error(f"Erreur lors vérification/màj statut commande ID {commande_id} après réception ligne: {e}")
              # Ne pas bloquer

    def update_commande(self, commande: Commande, current_user: Utilisateur) -> bool:
            """ Met à jour l'en-tête d'une commande existante. """
            if not commande.id_commande:
                logger.error("Tentative de màj commande sans ID.")
                return False
            try:
                # TODO: Ajouter validation métier si nécessaire avant update DB
                # (ex: vérifier si le statut peut être changé, etc.)
                logger.debug(f"Mise à jour commande ID {commande.id_commande}...")
                success = self.commande_repo.update(commande)
                if success:
                    # Recalculer total après màj (au cas où frais port changent?)
                    self._update_commande_total_ht(commande.id_commande)
                return success
            except DatabaseError as e:
                logger.error(f"Erreur DB màj commande ID {commande.id_commande}: {e}")
                raise # Remonter pour l'UI
            except Exception as e:
                logger.exception(f"Erreur inattendue màj commande ID {commande.id_commande}: {e}")
                raise DatabaseError(f"Erreur serveur màj commande {commande.id_commande}") from e


    # --- Méthode pour infos pièce (utilisée par ReceptionDialog si Option C n'est PAS totalement implémentée) ---
    # Si Option C est bien implémentée (LigneCommande contient déjà réf/nom), cette méthode n'est plus strictement nécessaire
    # Mais gardons-la pour flexibilité ou si besoin ailleurs.
    def get_piece_info_for_reception(self, piece_id: int) -> Optional[Dict[str, str]]:
        """ Récupère la référence et le nom d'une pièce. """
        try:
                # Assurez-vous que l'attribut piece_repo existe
                if not hasattr(self, 'piece_repo'):
                    logger.error("PieceRepository non disponible dans AchatService.")
                    return None
                piece = self.piece_repo.get_by_id(piece_id)
                if piece:
                    return {'ref': piece.reference, 'nom': piece.nom}
                else:
                    logger.warning(f"Info pièce non trouvée pour ID {piece_id}")
                    return None
        except Exception as e:
            logger.error(f"Erreur récupération info pièce ID {piece_id} pour réception: {e}")
            return None

    # ... (create_commande, get_commande_details, update_commande, delete_commande, add/update/remove_ligne...) ...

    # --- Méthode de Réception ---
    def receive_ligne_commande(self, ligne_id: int, quantite_recue_ajout: int,
                                date_reception: date, current_user: Utilisateur) -> bool:
        """
        Enregistre la réception d'une quantité pour une ligne de commande.
        Met à jour le stock de la pièce, les statuts ligne/commande et enregistre un mouvement.
        Retourne True si succès, lève une exception si échec critique ou permission refusée.
        """
        logger.info(f"Tentative réception ligne ID {ligne_id} ({quantite_recue_ajout} unités) par {current_user.login}")

        # --- 1. Vérification Permissions ---
        allowed_roles = ['Admin', 'GestionStock', 'Magasinier'] # Exemple
        if current_user.role not in allowed_roles:
            logger.warning(f"Tentative non autorisée de réception ligne {ligne_id} par {current_user.login} (rôle {current_user.role})")
            raise GmaoPermissionError("Droits insuffisants pour enregistrer une réception.")

        # --- 2. Validation Entrées ---
        if quantite_recue_ajout <= 0:
            raise ValueError("La quantité reçue ajoutée doit être positive.")

        try:
            # --- 3. Récupérer Ligne et Commande ---
            ligne = self.ligne_commande_repo.get_by_id(ligne_id)
            if not ligne:
                raise ValueError(f"Ligne de commande ID {ligne_id} non trouvée.")

            commande = self.commande_repo.get_by_id(ligne.commande_id)
            if not commande:
                raise DatabaseError(f"Commande ID {ligne.commande_id} associée à ligne ID {ligne_id} non trouvée.")

            # --- 4. Vérifier Statut Commande ---
            if commande.statut not in ['Envoyee', 'Partielle']:
                    raise BusinessLogicError(f"Impossible de réceptionner: la commande (ID {commande.id_commande}) n'est pas en statut 'Envoyee' ou 'Partielle' (statut: {commande.statut}).")

            # --- 5. Vérifier Quantité ---
            new_total_recu = ligne.quantite_recue + quantite_recue_ajout
            if new_total_recu > ligne.quantite_commandee:
                    raise ValueError(f"Quantité réceptionnée ({quantite_recue_ajout}) dépasse la quantité restante ({ligne.quantite_commandee - ligne.quantite_recue}) pour ligne ID {ligne_id}.")

            # --- Début Transaction Logique (idéalement supportée par une transaction DB) ---
            # NOTE: Sans transaction DB explicite, un échec à mi-parcours peut laisser des données incohérentes.
            # Avec PostgreSQL, utiliser les transactions adéquates pour garantir la cohérence.

            # 6. Mettre à jour Stock Pièce
            logger.debug(f"Mise à jour stock pièce ID {ligne.piece_id} (+{quantite_recue_ajout})")
            success_stock = self.piece_repo.update_stock(ligne.piece_id, quantite_recue_ajout)
            if not success_stock:
                # Ceci est critique. Lever une erreur pour potentiellement annuler.
                raise DatabaseError(f"Échec critique de la mise à jour du stock pour pièce ID {ligne.piece_id} lors de la réception ligne {ligne_id}.")

            # 7. Mettre à jour Ligne de Commande (Qté reçue, date)
            logger.debug(f"Mise à jour réception ligne ID {ligne_id} (Qté: +{quantite_recue_ajout}, Date: {date_reception})")
            success_ligne_update = self.ligne_commande_repo.update_reception(ligne_id, quantite_recue_ajout, date_reception)
            if not success_ligne_update:
                    # Aussi critique. Que faire si le stock a déjà été mis à jour ?
                    logger.error(f"Échec MAJEUR: Stock pièce ID {ligne.piece_id} mis à jour mais impossible de mettre à jour la ligne commande ID {ligne_id} !")
                    # Lever une erreur indiquant l'incohérence potentielle.
                    raise DatabaseError(f"Incohérence DB: Stock mis à jour mais échec màj ligne commande {ligne_id}.")

            # 8. Enregistrer Mouvement de Stock
            try:
                    mvt = MouvementStock(
                        piece_id=ligne.piece_id, type_mouvement='ENTREE', quantite=quantite_recue_ajout,
                        date_mouvement=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        raison=f"Réception Cmd ID {ligne.commande_id}, Ligne ID {ligne_id}",
                        user_id=current_user.id_utilisateur
                    )
                    # Assurez-vous que l'attribut existe et est correct
                    if hasattr(self, 'mouvement_stock_repo'):
                        mvt_id = self.mouvement_stock_repo.add(mvt)
                        if not mvt_id: logger.warning(f"Échec enregistrement mouvement stock pour réception ligne {ligne_id}")
                    else:
                        logger.error("MouvementStockRepository non disponible dans AchatService pour tracer la réception.")

            except Exception as e_mvt:
                    # Ne pas bloquer la réception principale pour une erreur de log de mouvement? A débattre.
                    logger.exception(f"Erreur lors de l'enregistrement du mouvement de stock pour ligne {ligne_id}: {e_mvt}")


            # 9. Mettre à jour Statut Ligne
            new_statut_ligne = 'Recue' if new_total_recu == ligne.quantite_commandee else 'Partielle'
            if new_statut_ligne != ligne.statut_ligne:
                    logger.debug(f"Mise à jour statut ligne ID {ligne_id} vers '{new_statut_ligne}'")
                    self.ligne_commande_repo.update_ligne_statut(ligne_id, new_statut_ligne)
            # Mettre à jour l'objet ligne localement pour _check_and_update_commande_statut
            ligne.quantite_recue = new_total_recu
            ligne.statut_ligne = new_statut_ligne


            # 10. Mettre à jour Statut Commande Globale (si nécessaire)
            self._check_and_update_commande_statut(ligne.commande_id)

            # --- Fin Transaction Logique ---

            logger.info(f"Réception ligne ID {ligne_id} enregistrée avec succès.")
            return True

        except (GmaoPermissionError, ValueError, DatabaseError, BusinessLogicError) as e:
                logger.error(f"Échec réception ligne ID {ligne_id}: {e}")
                raise # Remonter l'erreur gérée
        except Exception as e:
                logger.exception(f"Erreur inattendue réception ligne ID {ligne_id}: {e}")
                raise DatabaseError(f"Erreur serveur lors réception ligne {ligne_id}.") from e

    # _check_and_update_commande_statut (déjà défini précédemment, vérifier qu'il est correct)
    # _update_commande_total_ht (déjà défini précédemment)


    def envoyer_commande(self, commande_id: int, current_user: Utilisateur) -> bool:
            """ Change le statut d'une commande de 'Brouillon' à 'Envoyee'. """
            logger.info(f"Tentative d'envoi commande ID {commande_id} par {current_user.login}")

            # --- 1. Vérification Permissions ---
            allowed_roles = ['Admin', 'GestionStock'] # Rôles autorisés à envoyer
            if current_user.role not in allowed_roles:
                logger.warning(f"Tentative non autorisée d'envoi commande {commande_id} par {current_user.login} (rôle {current_user.role})")
                raise GmaoPermissionError("Droits insuffisants pour envoyer cette commande.")

            # --- 2. Vérification Statut Actuel ---
            try:
                # Récupérer la commande pour vérifier son statut actuel
                # Utiliser get_by_id du repo Commande, pas get_commande_details qui retourne un dict
                commande = self.commande_repo.get_by_id(commande_id)
                if not commande:
                    raise ValueError(f"Commande ID {commande_id} non trouvée.")

                if commande.statut != 'Brouillon':
                    logger.warning(f"Tentative d'envoyer commande {commande_id} qui est déjà au statut {commande.statut}.")
                    raise BusinessLogicError(f"La commande doit être au statut 'Brouillon' pour être envoyée (statut actuel: {commande.statut}).")

                # Optionnel: Vérifier si la commande a des lignes
                lignes = self.ligne_commande_repo.get_by_commande_id(commande_id)
                if not lignes:
                    raise BusinessLogicError("Impossible d'envoyer une commande vide (sans lignes).")

                # --- 3. Mise à jour Statut ---
                # Utiliser la méthode update_statut du repo Commande
                success = self.commande_repo.update_statut(commande_id, 'Envoyee')
                if success:
                    logger.info(f"Commande ID {commande_id} passée au statut 'Envoyee'.")
                else:
                    logger.error(f"La mise à jour du statut vers 'Envoyee' a échoué pour commande ID {commande_id} (rowCount=0?).")
                    raise DatabaseError(f"Échec de la mise à jour du statut pour commande ID {commande_id}.")

                return success

            except (GmaoPermissionError, ValueError, DatabaseError, BusinessLogicError) as e:
                logger.error(f"Échec envoi commande ID {commande_id}: {e}")
                raise # Remonter l'erreur gérée
            except Exception as e:
                logger.exception(f"Erreur inattendue envoi commande ID {commande_id}: {e}")
                raise DatabaseError(f"Erreur serveur lors envoi commande {commande_id}.") from e
        # -----------------------------

        # ... (autres méthodes : receive_ligne_commande, etc.) ...