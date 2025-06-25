
# gmao_app/main.py
"""
Point d'entrée principal de l'application GMAO.
Initialise les composants clés et lance l'interface graphique.
"""

# Importation des modules nécessaires
import logging
import sys  # Pour interagir avec le système (ex. : arguments, sortie)
import os
from typing import Optional, Dict
from clean_project import clean_project  # Ajout pour nettoyage automatique

# Import des modules de traduction
from app import i18n  # Import du module i18n pour les traductions
from app.config import app_config  # Import de la configuration de l'application

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,  # Affiche tous les messages DEBUG et supérieurs
    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.warning(f"[main.py] Niveau effectif du root logger: {logging.getLogger().getEffectiveLevel()}")

# Dictionnaire de correspondance entre les langues de l'interface et les codes de langue
LANGUAGE_MAPPING = {
    "Français": i18n.Language.FRENCH,
    "Anglais": i18n.Language.ENGLISH,
    "Allemand": i18n.Language.GERMAN,
    "Espagnol": i18n.Language.SPANISH,
    "Italien": i18n.Language.ITALIAN
}
import os  # Pour les opérations sur le système de fichiers
from typing import Optional  # Pour le typage des variables pouvant être None
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog, QWidget  # Pour l'interface graphique
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import QTranslator, Qt

# ... le reste de ton code ...

# --- Configuration initiale ---
# Normalement, pas besoin de modifier le répertoire de travail si l'application est lancée depuis la racine.

try:
    # 1. Configuration du logging (toujours en premier)
    logger = logging.getLogger(__name__)  # Création d'un logger pour ce fichier
    logger.warning(f"[main.py] Niveau effectif du root logger: {logging.getLogger().getEffectiveLevel()}")

    # 2. Import des composants UI (Fenêtre principale)
    from app.ui.main_window import MainWindow  # Import de la fenêtre principale de l'application

    # 3. Import des composants Data Access (Connexion et tous les Repositories)
    # Ces modules gèrent l'accès à la base de données et les opérations CRUD.
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
        app_temp = QApplication([])
        QMessageBox.critical(None, "Erreur d'Importation", f"Impossible de charger un module nécessaire:\n{e}\n\nL'application va se fermer.")
    except Exception:
        pass
    sys.exit(1)  # Quitte l'application avec un code d'erreur

def show_welcome_screen(app) -> Optional[str]:
    """
    Affiche l'écran d'accueil pour sélectionner la langue.
    Retourne la langue sélectionnée ou None si l'utilisateur a annulé.
    """
    try:
        from accueil import AccueilWindow
        
        # Créer et configurer la fenêtre d'accueil
        welcome = AccueilWindow()
        welcome.setWindowTitle("GMAO Industrielle - Sélection de la langue")
        welcome.setWindowIcon(QIcon("app/ui/resources/icons/app_icon.png"))
        welcome.setWindowFlags(welcome.windowFlags() & ~Qt.WindowCloseButtonHint)
        
        # Variable pour stocker la langue sélectionnée
        selected_language = None
        
        # Connecter le bouton GMAO pour définir la langue et fermer
        def on_gmao_clicked():
            nonlocal selected_language
            selected_language = welcome.lang_combo.currentText()
            welcome.close()
            
        welcome.btn_gmao.clicked.connect(on_gmao_clicked)
        
        # Afficher la fenêtre d'accueil
        welcome.show()
        app.exec()
        
        return selected_language
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'écran d'accueil: {e}")
        return None

