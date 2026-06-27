#!/usr/bin/env python3
"""
Widget spécialisé pour l'analyse des coûts par site.
Affiche les KPI financiers avec comparaisons entre sites.
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
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, 
    QPieSeries, QLineSeries, QDateTimeAxis
)

# Ajouter le chemin pour les imports de l'app
current_dir = os.path.dirname(os.path.abspath(__file__))
app_root = os.path.join(current_dir, '..', '..', '..')
project_root = os.path.join(current_dir, '..', '..', '..', '..')
sys.path.insert(0, app_root)
sys.path.insert(0, project_root)

import logging
logger = logging.getLogger(__name__)

try:
    from core.services.kpi_service import KPIService
    setup_logging = None
except ImportError as e:
    logger.debug("Erreur d'import KPIService: %s", e)
    try:
        from app.core.services.kpi_service import KPIService
        setup_logging = None
    except ImportError as e2:
        logger.debug("Erreur d'import KPIService (fallback): %s", e2)
        KPIService = None
        setup_logging = None

class SiteKPIWidget(QWidget):
    """
    Widget d'analyse des coûts par site.
    
    Fonctionnalités:
    - Comparaison des coûts entre sites
    - Évolution temporelle par site
    - Métriques de performance par site
    - Analyse de la répartition des coûts
    - Export et rapports
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
        title_label = QLabel("🏢 Analyse des Coûts par Site")
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
        
        # Période de début
        layout.addWidget(QLabel("Du:"), 0, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-6))
        self.date_debut.setCalendarPopup(True)
        self.date_debut.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_debut, 0, 1)
        
        # Période de fin
        layout.addWidget(QLabel("Au:"), 0, 2)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        self.date_fin.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_fin, 0, 3)
        
        # Type d'analyse
        layout.addWidget(QLabel("Analyse:"), 0, 4)
        self.analyse_combo = QComboBox()
        self.analyse_combo.addItems([
            "Vue d'ensemble",
            "Coûts de maintenance",
            "Coûts de pièces",
            "Coûts de main d'œuvre",
            "Coûts externes"
        ])
        self.analyse_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.analyse_combo, 0, 5)
        
        # Groupement temporel
        layout.addWidget(QLabel("Groupement:"), 1, 0)
        self.groupement_combo = QComboBox()
        self.groupement_combo.addItems(["Par mois", "Par trimestre", "Par semestre"])
        self.groupement_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.groupement_combo, 1, 1)
        
        # Inclure sites inactifs
        self.include_inactive = QCheckBox("Inclure sites sans activité")
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
        
        # Zone droite: Tableau et métriques détaillées
        details_widget = self.create_details_section()
        content_layout.addWidget(details_widget, 1)
        
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
        self.avg_cost_label = self.create_metric_card("Coût Moyen/Site", "0 €", "📊")
        self.site_count_label = self.create_metric_card("Nb Sites Actifs", "0", "🏢")
        self.best_site_label = self.create_metric_card("Site le Plus Économique", "Aucun", "🏆")
        
        layout.addWidget(self.total_cost_label)
        layout.addWidget(self.avg_cost_label)
        layout.addWidget(self.site_count_label)
        layout.addWidget(self.best_site_label)
        
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
        
        # Graphique en barres - Comparaison des sites
        bar_group = QGroupBox("Comparaison des Coûts par Site")
        bar_layout = QVBoxLayout(bar_group)
        
        self.bar_chart = QChart()
        self.bar_chart.setTitle("Coûts de Maintenance par Site")
        self.bar_chart_view = QChartView(self.bar_chart)
        self.bar_chart_view.setRenderHint(QPainter.Antialiasing)
        self.bar_chart_view.setMinimumHeight(250)
        
        bar_layout.addWidget(self.bar_chart_view)
        layout.addWidget(bar_group)
        
        # Graphique linéaire - Évolution temporelle
        line_group = QGroupBox("Évolution des Coûts dans le Temps")
        line_layout = QVBoxLayout(line_group)
        
        self.line_chart = QChart()
        self.line_chart.setTitle("Évolution Temporelle par Site")
        self.line_chart_view = QChartView(self.line_chart)
        self.line_chart_view.setRenderHint(QPainter.Antialiasing)
        self.line_chart_view.setMinimumHeight(250)
        
        line_layout.addWidget(self.line_chart_view)
        layout.addWidget(line_group)
        
        return charts_widget
        
    def create_details_section(self) -> QWidget:
        """Crée la section des détails et du tableau."""
        details_widget = QWidget()
        layout = QVBoxLayout(details_widget)
        
        # Tableau comparatif des sites
        table_group = QGroupBox("Comparaison Détaillée")
        table_layout = QVBoxLayout(table_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Site", "Coût Total €", "Nb Machines", "Nb Interventions", 
            "Coût/Machine €", "Coût/Intervention €", "Efficacité"
        ])
        
        # Configuration du tableau
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)
        
        # Zone d'analyse rapide
        analysis_group = QGroupBox("Analyse Rapide")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setMaximumHeight(150)
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlainText("Chargez les données pour voir l'analyse...")
        
        analysis_layout.addWidget(self.analysis_text)
        layout.addWidget(analysis_group)
        
        return details_widget
        
    def create_actions(self) -> QWidget:
        """Crée la zone des boutons d'actions."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        
        # Bouton export Excel
        export_btn = QPushButton("📊 Exporter Excel")
        export_btn.clicked.connect(self.export_to_excel)
        layout.addWidget(export_btn)
        
        # Bouton comparaison approfondie
        compare_btn = QPushButton("🔍 Analyse Comparative")
        compare_btn.clicked.connect(self.detailed_comparison)
        layout.addWidget(compare_btn)
        
        layout.addStretch()
        
        # Bouton rapport mensuel
        report_btn = QPushButton("📋 Rapport Mensuel")
        report_btn.clicked.connect(self.generate_monthly_report)
        layout.addWidget(report_btn)
        
        return actions
        
    def load_data(self, periode_debut: date, periode_fin: date):
        """Charge les données pour la période spécifiée."""
        try:
            if KPIService is None:
                QMessageBox.warning(self, "Erreur", "Service KPI non disponible")
                return
                
            if self.kpi_service is None:
                self.kpi_service = KPIService()
            
            # Charger les données de coûts par site
            data = self.kpi_service.get_couts_par_site(
                periode_debut=periode_debut,
                periode_fin=periode_fin
            )
            
            self.current_data = data
            self.update_display()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données site: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
            
    def update_display(self):
        """Met à jour l'affichage avec les données actuelles."""
        if not self.current_data:
            return
            
        # Mettre à jour les métriques
        self.update_metrics()
        
        # Mettre à jour les graphiques
        self.update_bar_chart()
        self.update_line_chart()
        
        # Mettre à jour le tableau
        self.update_table()
        
        # Mettre à jour l'analyse
        self.update_analysis()
        
    def update_metrics(self):
        """Met à jour les métriques de synthèse."""
        data = self.current_data
        
        if not data:
            return
            
        # Calculer les métriques
        total_cost = sum(item.get('cout_total', 0) for item in data)
        site_count = len([item for item in data if item.get('cout_total', 0) > 0])
        avg_cost = total_cost / site_count if site_count > 0 else 0
        
        # Site le plus économique (coût/machine le plus bas)
        best_site = None
        best_ratio = float('inf')
        for item in data:
            nb_machines = item.get('nb_machines', 0)
            cout = item.get('cout_total', 0)
            if nb_machines > 0 and cout > 0:
                ratio = cout / nb_machines
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_site = item.get('nom_site', 'Inconnu')
        
        # Mettre à jour les labels
        self.total_cost_label.value_label.setText(f"{total_cost:,.0f} €")
        self.avg_cost_label.value_label.setText(f"{avg_cost:,.0f} €")
        self.site_count_label.value_label.setText(str(site_count))
        self.best_site_label.value_label.setText(best_site or "Aucun")
        
    def update_bar_chart(self):
        """Met à jour le graphique en barres de comparaison."""
        self.bar_chart.removeAllSeries()
        
        if not self.current_data:
            return
            
        # Créer les données du graphique
        bar_set = QBarSet("Coût Total")
        categories = []
        
        # Trier par coût décroissant
        sorted_data = sorted(self.current_data, 
                           key=lambda x: x.get('cout_total', 0), 
                           reverse=True)
        
        for item in sorted_data:
            if item.get('cout_total', 0) > 0:  # Exclure les sites sans coût
                bar_set.append(item.get('cout_total', 0))
                site_name = item.get('nom_site', 'Inconnu')
                categories.append(site_name[:10])  # Limiter la longueur
        
        if not categories:
            return
            
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
        
    def update_line_chart(self):
        """Met à jour le graphique linéaire d'évolution."""
        self.line_chart.removeAllSeries()
        
        # Pour l'instant, afficher un message
        # TODO: Implémenter l'évolution temporelle réelle
        self.line_chart.setTitle("Évolution Temporelle (À implémenter)")
        
    def update_table(self):
        """Met à jour le tableau détaillé."""
        data = self.current_data
        self.table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Site
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('nom_site', ''))))
            
            # Coût total
            cout_total = item.get('cout_total', 0)
            self.table.setItem(row, 1, QTableWidgetItem(f"{cout_total:,.2f}"))
            
            # Nombre de machines
            nb_machines = item.get('nb_machines', 0)
            self.table.setItem(row, 2, QTableWidgetItem(str(nb_machines)))
            
            # Nombre d'interventions
            nb_interventions = item.get('nb_interventions', 0)
            self.table.setItem(row, 3, QTableWidgetItem(str(nb_interventions)))
            
            # Coût par machine
            cout_par_machine = cout_total / nb_machines if nb_machines > 0 else 0
            self.table.setItem(row, 4, QTableWidgetItem(f"{cout_par_machine:,.2f}"))
            
            # Coût par intervention
            cout_par_intervention = cout_total / nb_interventions if nb_interventions > 0 else 0
            self.table.setItem(row, 5, QTableWidgetItem(f"{cout_par_intervention:,.2f}"))
            
            # Efficacité (basée sur le coût par machine, inversé et normalisé)
            if cout_par_machine > 0:
                # Plus le coût est bas, plus l'efficacité est haute
                max_cout = max(item.get('cout_total', 0) / item.get('nb_machines', 1) 
                             for item in data if item.get('nb_machines', 0) > 0)
                efficacite = (1 - (cout_par_machine / max_cout)) * 100 if max_cout > 0 else 0
                self.table.setItem(row, 6, QTableWidgetItem(f"{efficacite:.1f}%"))
            else:
                self.table.setItem(row, 6, QTableWidgetItem("N/A"))
                
    def update_analysis(self):
        """Met à jour l'analyse rapide."""
        if not self.current_data:
            self.analysis_text.setPlainText("Aucune donnée disponible pour l'analyse.")
            return
            
        # Analyse simple des données
        total_sites = len(self.current_data)
        active_sites = len([s for s in self.current_data if s.get('cout_total', 0) > 0])
        total_cost = sum(s.get('cout_total', 0) for s in self.current_data)
        
        if active_sites == 0:
            self.analysis_text.setPlainText("Aucun site avec activité de maintenance détectée.")
            return
            
        # Site le plus coûteux
        most_expensive = max(self.current_data, key=lambda x: x.get('cout_total', 0))
        
        # Site le plus efficace (coût/machine le plus bas)
        efficient_sites = [s for s in self.current_data 
                          if s.get('nb_machines', 0) > 0 and s.get('cout_total', 0) > 0]
        
        most_efficient = None
        if efficient_sites:
            most_efficient = min(efficient_sites, 
                                key=lambda x: x.get('cout_total', 0) / x.get('nb_machines', 1))
        
        # Générer le texte d'analyse
        analysis = f"""📊 ANALYSE DES COÛTS PAR SITE

🔍 Vue d'ensemble:
• {total_sites} sites au total, {active_sites} actifs
• Coût total: {total_cost:,.0f} €
• Coût moyen par site actif: {total_cost/active_sites:,.0f} €

💰 Site le plus coûteux:
• {most_expensive.get('nom_site', 'Inconnu')}: {most_expensive.get('cout_total', 0):,.0f} €

⚡ Site le plus efficace:"""

        if most_efficient:
            cout_machine = most_efficient.get('cout_total', 0) / most_efficient.get('nb_machines', 1)
            analysis += f"""
• {most_efficient.get('nom_site', 'Inconnu')}: {cout_machine:,.0f} €/machine"""
        else:
            analysis += "\n• Données insuffisantes"
            
        analysis += f"""

📈 Recommandations:
• Analyser les pratiques du site le plus efficace
• Investiguer les coûts élevés du site le plus coûteux
• Standardiser les procédures entre sites"""

        self.analysis_text.setPlainText(analysis)
        
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
        
        self.load_data(debut, fin)
        
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
            
    def detailed_comparison(self):
        """Lance une analyse comparative détaillée."""
        try:
            # TODO: Implémenter l'analyse comparative approfondie
            QMessageBox.information(self, "Info", "Analyse comparative - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse comparative: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'analyse: {str(e)}")
            
    def generate_monthly_report(self):
        """Génère un rapport mensuel."""
        try:
            # TODO: Implémenter la génération de rapport mensuel
            QMessageBox.information(self, "Info", "Rapport mensuel - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")


if __name__ == "__main__":
    """Test standalone du widget."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = SiteKPIWidget()
    widget.show()
    widget.resize(1400, 900)
    
    # Simuler des données de test
    test_data = [
        {
            'nom_site': 'Site Production A',
            'cout_total': 15000.50,
            'nb_machines': 25,
            'nb_interventions': 45
        },
        {
            'nom_site': 'Site Production B',
            'cout_total': 8500.75,
            'nb_machines': 15,
            'nb_interventions': 28
        },
        {
            'nom_site': 'Site Logistique',
            'cout_total': 3200.25,
            'nb_machines': 8,
            'nb_interventions': 12
        },
        {
            'nom_site': 'Site Conditionnement',
            'cout_total': 12000.00,
            'nb_machines': 18,
            'nb_interventions': 35
        }
    ]
    
    widget.current_data = test_data
    widget.update_display()
    
    sys.exit(app.exec())
