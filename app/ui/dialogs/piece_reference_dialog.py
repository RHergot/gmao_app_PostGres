# gmao_app/app/ui/dialogs/piece_reference_dialog.py
"""
Dialogue pour sélectionner une référence de pièce à commander, saisir la quantité et le numéro de lot (optionnel).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt
from typing import Optional, Dict, Any

class PieceReferenceDialog(QDialog):
    def __init__(self, stock_service, parent=None):
        super().__init__(parent)
        self.stock_service = stock_service
        self.selected_piece_data: Optional[Dict[str, Any]] = None
        self.setWindowTitle(self.tr("Sélectionner une référence de pièce"))
        self.setMinimumWidth(650)
        self.setMinimumHeight(400)

        # Widgets
        self.search_input = QLineEdit(placeholderText=self.tr("Rechercher par Réf ou Nom..."))
        self.table_widget = QTableWidget()
        self.setup_table()
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 9999)
        self.quantity_spinbox.setValue(1)
        self.lot_input = QLineEdit(placeholderText=self.tr("N° de lot (optionnel)"))
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        # Layout
        main_layout = QVBoxLayout(self)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(self.tr("Rechercher:")))
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(QLabel(self.tr("Références de pièces disponibles :")))
        main_layout.addWidget(self.table_widget)
        selection_layout = QFormLayout()
        selection_layout.addRow(self.tr("Quantité à commander:"), self.quantity_spinbox)
        selection_layout.addRow(self.tr("N° de lot:"), self.lot_input)
        main_layout.addLayout(selection_layout)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        # Connexions
        self.search_input.textChanged.connect(self.refresh_table)
        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.refresh_table()

    def setup_table(self):
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "ID", "Référence", "Nom", "Unité", "Catégorie", "Prix Unitaire"
        ])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnHidden(0, True)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

    def refresh_table(self):
        search_term = self.search_input.text().lower()
        pieces = self.stock_service.get_all_pieces()
        filtered = [p for p in pieces if search_term in p.reference.lower() or search_term in p.nom.lower()]
        self.table_widget.setRowCount(0)
        for piece in filtered:
            row = self.table_widget.rowCount()
            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(piece.id_piece)))
            self.table_widget.setItem(row, 1, QTableWidgetItem(piece.reference))
            self.table_widget.setItem(row, 2, QTableWidgetItem(piece.nom))
            self.table_widget.setItem(row, 3, QTableWidgetItem(piece.unite or ""))
            self.table_widget.setItem(row, 4, QTableWidgetItem(piece.categorie or ""))
            self.table_widget.setItem(row, 5, QTableWidgetItem(f"{getattr(piece, 'prix_unitaire', 0.0):.2f}"))

    def on_selection_changed(self):
        selected = self.table_widget.selectedItems()
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(selected))
        if selected:
            row = self.table_widget.currentRow()
            self.selected_piece_data = {
                'id_piece': int(self.table_widget.item(row, 0).text()),
                'reference': self.table_widget.item(row, 1).text(),
                'nom': self.table_widget.item(row, 2).text(),
                'unite': self.table_widget.item(row, 3).text(),
                'categorie': self.table_widget.item(row, 4).text(),
                'prix_unitaire': float(self.table_widget.item(row, 5).text()),
            }
        else:
            self.selected_piece_data = None

    def accept(self):
        if not self.selected_piece_data:
            return
        self.selected_piece_data['quantite'] = self.quantity_spinbox.value()
        self.selected_piece_data['lot'] = self.lot_input.text().strip() or None
        super().accept()
