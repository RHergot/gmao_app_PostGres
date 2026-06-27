#!/usr/bin/env python3
"""
Widget de résumé global et de vue d'ensemble des KPI financiers.
Affiche les métriques principales et les tendances générales.
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
    QPieSeries, QLineSeries, QDateTimeAxis, QAreaSeries
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

class GlobalSummaryWidget(QWidget):
    """
    Widget de résumé global des KPI financiers.
    
    Fonctionnalités:
    - Vue d'ensemble des coûts totaux
    - Répartition par centre de frais
    - Tendances sur plusieurs périodes
    - Alertes et indicateurs de performance
    - Résumé exécutif
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
        title_label = QLabel("📊 Vue d'Ensemble - KPI Financiers GMAO")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Indicateur de mise à jour
        self.last_update_label = QLabel("Dernière MàJ: --")
        self.last_update_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.last_update_label)
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        return header
        
    def create_controls(self) -> QWidget:
        """Crée la zone de contrôles et filtres."""
        controls = QGroupBox("Paramètres de Vue")
        layout = QGridLayout(controls)
        
        # Période de début
        layout.addWidget(QLabel("Du:"), 0, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-3))
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
        
        # Vue rapide prédéfinie
        layout.addWidget(QLabel("Vue rapide:"), 0, 4)
        self.quick_view_combo = QComboBox()
        self.quick_view_combo.addItems([
            "Personnalisé", "Cette semaine", "Ce mois", 
            "Ce trimestre", "Cette année", "12 derniers mois"
        ])
        self.quick_view_combo.currentTextChanged.connect(self.on_quick_view_changed)
        layout.addWidget(self.quick_view_combo, 0, 5)
        
        # Type de comparaison
        layout.addWidget(QLabel("Comparaison:"), 1, 0)
        self.comparison_combo = QComboBox()
        self.comparison_combo.addItems([
            "Période précédente", "Année précédente", "Moyenne mobile", "Budget"
        ])
        self.comparison_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.comparison_combo, 1, 1)
        
        # Niveau de détail
        layout.addWidget(QLabel("Détail:"), 1, 2)
        self.detail_combo = QComboBox()
        self.detail_combo.addItems(["Résumé", "Détaillé", "Expert"])
        self.detail_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.detail_combo, 1, 3)
        
        # Alertes activées
        self.enable_alerts = QCheckBox("Alertes automatiques")
        self.enable_alerts.setChecked(True)
        self.enable_alerts.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.enable_alerts, 1, 4, 1, 2)
        
        layout.setColumnStretch(6, 1)
        return controls
        
    def create_main_content(self) -> QWidget:
        """Crée la zone principale avec métriques et graphiques."""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Métriques de synthèse principales
        main_metrics = self.create_main_metrics()
        layout.addWidget(main_metrics)
        
        # Conteneur horizontal pour graphiques et détails
        content_layout = QHBoxLayout()
        
        # Zone gauche: Graphiques de synthèse
        charts_widget = self.create_charts_section()
        content_layout.addWidget(charts_widget, 2)
        
        # Zone droite: Alertes et recommandations
        insights_widget = self.create_insights_section()
        content_layout.addWidget(insights_widget, 1)
        
        layout.addLayout(content_layout)
        
        # Zone bottom: Répartition par centre de frais
        breakdown_widget = self.create_breakdown_section()
        layout.addWidget(breakdown_widget)
        
        return main_widget
        
    def create_main_metrics(self) -> QWidget:
        """Crée la zone des métriques principales."""
        metrics = QFrame()
        metrics.setFrameStyle(QFrame.StyledPanel)
        metrics.setFixedHeight(140)
        
        layout = QHBoxLayout(metrics)
        
        # Métriques principales
        self.total_cost_label = self.create_main_metric_card("Coût Total", "0 €", "💰", "#2196F3")
        self.monthly_avg_label = self.create_main_metric_card("Moyenne Mensuelle", "0 €", "📊", "#4CAF50")
        self.trend_label = self.create_main_metric_card("Tendance", "+0%", "📈", "#FF9800")
        self.efficiency_label = self.create_main_metric_card("Efficacité", "0%", "⚡", "#9C27B0")
        
        layout.addWidget(self.total_cost_label)
        layout.addWidget(self.monthly_avg_label)
        layout.addWidget(self.trend_label)
        layout.addWidget(self.efficiency_label)
        
        return metrics
        
    def create_main_metric_card(self, title: str, value: str, icon: str, color: str) -> QWidget:
        """Crée une carte de métrique principale avec couleur."""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setLineWidth(2)
        card.setStyleSheet(f"QFrame {{ border-color: {color}; background-color: white; }}")
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icône
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Valeur
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        # Titre
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Stocker le label de valeur pour la mise à jour
        setattr(card, 'value_label', value_label)
        
        return card
        
    def create_charts_section(self) -> QWidget:
        """Crée la section des graphiques de synthèse."""
        charts_widget = QWidget()
        layout = QVBoxLayout(charts_widget)
        
        # Graphique en aires - Évolution temporelle
        area_group = QGroupBox("Évolution des Coûts de Maintenance")
        area_layout = QVBoxLayout(area_group)
        
        self.area_chart = QChart()
        self.area_chart.setTitle("Tendance sur la Période")
        self.area_chart_view = QChartView(self.area_chart)
        self.area_chart_view.setRenderHint(QPainter.Antialiasing)
        self.area_chart_view.setMinimumHeight(200)
        
        area_layout.addWidget(self.area_chart_view)
        layout.addWidget(area_group)
        
        # Graphique en secteurs - Répartition par centre de frais
        pie_group = QGroupBox("Répartition par Centre de Frais")
        pie_layout = QVBoxLayout(pie_group)
        
        self.pie_chart = QChart()
        self.pie_chart.setTitle("Répartition des Coûts")
        self.pie_chart_view = QChartView(self.pie_chart)
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        self.pie_chart_view.setMinimumHeight(200)
        
        pie_layout.addWidget(self.pie_chart_view)
        layout.addWidget(pie_group)
        
        return charts_widget
        
    def create_insights_section(self) -> QWidget:
        """Crée la section des insights et alertes."""
        insights_widget = QWidget()
        layout = QVBoxLayout(insights_widget)
        
        # Alertes et indicateurs
        alerts_group = QGroupBox("🚨 Alertes et Indicateurs")
        alerts_layout = QVBoxLayout(alerts_group)
        
        self.alerts_text = QTextEdit()
        self.alerts_text.setMaximumHeight(120)
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setPlainText("Chargement des alertes...")
        
        alerts_layout.addWidget(self.alerts_text)
        layout.addWidget(alerts_group)
        
        # Recommandations rapides
        recommendations_group = QGroupBox("💡 Recommandations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(120)
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setPlainText("Chargement des recommandations...")
        
        recommendations_layout.addWidget(self.recommendations_text)
        layout.addWidget(recommendations_group)
        
        # Résumé exécutif
        executive_group = QGroupBox("📋 Résumé Exécutif")
        executive_layout = QVBoxLayout(executive_group)
        
        self.executive_text = QTextEdit()
        self.executive_text.setMaximumHeight(100)
        self.executive_text.setReadOnly(True)
        self.executive_text.setPlainText("Génération du résumé...")
        
        executive_layout.addWidget(self.executive_text)
        layout.addWidget(executive_group)
        
        return insights_widget
        
    def create_breakdown_section(self) -> QWidget:
        """Crée la section de répartition par centre de frais."""
        breakdown_group = QGroupBox("Répartition Détaillée par Centre de Frais")
        layout = QVBoxLayout(breakdown_group)
        
        # Tableau de répartition
        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(6)
        self.breakdown_table.setHorizontalHeaderLabels([
            "Centre de Frais", "Coût Total €", "% du Total", "Évolution", 
            "Nb Interventions", "Coût/Intervention €"
        ])
        
        # Configuration du tableau
        header = self.breakdown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.breakdown_table.setAlternatingRowColors(True)
        self.breakdown_table.setMaximumHeight(150)
        
        layout.addWidget(self.breakdown_table)
        return breakdown_group
        
    def create_actions(self) -> QWidget:
        """Crée la zone des boutons d'actions."""
        actions = QFrame()
        layout = QHBoxLayout(actions)
        
        # Bouton export Excel complet
        export_btn = QPushButton("📊 Export Excel Complet")
        export_btn.clicked.connect(self.export_complete_excel)
        layout.addWidget(export_btn)
        
        # Bouton génération rapport
        report_btn = QPushButton("📄 Rapport Exécutif")
        report_btn.clicked.connect(self.generate_executive_report)
        layout.addWidget(report_btn)
        
        layout.addStretch()
        
        # Bouton configuration alertes
        config_btn = QPushButton("⚙️ Config Alertes")
        config_btn.clicked.connect(self.configure_alerts)
        layout.addWidget(config_btn)
        
        return actions
        
    def load_data(self, periode_debut: date, periode_fin: date):
        """Charge toutes les données pour la vue d'ensemble."""
        try:
            if KPIService is None:
                QMessageBox.warning(self, "Erreur", "Service KPI non disponible")
                return
                
            if self.kpi_service is None:
                self.kpi_service = KPIService()
            
            # Charger les données de tous les centres de frais
            data = {}
            
            # Coûts par machine
            data['machines'] = self.kpi_service.get_couts_par_machine(
                periode_debut=periode_debut,
                periode_fin=periode_fin,
                machine_ids=None,
                type_machine=None
            )
            
            # Coûts par site
            data['sites'] = self.kpi_service.get_couts_par_site(
                periode_debut=periode_debut,
                periode_fin=periode_fin
            )
            
            # Coûts par équipe
            data['equipes'] = self.kpi_service.get_couts_par_equipe(
                periode_debut=periode_debut,
                periode_fin=periode_fin
            )
            
            # Préventif vs curatif
            data['preventif_curatif'] = self.kpi_service.get_preventif_vs_curatif(
                periode_debut=periode_debut,
                periode_fin=periode_fin
            )
            
            self.current_data = data
            self.update_display()
            
            # Mettre à jour l'indicateur de dernière mise à jour
            self.last_update_label.setText(f"Dernière MàJ: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données globales: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement: {str(e)}")
            
    def update_display(self):
        """Met à jour l'affichage avec les données actuelles."""
        if not self.current_data:
            return
            
        # Mettre à jour les métriques principales
        self.update_main_metrics()
        
        # Mettre à jour les graphiques
        self.update_area_chart()
        self.update_pie_chart()
        
        # Mettre à jour le tableau de répartition
        self.update_breakdown_table()
        
        # Mettre à jour les insights
        self.update_alerts()
        self.update_recommendations()
        self.update_executive_summary()
        
    def update_main_metrics(self):
        """Met à jour les métriques principales."""
        data = self.current_data
        
        # Calculer le coût total de tous les centres
        total_cost = 0
        
        # Sommer les coûts de toutes les sources
        if 'machines' in data:
            total_cost += sum(item.get('cout_total', 0) for item in data['machines'])
        
        # Calculer la moyenne mensuelle (approximation)
        debut = self.date_debut.date().toPython()
        fin = self.date_fin.date().toPython()
        nb_mois = max(1, (fin.year - debut.year) * 12 + fin.month - debut.month)
        monthly_avg = total_cost / nb_mois
        
        # Tendance (simulée pour l'exemple)
        trend = "+12.5%"  # TODO: Calculer la vraie tendance
        
        # Efficacité (basée sur le ratio préventif/curatif)
        efficiency = 75  # TODO: Calculer la vraie efficacité
        if 'preventif_curatif' in data:
            pc_data = data['preventif_curatif']
            preventif = pc_data.get('cout_preventif', 0)
            curatif = pc_data.get('cout_curatif', 0)
            if preventif + curatif > 0:
                ratio_preventif = preventif / (preventif + curatif)
                efficiency = min(100, ratio_preventif * 200)  # Efficacité basée sur le préventif
        
        # Mettre à jour les labels
        self.total_cost_label.value_label.setText(f"{total_cost:,.0f} €")
        self.monthly_avg_label.value_label.setText(f"{monthly_avg:,.0f} €")
        self.trend_label.value_label.setText(trend)
        self.efficiency_label.value_label.setText(f"{efficiency:.0f}%")
        
    def update_area_chart(self):
        """Met à jour le graphique en aires d'évolution."""
        self.area_chart.removeAllSeries()
        
        # Simuler des données d'évolution mensuelle
        # TODO: Implémenter les vraies données temporelles
        series = QLineSeries()
        series.setName("Coûts Mensuels")
        
        # Données simulées sur 6 mois
        total_cost = sum(item.get('cout_total', 0) for item in self.current_data.get('machines', []))
        base_monthly = total_cost / 6
        
        for i in range(6):
            # Variation simulée
            variation = base_monthly * (0.8 + 0.4 * ((i + 2) % 3) / 2)
            series.append(i, variation)
        
        self.area_chart.addSeries(series)
        
        # Configurer les axes
        axis_x = QValueAxis()
        axis_x.setTitleText("Mois")
        axis_x.setRange(0, 5)
        self.area_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Coût (€)")
        self.area_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
    def update_pie_chart(self):
        """Met à jour le graphique en secteurs de répartition."""
        self.pie_chart.removeAllSeries()
        
        data = self.current_data
        
        # Calculer les coûts par centre de frais
        centres_couts = {}
        
        if 'machines' in data:
            for machine in data['machines']:
                site = machine.get('nom_site', 'Site Inconnu')
                cout = machine.get('cout_total', 0)
                centres_couts[f"Site: {site}"] = centres_couts.get(f"Site: {site}", 0) + cout
        
        if not centres_couts:
            return
            
        # Créer la série pie
        series = QPieSeries()
        
        # Limiter aux 5 premiers centres pour la lisibilité
        sorted_centres = sorted(centres_couts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for centre, cout in sorted_centres:
            if cout > 0:
                slice_pie = series.append(f"{centre}\n{cout:,.0f} €", cout)
                slice_pie.setLabelVisible(True)
        
        self.pie_chart.addSeries(series)
        
    def update_breakdown_table(self):
        """Met à jour le tableau de répartition."""
        data = self.current_data
        
        # Préparer les données de répartition
        breakdown_data = []
        
        # Machines par site
        if 'sites' in data:
            for site in data['sites']:
                breakdown_data.append({
                    'centre': f"Site: {site.get('nom_site', 'Inconnu')}",
                    'cout_total': site.get('cout_total', 0),
                    'nb_interventions': site.get('nb_interventions', 0)
                })
        
        # Calculer le total pour les pourcentages
        total_global = sum(item['cout_total'] for item in breakdown_data)
        
        self.breakdown_table.setRowCount(len(breakdown_data))
        
        for row, item in enumerate(breakdown_data):
            # Centre de frais
            self.breakdown_table.setItem(row, 0, QTableWidgetItem(item['centre']))
            
            # Coût total
            cout = item['cout_total']
            self.breakdown_table.setItem(row, 1, QTableWidgetItem(f"{cout:,.2f}"))
            
            # Pourcentage
            pourcent = (cout / total_global * 100) if total_global > 0 else 0
            self.breakdown_table.setItem(row, 2, QTableWidgetItem(f"{pourcent:.1f}%"))
            
            # Évolution (simulée)
            evolution = f"+{5 + (row % 3) * 3}%"
            self.breakdown_table.setItem(row, 3, QTableWidgetItem(evolution))
            
            # Nb interventions
            nb_inter = item['nb_interventions']
            self.breakdown_table.setItem(row, 4, QTableWidgetItem(str(nb_inter)))
            
            # Coût par intervention
            cout_par_inter = cout / nb_inter if nb_inter > 0 else 0
            self.breakdown_table.setItem(row, 5, QTableWidgetItem(f"{cout_par_inter:,.2f}"))
            
    def update_alerts(self):
        """Met à jour les alertes."""
        alerts = []
        
        data = self.current_data
        
        # Analyser les données pour générer des alertes
        if 'machines' in data and data['machines']:
            # Machine la plus coûteuse
            machine_max = max(data['machines'], key=lambda x: x.get('cout_total', 0))
            if machine_max.get('cout_total', 0) > 5000:
                alerts.append(f"⚠️ Machine '{machine_max.get('nom_machine', 'Inconnue')}' "
                             f"coûte {machine_max.get('cout_total', 0):,.0f} € (>5000€)")
        
        # Ratio préventif/curatif
        if 'preventif_curatif' in data:
            pc_data = data['preventif_curatif']
            preventif = pc_data.get('cout_preventif', 0)
            curatif = pc_data.get('cout_curatif', 0)
            total = preventif + curatif
            if total > 0:
                ratio = preventif / total * 100
                if ratio < 30:
                    alerts.append(f"🚨 Ratio préventif/curatif trop bas: {ratio:.1f}% (recommandé >40%)")
                elif ratio > 80:
                    alerts.append(f"⚠️ Ratio préventif/curatif élevé: {ratio:.1f}% (possible sur-maintenance)")
        
        # Budget dépassé (simulation)
        total_cost = sum(item.get('cout_total', 0) for item in data.get('machines', []))
        if total_cost > 50000:
            alerts.append(f"💰 Coût total élevé: {total_cost:,.0f} € (>50k€)")
        
        # Afficher les alertes
        if alerts:
            alert_text = "\n".join(alerts)
        else:
            alert_text = "✅ Aucune alerte critique détectée"
            
        self.alerts_text.setPlainText(alert_text)
        
    def update_recommendations(self):
        """Met à jour les recommandations."""
        recommendations = []
        
        data = self.current_data
        
        # Analyser les données pour générer des recommandations
        total_cost = sum(item.get('cout_total', 0) for item in data.get('machines', []))
        
        if total_cost > 0:
            recommendations.append("🔍 Analyser les 3 machines les plus coûteuses")
            recommendations.append("📅 Optimiser la planification préventive")
            
            # Recommandations basées sur le ratio préventif/curatif
            if 'preventif_curatif' in data:
                pc_data = data['preventif_curatif']
                preventif = pc_data.get('cout_preventif', 0)
                curatif = pc_data.get('cout_curatif', 0)
                total_pc = preventif + curatif
                if total_pc > 0:
                    ratio = preventif / total_pc * 100
                    if ratio < 50:
                        recommendations.append("⬆️ Augmenter les interventions préventives")
                    else:
                        recommendations.append("✅ Maintenir l'équilibre préventif/curatif")
            
            recommendations.append("📊 Former les équipes aux bonnes pratiques")
            recommendations.append("🎯 Mettre en place des indicateurs de suivi")
        else:
            recommendations.append("📊 Aucune donnée suffisante pour recommandations")
            
        rec_text = "\n".join(recommendations)
        self.recommendations_text.setPlainText(rec_text)
        
    def update_executive_summary(self):
        """Met à jour le résumé exécutif."""
        data = self.current_data
        
        total_cost = sum(item.get('cout_total', 0) for item in data.get('machines', []))
        nb_machines = len(data.get('machines', []))
        
        if total_cost > 0:
            summary = f"""💼 RÉSUMÉ EXÉCUTIF
            
Coût total: {total_cost:,.0f} € sur {nb_machines} machines
Performance: {"Satisfaisante" if total_cost < 50000 else "Attention requise"}
Tendance: Stable avec optimisations possibles"""
        else:
            summary = "💼 RÉSUMÉ EXÉCUTIF\n\nAucune donnée disponible pour la période sélectionnée."
            
        self.executive_text.setPlainText(summary)
        
    def on_filter_changed(self):
        """Gestionnaire de changement de filtre."""
        if hasattr(self, '_reload_timer'):
            self._reload_timer.stop()
        
        self._reload_timer = QTimer()
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self.refresh_data)
        self._reload_timer.start(1000)  # Délai de 1s pour vue globale
        
    def on_quick_view_changed(self, view_text: str):
        """Gestionnaire de changement de vue rapide."""
        if view_text == "Personnalisé":
            return
            
        today = QDate.currentDate()
        
        if view_text == "Cette semaine":
            start = today.addDays(-today.dayOfWeek() + 1)
            self.date_debut.setDate(start)
            self.date_fin.setDate(today)
        elif view_text == "Ce mois":
            start = QDate(today.year(), today.month(), 1)
            self.date_debut.setDate(start)
            self.date_fin.setDate(today)
        elif view_text == "Ce trimestre":
            start_month = ((today.month() - 1) // 3) * 3 + 1
            start = QDate(today.year(), start_month, 1)
            self.date_debut.setDate(start)
            self.date_fin.setDate(today)
        elif view_text == "Cette année":
            start = QDate(today.year(), 1, 1)
            self.date_debut.setDate(start)
            self.date_fin.setDate(today)
        elif view_text == "12 derniers mois":
            start = today.addMonths(-12)
            self.date_debut.setDate(start)
            self.date_fin.setDate(today)
            
    def refresh_data(self):
        """Actualise les données."""
        debut = self.date_debut.date().toPython()
        fin = self.date_fin.date().toPython()
        
        self.load_data(debut, fin)
        
    def export_complete_excel(self):
        """Exporte un rapport Excel complet."""
        try:
            QMessageBox.information(self, "Info", "Export Excel complet - À implémenter")
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
            
    def generate_executive_report(self):
        """Génère un rapport exécutif."""
        try:
            QMessageBox.information(self, "Info", "Rapport exécutif - À implémenter")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")
            
    def configure_alerts(self):
        """Configure les alertes."""
        try:
            QMessageBox.information(self, "Info", "Configuration des alertes - À implémenter")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la configuration: {str(e)}")


if __name__ == "__main__":
    """Test standalone du widget."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = GlobalSummaryWidget()
    widget.show()
    widget.resize(1600, 1000)
    
    # Simuler des données de test
    test_data = {
        'machines': [
            {'nom_machine': 'Machine A', 'nom_site': 'Site 1', 'cout_total': 5000},
            {'nom_machine': 'Machine B', 'nom_site': 'Site 1', 'cout_total': 3500},
            {'nom_machine': 'Machine C', 'nom_site': 'Site 2', 'cout_total': 7200}
        ],
        'sites': [
            {'nom_site': 'Site 1', 'cout_total': 8500, 'nb_interventions': 25},
            {'nom_site': 'Site 2', 'cout_total': 7200, 'nb_interventions': 18}
        ],
        'preventif_curatif': {
            'cout_preventif': 6000,
            'cout_curatif': 9700
        }
    }
    
    widget.current_data = test_data
    widget.update_display()
    
    sys.exit(app.exec())
