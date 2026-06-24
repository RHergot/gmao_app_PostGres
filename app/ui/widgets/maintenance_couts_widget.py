# gmao_app/app/ui/widgets/maintenance_couts_widget.py
"""
Widget pour gérer les coûts d'une maintenance (intervenants et frais externes).
"""
import logging
from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QMessageBox, QToolButton, QGroupBox, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QColor

from app.ui.dialogs.intervenant_dialog import IntervenantDialog
from app.ui.dialogs.frais_externe_dialog import FraisExterneDialog

logger = logging.getLogger()

class MaintenanceCoutsWidget(QWidget):
    """Widget affichant et permettant la gestion des coûts d'une maintenance."""
    
    # Signaux
    coutsModifies = Signal()  # Émis lorsque les coûts sont modifiés
    
    def __init__(self, parent=None, maintenance_id=None, maintenance_service=None):
        """
        Initialise le widget des coûts de maintenance.
        
        Args:
            parent: Widget parent
            maintenance_id: ID de la maintenance à afficher
            maintenance_service: Service pour les opérations sur la maintenance
        """
        super().__init__(parent)
        self.maintenance_id = maintenance_id
        self.maintenance_service = maintenance_service
        self.cout_data = None  # Données des coûts calculés
        
        self._setup_ui()
        
        if self.maintenance_id:
            self.charger_donnees()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # En-tête : titre et bouton de rafraîchissement
        header_layout = QHBoxLayout()
        self.lbl_titre = QLabel(self.tr("Coûts de la maintenance"))
        self.lbl_titre.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.lbl_titre)
        
        self.btn_refresh = QPushButton(self.tr("Actualiser"))
        self.btn_refresh.setIcon(QIcon.fromTheme("view-refresh", QIcon()))
        self.btn_refresh.clicked.connect(self.charger_donnees)
        header_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Résumé des coûts
        self.cout_summary_widget = QFrame()
        self.cout_summary_widget.setFrameShape(QFrame.StyledPanel)
        self.cout_summary_widget.setStyleSheet("background-color: #f5f5f5;")
        
        summary_layout = QVBoxLayout(self.cout_summary_widget)
        
        # Coût total
        total_layout = QHBoxLayout()
        self.lbl_cout_total_titre = QLabel(self.tr("Coût Total :"))
        self.lbl_cout_total_titre.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.lbl_cout_total = QLabel("0,00 €")
        self.lbl_cout_total.setStyleSheet("font-weight: bold; font-size: 16px; color: #006400;")
        self.lbl_cout_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        total_layout.addWidget(self.lbl_cout_total_titre)
        total_layout.addStretch()
        total_layout.addWidget(self.lbl_cout_total)
        
        summary_layout.addLayout(total_layout)
        
        # Détail par catégorie
        details_layout = QHBoxLayout()
        
        # Pièces internes
        pieces_layout = QVBoxLayout()
        self.lbl_pieces_titre = QLabel(self.tr("Pièces internes :"))
        self.lbl_pieces_titre.setStyleSheet("font-weight: bold;")
        self.lbl_pieces_cout = QLabel("0,00 €")
        self.lbl_pieces_cout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pieces_layout.addWidget(self.lbl_pieces_titre)
        pieces_layout.addWidget(self.lbl_pieces_cout)
        
        # Main d'œuvre
        mo_layout = QVBoxLayout()
        self.lbl_mo_titre = QLabel(self.tr("Main d'œuvre :"))
        self.lbl_mo_titre.setStyleSheet("font-weight: bold;")
        self.lbl_mo_cout = QLabel("0,00 €")
        self.lbl_mo_cout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mo_layout.addWidget(self.lbl_mo_titre)
        mo_layout.addWidget(self.lbl_mo_cout)
        
        # Frais externes
        frais_layout = QVBoxLayout()
        self.lbl_frais_titre = QLabel(self.tr("Frais externes :"))
        self.lbl_frais_titre.setStyleSheet("font-weight: bold;")
        self.lbl_frais_cout = QLabel("0,00 €")
        self.lbl_frais_cout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        frais_layout.addWidget(self.lbl_frais_titre)
        frais_layout.addWidget(self.lbl_frais_cout)
        
        details_layout.addLayout(pieces_layout)
        details_layout.addLayout(mo_layout)
        details_layout.addLayout(frais_layout)
        
        summary_layout.addLayout(details_layout)
        
        layout.addWidget(self.cout_summary_widget)
        
        # Onglets pour le détail
        self.tab_widget = QTabWidget()
        
        # Onglet Intervenants
        self.intervenants_widget = QWidget()
        intervenants_layout = QVBoxLayout(self.intervenants_widget)
        
        # Boutons d'action pour intervenants
        interv_buttons_layout = QHBoxLayout()
        self.btn_add_intervenant = QPushButton(self.tr("Ajouter un intervenant"))
        self.btn_add_intervenant.setIcon(QIcon.fromTheme("list-add", QIcon()))
        self.btn_edit_intervenant = QPushButton(self.tr("Modifier"))
        self.btn_edit_intervenant.setIcon(QIcon.fromTheme("document-edit", QIcon()))
        self.btn_edit_intervenant.setEnabled(False)
        self.btn_delete_intervenant = QPushButton(self.tr("Supprimer"))
        self.btn_delete_intervenant.setIcon(QIcon.fromTheme("edit-delete", QIcon()))
        self.btn_delete_intervenant.setEnabled(False)
        
        interv_buttons_layout.addWidget(self.btn_add_intervenant)
        interv_buttons_layout.addWidget(self.btn_edit_intervenant)
        interv_buttons_layout.addWidget(self.btn_delete_intervenant)
        interv_buttons_layout.addStretch()
        
        intervenants_layout.addLayout(interv_buttons_layout)
        
        # Tableau des intervenants
        self.tbl_intervenants = QTableWidget()
        self.tbl_intervenants.setColumnCount(6)
        self.tbl_intervenants.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom"), self.tr("Type"), self.tr("Heures"), self.tr("Coût horaire"), self.tr("Coût total")
        ])
        self.tbl_intervenants.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_intervenants.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_intervenants.verticalHeader().setVisible(False)
        self.tbl_intervenants.setAlternatingRowColors(True)
        self.tbl_intervenants.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_intervenants.setSelectionMode(QTableWidget.SingleSelection)
        
        intervenants_layout.addWidget(self.tbl_intervenants)
        
        # Onglet Frais Externes
        self.frais_widget = QWidget()
        frais_layout = QVBoxLayout(self.frais_widget)
        
        # Boutons d'action pour frais
        frais_buttons_layout = QHBoxLayout()
        self.btn_add_frais = QPushButton(self.tr("Ajouter un frais"))
        self.btn_add_frais.setIcon(QIcon.fromTheme("list-add", QIcon()))
        self.btn_edit_frais = QPushButton(self.tr("Modifier"))
        self.btn_edit_frais.setIcon(QIcon.fromTheme("document-edit", QIcon()))
        self.btn_edit_frais.setEnabled(False)
        self.btn_delete_frais = QPushButton(self.tr("Supprimer"))
        self.btn_delete_frais.setIcon(QIcon.fromTheme("edit-delete", QIcon()))
        self.btn_delete_frais.setEnabled(False)
        
        frais_buttons_layout.addWidget(self.btn_add_frais)
        frais_buttons_layout.addWidget(self.btn_edit_frais)
        frais_buttons_layout.addWidget(self.btn_delete_frais)
        frais_buttons_layout.addStretch()
        
        frais_layout.addLayout(frais_buttons_layout)
        
        # Tableau des frais
        self.tbl_frais = QTableWidget()
        self.tbl_frais.setColumnCount(7)
        self.tbl_frais.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Type"), self.tr("Description"), self.tr("Montant"), self.tr("Quantité"), self.tr("Total"), self.tr("Fournisseur")
        ])
        self.tbl_frais.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_frais.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_frais.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_frais.verticalHeader().setVisible(False)
        self.tbl_frais.setAlternatingRowColors(True)
        self.tbl_frais.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_frais.setSelectionMode(QTableWidget.SingleSelection)
        
        frais_layout.addWidget(self.tbl_frais)
        
        # Ajouter les onglets (sans l'onglet Pièces internes)
        self.tab_widget.addTab(self.intervenants_widget, self.tr("Intervenants"))
        self.tab_widget.addTab(self.frais_widget, self.tr("Frais externes"))
        
        layout.addWidget(self.tab_widget)
        
        # Connexions
        self.btn_add_intervenant.clicked.connect(self.ajouter_intervenant)
        self.btn_edit_intervenant.clicked.connect(self.modifier_intervenant)
        self.btn_delete_intervenant.clicked.connect(self.supprimer_intervenant)
        self.tbl_intervenants.itemSelectionChanged.connect(self.on_intervenant_selection_changed)
        
        self.btn_add_frais.clicked.connect(self.ajouter_frais)
        self.btn_edit_frais.clicked.connect(self.modifier_frais)
        self.btn_delete_frais.clicked.connect(self.supprimer_frais)
        self.tbl_frais.itemSelectionChanged.connect(self.on_frais_selection_changed)
    
    def set_maintenance_id(self, maintenance_id):
        """Définit l'ID de la maintenance et recharge les données."""
        self.maintenance_id = maintenance_id
        self.charger_donnees()
    
    def charger_donnees(self):
        """Charge les données de coûts pour la maintenance actuelle."""
        if not self.maintenance_id or not self.maintenance_service:
            self._clear_all()
            return
        
        try:
            # Récupérer les données de coût calculées
            
            self.cout_data = self.maintenance_service.calculate_maintenance_cost(self.maintenance_id)
            import pprint
            logger.debug("DUMP cout_data: %s", pprint.pformat(self.cout_data))
            print("DUMP cout_data:", pprint.pformat(self.cout_data))
            
            # Mettre à jour les montants du résumé
            self._update_summary()
            
            # Remplir les tableaux
            self._populate_intervenants_table()
            self._populate_frais_table()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des coûts de maintenance: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur de chargement"), 
                self.tr("Impossible de charger les coûts de maintenance : %1").replace("%1", str(e))
            )
            self._clear_all()
    
    def _format_currency(self, value):
        """Formate un montant en devise avec séparateur de milliers."""
        if isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return "0,00 €"
        
        return f"{value:,.2f} €".replace(",", " ").replace(".", ",")
    
    def _update_summary(self):
        """Met à jour les labels de résumé des coûts."""
        if not self.cout_data:
            self._clear_summary()
            return
        
        # Coût total
        self.lbl_cout_total.setText(self._format_currency(self.cout_data.get('cout_total', 0)))
        
        # Coûts par catégorie
        details = self.cout_data.get('detail', {})
        
        # Pièces internes
        pieces_cout = details.get('pieces_internes', {}).get('cout_total', 0)
        self.lbl_pieces_cout.setText(self._format_currency(pieces_cout))
        
        # Main d'œuvre
        mo_cout = details.get('main_oeuvre', {}).get('cout_total', 0)
        self.lbl_mo_cout.setText(self._format_currency(mo_cout))
        
        # Frais externes
        frais_cout = details.get('frais_externes', {}).get('cout_total', 0)
        self.lbl_frais_cout.setText(self._format_currency(frais_cout))

        # --- Ventilation centre de frais ---
        # Nettoyage préalable
        if hasattr(self, 'centre_frais_labels'):
            for lbl in self.centre_frais_labels:
                self.cout_summary_widget.layout().removeWidget(lbl)
                lbl.deleteLater()
        self.centre_frais_labels = []

        ventilation = details.get('frais_externes', {}).get('ventilation_centre_frais', {})
        if ventilation:
            for type_frais, montant in ventilation.items():
                lbl = QLabel(f"  - {self._format_type_frais(type_frais)} : {self._format_currency(montant)}")
                lbl.setStyleSheet("color: #555; margin-left: 16px;")
                self.cout_summary_widget.layout().addWidget(lbl)
                self.centre_frais_labels.append(lbl)
    
    def _clear_summary(self):
        """Réinitialise les labels de résumé."""
        self.lbl_cout_total.setText(self.tr("0,00 €"))
        self.lbl_pieces_cout.setText(self.tr("0,00 €"))
        self.lbl_mo_cout.setText(self.tr("0,00 €"))
        self.lbl_frais_cout.setText(self.tr("0,00 €"))
    
    def _populate_intervenants_table(self):
        """Remplit le tableau des intervenants."""
        self.tbl_intervenants.setRowCount(0)
        
        if not self.cout_data:
            return
        
        intervenants = self.cout_data.get('detail', {}).get('main_oeuvre', {}).get('items', [])
        print('DEBUG intervenants:', intervenants)  # DEBUG temporaire

        
        self.tbl_intervenants.setRowCount(len(intervenants))
        for row, intervenant in enumerate(intervenants):
            # ID
            # Afficher systématiquement la clé primaire en colonne 1 (intervenant_id ou id_intervenant)
            id_intervenant = intervenant.get('id_intervenant')
            if id_intervenant is None:
                id_intervenant = intervenant.get('intervenant_id', '')
            item_id = QTableWidgetItem(str(id_intervenant))
            item_id.setData(Qt.UserRole, id_intervenant)
            self.tbl_intervenants.setItem(row, 0, item_id)
            # Nom
            self.tbl_intervenants.setItem(row, 1, QTableWidgetItem(self.tr(intervenant.get('nom', ''))))
            # Type (interne/externe)
            type_text = self.tr("Interne") if "technicien_id" in intervenant else self.tr("Externe")
            self.tbl_intervenants.setItem(row, 2, QTableWidgetItem(type_text))
            type_text = self.tr("Interne") if "technicien_id" in intervenant else self.tr("Externe")
            self.tbl_intervenants.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Heures
            heures_item = QTableWidgetItem(self.tr("%1").replace("%1", f"{intervenant.get('heures', 0):.1f}"))
            heures_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_intervenants.setItem(row, 3, heures_item)
            
            # Coût horaire
            cout_h_item = QTableWidgetItem(self.tr("%1").replace("%1", self._format_currency(intervenant.get('cout_horaire', 0))))
            cout_h_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_intervenants.setItem(row, 4, cout_h_item)
            
            # Coût total
            cout_total_item = QTableWidgetItem(self.tr("%1").replace("%1", self._format_currency(intervenant.get('cout_total', 0))))
            cout_total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_intervenants.setItem(row, 5, cout_total_item)
    
    def _populate_frais_table(self):
        """Remplit le tableau des frais externes."""
        self.tbl_frais.setRowCount(0)
        
        if not self.cout_data:
            return
        
        frais_par_type = self.cout_data.get('detail', {}).get('frais_externes', {}).get('par_type', {})
        
        # Convertir la structure par type en liste plate
        all_frais = []
        for type_frais, frais_list in frais_par_type.items():
            for frais in frais_list:
                frais['type_affichage'] = self._format_type_frais(type_frais)
                frais['type_frais'] = type_frais
                all_frais.append(frais)
        
        self.tbl_frais.setRowCount(len(all_frais))
        
        for row, frais in enumerate(all_frais):
            # ID
            item_id = QTableWidgetItem(str(frais.get('frais_id', '')))
            item_id.setData(Qt.UserRole, frais.get('frais_id'))
            item_id.setData(Qt.UserRole + 1, frais.get('type_frais'))
            self.tbl_frais.setItem(row, 0, item_id)
            
            # Type
            self.tbl_frais.setItem(row, 1, QTableWidgetItem(self.tr(frais.get('type_affichage', ''))))
            
            # Description
            self.tbl_frais.setItem(row, 2, QTableWidgetItem(self.tr(frais.get('description', ''))))
            
            # Montant unitaire
            montant_item = QTableWidgetItem(self.tr("%1").replace("%1", self._format_currency(frais.get('montant', 0))))
            montant_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_frais.setItem(row, 3, montant_item)
            
            # Quantité
            qte_item = QTableWidgetItem(self.tr("%1").replace("%1", str(frais.get('quantite', 1))))
            qte_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_frais.setItem(row, 4, qte_item)
            
            # Montant total
            total_item = QTableWidgetItem(self.tr("%1").replace("%1", self._format_currency(frais.get('montant_total', 0))))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_frais.setItem(row, 5, total_item)
            
            # Fournisseur
            self.tbl_frais.setItem(row, 6, QTableWidgetItem(self.tr(frais.get('fournisseur', ''))))
    
    def _clear_all(self):
        """Réinitialise tous les contrôles."""
        self.cout_data = None
        self.tbl_intervenants.setRowCount(0)
        self.tbl_frais.setRowCount(0)
        self._clear_summary()
    
    def _format_type_frais(self, type_frais):
        """Formate le type de frais pour l'affichage."""
        mapping = {
            "PIECE_EXTERNE": self.tr("Pièce externe"),
            "DEPLACEMENT": self.tr("Frais de déplacement"),
            "SOUS_TRAITANCE": self.tr("Sous-traitance"),
            "AUTRE": self.tr("Autre frais")
        }
        return mapping.get(type_frais, self.tr(type_frais))
    
    def on_intervenant_selection_changed(self):
        """Gère le changement de sélection dans le tableau des intervenants."""
        selected_rows = self.tbl_intervenants.selectedItems()
        self.btn_edit_intervenant.setEnabled(len(selected_rows) > 0)
        self.btn_delete_intervenant.setEnabled(len(selected_rows) > 0)
    
    def on_frais_selection_changed(self):
        """Gère le changement de sélection dans le tableau des frais."""
        selected_rows = self.tbl_frais.selectedItems()
        self.btn_edit_frais.setEnabled(len(selected_rows) > 0)
        self.btn_delete_frais.setEnabled(len(selected_rows) > 0)
    
    def ajouter_intervenant(self):
        """Ajoute un nouvel intervenant."""
        if not self.maintenance_id or not self.maintenance_service:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Aucune maintenance sélectionnée."))
            return
        
        try:
            # Récupérer la liste des techniciens
            techniciens = self.maintenance_service.get_all_techniciens()
            
            # Ouvrir le dialogue
            dialog = IntervenantDialog(
                parent=self,
                techniciens=techniciens,
                maintenance_id=self.maintenance_id
            )
            
            if dialog.exec_() == IntervenantDialog.Accepted:
                # Récupérer les données du formulaire
                data = dialog.get_form_data()
                
                # Appeler le service pour ajouter l'intervenant
                self.maintenance_service.add_intervenant(data)
                
                # Recharger les données
                self.charger_donnees()
                
                # Émettre le signal de modification
                self.coutsModifies.emit()
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'un intervenant: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur"), 
                self.tr("Impossible d'ajouter l'intervenant : %1").replace("%1", str(e))
            )
    
    def modifier_intervenant(self):
        """Modifie l'intervenant sélectionné."""
        if not self.maintenance_id or not self.maintenance_service:
            return
        
        # Récupérer l'ID de l'intervenant sélectionné
        selected_items = self.tbl_intervenants.selectedItems()
        if not selected_items:
            return
        
        # Récupérer l'ID depuis la première colonne de la ligne sélectionnée
        row = selected_items[0].row()
        intervenant_id_item = self.tbl_intervenants.item(row, 0)
        intervenant_id = intervenant_id_item.data(Qt.UserRole)
        
        try:
            # Récupérer l'intervenant
            intervenant = self.maintenance_service.get_intervenant_by_id(intervenant_id)
            if not intervenant:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Intervenant ID %1 non trouvé.").replace("%1", str(intervenant_id)))
                return
            
            # Récupérer la liste des techniciens
            techniciens = self.maintenance_service.get_all_techniciens()
            
            # Ouvrir le dialogue
            dialog = IntervenantDialog(
                parent=self,
                techniciens=techniciens,
                intervenant=intervenant
            )
            
            if dialog.exec_() == IntervenantDialog.Accepted:
                # Récupérer les données du formulaire
                data = dialog.get_form_data()
                
                # Appeler le service pour modifier l'intervenant
                self.maintenance_service.update_intervenant(intervenant_id, data)
                
                # Recharger les données
                self.charger_donnees()
                
                # Émettre le signal de modification
                self.coutsModifies.emit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la modification d'un intervenant: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur"), 
                self.tr("Impossible de modifier l'intervenant : %1").replace("%1", str(e))
            )
    
    def supprimer_intervenant(self):
        """Supprime l'intervenant sélectionné."""
        if not self.maintenance_id or not self.maintenance_service:
            return
        
        # Récupérer l'ID de l'intervenant sélectionné
        selected_items = self.tbl_intervenants.selectedItems()
        if not selected_items:
            return
        
        # Récupérer l'ID depuis la première colonne de la ligne sélectionnée
        row = selected_items[0].row()
        intervenant_id_item = self.tbl_intervenants.item(row, 0)
        intervenant_id = intervenant_id_item.data(Qt.UserRole)
        
        if not intervenant_id:
            # Essayer de récupérer comme texte brut si UserRole ne fonctionne pas
            intervenant_id = intervenant_id_item.text()
        try:
            intervenant_id = int(intervenant_id)
        except Exception:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'intervenant sélectionné."))
            return

        # Confirmation
        nom_intervenant = self.tbl_intervenants.item(row, 1).text()
        reply = QMessageBox.question(
            self,
            self.tr("Confirmation"),
            self.tr("Êtes-vous sûr de vouloir supprimer l'intervenant '%1' ?").replace("%1", nom_intervenant),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Appeler le service pour supprimer l'intervenant
            success = self.maintenance_service.delete_intervenant(intervenant_id)
            
            if success:
                # Recharger les données
                self.charger_donnees()
                
                # Émettre le signal de modification
                self.coutsModifies.emit()
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer l'intervenant."))
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un intervenant: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur"), 
                self.tr("Impossible de supprimer l'intervenant : %1").replace("%1", str(e))
            )
    
    def ajouter_frais(self):
        """Ajoute un nouveau frais externe."""
        if not self.maintenance_id or not self.maintenance_service:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Aucune maintenance sélectionnée."))
            return
        
        try:
            # Ouvrir le dialogue
            dialog = FraisExterneDialog(
                parent=self,
                maintenance_id=self.maintenance_id
            )
            
            if dialog.exec_() == FraisExterneDialog.Accepted:
                # Récupérer les données du formulaire
                data = dialog.get_form_data()
                
                # Appeler le service pour ajouter le frais
                self.maintenance_service.add_frais_externe(data)
                
                # Recharger les données
                self.charger_donnees()
                
                # Émettre le signal de modification
                self.coutsModifies.emit()
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'un frais externe: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur"), 
                self.tr("Impossible d'ajouter le frais externe : %1").replace("%1", str(e))
            )
    
    def modifier_frais(self):
        """Modifie le frais externe sélectionné."""
        if not self.maintenance_id or not self.maintenance_service:
            return
        
        # Récupérer l'ID du frais sélectionné
        selected_items = self.tbl_frais.selectedItems()
        if not selected_items:
            return
        
        # Récupérer l'ID depuis la première colonne de la ligne sélectionnée
        row = selected_items[0].row()
        frais_id_item = self.tbl_frais.item(row, 0)
        frais_id = frais_id_item.data(Qt.UserRole)
        
        try:
            # Récupérer le frais
            frais = self.maintenance_service.get_frais_externe_by_id(frais_id)
            if not frais:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Frais externe ID %1 non trouvé.").replace("%1", str(frais_id)))
                return
            
            # Ouvrir le dialogue
            dialog = FraisExterneDialog(
                parent=self,
                frais=frais
            )
            
            if dialog.exec_() == FraisExterneDialog.Accepted:
                # Récupérer les données du formulaire
                data = dialog.get_form_data()
                
                # Appeler le service pour modifier le frais
                self.maintenance_service.update_frais_externe(frais_id, data)
                
                # Recharger les données
                self.charger_donnees()
                
                # Émettre le signal de modification
                self.coutsModifies.emit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la modification d'un frais externe: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur"), 
                self.tr("Impossible de modifier le frais externe : %1").replace("%1", str(e))
            )
    
    def supprimer_frais(self):
        """Supprime le frais externe sélectionné."""
        if not self.maintenance_id or not self.maintenance_service:
            return
        
        # Récupérer l'ID du frais sélectionné
        selected_items = self.tbl_frais.selectedItems()
        if not selected_items:
            return
        
        # Récupérer l'ID depuis la première colonne de la ligne sélectionnée
        row = selected_items[0].row()
        frais_id_item = self.tbl_frais.item(row, 0)
        frais_id = frais_id_item.data(Qt.UserRole)
        
        # Récupérer des informations pour la confirmation
        description = self.tbl_frais.item(row, 2).text()
        type_frais = self.tbl_frais.item(row, 1).text()
        
        # Confirmation
        reply = QMessageBox.question(
            self,
            self.tr("Confirmation"),
            self.tr("Êtes-vous sûr de vouloir supprimer le frais '%1' ?\n\n%2").replace("%1", type_frais).replace("%2", description),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Appeler le service pour supprimer le frais
            success = self.maintenance_service.delete_frais_externe(frais_id)
            
            if success:
                # Recharger les données
                self.charger_donnees()
                
                # Émettre le signal de modification
                self.coutsModifies.emit()
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de supprimer le frais externe."))
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un frais externe: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur"), 
                self.tr("Impossible de supprimer le frais externe : %1").replace("%1", str(e))
            )