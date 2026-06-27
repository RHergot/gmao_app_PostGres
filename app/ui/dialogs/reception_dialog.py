# gmao_app/app/ui/dialogs/reception_dialog.py
import logging
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QAbstractItemView,
                               QHeaderView, QSpinBox, QPushButton, QMessageBox,
                               QDialogButtonBox, QDateEdit, QWidget, QApplication) # Ajout QWidget
from PySide6.QtCore import Qt, QDate, Slot
from datetime import date

# Imports nécessaires
from app.core.models.commande import Commande
from app.core.models.ligne_commande import LigneCommande
from app.core.models.utilisateur import Utilisateur
from app.core.services.achat_service import AchatService
from app.utils.exceptions import GmaoPermissionError, DatabaseError, BusinessLogicError # Importer les exceptions

if TYPE_CHECKING:
     pass # Pas besoin de QWidget ici si déjà importé plus haut

logger = logging.getLogger(__name__)

# Constantes pour les colonnes
COL_ID_LIGNE = 0        # Cachée
COL_ID_PIECE = 1        # Cachée
COL_REF_PIECE = 2
COL_NOM_PIECE = 3
COL_QTY_CMD = 4
COL_QTY_RECUE_AVANT = 5 # Renommé pour clarté
COL_QTY_RESTANTE = 6
COL_QTY_RECEPTION = 7   # Éditable

