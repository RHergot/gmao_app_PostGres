#!/usr/bin/env python3
"""
Dashboard principal pour les KPI financiers de la GMAO.
Permet de visualiser les coûts par centre de frais avec des graphiques interactifs.
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Imports PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDateEdit, QPushButton, QFrame,
    QScrollArea, QGroupBox, QSplitter, QTabWidget,
    QMessageBox, QProgressBar, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QIcon

# Ajouter le chemin pour les imports de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.core.services.kpi_service import KPIService
    from app.utils.logging_config import setup_logging
    # Import des widgets spécialisés
    from app.ui.kpi.widgets.machine_kpi_widget import MachineKPIWidget
    from app.ui.kpi.widgets.site_kpi_widget import SiteKPIWidget
    from app.ui.kpi.widgets.equipe_kpi_widget import EquipeKPIWidget
    from app.ui.kpi.widgets.preventif_curatif_widget import PreventifCuratifWidget
    from app.ui.kpi.widgets.global_summary_widget import GlobalSummaryWidget
except ImportError as e:
    print(f"Erreur d'import KPIService: {e}")
    KPIService = None
    setup_logging = None
    # Widgets par défaut
    MachineKPIWidget = None
    SiteKPIWidget = None
    EquipeKPIWidget = None
    PreventifCuratifWidget = None
    GlobalSummaryWidget = None

import logging
logger = logging.getLogger(__name__)

class KPIDataLoader(QThread):
    """Thread pour charger les données KPI de manière asynchrone."""
    
    data_loaded = Signal(str, dict)  # (type_data, data)
    error_occurred = Signal(str, str)  # (type_data, error_message)
    progress_updated = Signal(str, int)  # (message, percentage)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kpi_service = None
        self.load_tasks = []
        
    def add_load_task(self, task_type: str, method_name: str, **kwargs):
        """Ajoute une tâche de chargement à la queue."""
        self.load_tasks.append({
            'type': task_type,
            'method': method_name,
            'kwargs': kwargs
        })
    
    def run(self):
        """Exécute les tâches de chargement."""
        if not self.load_tasks:
            return
            
        try:
            if KPIService is None:
                self.error_occurred.emit("general", "KPIService non disponible")
                return
                
            self.kpi_service = KPIService()
            total_tasks = len(self.load_tasks)
            
            for i, task in enumerate(self.load_tasks):
                try:
                    # Mettre à jour le progrès
                    progress = int((i / total_tasks) * 100)
                    self.progress_updated.emit(f"Chargement {task['type']}...", progress)
                    
                    # Exécuter la méthode du service
                    method = getattr(self.kpi_service, task['method'])
                    data = method(**task['kwargs'])
                    
                    # Émettre les données
                    self.data_loaded.emit(task['type'], data)
                    
                except Exception as e:
                    logger.error(f"Erreur lors du chargement {task['type']}: {e}")
                    self.error_occurred.emit(task['type'], str(e))
            
            # Chargement terminé
            self.progress_updated.emit("Chargement terminé", 100)
            
        except Exception as e:
            logger.error(f"Erreur générale dans KPIDataLoader: {e}")
            self.error_occurred.emit("general", str(e))
        finally:
            self.load_tasks.clear()


class KPIDashboard(QWidget):
    """
    Dashboard principal pour les KPI financiers.
    
    Permet de:
    - Sélectionner des centres de frais (machine, site, équipe)
    - Choisir des périodes d'analyse
    - Visualiser les KPI avec des graphiques
    - Exporter les données
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kpi_service = None
        self.current_data = {}
        self.data_loader = None
        
        # Configuration du logging
        setup_logging()
        logger.info("Initialisation du KPI Dashboard")
        
        self.setup_ui()
        self.setup_connections()
        self.setup_data_loader()
        
        # Chargement initial des données
        QTimer.singleShot(100, self.load_initial_data)
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("📊 Dashboard KPI Financiers")
        self.setMinimumSize(1200, 800)
        
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Splitter pour diviser sidebar et contenu principal
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # === SIDEBAR GAUCHE ===
        self.create_sidebar(splitter)
        
        # === ZONE PRINCIPALE ===
        self.create_main_content(splitter)
        
        # === BARRE DE STATUT ===
        self.create_status_bar()
        
        # Proportions du splitter (20% sidebar, 80% contenu)
        splitter.setSizes([300, 900])
        
        # Style général
        self.apply_styles()
    
    def create_sidebar(self, parent):
        """Crée la sidebar avec les contrôles."""
        sidebar = QFrame()
        sidebar.setFrameStyle(QFrame.StyledPanel)
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # === TITRE SIDEBAR ===
        title_label = QLabel("🎛️ Contrôles KPI")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_label)
        
        sidebar_layout.addSpacing(20)
        
        # === SÉLECTION CENTRE DE FRAIS ===
        centre_group = QGroupBox("Centre de Frais")
        centre_layout = QVBoxLayout(centre_group)
        
        centre_layout.addWidget(QLabel("Type d'analyse:"))
        self.centre_combo = QComboBox()
        self.centre_combo.addItems([
            "🏭 Par Machine",
            "🏢 Par Site", 
            "👥 Par Équipe",
            "🔧 Préventif vs Curatif",
            "📊 Résumé Global"
        ])
        centre_layout.addWidget(self.centre_combo)
        
        sidebar_layout.addWidget(centre_group)
        
        # === SÉLECTION PÉRIODE ===
        periode_group = QGroupBox("Période d'Analyse")
        periode_layout = QVBoxLayout(periode_group)
        
        periode_layout.addWidget(QLabel("Du:"))
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-6))
        self.date_debut.setCalendarPopup(True)
        periode_layout.addWidget(self.date_debut)
        
        periode_layout.addWidget(QLabel("Au:"))
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        periode_layout.addWidget(self.date_fin)
        
        # Boutons de période prédéfinie
        periode_buttons_layout = QHBoxLayout()
        
        self.btn_mois = QPushButton("1 Mois")
        self.btn_trimestre = QPushButton("3 Mois") 
        self.btn_semestre = QPushButton("6 Mois")
        
        periode_buttons_layout.addWidget(self.btn_mois)
        periode_buttons_layout.addWidget(self.btn_trimestre)
        periode_buttons_layout.addWidget(self.btn_semestre)
        
        periode_layout.addLayout(periode_buttons_layout)
        sidebar_layout.addWidget(periode_group)
        
        # === BOUTONS D'ACTION ===
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.btn_actualiser = QPushButton("🔄 Actualiser")
        self.btn_actualiser.setStyleSheet("QPushButton { background-color: #2E86AB; color: white; font-weight: bold; }")
        actions_layout.addWidget(self.btn_actualiser)
        
        self.btn_export = QPushButton("📊 Exporter Excel")
        actions_layout.addWidget(self.btn_export)
        
        self.btn_rapport = QPushButton("📄 Générer Rapport")
        actions_layout.addWidget(self.btn_rapport)
        
        sidebar_layout.addWidget(actions_group)
        
        # === RÉSUMÉ RAPIDE ===
        self.create_quick_summary(sidebar_layout)
        
        # Spacer pour pousser tout vers le haut
        sidebar_layout.addStretch()
        
        parent.addWidget(sidebar)
        self.sidebar = sidebar
    
    def create_quick_summary(self, parent_layout):
        """Crée le widget de résumé rapide."""
        summary_group = QGroupBox("📋 Résumé Rapide")
        summary_layout = QVBoxLayout(summary_group)
        
        # Métriques clés
        self.lbl_cout_total = QLabel("Coût Total: --")
        self.lbl_nb_interventions = QLabel("Interventions: --")
        self.lbl_cout_moyen = QLabel("Coût Moyen: --")
        self.lbl_machines_actives = QLabel("Machines: --")
        
        # Style pour les métriques
        metric_style = "QLabel { font-size: 12px; margin: 2px; }"
        for lbl in [self.lbl_cout_total, self.lbl_nb_interventions, 
                   self.lbl_cout_moyen, self.lbl_machines_actives]:
            lbl.setStyleSheet(metric_style)
            summary_layout.addWidget(lbl)
        
        parent_layout.addWidget(summary_group)
    
    def create_main_content(self, parent):
        """Crée la zone de contenu principal avec onglets des widgets KPI."""
        # Widget principal avec onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        
        # === ONGLET VUE D'ENSEMBLE ===
        if GlobalSummaryWidget:
            self.global_widget = GlobalSummaryWidget()
            self.tab_widget.addTab(self.global_widget, "🏠 Vue d'Ensemble")
        else:
            self.tab_widget.addTab(QLabel("Widget Vue d'Ensemble non disponible"), "🏠 Vue d'Ensemble")
        
        # === ONGLET MACHINES ===
        if MachineKPIWidget:
            self.machine_widget = MachineKPIWidget()
            self.tab_widget.addTab(self.machine_widget, "🏭 Par Machine")
        else:
            self.tab_widget.addTab(QLabel("Widget Machine non disponible"), "🏭 Par Machine")
        
        # === ONGLET SITES ===
        if SiteKPIWidget:
            self.site_widget = SiteKPIWidget()
            self.tab_widget.addTab(self.site_widget, "🏢 Par Site")
        else:
            self.tab_widget.addTab(QLabel("Widget Site non disponible"), "🏢 Par Site")
        
        # === ONGLET ÉQUIPES ===
        if EquipeKPIWidget:
            self.equipe_widget = EquipeKPIWidget()
            self.tab_widget.addTab(self.equipe_widget, "👥 Par Équipe")
        else:
            self.tab_widget.addTab(QLabel("Widget Équipe non disponible"), "👥 Par Équipe")
        
        # === ONGLET PRÉVENTIF/CURATIF ===
        if PreventifCuratifWidget:
            self.preventif_widget = PreventifCuratifWidget()
            self.tab_widget.addTab(self.preventif_widget, "🔧 Préventif/Curatif")
        else:
            self.tab_widget.addTab(QLabel("Widget Préventif/Curatif non disponible"), "🔧 Préventif/Curatif")
        
        # Connecter le changement d'onglet
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        parent.addWidget(self.tab_widget)
        self.content_widget = self.tab_widget
        
    def on_tab_changed(self, index):
        """Gestionnaire de changement d'onglet."""
        tab_names = ["Vue d'Ensemble", "Par Machine", "Par Site", "Par Équipe", "Préventif/Curatif"]
        if 0 <= index < len(tab_names):
            logger.info(f"Changement vers l'onglet: {tab_names[index]}")
            
            # Rafraîchir les données du widget actuel
            current_widget = self.tab_widget.currentWidget()
            if hasattr(current_widget, 'refresh_data'):
                QTimer.singleShot(100, current_widget.refresh_data)
    
    def create_status_bar(self):
        """Crée la barre de statut."""
        status_layout = QHBoxLayout()
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        
        # Label de statut
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("QLabel { color: #6C757D; }")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_bar)
        
        # Ajouter au layout principal
        main_layout = self.layout()
        main_layout.addLayout(status_layout)
    
    def setup_connections(self):
        """Configure les connexions des signaux."""
        # Connexions des contrôles
        self.centre_combo.currentTextChanged.connect(self.on_centre_changed)
        self.date_debut.dateChanged.connect(self.on_date_changed)
        self.date_fin.dateChanged.connect(self.on_date_changed)
        
        # Boutons de période
        self.btn_mois.clicked.connect(lambda: self.set_periode_relative(30))
        self.btn_trimestre.clicked.connect(lambda: self.set_periode_relative(90))
        self.btn_semestre.clicked.connect(lambda: self.set_periode_relative(180))
        
        # Boutons d'action
        self.btn_actualiser.clicked.connect(self.refresh_data)
        self.btn_export.clicked.connect(self.export_data)
        self.btn_rapport.clicked.connect(self.generate_report)
    
    def setup_data_loader(self):
        """Configure le loader de données asynchrone."""
        self.data_loader = KPIDataLoader()
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.error_occurred.connect(self.on_data_error)
        self.data_loader.progress_updated.connect(self.on_progress_updated)
    
    def apply_styles(self):
        """Applique les styles CSS."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                padding: 8px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: #F8F9FA;
            }
            
            QPushButton:hover {
                background-color: #E9ECEF;
            }
            
            QPushButton:pressed {
                background-color: #DEE2E6;
            }
            
            QComboBox, QDateEdit {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            
            QFrame {
                background-color: #FFFFFF;
            }
        """)
    
    # === ÉVÉNEMENTS ===
    
    def on_centre_changed(self, text):
        """Gère le changement de centre de frais."""
        logger.info(f"Centre de frais changé: {text}")
        
        # Mettre à jour le titre
        if "Machine" in text:
            self.main_title.setText("🏭 Analyse des Coûts par Machine")
        elif "Site" in text:
            self.main_title.setText("🏢 Analyse des Coûts par Site")
        elif "Équipe" in text:
            self.main_title.setText("👥 Analyse des Coûts par Équipe")
        elif "Préventif" in text:
            self.main_title.setText("🔧 Analyse Préventif vs Curatif")
        else:
            self.main_title.setText("📊 Résumé Global des KPI")
        
        # Recharger les données
        self.refresh_data()
    
    def on_date_changed(self):
        """Gère le changement de dates."""
        logger.debug("Dates modifiées")
        # Auto-refresh après 1 seconde d'inactivité
        if hasattr(self, '_date_timer'):
            self._date_timer.stop()
        
        self._date_timer = QTimer()
        self._date_timer.setSingleShot(True)
        self._date_timer.timeout.connect(self.refresh_data)
        self._date_timer.start(1000)
    
    def set_periode_relative(self, days: int):
        """Définit une période relative (ex: 30 derniers jours)."""
        date_fin = QDate.currentDate()
        date_debut = date_fin.addDays(-days)
        
        self.date_debut.setDate(date_debut)
        self.date_fin.setDate(date_fin)
    
    def on_data_loaded(self, data_type: str, data: dict):
        """Gère la réception de données."""
        logger.info(f"Données reçues pour {data_type}: {len(data) if isinstance(data, list) else 'dict'}")
        
        self.current_data[data_type] = data
        self.update_display(data_type, data)
        self.update_quick_summary()
    
    def on_data_error(self, data_type: str, error_message: str):
        """Gère les erreurs de chargement."""
        logger.error(f"Erreur chargement {data_type}: {error_message}")
        
        # Afficher message d'erreur
        self.show_error_message(f"Erreur lors du chargement des données {data_type}:\n{error_message}")
        
        # Masquer la barre de progression
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Erreur: {data_type}")
    
    def on_progress_updated(self, message: str, percentage: int):
        """Met à jour la barre de progression."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        
        if percentage >= 100:
            QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))
            QTimer.singleShot(2000, lambda: self.status_label.setText("Prêt"))
    
    # === MÉTHODES DE DONNÉES ===
    
    def load_initial_data(self):
        """Charge les données initiales."""
        logger.info("Chargement des données initiales")
        self.refresh_data()
    
    def refresh_data(self):
        """Actualise les données dans tous les widgets KPI."""
        if not self.date_debut.date().isValid() or not self.date_fin.date().isValid():
            logger.warning("Dates invalides pour le chargement")
            return
        
        debut = self.date_debut.date().toPython()
        fin = self.date_fin.date().toPython()
        
        logger.info(f"Actualisation des données du {debut} au {fin}")
        
        # Mettre à jour chaque widget avec les nouvelles dates
        try:
            # Widget global (vue d'ensemble)
            if hasattr(self, 'global_widget') and hasattr(self.global_widget, 'load_data'):
                self.global_widget.load_data(debut, fin)
            
            # Widget machines
            if hasattr(self, 'machine_widget') and hasattr(self.machine_widget, 'load_data'):
                self.machine_widget.load_data(debut, fin)
            
            # Widget sites
            if hasattr(self, 'site_widget') and hasattr(self.site_widget, 'load_data'):
                self.site_widget.load_data(debut, fin)
            
            # Widget équipes
            if hasattr(self, 'equipe_widget') and hasattr(self.equipe_widget, 'load_data'):
                self.equipe_widget.load_data(debut, fin)
            
            # Widget préventif/curatif
            if hasattr(self, 'preventif_widget') and hasattr(self.preventif_widget, 'load_data'):
                self.preventif_widget.load_data(debut, fin)
                
            # Mettre à jour le résumé rapide dans la sidebar
            self.update_quick_summary()
                
        except Exception as e:
            logger.error(f"Erreur lors de l'actualisation: {e}")
            self.show_error_message(f"Erreur lors de l'actualisation des données:\n{str(e)}")
    
    def update_quick_summary(self):
        """Met à jour le résumé rapide dans la sidebar."""
        try:
            if hasattr(self, 'global_widget') and hasattr(self.global_widget, 'current_data'):
                data = self.global_widget.current_data
                
                if 'machines' in data and data['machines']:
                    total_cost = sum(item.get('cout_total', 0) for item in data['machines'])
                    nb_machines = len(data['machines'])
                    nb_interventions = sum(item.get('nb_interventions', 0) for item in data['machines'])
                    cout_moyen = total_cost / nb_machines if nb_machines > 0 else 0
                    
                    self.lbl_cout_total.setText(f"Coût Total: {total_cost:,.0f} €")
                    self.lbl_nb_interventions.setText(f"Interventions: {nb_interventions}")
                    self.lbl_cout_moyen.setText(f"Coût Moyen: {cout_moyen:,.0f} €")
                    self.lbl_machines_actives.setText(f"Machines: {nb_machines}")
                else:
                    self.lbl_cout_total.setText("Coût Total: --")
                    self.lbl_nb_interventions.setText("Interventions: --")
                    self.lbl_cout_moyen.setText("Coût Moyen: --")
                    self.lbl_machines_actives.setText("Machines: --")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du résumé: {e}")
    
    def show_error_message(self, message: str):
        """Affiche un message d'erreur."""
        QMessageBox.critical(self, "Erreur", message)
    
    def export_data(self):
        """Exporte les données actuelles."""
        try:
            current_widget = self.tab_widget.currentWidget()
            if hasattr(current_widget, 'export_to_excel'):
                current_widget.export_to_excel()
            else:
                QMessageBox.information(self, "Info", "Export non disponible pour cet onglet")
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            self.show_error_message(f"Erreur lors de l'export: {str(e)}")


