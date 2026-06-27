# gmao_app/app/core/services/compteur_service.py
""" Service pour la gestion des Compteurs et des relevés historiques. """
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date # Import pour date/datetime

# --- Imports nécessaires ---
from app.core.models.compteur import Compteur
from app.core.models.historique_compteur import HistoriqueCompteur
from app.core.models.utilisateur import Utilisateur # Pour permissions
from app.data.repositories.compteur_repository import CompteurRepository
from app.data.repositories.historique_compteur_repository import HistoriqueCompteurRepository
# Autres repos potentiels pour validations (Machine, Utilisateur)
from app.data.repositories.machine_repository import MachineRepository # Pour vérifier existence Machine
from app.data.repositories.user_repository import UserRepository # Pour vérifier existence Utilisateur (si besoin)

from app.utils.exceptions import GmaoPermissionError, DatabaseError, BusinessLogicError # Imports exceptions

from app.core.services.maintenance_service import MaintenanceService
print('### DEBUG: Chargement module compteur_service.py')
logger = logging.getLogger(__name__)

class CompteurService:
    """ Gère la logique métier liée aux compteurs machines et leurs relevés. """

    def __init__(self,
                 compteur_repo: CompteurRepository,
                 historique_compteur_repo: HistoriqueCompteurRepository,
                 machine_repo: MachineRepository, # Injecter le repo Machine pour validation FK
                 user_repo: UserRepository, # Injecter le repo User pour validation FK (Historique)
                 maintenance_service: MaintenanceService # NOUVEAU: injection du service maintenance
                 ):
        """ Initialise le service avec les repositories requis. """
        self.compteur_repo = compteur_repo
        self.historique_compteur_repo = historique_compteur_repo
        self.machine_repo = machine_repo
        self.user_repo = user_repo # Pour validation dans add_historique
        self.maintenance_service = maintenance_service # NOUVEAU: pour création OT auto
        logger.info("CompteurService initialisé.")


    # --- Gestion des Compteurs (paramètres des compteurs, pas les valeurs) ---

    def create_compteur(self, compteur_data: Dict[str, Any], current_user: Utilisateur) -> Optional[Compteur]:
        """ Crée un nouveau compteur pour une machine, avec vérification des droits. """
        logger.debug(f"Tentative création compteur par {current_user.login}...")

        # --- 1. Vérification Permissions ---
        # Qui peut définir des compteurs sur les machines ? Admin, Responsable Maint ?
        allowed_roles = ['Admin', 'RespMaint'] # Exemple
        if current_user.role not in allowed_roles:
            msg = "Droits insuffisants pour créer un compteur."
            logger.warning(f"Tentative non autorisée création compteur par {current_user.login} (rôle {current_user.role}). {msg}")
            raise GmaoPermissionError(msg)

        # --- 2. Validation et Préparation des Données ---
        try:
            # Champs obligatoires pour la création du modèle
            if not all(k in compteur_data for k in ['machine_id', 'nom', 'unite']):
                raise ValueError("Machine ID, nom et unité sont requis pour créer un compteur.")

            machine_id = int(compteur_data['machine_id'])
            nom_compteur = compteur_data['nom'].strip()
            unite_compteur = compteur_data['unite'].strip()

            if not nom_compteur or not unite_compteur:
                 raise ValueError("Le nom et l'unité du compteur ne peuvent pas être vides.")

            # Optionnel: Valider existence Machine
            machine = self.machine_repo.get_by_id(machine_id)
            if not machine:
                 raise ValueError(f"La machine ID {machine_id} n'existe pas.")

            compteur_model = Compteur(
                machine_id=machine_id,
                nom=nom_compteur,
                unite=unite_compteur,
                # Valeur actuelle et date de dernier relevé sont initialisés à 0.0 / None par le modèle
                seuil_alerte=float(compteur_data.get('seuil_alerte')) if compteur_data.get('seuil_alerte') is not None else None,
                seuil_prev_ot=float(compteur_data.get('seuil_prev_ot')) if compteur_data.get('seuil_prev_ot') is not None else None,
                # actif=bool(compteur_data.get('actif', True)) # Si champ actif est utilisé
            )

        except (ValueError, TypeError) as e:
             logger.error(f"Validation/Préparation données compteur échouée: {e}")
             raise ValueError(f"Données invalides pour le compteur: {e}") # Renvoyer une ValueError métier
        except Exception as e:
            logger.exception(f"Erreur inattendue préparation données compteur: {e}")
            raise BusinessLogicError("Erreur serveur lors de la préparation des données du compteur.")

        # --- 3. Appel au Repository ---
        try:
            new_id = self.compteur_repo.add(compteur_model)
            if new_id:
                compteur_model.id_compteur = new_id # Mettre à jour l'objet
                logger.info(f"Compteur ID {new_id} créé pour machine {machine_id} par {current_user.login}.")
                return compteur_model
            else:
                 # Le repository devrait lever DatabaseError, ce cas ne devrait pas arriver souvent
                 logger.error("Le repository.add(Compteur) n'a pas retourné d'ID après succès apparent.")
                 raise DatabaseError("Erreur inconnue lors de l'ajout du compteur en base de données.")

        except (DatabaseError, ValueError) as e: # Attrape DatabaseError et potentielle ValueError du repo
             logger.error(f"Échec création compteur en DB pour machine {machine_id} par {current_user.login}: {e}")
             raise # Remonter l'erreur gérée
        except Exception as e:
              logger.exception(f"Erreur inattendue ajout compteur DB pour machine {machine_id}: {e}")
              raise DatabaseError("Erreur serveur lors de l'ajout du compteur en base de données.")


    def get_compteur_by_id(self, compteur_id: int) -> Optional[Compteur]:
        """ Récupère un compteur par son ID. Pas de permission requise ici a priori (Lecture simple). """
        try:
            return self.compteur_repo.get_by_id(compteur_id)
        except DatabaseError as e:
             logger.error(f"Erreur service get compteur ID {compteur_id}: {e}")
             # Préférer retourner None en cas d'erreur de lecture pour ne pas bloquer l'UI?
             return None
        except Exception as e:
             logger.exception(f"Erreur inattendue service get compteur ID {compteur_id}: {e}")
             return None


    def get_compteurs_for_machine(self, machine_id: int) -> List[Compteur]:
        """ Récupère la liste des compteurs d'une machine. Pas de permission requise ici. """
        try:
             return self.compteur_repo.get_by_machine_id(machine_id)
        except DatabaseError as e:
             logger.error(f"Erreur service get compteurs pour machine ID {machine_id}: {e}")
             return [] # Retourner liste vide
        except Exception as e:
             logger.exception(f"Erreur inattendue service get compteurs pour machine ID {machine_id}: {e}")
             return [] # Retourner liste vide


    def update_compteur(self, compteur: Compteur, current_user: Utilisateur) -> bool:
        """ Met à jour les paramètres d'un compteur (pas sa valeur), avec droits. """
        logger.debug(f"Tentative màj compteur ID {compteur.id_compteur} par {current_user.login}...")

        # --- 1. Vérification Permissions ---
        # Qui peut modifier les paramètres d'un compteur ? Admin, Responsable Maint ?
        allowed_roles = ['Admin', 'RespMaint'] # Exemple
        if current_user.role not in allowed_roles:
            msg = "Droits insuffisants pour modifier un compteur."
            logger.warning(f"Tentative non autorisée màj compteur ID {compteur.id_compteur} par {current_user.login} (rôle {current_user.role}). {msg}")
            raise GmaoPermissionError(msg)

        # --- 2. Validation Données (si applicable, si update_compteur prend un dict plutot que l'objet) ---
        # Si on passe l'objet complet, la validation doit se faire avant l'appel au service
        if not compteur.id_compteur:
             raise ValueError("ID du compteur manquant pour la mise à jour.")
        # TODO: Ajouter d'autres validations si des champs sont passés via dict


        # --- 3. Appel au Repository ---
        try:
            # Note: Le repository update_compteur ne met pas à jour la valeur actuelle / date
            success = self.compteur_repo.update(compteur)
            if success:
                logger.info(f"Compteur ID {compteur.id_compteur} mis à jour (paramètres) par {current_user.login}.")
            return success # Le repository logguerait déjà si rowCount=0

        except (DatabaseError, ValueError) as e:
             logger.error(f"Échec màj paramètres compteur ID {compteur.id_compteur} en DB: {e}")
             raise
        except Exception as e:
             logger.exception(f"Erreur inattendue màj paramètres compteur ID {compteur.id_compteur}: {e}")
             raise DatabaseError("Erreur serveur lors de la mise à jour des paramètres du compteur.")


    def delete_compteur(self, compteur_id: int, current_user: Utilisateur) -> bool:
        """ Supprime un compteur et ses historiques, avec droits. """
        logger.debug(f"Tentative suppression compteur ID {compteur_id} par {current_user.login}...")

        # --- 1. Vérification Permissions ---
        # Qui peut supprimer un compteur ? Admin, Responsable Maint ?
        allowed_roles = ['Admin', 'RespMaint'] # Exemple
        if current_user.role not in allowed_roles:
            msg = "Droits insuffisants pour supprimer un compteur."
            logger.warning(f"Tentative non autorisée suppression compteur ID {compteur_id} par {current_user.login} (rôle {current_user.role}). {msg}")
            raise GmaoPermissionError(msg)

        # --- 2. Appel au Repository ---
        try:
            success = self.compteur_repo.delete(compteur_id)
            if success:
                logger.info(f"Compteur ID {compteur_id} supprimé par {current_user.login}.")
            return success # Le repository logguerait si rowCount=0

        except DatabaseError as e:
            logger.error(f"Échec suppression compteur ID {compteur_id} en DB: {e}")
            raise # Le repository gère l'erreur si le compteur est référencé ailleurs
        except Exception as e:
             logger.exception(f"Erreur inattendue suppression compteur ID {compteur_id}: {e}")
             raise DatabaseError("Erreur serveur lors de la suppression du compteur.")


    # --- Gestion des Relevés Historiques ---

    def add_historique_releve(self, releve_data: Dict[str, Any], current_user: Utilisateur) -> Optional[HistoriqueCompteur]:

        """ Enregistre un nouveau relevé de compteur et met à jour la valeur actuelle du compteur principal. """
        logger.debug(f"Tentative ajout relevé historique par {current_user.login}...")

        # --- 1. Vérification Permissions ---
        # Qui peut saisir des relevés ? Techniciens, Opérateurs (futur), Admin?
        allowed_roles = ['Admin', 'Technicien'] # Exemple
        if current_user.role not in allowed_roles:
            msg = "Droits insuffisants pour enregistrer un relevé."
            logger.warning(f"Tentative non autorisée ajout relevé par {current_user.login} (rôle {current_user.role}). {msg}")
            raise GmaoPermissionError(msg)

        # --- 2. Validation et Préparation des Données ---
        try:
            # Champs obligatoires
            if not all(k in releve_data for k in ['compteur_id', 'valeur']):
                 raise ValueError("Compteur ID et valeur du relevé sont requis.")

            compteur_id = int(releve_data['compteur_id'])
            valeur_releve = float(releve_data['valeur'])
            date_releve_data = releve_data.get('date_releve') # Peut être fourni, sinon utiliser NOW
            utilisateur_releve_id = releve_data.get('utilisateur_id', current_user.id_utilisateur) # Utiliser l'utilisateur courant par défaut
            maintenance_releve_id = releve_data.get('maintenance_id') # Optionnel

            # Déterminer la date/heure exacte du relevé
            if date_releve_data is None:
                date_releve_obj = datetime.now()
            elif isinstance(date_releve_data, datetime):
                date_releve_obj = date_releve_data
            elif isinstance(date_releve_data, date):
                 # Si seule la date est fournie, utiliser le début de journée ou l'heure actuelle? Utilisons heure actuelle par défaut.
                 date_releve_obj = datetime.combine(date_releve_data, datetime.now().time()) # Combine date fournie avec heure actuelle
            # TODO: Gérer si date_releve_data est une chaîne et qu'il faut la parser


            if valeur_releve < 0: # Une valeur de compteur ne doit pas être négative ?
                 raise ValueError("La valeur du relevé ne peut pas être négative.")


            # Optionnel: Valider existence Compteur et Utilisateur/Maintenance si IDs fournis
            compteur = self.compteur_repo.get_by_id(compteur_id)
    
            if not compteur: raise ValueError(f"Le compteur ID {compteur_id} n'existe pas.")
            # Note: La FK dans la DB gère l'existence des FKs, mais la validation métier ici peut donner un message plus clair.

            historique_model = HistoriqueCompteur(
                compteur_id=compteur_id,
                date_releve=date_releve_obj,
                valeur=valeur_releve,
                utilisateur_id=utilisateur_releve_id,
                maintenance_id=maintenance_releve_id
            )

        except (ValueError, TypeError) as e:
             logger.error(f"Validation/Préparation données relevé échouée: {e}")
             raise ValueError(f"Données invalides pour le relevé: {e}")
        except DatabaseError as e: # Erreur get_by_id
              logger.error(f"Erreur DB lors validation relevé: {e}")
              raise e # Remonter l'erreur DB
        except Exception as e:
            logger.exception(f"Erreur inattendue préparation données relevé: {e}")
            raise BusinessLogicError("Erreur serveur lors de la préparation des données du relevé.")


        # --- 3. Appel aux Repositories (!!! Ordre Important + Idéalement Transaction !!!) ---
        try:
            # 3a. Enregistrer le relevé historique
            logger.debug("Appel repo.add(HistoriqueCompteur)...")
            new_hist_id = self.historique_compteur_repo.add(historique_model)
            if new_hist_id is None:
                 # Le repository devrait lever DatabaseError
                 raise DatabaseError("Échec inconnu lors de l'ajout de l'historique en DB.")
            historique_model.id_historique = new_hist_id

            # 3b. Mettre à jour la valeur actuelle et la date dans la table COMPTEUR principale
            logger.debug(f"Appel repo.update_current_value(Compteur ID {compteur_id})...")
            if not hasattr(self, 'compteur_repo'): raise DatabaseError("CompteurRepository non disponible.")
            success_compteur_update = self.compteur_repo.update_current_value(
                compteur_id, historique_model.valeur, historique_model.date_releve.date() # Passer seulement la date
            )
            if not success_compteur_update:
                 # Ceci est critique! L'historique est ajouté mais la valeur actuelle n'est pas mise à jour.
                 # Il faudrait idéalement un rollback de l'historique si l'update échoue.
                 logger.critical(f"INCOHÉRENCE DB MAJEURE: Historique ID {new_hist_id} ajouté, mais échec mise à jour valeur actuelle pour compteur ID {compteur_id}!")
                 # Lever une erreur indiquant l'incohérence potentielle.
                 raise DatabaseError(f"Incohérence DB: Historique enregistré, mais échec màj valeur actuelle compteur {compteur_id}.")

            # Déclenchement automatique d'OT si activé
            from app.config import AUTO_OT_ENABLED
            # Logique métier : après chaque ajout de relevé, si la valeur dépasse un seuil, on déclenche automatiquement un OT.
            if AUTO_OT_ENABLED:
                seuil_prev = getattr(compteur, 'seuil_prev_ot', None)
                seuil_alerte = getattr(compteur, 'seuil_alerte', None)
                ot_type = None
                ot_urgence = False
                if seuil_alerte is not None and valeur_releve >= seuil_alerte:
                    ot_type = 'Correctif'
                    ot_urgence = True
                elif seuil_prev is not None and valeur_releve >= seuil_prev:
                    ot_type = 'Préventif'
                    ot_urgence = False
                if ot_type:
                    ot_data = {
                        "machine_id": compteur.machine_id,
                        "type": ot_type,
                        "urgence": ot_urgence,
                        "description": f"OT automatique déclenché par compteur {compteur.nom} (valeur: {valeur_releve})",
                        "utilisateur_createur_id": current_user.id_utilisateur,
                        "date_creation": datetime.now(),
                        "statut": "Créé",
                    }
                    try:
                        created_ot = self.maintenance_service.create_ot(ot_data)
                        logger.info(f"OT automatique ({ot_type}) déclenché pour machine {compteur.machine_id} via compteur {compteur.id_compteur}, OT ID: {created_ot.id_ot}, numéro: {created_ot.numero_ot}")
                        # Indiquer dynamiquement sur l'historique qu'un OT a été déclenché
                        setattr(historique_model, 'ot_auto_triggered', True)
                        setattr(historique_model, 'ot_auto_type', ot_type)
                    except Exception as e:
                        logger.error(f"Erreur lors de la création automatique de l'OT: {e}")
                        setattr(historique_model, 'ot_auto_triggered', False)
                        setattr(historique_model, 'ot_auto_type', None)
            logger.info(f"Relevé historique ID {new_hist_id} ajouté pour compteur {compteur_id}. Valeur actuelle {historique_model.valeur} mise à jour.")
            return historique_model # Retourne l'objet créé

        except (DatabaseError, ValueError) as e: # Attrape les erreurs gérées
             logger.error(f"Échec enregistrement relevé historique pour compteur {compteur_id} en DB: {e}")
             raise
        except Exception as e:
              logger.exception(f"Erreur inattendue enregistrement relevé historique pour compteur {compteur_id}: {e}")
              raise DatabaseError("Erreur serveur lors de l'enregistrement du relevé.")


    def get_historique_for_compteur(self, compteur_id: int, limit: Optional[int] = None) -> List[HistoriqueCompteur]:
        """ Récupère l'historique pour un compteur donné. """
        try:
             return self.historique_compteur_repo.get_by_compteur_id(compteur_id, limit=limit)
        except DatabaseError as e:
             logger.error(f"Erreur service get historique pour compteur ID {compteur_id}: {e}")
             return []
        except Exception as e:
             logger.exception(f"Erreur inattendue service get historique pour compteur ID {compteur_id}: {e}")
             return []


    # Pas de méthodes pour l'historique comme update_historique ou delete_historique ici a priori.
    # L'historique est une trace immuable.