# Fonction principale de l'application
def main():
    """Fonction principale pour lancer l'application."""
    logger.info(f"--- Démarrage GMAO Industrielle v{APP_VERSION} ---")  # Log du démarrage

    # Créer une seule instance de QApplication
    app = QApplication(sys.argv)

    # Afficher l'écran d'accueil pour sélectionner la langue
    selected_lang = show_welcome_screen(app)
    if not selected_lang:
        logger.warning("Aucune langue sélectionnée. Utilisation du français par défaut.")
        selected_lang = "Français"
    
    # Configurer la langue de l'application
    from app.config import app_config
    app_config.language = LANGUAGE_MAPPING[selected_lang]
    logger.info(f"Langue sélectionnée: {selected_lang}")

    login_dialog = None  # Initialisation de la variable pour gérer les erreurs liées au LoginDialog
    logged_in_user: Optional[Utilisateur] = None

    try:

        # --- 0. Nettoyage du projet avant initialisation DB ---
        clean_project()
        # --- 1. Connexion DB & Initialisation ---
        db_connection = get_connection() # Établit la connexion
        initialize_database() # Crée les tables si nécessaire

        # --- 2. Injection de dépendances (instanciation) ---
        # Instanciation des repositories (accès aux données)
        logger.debug("Instanciation des Repositories...")
        user_repo = UserRepository()
        site_repo = SiteRepository()
        fab_repo = FabricantRepository()
        type_repo = TypeMachineRepository()
        machine_repo = MachineRepository()
        equipe_repo = EquipeRepository()
        tech_repo = TechnicienRepository()
        ot_repo = OrdreTravailRepository()
        maint_repo = MaintenanceRepository()
        # Ajouts Phase 4
        fours_repo = FournisseurRepository()
        piece_repo = PieceRepository()
        ip_repo = InterventionPieceRepository() # <-- Nouveau Repo
        mvt_stock_repo = MouvementStockRepository() # <-- Nouveau Repo
        # Ajouts Phase 6
        gamme_repo = GammeEntretienRepository()
        etape_repo = GammeEtapeRepository()
        gpt_repo = GammePieceTypeRepository()

        # Ajouts Phase 7
        commande_repo = CommandeRepository()
        ligne_commande_repo = LigneCommandeRepository()
        compteur_repo = CompteurRepository() # <-- Instanciez le REPO
        historique_compteur_repo = HistoriqueCompteurRepository() # <-- Instanciez le REPO
        
        # Ajouts Phase 11 - Gestion Financière
        maintenance_intervenant_repo = MaintenanceIntervenantRepository()
        maintenance_frais_externe_repo = MaintenanceFraisExterneRepository()

        logger.debug("Repositories instanciés.")

        # Instanciation des services (logique métier)
        logger.debug("Instanciation des Services...")
        stock_service = StockService(piece_repo, fours_repo, mvt_stock_repo) # Needs repos first
        user_service = UserService(user_repo)
        machine_service = MachineService(machine_repo, site_repo, fab_repo, type_repo)
       

        # Ajouts Phase 7
        # --- Instanciation AchatService ---
        achat_service = AchatService(
            commande_repo=commande_repo,
            ligne_commande_repo=ligne_commande_repo,
            piece_repo=piece_repo,
            mouvement_stock_repo=mvt_stock_repo
        )


        # --- AJOUT : Vérifier/Créer l'admin initial ---
        logger.debug("Vérification de l'existence de l'admin initial...")
        user_service.ensure_admin_exists() # Utilise les logins/mdp par défaut définis DANS le service
        # ---------------------------------------------

        
        # --- Instanciation des services de maintenance ---
        maintenance_service = MaintenanceService(
            ot_repo=ot_repo,
            maint_repo=maint_repo,
            tech_repo=tech_repo,
            equipe_repo=equipe_repo,
            machine_repo=machine_repo,
            ip_repo=ip_repo,
            stock_service=stock_service,
            mi_repo=maintenance_intervenant_repo,    # Ajout du repo des intervenants
            mfe_repo=maintenance_frais_externe_repo  # Ajout du repo des frais externes
        )
        
        preventive_service = PreventiveMaintenanceService(
            gamme_repo=gamme_repo,
            etape_repo=etape_repo,
            piece_type_repo=gpt_repo,
            type_machine_repo=type_repo,
            user_repo=user_repo,
            piece_repo=piece_repo,
            ot_repo=ot_repo,
            machine_repo=machine_repo,
        )

        compteur_service = CompteurService(
            compteur_repo=compteur_repo,
            historique_compteur_repo=historique_compteur_repo,
            machine_repo=machine_repo, # <- machine_repo doit être instancié AVANT
            user_repo=user_repo, # <- user_repo doit être instancié AVANT
            maintenance_service=maintenance_service # <-- Injection du service maintenance
        )

        # Service financier (Phase 11)
        finance_service = FinanceService(
            maintenance_repo=maint_repo,
            intervenant_repo=maintenance_intervenant_repo,
            frais_repo=maintenance_frais_externe_repo,
            intervention_piece_repo=ip_repo,
            piece_repo=piece_repo
        )

        # ---- Dépendance Inverse ----
        maintenance_service.set_preventive_service(preventive_service)
        logger.debug("Services prêts.") # Consolidated logging

        # --- 3. Configuration de la langue ---
        from app.config import app_config, Language
        
        # Définir la langue de l'application (par défaut: français)
        app_config.language = Language.FRENCH  # ou Language.ENGLISH, etc.
        
        logger.debug("Configuration QApplication...")
        app.setFont(QFont("Arial", 14))  # Police de base
        
        # --- Traduction globale ---
        if app_config.language != Language.FRENCH:  # Si ce n'est pas le français par défaut
            from PySide6.QtCore import QTranslator, QCoreApplication
            
            # Chemin vers les traductions (ex: 'en_translations' pour l'anglais)
            translations_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                f'{app_config.language.value}_translations'
            ))
            
            translators = []
            translation_files = [
                f"{app_config.language.value}.qm",  # Fichier de traduction principal
                "ot_view.qm", "ot_dialog.qm", "main_window.qm", 
                "welcome_view.qm", "fabricant_view.qm", "fabricant_dialog.qm", 
                "site_dialog.qm", "site_view.qm", "type_machine_dialog.qm",
                "type_machine_view.qm", "technicien_dialog.qm", "technicien_view.qm", 
                "user_dialog.qm", "user_view.qm", "machine_dialog.qm", 
                "machine_view.qm", "equipe_dialog.qm", "equipe_view.qm", 
                "commande_view.qm", "commande_dialog.qm"
            ]
            
            for qm_file in translation_files:
                translator = QTranslator()
                qm_path = qm_file if os.path.isabs(qm_file) else os.path.join(translations_path, qm_file)
                loaded = translator.load(qm_path)
                
                logger.debug(f"Chargement traduction: {qm_path} => {loaded}")
                if loaded:
                    app.installTranslator(translator)
                    translators.append(translator)
                else:
                    logger.warning(f"Impossible de charger le fichier de traduction: {qm_path}")
            
            # Pour le débogage
            if logger.isEnabledFor(logging.DEBUG):
                from PySide6.QtCore import QCoreApplication
                print(f"\n=== Test des traductions (langue: {app_config.language.value}) ===")
                print("TR TEST (EquipeDialog):", QCoreApplication.translate("EquipeDialog", "Ajouter Équipe"))
                print("TR TEST (EquipeView):", QCoreApplication.translate("EquipeView", "Ajouter Équipe"))
                print("TR TEST (FabricantDialog):", QCoreApplication.translate("FabricantDialog", "Ajouter Fabricant"))
                print("TR TEST (FabricantDialog - Field):", QCoreApplication.translate("FabricantDialog", "Nom (*):"))
                print("="*50 + "\n")
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
            # Passer l'utilisateur connecté ou son ID à MainWindow
            logged_in_user=logged_in_user, # Ou logged_in_user_id=logged_in_user.id_utilisateur                    
            compteur_service=compteur_service,
            finance_service=finance_service,  # Ajout du service financier
            app_language=app_config.language.value  # Utilisation de la configuration centralisée
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
        if app is None:
            app = QApplication([])
        QMessageBox.critical(None, "Erreur Base de Données", f"Impossible de se connecter ou d'utiliser la base de données:\n{e}\n\nVérifiez la configuration et le fichier DB.")
        sys.exit(1)
    except NameError as e:
        # Gestion des erreurs de nom (ex. : import manquant ou faute de frappe)
        logger.critical(f"Erreur de Nom (Import manquant ou faute de frappe?): {e}", exc_info=True)
        if app is None:
            app = QApplication([])
        QMessageBox.critical(None, "Erreur de Programmation", f"Un nom nécessaire n'a pas été trouvé:\n{e}\n\nVérifiez les imports et les noms de variables/classes.")
        sys.exit(1)
    except Exception as e:
        # Gestion des erreurs inattendues
        logger.critical(f"Erreur fatale non gérée dans main: {e}", exc_info=True)
        if app is None:
            app = QApplication([])
        QMessageBox.critical(None, "Erreur Inattendue", f"Une erreur critique est survenue:\n{e}\n\nL'application va se fermer. Consultez les logs.")
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
        from config import APP_NAME, APP_VERSION
    except ImportError:
        APP_NAME = "GMAO App"
        APP_VERSION = "?"

    main()  # Appelle la fonction principale