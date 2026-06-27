"""
Widget pour afficher et gérer la liste des Machines.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QLabel, QLineEdit, QComboBox, # Ajouts pour filtres
    QSpacerItem, QSizePolicy, QDialog, QDateEdit, QDateTimeEdit
)
from PySide6.QtCore import Qt, Slot, QDate, QDateTime
from typing import TYPE_CHECKING,Optional, List, Dict, Any
from datetime import date

# Importer modèles, services et dialogue
from app.core.models.machine import Machine
from app.core.services.machine_service import MachineService # Service principal
from app.ui.dialogs.machine_dialog import MachineDialog
# Import du futur dialogue (même s'il n'existe pas encore)
from app.ui.dialogs.machine_counters_dialog import MachineCountersDialog
from app.utils.exceptions import BusinessLogicError, NotFoundError, DatabaseError
from app.core.services.compteur_service import CompteurService


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
     from app.ui.main_window import MainWindow # Importer pour le type hinting

class MachineView(QWidget):
    """Vue pour la gestion des Machines."""

    def __init__(self, machine_service: MachineService, main_window: "MainWindow"):
        """Initialise la vue."""
        super().__init__(main_window)
        self.machine_service = machine_service
        self.main_window = main_window # Stocker la référence à MainWindow

        # --- Maintenant, accéder au compteur_service via self.main_window ---
        if hasattr(self.main_window, 'compteur_service'):
            self.compteur_service = self.main_window.compteur_service
        else:
            self.compteur_service = None
            logger.warning("CompteurService non disponible dans MachineView: le bouton 'Gérer Compteurs' sera désactivé mais la vue reste accessible.")
        # -------------------------------------------------------------------
        self.current_machines: list[Machine] = [] 

        logger.debug("Initialisation de MachineView...")

        # --- Widgets de Filtre (optionnel mais utile) ---
        self.filter_nom_input = QLineEdit(placeholderText=self.tr("Filtrer par nom/serial..."))
        self.filter_site_combo = QComboBox()
        self.filter_type_combo = QComboBox()
        self.filter_etat_combo = QComboBox()
        self.clear_filters_button = QPushButton(self.tr("Effacer Filtres"))

        self._populate_filter_combos() # Charger les listes pour les filtres

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(self.tr("Filtres:")))
        filter_layout.addWidget(self.filter_nom_input)
        filter_layout.addWidget(QLabel(self.tr("Site:")))
        filter_layout.addWidget(self.filter_site_combo)
        filter_layout.addWidget(QLabel(self.tr("Type:")))
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addWidget(QLabel(self.tr("État:")))
        filter_layout.addWidget(self.filter_etat_combo)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addStretch()

        # --- Widgets Principaux ---
        self.table_widget = QTableWidget(self)
        self.setup_table()

        self.add_button = QPushButton(self.tr("Ajouter Machine"))
        self.edit_button = QPushButton(self.tr("Modifier Machine"))
        self.delete_button = QPushButton(self.tr("Supprimer Machine"))
        self.refresh_button = QPushButton(self.tr("Rafraîchir"))
        self.manage_counters_button = QPushButton(self.tr("Gérer Compteurs"))
        # Switch général pour OT auto
        from app.config import AUTO_OT_ENABLED
        from PySide6.QtWidgets import QCheckBox
        self.auto_ot_checkbox = QCheckBox(self.tr("OT Auto"))
        self.auto_ot_checkbox.setChecked(AUTO_OT_ENABLED)
        self.auto_ot_checkbox.setToolTip(self.tr("Déclenchement automatique des OT préventifs/urgents via compteur"))
        self.auto_ot_checkbox.stateChanged.connect(self._on_auto_ot_switch_changed)

        # --- Layouts ---
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.manage_counters_button)
        button_layout.addWidget(self.auto_ot_checkbox)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(filter_layout) # Ajout des filtres en haut
        main_layout.addWidget(self.table_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- Connexions ---
        self.connect_signals()

        # --- État initial & chargement données ---
        self._update_button_states()
        self.refresh_machines()

        logger.debug("MachineView initialisée.")

    def _on_auto_ot_switch_changed(self, state):
        """Active/désactive le déclenchement auto des OT (runtime seulement)."""
        # Variable globale runtime (module-level)
        import config
        config.AUTO_OT_ENABLED = bool(state)
        logger.info(f"Déclenchement auto OT {'activé' if state else 'désactivé'} (runtime)")

    def setup_table(self):
        """Configure la table des machines."""
        # ID(0,hid), Nom(1), Site(2), Type(3), Etat(4), Serial(5), Criticite(6), Install(7)
        self.table_widget.setColumnCount(8)
        self.table_widget.setHorizontalHeaderLabels([
            self.tr("ID"), 
            self.tr("Nom"), 
            self.tr("Site"), 
            self.tr("Type"), 
            self.tr("État"), 
            self.tr("N° Série"), 
            self.tr("Criticité"), 
            self.tr("Date Install.")
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True) # Meilleure lisibilité
        self.table_widget.setSortingEnabled(True) # Activer tri par colonne

        self.table_widget.setColumnHidden(0, True) # Cacher ID technique

        # Ajuster colonnes
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Site
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Type
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Etat
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Serial
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Criticite
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Date

        # Connecter le tri
        self.table_widget.horizontalHeader().sectionClicked.connect(self.sort_table)
        self._sort_column = 1 # Colonne Nom par défaut
        self._sort_order = Qt.SortOrder.AscendingOrder

    def _populate_filter_combos(self):
        """ Remplit les combobox de filtre (Site, Type, Etat). """
        try:
            # Sites
            self.filter_site_combo.clear()
            self.filter_site_combo.addItem(self.tr("Tous"), userData=None)
            sites = self.machine_service.get_all_sites()
            for site in sites:
                self.filter_site_combo.addItem(site.nom, userData=site.id_site)

            # Types
            self.filter_type_combo.clear()
            self.filter_type_combo.addItem(self.tr("Tous"), userData=None)
            types = self.machine_service.get_all_type_machines()
            for tm in types:
                 display_text = f"{tm.categorie} - {tm.nom}" if tm.categorie else tm.nom
                 self.filter_type_combo.addItem(display_text, userData=tm.id_type_machine)

            # États (pour l'instant, en dur)
            self.filter_etat_combo.clear()
            self.filter_etat_combo.addItem(self.tr("Tous"), userData=None)
            # Associer chaque label traduit à la valeur d'origine (français) attendue par la base
            etats = [
                (self.tr("Inconnu"), "Inconnu"),
                (self.tr("En service"), "En service"),
                (self.tr("Arrêt planifié"), "Arrêt planifié"),
                (self.tr("En panne"), "En panne"),
                (self.tr("En maintenance"), "En maintenance"),
                (self.tr("Hors service"), "Hors service"),
            ]
            for label, value in etats:
                self.filter_etat_combo.addItem(label, userData=value)


        except BusinessLogicError as e:
            logger.error(f"Erreur chargement données filtres MachineView: {e}")
            # Ne pas bloquer, mais informer
            QMessageBox.warning(self, self.tr("Erreur Filtres"),
            self.tr("Impossible de charger les listes pour les filtres:") + f"\n{e}")

    def connect_signals(self):
        """Connecte les signaux."""
        self.add_button.clicked.connect(self.add_machine)
        self.edit_button.clicked.connect(self.edit_machine)
        self.delete_button.clicked.connect(self.delete_machine)
        self.refresh_button.clicked.connect(self.refresh_machines)
        self.manage_counters_button.clicked.connect(self._on_manage_counters)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)
        self.table_widget.doubleClicked.connect(self.edit_machine)

        # Signaux des filtres
        self.filter_nom_input.textChanged.connect(self.apply_filters) # Appliquer filtre en direct
        self.filter_site_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_type_combo.currentIndexChanged.connect(self.apply_filters)
        self.filter_etat_combo.currentIndexChanged.connect(self.apply_filters)
        self.clear_filters_button.clicked.connect(self.clear_filters)


    # Dans app/ui/views/machine_view.py

    # Assurez-vous d'avoir cette méthode helper pour récupérer l'objet sélectionné
    def _get_selected_machine_object(self) -> Optional[Machine]:
        """ Retourne l'objet Machine complet sélectionné, ou None. """
        # Il faut une méthode _get_selected_machine_id pour obtenir l'ID d'abord
        selected_id = self._get_selected_machine_id() # <-- Assurez-vous que cette méthode existe et est correcte (récupère ID depuis table)
        if selected_id is None:
            # Clear cached object if no selection
            if hasattr(self, 'current_machine'): self.current_machine = None
            return None

        # Si l'objet Machine actuel en cache correspond à l'ID sélectionné, on le retourne
        if hasattr(self, 'current_machine') and self.current_machine and self.current_machine.id_machine == selected_id:
             return self.current_machine

        # Sinon, récupérer l'objet depuis le service
        try:
            self.current_machine = self.machine_service.get_machine_by_id(selected_id) # <-- Assurez-vous que cette méthode existe dans MachineService
            return self.current_machine
        except Exception as e:
             logger.error(f"Erreur récupération machine ID {selected_id}: {e}")
             self.current_machine = None
             return None


    # --- REMPLACER VOTRE MÉTHODE _update_button_states SIMPLE PAR CELLE-CI ---
    @Slot() # type: ignore
    def _update_button_states(self):
        """ Active/désactive les boutons selon la sélection ET les droits. """
        logger.debug("Début _update_button_states dans MachineView...")
        # 1. Récupérer l'objet Machine sélectionné et vérifier la sélection
        selected_machine = self._get_selected_machine_object() # Récupère l'objet (et le met en cache localement)
        has_selection = selected_machine is not None

        # 2. Récupérer l'utilisateur et son rôle (via MainWindow)
        user_role = "Inconnu"
        current_user = None
        if hasattr(self.main_window, 'current_user') and self.main_window.current_user:
             current_user = self.main_window.current_user
             user_role = current_user.role
        else:
             # Ce cas ne devrait plus arriver si login+injection est OK, mais sécurité
             logger.error("_update_button_states: Impossible de récupérer l'objet/rôle utilisateur.")
             # Optionnel : désactiver tous les boutons ici par sécurité si pas d'utilisateur

        # 3. Définir les permissions pour cette vue/ces boutons (Exemples de règles métier)
        can_create = user_role in ['Admin', 'RespMaint'] # Qui peut ajouter une machine
        can_edit_delete = user_role in ['Admin', 'RespMaint'] # Qui peut modifier/supprimer machines
        allowed_manage_counters_roles = ['Admin', 'RespMaint'] # Qui peut gérer les paramètres des compteurs
        can_manage_counters = user_role in allowed_manage_counters_roles
        can_add_releve_elsewhere = user_role in ['Admin', 'Technicien'] # Qui peut saisir un relevé (action qui sera dans le dialogue compteur)

        logger.debug(
            f"DEBUG Compteurs: has_selection={has_selection}, "
            f"can_manage_counters={can_manage_counters}, "
            f"service_is_available={self.compteur_service is not None}, "
            f"user_role={user_role}, selected_machine={selected_machine}"
        )

        # 2. Récupérer l'utilisateur et son rôle (via MainWindow)
        user_role = "Inconnu"
        current_user = None
        if hasattr(self.main_window, 'current_user') and self.main_window.current_user:
             current_user = self.main_window.current_user
             user_role = current_user.role
        else:
             # Ce cas ne devrait plus arriver si login+injection est OK, mais sécurité
             logger.error("_update_button_states: Impossible de récupérer l'objet/rôle utilisateur.")
             # Optionnel : désactiver tous les boutons ici par sécurité si pas d'utilisateur

        # 3. Définir les permissions pour cette vue/ces boutons (Exemples de règles métier)
        can_create = user_role in ['Admin', 'RespMaint'] # Qui peut ajouter une machine
        can_edit_delete = user_role in ['Admin', 'RespMaint'] # Qui peut modifier/supprimer machines
        allowed_manage_counters_roles = ['Admin', 'RespMaint'] # Qui peut gérer les paramètres des compteurs
        can_manage_counters = user_role in allowed_manage_counters_roles
        can_add_releve_elsewhere = user_role in ['Admin', 'Technicien'] # Qui peut saisir un relevé (action qui sera dans le dialogue compteur)

        # 4. Définir l'état d'activation de CHAQUE bouton
        # Bouton "Ajouter Machine" : dépend des droits
        self.add_button.setEnabled(can_create)
        self.add_button.setToolTip("" if can_create else self.tr("Droits insuffisants"))

        # Boutons "Modifier" et "Supprimer" : dépendent de la sélection ET des droits
        self.edit_button.setEnabled(has_selection and can_edit_delete)
        self.edit_button.setToolTip("" if (has_selection and can_edit_delete) else (self.tr("Sélectionnez une machine") if not has_selection else self.tr("Droits insuffisants")))
        self.delete_button.setEnabled(has_selection and can_edit_delete)
        self.delete_button.setToolTip("" if (has_selection and can_edit_delete) else (self.tr("Sélectionnez une machine") if not has_selection else self.tr("Droits insuffisants")))


        # Bouton "Gérer Compteurs" : dépend de la sélection ET des droits ET si le service compteur est injecté
        # Assurez-vous que self.compteur_service est bien injecté et not None dans __init__
        service_is_available = self.compteur_service is not None
        self.manage_counters_button.setEnabled(has_selection and can_manage_counters and service_is_available)
        self.manage_counters_button.setToolTip(
    "" if (has_selection and can_manage_counters and service_is_available)
    else (
        self.tr("Sélectionnez une machine") if not has_selection
        else (self.tr("Service Compteur non disponible") if not service_is_available
        else self.tr("Droits insuffisants") + f" (Rôle: {user_role})")
    )
) # Tooltip plus détaillé


        # Bouton "Rafraîchir" : toujours actif
        self.refresh_button.setEnabled(True)
        self.refresh_button.setToolTip("")


        logger.debug("Fin _update_button_states dans MachineView.")
    # ----------------------------------------------------------------------
    def _get_selected_machine_id(self) -> Optional[int]:
        """Retourne l'ID de la machine sélectionnée."""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        logger.debug(f"_get_selected_machine_id: rows={selected_rows}")
        if not selected_rows: return None
        id_item = self.table_widget.item(selected_rows[0].row(), 0) # Colonne ID (cachée)
        logger.debug(f"_get_selected_machine_id: id_item={id_item}")
        return int(id_item.data(Qt.ItemDataRole.UserRole)) if id_item else None

    @Slot()
    def refresh_machines(self):
        """Recharge les machines en appliquant les filtres et le tri actuels."""
        logger.info("Rafraîchissement de la liste des machines...")
        filters = self._get_current_filters()
        sort_column_name = self._get_sort_column_name()
        sort_desc = self._sort_order == Qt.SortOrder.DescendingOrder

        try:
            # Utiliser get_all avec filtres et tri
            self.current_machines = self.machine_service.get_all_machines(
                filters=filters,
                sort_by=sort_column_name,
                sort_desc=sort_desc
            )
            self.populate_table(self.current_machines) # Appeler fonction séparée pour peupler
            logger.info(f"{len(self.current_machines)} machines affichées après filtres/tri.")

        except BusinessLogicError as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"), self.tr("Impossible de charger les machines:") + f"\n{e}")
            logger.error(f"Erreur métier chargement machines: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue:\n{e}")
            logger.exception("Erreur inattendue chargement/affichage machines.")

    def populate_table(self, machines: List[Machine]):
         """ Remplit la table avec la liste de machines fournie. """
         # Désactiver temporairement le tri pour éviter problèmes lors du remplissage
         self.table_widget.setSortingEnabled(False)
         self.table_widget.setRowCount(len(machines))

         # Pré-charger les noms des références pour efficacité
         # (Évite appels répétitifs au service dans la boucle)
         sites_map = {s.id_site: s.nom for s in self.machine_service.get_all_sites()}
         types_map = {t.id_type_machine: (f"{t.categorie} - {t.nom}" if t.categorie else t.nom)
                      for t in self.machine_service.get_all_type_machines()}

         for row_index, machine in enumerate(machines):
             # ID (caché)
             id_item = QTableWidgetItem(str(machine.id_machine))
             id_item.setData(Qt.ItemDataRole.UserRole, machine.id_machine)
             self.table_widget.setItem(row_index, 0, id_item)

             # Autres colonnes
             self.table_widget.setItem(row_index, 1, QTableWidgetItem(machine.nom or ""))
             # Utiliser les maps pour afficher les noms des FK
             self.table_widget.setItem(row_index, 2, QTableWidgetItem(sites_map.get(machine.site_id, "N/A")))
             self.table_widget.setItem(row_index, 3, QTableWidgetItem(types_map.get(machine.type_machine_id, "N/A")))
             self.table_widget.setItem(row_index, 4, QTableWidgetItem(machine.etat or ""))
             self.table_widget.setItem(row_index, 5, QTableWidgetItem(machine.serial or ""))
             self.table_widget.setItem(row_index, 6, QTableWidgetItem(machine.criticite or ""))
             date_install_str = machine.date_installation.strftime('%Y-%m-%d') if machine.date_installation else ""
             self.table_widget.setItem(row_index, 7, QTableWidgetItem(date_install_str))

         self._update_button_states()
         # Réactiver le tri
         self.table_widget.setSortingEnabled(True)
         # Restaurer l'indicateur de tri sur l'en-tête
         self.table_widget.horizontalHeader().setSortIndicator(self._sort_column, self._sort_order)


    @Slot(int)
    def sort_table(self, logical_index: int):
        """ Slot appelé quand l'utilisateur clique sur un en-tête de colonne. """
        if self._sort_column == logical_index:
             # Inverse l'ordre si on clique sur la même colonne
             self._sort_order = Qt.SortOrder.DescendingOrder if self._sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
             # Nouvelle colonne, tri ascendant par défaut
             self._sort_column = logical_index
             self._sort_order = Qt.SortOrder.AscendingOrder

        # Rafraîchir les données avec le nouveau tri
        self.refresh_machines()

    def _get_sort_column_name(self) -> str:
         """ Traduit l'index logique de colonne en nom de champ pour le tri DB. """
         # Doit correspondre à l'ordre des colonnes dans setup_table et aux noms de champ dans MachineRepository/DB
         column_map = {
             # 0: "id_machine", # ID caché
             1: "nom",
             2: "site_id", # Tri par ID pour l'instant, joindre pour tri par nom serait mieux
             3: "type_machine_id", # Idem
             4: "etat",
             5: "serial",
             6: "criticite",
             7: "date_installation"
         }
         return column_map.get(self._sort_column, "nom") # Défaut sur "nom"


    @Slot()
    def apply_filters(self):
        """ Slot pour rafraîchir la table quand un filtre change. """
        # Utiliser un QTimer pour éviter rafraîchissements trop fréquents si frappe rapide?
        # Pour l'instant, rafraîchit immédiatement.
        self.refresh_machines()

    def _get_current_filters(self) -> Dict[str, Any]:
        """ Construit le dictionnaire de filtres basé sur l'état des widgets de filtre. """
        filters = {}
        nom_filter = self.filter_nom_input.text().strip()
        if nom_filter:
            # Filtrer sur nom OU serial avec LIKE
            # Ceci n'est pas directement géré par le repo actuel, besoin d'adapter
            # Pour l'instant, filtrons juste sur nom
             filters['nom'] = f"%{nom_filter}%" # Utilise LIKE
             # Ou faire recherche côté Python après get_all si LIKE complexe non supporté?

        site_id = self.filter_site_combo.currentData()
        if site_id is not None:
            filters['site_id'] = site_id

        type_id = self.filter_type_combo.currentData()
        if type_id is not None:
            filters['type_machine_id'] = type_id

        etat = self.filter_etat_combo.currentData()
        if etat is not None:
            filters['etat'] = etat

        return filters

    @Slot()
    def clear_filters(self):
        """ Réinitialise tous les filtres et rafraîchit. """
        self.filter_nom_input.clear()
        self.filter_site_combo.setCurrentIndex(0) # "Tous"
        self.filter_type_combo.setCurrentIndex(0) # "Tous"
        self.filter_etat_combo.setCurrentIndex(0) # "Tous"
        self.refresh_machines() # Appliquer (donc sans filtres)


    @Slot()
    def add_machine(self):
        """ Ouvre le dialogue pour ajouter une machine. """
        logger.debug("Ouverture dialogue ajout machine.")
        # Le dialogue a besoin du service pour charger ses propres ComboBox
        dialog = MachineDialog(machine_service=self.machine_service, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            machine_data = dialog.get_machine_data()
            try:
                logger.info(f"Tentative création machine via service: {machine_data.get('nom')}")
                self.machine_service.create_machine(machine_data)
                QMessageBox.information(self, self.tr("Succès"), self.tr("Machine '{nom}' créée avec succès.").format(nom=machine_data.get('nom'))) # OK
                self.refresh_machines() # Mettre à jour la liste
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Création"), self.tr("Impossible de créer la machine:\n{err}").format(err=e))
                 logger.error(f"Échec création machine: {e}")
            except Exception as e:
                 QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue:\n{e}")
                 logger.exception(f"Erreur inattendue création machine.")


    @Slot()
    def edit_machine(self):
        """ Ouvre le dialogue pour modifier la machine sélectionnée. """
        machine_id = self._get_selected_machine_id()
        if machine_id is None:
             QMessageBox.warning(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner une machine à modifier."))
             return

        try:
            machine_to_edit = self.machine_service.get_machine_by_id(machine_id)
            if not machine_to_edit:
                 QMessageBox.warning(self, self.tr("Erreur"), self.tr("La machine sélectionnée n'existe plus."))
                 self.refresh_machines()
                 return

            logger.debug(f"Ouverture dialogue édition pour machine ID: {machine_id}")
            dialog = MachineDialog(machine_service=self.machine_service, machine=machine_to_edit, parent=self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_data = dialog.get_machine_data()
                # L'ID est déjà dans update_data si mode édition
                try:
                    logger.info(f"Tentative màj machine ID {machine_id} via service.")
                    updated_machine = self.machine_service.update_machine(machine_id, update_data)
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Machine '{nom}' mise à jour.").format(nom=updated_machine.nom))
                    self.refresh_machines()
                except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                     QMessageBox.warning(self, self.tr("Erreur Mise à Jour"), self.tr("Impossible de mettre à jour:\n{err}").format(err=e))
                     logger.error(f"Échec màj machine ID {machine_id}: {e}")
                     self.refresh_machines()
                except Exception as e:
                     QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue:\n{e}")
                     logger.exception(f"Erreur inattendue màj machine ID {machine_id}'.")

        except (BusinessLogicError, NotFoundError) as e:
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger la machine pour modification:\n{err}").format(err=e))
             self.refresh_machines()
        except Exception as e:
             QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue:\n{e}")
             logger.exception(f"Erreur inattendue avant dialogue édition machine ID {machine_id}'.")


    @Slot()
    def delete_machine(self):
        """ Supprime la machine sélectionnée après confirmation. """
        machine_id = self._get_selected_machine_id()
        if machine_id is None:
             QMessageBox.warning(self, self.tr("Aucune Sélection"), self.tr("Veuillez sélectionner une machine à supprimer."))
             return

        machine = self.machine_service.get_machine_by_id(machine_id)
        nom = machine.nom if machine else f"ID {machine_id}"

        reply = QMessageBox.question(
            self,
            self.tr("Confirmation Suppression"),
            self.tr("Êtes-vous sûr de vouloir supprimer la machine '{nom}'?\nCette action peut échouer si elle est référencée (OT, Maintenance...).").format(nom=nom),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.warning(f"Tentative suppression machine ID {machine_id} via service.")
                success = self.machine_service.delete_machine(machine_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Machine '{nom}' supprimée.").format(nom=nom))
                    self.refresh_machines()
            except (BusinessLogicError, DatabaseError, NotFoundError) as e:
                 QMessageBox.warning(self, self.tr("Erreur Suppression"), self.tr("Impossible de supprimer la machine:\n{err}").format(err=e))
                 logger.error(f"Échec suppression machine ID {machine_id}: {e}")
                 self.refresh_machines()
            except Exception as e:
                 QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue:\n{e}")
                 logger.exception(f"Erreur inattendue suppression machine ID {machine_id}'.")


    @Slot() # type: ignore
    def _on_manage_counters(self):
        """ Ouvre le dialogue pour gérer les compteurs de la machine sélectionnée. """
        # S'assurer que la machine sélectionnée et le service Compteur sont disponibles
        selected_machine = self._get_selected_machine_object() # Appelle une méthode pour récupérer l'objet Machine
        if not selected_machine: # Vérifie si _get_selected_machine_object a réussi
             logger.warning("Action Gérer Compteurs sans machine sélectionnée.")
             QMessageBox.warning(self, self.tr("Action Impossible"), self.tr("Veuillez sélectionner une machine pour gérer ses compteurs."))
             self._update_button_states() # Mettre à jour l'état des boutons au cas où
             return

        # S'assurer que le service compteur est disponible et que l'utilisateur est connu (sécurité, bien que l'état du bouton doive déjà garantir cela)
        if self.compteur_service is None or not self.main_window or not self.main_window.current_user:
            logger.error("Action Gérer Compteurs mais service ou utilisateur manquant. Bouton mal activé?")
            QMessageBox.critical(self, self.tr("Erreur Interne"), self.tr("Service de compteurs ou information utilisateur non disponible."))
            self._update_button_states()
            return


        logger.debug(f"Action: Gérer Compteurs pour Machine ID {selected_machine.id_machine} ('{selected_machine.nom}')")

        # --- OUVRIR LE DIALOGUE DE GESTION DES COMPTEURS (Maintenant importé si l'import en haut est fait) ---
        try:
            # Assurez-vous que l'import de MachineCountersDialog est en haut du fichier et décommenté.
            from app.ui.dialogs.machine_counters_dialog import MachineCountersDialog

            # Passer les informations nécessaires au dialogue
            dialog = MachineCountersDialog(
                machine=selected_machine, # Passe l'objet Machine sélectionné
                compteur_service=self.compteur_service,
                current_user=self.main_window.current_user,
                parent=self.main_window # Utiliser MainWindow comme parent
            )

            # Si le dialogue retourne Accepted (on pourrait l'utiliser pour indiquer si des modifications majeures ont été faites)
            if dialog.exec(): # Bloque jusqu'à la fermeture du dialogue
                 logger.info(f"Dialogue Gérer Compteurs fermé (Accepté) pour machine ID {selected_machine.id_machine}.")
                 # Pas besoin de refresh_machines ici car la vue MachineView n'affiche pas les détails des compteurs
                 # self.refresh_data()
            else:
                 logger.debug(f"Dialogue Gérer Compteurs fermé (Annulé) pour machine ID {selected_machine.id_machine}.")

        # Gérer les exceptions potentielles lors de l'ouverture ou l'exécution du dialogue
        # L'ImportError est déjà gérée si l'import est en haut.
        except Exception as e: # Attrape toute autre erreur inattendue
             logger.exception(f"Erreur ouverture/exécution dialogue Gérer Compteurs pour machine ID {selected_machine.id_machine}: {e}")
             QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue des compteurs:\n{err}").format(err=e))
             self._update_button_states() # Mettre à jour