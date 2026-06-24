# gmao_app/app/ui/dialogs/machine_counters_dialog.py
""" Dialogue pour gérer les compteurs associés à une machine et saisir des relevés. """
import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING

# --- Imports Qt ---
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QAbstractItemView,
                               QHeaderView, QPushButton, QMessageBox, QDialogButtonBox,
                               QSpacerItem, QSizePolicy, QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QFormLayout, QGroupBox, QWidget)
from PySide6.QtCore import Qt, Slot, QDate, QDateTime # Ajoutez les si besoin pour relevés
from datetime import datetime, date

# --- Imports Application ---
from app.core.models.machine import Machine # La machine dont on gère les compteurs
from app.core.models.compteur import Compteur # Les compteurs à afficher/gérer
from app.core.models.utilisateur import Utilisateur # Pour les permissions
from app.core.services.compteur_service import CompteurService
# Imports des dialogues futurs (à créer)
# from app.ui.dialogs.compteur_dialog import CompteurDialog # Dialogue pour Ajouter/Modifier Compteur (params)
# from app.ui.dialogs.releve_compteur_dialog import ReleveCompteurDialog # Dialogue pour Saisir un relevé

if TYPE_CHECKING:
     from PySide6.QtWidgets import QWidget # Si parent est de type QWidget

logger = logging.getLogger(__name__)

# --- Constantes pour les colonnes de la table des compteurs ---
COL_ID_COMPTEUR = 0     # Cachée
COL_NOM_COMPTEUR = 1
COL_UNITE = 2
COL_VALEUR_ACTUELLE = 3
COL_DATE_DERNIER_RELEVE = 4
COL_SEUIL_ALERTE = 5
COL_SEUIL_PREV_OT = 6
# --------------------------------------------------------------

