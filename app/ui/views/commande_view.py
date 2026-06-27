# gmao_app/app/ui/views/commande_view.py
""" Vue pour lister et gérer les commandes d'achat. """
import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableView, QAbstractItemView, QMessageBox,
                               QLabel, QSpacerItem, QSizePolicy, QHeaderView)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Slot

from app.core.services.achat_service import AchatService
from app.core.models.commande import Commande
# Importer le dialogue (même s'il n'existe pas encore complètement)
from app.ui.dialogs.commande_dialog import CommandeDialog # Décommenter quand le dialogue existe
from app.ui.dialogs.reception_dialog import ReceptionDialog
from app.utils.exceptions import GmaoPermissionError, DatabaseError, BusinessLogicError # Ajouter imports exceptions

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)

class CommandeView(QWidget):
    """ Widget de la vue principale pour les commandes d'achat. """

    def __init__(self, achat_service: AchatService, main_window: "MainWindow"):
        super().__init__()
        self.achat_service = achat_service
        self.main_window = main_window
        self.model = None # Sera initialisé dans setup_ui

        logger.info("Initialisation de CommandeView...")
        self._setup_ui()
        self.refresh_data() # Charger les données initiales
        logger.info("CommandeView initialisée.")

    def _setup_ui(self):
        # --- Barre d'actions ---
        action_layout = QHBoxLayout()
        self.new_button = QPushButton("➕ " + self.tr("Nouvelle Commande"))
        self.edit_button = QPushButton("✏️ " + self.tr("Modifier"))
        self.delete_button = QPushButton("🗑️ " + self.tr("Supprimer"))
        self.send_button = QPushButton("➡️ " + self.tr("Envoyer"))
        self.receive_button = QPushButton("🚚 " + self.tr("Réceptionner...")) # Action future
        self.refresh_button = QPushButton("🔄 " + self.tr("Rafraîchir"))

        # Contrôle des droits d'accès sur le bouton Nouvelle Commande
        if not self.main_window.current_user or self.main_window.current_user.role not in ['Admin', 'GestionStock']:
            self.new_button.setEnabled(False)
            self.new_button.setToolTip(self.tr("Droits insuffisants"))
        else:
            self.new_button.setEnabled(True)

        """ Configure l'interface utilisateur de la vue. """
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10) # Ajouter des marges
        self.layout.setSpacing(10) # Espacement entre widgets

        action_layout.addWidget(self.new_button)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addWidget(self.send_button)
        action_layout.addWidget(self.receive_button)
        action_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        action_layout.addWidget(self.refresh_button)
        self.layout.addLayout(action_layout)

        # --- Table des Commandes ---
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Sélection par ligne
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Non éditable directement
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False) # Masquer numéros de ligne
        self.table_view.horizontalHeader().setStretchLastSection(True) # Étirer dernière colonne
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive) # Permettre redimensionnement

        # Création du modèle
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)
        self._setup_table_headers() # Définir les en-têtes

        self.layout.addWidget(self.table_view)

        # --- Zone d'information (optionnel) ---
        info_layout = QHBoxLayout()
        self.info_label = QLabel(self.tr("Chargement..."))
        info_layout.addWidget(self.info_label)
        info_layout.addSpacerItem(QSpacerItem(40, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.layout.addLayout(info_layout)

        # --- Connecter les signaux ---
        self.new_button.clicked.connect(self._on_new_commande)
        self.edit_button.clicked.connect(self._on_edit_commande)
        self.delete_button.clicked.connect(self._on_delete_commande)
        self.send_button.clicked.connect(self._on_send_commande)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.receive_button.clicked.connect(self._on_receive_commande) # Connecter, même si pas implémenté
        self.table_view.doubleClicked.connect(self._on_edit_commande) # Double-clic pour éditer

        # Désactiver boutons qui nécessitent une sélection au départ
        self._update_button_states()
        self.table_view.selectionModel().selectionChanged.connect(self._update_button_states)
        self.send_button.setEnabled(True) # Désactivé pour l'instant
        self.receive_button.setEnabled(True) # Désactivé pour l'instant

    def _setup_table_headers(self):
        """ Définit les en-têtes pour la table des commandes. """
        if not self.model: return
        # ORDRE DES LABELS IMPORTANTS
        headers = ["ID", "Numéro Cmd", "Fournisseur", "Date Cmd", "Statut", "Total HT", "Date Création", "Date MàJ"]
        self.model.setHorizontalHeaderLabels(headers)
        # Cacher ID (Colonne 0)
        self.table_view.setColumnHidden(0, True)
        # Ajustement largeurs (indices se réfèrent aux colonnes VISIBLES ou TOTALES ?)
        # Testez avec les indices basés sur les headers initiaux:
        self.table_view.horizontalHeader().resizeSection(1, 150) # Numéro Cmd
        self.table_view.horizontalHeader().resizeSection(2, 200) # Fournisseur
        self.table_view.horizontalHeader().resizeSection(3, 120) # Date Cmd
        self.table_view.horizontalHeader().resizeSection(4, 100) # Statut
        self.table_view.horizontalHeader().resizeSection(5, 100) # Total HT
        self.table_view.horizontalHeader().resizeSection(6, 120) # Date Création
        self.table_view.horizontalHeader().resizeSection(7, 120) # Date MàJ


    def refresh_data(self):
        """ Recharge et affiche les données des commandes. """
        logger.info("Rafraîchissement liste des commandes...")
        if not self.model:
            logger.error("Modèle de table non initialisé.")
            return

        try:
            # Récupérer les données depuis le service
            # TODO: Ajouter la gestion des filtres ici si des widgets de filtre sont ajoutés
            commandes = self.achat_service.get_all_commandes(sort_by="date_commande", sort_desc=True)

            # Effacer le modèle actuel et remettre les en-têtes
            self.model.removeRows(0, self.model.rowCount())
            # self._setup_table_headers() # Normalement pas nécessaire si on efface juste les lignes

            if not commandes:
                 logger.info("Aucune commande trouvée.")
                 self.info_label.setText(self.tr("Aucune commande à afficher."))
                 self._update_button_states()
                 return

            # Remplir le modèle
            for cmd in commandes:
                row = [] # Nouvelle liste pour chaque ligne

                # Item 0 : ID Commande (sera caché)
                id_item = QStandardItem(str(cmd.id_commande))
                id_item.setData(cmd.id_commande, Qt.ItemDataRole.UserRole)
                row.append(id_item)

                # Item 1 : Numéro Cmd (Correspond à header[1])
                row.append(QStandardItem(cmd.numero_commande or "N/A"))

                # Item 2 : Fournisseur (Correspond à header[2])
                row.append(QStandardItem(cmd.nom_fournisseur or f"ID {cmd.fournisseur_id}")) # Utilise nom_fournisseur

                # Item 3 : Date Cmd (Correspond à header[3])
                row.append(QStandardItem(cmd.date_commande.strftime('%Y-%m-%d') if cmd.date_commande else ""))

                # Item 4 : Statut (Correspond à header[4])
                row.append(QStandardItem(cmd.statut))

                # Item 5 : Total HT (Correspond à header[5])
                row.append(QStandardItem(f"{cmd.total_ht:.2f}"))

                # Item 6 : Date Création (Correspond à header[6])
                row.append(QStandardItem(cmd.created_at.strftime('%Y-%m-%d %H:%M') if cmd.created_at else ""))

                # Item 7 : Date MàJ (Correspond à header[7])
                row.append(QStandardItem(cmd.updated_at.strftime('%Y-%m-%d %H:%M') if cmd.updated_at else ""))

                # --- Assurer que chaque item a les bons flags ---
                for item in row:
                    if item: item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        # --------------------------------------------


                self.model.appendRow(row)

            logger.info(f"{len(commandes)} commandes affichées.")
            self.info_label.setText(self.tr("{} commande(s) affichée(s).").format(len(commandes)))
            # Ajuster colonnes au contenu après remplissage
            # self.table_view.resizeColumnsToContents()

        except Exception as e: # Attraper large pour erreurs service/DB
            logger.exception(f"Erreur lors du rafraîchissement des commandes : {e}")
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les commandes:\n{}".format(e)))
            self.info_label.setText(self.tr("Erreur chargement."))

        self._update_button_states()

     # --- MÉTHODE POUR RÉCUPÉRER L'ID DEPUIS LA TABLE ---
    def _get_selected_commande_id(self) -> Optional[int]:
         """ Retourne l'ID de la commande sélectionnée dans la table, ou None. """
         selected_indexes = self.table_view.selectionModel().selectedRows()
         if not selected_indexes:
             return None
         # Récupérer l'item de la première colonne (ID) de la ligne sélectionnée
         # L'index 0 correspond à la colonne "ID"
         id_item_index = selected_indexes[0].siblingAtColumn(0)
         id_item = self.model.itemFromIndex(id_item_index)
         if id_item:
             # Récupérer l'ID stocké dans UserRole lors du refresh_data
             data = id_item.data(Qt.ItemDataRole.UserRole)
             if data is not None:
                  try:
                       return int(data)
                  except (ValueError, TypeError):
                       logger.error(f"Donnée UserRole invalide pour ID commande: {data}")
                       return None
             else:
                  logger.warning("Aucune donnée UserRole trouvée pour l'ID commande.")
                  return None
         logger.warning("Item ID non trouvé pour la ligne sélectionnée.")
         return None
    # ----------------------------------------------------

    def _get_selected_commande_object(self) -> Optional[Commande]:
         """ Retourne l'objet Commande complet sélectionné, ou None. """
         selected_id = self._get_selected_commande_id()
         if selected_id is None:
             return None
         try:
             # Appeler le service pour obtenir l'objet complet
             commande = self.achat_service.get_commande_details(selected_id)
             if commande:
                 return commande['commande'] # Retourne l'objet Commande
             return None
         except Exception as e:
              logger.error(f"Erreur récupération détails commande ID {selected_id} pour _get_selected_commande_object: {e}")
              return None

    @Slot() # type: ignore
    def _update_button_states(self):
        selected_commande = self._get_selected_commande_object()
        has_selection = selected_commande is not None
        can_edit_delete = False
        can_receive = False
        can_send = False # Nouvelle variable

        user_role = "Inconnu"
        if hasattr(self, 'main_window') and hasattr(self.main_window, 'current_user') and self.main_window.current_user:
            user_role = self.main_window.current_user.role
        else:
            logger.error("Impossible de récupérer le rôle utilisateur dans _update_button_states.")

        allowed_edit_roles = ['Admin', 'GestionStock']
        allowed_receive_roles = ['Admin', 'GestionStock', 'Magasinier']
        allowed_send_roles = ['Admin', 'GestionStock'] # Rôles qui peuvent envoyer

        if has_selection:
            # Editer/Supprimer si Brouillon et bon rôle
            if selected_commande.statut == 'Brouillon' and user_role in allowed_edit_roles:
                can_edit_delete = True
            # Envoyer si Brouillon et bon rôle
            if selected_commande.statut == 'Brouillon' and user_role in allowed_send_roles:
                can_send = True
            # Réceptionner si Envoyee/Partielle et bon rôle
            if selected_commande.statut in ['Envoyee', 'Partielle'] and user_role in allowed_receive_roles:
                can_receive = True

        self.edit_button.setEnabled(can_edit_delete)
        self.delete_button.setEnabled(can_edit_delete)
        self.send_button.setEnabled(can_send) # Activer/Désactiver le nouveau bouton
        self.receive_button.setEnabled(can_receive)

        # Tooltips
        self.edit_button.setToolTip("" if can_edit_delete else "Modif. impossible (statut/droits)")
        self.delete_button.setToolTip("" if can_edit_delete else "Suppr. impossible (statut/droits)")
        self.send_button.setToolTip("" if can_send else "Envoi impossible (statut/droits)") # Tooltip pour envoyer
        self.receive_button.setToolTip("" if can_receive else "Récept. impossible (statut/droits)")


    @Slot() # type: ignore
    def _on_new_commande(self):
        """ Ouvre le dialogue pour créer une nouvelle commande. """
        logger.debug("Action: Nouvelle Commande")
        # --- CODE ACTIVÉ ---
        # Assurez-vous que self.stock_service existe et est passé correctement
        try:
            if not hasattr(self.main_window, 'stock_service'): # Vérifier si stock_service est accessible
                 logger.error("StockService non trouvé pour CommandeDialog.")
                 QMessageBox.critical(self,"Erreur", "Service de Stock non initialisé.")
                 return

            dialog = CommandeDialog(self.achat_service, self.main_window.stock_service, None, self.main_window) # None car nouvelle commande
            if dialog.exec():
                logger.info("Dialogue Nouvelle Commande fermé avec succès (OK).")
                self.refresh_data() # Recharger la liste
            else:
                logger.info("Dialogue Nouvelle Commande annulé.")
        except Exception as e:
             logger.exception(f"Erreur ouverture dialogue Nouvelle Commande: {e}")
             QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le dialogue:\n{e}")
        # --- FIN CODE ACTIVÉ ---
        # QMessageBox.information(self, "Info", "Fonctionnalité 'Nouvelle Commande' à implémenter (Dialogue).") # <- Supprimer ou commenter


    @Slot() # type: ignore
    def _on_edit_commande(self):
        """ Ouvre le dialogue pour modifier la commande sélectionnée. """
        selected_id = self._get_selected_commande_id()
        if selected_id is None:
            QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner une commande à modifier.")
            return
        logger.debug(f"Action: Modifier Commande ID {selected_id}")
        # --- CODE ACTIVÉ ---
        try:
            if not hasattr(self.main_window, 'stock_service'):
                 logger.error("StockService non trouvé pour CommandeDialog.")
                 QMessageBox.critical(self,"Erreur", "Service de Stock non initialisé.")
                 return

            dialog = CommandeDialog(self.achat_service, self.main_window.stock_service, selected_id, self.main_window) # Passer l'ID
            if dialog.exec():
                logger.info(f"Dialogue Modifier Commande ID {selected_id} fermé avec succès (OK).")
                self.refresh_data()
            else:
                logger.info(f"Dialogue Modifier Commande ID {selected_id} annulé.")
        except Exception as e:
             logger.exception(f"Erreur ouverture dialogue Modifier Commande ID {selected_id}: {e}")
             QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le dialogue pour ID {selected_id}:\n{e}")
        # --- FIN CODE ACTIVÉ ---
        # QMessageBox.information(self, "Info", f"Fonctionnalité 'Modifier Commande {selected_id}' à implémenter (Dialogue).") # <- Supprimer ou commenter

    @Slot() # type: ignore
    def _on_delete_commande(self):
        """ Supprime la commande sélectionnée après confirmation. """
        selected_id = self._get_selected_commande_id()
        if selected_id is None:
            QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner une commande à supprimer.")
            return

        commande = self.achat_service.get_commande_details(selected_id) # Récupérer détails pour affichage
        if not commande:
             QMessageBox.critical(self, "Erreur", f"Commande ID {selected_id} non trouvée.")
             self.refresh_data() # Au cas où elle ait disparu entre-temps
             return

        cmd_num = commande['commande'].numero_commande or f"ID {selected_id}"
        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer la commande '{cmd_num}' et toutes ses lignes associées ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.debug(f"Action: Supprimer Commande ID {selected_id}")
            try:
                success = self.achat_service.delete_commande(selected_id)
                if success:
                    QMessageBox.information(self, "Succès", f"Commande '{cmd_num}' supprimée avec succès.")
                    self.refresh_data()
                else:
                    # Le service devrait lever une erreur si la suppression échoue (ex: statut incorrect)
                     QMessageBox.warning(self, "Échec", f"Impossible de supprimer la commande '{cmd_num}'.")
            except Exception as e:
                 logger.exception(f"Erreur lors de la suppression de la commande ID {selected_id}: {e}")
                 QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la suppression:\n{e}")
        else:
             logger.debug(f"Suppression commande ID {selected_id} annulée.")


    @Slot() # type: ignore
    def _on_receive_commande(self):
        """ Ouvre le dialogue/processus de réception pour la commande sélectionnée. """
        selected_commande = self._get_selected_commande_object() # Récupère l'objet complet

        if selected_commande is None:
             QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner une commande pour la réception.")
             return

        # Vérification supplémentaire du statut (déjà fait dans _update_button_states mais sécurité)
        if selected_commande.statut not in ['Envoyee', 'Partielle']:
            QMessageBox.warning(self, "Action Impossible", f"La commande {selected_commande.numero_commande or selected_commande.id_commande} n'est pas dans un statut permettant la réception (Statut: {selected_commande.statut}).")
            return

        # Vérification des droits (déjà fait mais sécurité)
        user_role = self.main_window.current_user.role
        allowed_receive_roles = ['Admin', 'GestionStock', 'Magasinier']
        if user_role not in allowed_receive_roles:
             QMessageBox.warning(self, "Accès Refusé", "Vous n'avez pas les droits pour enregistrer une réception.")
             return

        selected_id = selected_commande.id_commande
        logger.debug(f"Action: Réceptionner Commande ID {selected_id}")

        # --- OUVERTURE DU DIALOGUE DE RÉCEPTION (à créer) ---
        try:
             dialog = ReceptionDialog(selected_id, self.achat_service, self.main_window.current_user, self.main_window) # Parent = MainWindow

             if dialog.exec():
                 logger.info(f"Réception enregistrée pour commande ID {selected_id}.")
                 self.refresh_data() # Recharger la liste pour voir les statuts mis à jour
             else:
                 logger.info(f"Réception annulée pour commande ID {selected_id}.")

        except ImportError:
              logger.error("Le dialogue de réception (ReceptionDialog) n'est pas encore créé/importable.")
              QMessageBox.information(self, "Info", f"Fonctionnalité 'Réception Commande {selected_id}' à implémenter (ReceptionDialog).")
        except Exception as e:
              logger.exception(f"Erreur ouverture/exécution dialogue Réception pour commande ID {selected_id}: {e}")
              QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le dialogue de réception:\n{e}")
        # ----------------------------------------------------

    @Slot() # type: ignore
    def _on_send_commande(self):
        """ Change le statut de la commande sélectionnée à 'Envoyee'. """
        selected_commande = self._get_selected_commande_object()
        if selected_commande is None:
            QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner une commande à envoyer.")
            return

        # Vérifications (normalement déjà faites par _update_button_states, mais sécurité)
        if selected_commande.statut != 'Brouillon':
             QMessageBox.warning(self, "Action Impossible", f"La commande doit être au statut 'Brouillon' pour être envoyée (Statut actuel: {selected_commande.statut}).")
             return

        user = self.main_window.current_user # Récupérer l'utilisateur
        if not user:
             QMessageBox.critical(self, "Erreur", "Utilisateur non identifié.")
             return

        cmd_num = selected_commande.numero_commande or f"ID {selected_commande.id_commande}"
        reply = QMessageBox.question(
            self,
            "Confirmation d'envoi",
            f"Êtes-vous sûr de vouloir passer la commande '{cmd_num}' au statut 'Envoyee' ?\n"
            f"Elle ne sera plus modifiable (sauf statut par admin?).", # Préciser les conséquences
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Tentative d'envoi commande ID {selected_commande.id_commande} par {user.login}")
            try:
                 # Appel à la nouvelle méthode du service
                 success = self.achat_service.envoyer_commande(selected_commande.id_commande, user)
                 if success:
                     QMessageBox.information(self, "Succès", f"Commande '{cmd_num}' passée au statut 'Envoyee'.")
                     self.refresh_data() # Mettre à jour la vue pour voir le nouveau statut
                 else:
                      # Le service devrait lever une exception normalement en cas d'échec
                      QMessageBox.warning(self, "Échec", f"L'envoi de la commande '{cmd_num}' a échoué (voir logs).")
            except GmaoPermissionError as pe:
                 logger.warning(f"Permission refusée envoi commande {selected_commande.id_commande}: {pe}")
                 QMessageBox.warning(self, "Accès Refusé", str(pe))
            except (DatabaseError, BusinessLogicError, ValueError) as e:
                 logger.error(f"Erreur lors de l'envoi commande {selected_commande.id_commande}: {e}")
                 QMessageBox.critical(self, "Erreur Envoi", f"Impossible d'envoyer la commande:\n{e}")
            except Exception as e:
                 logger.exception(f"Erreur inattendue envoi commande {selected_commande.id_commande}: {e}")
                 QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur serveur est survenue:\n{e}")
        else:
             logger.debug(f"Envoi commande ID {selected_commande.id_commande} annulé.")
