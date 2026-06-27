#!/usr/bin/env python3
"""
Widget spécialisé pour l'analyse des coûts par équipe.
Affiche les KPI financiers et de performance des équipes de maintenance.
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
    QPieSeries, QLineSeries, QScatterSeries
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

class EquipeKPIWidget(QWidget):
    """
    Widget d'analyse des coûts et performances par équipe.
    
    Fonctionnalités:
    - Performance des équipes de maintenance
    - Coûts par équipe et par type d'intervention
    - Efficacité et productivité
    - Charge de travail et répartition
    - Analyse des compétences
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
        title_label = QLabel("👥 Analyse des Performances par Équipe")
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
        
        # Sélection de l'équipe
        layout.addWidget(QLabel("Équipe:"), 0, 0)
        self.equipe_combo = QComboBox()
        self.equipe_combo.addItem("Toutes les équipes", None)
        self.equipe_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.equipe_combo, 0, 1)
        
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
        
        # Type de vue
        layout.addWidget(QLabel("Vue:"), 1, 0)
        self.vue_combo = QComboBox()
        self.vue_combo.addItems([
            "Performance globale",
            "Coûts par équipe",
            "Efficacité",
            "Charge de travail",
            "Spécialisations"
        ])
        self.vue_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.vue_combo, 1, 1)
        
        # Groupement
        layout.addWidget(QLabel("Grouper par:"), 1, 2)
        self.group_combo = QComboBox()
        self.group_combo.addItems(["Équipe", "Site", "Type intervention"])
        self.group_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.group_combo, 1, 3)
        
        # Inclure équipes inactives
        self.include_inactive = QCheckBox("Inclure équipes inactives")
        self.include_inactive.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.include_inactive, 1, 4, 1, 2)
        
        layout.setColumnStretch(6, 1)
        return controls
        
    def create_main_content(self) -> QWidget:
        """Crée la zone principale avec métriques et graphiques."""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Métriques de synthèse
        metrics = self.create_metrics_summary()
        layout.addWidget(metrics)
        
        # Conteneur horizontal pour graphiques et détails
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
        self.efficiency_label = self.create_metric_card("Efficacité Moyenne", "0%", "⚡")
        self.team_count_label = self.create_metric_card("Nb Équipes Actives", "0", "👥")
        self.best_team_label = self.create_metric_card("Équipe la Plus Efficace", "Aucune", "🏆")
        
        layout.addWidget(self.total_cost_label)
        layout.addWidget(self.efficiency_label)
        layout.addWidget(self.team_count_label)
        layout.addWidget(self.best_team_label)
        
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
        
        # Graphique en barres - Performance par équipe
        bar_group = QGroupBox("Performance par Équipe")
        bar_layout = QVBoxLayout(bar_group)
        
        self.bar_chart = QChart()
        self.bar_chart.setTitle("Coûts et Efficacité par Équipe")
        self.bar_chart_view = QChartView(self.bar_chart)
        self.bar_chart_view.setRenderHint(QPainter.Antialiasing)
        self.bar_chart_view.setMinimumHeight(250)
        
        bar_layout.addWidget(self.bar_chart_view)
        layout.addWidget(bar_group)
        
        # Graphique scatter - Efficacité vs Charge de travail
        scatter_group = QGroupBox("Efficacité vs Charge de Travail")
        scatter_layout = QVBoxLayout(scatter_group)
        
        self.scatter_chart = QChart()
        self.scatter_chart.setTitle("Analyse Efficacité/Charge")
        self.scatter_chart_view = QChartView(self.scatter_chart)
        self.scatter_chart_view.setRenderHint(QPainter.Antialiasing)
        self.scatter_chart_view.setMinimumHeight(250)
        
        scatter_layout.addWidget(self.scatter_chart_view)
        layout.addWidget(scatter_group)
        
        return charts_widget
        
    def create_details_section(self) -> QWidget:
        """Crée la section des détails et du tableau."""
        details_widget = QWidget()
        layout = QVBoxLayout(details_widget)
        
        # Tableau détaillé des équipes
        table_group = QGroupBox("Détail par Équipe")
        table_layout = QVBoxLayout(table_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Équipe", "Nb Interventions", "Coût Total €", "Coût/Inter. €",
            "Temps Moyen", "Efficacité %", "Spécialité", "Site Principal"
        ])
        
        # Configuration du tableau
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)
        
        # Zone d'analyse des compétences
        skills_group = QGroupBox("Analyse des Compétences")
        skills_layout = QVBoxLayout(skills_group)
        
        self.skills_text = QTextEdit()
        self.skills_text.setMaximumHeight(120)
        self.skills_text.setReadOnly(True)
        self.skills_text.setPlainText("Chargez les données pour voir l'analyse des compétences...")
        
        skills_layout.addWidget(self.skills_text)
        layout.addWidget(skills_group)
        
        return details_widget
        
    def create_actions(self) -> QWidget:
        """Crée la zone des boutons d'actions."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        
        # Bouton export Excel
        export_btn = QPushButton("📊 Exporter Excel")
        export_btn.clicked.connect(self.export_to_excel)
        layout.addWidget(export_btn)
        
        # Bouton analyse des compétences
        skills_btn = QPushButton("🎓 Analyse Compétences")
        skills_btn.clicked.connect(self.analyze_skills)
        layout.addWidget(skills_btn)
        
        layout.addStretch()
        
        # Bouton rapport d'équipe
        report_btn = QPushButton("📋 Rapport d'Équipe")
        report_btn.clicked.connect(self.generate_team_report)
        layout.addWidget(report_btn)
        
        return actions
        
    def load_data(self, periode_debut: date, periode_fin: date, equipe_id: Optional[int] = None):
        """Charge les données pour la période et l'équipe spécifiées."""
        try:
            if KPIService is None:
                QMessageBox.warning(self, "Erreur", "Service KPI non disponible")
                return
                
            if self.kpi_service is None:
                self.kpi_service = KPIService()
            
            # Charger les données de performance par équipe
            data = self.kpi_service.get_couts_par_equipe(
                periode_debut=periode_debut,
                periode_fin=periode_fin,
                equipe_id=equipe_id
            )
            
            self.current_data = data
            self.update_display()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données équipe: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
            
    def update_display(self):
        """Met à jour l'affichage avec les données actuelles."""
        if not self.current_data:
            return
            
        # Mettre à jour les métriques
        self.update_metrics()
        
        # Mettre à jour les graphiques
        self.update_bar_chart()
        self.update_scatter_chart()
        
        # Mettre à jour le tableau
        self.update_table()
        
        # Mettre à jour l'analyse des compétences
        self.update_skills_analysis()
        
    def update_metrics(self):
        """Met à jour les métriques de synthèse."""
        data = self.current_data
        
        if not data:
            return
            
        # Calculer les métriques
        total_cost = sum(item.get('cout_total', 0) for item in data)
        team_count = len([item for item in data if item.get('cout_total', 0) > 0])
        
        # Efficacité moyenne (basée sur coût/intervention)
        efficacite_values = []
        for item in data:
            nb_inter = item.get('nb_interventions', 0)
            cout = item.get('cout_total', 0)
            if nb_inter > 0 and cout > 0:
                cout_par_inter = cout / nb_inter
                # Inverse normalisé pour efficacité (plus le coût est bas, plus c'est efficace)
                efficacite_values.append(cout_par_inter)
        
        avg_efficiency = 0
        if efficacite_values:
            max_cout = max(efficacite_values)
            min_cout = min(efficacite_values)
            if max_cout > min_cout:
                avg_efficiency = sum((max_cout - val) / (max_cout - min_cout) * 100 
                                   for val in efficacite_values) / len(efficacite_values)
        
        # Équipe la plus efficace
        best_team = None
        if efficacite_values:
            best_cout = min(efficacite_values)
            for item in data:
                nb_inter = item.get('nb_interventions', 0)
                cout = item.get('cout_total', 0)
                if nb_inter > 0 and cout > 0:
                    if abs((cout / nb_inter) - best_cout) < 0.01:
                        best_team = item.get('nom_equipe', 'Inconnue')
                        break
        
        # Mettre à jour les labels
        self.total_cost_label.value_label.setText(f"{total_cost:,.0f} €")
        self.efficiency_label.value_label.setText(f"{avg_efficiency:.1f}%")
        self.team_count_label.value_label.setText(str(team_count))
        self.best_team_label.value_label.setText(best_team or "Aucune")
        
    def update_bar_chart(self):
        """Met à jour le graphique en barres de performance."""
        self.bar_chart.removeAllSeries()
        
        if not self.current_data:
            return
            
        # Créer les données du graphique - Coûts par équipe
        cost_set = QBarSet("Coût Total")
        intervention_set = QBarSet("Nb Interventions × 100")
        categories = []
        
        # Trier par coût décroissant
        sorted_data = sorted(self.current_data, 
                           key=lambda x: x.get('cout_total', 0), 
                           reverse=True)
        
        for item in sorted_data:
            if item.get('cout_total', 0) > 0:  # Exclure les équipes sans activité
                cost_set.append(item.get('cout_total', 0))
                intervention_set.append(item.get('nb_interventions', 0) * 100)  # Échelle × 100
                team_name = item.get('nom_equipe', 'Équipe Inconnue')
                categories.append(team_name[:15])  # Limiter la longueur
        
        if not categories:
            return
            
        # Créer la série
        series = QBarSeries()
        series.append(cost_set)
        series.append(intervention_set)
        
        # Ajouter la série au graphique
        self.bar_chart.addSeries(series)
        
        # Configurer les axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-45)
        self.bar_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Coût (€) / Interventions × 100")
        self.bar_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
    def update_scatter_chart(self):
        """Met à jour le graphique scatter efficacité/charge."""
        self.scatter_chart.removeAllSeries()
        
        if not self.current_data:
            return
            
        # Créer la série scatter
        series = QScatterSeries()
        series.setName("Équipes")
        series.setMarkerSize(10)
        
        for item in self.current_data:
            nb_inter = item.get('nb_interventions', 0)
            cout_total = item.get('cout_total', 0)
            
            if nb_inter > 0 and cout_total > 0:
                # X = Charge de travail (nb interventions)
                # Y = Efficacité (inverse du coût par intervention, normalisé)
                cout_par_inter = cout_total / nb_inter
                efficacite = 1000 / cout_par_inter if cout_par_inter > 0 else 0  # Inverse pour efficacité
                
                series.append(nb_inter, efficacite)
        
        # Ajouter la série au graphique
        self.scatter_chart.addSeries(series)
        
        # Configurer les axes
        axis_x = QValueAxis()
        axis_x.setTitleText("Charge de Travail (Nb Interventions)")
        self.scatter_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Efficacité (1000/Coût par Intervention)")
        self.scatter_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
    def update_table(self):
        """Met à jour le tableau détaillé."""
        data = self.current_data
        self.table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Équipe
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get('nom_equipe', ''))))
            
            # Nb interventions
            nb_interventions = item.get('nb_interventions', 0)
            self.table.setItem(row, 1, QTableWidgetItem(str(nb_interventions)))
            
            # Coût total
            cout_total = item.get('cout_total', 0)
            self.table.setItem(row, 2, QTableWidgetItem(f"{cout_total:,.2f}"))
            
            # Coût par intervention
            cout_par_inter = cout_total / nb_interventions if nb_interventions > 0 else 0
            self.table.setItem(row, 3, QTableWidgetItem(f"{cout_par_inter:,.2f}"))
            
            # Temps moyen (simulé pour l'exemple)
            temps_moyen = f"{2.5 + (cout_par_inter / 100):.1f}h"
            self.table.setItem(row, 4, QTableWidgetItem(temps_moyen))
            
            # Efficacité (basée sur le coût par intervention)
            if cout_par_inter > 0:
                # Calcul d'efficacité simple (à ajuster selon les besoins métier)
                efficacite = max(0, 100 - (cout_par_inter / 10))  # Exemple de calcul
                self.table.setItem(row, 5, QTableWidgetItem(f"{efficacite:.1f}%"))
            else:
                self.table.setItem(row, 5, QTableWidgetItem("N/A"))
            
            # Spécialité (simulée)
            specialites = ["Mécanique", "Électrique", "Hydraulique", "Automatisme", "Généraliste"]
            specialite = specialites[row % len(specialites)]
            self.table.setItem(row, 6, QTableWidgetItem(specialite))
            
            # Site principal (simulé)
            site = item.get('site_principal', f"Site {row % 3 + 1}")
            self.table.setItem(row, 7, QTableWidgetItem(site))
            
    def update_skills_analysis(self):
        """Met à jour l'analyse des compétences."""
        if not self.current_data:
            self.skills_text.setPlainText("Aucune donnée disponible pour l'analyse des compétences.")
            return
            
        # Analyse simple des compétences basée sur les données
        total_teams = len(self.current_data)
        active_teams = len([t for t in self.current_data if t.get('cout_total', 0) > 0])
        
        if active_teams == 0:
            self.skills_text.setPlainText("Aucune équipe avec activité détectée.")
            return
            
        # Équipe la plus polyvalente (plus d'interventions variées)
        most_versatile = max(self.current_data, key=lambda x: x.get('nb_interventions', 0))
        
        # Équipe la plus efficace
        efficient_teams = [t for t in self.current_data 
                          if t.get('nb_interventions', 0) > 0 and t.get('cout_total', 0) > 0]
        
        most_efficient = None
        if efficient_teams:
            most_efficient = min(efficient_teams, 
                                key=lambda x: x.get('cout_total', 0) / x.get('nb_interventions', 1))
        
        # Générer l'analyse
        analysis = f"""🎓 ANALYSE DES COMPÉTENCES D'ÉQUIPE

📊 Vue d'ensemble:
• {total_teams} équipes au total, {active_teams} actives
• Charge moyenne: {sum(t.get('nb_interventions', 0) for t in self.current_data) / active_teams:.1f} interventions/équipe

👥 Équipe la plus polyvalente:
• {most_versatile.get('nom_equipe', 'Inconnue')}: {most_versatile.get('nb_interventions', 0)} interventions

⚡ Équipe la plus efficace:"""

        if most_efficient:
            cout_inter = most_efficient.get('cout_total', 0) / most_efficient.get('nb_interventions', 1)
            analysis += f"""
• {most_efficient.get('nom_equipe', 'Inconnue')}: {cout_inter:.0f} €/intervention"""
        else:
            analysis += "\n• Données insuffisantes"
            
        analysis += f"""

🔧 Recommandations:
• Partager les bonnes pratiques de l'équipe efficace
• Former les équipes moins performantes
• Équilibrer la charge de travail
• Développer la polyvalence des équipes spécialisées"""

        self.skills_text.setPlainText(analysis)
        
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
        equipe_id = self.equipe_combo.currentData()
        
        self.load_data(debut, fin, equipe_id)
        
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
            
    def analyze_skills(self):
        """Lance une analyse approfondie des compétences."""
        try:
            # TODO: Implémenter l'analyse des compétences approfondie
            QMessageBox.information(self, "Info", "Analyse des compétences - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des compétences: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'analyse: {str(e)}")
            
    def generate_team_report(self):
        """Génère un rapport d'équipe."""
        try:
            # TODO: Implémenter la génération de rapport d'équipe
            QMessageBox.information(self, "Info", "Rapport d'équipe - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")


if __name__ == "__main__":
    """Test standalone du widget."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = EquipeKPIWidget()
    widget.show()
    widget.resize(1400, 900)
    
    # Simuler des données de test
    test_data = [
        {
            'nom_equipe': 'Équipe Mécanique A',
            'cout_total': 8500.50,
            'nb_interventions': 25,
            'site_principal': 'Site Production'
        },
        {
            'nom_equipe': 'Équipe Électrique',
            'cout_total': 6200.75,
            'nb_interventions': 18,
            'site_principal': 'Site Logistique'
        },
        {
            'nom_equipe': 'Équipe Polyvalente',
            'cout_total': 12000.25,
            'nb_interventions': 45,
            'site_principal': 'Tous sites'
        },
        {
            'nom_equipe': 'Équipe Hydraulique',
            'cout_total': 4800.00,
            'nb_interventions': 15,
            'site_principal': 'Site Production'
        }
    ]
    
    widget.current_data = test_data
    widget.update_display()
    
    sys.exit(app.exec())
