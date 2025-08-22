
# gmao_app/main.py
"""
Point d'entrée principal de l'application GMAO.
Initialise les composants clés et lance l'interface graphique.

Ce fichier est la colonne vertébrale de l'application et suit une architecture à plusieurs couches :
- UI (main_window.py, vues) : Interface utilisateur
- Services : Contiennent la logique métier et orchestrent les opérations
- Repositories : Gèrent l'accès aux données dans PostgreSQL
- Modèles : Représentent les entités métier

Le flux de démarrage est le suivant :
1. Configuration du logging et import des modules
2. Sélection de la langue via AccueilWindow
3. Connexion à PostgreSQL et initialisation du schéma
4. Injection des dépendances (repositories puis services)
5. Authentification utilisateur via LoginDialog
6. Création et affichage de la fenêtre principale (MainWindow)
7. Démarrage de la boucle d'événements Qt
"""

# Configuration du chemin pour permettre les imports depuis le répertoire parent
import sys
import os
# Ajouter le répertoire parent au sys.path pour résoudre les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importation des modules nécessaires
import sys  # Pour interagir avec le système (ex. : arguments, sortie)
import logging  # Pour la gestion des logs et la traçabilité des actions
from clean_project import clean_project  # Module pour nettoyer les fichiers .pyc et __pycache__

# Configuration unique du système de logging
# Cette configuration s'applique à tous les loggers de l'application
logging.basicConfig(
    level=logging.DEBUG,  # Niveau DEBUG (10) capture tous les niveaux de messages (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'  # Format détaillé avec horodatage, module, ligne et niveau
)
# Affiche le niveau effectif du logger racine (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)
print(f"DEBUG? {logging.getLogger().getEffectiveLevel()}")

# Ces imports sont placés après la configuration du logging pour bénéficier du système de logs
import os  # Pour les opérations sur le système de fichiers
from typing import Optional  # Pour le typage des variables pouvant être None
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog  # Pour l'interface graphique
from PySide6.QtGui import QFont
from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QPushButton, QHBoxLayout, QFrame  # et tout autre widget utilisé

# ... le reste de ton code ...

# --- Configuration initiale ---
# Normalement, pas besoin de modifier le répertoire de travail si l'application est lancée depuis la racine.

try:
    # 1. Configuration du logging spécifique au module main
    # La création d'un logger nommé permet une identification précise dans les logs
    logger = logging.getLogger(__name__)  # __name__ sera '__main__' quand le script est exécuté directement
    logger.warning(f"[main.py] Niveau effectif du root logger: {logging.getLogger().getEffectiveLevel()}")

    # 2. Import des composants UI (Fenêtre principale)
    # Importé ici plutôt qu'au début pour éviter les imports circulaires potentiels
    # et accélérer le démarrage initial de l'application
    from app.ui.main_window import MainWindow  # MainWindow est le conteneur principal de l'UI

    # 3. Import des composants Data Access (Connexion et tous les Repositories)
    # La couche d'accès aux données est basée sur le pattern Repository
    # Chaque entité a son propre repository qui encapsule les opérations CRUD
    # L'accès à PostgreSQL est centralisé dans le module database.py
    from app.data.database import get_connection, close_connection, initialize_database, DatabaseError
    from app.data.repositories.user_repository import UserRepository
    from app.data.repositories.site_repository import SiteRepository
    from app.data.repositories.fabricant_repository import FabricantRepository
    from app.data.repositories.type_machine_repository import TypeMachineRepository
    from app.data.repositories.machine_repository import MachineRepository
    from app.data.repositories.equipe_repository import EquipeRepository
    from app.data.repositories.technicien_repository import TechnicienRepository
    from app.data.repositories.ordre_travail_repository import OrdreTravailRepository
    from app.data.repositories.maintenance_repository import MaintenanceRepository
    from app.data.repositories.fournisseur_repository import FournisseurRepository # <- Phase 4
    from app.data.repositories.piece_repository import PieceRepository           # <- Phase 4
    from app.data.repositories.intervention_piece_repository import InterventionPieceRepository
    from app.data.repositories.mouvement_stock_repository import MouvementStockRepository # <- Ajout
    from app.data.repositories.gamme_entretien_repository import GammeEntretienRepository
    from app.data.repositories.gamme_etape_repository import GammeEtapeRepository
    from app.data.repositories.gamme_piece_type_repository import GammePieceTypeRepository
    from app.data.repositories.commande_repository import CommandeRepository
    from app.data.repositories.ligne_commande_repository import LigneCommandeRepository
    from app.data.repositories.compteur_repository import CompteurRepository # <-- Assurez-vous d'importer le REPO
    from app.data.repositories.historique_compteur_repository import HistoriqueCompteurRepository # <-- Assurez-vous d'importer le REPO
    from app.data.repositories.maintenance_intervenant_repository import MaintenanceIntervenantRepository
    from app.data.repositories.maintenance_frais_externe_repository import MaintenanceFraisExterneRepository
    from app.core.services.compteur_service import CompteurService
    from app.core.services.finance_service import FinanceService  # Ajout du service financier
          
    # Ajouter les futurs repositories ici...

    # 4. Import des composants Core (Tous les Services)
    # Les services contiennent la logique métier et orchestrent les opérations.
    from app.core.services.machine_service import MachineService
    from app.core.services.maintenance_service import MaintenanceService
    from app.core.services.stock_service import StockService  # Import StockService
    from app.core.services.preventive_service import PreventiveMaintenanceService  # Corrected module name
    from app.core.services.achat_service import AchatService
    from app.core.services.user_service import UserService
    from app.ui.dialogs.login_dialog import LoginDialog # <-- Importer le dialogue
    from app.core.models.utilisateur import Utilisateur # <-- Importer le modèle
    
    # Ajouter les futurs services ici...

