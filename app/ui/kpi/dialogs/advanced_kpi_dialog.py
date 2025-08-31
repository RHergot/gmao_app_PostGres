#!/usr/bin/env python3
"""
Dialog d'analyse KPI avancée.
Fonctionnalités d'analyse statistique et de prédiction.
"""

from .base_kpi_dialog import BaseKPIDialog, get_shared_text
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QTabWidget, QWidget, QLabel, QGridLayout, QCheckBox
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

try:
    from app.config import app_config, Language
    from app.ui.kpi.widgets.advanced_kpi_widget import AdvancedKPIWidget
except ImportError:
    AdvancedKPIWidget = None

# === TRADUCTIONS SPÉCIFIQUES ===
ADVANCED_TRANSLATIONS = {
    "FRENCH": {
        "title": "📊 Analyse KPI Avancée",
        "analysis_type": "Type d'Analyse",
        "statistical": "Statistique",
        "predictive": "Prédictive",
        "correlation": "Corrélation",
        "overview_tab": "📊 Vue d'Ensemble",
        "statistics_tab": "📈 Statistiques",
        "predictions_tab": "🔮 Prédictions",
        "correlations_tab": "🔗 Corrélations",
        "advanced_metrics": "Métriques Avancées",
        "trend_analysis": "Analyse de Tendances",
        "anomaly_detection": "Détection d'Anomalies",
        "cost_prediction": "Prédiction des Coûts",
        "failure_prediction": "Prédiction de Pannes",
        "efficiency_trends": "Tendances d'Efficacité",
        "show_anomalies": "Afficher les Anomalies",
        "show_trends": "Afficher les Tendances",
        "show_predictions": "Afficher les Prédictions",
        "loading_advanced": "Chargement des analyses avancées...",
        "export_success": "Analyses avancées exportées avec succès"
    }
}

def get_advanced_text(key: str) -> str:
    return ADVANCED_TRANSLATIONS.get("FRENCH", {}).get(key, key)

