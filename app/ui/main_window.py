# gmao_app/app/ui/main_window.py
"""
Fenêtre principale de l'application GMAO.
Contient la structure de base (menu, barre d'état) et accueillera les vues des modules.

Ce fichier est crucial pour l'application car il:
1. Définit l'interface utilisateur principale et sa structure
2. Gère la navigation entre les différentes vues (machines, maintenances, stocks...)
3. Implémente le contrôle d'accès basé sur les rôles utilisateurs
4. Centralise les interactions entre les services métier et l'interface
5. Coordonne les différentes vues spécialisées

L'architecture UI utilise:
- QStackedWidget: pour afficher une seule vue à la fois
- Pattern d'injection de dépendances: les services sont injectés dans la fenêtre
- Traduction internationalisée: via le mécanisme Qt Translator
- Personnalisation: police, disposition clavier, etc.

Le cycle de vie de la fenêttre principale:
1. Initialisation avec les services injectés
2. Création des vues spécialisées
3. Configuration des menus et actions avec contrôle d'accès
4. Connexion des signaux et slots
5. Affichage de la vue d'accueil par défaut
"""
# Imports pour le logging et les types
import logging
logger = logging.getLogger(__name__)  # Logger spécifique à ce module
from typing import TYPE_CHECKING, Optional  # Types pour les annotations et vérifications

# Imports des composants Qt pour l'interface utilisateur
# PySide6 est la version officielle Python du framework Qt
from PySide6.QtWidgets import QMainWindow, QStatusBar, QMessageBox, QWidget, QStackedWidget, QDialog
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QInputDialog
from app.ui.dialogs.maintenance_detail_dialog import MaintenanceDetailDialog
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog  # Pour l'interface graphique
from PySide6.QtWidgets import QVBoxLayout, QLabel  # Pour la construction des dialogues
from PySide6.QtGui import QFont, QKeySequence  # Pour les polices, actions et raccourcis
from PySide6.QtCore import Slot  # Décorateur pour les gestionnaires de signaux Qt

# Modules standard pour la gestion des fichiers et données
import json  # Pour sérialiser/désérialiser les préférences utilisateur
import os  # Pour les opérations sur le système de fichiers
import traceback  # Pour les traces d'erreur détaillées

# Imports pour les fonctions de base de données et backup
from app.data.database import close_connection
from app.utils.backup_utils import backup_database

# Chemin du fichier de configuration utilisateur
# Utilise le répertoire utilisateur pour persister les préférences entre les sessions
CONFIG_FILE = os.path.expanduser("~/.gmao_app_config.json")  # ~/.gmao_app_config.json sur tous les OS

def save_user_config(font=None, keyboard_layout=None):
    """
    Sauvegarde les préférences utilisateur dans un fichier JSON.
    
    Cette fonction permet de persister les choix de l'utilisateur entre les sessions,
    notamment la police d'affichage et la disposition du clavier. Elle fonctionne de
    manière incrémentale en ne modifiant que les paramètres spécifiés.
    
    Args:
        font (QFont, optional): Police à sauvegarder. Si None, la police existante n'est pas modifiée.
        keyboard_layout (str, optional): Code de disposition clavier. Si None, la disposition existante n'est pas modifiée.
    """
    import logging  # Import local pour éviter les dépendances circulaires
    
    # Dictionnaire pour stocker les préférences
    data = {}
    
    # Charge la configuration existante si le fichier existe
    # Cette approche préserve les paramètres non modifiés
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            # En cas d'erreur de lecture, initialise un dictionnaire vide
            data = {}
    
    # Mise à jour de la police si spécifiée
    if font is not None:
        # Sauvegarde le nom de famille et la taille de la police
        data["font"] = {"family": font.family(), "size": font.pointSize()}
    
    # Mise à jour de la disposition clavier si spécifiée
    if keyboard_layout is not None:
        data["keyboard_layout"] = keyboard_layout
    
    # Écriture du fichier de configuration
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)  # Sérialisation des données en JSON
        logging.info(f"Config utilisateur sauvegardée dans {CONFIG_FILE}: {data}")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de la config utilisateur: {e}")

def load_user_config():
    """
    Charge les préférences utilisateur depuis le fichier JSON.
    
    Cette fonction récupère les préférences de l'utilisateur sauvegardées entre les sessions.
    Si le fichier n'existe pas ou est corrompu, un dictionnaire vide est retourné,
    ce qui conduira à l'utilisation des valeurs par défaut de l'application.
    
    Returns:
        dict: Dictionnaire contenant les préférences utilisateur, ou dict vide si non disponible
    """
    import logging  # Import local pour éviter les dépendances circulaires
    
    # Vérifie si le fichier de configuration existe
    if not os.path.exists(CONFIG_FILE):
        logging.info(f"Aucun fichier de config utilisateur trouvé ({CONFIG_FILE})")
        return {}  # Retourne un dictionnaire vide pour utiliser les valeurs par défaut
    
    # Tentative de lecture du fichier
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)  # Désérialisation du JSON
        logging.info(f"Config utilisateur chargée depuis {CONFIG_FILE}: {data}")
        return data
    except Exception as e:
        # En cas d'erreur (fichier corrompu, format invalide...)
        logging.warning(f"Impossible de charger la config utilisateur: {e}")
        return {}  # Retourne un dictionnaire vide pour utiliser les valeurs par défaut

# Compatibilité ancienne version
save_font_to_config = lambda font: save_user_config(font=font)
load_font_from_config = lambda: (lambda d: QFont(d["font"]["family"], d["font"]["size"]) if "font" in d else None)(load_user_config())

from app.ui.views.machine_view import MachineView  # Machine management view
from app.core.services.machine_service import MachineService
from app.ui.views.welcome_view import WelcomeView  # Ajout de la vue d'accueil
from app.core.models.utilisateur import Utilisateur
from app.ui.views.site_view import SiteView
from app.ui.views.fabricant_view import FabricantView
from app.ui.views.type_machine_view import TypeMachineView
from app.ui.views.ot_view import OTView
from app.ui.views.fournisseur_view import FournisseurView
from app.ui.views.piece_view import PieceView