except ImportError as e:
    # Gestion des erreurs d'importation critiques
    print(f"[ERREUR CRITIQUE IMPORT] {e}. Vérifiez la structure du projet, les noms des fichiers/classes, et les fichiers '__init__.py'.", file=sys.stderr)
    import traceback
    traceback.print_exc()  # Affiche la pile d'erreurs pour le diagnostic
    try:
        # Affiche une boîte de dialogue pour informer l'utilisateur
        from PySide6.QtWidgets import QApplication
        app_temp = QApplication.instance() or QApplication([])
        QMessageBox.critical(None, "Erreur d'Importation", f"Impossible de charger un module nécessaire:\n{e}\n\nL'application va se fermer.")
    except Exception:
        pass
    sys.exit(1)  # Quitte l'application avec un code d'erreur

# Fonction principale de l'application
def main():
    """
    Fonction principale pour lancer l'application.
    
    Cette fonction orchestre toute l'initialisation de l'application:
    1. Sélection de la langue via AccueilWindow
    2. Connexion à PostgreSQL et initialisation du schéma
    3. Initialisation des repositories et services (injection de dépendances)
    4. Authentification utilisateur
    5. Création et affichage de la fenêtre principale
    6. Démarrage de la boucle d'événements Qt
    """
    # Imports locaux pour éviter les dépendances circulaires et accélérer le démarrage
    from app.config import APP_NAME, APP_VERSION  # Import des configurations de base
    from app.config import app_config, Language  # Import des configurations et de l'énumération des langues
    # Import de AccueilWindow supprimé car la sélection de langue n'est plus utilisée.
    from PySide6.QtWidgets import QApplication  # Import local de QApplication
    
    # Log du démarrage de l'application avec sa version
    logger.info(f"--- Démarrage GMAO Industrielle v{APP_VERSION} ---")

    # Création de l'application Qt (doit être fait avant toute création de widget)
    # sys.argv permet de passer des arguments en ligne de commande à l'application Qt
    # Vérifier si une instance QApplication existe déjà
    app = QApplication.instance() or QApplication(sys.argv)
    
    # --- Phase 1: Configuration de la langue via argument ---
    import argparse
    parser = argparse.ArgumentParser(description="Lancement de l'application GMAO.")
    parser.add_argument("--lang", type=str, default="Anglais", help="Langue de l'application (ex: Français, Anglais)")
    # Parse les arguments connus, ignore les autres (comme ceux de Qt)
    args, unknown = parser.parse_known_args()
    selected_language_str = args.lang

    # Mapping des noms de langue vers l'énumération Language
    language_map = {
        "Français": Language.FRENCH,
        "Anglais": Language.ENGLISH,
        "Allemand": Language.GERMAN,
        "Espagnol": Language.SPANISH,
        "Italien": Language.ITALIAN
    }
    
    # Utiliser le mapping, avec l'anglais comme valeur par défaut
    app_language_enum = language_map.get(selected_language_str, Language.ENGLISH)

    global APP_LANGUAGE
    APP_LANGUAGE = app_language_enum
    app_config.language = app_language_enum
    logger.info(f"Langue sélectionnée: {selected_language_str} -> {app_config.language.name} (code: {app_config.language.value})")

    # --- Chargement du traducteur Qt pour l'anglais ---
    from PySide6.QtCore import QTranslator
    import os
    
    lang_code = app_config.language.value  # ex: 'fr', 'en', etc.
    # Construction du chemin absolu pour le dossier de traduction basé sur le dossier du script main.py
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # gmao_app_PostGres
    qm_path = os.path.join(base_dir, f"{lang_code}_translations", f"{lang_code}.qm")
    translator = QTranslator()
    if translator.load(qm_path):
        app.installTranslator(translator)
        logger.info(f"Traduction chargée : {qm_path}")
    else:
        logger.warning(f"Impossible de charger la traduction : {qm_path}")
    
    # Le log de la langue sélectionnée a été intégré au bloc de configuration de la langue par défaut.
    
    # --- Phase 2: Initialisation de la base de données et des repositories ---

    # Variables préparées pour l'authentification utilisateur et la gestion des erreurs
    login_dialog = None  # Initialisation de la variable pour gérer les erreurs liées au LoginDialog
    logged_in_user: Optional[Utilisateur] = None  # Variable pour stocker l'utilisateur authentifié
    # Ne pas réinitialiser app à None ici car elle est déjà créée plus haut

    try:
        # --- Préparation et initialisation de la base de données PostgreSQL ---
        
        # Nettoyage des fichiers .pyc et __pycache__ pour éviter les problèmes de cache Python
        # Particulièrement utile après des mises à jour de code
        clean_project()
        
        # Établissement de la connexion PostgreSQL
        # La fonction get_connection() utilise les paramètres de config.py ou les variables d'environnement
        # Elle retourne une connexion psycopg2 avec RealDictCursor pour des résultats au format dictionnaire
        db_connection = get_connection()
        
        # Initialisation du schéma de la base de données
        # Crée les tables, contraintes et triggers si nécessaire
        # Cette fonction est idempotente (peut être appelée plusieurs fois sans conséquence)
        initialize_database()

        # --- Architecture basée sur l'injection de dépendances ---
        # Le pattern d'injection de dépendances permet:
        # 1. Un découplage des composants pour faciliter les tests
        # 2. Une meilleure lisibilité des dépendances
        # 3. Une modification facile des implémentations

        # --- Étape 1: Instanciation des repositories ---
        # Chaque repository encapsule les opérations CRUD pour une entité métier
        logger.debug("Instanciation des Repositories...")
        
        # Repositories de base (gestion des utilisateurs, sites, équipes et machines)
        user_repo = UserRepository()
        site_repo = SiteRepository()
        fab_repo = FabricantRepository()
        type_repo = TypeMachineRepository()
        machine_repo = MachineRepository()
        equipe_repo = EquipeRepository()
        tech_repo = TechnicienRepository()
        
        # Repositories pour la maintenance
        ot_repo = OrdreTravailRepository()  # Ordres de travail
        maint_repo = MaintenanceRepository()  # Interventions de maintenance
        
        # Repositories pour la gestion des stocks et pièces (Phase 4)
        fours_repo = FournisseurRepository()  # Fournisseurs
        piece_repo = PieceRepository()  # Pièces
        ip_repo = InterventionPieceRepository()  # Association maintenance-pièces
        mvt_stock_repo = MouvementStockRepository()  # Mouvements de stock
        
        # Repositories pour la maintenance préventive (Phase 6)
        gamme_repo = GammeEntretienRepository()  # Gammes d'entretien
        etape_repo = GammeEtapeRepository()  # Étapes des gammes
        gpt_repo = GammePieceTypeRepository()  # Types de pièces par gamme

        # Repositories pour les achats et compteurs (Phase 7)
        commande_repo = CommandeRepository()  # Commandes
        ligne_commande_repo = LigneCommandeRepository()  # Lignes de commande
        compteur_repo = CompteurRepository()  # Compteurs machines
        historique_compteur_repo = HistoriqueCompteurRepository()  # Historique des relèves
        
        # Repositories pour la gestion financière (Phase 11)
        maintenance_intervenant_repo = MaintenanceIntervenantRepository()  # Intervenants sur maintenance
        maintenance_frais_externe_repo = MaintenanceFraisExterneRepository()  # Frais externes

        # Journalisation de la fin d'instanciation des repositories
        logger.debug("Repositories instanciés avec succès.")
        
        # --- Étape 2: Instanciation des services métier ---

        # Instanciation des services (logique métier)
        # Les services contiennent la logique métier et orchestrent les opérations
        # Ils utilisent les repositories pour accéder aux données
        logger.debug("Instanciation des Services...")
        
        # --- Services de base ---
        
        # Service de gestion du stock
        # Gère les opérations de stock: mouvements, inventaire, seuils d'alerte
        stock_service = StockService(
            piece_repository=piece_repo,  # Repository des pièces
            fournisseur_repository=fours_repo,  # Repository des fournisseurs
            mouvement_stock_repository=mvt_stock_repo  # Repository des mouvements de stock
        )
        
        # Service de gestion des utilisateurs
        # Gère les opérations sur les utilisateurs: authentification, droits d'accès
        user_service = UserService(user_repo)
        
        # Service de gestion des machines
        # Gère le parc machines et ses dépendances (sites, fabricants, types)
        machine_service = MachineService(
            machine_repository=machine_repo,
            site_repository=site_repo,
            fabricant_repository=fab_repo,
            type_machine_repository=type_repo
        )
       
        # Service d'achat (Phase 7)
        # Gère le processus d'achat: commandes, réception, suivi
        achat_service = AchatService(
            commande_repo=commande_repo,       # Repository des commandes
            ligne_commande_repo=ligne_commande_repo,  # Repository des lignes de commande
            piece_repo=piece_repo,            # Repository des pièces
            mouvement_stock_repo=mvt_stock_repo  # Repository des mouvements de stock
        )

        # --- Étape supplémentaire: Vérification de l'existence d'un administrateur ---
        # Garantit qu'un compte administrateur existe toujours dans le système
        # Crée un compte par défaut si aucun admin n'existe
        logger.debug("Vérification de l'existence de l'admin initial...")
        user_service.ensure_admin_exists()  # Méthode du service utilisateur qui vérifie/crée un admin par défaut
        # ---------------------------------------------

        # --- Services spécialisés ---
        
        # Service de maintenance curative
        # Gère les interventions de maintenance, ordres de travail et équipes
        maintenance_service = MaintenanceService(
            ot_repo=ot_repo,                  # Repository des ordres de travail
            maint_repo=maint_repo,            # Repository des interventions
            tech_repo=tech_repo,              # Repository des techniciens
            equipe_repo=equipe_repo,          # Repository des équipes
            machine_repo=machine_repo,        # Repository des machines
            ip_repo=ip_repo,                  # Repository des pièces utilisées en intervention
            stock_service=stock_service,       # Service de gestion du stock (injection de service)
            mi_repo=maintenance_intervenant_repo,    # Repository des intervenants (interne/externe)
            mfe_repo=maintenance_frais_externe_repo  # Repository des frais externes
        )
        
        # Service de maintenance préventive
        # Gère les plans de maintenance planifiée et la génération d'OT préventifs
        preventive_service = PreventiveMaintenanceService(
            gamme_repo=gamme_repo,           # Repository des gammes d'entretien
            etape_repo=etape_repo,           # Repository des étapes de gamme
            piece_type_repo=gpt_repo,        # Repository des types de pièces par gamme
            type_machine_repo=type_repo,     # Repository des types de machines
            user_repo=user_repo,             # Repository des utilisateurs
            piece_repo=piece_repo,           # Repository des pièces
            ot_repo=ot_repo,                 # Repository des ordres de travail
            machine_repo=machine_repo,       # Repository des machines
        )

        # Service de gestion des compteurs machines
        # Gère les compteurs (heures, cycles, etc.) et déclenche les OT basés sur seuils
        compteur_service = CompteurService(
            compteur_repo=compteur_repo,                 # Repository des compteurs
            historique_compteur_repo=historique_compteur_repo,  # Repository de l'historique
            machine_repo=machine_repo,                  # Repository des machines (dépendance)
            user_repo=user_repo,                        # Repository des utilisateurs (dépendance)
            maintenance_service=maintenance_service     # Service de maintenance (injection de service)
        )

        # Service de gestion financière (Phase 11)
        # Gère les aspects financiers des interventions (coûts, MOD, pièces, frais externes)
        finance_service = FinanceService(
            maintenance_repo=maint_repo,                  # Repository des interventions
            intervenant_repo=maintenance_intervenant_repo,  # Repository des intervenants
            frais_repo=maintenance_frais_externe_repo,     # Repository des frais externes
            intervention_piece_repo=ip_repo,              # Repository des pièces utilisées
            piece_repo=piece_repo                         # Repository des pièces
        )

        # Injection du service financier dans MaintenanceService (pour calculs de coûts)
        # CRITIQUE: Cette injection doit être faite AVANT toute utilisation de maintenance_service
        maintenance_service.set_finance_service(finance_service)

        # ---- Résolution de la dépendance circulaire ----
        # Utilisation du pattern d'injection par setter pour résoudre une dépendance circulaire
        # maintenance_service a besoin de preventive_service et vice-versa
        maintenance_service.set_preventive_service(preventive_service)
        
        # Tous les services sont maintenant instanciés et configurés
        logger.debug("Services métier instanciés et prêts.")

        # --- 3. Configuration QApplication et traduction globale (après choix langue) ---
        logger.debug("Configuration QApplication...")
        app.setFont(QFont("Arial", 14))  # Change "Arial" et 14 selon tes besoins

        if app_config.language != Language.FRENCH:
            from PySide6.QtCore import QTranslator, QCoreApplication
            translations_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f'{app_config.language.value}_translations')
            translators = []
            # Liste complète et unique de tous les fichiers .qm nécessaires
            translation_files = [
                f"{app_config.language.value}.qm",
                "ot_view.qm", "ot_dialog.qm", "main_window.qm",
                "welcome_view.qm", "fabricant_view.qm", "fabricant_dialog.qm",
                "site_dialog.qm", "site_view.qm", "type_machine_dialog.qm",
                "type_machine_view.qm", "technicien_dialog.qm", "technicien_view.qm", "user_dialog.qm", "user_view.qm",
                "machine_dialog.qm", "machine_view.qm", "equipe_dialog.qm", "equipe_view.qm", "commande_view.qm", "commande_dialog.qm",
                "gamme_dialog.qm", "gamme_etape_dialog.qm", "gamme_view.qm", 
                "piece_dialog.qm", "piece_view.qm", "piece_reference_dialog.qm", "piece_selection_dialog.qm",
                "stock_adjustment_dialog.qm", "fournisseur_dialog.qm", 
                "fournisseur_view.qm", "reception_dialog.qm", "maintenance_detail_dialog.qm", "maintenance_detail_view.qm",
                "maintenance_report_dialog.qm", "db_connection_dialog.qm",
                "frais_externe_dialog.qm", "intervenant_dialog.qm", "finance_couts_widget.qm", "maintenance_couts_widget.qm",
                "maintenance_pieces_widget.qm", "historique_compteur_dialog.qm", "historique_compteur_view.qm", "compteur_dialog.qm",
                "machine_counters_dialog.qm", "login_dialog.qm", "intervention_request_view.qm"
            ]
            # Utilise un set pour éviter les doublons éventuels
            for qm_file in dict.fromkeys(translation_files):
                translator = QTranslator()
                qm_path = qm_file if os.path.isabs(qm_file) else os.path.join(translations_path, qm_file)
                loaded = translator.load(qm_path)
                logger.debug(f"Loading translation: {qm_path} => {loaded}")
                if loaded:
                    app.installTranslator(translator)
                    translators.append(translator)
                else:
                    logger.warning(f"Could not load translation file: {qm_path}")
            '''# (Optionnel) Test console
            print("TR TEST (EquipeDialog):", QCoreApplication.translate("EquipeDialog", "Ajouter Équipe"))
            print("TR TEST (EquipeView):", QCoreApplication.translate("EquipeView", "Ajouter Équipe"))
            print("TR TEST (FabricantDialog):", QCoreApplication.translate("FabricantDialog", "Ajouter Fabricant"))
            print("TR TEST (FabricantDialog - Field):", QCoreApplication.translate("FabricantDialog", "Nom (*):"))
            print("TR TEST:", QCoreApplication.translate("GammeView", "Lancement de la recherche des gammes échues et création des OT correspondants.\n    Ceci peut prendre quelques instants..."))
            print("TR TEST:", QCoreApplication.translate("GammeView", "{len_created_ots} OT préventifs ont été générés."))
            print("TR TEST:", QCoreApplication.translate("GammeView", "\n    Rafraîchissez la vue des Ordres de Travail pour les voir."))
            print("TR TEST:", QCoreApplication.translate("GammeView", "Une erreur est survenue:\n    {e}"))
            print("TR TEST (FournisseurView):", QCoreApplication.translate("FournisseurView", "Ajouter Fournisseur"))
            '''
           
        logger.debug("Création MainWindow...")
        # Injection des services dans la fenêtre principale

        # --- Authentification utilisateur ---
        login_dialog = LoginDialog(user_service)
        result = login_dialog.exec()
        if result == QDialog.Accepted:
            logged_in_user = login_dialog.authenticated_user  # or the correct attribute/method
            if logged_in_user is None:
                logger.critical("Aucun utilisateur authentifié après le login.")
                sys.exit(1)
        else:
            logger.warning("L'utilisateur a annulé la connexion. Fermeture de l'application.")
            sys.exit(0)


        logger.debug(f"Création MainWindow pour l'utilisateur ID {logged_in_user.id_utilisateur}...")
        main_window = MainWindow(
            user_service=user_service,
            machine_service=machine_service,
            maintenance_service=maintenance_service,
            stock_service=stock_service,
            preventive_service=preventive_service,
            achat_service=achat_service,
            logged_in_user=logged_in_user,
            compteur_service=compteur_service,
            finance_service=finance_service,
            app_language=app_config.language.value
        )
        logger.debug("Affichage MainWindow...")
        main_window.show()  # Affiche la fenêtre principale

        # --- 4. Démarrage boucle d'événements ---
        logger.info("Application démarrée. Démarrage boucle d'événements Qt...")
        exit_code = app.exec()  # Démarre la boucle d'événements Qt
        logger.info(f"Application terminée avec le code: {exit_code}")
        sys.exit(exit_code)  # Quitte l'application avec le code de sortie

    except DatabaseError as e:
        # Gestion des erreurs liées à la base de données
        logger.critical(f"Impossible de démarrer: Erreur de base de données - {e}", exc_info=True)
        try:
            # Vérifier si une instance QApplication existe déjà
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Erreur Base de Données", f"Impossible de se connecter ou d'utiliser la base de données:\n{e}\n\nVérifiez la configuration et le fichier DB.")
        except Exception:
            print(f"Erreur de base de données: {e}", file=sys.stderr)
        sys.exit(1)
    except NameError as e:
        # Gestion des erreurs de nom (ex. : import manquant ou faute de frappe)
        logger.critical(f"Erreur de Nom (Import manquant ou faute de frappe?): {e}", exc_info=True)
        try:
            # Vérifier si une instance QApplication existe déjà
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Erreur de Programmation", f"Un nom nécessaire n'a pas été trouvé:\n{e}\n\nVérifiez les imports et les noms de variables/classes.")
        except Exception:
            print(f"Erreur de nom: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Gestion des erreurs inattendues
        logger.critical(f"Erreur fatale non gérée dans main: {e}", exc_info=True)
        try:
            # Vérifier si une instance QApplication existe déjà
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Erreur Inattendue", f"Une erreur critique est survenue:\n{e}\n\nL'application va se fermer. Consultez les logs.")
        except Exception as ex:
            logger.error(f"Erreur lors de l'affichage du message d'erreur: {ex}")
            print(f"Erreur critique: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Fermeture de la connexion à la base de données
        logger.info("Fermeture de la connexion DB...")
        close_connection()
        logger.info("--- Fin Application ---")

# Point d'entrée du script
if __name__ == "__main__":
    # Importer la configuration pour afficher le nom et la version de l'application
    try:
        from app.config import APP_NAME, APP_VERSION
    except ImportError:
        APP_NAME = "GMAO App"
        APP_VERSION = "1.0"

    main()  # Appelle la fonction principale