class MachineCountersDialog(QDialog):
    """ Dialogue pour gérer les compteurs d'une machine spécifique. """

    def __init__(self, machine: Machine, compteur_service: CompteurService,
                 current_user: Utilisateur, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.machine = machine
        self.compteur_service = compteur_service
        self.current_user = current_user # L'utilisateur connecté pour les permissions

        self.setWindowTitle(self.tr("Compteurs de la machine : {} ({})").format(self.machine.nom, self.machine.serial))
        self.setMinimumSize(700, 500)

        self.current_compteurs: List[Compteur] = [] # Liste des compteurs de la machine

        self._setup_ui()
        self._load_data() # Charger les compteurs initiaux


    def _setup_ui(self):
        """ Configure l'interface utilisateur du dialogue. """
        self.layout = QVBoxLayout(self)

        # --- Information Machine ---
        info_label = QLabel(self.tr("Machine: <b>{}</b> ({})").format(self.machine.nom, self.machine.serial))
        self.layout.addWidget(info_label)

        # --- Barre d'actions ---
        action_layout = QHBoxLayout()
        self.add_compteur_btn = QPushButton(self.tr("➥ Ajouter Compteur"), self)
        self.edit_compteur_btn = QPushButton(self.tr("✏️ Modifier Compteur"), self)
        self.delete_compteur_btn = QPushButton(self.tr("🗑️ Supprimer Compteur"), self)
        self.releve_btn = QPushButton(self.tr("📝 Enregistrer Relevé"), self)
        self.historique_btn = QPushButton(self.tr("📜 Voir Historique"), self)
        action_layout.addWidget(self.add_compteur_btn)
        action_layout.addWidget(self.edit_compteur_btn)
        action_layout.addWidget(self.delete_compteur_btn)
        action_layout.addWidget(self.releve_btn)
        action_layout.addWidget(self.historique_btn)
        action_layout.addStretch() # Séparateur visuel ou espace
        self.refresh_button = QPushButton(self.tr("🔄 Rafraîchir"))
        action_layout.addWidget(self.refresh_button)
        self.layout.addLayout(action_layout)


        # --- Table des Compteurs ---
        self.counters_table = QTableWidget()
        self.counters_table.setColumnCount(7) # ID, Nom, Unite, Valeur Actuelle, Date Dernier Releve, Seuil Alerte, Seuil Prev OT
        headers = [
            self.tr("ID"),
            self.tr("Nom"),
            self.tr("Unité"),
            self.tr("Valeur Actuelle"),
            self.tr("Date Dernier Relevé"),
            self.tr("Seuil Alerte"),
            self.tr("Seuil OT Prév.")
        ]
        self.counters_table.setHorizontalHeaderLabels(headers)
        self.counters_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.counters_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Sélection unique
        self.counters_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.counters_table.verticalHeader().setVisible(False)
        self.counters_table.setColumnHidden(COL_ID_COMPTEUR, True) # Cacher ID technique

        # Ajuster colonnes
        header = self.counters_table.horizontalHeader()
        header.setSectionResizeMode(COL_NOM_COMPTEUR, QHeaderView.ResizeMode.Stretch) # Nom compteur s'étend
        # Ajustement des autres colonnes
        for col in [COL_UNITE, COL_VALEUR_ACTUELLE, COL_DATE_DERNIER_RELEVE, COL_SEUIL_ALERTE, COL_SEUIL_PREV_OT]:
             header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)


        self.layout.addWidget(self.counters_table)

        # --- Boutons OK / Annuler ---
        # Ce dialogue n'a peut-être pas de bouton OK/Cancel standard si son but est juste de gérer les compteurs
        # au lieu de valider une modification globale de la machine.
        # Pour l'instant, ajoutons un bouton "Fermer".
        close_layout = QHBoxLayout()
        self.close_button = QPushButton(self.tr("Fermer"))
        close_layout.addStretch()
        close_layout.addWidget(self.close_button)
        self.layout.addLayout(close_layout)

        # --- Connexions ---
        self.refresh_button.clicked.connect(self._load_data) # Recharger les données
        self.close_button.clicked.connect(self.accept) # Fermer le dialogue (utiliser accept ou reject?)
        self.counters_table.itemSelectionChanged.connect(self._update_button_states)
        self.counters_table.doubleClicked.connect(self._on_edit_compteur) # Double-clic pour modifier paramètres

        # --- Connexions aux actions des boutons (à implémenter plus tard) ---
        self.add_compteur_btn.clicked.connect(self._on_add_compteur)
        self.edit_compteur_btn.clicked.connect(self._on_edit_compteur) # Aussi sur double-clic
        self.delete_compteur_btn.clicked.connect(self._on_delete_compteur)
        self.releve_btn.clicked.connect(self._on_add_releve)
        self.historique_btn.clicked.connect(self._on_view_history)

        # -----------------------------------------------------------------


        # --- État initial des boutons ---
        self._update_button_states() # Met à jour l'état des boutons basé sur la sélection

        logger.debug(self.tr("MachineCountersDialog UI setup complete."))


    def _load_data(self):
        """ Charge les compteurs pour la machine et remplit la table. """
        logger.info(self.tr("Chargement compteurs pour machine ID {} ('{}')...").format(self.machine.id_machine, self.machine.nom))
        try:
            # Appel au service pour récupérer les compteurs de la machine
            self.current_compteurs = self.compteur_service.get_compteurs_for_machine(self.machine.id_machine)

            self._populate_table(self.current_compteurs) # Remplir la table
            logger.info(self.tr("{} compteurs affichés pour machine {}.").format(len(self.current_compteurs), self.machine.id_machine))

        except Exception as e:
            logger.exception(self.tr("Erreur chargement compteurs machine ID {}: {}").format(self.machine.id_machine, str(e)))
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les compteurs:\n{}").format(str(e)))
            self._populate_table([]) # Afficher une table vide en cas d'erreur

        self._update_button_states() # Mettre à jour l'état des boutons


    def _populate_table(self, compteurs: List[Compteur]):
         """ Remplit la table avec la liste des objets Compteur. """
         if not self.counters_table:
             logger.warning(self.tr("Tentative de peupler la table sans table UI."))
             return

         self.counters_table.setRowCount(len(compteurs))
         # Désactiver tri temporairement si table est triable et tri activé

         for row_index, compteur in enumerate(compteurs):
             # Colonne ID (cachée), stocke l'ID dans UserRole
             id_item = QTableWidgetItem(str(compteur.id_compteur))
             id_item.setData(Qt.ItemDataRole.UserRole, compteur.id_compteur)
             self.counters_table.setItem(row_index, COL_ID_COMPTEUR, id_item)

             # Autres colonnes (récupérer attributs du modèle)
             self.counters_table.setItem(row_index, COL_NOM_COMPTEUR, QTableWidgetItem(compteur.nom))
             self.counters_table.setItem(row_index, COL_UNITE, QTableWidgetItem(compteur.unite))
             # Formater la valeur actuelle (ex: 2 décimales)
             valeur_str = self.tr("{:.2f}").format(compteur.valeur_actuelle) if compteur.valeur_actuelle is not None else ""
             self.counters_table.setItem(row_index, COL_VALEUR_ACTUELLE, QTableWidgetItem(valeur_str))
             # Formatter la date
             date_releve_str = compteur.date_dernier_releve.strftime(self.tr('%Y-%m-%d')) if compteur.date_dernier_releve else ""
             self.counters_table.setItem(row_index, COL_DATE_DERNIER_RELEVE, QTableWidgetItem(date_releve_str))
             # Afficher les seuils (avec None si Null)
             seuil_alerte_str = self.tr("{:.2f}").format(compteur.seuil_alerte) if compteur.seuil_alerte is not None else ""
             seuil_prev_str = self.tr("{:.2f}").format(compteur.seuil_prev_ot) if compteur.seuil_prev_ot is not None else ""
             self.counters_table.setItem(row_index, COL_SEUIL_ALERTE, QTableWidgetItem(seuil_alerte_str))
             self.counters_table.setItem(row_index, COL_SEUIL_PREV_OT, QTableWidgetItem(seuil_prev_str))

             # Rendre les items non éditables
             for col in range(self.counters_table.columnCount()):
                  item = self.counters_table.item(row_index, col)
                  if item: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

         # self.counters_table.resizeColumnsToContents() # Ajuster largeur colonnes


    def _get_selected_compteur_id(self) -> Optional[int]:
         """ Retourne l'ID du compteur sélectionné dans la table, ou None. """
         selected_rows = self.counters_table.selectionModel().selectedRows()
         if not selected_rows:
             return None
         # L'ID est dans la colonne cachée 0, stocké dans UserRole
         id_item = self.counters_table.item(selected_rows[0].row(), COL_ID_COMPTEUR)
         if id_item:
             data = id_item.data(Qt.ItemDataRole.UserRole)
             if data is not None:
                  try:
                       return int(data)
                  except (ValueError, TypeError):
                       logger.error(f"Donnée UserRole invalide pour ID compteur: {data}")
                       return None
             return None # UserRole était None
         return None # Item non trouvé


    def _get_selected_compteur_object(self) -> Optional[Compteur]:
         """ Retourne l'objet Compteur complet sélectionné, ou None. """
         selected_id = self._get_selected_compteur_id()
         if selected_id is None:
              return None

         # Optionnel: chercher l'objet dans self.current_compteurs (si la liste est petite)
         # pour éviter un appel DB. Ou faire un appel DB si la liste est grande.
         # Appelons le service pour être sûr d'avoir les infos les plus récentes.
         try:
              return self.compteur_service.get_compteur_by_id(selected_id) # Méthode service déjà implémentée
         except Exception as e:
              logger.error(f"Erreur récupération objet compteur ID {selected_id}: {e}")
              return None


    @Slot() # type: ignore
    def _update_button_states(self):
        """ Active/désactive les boutons selon la sélection et les droits. """
        has_selection = len(self.counters_table.selectedItems()) > 0

        # Récupérer l'utilisateur (devrait toujours exister, mais sécurité)
        user = self.current_user
        if not user:
             logger.error("Utilisateur manquant dans MachineCountersDialog._update_button_states.")
             # Désactiver tout par sécurité
             self.add_compteur_btn.setEnabled(False)
             self.edit_compteur_btn.setEnabled(False)
             self.delete_compteur_btn.setEnabled(False)
             self.add_releve_button.setEnabled(False)
             self.view_history_button.setEnabled(False)
             return

        user_role = user.role

        # Permissions (exemples, adaptez selon vos règles et l'approche hybride)
        can_manage_compteurs = user_role in ['Admin', 'RespMaint'] # Ajouter/Modifier/Supprimer compteur (les paramètres)
        can_add_releve = user_role in ['Admin', 'Technicien'] # Ajouter un relevé historique
        can_view_history = user_role in ['Admin', 'Technicien', 'RespMaint', 'Lecteur'] # Qui peut voir l'historique?


        # Boutons de gestion des paramètres des compteurs (dépendent de can_manage_compteurs)
        self.add_compteur_btn.setEnabled(can_manage_compteurs) # Ajouter
        self.edit_compteur_btn.setEnabled(has_selection and can_manage_compteurs) # Modifier
        self.delete_compteur_btn.setEnabled(has_selection and can_manage_compteurs) # Supprimer

        # Tooltips (optionnel, mais bonne UX)
        self.add_compteur_btn.setToolTip("" if can_manage_compteurs else "Droits insuffisants")
        self.edit_compteur_btn.setToolTip("" if has_selection and can_manage_compteurs else ("Sélectionnez un compteur" if not has_selection else "Droits insuffisants"))
        self.delete_compteur_btn.setToolTip("" if has_selection and can_manage_compteurs else ("Sélectionnez un compteur" if not has_selection else "Droits insuffisants"))





    @Slot() # type: ignore
    def _on_add_compteur(self):
        """ Ouvre le dialogue pour ajouter un compteur à cette machine. """
        logger.debug(f"Action: Ajouter Compteur pour machine ID {self.machine.id_machine}")
        try:
            from app.ui.dialogs.compteur_dialog import CompteurDialog
        except ImportError as e:
            logger.error(f"Erreur import CompteurDialog: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le dialogue d'ajout de compteur :\n{e}")
            return

        dialog = CompteurDialog(self.compteur_service, self.machine.id_machine, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                compteur_data = {
                    "machine_id": self.machine.id_machine,
                    "nom": data["nom"],
                    "unite": data["unite"],
                    "seuil_alerte": data["seuil_alerte"],
                    "seuil_prev_ot": data["seuil_preventif_ot"]
                }
                compteur = self.compteur_service.create_compteur(compteur_data, self.current_user)
                logger.info(f"Compteur '{compteur.nom}' ajouté à la machine ID {self.machine.id_machine}.")
                QMessageBox.information(self, self.tr("Succès"), self.tr("Compteur '{compteur.nom}' ajouté avec succès."))
                self._load_data()  # Recharge la liste
            except Exception as e:
                logger.exception(f"Erreur lors de la création du compteur: {e}")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible d'ajouter le compteur:\n%1").replace("%1", str(e)))

    @Slot() # type: ignore
    def _on_edit_compteur(self):
        """ Ouvre le dialogue pour modifier le compteur sélectionné. """
        selected_compteur_id = self._get_selected_compteur_id()
        if selected_compteur_id is None:
            QMessageBox.warning(self, self.tr("Sélection requise"), self.tr("Veuillez sélectionner un compteur à modifier."))
            return

        # Récupérer l'objet compteur sélectionné
        compteur = next((c for c in self.current_compteurs if c.id_compteur == selected_compteur_id), None)
        if compteur is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de retrouver le compteur sélectionné."))
            return

        logger.debug(f"Action: Modifier Compteur ID {selected_compteur_id} pour machine {self.machine.id_machine}")
        try:
            from app.ui.dialogs.compteur_dialog import CompteurDialog
        except ImportError as e:
            logger.error(f"Erreur import CompteurDialog: {e}")
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de modification :\n%1").replace("%1", str(e)))
            return

        dialog = CompteurDialog(self.compteur_service, self.machine.id_machine, compteur=compteur, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                compteur.nom = data["nom"]
                compteur.unite = data["unite"]
                compteur.seuil_alerte = data["seuil_alerte"]
                compteur.seuil_prev_ot = data["seuil_preventif_ot"]
                success = self.compteur_service.update_compteur(compteur, self.current_user)
                if success:
                    logger.info(f"Compteur ID {compteur.id_compteur} modifié.")
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Compteur modifié avec succès."))
                    self._load_data()
                else:
                    logger.error(f"Échec modification compteur ID {compteur.id_compteur}")
                    QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de modifier le compteur."))
            except Exception as e:
                logger.exception(f"Erreur lors de la modification du compteur: {e}")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur lors de la modification :\n%1").replace("%1", str(e)))



    @Slot() # type: ignore
    def _on_delete_compteur(self):
         """ Supprime le compteur sélectionné après confirmation. """
         selected_compteur = self._get_selected_compteur_object() # Récupérer l'objet pour le nom
         if selected_compteur is None:
              QMessageBox.warning(self, self.tr("Sélection requise"), self.tr("Veuillez sélectionner un compteur à supprimer."))
              return

         logger.debug(f"Action: Supprimer Compteur ID {selected_compteur.id_compteur} ('{selected_compteur.nom}')")
         # Confirmer
         reply = QMessageBox.question(
             self, self.tr("Confirmation Suppression"),
             self.tr(f"Êtes-vous sûr de vouloir supprimer le compteur '{selected_compteur.nom}'?\n"
             "Cela supprimera aussi tout son historique de relevés."),
             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
             QMessageBox.StandardButton.Cancel
         )

         if reply == QMessageBox.StandardButton.Yes:
              try:
                  # Appel au service (il gérera les droits et la suppression en cascade)
                  success = self.compteur_service.delete_compteur(selected_compteur.id_compteur, self.current_user)
                  if success:
                       QMessageBox.information(self, self.tr("Succès"), self.tr(f"Compteur '{selected_compteur.nom}' supprimé."))
                       self._load_data() # Recharger la liste dans le dialogue
                  else:
                       # Le service lève une exception si échec, mais si rowCount=0
                       QMessageBox.warning(self, self.tr("Échec Suppression"), self.tr(f"Impossible de supprimer le compteur '{selected_compteur.nom}'."))

              except PermissionError as pe:
                   logger.warning(f"Perm. refusée suppression compteur {selected_compteur.id_compteur}: {pe}")
                   QMessageBox.warning(self, self.tr("Accès Refusé"), str(pe))
              except (DatabaseError, BusinessLogicError) as e:
                   logger.error(f"Erreur suppression compteur ID {selected_compteur.id_compteur}: {e}")
                   QMessageBox.critical(self, self.tr("Erreur"), self.tr(f"Impossible de supprimer le compteur:\n{e}"))
              except Exception as e:
                   logger.exception(f"Erreur inattendue suppression compteur ID {selected_compteur.id_compteur}: {e}")
                   QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Une erreur est survenue:\n{e}"))


    @Slot() # type: ignore
    def _on_add_releve(self):
        """ Ouvre le dialogue pour saisir un nouveau relevé pour le compteur sélectionné. """
        selected_compteur_id = self._get_selected_compteur_id()
        if selected_compteur_id is None:
            QMessageBox.warning(self, self.tr("Sélection requise"), self.tr("Veuillez sélectionner un compteur pour enregistrer un relevé."))
            return

        compteur = self.compteur_service.get_compteur_by_id(selected_compteur_id)
        if not compteur:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger le compteur."))
            return
        from app.ui.dialogs.historique_compteur_dialog import HistoriqueCompteurDialog
        dialog = HistoriqueCompteurDialog(compteur, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                result = self.compteur_service.add_historique_releve(
                    {
                        "compteur_id": selected_compteur_id,
                        "valeur": data["valeur"],
                        "date_releve": data["date_releve"]
                    },
                    self.current_user
                )
                logger.info(f"Nouveau relevé enregistré pour compteur ID {selected_compteur_id}.")
                # Vérification si un OT a été déclenché automatiquement (attribut ajouté dynamiquement)
                ot_triggered = getattr(result, 'ot_auto_triggered', None)
                ot_type = getattr(result, 'ot_auto_type', None)
                if ot_triggered and ot_type:
                    QMessageBox.information(self, self.tr("OT automatique déclenché"),
                    self.tr("Un OT automatique de type %1 a été créé pour la machine '%2'.")
                    .replace("%1", ot_type.upper())
                    .replace("%2", compteur.nom))
                QMessageBox.information(self, self.tr("Succès"), self.tr("Relevé enregistré avec succès."))
                self._load_data()
            except Exception as e:
                logger.exception(f"Erreur lors de l'enregistrement du relevé: {e}")
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible d'enregistrer le relevé :\n%1").replace("%1", str(e)))



    @Slot() # type: ignore
    def _on_view_history(self):
        """ Ouvre la vraie vue d'historique pour le compteur sélectionné. """
        selected_compteur_id = self._get_selected_compteur_id()
        if selected_compteur_id is None:
            QMessageBox.warning(self, self.tr("Sélection requise"), self.tr("Veuillez sélectionner un compteur pour voir l'historique."))
            return
        compteur = self.compteur_service.get_compteur_by_id(selected_compteur_id)
        if not compteur:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger le compteur."))
            return
        historiques = self.compteur_service.get_historique_for_compteur(selected_compteur_id)
        from app.ui.dialogs.historique_compteur_view import HistoriqueCompteurView
        dialog = HistoriqueCompteurView(compteur, historiques, parent=self)
        dialog.exec()



    # Le bouton Fermer appelle accept() (qui ferme le dialogue).