# === MAIN STANDALONE ===

if __name__ == "__main__":
    """Test standalone du dashboard."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Créer et afficher le dashboard
    dashboard = KPIDashboard()
    dashboard.show()
    dashboard.resize(1400, 900)
    
    sys.exit(app.exec())
                        info_text += f"  {key}: {value}\n"
                    info_text += "\n"
            
            if len(data) > 5:
                info_text += f"... et {len(data) - 5} autres éléments"
                
        elif isinstance(data, dict):
            info_text = "Données reçues:\n\n"
            for key, value in data.items():
                info_text += f"• {key}: {value}\n"
        else:
            info_text = f"Type de données: {type(data)}\nContenu: {str(data)[:200]}"
        
        info_label.setText(info_label.text() + info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { padding: 20px; background-color: #F8F9FA; border-radius: 5px; }")
        
        self.kpi_layout.addWidget(info_label)
    
    def display_machines_data(self, data):
        """Affiche les données des machines."""
        self.display_simple_data("Machines", data)
    
    def display_sites_data(self, data):
        """Affiche les données des sites."""
        self.display_simple_data("Sites", data)
    
    def display_equipes_data(self, data):
        """Affiche les données des équipes."""
        self.display_simple_data("Équipes", data)
    
    def display_preventif_curatif_data(self, data):
        """Affiche les données préventif/curatif."""
        self.display_simple_data("Préventif/Curatif", data)
    
    def display_resume_data(self, data):
        """Affiche le résumé global."""
        self.display_simple_data("Résumé Global", data)
    
    def update_quick_summary(self):
        """Met à jour le résumé rapide dans la sidebar."""
        try:
            # Calculer un résumé basé sur les données actuelles
            total_cout = 0
            total_interventions = 0
            machines_count = 0
            
            for data_type, data in self.current_data.items():
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            total_cout += float(item.get('cout_total', 0) or 0)
                            total_interventions += int(item.get('nb_interventions', 0) or 0)
                            if 'machine_nom' in item or 'id_machine' in item:
                                machines_count += 1
                elif isinstance(data, dict):
                    total_cout += float(data.get('cout_total', 0) or 0)
                    total_interventions += int(data.get('nb_interventions', 0) or 0)
            
            # Mettre à jour les labels
            self.lbl_cout_total.setText(f"Coût Total: {total_cout:,.2f}€")
            self.lbl_nb_interventions.setText(f"Interventions: {total_interventions}")
            
            if total_interventions > 0:
                cout_moyen = total_cout / total_interventions
                self.lbl_cout_moyen.setText(f"Coût Moyen: {cout_moyen:.2f}€")
            else:
                self.lbl_cout_moyen.setText("Coût Moyen: --")
            
            self.lbl_machines_actives.setText(f"Machines: {machines_count}")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour résumé: {e}")
    
    # === ACTIONS ===
    
    def export_data(self):
        """Exporte les données vers Excel."""
        self.show_info_message("Export en cours de développement", 
                              "La fonctionnalité d'export sera disponible dans la prochaine version.")
    
    def generate_report(self):
        """Génère un rapport PDF."""
        self.show_info_message("Rapport en cours de développement",
                              "La génération de rapports sera disponible dans la prochaine version.")
    
    # === UTILITAIRES ===
    
    def show_error_message(self, message: str):
        """Affiche un message d'erreur."""
        QMessageBox.critical(self, "Erreur", message)
    
    def show_info_message(self, title: str, message: str):
        """Affiche un message d'information."""
        QMessageBox.information(self, title, message)


# === TEST STANDALONE ===
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("Dashboard KPI GMAO")
    
    # Test du dashboard
    dashboard = KPIDashboard()
    dashboard.show()
    
    sys.exit(app.exec())