# Importer les services et vues nécessaires
from app.core.services.user_service import UserService
from app.ui.views.user_view import UserView
from app.core.services.maintenance_service import MaintenanceService
from app.ui.views.equipe_view import EquipeView
from app.ui.views.technicien_view import TechnicienView
from app.core.services.stock_service import StockService
from app.core.services.preventive_service import PreventiveMaintenanceService
from app.ui.views.gamme_view import GammeView
from app.core.services.achat_service import AchatService
from app.ui.views.commande_view import CommandeView
from app.core.services.compteur_service import CompteurService
from app.core.services.finance_service import FinanceService # <-- Ajouter cet import
# Importer d'autres vues ici dans les phases futures
# from app.ui.views.machine_view import MachineView
# ... etc ...
# Importer la configuration pour le dialogue "À Propos"
from app.config import APP_NAME, APP_VERSION
from app.access_control import can_access, normalize_role

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application GMAO.
    """
    def open_intervention_request_dialog(self):
        """
        Ouvre la fenêtre de demande d'intervention depuis le menu Gestion.
        """
        # Logique similaire à WelcomeView.open_intervention_request
        machine_list = []
        machine_id_map = {}
        current_user = getattr(self, 'current_user', None)
        if hasattr(self, 'machine_service') and self.machine_service:
            try:
                machines = self.machine_service.get_all_machines()
                for m in machines:
                    machine_list.append(m.nom)
                    machine_id_map[m.nom] = m.id_machine
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer la liste des machines: ") + str(e))
        from app.ui.views.intervention_request_view import InterventionRequestView
        dialog = InterventionRequestView(machine_list=machine_list, machine_id_map=machine_id_map, current_user=current_user, parent=self)
        dialog.exec()

    VIEW_INDEX_WELCOME = 0   # Vue d'accueil (dashboard)
    VIEW_INDEX_USERS = 1     # Gestion des utilisateurs
    VIEW_INDEX_MACHINES = 2  # Gestion des machines/équipements
    # Les autres vues sont définies dans l'ordre d'ajout au QStackedWidget

    def __init__(self, 
                user_service: UserService, 
                machine_service: MachineService, 
                maintenance_service: MaintenanceService, 
                stock_service: StockService, 
                preventive_service: PreventiveMaintenanceService, 
                achat_service: AchatService,
                compteur_service: CompteurService,
                finance_service: FinanceService,
                logged_in_user: Utilisateur,
                app_language: str = "fr"
                ):
        """
        Initialise la fenêtre principale avec tous les services et paramètres nécessaires.
        
        Cette méthode implémente le pattern d'injection de dépendances, où tous les services
        nécessaires sont passés en paramètres plutôt que créés à l'intérieur. Cela facilite
        les tests et permet le découplage des composants.
        
        Args:
            user_service (UserService): Service de gestion des utilisateurs
            machine_service (MachineService): Service de gestion des machines et équipements
            maintenance_service (MaintenanceService): Service de gestion des interventions
            stock_service (StockService): Service de gestion des stocks et pièces
            preventive_service (PreventiveMaintenanceService): Service de maintenance préventive
            achat_service (AchatService): Service de gestion des achats et commandes
            compteur_service (CompteurService): Service de gestion des compteurs machines
            finance_service (FinanceService): Service de gestion financière
            logged_in_user (Utilisateur): L'utilisateur authentifié
            app_language (str): Code de langue de l'application (par défaut: 'fr')
        """
        # Le flux d'initialisation suit plusieurs étapes:
        # 1. Chargement des préférences utilisateur
        # 2. Stockage des services injectés
        # 3. Configuration de la fenêtre principale
        # 4. Création des vues et des menus
        # 5. Connexion des signaux
        # 6. Configuration des actions spécifiques (comme les KPI)
        # 7. Affichage de la vue d'accueil par défaut
        # --- Étape 1: Chargement des préférences utilisateur ---
        # Charger les préférences utilisateur AVANT la création des widgets pour une application cohérente
        config = load_user_config()
        
        # Configuration de la police personnalisée si définie dans les préférences
        font = None
        if "font" in config:
            # Création d'un objet QFont à partir des paramètres sauvegardés
            font = QFont(config["font"]["family"], config["font"]["size"])
        
        if font:
            # Application de la police à toute l'application via QApplication
            # Ceci affecte tous les widgets qui n'ont pas de police spécifique définie
            QApplication.setFont(font)
            self.current_font = font
            logger.info(f"Police chargée: {font.family()} - {font.pointSize()}")
        else:
            # Aucune police personnalisée, utilisation de la police par défaut du système
            self.current_font = None
        
        # Configuration de la disposition clavier (utilisé pour certaines opérations spécifiques)
        self.keyboard_layout = config.get("keyboard_layout", "fr")
        logger.info(f"Layout clavier chargé: {self.keyboard_layout}")
        
        # Initialisation de la classe parent QMainWindow
        super().__init__()
        
        # --- Étape 2: Stockage des services injectés ---
        # Ces services contiennent la logique métier et seront utilisés par les différentes vues
        self.user_service = user_service         # Service de gestion des utilisateurs
        self.machine_service = machine_service    # Service de gestion des machines
        self.maintenance_service = maintenance_service  # Service de maintenance curative
        self.stock_service = stock_service        # Service de gestion des stocks
        self.preventive_service = preventive_service  # Service de maintenance préventive
        self.achat_service = achat_service        # Service d'achat et approvisionnement
        self.compteur_service = compteur_service  # Service de gestion des compteurs
        self.finance_service = finance_service    # Service de gestion financière

        # --- Étape 3: Gestion de l'utilisateur connecté ---
        # Stockage de l'objet utilisateur complet pour un accès facile aux attributs
        self.current_user: Utilisateur = logged_in_user

        # --- Étape 4: Configuration de la chaîne de connexion PostgreSQL ---
        # Cette chaîne sera utilisée par la vue d'accueil pour afficher des informations de connexion
        import os
        if hasattr(self, 'db_connection_str') and self.db_connection_str:
            # Utilise la chaîne de connexion déjà définie si elle existe
            welcome_db_str = self.db_connection_str
        else:
            # Construction de la chaîne de connexion à partir des paramètres de configuration
            # Cela permet une flexibilité dans la définition des paramètres PostgreSQL
            from app.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
            welcome_db_str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            self.db_connection_str = welcome_db_str
        
        # Stockage de la langue de l'application pour la transmettre aux vues
        self.app_language = app_language

        # --- Étape 5: Initialisation de la vue d'accueil ---
        # La vue d'accueil est la première vue affichée à l'utilisateur
        # Elle contient le tableau de bord et doit inclure un bouton pour les demandes d'intervention
        # Note: Ce bouton sera accessible à tous les utilisateurs pour simplifier la création de demandes
        self.welcome_view = WelcomeView(parent=self, maintenance_service=self.maintenance_service)
        self.welcome_view.db_connection_str = welcome_db_str  # Transmission de la chaîne de connexion
        self.welcome_view.app_language = self.app_language     # Transmission de la langue

        # --- Étape 6: Configuration des informations utilisateur ---
        # Stockage de l'ID utilisateur pour les opérations de base de données
        self.logged_in_user_id: Optional[int] = logged_in_user.id_utilisateur if logged_in_user else None
        
        # Détermination du rôle utilisateur pour le contrôle d'accès
        # Cette information est essentielle pour la configuration des menus et actions
        self.user_role = getattr(logged_in_user, 'role', None)
        
        # Journalisation des informations utilisateur pour le débogage
        logger.debug(f"[MainWindow] Utilisateur connecté: {self.current_user.login if self.current_user else 'Inconnu'} "
                     f"(ID: {self.logged_in_user_id}), Rôle: {self.user_role}")
        
        # Vérification de la validité de l'utilisateur
        if self.logged_in_user_id is None:
             logger.error("MainWindow initialisée sans ID utilisateur valide !")
             # Cette condition ne devrait jamais se produire car l'authentification est vérifiée avant
             # Commentaire: Le code pour quitter l'application est commenté car une vérification 
             # préalable est déjà effectuée dans main.py
             # QMessageBox.critical(self, "Erreur Critique", "Utilisateur non valide.")
             # QApplication.quit()
        
        # Confirmation de l'initialisation réussie
        logger.info(f"MainWindow initialisée pour l'utilisateur ID {self.logged_in_user_id} "
                    f"({self.current_user.login if self.current_user else 'Inconnu'})")
        # ------------------------------------
        
        # --- Commentaire sur le code de test temporaire ---
        # Ce bloc de code était utilisé pour les tests initiaux avec un utilisateur simulé
        # Il est maintenant remplacé par l'authentification réelle via LoginDialog
        # self.logged_in_user_id: Optional[int] = None # Initialiser
        # !! SIMULATION LOGIN POUR TEST !! A REMPLACER PLUS TARD !!
        # Supposons que l'utilisateur avec ID=1 se connecte
        # self.logged_in_user_id = 1
        # logger.warning(f"!!! Utilisateur connecté simulé pour TEST: ID={self.logged_in_user_id} !!!")
        # ---------------------
        
        # --- Étape 7: Configuration de l'interface utilisateur principale ---
        logger.info("Initialisation de la MainWindow...")
        
        # Définition du titre de la fenêtre (avec support de traduction via self.tr)
        self.setWindowTitle(self.tr(f"{APP_NAME} - v{APP_VERSION}"))
        
        # Définition des dimensions initiales de la fenêtre
        # Pour un meilleur affichage sur les écrans haute résolution, une taille large est utilisée
        self.setGeometry(0, 0, 1920, 1080)  # Format x, y, largeur, hauteur

        # --- Configuration de la barre de statut ---
        # La barre de statut affiche des messages informatifs à l'utilisateur
        self.status_bar = QStatusBar(self)  # Création de la barre de statut
        self.setStatusBar(self.status_bar)  # Installation dans la fenêtre principale
        self.update_status_bar(self.tr("Prêt."))  # Message initial

        # --- Configuration du widget central QStackedWidget ---
        # QStackedWidget permet d'afficher une seule vue à la fois dans la zone centrale
        # Il facilite la navigation entre les différentes vues de l'application
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)  # Définition comme widget central

        # --- Étape 8: Initialisation des vues, menus et connexions ---
        # Création et configuration des différentes vues de l'application
        self.setup_views()  # Initialise toutes les vues et les ajoute au QStackedWidget
        
        # Création des actions pour les menus
        # Cette étape prend en compte le rôle de l'utilisateur pour le contrôle d'accès
        self.create_actions()
        
        # Création de la barre de menu avec les actions
        self.create_menu_bar()
        
        # Connexion des signaux entre les vues
        self._connect_view_actions()
        
        # Affichage de la vue d'accueil par défaut
        # Cette vue doit inclure un bouton visible pour les demandes d'intervention
        # accessible à tous les utilisateurs pour simplifier le processus
        self.stacked_widget.setCurrentIndex(self.VIEW_INDEX_WELCOME)

    def switch_view(self, view_widget):
        """
        Change la vue active dans l'interface utilisateur.
        
        Cette méthode est centrale dans la navigation de l'application. Elle permet
        de basculer entre les différentes vues (accueil, machines, maintenance, etc.)
        en utilisant le QStackedWidget comme conteneur principal. Les vues sont des
        widgets complets qui occupent toute la zone centrale de l'application.
        
        Remarque: La vue d'accueil (WelcomeView) doit inclure un bouton bien visible
        pour la création des demandes d'intervention, accessible à tous les utilisateurs
        quel que soit leur rôle, afin de simplifier le processus de signalement.
        
        Args:
            view_widget: Le widget de vue à afficher dans la zone centrale
        """
        # Récupération de l'index de la vue dans le QStackedWidget
        index = self.stacked_widget.indexOf(view_widget)
        
        # Vérification que la vue existe dans le QStackedWidget
        if index == -1:
            # Message d'erreur si la vue n'est pas trouvée
            self.update_status_bar(self.tr("Vue non trouvée dans le QStackedWidget."))
            return
            
        # Changement de la vue active
        self.stacked_widget.setCurrentIndex(index)
        
        # Mise à jour de la barre de statut pour informer l'utilisateur
        self.update_status_bar(self.tr(f"Vue {view_widget.__class__.__name__} affichée."))

    def choose_font(self):
        """
        Permet à l'utilisateur de choisir une police personnalisée pour l'application.
        
        Cette méthode ouvre une boîte de dialogue de sélection de police, applique la police 
        choisie à toute l'application et sauvegarde ce choix dans les préférences utilisateur.
        La taille de police est limitée entre 8 et 24 points pour garantir la lisibilité.
        
        Cette fonctionnalité améliore l'ergonomie de l'application en permettant aux 
        utilisateurs d'adapter l'interface à leurs besoins (vision, confort de lecture).
        """
        # Import local pour éviter les imports circulaires
        from PySide6.QtWidgets import QFontDialog, QApplication
        
        # Ouverture de la boîte de dialogue de sélection de police
        # Cette boîte retourne un tuple (QFont, bool) indiquant la police sélectionnée et si l'utilisateur a validé
        result = QFontDialog.getFont(self)
        
        # Initialisation des variables
        font = None
        ok = False
        
        # Gérer les différentes versions de PySide6 qui peuvent renvoyer le tuple dans un ordre différent
        if isinstance(result[0], type(QApplication.font())):
            font, ok = result  # Format: (QFont, bool)
        else:
            ok, font = result  # Format: (bool, QFont)
        
        # Vérification de la validité de la police et de sa taille
        # La taille est limitée entre 8 et 24 points pour garantir la lisibilité
        if ok and font is not None and hasattr(font, "family") and 8 <= font.pointSize() <= 24:
            # Application de la police à toute l'application
            QApplication.setFont(font)
            # Stockage de la police courante pour référence future
            self.current_font = font
            # Sauvegarde des préférences utilisateur dans un fichier JSON
            # Cette sauvegarde inclut également la disposition clavier actuelle
            save_user_config(font=font, keyboard_layout=self.keyboard_layout)

    def reset_font(self):
        """
        Réinitialise la police de l'application à une police par défaut lisible.
        
        Cette méthode essaie d'utiliser une police standard disponible sur le système
        en suivant un ordre de préférence. Si aucune police préférée n'est disponible,
        la police par défaut du système est utilisée. La taille est fixée à 12 points
        pour garantir une bonne lisibilité.
        
        Cette fonctionnalité permet à l'utilisateur de revenir à une configuration standard
        après avoir expérimenté avec différentes polices.  
        """
        # Imports locaux pour éviter les imports circulaires
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont
        
        # Liste des polices préférées dans l'ordre de priorité
        # Ces polices sont choisies pour leur lisibilité et leur disponibilité sur différents OS
        preferred_fonts = ["DejaVu Sans", "Arial", "Ubuntu", "Liberation Sans", "Sans Serif"]
        font_family = None
        
        # Recherche de la première police disponible dans la liste de préférences
        for fam in preferred_fonts:
            f = QFont(fam, 12)  # Création d'un objet QFont pour test
            # Vérification si la police est disponible sur le système
            if QFont(fam).exactMatch() or fam in QFont().families():
                font_family = fam
                break
        
        # Si aucune police préférée n'est disponible, utilisation de la police par défaut du système
        if not font_family:
            font_family = QFont().defaultFamily()
        
        # Création et application de la police
        font = QFont(font_family, 12)  # Taille 12 points: bon compromis de lisibilité
        QApplication.setFont(font)     # Application à toute l'application
        self.current_font = font        # Stockage pour référence
        
        # Sauvegarde de la configuration (conserve la disposition clavier actuelle)
        save_user_config(font=font)  # Sauvegarde dans le fichier de configuration utilisateur

    def adapt_to_screen_resolution(self):
        """
        Adapte la taille de la fenêtre principale à la résolution de l'écran.
        
        Cette méthode détecte la résolution de l'écran principal et ajuste la taille
        de la fenêtre pour utiliser optimalement l'espace disponible. Cette
        fonctionnalité est particulièrement utile lors du premier lancement de
        l'application ou lors du changement d'écran.
        """
        # Import local pour éviter les imports circulaires
        from PySide6.QtWidgets import QApplication
        
        # Récupération de l'écran principal
        screen = QApplication.primaryScreen()
        
        # Vérification que l'écran est disponible et adaptation de la géométrie
        if screen:
            # Récupération de la géométrie disponible (espace utilisable sans les barres d'outils système)
            geometry = screen.availableGeometry()
            # Application de cette géométrie à la fenêtre principale
            self.setGeometry(geometry)

    def update_status_bar(self, message: str):
        """
        Affiche un message temporaire dans la barre de statut de l'application.
        
        Cette méthode permet d'informer l'utilisateur sur l'action en cours ou
        le résultat d'une opération. Le message est automatiquement traduit
        via le système de traduction Qt (self.tr) et disparait après 5 secondes.
        
        Args:
            message (str): Le message à afficher dans la barre de statut
        """
        # Affichage du message traduit avec une durée de 5000 ms (5 secondes)
        self.status_bar.showMessage(self.tr(message), 5000)
        
        # Journalisation du message pour le débogage
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Status Bar: {message}")

    def show_db_connection_dialog(self):
        """
        Affiche une boîte de dialogue permettant de modifier la connexion à la base de données.
        
        Cette fonctionnalité est principalement destinée aux administrateurs et
        permet de changer la chaîne de connexion PostgreSQL sans modifier le code source.
        Les changements prennent effet au prochain redémarrage de l'application.
        """
        # Import local pour éviter les imports circulaires
        from app.ui.dialogs.db_connection_dialog import DBConnectionDialog
        
        # Création de la boîte de dialogue avec la configuration actuelle
        # On suppose que self.db_connection_str est une URL du type postgresql://user:password@host:port/db
        import re
        current_config = {}
        if hasattr(self, 'db_connection_str') and self.db_connection_str:
            match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(\w+)", self.db_connection_str)
            if match:
                current_config = {
                    "POSTGRES_USER": match.group(1),
                    "POSTGRES_PASSWORD": match.group(2),
                    "POSTGRES_HOST": match.group(3),
                    "POSTGRES_PORT": match.group(4),
                    "POSTGRES_DB": match.group(5),
                }
        dlg = DBConnectionDialog(current_config=current_config, parent=self)
        
        # Si l'utilisateur valide le dialogue
        if dlg.exec() == QDialog.Accepted:
            # Récupération de la nouvelle chaîne de connexion
            new_conn_str = dlg.get_conn_str()
            
            # Vérification et application de la nouvelle chaîne
            if new_conn_str:
                self.db_connection_str = new_conn_str
                # Information à l'utilisateur (changement effectif au redémarrage)
                QMessageBox.information(
                    self, 
                    "Connexion modifiée", 
                    f"Nouvelle connexion :\n{new_conn_str}\n\n(Reconnexion effective au prochain redémarrage de l'application)"
                )
            else:
                # Avertissement si la chaîne est vide
                QMessageBox.warning(self, "Chaîne vide", "Aucune chaîne de connexion saisie.")

        # Confirmation de l'initialisation complète
        logger.info("MainWindow initialisée avec succès.")

    def setup_views(self):
        """
        Crée et configure toutes les vues de l'application.
        
        Cette méthode initialise les différentes vues spécialisées (accueil, machines,
        maintenance, stock, etc.) et les ajoute au QStackedWidget principal. Elle définit
        également les constantes d'index pour faciliter la navigation entre les vues.
        
        La vue d'accueil (WelcomeView) doit inclure un bouton bien visible pour
        la création des demandes d'intervention, accessible à tous les utilisateurs
        pour simplifier le processus de signalement des problèmes par la production.
        """
        logger.debug("Configuration des vues...")
        
        # La méthode continue avec l'initialisation des différentes vues...
        # --- Ajout de la page d'accueil WelcomeView (déjà instanciée avec maintenance_service) ---
        self.stacked_widget.insertWidget(self.VIEW_INDEX_WELCOME, self.welcome_view)

        # Mise à jour barre de statut pour afficher l'utilisateur?
        self.update_status_bar(self.tr(f"Prêt. Connecté en tant que: {self.current_user.login} ({self.current_user.role})"))
        # 1. Vue Utilisateurs (Phase 1)
        try:
            self.user_view = UserView(self.user_service, self)
            self.stacked_widget.addWidget(self.user_view) # Index VIEW_INDEX_USERS implicite (0 pour le premier) -> NON, voir correction ci-dessous
            logger.debug("UserView ajoutée au StackedWidget.")
            # ATTENTION: L'index est déterminé par l'ordre d'ajout.
            # C'est plus sûr d'utiliser insertWidget avec un index prédéfini si l'ordre compte.
            # self.stacked_widget.insertWidget(self.VIEW_INDEX_USERS, self.user_view)
        except Exception as e:
            logger.exception("Erreur lors de la création ou ajout de UserView.")
            # Afficher un message ou désactiver l'accès à cette vue?

        # 2. Vues Futures (Exemples Phases suivantes)
        try:
            self.machine_view = MachineView(machine_service=self.machine_service, main_window=self)
            self.stacked_widget.insertWidget(self.VIEW_INDEX_MACHINES, self.machine_view)
            logger.debug("MachineView ajoutée au StackedWidget.")
        except Exception as e:
            logger.exception("Erreur lors de la création ou ajout de MachineView.")
            self.machine_view = None
            # Ajout d'un log explicite
            logger.error("self.machine_view n'a pas pu être créée : attribut mis à None.")

        
        # Dans MainWindow.setup_views

        # 3. Vue Sites (Phase 2a.1)
        try:
            self.site_view = SiteView(self.machine_service, self) # Réutilise MachineService
            self.stacked_widget.addWidget(self.site_view)
            logger.debug("SiteView ajoutée au StackedWidget.")
        except Exception as e:
            logger.error(f"Erreur création/ajout SiteView : {e}")
            self.site_view = None # Marquer comme non créé
            
        
        # Dans MainWindow.setup_views
        # ... (après SiteView) ...
        # 4. Vue Fabricants (Phase 2a.2)
        try:
            self.fabricant_view = FabricantView(self.machine_service, main_window=self)
            self.stacked_widget.addWidget(self.fabricant_view)
            logger.debug(f"FabricantView registered at index: {self.stacked_widget.indexOf(self.fabricant_view)}")
            logger.debug("FabricantView ajoutée au StackedWidget.")
        except Exception as e:
            logger.exception("Erreur création/ajout FabricantView.")
            self.fabricant_view = None
        

        # Dans MainWindow.setup_views
        # ... (après FabricantView) ...
        # 5. Vue Types Machine (Phase 2a.3)
        try:
            self.type_machine_view = TypeMachineView(self.machine_service, self)
            self.stacked_widget.addWidget(self.type_machine_view)
            logger.debug("TypeMachineView ajoutée au StackedWidget.")
        except Exception as e:
            logger.exception("Erreur création/ajout TypeMachineView.")
            self.type_machine_view = None


         # 6. Vue Equipes (Phase 3a)
        try:
            self.equipe_view = EquipeView(self.maintenance_service, self)
            self.stacked_widget.addWidget(self.equipe_view)
            logger.debug("EquipeView ajoutée.")
        except Exception as e: logger.exception("Erreur EquipeView."); self.equipe_view = None

        # 7. Vue Techniciens (Phase 3a)
        try:
            self.technicien_view = TechnicienView(self.maintenance_service, self)
            self.stacked_widget.addWidget(self.technicien_view)
            logger.debug("TechnicienView ajoutée.")
        except Exception as e: logger.exception("Erreur TechnicienView."); self.technicien_view = None

        # Ajouter ici les autres vues (OT, Pièces...) au fur et à mesure
        # Dans MainWindow.setup_views
        # ... (après les autres vues) ...
        # 8. Vue Ordres de Travail (Phase 3b)
        try:
            # OTView a besoin des deux services pour listes machines/tech et actions OT/Maint
            self.ot_view = OTView(self.machine_service, self.maintenance_service, self.stock_service, self.user_service, self)
            self.stacked_widget.addWidget(self.ot_view)
            logger.debug("OTView ajoutée.")
        except Exception as e:
            logger.exception("Erreur création/ajout OTView."); self.ot_view = None

        # 9. Vue Fournisseurs (Phase 4)
        try:
            self.fournisseur_view = FournisseurView(self.stock_service, self)
            self.stacked_widget.addWidget(self.fournisseur_view)
            logger.debug("FournisseurView ajoutée.")
        except Exception as e: logger.exception("Erreur FournisseurView."); self.fournisseur_view = None

        # 10. Vue Pièces (Phase 4)
        try:
            self.piece_view = PieceView(self.stock_service, self)
            self.stacked_widget.addWidget(self.piece_view)
            logger.debug("PieceView ajoutée.")
        except Exception as e: logger.exception("Erreur PieceView."); self.piece_view = None

        # 11. Vue Gammes (Phase 6)
        try:
            # TODO: Replace placeholder 1 with actual logged-in user ID
            placeholder_user_id = 1
            self.gamme_view = GammeView(self.preventive_service, self.machine_service, self.stock_service, placeholder_user_id, self)
            self.stacked_widget.addWidget(self.gamme_view)
            logger.debug("GammeView ajoutée.")
        except Exception as e: logger.exception("Erreur GammeView."); self.gamme_view = None


        # ... (après les autres vues) ...
        # 12. Vue Commandes (Phase 7)
        try:
            # AchatService a déjà été instancié dans main.py et passé à __init__ de MainWindow implicitement via **kwargs? Non, explicitement!
            # Il faut le récupérer depuis self.
            # Pour l'instant, supposons qu'il est passé via main.py (à corriger si nécessaire)
            # --> Correction: Il faut passer achat_service à MainWindow dans main.py
            self.commande_view = CommandeView(self.achat_service, self) # self.achat_service doit exister
            self.stacked_widget.addWidget(self.commande_view)
            logger.debug("CommandeView ajoutée.")
        except AttributeError as e:
            logger.exception(f"Erreur: AchatService non trouvé dans MainWindow pour CommandeView. Assurez-vous qu'il est injecté dans main.py. {e}")
            self.commande_view = None
        except Exception as e:
            logger.exception("Erreur création/ajout CommandeView."); self.commande_view = None

        # Mettre l'index 0 (Accueil) comme défaut
        self.stacked_widget.setCurrentIndex(self.VIEW_INDEX_WELCOME)

    def logout(self):
        """Déconnecte l'utilisateur et revient à l'écran de connexion."""
        from PySide6.QtWidgets import QMessageBox
        logger.info(f"Déconnexion de l'utilisateur: {self.current_user.login if self.current_user else 'Invité'}")
        self.show_popup(self.tr("Déconnexion"), self.tr("Vous avez été déconnecté."), QMessageBox.Information)
        self.close()


    def create_actions(self):
        """
        Crée les actions pour les menus en fonction du rôle de l'utilisateur.
        
        Cette méthode implémente le contrôle d'accès basé sur les rôles en vérifiant
        pour chaque fonctionnalité si l'utilisateur connecté dispose des autorisations
        nécessaires. Les actions non autorisées ne sont pas créées ou sont désactivées,
        ce qui permet d'adapter l'interface utilisateur aux droits de chaque utilisateur.
        
        Remarque importante: La fonctionnalité de demande d'intervention doit rester
        accessible à tous les utilisateurs via un bouton bien visible sur l'écran d'accueil,
        permettant aux opérateurs de production de signaler facilement les problèmes.
        Cette fonctionnalité permettra de saisir un texte décrivant le besoin, de choisir 
        la machine concernée et d'indiquer le degré d'urgence.
        """
        logger.debug(f"[create_actions] Rôle utilisateur courant: {self.user_role}")
        
        # La méthode can_access vérifie si le rôle de l'utilisateur a accès à une fonctionnalité donnée
        # Cette vérification est faite pour chaque action de menu
        # --- Fichier ---
        self.home_action = QAction(self.tr("Vue Accueil"), self)
        self.home_action.setStatusTip(self.tr("Revenir à la page d'accueil"))
        self.home_action.triggered.connect(lambda: self.switch_view(self.welcome_view))

        self.exit_action = QAction(self.tr("&Quitter"), self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.setStatusTip(self.tr("Fermer l'application"))
        self.exit_action.triggered.connect(self.close)
        
        # Action À propos (affiche les informations sur l'application)
        self.about_action = QAction(self.tr("À propos"), self)
        self.about_action.setStatusTip(self.tr("Informations sur l'application"))
        self.about_action.triggered.connect(self.show_about_dialog)
        
        # Action de déconnexion (pour le menu utilisateur)
        self.logout_action = QAction(self.tr("Déconnexion"), self)
        self.logout_action.setStatusTip(self.tr("Se déconnecter de l'application"))
        self.logout_action.triggered.connect(self.logout)

        # --- Gestion ---
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Utilisateurs' pour rôle {self.user_role}")

        # Clé: Gérer les Utilisateurs
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Utilisateurs' pour rôle {self.user_role}")
        if can_access("Gérer les Utilisateurs", self.user_role):
            self.manage_users_action = QAction(self.tr("Gérer les Utilisateurs"), self)
            self.manage_users_action.setStatusTip(self.tr("Accéder à la gestion des comptes utilisateurs"))
        else:
            self.manage_users_action = None

        # Clé: Gérer les Machines
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Machines' pour rôle {self.user_role}")
        if can_access("Gérer les Machines", self.user_role):
            self.manage_machines_action = QAction(self.tr("Gérer les Machines"), self)
            self.manage_machines_action.setStatusTip(self.tr("Accéder à la gestion des équipements"))
        else:
            self.manage_machines_action = None

        # Clé: Gérer les OTs
        # DEBUG: Afficher la valeur réelle du rôle avant le test d'accès
        logger.debug(f"[create_actions] Rôle AVANT normalisation: {self.user_role} (type: {type(self.user_role)})")
        # On force la normalisation du rôle pour éviter tout problème de casse ou synonyme
        normalized_role = normalize_role(self.user_role)
        logger.debug(f"[create_actions] Rôle APRÈS normalisation: {normalized_role}")
        if can_access("Gérer les OTs", normalized_role):
            self.manage_ots_action = QAction(self.tr("Gérer les OTs"), self)
            self.manage_ots_action.setStatusTip(self.tr("Accéder à la gestion des OT"))
        else:
            self.manage_ots_action = None

        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Sites' pour rôle {self.user_role}")
        if can_access("Gérer les Sites", self.user_role):
            self.manage_sites_action = QAction(self.tr("Gérer les Sites"), self)
            self.manage_sites_action.setStatusTip(self.tr("Accéder à la gestion des sites géographiques"))
            # Toujours ajouter l'action si le rôle y a accès, mais désactiver si la vue n'existe pas
        else:
            self.manage_sites_action = None

        # Clé: Gérer les Fournisseurs
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Fournisseurs' pour rôle {self.user_role}")
        if can_access("Gérer les Fournisseurs", self.user_role):
            self.manage_fournisseurs_action = QAction(self.tr("Gérer les Fournisseurs"), self)
            self.manage_fournisseurs_action.setStatusTip(self.tr("Accéder à la gestion des fournisseurs"))
        else:
            self.manage_fournisseurs_action = None

        # Clé: Gérer les Pièces Détachées
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Pièces Détachées' pour rôle {self.user_role}")
        if can_access("Gérer les Pièces Détachées", self.user_role):
            self.manage_pieces_action = QAction(self.tr("Gérer les Pièces Détachées"), self)
            self.manage_pieces_action.setStatusTip(self.tr("Accéder à la gestion des pièces détachées"))
        else:
            self.manage_pieces_action = None

        # Clé: Gérer les Gammes d'Entretien
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer les Gammes d'Entretien' pour rôle {self.user_role}")
        if can_access("Gérer les Gammes d'Entretien", self.user_role):
            self.manage_gammes_action = QAction(self.tr("Gérer les Gammes d'Entretien"), self)
            self.manage_gammes_action.setStatusTip(self.tr("Accéder à la gestion des gammes d'entretien"))
        else:
            self.manage_gammes_action = None

        # Clé: Gérer le Stock
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer le Stock' pour rôle {self.user_role}")
        if can_access("Gérer le Stock", self.user_role):
            self.manage_stock_action = QAction(self.tr("Gérer le Stock"), self)
            self.manage_stock_action.setStatusTip(self.tr("Accéder à la gestion du stock"))
        else:
            self.manage_stock_action = None

        # Clé: Configuration
        logger.debug(f"[create_actions] Vérification accès menu 'Configuration' pour rôle {self.user_role}")
        if can_access("Configuration", self.user_role):
            self.manage_config_action = QAction("Configuration", self)
            self.manage_config_action.setStatusTip("Configurer l'application")
        else:
            self.manage_config_action = None

        # Clé: Gérer les Commandes
        logger.debug(f"[create_actions] Vérification accès menu 'Gérer Commandes' pour rôle {self.user_role}")
        if can_access("Gérer Commandes", self.user_role):
            self.manage_commandes_action = QAction(self.tr("Gérer Commandes"), self)
            self.manage_commandes_action.setStatusTip(self.tr("Accéder à la gestion des commandes d'achat"))
        else:
            self.manage_commandes_action = None

        # Menu Fabricants : accessible si droits, mais activé uniquement si la vue existe
        if can_access("Gérer les Fabricants", self.user_role):
            self.manage_fabricants_action = QAction(self.tr("Gérer les Fabricants"), self)
            self.manage_fabricants_action.setStatusTip(self.tr("Accéder à la gestion des fabricants"))
            def show_fabricant_view():
                if hasattr(self, 'fabricant_view') and self.fabricant_view is not None:
                    self.switch_view(self.fabricant_view)
                else:
                    logger.error("[Menu] Impossible d'afficher FabricantView : vue non initialisée ou erreur à la création.")
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Erreur", "La vue Fabricants n'a pas pu être initialisée. Consultez les logs.")
            self.manage_fabricants_action.triggered.connect(show_fabricant_view)
            if hasattr(self, 'fabricant_view') and self.fabricant_view is not None:
                self.manage_fabricants_action.setEnabled(True)
            else:
                self.manage_fabricants_action.setEnabled(False)
        else:
            self.manage_fabricants_action = None

        # --- Bouton Gérer les Sites (même logique que Fabricants) ---
        self.manage_sites_action = QAction(self.tr("Gérer les Sites"), self)
        self.manage_sites_action.setStatusTip(self.tr("Accéder à la gestion des sites géographiques"))
        if hasattr(self, 'site_view') and self.site_view is not None:
            self.manage_sites_action.triggered.connect(lambda: self.switch_view(self.site_view))
            self.manage_sites_action.setEnabled(True)
        else:
            self.manage_sites_action.setEnabled(False)

        self.manage_types_action = QAction(self.tr("Gérer les Types Machine"), self)
        self.manage_types_action.setStatusTip(self.tr("Accéder à la gestion des types de machine"))
        if hasattr(self, 'type_machine_view') and self.type_machine_view is not None:
            self.manage_types_action.triggered.connect(lambda: self.switch_view(self.type_machine_view))
            self.manage_types_action.setEnabled(True)
        else:
            self.manage_types_action.setEnabled(False)

        # Menu Équipes : accessible si droits, mais activé uniquement si la vue existe
        if can_access("Gérer les Équipes", self.user_role):
            self.manage_equipes_action = QAction(self.tr("Gérer les Équipes"), self)
            self.manage_equipes_action.setStatusTip(self.tr("Accéder à la gestion des équipes"))
            def show_equipe_view():
                if hasattr(self, 'equipe_view') and self.equipe_view is not None:
                    self.switch_view(self.equipe_view)
                else:
                    logger.error("[Menu] Impossible d'afficher EquipeView : vue non initialisée ou erreur à la création.")
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Erreur", "La vue Équipes n'a pas pu être initialisée. Consultez les logs.")
            self.manage_equipes_action.triggered.connect(show_equipe_view)
            if hasattr(self, 'equipe_view') and self.equipe_view is not None:
                self.manage_equipes_action.setEnabled(True)
            else:
                self.manage_equipes_action.setEnabled(False)
        else:
            self.manage_equipes_action = None

        self.manage_techniciens_action = QAction(self.tr("Gérer les Techniciens"), self)
        self.manage_techniciens_action.setStatusTip(self.tr("Accéder à la gestion des techniciens"))
        if hasattr(self, 'technicien_view') and self.technicien_view:
            self.manage_techniciens_action.triggered.connect(lambda: self.switch_view(self.technicien_view))
            self.manage_techniciens_action.setEnabled(True)
        else:
            self.manage_techniciens_action.setEnabled(False)

        # Action pour Gérer les Compteurs
        '''
        if can_access("Gérer les Compteurs", self.user_role):
            self.manage_compteurs_action = QAction(self.tr("Gérer les Compteurs"), self)
            self.manage_compteurs_action.setStatusTip(self.tr("Accéder à la gestion des compteurs"))
            self.manage_compteurs_action.triggered.connect(self.show_compteur_dialog)
        else:
            self.manage_compteurs_action = None
        '''
        # Action pour Demande Intervention
        self.demande_intervention_action = QAction(self.tr("Demande Intervention"), self)
        self.demande_intervention_action.setStatusTip(self.tr("Accéder au formulaire de demande d'intervention"))

        # Action pour KPI Machines (nouvelle version)
        self.machine_kpi_action = QAction(self.tr("KPI Machines"), self)
        self.machine_kpi_action.setStatusTip(self.tr("Analyse des performances machines avec graphiques et tendances"))
        self.machine_kpi_action.triggered.connect(self.show_machine_kpi_dialog)

    def create_menu_bar(self):
        """
        Crée la barre de menu de l'application avec contrôle d'accès.
        
        Cette méthode construit l'interface de navigation principale en prenant en compte
        les droits d'accès de l'utilisateur connecté. Seuls les menus pour lesquels
        l'utilisateur possède les permissions appropriées sont affichés.
        
        Remarque: La fonctionnalité de demande d'intervention par la production est
        accessible à tous les utilisateurs via un bouton dans l'écran d'accueil, indépendamment
        de cette barre de menu. Cette fonctionnalité permet aux opérateurs de signaler
        facilement les problèmes via un formulaire simple permettant de décrire le besoin,
        choisir la machine concernée et indiquer le degré d'urgence.
        """
        logger.debug("Création de la barre de menu...")
        # Récupération de la barre de menu Qt (ou création si elle n'existe pas encore)
        menu_bar = self.menuBar()
        lang = getattr(self, 'app_language', None)
        from PySide6.QtWidgets import QWidget, QSizePolicy

        # Menu Fichier
        file_menu = menu_bar.addMenu(self.tr("Fichier"))

        # Add spacing between menus to prevent overlap (fix: use stylesheet for spacing)
        menu_bar.setStyleSheet("QMenuBar::item { padding-left: 18px; padding-right: 18px; }")

        file_menu.addAction(self.home_action)
        file_menu.addSeparator()
        self.change_db_action = QAction(self.tr("Changer la base de données..."), self)
        self.change_db_action.setStatusTip(self.tr("Changer la connexion à la base de données PostgreSQL"))
        self.change_db_action.triggered.connect(self.show_db_connection_dialog)
        file_menu.addAction(self.change_db_action)
        file_menu.addSeparator()
        self.choose_font_action = QAction(self.tr("Choisir la police..."), self)
        self.choose_font_action.setStatusTip(self.tr("Changer la police et la taille de l'application"))
        self.choose_font_action.triggered.connect(self.choose_font)
        file_menu.addAction(self.choose_font_action)
        self.reset_font_action = QAction(self.tr("Réinitialiser la police"), self)
        self.reset_font_action.setStatusTip(self.tr("Restaurer la police par défaut de l'application"))
        self.reset_font_action.triggered.connect(self.reset_font)
        file_menu.addAction(self.reset_font_action)
        self.adapt_resolution_action = QAction(self.tr("Adapter à la résolution"), self)
        self.adapt_resolution_action.setStatusTip(self.tr("Ajuster la taille de la fenêtre à la résolution de l'écran"))
        self.adapt_resolution_action.triggered.connect(self.adapt_to_screen_resolution)
        file_menu.addAction(self.adapt_resolution_action)


        # Séparateur et action pour quitter l'application
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # --- Menu Gestion (simplifié) ---
        # Ce menu regroupe uniquement les fonctionnalités opérationnelles principales
        manage_menu = menu_bar.addMenu(self.tr("Gestion"))

        # Ajout du sous-menu Demande Intervention
        # Création unique de l'action dans create_actions
        if hasattr(self, 'demande_intervention_action') and self.demande_intervention_action:
            manage_menu.addAction(self.demande_intervention_action)

        # Ajout des actions opérationnelles uniquement
        if self.manage_ots_action:
            manage_menu.addAction(self.manage_ots_action)
        
        # Ajout des actions de gestion des gammes si autorisées
        if self.manage_gammes_action and can_access("Gérer les Gammes d'Entretien", self.user_role):
            manage_menu.addAction(self.manage_gammes_action)

        # --- Menu Stock ---
        # Ce menu regroupe les fonctionnalités de gestion des stocks et pièces détachées
        # Important pour la réalisation des interventions de maintenance curative et préventive
        # Les demandes d'intervention créées via le bouton dédié sur l'écran d'accueil
        # pourront être associées à des pièces lors de leur transformation en OT
        if self.manage_pieces_action or self.manage_fournisseurs_action:
            stock_menu = menu_bar.addMenu(self.tr("Stock"))
            
            # Action pour gérer les pièces détachées (références, quantités, seuils d'alerte)
            if self.manage_pieces_action:
                stock_menu.addAction(self.manage_pieces_action)
                
            # Action pour gérer les fournisseurs des pièces détachées
            if self.manage_fournisseurs_action:
                stock_menu.addAction(self.manage_fournisseurs_action)
                
            # Ajout d'un séparateur si l'action de gestion des commandes est disponible
            if self.manage_commandes_action and can_access("Gérer Commandes", self.user_role):
                stock_menu.addSeparator()
                stock_menu.addAction(self.manage_commandes_action)

        # --- Menu KPI & Analyses (menu principal) ---
        # Ce menu regroupe tous les tableaux de bord et analyses de performance
        if hasattr(self, 'machine_kpi_action') and self.machine_kpi_action:
            kpi_menu = menu_bar.addMenu(self.tr(" KPI & Analyses"))
            kpi_menu.setStatusTip("Accéder aux tableaux de bord et analyses de performance")
            
            # KPI Machines (nouvelle version avec graphiques et tendances)
            if hasattr(self, 'machine_kpi_action') and self.machine_kpi_action:
                kpi_menu.addAction(self.machine_kpi_action)
            # Ajout du sous-menu BI Reporting
            # from PySide6.QtWidgets import QAction
            bi_reporting_action = QAction(self.tr("BI Reporting"), self)
            bi_reporting_action.setStatusTip(self.tr("Ouvrir le module de reporting BI"))
            bi_reporting_action.triggered.connect(self.launch_bi_reporting)
            kpi_menu.addSeparator()
            kpi_menu.addAction(bi_reporting_action)
        
        # --- Menu Configuration (menu principal) ---
        # Ce menu regroupe tous les paramètres système et référentiels
        if can_access("Configuration", self.user_role):
            config_menu = menu_bar.addMenu(self.tr("Configuration"))
            config_menu.setStatusTip("Paramètres système et référentiels")
            
            # Gestion des utilisateurs (déplacé depuis Gestion)
            if self.manage_users_action:
                config_menu.addAction(self.manage_users_action)
            
            # Gestion des machines (déplacé depuis Gestion)
            if self.manage_machines_action:
                config_menu.addAction(self.manage_machines_action)
            
            config_menu.addSeparator()
            
            # Action pour gérer les sites géographiques où sont installées les machines
            if self.manage_sites_action:
                config_menu.addAction(self.manage_sites_action)
                
            # Actions pour gérer les fabricants et types de machines
            # Ces actions sont ajoutées même si elles sont désactivées pour une meilleure cohérence
            # Elles seront activées lors de l'implémentation des vues correspondantes
            if hasattr(self, 'manage_fabricants_action'):
                config_menu.addAction(self.manage_fabricants_action)
                
            # Action pour gérer les types de machines (catégories d'équipements)
            if hasattr(self, 'manage_types_action') and self.manage_types_action:
                config_menu.addAction(self.manage_types_action)
                
            # Action pour gérer les équipes (intervenants et groupes de travail)
            if hasattr(self, 'manage_equipes_action'):
                config_menu.addAction(self.manage_equipes_action)
            if hasattr(self, 'manage_techniciens_action') and self.manage_techniciens_action:
                config_menu.addAction(self.manage_techniciens_action)
                
            # Action pour gérer les compteurs des machines
            if hasattr(self, 'manage_compteurs_action') and self.manage_compteurs_action:
                config_menu.addSeparator()
                config_menu.addAction(self.manage_compteurs_action)

        # --- Menu Aide ---
        # Ce menu contient les actions d'assistance et d'information sur l'application
        help_menu = menu_bar.addMenu(self.tr("Aide"))
        help_menu.addAction(self.about_action)
        
        # --- Menu utilisateur (placé à droite) ---
        # Utilisation d'un menu vide pour pousser le menu utilisateur à droite
        spacer_menu = menu_bar.addMenu("")
        spacer_menu.menuAction().setVisible(False)
        
        # Création du menu utilisateur avec le nom et le rôle de l'utilisateur connecté
        # Ce menu permet d'accéder à l'action de déconnexion

        # Note finale: La fonctionnalité de demande d'intervention par la production sera accessible
        # via un bouton bien visible sur l'écran d'accueil (WelcomeView), permettant ainsi
        # à tous les utilisateurs de signaler facilement les problèmes nécessitant une
        # intervention de maintenance. Ces demandes seront stockées dans la table OT
        # avec un statut spécifique (DEMANDE_PROD) et suivront le workflow :
        # création → validation/complétion → transformation en OT officiel.
        
    def show_popup(self, title, message, icon=QMessageBox.Information):
        """Affiche une popup avec la police utilisateur si définie."""
        from PySide6.QtWidgets import QMessageBox
        popup = QMessageBox(self)
        popup.setWindowTitle(title)
        popup.setText(message)
        popup.setIcon(icon)
        if self.current_font:
            popup.setFont(self.current_font)
        popup.exec()

    def show_compteur_dialog(self):
        """Affiche le dialogue de gestion des compteurs d'une machine."""
        from app.ui.dialogs.machine_counters_dialog import MachineCountersDialog
        import logging
        logger = logging.getLogger(__name__)
        
        # Vérifier si nous sommes dans la vue machine
        if not hasattr(self, 'machine_view'):
            self.show_popup("Information", "La vue Machines n'est pas disponible.", QMessageBox.Information)
            return
            
        # Basculer vers la vue machine si ce n'est pas déjà le cas
        if not self.machine_view.isVisible():
            self.switch_view(self.machine_view)
            self.show_popup("Information", "Veuillez sélectionner une machine pour gérer ses compteurs.", QMessageBox.Information)
            return
            
        # Utiliser la méthode _get_selected_machine_object de la vue machine
        selected_machine = self.machine_view._get_selected_machine_object()
        
        # Si aucune machine n'est sélectionnée
        if not selected_machine:
            self.show_popup("Information", "Veuillez d'abord sélectionner une machine dans la vue Machines.", QMessageBox.Information)
            return
            
        logger.debug(f"Machine sélectionnée pour gestion compteurs: ID={selected_machine.id_machine}, Nom={selected_machine.nom}")
        
        # Ouvrir le dialogue complet de gestion des compteurs pour cette machine
        try:
            dialog = MachineCountersDialog(
                machine=selected_machine,
                compteur_service=self.compteur_service,
                current_user=self.current_user,
                parent=self
            )
            
            # Afficher le dialogue (bloquant)
            result = dialog.exec()
            
            # Rafraîchir la vue machine après fermeture du dialogue
            if hasattr(self, 'machine_view') and self.machine_view.isVisible():
                self.machine_view.refresh_machines()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_popup("Erreur", f"Erreur lors de l'ouverture du dialogue des compteurs: {str(e)}", QMessageBox.Critical)
        QApplication.processEvents()  # Permet d'afficher le dialog avant le backup
        dialog.show()
        QApplication.processEvents()
        try:
            # 2. Effectuer le backup
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, 'gmao_data.db')
            if os.path.exists(db_path):
                backup_database(db_path)
                logger.info(f"Sauvegarde automatique terminée ({db_path})")
            else:
                logger.info("Utilisation de PostgreSQL : pas de fichier local à sauvegarder.")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde automatique: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Erreur Backup", f"Erreur lors de la sauvegarde automatique de la base de données :\n{e}")
        finally:
            dialog.close()
        # 3. Fermer proprement la DB
        close_connection()
        logger.info("Application fermée.")

    def show_maintenance_detail_dialog(self):
        """
        Ouvre une boîte de dialogue pour demander l'ID de maintenance, puis affiche la MaintenanceDetailDialog.
        """
        maintenance_id, ok = QInputDialog.getInt(self, self.tr("Maintenance Détail"), self.tr("Entrer l'ID de la maintenance à afficher:"))
        if ok:
            dialog = MaintenanceDetailDialog(maintenance_id, maintenance_service=self.maintenance_service, parent=self)
            dialog.exec()

    def launch_bi_reporting(self):
        """Lance l'application de reporting BI dans un environnement séparé."""
        import subprocess
        import os
        from PySide6.QtWidgets import QMessageBox

        # Définir le chemin vers le script principal du BI Reporting
        bi_reporting_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../Projets/Graph/main.py"))
        try:
            subprocess.Popen(["python", bi_reporting_path])
            self.show_popup("BI Reporting", "L'application de reporting BI a été lancée.", QMessageBox.Information)
        except Exception as e:
            self.show_popup("Erreur", f"Impossible de lancer l'application BI Reporting: {str(e)}", QMessageBox.Critical)

    def show_about_dialog(self):
        """Affiche une boîte de dialogue avec les informations sur l'application."""
        from PySide6.QtWidgets import QMessageBox
        title = self.tr("À propos de GMAO App")
        message = self.tr(
            "<h2>GMAO App</h2>"
            "<p>Application de Gestion de Maintenance Assistée par Ordinateur</p>"
            "<p>Développée avec PySide6 (Qt pour Python)</p>"
            "<p>&copy; 2025 Windsurf Engineering</p>"
        )
        QMessageBox.about(self, title, message)

    def show_kpi_dashboard(self):
        """Affiche le dashboard des KPI financiers modularisé."""
        try:
            from app.ui.kpi.kpi_dashboard_clean import KPIDashboard
            
            # Créer et afficher le dashboard KPI modal
            kpi_dialog = KPIDashboard(parent=self)
            
            # Le dashboard est maintenant modal - pas besoin de resize ni de show()
            # La méthode exec() bloque jusqu'à ce que la fenêtre soit fermée
            result = kpi_dialog.exec()
            
            logger.info("Dashboard KPI fermé")
            
        except ImportError as e:
            logger.error(f"Erreur d'import du dashboard KPI: {e}")
            self.show_popup("Erreur", f"Impossible d'ouvrir le dashboard KPI:\n{str(e)}", QMessageBox.Critical)
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du dashboard KPI: {e}")
            self.show_popup("Erreur", f"Erreur inattendue:\n{str(e)}", QMessageBox.Critical)

    def show_machine_kpi_dialog(self):
        """Affiche le dialog KPI Machines (nouvelle version avec graphiques et tendances)."""
        try:
            from app.kpi.dialogs.machine_kpi_dialog_new import MachineKPIDialogNew
            
            # Créer et afficher le dialog KPI Machines modal
            machine_kpi_dialog = MachineKPIDialogNew(parent=self)
            
            # Dialog modal - la méthode exec() bloque jusqu'à ce que la fenêtre soit fermée
            result = machine_kpi_dialog.exec()
            
            logger.info("Dialog KPI Machines fermé")
            
        except ImportError as e:
            logger.error(f"Erreur d'import du dialog KPI Machines: {e}")
            self.show_popup("Erreur", f"Impossible d'ouvrir le dialog KPI Machines:\n{str(e)}", QMessageBox.Critical)
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du dialog KPI Machines: {e}")
            self.show_popup("Erreur", f"Erreur inattendue:\n{str(e)}", QMessageBox.Critical)

    # Les méthodes show_kpi_* spécialisées ont été supprimées.

    def _connect_view_actions(self):
        """
        Connecte les actions des menus aux méthodes des différentes vues.
        
        Cette méthode est cruciale pour la navigation dans l'application car elle crée les
        liens entre les éléments de menu et les vues correspondantes. Elle gère également
        les erreurs potentielles en désactivant les actions dont les vues n'ont pas pu être
        créées correctement.
        
        Remarque: La vue d'accueil (WelcomeView) doit inclure un bouton bien visible
        pour les demandes d'intervention par la production. Cette fonctionnalité permet
        de saisir un texte décrivant le besoin, choisir la machine concernée et
        indiquer le degré d'urgence. Ces demandes sont ensuite stockées dans la table OT
        avec un type spécifique et validées/complétées par le responsable maintenance.
        """
        logger.debug("Connexion des actions aux vues...")

        # Connexion de l'action Demande Intervention
        if hasattr(self, 'demande_intervention_action') and self.demande_intervention_action is not None:
            self.demande_intervention_action.triggered.connect(self.open_intervention_request_dialog)
            self.demande_intervention_action.setEnabled(True)

        # --- Connexion des actions du menu Administration ---
        # Connexion de l'action Gérer Utilisateurs à la vue utilisateurs (Phase 1)
        if self.manage_users_action and hasattr(self, 'user_view') and self.user_view is not None:
            # La vue existe, on connecte l'action pour basculer vers cette vue
            self.manage_users_action.triggered.connect(lambda: self.switch_view(self.user_view))
            logger.debug("Action 'Gérer Utilisateurs' connectée.")
            self.manage_users_action.setEnabled(True)
        elif self.manage_users_action is not None:
            # La vue n'existe pas (erreur dans setup_views), on désactive l'action
            # pour éviter des erreurs lors de l'utilisation de l'application
            self.manage_users_action.setEnabled(False)
            logger.warning("Action 'Gérer Utilisateurs' désactivée: vue non disponible.")


        # --- Connexion de l'action Gérer Machines à la vue machines ---
        # Cette action permet d'accéder à la gestion du parc machines et équipements
        logger.debug(f"Vérification pour connecter action Gérer Machines. self.machine_view = {self.machine_view}")
        
        # Vérification que l'action et la vue existent
        if self.manage_machines_action and hasattr(self, 'machine_view') and self.machine_view is not None:
            # Connexion de l'action au changement de vue via une fonction lambda
            # Lambda permet de passer des paramètres à la méthode switch_view lors de son appel
            self.manage_machines_action.triggered.connect(lambda: self.switch_view(self.machine_view))
            logger.debug("Action 'Gérer Machines' connectée.")
            self.manage_machines_action.setEnabled(True)
            
            # Gestion spéciale pour le service des compteurs
            # Si le service des compteurs n'est pas disponible, on ajoute une info-bulle explicative
            # pour informer l'utilisateur que cette fonctionnalité est limitée
            if hasattr(self.machine_view, 'compteur_service') and self.machine_view.compteur_service is None:
                self.manage_machines_action.setToolTip(self.tr("La gestion des machines est accessible, mais la gestion des compteurs est désactivée (service manquant)."))
            else:
                # Sinon on supprime tout tooltip existant
                self.manage_machines_action.setToolTip("")
        elif self.manage_machines_action is not None:
            # Afficher une info à l'utilisateur si la vue machine n'est pas disponible
            from PySide6.QtWidgets import QMessageBox
            logger.warning(f"CONDITION FAUSSE: Action 'Gérer Machines' désactivée. self.machine_view = {self.machine_view}")
            self.manage_machines_action.setEnabled(False)
            # Affichage différée pour éviter popup au démarrage, mais on log bien la cause
            # QMessageBox.warning(self, "Erreur", "La vue Machines n'a pas pu être initialisée. Vérifiez les logs pour le détail.")
            # Conseil debug: Vérifiez les exceptions dans setup_views (MachineView)

        # Connecter les actions pour les autres vues ici, DANS LE BON ORDRE si VIEW_INDEX_xx est utilisé par switch_view
        # Sinon, switch_view utilise indexOf, l'ordre n'est pas strict ici, juste que la vue DOIT exister.
        if self.manage_ots_action and hasattr(self, 'ot_view') and self.ot_view is not None:
            self.manage_ots_action.triggered.connect(lambda: self.switch_view(self.ot_view))
            logger.debug("Action 'Gérer OTs' connectée.")
            self.manage_ots_action.setEnabled(True) # Activer si connexion OK
        elif self.manage_ots_action is not None:
            self.manage_ots_action.setEnabled(False)

        if self.manage_sites_action:
            if hasattr(self, 'site_view') and self.site_view is not None:
                self.manage_sites_action.triggered.connect(lambda: self.switch_view(self.site_view))
                logger.debug("Action 'Gérer Sites' connectée.")
                self.manage_sites_action.setEnabled(True)
            else:
                logger.warning("L'action 'Gérer les Sites' est affichée mais désactivée car la vue SiteView n'existe pas.")
                self.manage_sites_action.setEnabled(False)

        # Connexion de l'action 'Gérer les Fabricants'
        if self.manage_fabricants_action and hasattr(self, 'fabricant_view') and self.fabricant_view is not None:
            self.manage_fabricants_action.triggered.connect(lambda: self.switch_view(self.fabricant_view))
            logger.debug("Action 'Gérer Fabricants' connectée.")
            self.manage_fabricants_action.setEnabled(True)
        elif self.manage_fabricants_action is not None:
            self.manage_fabricants_action.setEnabled(False)

        if self.manage_fournisseurs_action is not None and hasattr(self, 'fournisseur_view') and self.fournisseur_view is not None:
            self.manage_fournisseurs_action.triggered.connect(lambda: self.switch_view(self.fournisseur_view))
            logger.debug("Action 'Gérer Fournisseurs' connectée.")
            self.manage_fournisseurs_action.setEnabled(True)
        elif self.manage_fournisseurs_action is not None:
            self.manage_fournisseurs_action.setEnabled(False)


        if self.manage_pieces_action is not None and hasattr(self, 'piece_view') and self.piece_view is not None:
            self.manage_pieces_action.triggered.connect(lambda: self.switch_view(self.piece_view))
            logger.debug("Action 'Gérer Pièces' connectée.")
            self.manage_pieces_action.setEnabled(True)
        elif self.manage_pieces_action is not None:
            self.manage_pieces_action.setEnabled(False)


        if self.manage_gammes_action is not None and hasattr(self, 'gamme_view') and self.gamme_view is not None:
            self.manage_gammes_action.triggered.connect(lambda: self.switch_view(self.gamme_view))
            logger.debug("Action 'Gérer Gammes' connectée.")
            self.manage_gammes_action.setEnabled(True)
        elif self.manage_gammes_action is not None:
            self.manage_gammes_action.setEnabled(False)

        # Connexion de l'action 'Gérer les Types Machine'
        if self.manage_types_action is not None and hasattr(self, 'type_machine_view') and self.type_machine_view is not None:
            self.manage_types_action.triggered.connect(lambda: self.switch_view(self.type_machine_view))
            logger.debug("Action 'Gérer Types Machine' connectée.")
            self.manage_types_action.setEnabled(True)
        elif self.manage_types_action is not None:
            self.manage_types_action.setEnabled(False)

        # Connexion de l'action 'Gérer les Équipes'
        if self.manage_equipes_action is not None and hasattr(self, 'equipe_view') and self.equipe_view is not None:
            self.manage_equipes_action.triggered.connect(lambda: self.switch_view(self.equipe_view))
            logger.debug("Action 'Gérer Équipes' connectée.")
            self.manage_equipes_action.setEnabled(True)
        elif self.manage_equipes_action is not None:
            self.manage_equipes_action.setEnabled(False)

        # Connexion de l'action 'Gérer les Techniciens'
        if self.manage_techniciens_action is not None and hasattr(self, 'technicien_view') and self.technicien_view is not None:
            self.manage_techniciens_action.triggered.connect(lambda: self.switch_view(self.technicien_view))
            logger.debug("Action 'Gérer Techniciens' connectée.")
            self.manage_techniciens_action.setEnabled(True)
        elif self.manage_techniciens_action is not None:
            self.manage_techniciens_action.setEnabled(False)

        # --- Connecter les actions de la Phase 7 (Commandes) ---
        if self.manage_commandes_action is not None and hasattr(self, 'commande_view') and self.commande_view is not None:
            self.manage_commandes_action.triggered.connect(lambda: self.switch_view(self.commande_view))
            logger.debug("Action 'Gérer Commandes' connectée.")
            self.manage_commandes_action.setEnabled(True) # Activer l'action
        elif self.manage_commandes_action is not None:
            self.manage_commandes_action.setEnabled(False)

        logger.debug("Connexions des actions de vue terminées.")