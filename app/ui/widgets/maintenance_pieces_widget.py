# gmao_app/app/ui/widgets/maintenance_pieces_widget.py
"""
Widget pour afficher et gérer les pièces utilisées dans une maintenance.
"""
import logging
from decimal import Decimal
from typing import Optional, Dict, List, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor

logger = logging.getLogger(__name__)

class MaintenancePiecesWidget(QWidget):
    """Widget affichant les pièces utilisées lors d'une maintenance."""
    
    # Signaux
    piecesModifiees = Signal()  # Émis lorsque les pièces sont modifiées
    
    def __init__(self, parent=None, maintenance_id=None, maintenance_service=None, stock_service=None):
        """
        Initialise le widget des pièces de maintenance.
        
        Args:
            parent: Widget parent
            maintenance_id: ID de la maintenance à afficher
            maintenance_service: Service pour les opérations sur la maintenance
            stock_service: Service pour les opérations sur le stock et les pièces
        """
        super().__init__(parent)
        self.parent_view = parent
        self.maintenance_id = maintenance_id
        self.maintenance_service = maintenance_service
        self.stock_service = stock_service
        
        self._setup_ui()
        
        # Initialisation différée si les services sont fournis plus tard
        if self.maintenance_id and self.maintenance_service and self.stock_service:
            self.charger_donnees()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # En-tête : titre et bouton de rafraîchissement
        header_layout = QHBoxLayout()
        self.lbl_titre = QLabel(self.tr("Pièces utilisées"))
        self.lbl_titre.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.lbl_titre)
        
        self.btn_refresh = QPushButton(self.tr("Actualiser"))
        self.btn_refresh.setIcon(QIcon.fromTheme("view-refresh"))
        self.btn_refresh.clicked.connect(self.charger_donnees)
        header_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Résumé des pièces
        self.pieces_summary_widget = QFrame()
        self.pieces_summary_widget.setFrameShape(QFrame.StyledPanel)
        self.pieces_summary_widget.setStyleSheet("background-color: #f5f5f5;")
        
        summary_layout = QVBoxLayout(self.pieces_summary_widget)
        
        # Total des pièces
        total_layout = QHBoxLayout()
        self.lbl_pieces_total_titre = QLabel(self.tr("Nombre total de pièces :"))
        self.lbl_pieces_total_titre.setStyleSheet("font-weight: bold;")
        self.lbl_pieces_total = QLabel("0")
        self.lbl_pieces_total.setStyleSheet("font-weight: bold;")
        self.lbl_pieces_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.lbl_cout_pieces_titre = QLabel(self.tr("Coût total des pièces :"))
        self.lbl_cout_pieces_titre.setStyleSheet("font-weight: bold;")
        self.lbl_cout_pieces = QLabel(self.tr("0,00 €"))
        self.lbl_cout_pieces.setStyleSheet("font-weight: bold; color: #006400;")
        self.lbl_cout_pieces.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        total_layout.addWidget(self.lbl_pieces_total_titre)
        total_layout.addWidget(self.lbl_pieces_total)
        total_layout.addStretch()
        total_layout.addWidget(self.lbl_cout_pieces_titre)
        total_layout.addWidget(self.lbl_cout_pieces)
        
        summary_layout.addLayout(total_layout)
        
        layout.addWidget(self.pieces_summary_widget)
        
        # Tableau des pièces
        self.tbl_pieces = QTableWidget()
        self.tbl_pieces.setColumnCount(7)
        self.tbl_pieces.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Référence"), self.tr("Nom"), self.tr("Stock dispo"), self.tr("Quantité"), self.tr("Prix unitaire"), self.tr("Total")
        ])
        self.tbl_pieces.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_pieces.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_pieces.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_pieces.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tbl_pieces.verticalHeader().setVisible(False)
        self.tbl_pieces.setAlternatingRowColors(True)
        self.tbl_pieces.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_pieces.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.tbl_pieces)
        
        # Informations
        self.lbl_info = QLabel(self.tr("Les pièces sont consommées automatiquement depuis le stock lors de l'enregistrement d'une maintenance."))
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
    
    def set_services(self, maintenance_service=None, stock_service=None):
        """Définit les services si non fournis dans le constructeur."""
        if maintenance_service:
            self.maintenance_service = maintenance_service
        
        if stock_service:
            self.stock_service = stock_service
            
        # Recharger les données si les services sont maintenant disponibles
        if self.maintenance_id and self.maintenance_service and self.stock_service:
            self.charger_donnees()
    
    def set_maintenance_id(self, maintenance_id):
        """Définit l'ID de la maintenance et recharge les données."""
        self.maintenance_id = maintenance_id
        
        # Essayer de récupérer les services depuis le parent si nécessaire
        if not self.maintenance_service and hasattr(self.parent_view, 'maintenance_service'):
            self.maintenance_service = self.parent_view.maintenance_service
            
        if not self.stock_service and hasattr(self.parent_view, 'stock_service'):
            self.stock_service = self.parent_view.stock_service
            
        self.charger_donnees()
    
    def charger_donnees(self):
        """Charge les données des pièces pour la maintenance actuelle."""
        if not self.maintenance_id or not self.maintenance_service or not self.stock_service:
            self._clear_all()
            return
        
        try:
            # Récupérer les pièces utilisées pour cette maintenance
            self.intervention_pieces = self.maintenance_service.get_intervention_pieces_by_maintenance_id(self.maintenance_id)
            
            # Récupérer les détails des pièces et calculer le coût total
            self.pieces_details = []
            cout_total = 0
            total_pieces = 0
            
            for ip in self.intervention_pieces:
                # Récupérer les détails de la pièce
                piece = self.stock_service.get_piece_by_id(ip.piece_id)
                if piece:
                    # Calculer le coût pour cette pièce
                    cout_unitaire = piece.prix_unitaire or 0
                    cout_total_piece = cout_unitaire * ip.quantite
                    cout_total += cout_total_piece
                    total_pieces += ip.quantite
                    
                    # Calculer le stock disponible
                    stock_dispo = self.stock_service.get_quantite_disponible(ip.piece_id)
                    
                    # Stocker les détails pour l'affichage
                    self.pieces_details.append({
                        'piece_id': ip.piece_id,
                        'reference': piece.reference,
                        'nom': piece.nom,
                        'stock_dispo': stock_dispo,
                        'quantite': ip.quantite,
                        'cout_unitaire': cout_unitaire,
                        'cout_total': cout_total_piece,
                        'lot': ip.lot
                    })
            
            # Mettre à jour le résumé
            self.lbl_pieces_total.setText(str(total_pieces))
            self.lbl_cout_pieces.setText(self._format_currency(cout_total))
            
            # Remplir le tableau
            self._populate_pieces_table()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des pièces de maintenance: {e}")
            QMessageBox.warning(
                self, 
                self.tr("Erreur de chargement"), 
                self.tr("Impossible de charger les pièces utilisées : %1").replace("%1", str(e))
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
    
    def _populate_pieces_table(self):
        """Remplit le tableau des pièces."""
        self.tbl_pieces.setRowCount(0)
        
        if not hasattr(self, 'pieces_details') or not self.pieces_details:
            return
        
        self.tbl_pieces.setRowCount(len(self.pieces_details))
        
        for row, piece in enumerate(self.pieces_details):
            # ID
            item_id = QTableWidgetItem(str(piece['piece_id']))
            item_id.setData(Qt.UserRole, piece['piece_id'])
            self.tbl_pieces.setItem(row, 0, item_id)
            
            # Référence
            self.tbl_pieces.setItem(row, 1, QTableWidgetItem(self.tr("%1").replace("%1", piece.get('reference', ''))))
            
            # Nom
            self.tbl_pieces.setItem(row, 2, QTableWidgetItem(self.tr("%1").replace("%1", piece.get('nom', ''))))
            
            # Stock disponible
            stock_item = QTableWidgetItem(str(piece.get('stock_dispo', 0)))
            stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_pieces.setItem(row, 3, stock_item)
            
            # Quantité utilisée
            qte_item = QTableWidgetItem(str(piece.get('quantite', 0)))
            qte_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_pieces.setItem(row, 4, qte_item)
            
            # Prix unitaire
            prix_item = QTableWidgetItem(self._format_currency(piece.get('cout_unitaire', 0)))
            prix_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_pieces.setItem(row, 5, prix_item)
            
            # Total
            total_item = QTableWidgetItem(self._format_currency(piece.get('cout_total', 0)))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_pieces.setItem(row, 6, total_item)
    
    def _clear_all(self):
        """Réinitialise tous les contrôles."""
        self.lbl_pieces_total.setText("0")
        self.lbl_cout_pieces.setText("0,00 €")
        self.tbl_pieces.setRowCount(0)
        if hasattr(self, 'pieces_details'):
            self.pieces_details = []
        if hasattr(self, 'intervention_pieces'):
            self.intervention_pieces = []