#!/usr/bin/env python3
"""
Widget spécialisé pour l'analyse des coûts par machine.
Affiche les KPI financiers avec graphiques et tableaux interactifs.
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Imports PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDateEdit, QPushButton, QFrame,
    QScrollArea, QGroupBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QHeaderView, QTextEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QIcon, QPixmap, QPainter
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, QPieSeries

import logging
logger = logging.getLogger(__name__)

from app.core.services.kpi_service import KPIService

class MachineKPIWidget(QWidget):
    """
    Widget d'analyse des coûts par machine.
    
    Fonctionnalités:
    - Tableau des coûts par machine
    - Graphique en barres des top machines coûteuses
    - Graphique en secteurs répartition par site
    - Métriques de synthèse
    - Export Excel
    """
    
    data_requested = Signal(str, dict)  # (data_type, params)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kpi_service = None
        self.current_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # En-tête avec titre et boutons
        header = self.create_header()
        layout.addWidget(header)
        
        # Zone de contrôles/filtres
        controls = self.create_controls()
        layout.addWidget(controls)
        
        # Zone principale avec métriques et graphiques
        main_content = self.create_main_content()
        layout.addWidget(main_content)
        
        # Boutons d'actions
        actions = self.create_actions()
        layout.addWidget(actions)
        
    def create_header(self) -> QWidget:
        """Crée l'en-tête du widget."""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        
        # Titre avec icône
        title_label = QLabel("📊 Analyse des Coûts par Machine")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        return header
        
    def create_controls(self) -> QWidget:
        """Crée la zone de contrôles et filtres."""
        controls = QGroupBox("Filtres et Paramètres")
        layout = QGridLayout(controls)
        
        # Sélection du site
        layout.addWidget(QLabel("Site:"), 0, 0)
        self.site_combo = QComboBox()
        self.site_combo.addItem("Tous les sites", None)
        self.site_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.site_combo, 0, 1)
        
        # Période de début
        layout.addWidget(QLabel("Du:"), 0, 2)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-3))
        self.date_debut.setCalendarPopup(True)
        self.date_debut.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_debut, 0, 3)
        
        # Période de fin
        layout.addWidget(QLabel("Au:"), 0, 4)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_fin, 0, 5)
        
        # Nombre de machines à afficher
        layout.addWidget(QLabel("Top machines:"), 1, 0)
        self.top_machines_spin = QSpinBox()
        self.top_machines_spin.setRange(5, 50)
        self.top_machines_spin.setValue(10)
        self.top_machines_spin.valueChanged.connect(self.on_filter_changed)
        layout.addWidget(self.top_machines_spin, 1, 1)
        
        # Inclure/exclure les machines inactives
        self.include_inactive = QCheckBox("Inclure machines inactives")
        self.include_inactive.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.include_inactive, 1, 2, 1, 2)
        
        layout.setColumnStretch(6, 1)
        return controls
        
    def create_main_content(self) -> QWidget:
        """Crée la zone principale avec métriques et graphiques."""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Métriques de synthèse
        metrics = self.create_metrics_summary()
        layout.addWidget(metrics)
        
        # Conteneur horizontal pour graphiques et tableau
        content_layout = QHBoxLayout()
        
        # Zone gauche: Graphiques
        charts_widget = self.create_charts_section()
        content_layout.addWidget(charts_widget, 2)
        
        # Zone droite: Tableau détaillé
        table_widget = self.create_table_section()
        content_layout.addWidget(table_widget, 1)
        
        layout.addLayout(content_layout)
        return main_widget
        
    def create_metrics_summary(self) -> QWidget:
        """Crée la zone des métriques de synthèse."""
        metrics = QFrame()
        metrics.setFrameStyle(QFrame.StyledPanel)
        metrics.setFixedHeight(120)
        
        layout = QHBoxLayout(metrics)
        
        # Métriques individuelles
        self.total_cost_label = self.create_metric_card("Coût Total", "0 €", "💰")
        self.avg_cost_label = self.create_metric_card("Coût Moyen/Machine", "0 €", "📊")
        self.machine_count_label = self.create_metric_card("Nb Machines", "0", "🏭")
        self.max_cost_label = self.create_metric_card("Machine la Plus Coûteuse", "Aucune", "🔝")
        
        layout.addWidget(self.total_cost_label)
        layout.addWidget(self.avg_cost_label)
        layout.addWidget(self.machine_count_label)
        layout.addWidget(self.max_cost_label)
        
        return metrics
        
    def create_metric_card(self, title: str, value: str, icon: str) -> QWidget:
        """Crée une carte de métrique."""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setLineWidth(1)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icône et titre
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(icon))
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(9)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Valeur
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(14)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Stocker le label de valeur pour la mise à jour
        setattr(card, 'value_label', value_label)
        
        return card
        
    def create_charts_section(self) -> QWidget:
        """Crée la section des graphiques."""
        charts_widget = QWidget()
        layout = QVBoxLayout(charts_widget)
        
        # Graphique en barres - Top machines coûteuses
        bar_group = QGroupBox("Top Machines par Coût")
        bar_layout = QVBoxLayout(bar_group)
        
        self.bar_chart = QChart()
        self.bar_chart.setTitle("Coûts de Maintenance par Machine")
        self.bar_chart_view = QChartView(self.bar_chart)
        self.bar_chart_view.setRenderHint(QPainter.Antialiasing)
        self.bar_chart_view.setMinimumHeight(300)
        
        bar_layout.addWidget(self.bar_chart_view)
        layout.addWidget(bar_group)
        
        # Graphique en secteurs - Répartition par site
        pie_group = QGroupBox("Répartition par Site")
        pie_layout = QVBoxLayout(pie_group)
        
        self.pie_chart = QChart()
        self.pie_chart.setTitle("Coûts par Site")
        self.pie_chart_view = QChartView(self.pie_chart)
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        self.pie_chart_view.setMinimumHeight(300)
        
        pie_layout.addWidget(self.pie_chart_view)
        layout.addWidget(pie_group)
        
        return charts_widget
        
    def create_table_section(self) -> QWidget:
        """Crée la section du tableau détaillé."""
        table_group = QGroupBox("Détail par Machine")
        layout = QVBoxLayout(table_group)
        
        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Machine", "Site", "Type", "Coût Total €", "Nb Interventions", "Coût/Intervention €"
        ])
        
        # Configuration du tableau
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        layout.addWidget(self.table)
        return table_group
        
    def create_actions(self) -> QWidget:
        """Crée la zone des boutons d'actions."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        
        # Bouton export Excel
        export_btn = QPushButton("📊 Exporter Excel")
        export_btn.clicked.connect(self.export_to_excel)
        layout.addWidget(export_btn)
        
        # Bouton export graphique
        export_chart_btn = QPushButton("📈 Exporter Graphiques")
        export_chart_btn.clicked.connect(self.export_charts)
        layout.addWidget(export_chart_btn)
        
        layout.addStretch()
        
        # Bouton rapport détaillé
        report_btn = QPushButton("📋 Rapport Détaillé")
        report_btn.clicked.connect(self.generate_report)
        layout.addWidget(report_btn)
        
        return actions
        
    def load_data(self, periode_debut: date, periode_fin: date, site_id: Optional[int] = None):
        """Charge les données pour la période et le site spécifiés."""
        try:
            if KPIService is None:
                QMessageBox.warning(self, "Erreur", "Service KPI non disponible")
                return
                
            if self.kpi_service is None:
                self.kpi_service = KPIService()
            
            # Charger les données de coûts par machine
            data = self.kpi_service.get_couts_par_machine(
                periode_debut=periode_debut,
                periode_fin=periode_fin,
                site_id=site_id,
                limite=self.top_machines_spin.value()
            )
            
            self.current_data = data
            self.update_display()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données machine: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
            
    def update_display(self):
        """Met à jour l'affichage avec les données actuelles."""
        if not self.current_data:
            return
            
        # Mettre à jour les métriques
        self.update_metrics()
        
        # Mettre à jour les graphiques
        self.update_bar_chart()
        self.update_pie_chart()
        
        # Mettre à jour le tableau
        self.update_table()
        
    def update_metrics(self):
        """Met à jour les métriques de synthèse."""
        data = self.current_data
        
        # Calculer les métriques
        total_cost = sum(item.get('cout_total', 0) for item in data)
        machine_count = len(data)
        avg_cost = total_cost / machine_count if machine_count > 0 else 0
        
        # Machine la plus coûteuse
        max_machine = max(data, key=lambda x: x.get('cout_total', 0)) if data else None
        max_machine_text = max_machine.get('nom_machine', 'Aucune') if max_machine else 'Aucune'
        
        # Mettre à jour les labels
        self.total_cost_label.value_label.setText(f"{total_cost:,.0f} €")
        self.avg_cost_label.value_label.setText(f"{avg_cost:,.0f} €")
        self.machine_count_label.value_label.setText(str(machine_count))
        self.max_cost_label.value_label.setText(max_machine_text)
        
    def update_bar_chart(self):
        """Met à jour le graphique en barres."""
        self.bar_chart.removeAllSeries()
        
        if not self.current_data:
            return
            
        # Créer les données du graphique
        bar_set = QBarSet("Coût de Maintenance")
        categories = []
        
        for item in self.current_data[:self.top_machines_spin.value()]:
            bar_set.append(item.get('cout_total', 0))
            categories.append(item.get('nom_machine', 'Inconnue')[:15])  # Limiter la longueur
            
        # Créer la série
        series = QBarSeries()
        series.append(bar_set)
        
        # Ajouter la série au graphique
        self.bar_chart.addSeries(series)
        
        # Configurer les axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-45)
        self.bar_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Coût (€)")
        self.bar_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
    def update_pie_chart(self):
        """Met à jour le graphique en secteurs."""
        self.pie_chart.removeAllSeries()
        
        if not self.current_data:
            return
            
        # Regrouper par site
        sites_data = {}
        for item in self.current_data:
            site = item.get('nom_site', 'Site Inconnu')
            cout = item.get('cout_total', 0)
            sites_data[site] = sites_data.get(site, 0) + cout
            
        # Créer la série pie
        series = QPieSeries()
        
        for site, cout in sites_data.items():
            slice_pie = series.append(f"{site}", cout)
            slice_pie.setLabelVisible(True)
            
        # Ajouter la série au graphique
        self.pie_chart.addSeries(series)
        
    def update_table(self):
        """Met à jour le tableau détaillé."""
        self.table.setRowCount(len(self.current_data))
        
        for row, item in enumerate(self.current_data):
            # Machine
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('nom_machine', ''))))
            
            # Site
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get('nom_site', ''))))
            
            # Type
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get('type_machine', ''))))
            
            # Coût total
            cout_total = item.get('cout_total', 0)
            self.table.setItem(row, 3, QTableWidgetItem(f"{cout_total:,.2f}"))
            
            # Nombre d'interventions
            nb_interventions = item.get('nb_interventions', 0)
            self.table.setItem(row, 4, QTableWidgetItem(str(nb_interventions)))
            
            # Coût par intervention
            cout_par_intervention = cout_total / nb_interventions if nb_interventions > 0 else 0
            self.table.setItem(row, 5, QTableWidgetItem(f"{cout_par_intervention:,.2f}"))
            
    def on_filter_changed(self):
        """Gestionnaire de changement de filtre."""
        # Déclencher un rechargement des données avec un délai
        if hasattr(self, '_reload_timer'):
            self._reload_timer.stop()
        
        self._reload_timer = QTimer()
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self.refresh_data)
        self._reload_timer.start(500)  # Délai de 500ms
        
    def refresh_data(self):
        """Actualise les données avec les filtres actuels."""
        debut = self.date_debut.date().toPython()
        fin = self.date_fin.date().toPython()
        site_id = self.site_combo.currentData()
        
        self.load_data(debut, fin, site_id)
        
    def export_to_excel(self):
        """Exporte les données vers Excel."""
        try:
            if not self.current_data:
                QMessageBox.information(self, "Info", "Aucune donnée à exporter")
                return
                
            # TODO: Implémenter l'export Excel
            QMessageBox.information(self, "Info", "Export Excel - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
            
    def export_charts(self):
        """Exporte les graphiques."""
        try:
            # TODO: Implémenter l'export des graphiques
            QMessageBox.information(self, "Info", "Export graphiques - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export des graphiques: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
            
    def generate_report(self):
        """Génère un rapport détaillé."""
        try:
            # TODO: Implémenter la génération de rapport
            QMessageBox.information(self, "Info", "Génération de rapport - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")


if __name__ == "__main__":
    """Test standalone du widget."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = MachineKPIWidget()
    widget.show()
    widget.resize(1200, 800)
    
    # Simuler des données de test
    test_data = [
        {
            'nom_machine': 'Machine A',
            'nom_site': 'Site 1',
            'type_machine': 'Production',
            'cout_total': 5000.50,
            'nb_interventions': 12
        },
        {
            'nom_machine': 'Machine B',
            'nom_site': 'Site 1',
            'type_machine': 'Conditionnement',
            'cout_total': 3500.75,
            'nb_interventions': 8
        },
        {
            'nom_machine': 'Machine C',
            'nom_site': 'Site 2',
            'type_machine': 'Production',
            'cout_total': 7200.25,
            'nb_interventions': 15
        }
    ]
    
    widget.current_data = test_data
    widget.update_display()
    
    sys.exit(app.exec())