class AdvancedKPIDialog(BaseKPIDialog):
    """Dialog d'analyse KPI avancée."""
    
    def __init__(self, parent=None):
        super().__init__(parent, get_advanced_text("title"))
        self.advanced_data = {}
        logger.info("Initialisation du AdvancedKPIDialog")
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute les filtres spécifiques aux analyses avancées."""
        # Type d'analyse
        analysis_group = QGroupBox(get_advanced_text("analysis_type"))
        analysis_layout = QHBoxLayout(analysis_group)
        self.analysis_combo = QComboBox()
        self.analysis_combo.addItems([
            get_advanced_text("statistical"),
            get_advanced_text("predictive"),
            get_advanced_text("correlation")
        ])
        analysis_layout.addWidget(self.analysis_combo)
        toolbar_layout.addWidget(analysis_group)
        
        # Options d'affichage
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.show_anomalies_cb = QCheckBox(get_advanced_text("show_anomalies"))
        self.show_trends_cb = QCheckBox(get_advanced_text("show_trends"))
        self.show_predictions_cb = QCheckBox(get_advanced_text("show_predictions"))
        
        self.show_anomalies_cb.setChecked(True)
        self.show_trends_cb.setChecked(True)
        
        options_layout.addWidget(self.show_anomalies_cb)
        options_layout.addWidget(self.show_trends_cb)
        options_layout.addWidget(self.show_predictions_cb)
        
        toolbar_layout.addWidget(options_group)
    
    def create_specific_content(self):
        """Crée le contenu spécifique aux analyses avancées."""
        self.tab_widget = QTabWidget()
        self.content_layout.addWidget(self.tab_widget)
        
        # === ONGLET VUE D'ENSEMBLE ===
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Métriques avancées
        metrics_group = QGroupBox(get_advanced_text("advanced_metrics"))
        metrics_layout = QGridLayout(metrics_group)
        
        self.variance_label = QLabel("Variance des Coûts: --")
        self.std_dev_label = QLabel("Écart Type: --")
        self.trend_slope_label = QLabel("Pente de Tendance: --")
        self.correlation_coeff_label = QLabel("Coefficient de Corrélation: --")
        self.anomaly_count_label = QLabel("Anomalies Détectées: --")
        self.prediction_accuracy_label = QLabel("Précision Prédiction: --")
        
        # Style des métriques
        metric_style = """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                background-color: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }
        """
        
        for label in [self.variance_label, self.std_dev_label, self.trend_slope_label,
                     self.correlation_coeff_label, self.anomaly_count_label, self.prediction_accuracy_label]:
            label.setStyleSheet(metric_style)
        
        metrics_layout.addWidget(self.variance_label, 0, 0)
        metrics_layout.addWidget(self.std_dev_label, 0, 1)
        metrics_layout.addWidget(self.trend_slope_label, 1, 0)
        metrics_layout.addWidget(self.correlation_coeff_label, 1, 1)
        metrics_layout.addWidget(self.anomaly_count_label, 2, 0)
        metrics_layout.addWidget(self.prediction_accuracy_label, 2, 1)
        
        overview_layout.addWidget(metrics_group)
        
        # Utilisation du widget avancé si disponible
        if AdvancedKPIWidget:
            self.advanced_widget = AdvancedKPIWidget()
            overview_layout.addWidget(self.advanced_widget)
        else:
            placeholder = QLabel("📊 Graphiques d'analyse avancée en développement")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 16px;
                    font-style: italic;
                    padding: 40px;
                    border: 2px dashed #CCCCCC;
                    border-radius: 8px;
                }
            """)
            overview_layout.addWidget(placeholder)
        
        self.tab_widget.addTab(overview_widget, get_advanced_text("overview_tab"))
        
        # === AUTRES ONGLETS ===
        tab_names = [
            get_advanced_text("statistics_tab"),
            get_advanced_text("predictions_tab"),
            get_advanced_text("correlations_tab")
        ]
        
        for tab_name in tab_names:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            if "Statistiques" in tab_name:
                # Table statistique
                stats_table = QTableWidget()
                stats_table.setColumnCount(4)
                stats_table.setHorizontalHeaderLabels(["Métrique", "Valeur", "Tendance", "Statut"])
                stats_table.setRowCount(5)
                
                # Données exemple
                stats_data = [
                    ("Coût Moyen", "2,450€", "↗ +5%", "Normal"),
                    ("Temps Moyen", "3.2h", "↘ -2%", "Bon"),
                    ("Taux de Panne", "12%", "↗ +8%", "Attention"),
                    ("Disponibilité", "94%", "↗ +1%", "Excellent"),
                    ("Efficacité", "87%", "→ 0%", "Normal")
                ]
                
                for row, (metric, value, trend, status) in enumerate(stats_data):
                    stats_table.setItem(row, 0, QTableWidgetItem(metric))
                    stats_table.setItem(row, 1, QTableWidgetItem(value))
                    stats_table.setItem(row, 2, QTableWidgetItem(trend))
                    stats_table.setItem(row, 3, QTableWidgetItem(status))
                
                stats_table.setAlternatingRowColors(True)
                tab_layout.addWidget(stats_table)
            
            else:
                placeholder = QLabel(f"📊 {tab_name} en cours de développement")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("color: #666666; font-style: italic; padding: 40px;")
                tab_layout.addWidget(placeholder)
            
            self.tab_widget.addTab(tab_widget, tab_name)
    
    def load_data(self):
        """Charge les données d'analyse avancée."""
        self.set_status(get_advanced_text("loading_advanced"))
        
        try:
            # Simulation de calculs statistiques avancés
            import random
            import math
            
            # Génération de données temporelles
            data_points = [random.uniform(1000, 5000) for _ in range(100)]
            
            # Calculs statistiques
            mean_value = sum(data_points) / len(data_points)
            variance = sum((x - mean_value) ** 2 for x in data_points) / len(data_points)
            std_dev = math.sqrt(variance)
            
            # Simulation d'une tendance
            trend_slope = random.uniform(-50, 50)
            
            # Simulation de corrélation
            correlation_coeff = random.uniform(-1, 1)
            
            # Détection d'anomalies (simulation)
            anomaly_count = random.randint(3, 12)
            
            # Précision de prédiction (simulation)
            prediction_accuracy = random.uniform(75, 95)
            
            self.advanced_data = {
                "variance": variance,
                "std_dev": std_dev,
                "trend_slope": trend_slope,
                "correlation_coeff": correlation_coeff,
                "anomaly_count": anomaly_count,
                "prediction_accuracy": prediction_accuracy
            }
            
            self.update_views()
            self.set_status("Analyses avancées terminées", success=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse avancée: {e}")
            self.set_status(f"Erreur: {e}", success=False)
    
    def update_views(self):
        """Met à jour les vues avec les données calculées."""
        if not self.advanced_data:
            return
        
        data = self.advanced_data
        
        # Mise à jour des métriques
        self.variance_label.setText(f"Variance des Coûts: {data['variance']:.2f}")
        self.std_dev_label.setText(f"Écart Type: {data['std_dev']:.2f}")
        self.trend_slope_label.setText(f"Pente de Tendance: {data['trend_slope']:.2f}")
        self.correlation_coeff_label.setText(f"Coefficient de Corrélation: {data['correlation_coeff']:.3f}")
        self.anomaly_count_label.setText(f"Anomalies Détectées: {data['anomaly_count']}")
        self.prediction_accuracy_label.setText(f"Précision Prédiction: {data['prediction_accuracy']:.1f}%")
        
        # Mise à jour du widget avancé si disponible
        if hasattr(self, 'advanced_widget') and self.advanced_widget:
            # self.advanced_widget.update_data(self.advanced_data)
            pass
    
    def export_data(self):
        """Exporte les analyses avancées."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export", get_advanced_text("export_success"))