class ReceptionDialog(QDialog):
    """ Dialogue modal pour saisir les quantités reçues. """

    def __init__(self, commande_id: int, achat_service: AchatService,
                 current_user: Utilisateur, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.commande_id = commande_id
        self.achat_service = achat_service
        self.current_user = current_user
        self.commande: Optional[Commande] = None
        self.lignes_a_receptionner: List[LigneCommande] = [] # Lignes éligibles

        self.setWindowTitle(self.tr("Réception Commande ID: %1").replace("%1", str(self.commande_id)))
        self.setMinimumSize(750, 450)

        # Mettre load_data dans un try pour gérer erreurs avant même setup_ui
        try:
            if not self._load_data(): # Retourne False si erreur ou pas de lignes
                 # Fermer immédiatement si pas de lignes ou erreur chargement
                 # Utiliser QTimer pour appeler reject après que le constructeur soit fini
                 from PySide6.QtCore import QTimer
                 QTimer.singleShot(0, self.reject)
                 # Il faut quand même initialiser les attributs UI pour éviter erreurs potentielles
                 self._setup_ui_minimal() # Appeler une version minimale de setup_ui
            else:
                 self._setup_ui()
                 self._populate_table()
        except Exception as e:
             logger.critical(f"Erreur critique pendant __init__ de ReceptionDialog: {e}", exc_info=True)
             # Afficher message même si l'UI n'est pas prête
             QMessageBox.critical(None, self.tr("Erreur Init"), self.tr(f"Impossible d'initialiser le dialogue de réception:\n{e}"))
             from PySide6.QtCore import QTimer
             QTimer.singleShot(0, self.reject)
             self._setup_ui_minimal() # Initialiser widgets à None

    def _setup_ui_minimal(self):
         """ Initialise les attributs UI à None pour éviter crash si _load_data échoue. """
         self.layout = None
         self.reception_table = None
         self.date_reception_edit = None
         self.button_box = None

    def _load_data(self) -> bool:
        """ Charge la commande et ses lignes éligibles. Retourne True si succès et lignes trouvées. """
        logger.debug(f"Chargement données pour réception commande ID {self.commande_id}")
        try:
            details = self.achat_service.get_commande_details(self.commande_id)
            if not details or not details.get('commande'):
                raise ValueError(f"Commande ID {self.commande_id} non trouvée ou invalide.")

            self.commande = details['commande']
            # Assurer que nom_fournisseur est chargé (peut nécessiter modif get_commande_details/get_by_id)
            if self.commande.nom_fournisseur is None and self.commande.fournisseur_id:
                 logger.warning(f"Nom fournisseur manquant pour Commande ID {self.commande_id}. Affichage ID.")
                 # Optionnel: essayer de le charger ici si besoin absolu
                 # fournisseur = self.achat_service.get_fournisseur_by_id(self.commande.fournisseur_id) # Méthode à créer
                 # if fournisseur: self.commande.nom_fournisseur = fournisseur.nom

            if self.commande.statut not in ['Envoyee', 'Partielle']:
                 QMessageBox.warning(self, self.tr("Action Impossible"), self.tr(f"La commande n'est pas dans un statut permettant la réception ({self.commande.statut})."))
                 return False # Indiquer échec

            all_lignes = details.get('lignes', [])
            self.lignes_a_receptionner = [ligne for ligne in all_lignes if ligne.quantite_recue < ligne.quantite_commandee]

            if not self.lignes_a_receptionner:
                 QMessageBox.information(self, self.tr("Info"), self.tr("Toutes les lignes de cette commande ont déjà été entièrement réceptionnées."))
                 return False # Indiquer qu'il n'y a rien à faire

            return True # Succès

        except (ValueError, DatabaseError, Exception) as e:
            logger.exception(f"Erreur chargement données réception Commande ID {self.commande_id}: {e}")
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr(f"Impossible de charger les données de réception:\n{e}"))
            return False # Indiquer échec


    def _setup_ui(self):
        """ Configure l'interface. """
        self.layout = QVBoxLayout(self)

        if self.commande:
             info_text = self.tr("Commande: %1 - Fournisseur: %2 - Statut: %3") \
                 .replace("%1", str(self.commande.numero_commande or self.commande_id)) \
                 .replace("%2", str(self.commande.nom_fournisseur or f"ID {self.commande.fournisseur_id}")) \
                 .replace("%3", str(self.commande.statut))
             label = QLabel(info_text)
             self.layout.addWidget(label)

        self.reception_table = QTableWidget()
        self.reception_table.setColumnCount(8)
        headers = [self.tr("ID Ligne"), self.tr("ID Pièce"), self.tr("Réf. Pièce"), self.tr("Désignation"), self.tr("Qté Cmd"), self.tr("Déjà Reçue"), self.tr("Qté Restante"), self.tr("Qté à Réceptionner")]
        self.reception_table.setHorizontalHeaderLabels(headers)
        self.reception_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.reception_table.verticalHeader().setVisible(False)
        self.reception_table.setColumnHidden(COL_ID_LIGNE, True)
        self.reception_table.setColumnHidden(COL_ID_PIECE, True)
        self.reception_table.horizontalHeader().setSectionResizeMode(COL_NOM_PIECE, QHeaderView.ResizeMode.Stretch)
        for col in range(COL_QTY_RECEPTION):
            self.reception_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        self.layout.addWidget(self.reception_table)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel(self.tr("Date de Réception:")))
        self.date_reception_edit = QDateEdit(QDate.currentDate())
        self.date_reception_edit.setCalendarPopup(True)
        self.date_reception_edit.setDisplayFormat("yyyy-MM-dd")
        date_layout.addWidget(self.date_reception_edit)
        date_layout.addStretch()
        self.layout.addLayout(date_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(self.tr("Enregistrer Réception"))
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)

    def _populate_table(self):
        """ Remplit la table avec les lignes éligibles. """
        if not self.reception_table: return # Si UI minimale
        self.reception_table.setRowCount(0)

        for ligne in self.lignes_a_receptionner:
             row_position = self.reception_table.rowCount()
             self.reception_table.insertRow(row_position)

             qty_cmd = ligne.quantite_commandee
             qty_recue_avant = ligne.quantite_recue # Renommé
             qty_restante = qty_cmd - qty_recue_avant

             item_id_ligne = QTableWidgetItem(str(ligne.id_ligne))
             item_id_ligne.setData(Qt.ItemDataRole.UserRole, ligne.id_ligne)
             item_id_piece = QTableWidgetItem(str(ligne.piece_id))
             # Utiliser les infos pièces déjà dans l'objet LigneCommande
             item_ref = QTableWidgetItem(ligne.piece_reference or "???")
             item_nom = QTableWidgetItem(ligne.piece_nom or "Pièce Inconnue")
             item_cmd_str = QTableWidgetItem(str(qty_cmd))
             item_recue_avant_str = QTableWidgetItem(str(qty_recue_avant))
             item_restante_str = QTableWidgetItem(str(qty_restante))
             item_restante_str.setData(Qt.ItemDataRole.UserRole, qty_restante)

             flags_uneditable = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
             for item in [item_id_ligne, item_id_piece, item_ref, item_nom, item_cmd_str, item_recue_avant_str, item_restante_str]:
                 item.setFlags(flags_uneditable)

             spin_reception = QSpinBox()
             spin_reception.setMinimum(0)
             spin_reception.setMaximum(qty_restante)
             spin_reception.setValue(0)

             self.reception_table.setItem(row_position, COL_ID_LIGNE, item_id_ligne)
             self.reception_table.setItem(row_position, COL_ID_PIECE, item_id_piece)
             self.reception_table.setItem(row_position, COL_REF_PIECE, item_ref)
             self.reception_table.setItem(row_position, COL_NOM_PIECE, item_nom)
             self.reception_table.setItem(row_position, COL_QTY_CMD, item_cmd_str)
             self.reception_table.setItem(row_position, COL_QTY_RECUE_AVANT, item_recue_avant_str)
             self.reception_table.setItem(row_position, COL_QTY_RESTANTE, item_restante_str)
             self.reception_table.setCellWidget(row_position, COL_QTY_RECEPTION, spin_reception)

        self.reception_table.resizeRowsToContents() # Ajuster hauteur lignes

    @Slot() # type: ignore
    def _on_accept(self):
        """ Traite les saisies et appelle le service pour enregistrer la réception. """
        if not self.reception_table: # Sécurité si UI minimale
            self.reject()
            return

        reception_date = self.date_reception_edit.date().toPython()
        if reception_date > date.today():
             QMessageBox.warning(self, self.tr("Date Invalide"), self.tr("La date de réception ne peut pas être dans le futur."))
             return

        lignes_a_receptionner_service: List[Dict[str, Any]] = []
        has_input_errors = False

        for row in range(self.reception_table.rowCount()):
            widget = self.reception_table.cellWidget(row, COL_QTY_RECEPTION)
            if isinstance(widget, QSpinBox):
                qty_recep_now = widget.value()
                if qty_recep_now > 0:
                     id_ligne_item = self.reception_table.item(row, COL_ID_LIGNE)
                     id_ligne = id_ligne_item.data(Qt.ItemDataRole.UserRole) if id_ligne_item else None
                     nom_piece = self.reception_table.item(row, COL_NOM_PIECE).text() if self.reception_table.item(row, COL_NOM_PIECE) else "Inconnue"

                     if id_ligne is None:
                          logger.error(f"Erreur interne: ID Ligne manquant à la ligne {row} du dialogue réception.")
                          QMessageBox.critical(self, self.tr("Erreur Interne"), self.tr(f"Erreur de données pour la ligne {row+1} (Pièce: {nom_piece})."))
                          has_input_errors = True
                          break # Arrêter le traitement

                     # La validation de quantité max est normalement gérée par le SpinBox, mais double-vérifions
                     restante_item = self.reception_table.item(row, COL_QTY_RESTANTE)
                     qty_max_recep = restante_item.data(Qt.ItemDataRole.UserRole) if restante_item else 0
                     if qty_recep_now > qty_max_recep:
                         QMessageBox.warning(self, self.tr("Quantité Invalide"), self.tr(f"Pour la pièce '{nom_piece}', vous ne pouvez pas réceptionner plus que la quantité restante ({qty_max_recep})."))
                         has_input_errors = True
                         widget.setFocus() # Mettre le focus sur le champ erroné
                         break # Arrêter

                     lignes_a_receptionner_service.append({
                         'ligne_id': id_ligne,
                         'quantite': qty_recep_now,
                         'nom_piece': nom_piece # Pour messages d'erreur
                     })
            else:
                 logger.warning(f"Widget inattendu à la ligne {row}, colonne {COL_QTY_RECEPTION}")

        if has_input_errors:
             # Bouton Save reste actif pour correction
             return # Ne pas continuer si erreur de saisie

        if not lignes_a_receptionner_service:
             QMessageBox.information(self, self.tr("Aucune Réception"), self.tr("Aucune quantité n'a été saisie pour la réception."))
             # On pourrait rejeter ou accepter ici ? Rejeter semble plus logique.
             self.reject()
             return

        # Désactiver bouton pendant traitement
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        save_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor) # Curseur attente

        errors_service = []
        success_count = 0

        for ligne_info in lignes_a_receptionner_service:
             try:
                 # L'appel à receive_ligne_commande doit prendre current_user
                 success = self.achat_service.receive_ligne_commande(
                     ligne_id=ligne_info['ligne_id'],
                     quantite_recue_ajout=ligne_info['quantite'],
                     date_reception=reception_date,
                     current_user=self.current_user # L'utilisateur est stocké dans self.current_user
                 )
                 if success:
                     success_count += 1
                 else:
                     errors_service.append(self.tr(f"Pièce '{ligne_info['nom_piece']}': Échec enregistrement (voir logs)."))

             except (GmaoPermissionError, ValueError, DatabaseError, BusinessLogicError) as e:
                 logger.error(f"Erreur service réception ligne ID {ligne_info['ligne_id']}: {e}")
                 errors_service.append(self.tr(f"Pièce '{ligne_info['nom_piece']}': {e}"))
             except Exception as e:
                 logger.exception(f"Erreur inattendue service réception ligne ID {ligne_info['ligne_id']}: {e}")
                 errors_service.append(self.tr(f"Pièce '{ligne_info['nom_piece']}': Erreur serveur."))

        QApplication.restoreOverrideCursor() # Restaurer curseur normal
        save_button.setEnabled(True) # Réactiver bouton

        # Afficher résultat global
        if errors_service:
             error_details = "\n - ".join(errors_service)
             msg = self.tr(f"{success_count} ligne(s) réceptionnée(s) avec succès.\n\nErreurs survenue(s):\n - {error_details}")
             QMessageBox.warning(self, self.tr("Réception Partielle / Erreurs"), msg)
        else:
             QMessageBox.information(self, self.tr("Succès"), self.tr(f"{success_count} ligne(s) réceptionnée(s) avec succès."))

        self.accept() # Accepter pour indiquer que le processus est terminé (même si erreurs)