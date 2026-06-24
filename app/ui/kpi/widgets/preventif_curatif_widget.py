#!/usr/bin/env python3
"""
Widget spécialisé pour l'analyse préventif vs curatif.
Affiche les KPI financiers et de performance entre maintenance préventive et curative.
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
from PySide6.QtGui import QFont, QPalette, QIcon, QPixmap, QPainter, QColor
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, 
    QPieSeries, QLineSeries, QDateTimeAxis, QStackedBarSeries
)

# Ajouter le chemin pour les imports de l'app
current_dir = os.path.dirname(os.path.abspath(__file__))
app_root = os.path.join(current_dir, '..', '..', '..')
project_root = os.path.join(current_dir, '..', '..', '..', '..')
sys.path.insert(0, app_root)
sys.path.insert(0, project_root)

try:
    from core.services.kpi_service import KPIService
    setup_logging = None
except ImportError as e:
    print(f"Erreur d'import KPIService: {e}")
    try:
        from app.core.services.kpi_service import KPIService
        setup_logging = None
    except ImportError as e2:
        print(f"Erreur d'import KPIService (fallback): {e2}")
        KPIService = None
        setup_logging = None

import logging
logger = logging.getLogger(__name__)

class PreventifCuratifWidget(QWidget):
    """
    Widget d'analyse de la maintenance préventive vs curative.
    
    Fonctionnalités:
    - Comparaison des coûts préventif/curatif
    - Ratios et tendances
    - Efficacité de la stratégie préventive
    - ROI de la maintenance préventive
    - Prédictions et recommandations
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
        title_label = QLabel("🔧 Analyse Préventif vs Curatif")
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
        self.date_debut.setDate(QDate.currentDate().addMonths(-6))
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
        
        # Type d'analyse
        layout.addWidget(QLabel("Analyse:"), 1, 0)
        self.analyse_combo = QComboBox()
        self.analyse_combo.addItems([
            "Vue d'ensemble",
            "Par machine",
            "Par équipe",
            "Évolution temporelle",
            "ROI Préventif"
        ])
        self.analyse_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.analyse_combo, 1, 1)
        
        # Groupement temporel
        layout.addWidget(QLabel("Période:"), 1, 2)
        self.periode_combo = QComboBox()
        self.periode_combo.addItems(["Mensuel", "Trimestriel", "Annuel"])
        self.periode_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.periode_combo, 1, 3)
        
        # Options d'affichage
        self.show_trends = QCheckBox("Afficher tendances")
        self.show_trends.setChecked(True)
        self.show_trends.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.show_trends, 1, 4, 1, 2)
        
        layout.setColumnStretch(6, 1)
        return controls
        
    def create_main_content(self) -> QWidget:
        """Crée la zone principale avec métriques et graphiques."""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Métriques de synthèse
        metrics = self.create_metrics_summary()
        layout.addWidget(metrics)
        
        # Conteneur horizontal pour graphiques et analyse
        content_layout = QHBoxLayout()
        
        # Zone gauche: Graphiques
        charts_widget = self.create_charts_section()
        content_layout.addWidget(charts_widget, 2)
        
        # Zone droite: Analyse et recommandations
        analysis_widget = self.create_analysis_section()
        content_layout.addWidget(analysis_widget, 1)
        
        layout.addLayout(content_layout)
        return main_widget
        
    def create_metrics_summary(self) -> QWidget:
        """Crée la zone des métriques de synthèse."""
        metrics = QFrame()
        metrics.setFrameStyle(QFrame.StyledPanel)
        metrics.setFixedHeight(120)
        
        layout = QHBoxLayout(metrics)
        
        # Métriques individuelles
        self.preventif_cost_label = self.create_metric_card("Coût Préventif", "0 €", "🛠️")
        self.curatif_cost_label = self.create_metric_card("Coût Curatif", "0 €", "🚨")
        self.ratio_label = self.create_metric_card("Ratio P/C", "0%", "📊")
        self.roi_label = self.create_metric_card("ROI Préventif", "0%", "💹")
        
        layout.addWidget(self.preventif_cost_label)
        layout.addWidget(self.curatif_cost_label)
        layout.addWidget(self.ratio_label)
        layout.addWidget(self.roi_label)
        
        return metrics
        
    def create_metric_card(self, title: str, value: str, icon: str) -> QWidget:
        """Crée une carte de métrique avec couleur selon le type."""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setLineWidth(1)
        
        # Couleur selon le type
        if "Préventif" in title:
            card.setStyleSheet("QFrame { background-color: #e8f5e8; }")
        elif "Curatif" in title:
            card.setStyleSheet("QFrame { background-color: #ffe8e8; }")
        elif "ROI" in title:
            card.setStyleSheet("QFrame { background-color: #e8f4ff; }")
        
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
        
        # Graphique en secteurs - Répartition préventif/curatif
        pie_group = QGroupBox("Répartition des Coûts")
        pie_layout = QVBoxLayout(pie_group)
        
        self.pie_chart = QChart()
        self.pie_chart.setTitle("Préventif vs Curatif")
        self.pie_chart_view = QChartView(self.pie_chart)
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        self.pie_chart_view.setMinimumHeight(250)
        
        pie_layout.addWidget(self.pie_chart_view)
        layout.addWidget(pie_group)
        
        # Graphique empilé - Évolution par période
        stacked_group = QGroupBox("Évolution Temporelle")
        stacked_layout = QVBoxLayout(stacked_group)
        
        self.stacked_chart = QChart()
        self.stacked_chart.setTitle("Évolution Préventif/Curatif")
        self.stacked_chart_view = QChartView(self.stacked_chart)
        self.stacked_chart_view.setRenderHint(QPainter.Antialiasing)
        self.stacked_chart_view.setMinimumHeight(250)
        
        stacked_layout.addWidget(self.stacked_chart_view)
        layout.addWidget(stacked_group)
        
        return charts_widget
        
    def create_analysis_section(self) -> QWidget:
        """Crée la section d'analyse et recommandations."""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        
        # Tableau de comparaison
        table_group = QGroupBox("Comparaison Détaillée")
        table_layout = QVBoxLayout(table_group)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Type", "Coût Total €", "Nb Interventions", "Coût Moyen €", 
            "Temps Moyen", "Efficacité %"
        ])
        
        # Configuration du tableau
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setFixedHeight(120)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)
        
        # Analyse ROI
        roi_group = QGroupBox("Analyse ROI")
        roi_layout = QVBoxLayout(roi_group)
        
        self.roi_text = QTextEdit()
        self.roi_text.setMaximumHeight(120)
        self.roi_text.setReadOnly(True)
        self.roi_text.setPlainText("Chargez les données pour voir l'analyse ROI...")
        
        roi_layout.addWidget(self.roi_text)
        layout.addWidget(roi_group)
        
        # Recommandations
        recommendations_group = QGroupBox("Recommandations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(150)
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setPlainText("Chargez les données pour voir les recommandations...")
        
        recommendations_layout.addWidget(self.recommendations_text)
        layout.addWidget(recommendations_group)
        
        return analysis_widget
        
    def create_actions(self) -> QWidget:
        """Crée la zone des boutons d'actions."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        
        # Bouton export Excel
        export_btn = QPushButton("📊 Exporter Excel")
        export_btn.clicked.connect(self.export_to_excel)
        layout.addWidget(export_btn)
        
        # Bouton optimisation
        optimize_btn = QPushButton("⚡ Optimiser Stratégie")
        optimize_btn.clicked.connect(self.optimize_strategy)
        layout.addWidget(optimize_btn)
        
        layout.addStretch()
        
        # Bouton rapport stratégique
        report_btn = QPushButton("📋 Rapport Stratégique")
        report_btn.clicked.connect(self.generate_strategic_report)
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
            
            # Charger les données préventif/curatif
            data = self.kpi_service.get_preventif_vs_curatif(
                periode_debut=periode_debut,
                periode_fin=periode_fin,
                site_id=site_id
            )
            
            self.current_data = data
            self.update_display()
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données préventif/curatif: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
            
    def update_display(self):
        """Met à jour l'affichage avec les données actuelles."""
        if not self.current_data:
            return
            
        # Mettre à jour les métriques
        self.update_metrics()
        
        # Mettre à jour les graphiques
        self.update_pie_chart()
        self.update_stacked_chart()
        
        # Mettre à jour le tableau
        self.update_table()
        
        # Mettre à jour les analyses
        self.update_roi_analysis()
        self.update_recommendations()
        
    def update_metrics(self):
        """Met à jour les métriques de synthèse."""
        data = self.current_data
        
        if not data:
            return
            
        # Calculer les coûts par type
        preventif_cost = data.get('cout_preventif', 0)
        curatif_cost = data.get('cout_curatif', 0)
        total_cost = preventif_cost + curatif_cost
        
        # Ratio préventif/curatif
        ratio_pc = (preventif_cost / total_cost * 100) if total_cost > 0 else 0
        
        # ROI du préventif (estimation basée sur les coûts évités)
        # Hypothèse: chaque euro de préventif évite 3 euros de curatif
        cout_evite_estime = preventif_cost * 3
        roi = ((cout_evite_estime - curatif_cost) / preventif_cost * 100) if preventif_cost > 0 else 0
        
        # Mettre à jour les labels
        self.preventif_cost_label.value_label.setText(f"{preventif_cost:,.0f} €")
        self.curatif_cost_label.value_label.setText(f"{curatif_cost:,.0f} €")
        self.ratio_label.value_label.setText(f"{ratio_pc:.1f}%")
        self.roi_label.value_label.setText(f"{roi:.1f}%")
        
    def update_pie_chart(self):
        """Met à jour le graphique en secteurs."""
        self.pie_chart.removeAllSeries()
        
        data = self.current_data
        if not data:
            return
            
        preventif_cost = data.get('cout_preventif', 0)
        curatif_cost = data.get('cout_curatif', 0)
        
        if preventif_cost == 0 and curatif_cost == 0:
            return
            
        # Créer la série pie
        series = QPieSeries()
        
        # Slice préventif (vert)
        if preventif_cost > 0:
            slice_preventif = series.append(f"Préventif\n{preventif_cost:,.0f} €", preventif_cost)
            slice_preventif.setLabelVisible(True)
            slice_preventif.setColor(QColor(76, 175, 80))  # Vert
            
        # Slice curatif (rouge)
        if curatif_cost > 0:
            slice_curatif = series.append(f"Curatif\n{curatif_cost:,.0f} €", curatif_cost)
            slice_curatif.setLabelVisible(True)
            slice_curatif.setColor(QColor(244, 67, 54))  # Rouge
        
        # Ajouter la série au graphique
        self.pie_chart.addSeries(series)
        
    def update_stacked_chart(self):
        """Met à jour le graphique empilé d'évolution."""
        self.stacked_chart.removeAllSeries()
        
        # Pour l'instant, simuler des données d'évolution
        # TODO: Implémenter l'évolution temporelle réelle
        
        # Créer des données simulées par mois
        preventif_set = QBarSet("Préventif")
        curatif_set = QBarSet("Curatif")
        categories = []
        
        # Simuler 6 mois de données
        data = self.current_data
        base_preventif = data.get('cout_preventif', 0) / 6
        base_curatif = data.get('cout_curatif', 0) / 6
        
        for i in range(6):
            # Variation légère pour simulation
            var_preventif = base_preventif * (0.8 + 0.4 * (i % 3) / 2)
            var_curatif = base_curatif * (1.2 - 0.4 * (i % 2))
            
            preventif_set.append(var_preventif)
            curatif_set.append(var_curatif)
            
            # Nom du mois (simulation)
            mois = QDate.currentDate().addMonths(-5 + i).toString("MMM yyyy")
            categories.append(mois)
        
        # Couleurs
        preventif_set.setColor(QColor(76, 175, 80))  # Vert
        curatif_set.setColor(QColor(244, 67, 54))   # Rouge
        
        # Créer la série empilée
        series = QStackedBarSeries()
        series.append(preventif_set)
        series.append(curatif_set)
        
        # Ajouter la série au graphique
        self.stacked_chart.addSeries(series)
        
        # Configurer les axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-45)
        self.stacked_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Coût (€)")
        self.stacked_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
    def update_table(self):
        """Met à jour le tableau de comparaison."""
        data = self.current_data
        
        # Données préventif et curatif
        preventif_cost = data.get('cout_preventif', 0)
        curatif_cost = data.get('cout_curatif', 0)
        preventif_nb = data.get('nb_preventif', 0)
        curatif_nb = data.get('nb_curatif', 0)
        
        self.table.setRowCount(2)
        
        # Ligne préventif
        self.table.setItem(0, 0, QTableWidgetItem("🛠️ Préventif"))
        self.table.setItem(0, 1, QTableWidgetItem(f"{preventif_cost:,.2f}"))
        self.table.setItem(0, 2, QTableWidgetItem(str(preventif_nb)))
        
        cout_moyen_prev = preventif_cost / preventif_nb if preventif_nb > 0 else 0
        self.table.setItem(0, 3, QTableWidgetItem(f"{cout_moyen_prev:,.2f}"))
        self.table.setItem(0, 4, QTableWidgetItem("2.5h"))  # Simulé
        self.table.setItem(0, 5, QTableWidgetItem("85%"))   # Simulé
        
        # Ligne curatif
        self.table.setItem(1, 0, QTableWidgetItem("🚨 Curatif"))
        self.table.setItem(1, 1, QTableWidgetItem(f"{curatif_cost:,.2f}"))
        self.table.setItem(1, 2, QTableWidgetItem(str(curatif_nb)))
        
        cout_moyen_cur = curatif_cost / curatif_nb if curatif_nb > 0 else 0
        self.table.setItem(1, 3, QTableWidgetItem(f"{cout_moyen_cur:,.2f}"))
        self.table.setItem(1, 4, QTableWidgetItem("4.2h"))  # Simulé
        self.table.setItem(1, 5, QTableWidgetItem("65%"))   # Simulé
        
        # Colorer les lignes
        for col in range(6):
            item_prev = self.table.item(0, col)
            if item_prev:
                item_prev.setBackground(QColor(240, 248, 240))  # Vert très clair
                
            item_cur = self.table.item(1, col)
            if item_cur:
                item_cur.setBackground(QColor(248, 240, 240))   # Rouge très clair
                
    def update_roi_analysis(self):
        """Met à jour l'analyse ROI."""
        data = self.current_data
        
        if not data:
            self.roi_text.setPlainText("Aucune donnée disponible pour l'analyse ROI.")
            return
            
        preventif_cost = data.get('cout_preventif', 0)
        curatif_cost = data.get('cout_curatif', 0)
        total_cost = preventif_cost + curatif_cost
        
        if total_cost == 0:
            self.roi_text.setPlainText("Aucun coût de maintenance détecté.")
            return
            
        # Calculs ROI
        ratio_preventif = (preventif_cost / total_cost * 100) if total_cost > 0 else 0
        
        # Estimation des coûts évités (hypothèse métier)
        cout_evite_estime = preventif_cost * 2.5  # 1€ préventif évite 2.5€ curatif
        economie_realisee = max(0, cout_evite_estime - curatif_cost)
        roi_pourcent = (economie_realisee / preventif_cost * 100) if preventif_cost > 0 else 0
        
        # Analyse
        analysis = f"""💹 ANALYSE ROI DE LA MAINTENANCE PRÉVENTIVE

💰 Investissement préventif: {preventif_cost:,.0f} €
🚨 Coûts curatifs réels: {curatif_cost:,.0f} €
📊 Ratio préventif: {ratio_preventif:.1f}%

💡 Estimation des bénéfices:
• Coûts évités estimés: {cout_evite_estime:,.0f} €
• Économie réalisée: {economie_realisee:,.0f} €
• ROI: {roi_pourcent:.1f}%

📈 Interprétation:"""

        if roi_pourcent > 50:
            analysis += "\n✅ Excellent ROI - Stratégie préventive très rentable"
        elif roi_pourcent > 20:
            analysis += "\n✅ Bon ROI - Stratégie préventive rentable"
        elif roi_pourcent > 0:
            analysis += "\n⚠️ ROI modeste - Optimisation possible"
        else:
            analysis += "\n❌ ROI négatif - Revoir la stratégie préventive"

        self.roi_text.setPlainText(analysis)
        
    def update_recommendations(self):
        """Met à jour les recommandations."""
        data = self.current_data
        
        if not data:
            self.recommendations_text.setPlainText("Aucune donnée pour générer des recommandations.")
            return
            
        preventif_cost = data.get('cout_preventif', 0)
        curatif_cost = data.get('cout_curatif', 0)
        total_cost = preventif_cost + curatif_cost
        
        if total_cost == 0:
            self.recommendations_text.setPlainText("Aucun coût de maintenance - Pas de recommandations.")
            return
            
        ratio_preventif = (preventif_cost / total_cost * 100) if total_cost > 0 else 0
        
        # Générer des recommandations basées sur le ratio
        recommendations = "🎯 RECOMMANDATIONS STRATÉGIQUES\n\n"
        
        if ratio_preventif < 30:
            recommendations += """❗ CRITIQUE - Trop peu de préventif:
• Augmenter immédiatement le budget préventif
• Mettre en place un plan de maintenance préventive
• Former les équipes sur les pratiques préventives
• Analyser les pannes récurrentes pour prévention

💡 Objectif: Atteindre 40-60% de préventif"""
            
        elif ratio_preventif < 50:
            recommendations += """⚠️ AMÉLIORATION NÉCESSAIRE:
• Renforcer le programme préventif existant
• Identifier les machines critiques pour prévention
• Optimiser la fréquence des interventions préventives
• Analyser l'efficacité des actions préventives actuelles

💡 Objectif: Atteindre 50-70% de préventif"""
            
        elif ratio_preventif < 80:
            recommendations += """✅ BON ÉQUILIBRE:
• Maintenir le niveau actuel de préventif
• Optimiser les coûts des interventions préventives
• Surveiller l'évolution du ratio mensuel
• Continuer l'amélioration continue

💡 Objectif: Optimiser les coûts tout en maintenant l'efficacité"""
            
        else:
            recommendations += """⚠️ EXCÈS DE PRÉVENTIF:
• Revoir la fréquence des interventions préventives
• Analyser la nécessité de chaque action préventive
• Optimiser les coûts (peut-être sur-maintenance)
• Équilibrer avec curatif planifié

💡 Objectif: Trouver l'équilibre optimal coût/efficacité"""

        recommendations += f"\n\n📊 Actions prioritaires:"
        recommendations += f"\n• Analyse détaillée des {3} machines les plus coûteuses"
        recommendations += f"\n• Formation équipes sur maintenance prédictive"
        recommendations += f"\n• Mise en place d'indicateurs de suivi mensuel"

        self.recommendations_text.setPlainText(recommendations)
        
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
            
    def optimize_strategy(self):
        """Lance l'optimisation de la stratégie préventive."""
        try:
            # TODO: Implémenter l'optimisation de stratégie
            QMessageBox.information(self, "Info", "Optimisation de stratégie - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'optimisation: {str(e)}")
            
    def generate_strategic_report(self):
        """Génère un rapport stratégique."""
        try:
            # TODO: Implémenter la génération de rapport stratégique
            QMessageBox.information(self, "Info", "Rapport stratégique - À implémenter")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")


if __name__ == "__main__":
    """Test standalone du widget."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = PreventifCuratifWidget()
    widget.show()
    widget.resize(1400, 900)
    
    # Simuler des données de test
    test_data = {
        'cout_preventif': 8500.50,
        'cout_curatif': 15200.75,
        'nb_preventif': 25,
        'nb_curatif': 18
    }
    
    widget.current_data = test_data
    widget.update_display()
    
    sys.exit(app.exec())
