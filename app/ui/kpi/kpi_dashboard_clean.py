#!/usr/bin/env python3
"""
Dashboard principal pour les KPI financiers de la GMAO.
Permet de visualiser les coûts par centre de frais avec des graphiques interactifs.

Note sur la traduction :
Ce module utilise un système de dictionnaire de traductions (TRANSLATIONS + get_text())
pour des raisons de simplicité et d'isolement. Le reste de l'application utilise
QTranslator + self.tr() qui est la méthode standard Qt.
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
    from config import APP_NAME, APP_VERSION, LOG_LEVEL  # Import de la configuration principale
    from app.config import app_config, Language  # Import de la configuration de langue
    from app.core.services.kpi_service import KPIService
    from app.utils.logging_config import setup_logging
    # Import des widgets spécialisés
    from app.ui.kpi.widgets.machine_kpi_widget import MachineKPIWidget
    from app.ui.kpi.widgets.site_kpi_widget import SiteKPIWidget
    from app.ui.kpi.widgets.equipe_kpi_widget import EquipeKPIWidget
    from app.ui.kpi.widgets.preventif_curatif_widget import PreventifCuratifWidget
    from app.ui.kpi.widgets.global_summary_widget import GlobalSummaryWidget
    from app.ui.kpi.widgets.advanced_kpi_widget import AdvancedKPIWidget
except ImportError as e:
    print(f"Erreur d'import KPIService: {e}")
    # Valeurs par défaut si config.py n'est pas accessible
    APP_NAME = "GMAO Industrielle"
    APP_VERSION = "1.0"
    LOG_LEVEL = "INFO"
    KPIService = None
    setup_logging = None
    # Widgets par défaut
    MachineKPIWidget = None
    SiteKPIWidget = None
    EquipeKPIWidget = None
    PreventifCuratifWidget = None
    GlobalSummaryWidget = None
    AdvancedKPIWidget = None

import logging
logger = logging.getLogger(__name__)

# === TRADUCTIONS ===
TRANSLATIONS = {
    Language.FRENCH: {
        "dashboard_title": "📊 Dashboard KPI Financiers",
        "controls_title": "🎛️ Contrôles KPI",
        "cost_center": "Centre de Frais",
        "analysis_period": "Période d'Analyse",
        "quick_summary": "📋 Résumé Rapide",
        "actions": "Actions",
        "refresh": "🔄 Actualiser",
        "export": "📊 Exporter",
        "close": "❌ Fermer",
        "overview": "📊 Vue d'Ensemble",
        "by_machine": "🏭 Par Machine",
        "by_site": "🏢 Par Site", 
        "by_team": "👥 Par Équipe",
        "preventive_corrective": "🔧 Préventif vs Curatif",
        "advanced_analysis": "🔬 Analyse Avancée",
        "total_cost": "Coût Total",
        "interventions": "Interventions",
        "average_cost": "Coût Moyen",
        "machines": "Machines",
        "from": "Du:",
        "to": "Au:",
        "refresh_tooltip": "Actualiser les données (F5)",
        "export_tooltip": "Exporter les données vers Excel",
        "close_tooltip": "Fermer le dashboard KPI (Échap ou Ctrl+W)"
    },
    Language.ENGLISH: {
        "dashboard_title": "📊 Financial KPI Dashboard",
        "controls_title": "🎛️ KPI Controls",
        "cost_center": "Cost Center",
        "analysis_period": "Analysis Period",
        "quick_summary": "📋 Quick Summary",
        "actions": "Actions",
        "refresh": "🔄 Refresh",
        "export": "📊 Export",
        "close": "❌ Close",
        "overview": "📊 Overview",
        "by_machine": "🏭 By Machine",
        "by_site": "🏢 By Site",
        "by_team": "👥 By Team",
        "preventive_corrective": "🔧 Preventive vs Corrective",
        "advanced_analysis": "🔬 Advanced Analysis",
        "total_cost": "Total Cost",
        "interventions": "Interventions",
        "average_cost": "Average Cost",
        "machines": "Machines",
        "from": "From:",
        "to": "To:",
        "refresh_tooltip": "Refresh data (F5)",
        "export_tooltip": "Export data to Excel",
        "close_tooltip": "Close KPI dashboard (Esc or Ctrl+W)"
    },
    Language.GERMAN: {
        "dashboard_title": "📊 Finanzkennzahlen Dashboard",
        "controls_title": "🎛️ KPI Steuerung",
        "cost_center": "Kostenstelle",
        "analysis_period": "Analysezeitraum",
        "quick_summary": "📋 Schnellübersicht",
        "actions": "Aktionen",
        "refresh": "🔄 Aktualisieren",
        "export": "📊 Exportieren",
        "close": "❌ Schließen",
        "overview": "📊 Übersicht",
        "by_machine": "🏭 Nach Maschine",
        "by_site": "🏢 Nach Standort",
        "by_team": "👥 Nach Team",
        "preventive_corrective": "🔧 Präventiv vs Korrektiv",
        "advanced_analysis": "🔬 Erweiterte Analyse",
        "total_cost": "Gesamtkosten",
        "interventions": "Interventionen",
        "average_cost": "Durchschnittskosten",
        "machines": "Maschinen",
        "from": "Von:",
        "to": "Bis:",
        "refresh_tooltip": "Daten aktualisieren (F5)",
        "export_tooltip": "Daten nach Excel exportieren",
        "close_tooltip": "KPI Dashboard schließen (Esc oder Ctrl+W)"
    }
}

def get_text(key: str) -> str:
    """Récupère le texte traduit selon la langue configurée."""
    try:
        current_lang = app_config.language if 'app_config' in globals() else Language.FRENCH
        return TRANSLATIONS.get(current_lang, TRANSLATIONS[Language.FRENCH]).get(key, key)
    except:
        return TRANSLATIONS[Language.FRENCH].get(key, key)


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
        
        # Configuration du logging
        if setup_logging:
            setup_logging()
        logger.info(f"Initialisation du KPI Dashboard - {APP_NAME} v{APP_VERSION}")
        logger.debug(f"Niveau de log configuré: {LOG_LEVEL}")
        
        self.setup_ui()
        self.setup_connections()
        
        # Chargement initial des données
        QTimer.singleShot(100, self.load_initial_data)
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle(f"{get_text('dashboard_title')} - {APP_NAME}")
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
        
        # === RACCOURCIS CLAVIER ===
        self.setup_shortcuts()
        
        # Proportions du splitter (20% sidebar, 80% contenu)
        splitter.setSizes([300, 900])
    
    def setup_shortcuts(self):
        """Configure les raccourcis clavier."""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Raccourci Escape pour fermer
        escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        escape_shortcut.activated.connect(self.close_dashboard)
        
        # Raccourci Ctrl+W pour fermer (standard Windows/Mac)
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close_dashboard)
        
        # Raccourci F5 pour actualiser
        refresh_shortcut = QShortcut(QKeySequence(Qt.Key_F5), self)
        refresh_shortcut.activated.connect(self.refresh_data)
        
    def create_sidebar(self, parent):
        """Crée la sidebar de navigation et contrôles."""
        sidebar = QFrame()
        sidebar.setFrameStyle(QFrame.StyledPanel)
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("QFrame { background-color: #F8F9FA; }")
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(15)
        
        # === TITRE SIDEBAR ===
        title_label = QLabel(f"{get_text('controls_title')}\nv{APP_VERSION}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_label)
        
        # === SÉLECTION CENTRE DE FRAIS ===
        self.create_centre_selection(sidebar_layout)
        
        # === SÉLECTION PÉRIODE ===
        self.create_periode_selection(sidebar_layout)
        
        # === RÉSUMÉ RAPIDE ===
        self.create_quick_summary(sidebar_layout)
        
        # === BOUTONS D'ACTIONS ===
        self.create_action_buttons(sidebar_layout)
        
        # Spacer pour pousser tout vers le haut
        sidebar_layout.addStretch()
        
        parent.addWidget(sidebar)
        self.sidebar = sidebar
    
    def create_centre_selection(self, parent_layout):
        """Crée la zone de sélection du centre de frais."""
        centre_group = QGroupBox(get_text("cost_center"))
        centre_layout = QVBoxLayout(centre_group)
        
        self.centre_combo = QComboBox()
        self.centre_combo.addItems([
            get_text("overview"),
            get_text("by_machine"), 
            get_text("by_site"),
            get_text("by_team"),
            get_text("preventive_corrective"),
            get_text("advanced_analysis")
        ])
        self.centre_combo.setCurrentIndex(0)
        centre_layout.addWidget(self.centre_combo)
        
        parent_layout.addWidget(centre_group)
    
    def create_periode_selection(self, parent_layout):
        """Crée la zone de sélection de période."""
        periode_group = QGroupBox(get_text("analysis_period"))
        periode_layout = QVBoxLayout(periode_group)
        
        # Dates
        date_layout = QGridLayout()
        
        date_layout.addWidget(QLabel(get_text("from")), 0, 0)
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.currentDate().addMonths(-3))
        self.date_debut.setCalendarPopup(True)
        date_layout.addWidget(self.date_debut, 0, 1)
        
        date_layout.addWidget(QLabel(get_text("to")), 1, 0)
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setCalendarPopup(True)
        date_layout.addWidget(self.date_fin, 1, 1)
        
        periode_layout.addLayout(date_layout)
        
        # Boutons de période rapide
        quick_buttons_layout = QHBoxLayout()
        
        btn_30j = QPushButton("30j")
        btn_30j.setMaximumWidth(40)
        btn_30j.clicked.connect(lambda: self.set_periode_relative(30))
        quick_buttons_layout.addWidget(btn_30j)
        
        btn_90j = QPushButton("90j")
        btn_90j.setMaximumWidth(40)
        btn_90j.clicked.connect(lambda: self.set_periode_relative(90))
        quick_buttons_layout.addWidget(btn_90j)
        
        btn_1an = QPushButton("1an")
        btn_1an.setMaximumWidth(40)
        btn_1an.clicked.connect(lambda: self.set_periode_relative(365))
        quick_buttons_layout.addWidget(btn_1an)
        
        periode_layout.addLayout(quick_buttons_layout)
        parent_layout.addWidget(periode_group)
    
    def create_quick_summary(self, parent_layout):
        """Crée le widget de résumé rapide."""
        summary_group = QGroupBox(get_text("quick_summary"))
        summary_layout = QVBoxLayout(summary_group)
        
        # Métriques clés
        self.lbl_cout_total = QLabel(f"{get_text('total_cost')}: --")
        self.lbl_nb_interventions = QLabel(f"{get_text('interventions')}: --")
        self.lbl_cout_moyen = QLabel(f"{get_text('average_cost')}: --")
        self.lbl_machines_actives = QLabel(f"{get_text('machines')}: --")
        
        # Style pour les métriques
        metric_style = "QLabel { font-size: 12px; margin: 2px; }"
        for lbl in [self.lbl_cout_total, self.lbl_nb_interventions, 
                   self.lbl_cout_moyen, self.lbl_machines_actives]:
            lbl.setStyleSheet(metric_style)
            summary_layout.addWidget(lbl)
        
        parent_layout.addWidget(summary_group)
    
    def create_action_buttons(self, parent_layout):
        """Crée les boutons d'actions."""
        actions_group = QGroupBox(get_text("actions"))
        actions_layout = QVBoxLayout(actions_group)
        
        # Bouton rafraîchir
        btn_refresh = QPushButton(get_text("refresh"))
        btn_refresh.setToolTip(get_text("refresh_tooltip"))
        btn_refresh.clicked.connect(self.refresh_data)
        actions_layout.addWidget(btn_refresh)
        
        # Bouton export
        btn_export = QPushButton(get_text("export"))
        btn_export.setToolTip(get_text("export_tooltip"))
        btn_export.clicked.connect(self.export_data)
        actions_layout.addWidget(btn_export)
        
        # Séparateur
        actions_layout.addSpacing(10)
        
        # Bouton fermer
        btn_close = QPushButton(get_text("close"))
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        btn_close.setToolTip(get_text("close_tooltip"))
        btn_close.clicked.connect(self.close_dashboard)
        actions_layout.addWidget(btn_close)
        
        parent_layout.addWidget(actions_group)
    
    def create_main_content(self, parent):
        """Crée la zone de contenu principal avec onglets des widgets KPI."""
        # Widget principal avec onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        
        # === ONGLET VUE D'ENSEMBLE ===
        if GlobalSummaryWidget:
            self.global_widget = GlobalSummaryWidget()
            self.tab_widget.addTab(self.global_widget, get_text("overview"))
        else:
            self.tab_widget.addTab(QLabel("Widget Vue d'Ensemble non disponible"), get_text("overview"))
        
        # === ONGLET MACHINES ===
        if MachineKPIWidget:
            self.machine_widget = MachineKPIWidget()
            self.tab_widget.addTab(self.machine_widget, get_text("by_machine"))
        else:
            self.tab_widget.addTab(QLabel("Widget Machine non disponible"), get_text("by_machine"))
        
        # === ONGLET SITES ===
        if SiteKPIWidget:
            self.site_widget = SiteKPIWidget()
            self.tab_widget.addTab(self.site_widget, get_text("by_site"))
        else:
            self.tab_widget.addTab(QLabel("Widget Site non disponible"), get_text("by_site"))
        
        # === ONGLET ÉQUIPES ===
        if EquipeKPIWidget:
            self.equipe_widget = EquipeKPIWidget()
            self.tab_widget.addTab(self.equipe_widget, get_text("by_team"))
        else:
            self.tab_widget.addTab(QLabel("Widget Équipe non disponible"), get_text("by_team"))
        
        # === ONGLET PRÉVENTIF/CURATIF ===
        if PreventifCuratifWidget:
            self.preventif_widget = PreventifCuratifWidget()
            self.tab_widget.addTab(self.preventif_widget, get_text("preventive_corrective"))
        else:
            self.tab_widget.addTab(QLabel("Widget Préventif/Curatif non disponible"), get_text("preventive_corrective"))
        
        # === ONGLET ANALYSE AVANCÉE ===
        if AdvancedKPIWidget:
            self.advanced_widget = AdvancedKPIWidget()
            self.tab_widget.addTab(self.advanced_widget, get_text("advanced_analysis"))
        else:
            self.tab_widget.addTab(QLabel("Widget Analyse Avancée non disponible"), get_text("advanced_analysis"))
        
        # Connecter le changement d'onglet
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        parent.addWidget(self.tab_widget)
        self.content_widget = self.tab_widget
        
    def on_tab_changed(self, index):
        """Gestionnaire de changement d'onglet."""
        tab_names = ["Vue d'Ensemble", "Par Machine", "Par Site", "Par Équipe", "Préventif/Curatif", "Analyse Avancée"]
        if 0 <= index < len(tab_names):
            logger.info(f"Changement vers l'onglet: {tab_names[index]}")
            
            # Synchroniser la combo box de la sidebar
            self.centre_combo.setCurrentIndex(index)
            
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
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_bar)
        
        # Ajouter à la layout principale (en bas)
        if hasattr(self, 'layout'):
            self.layout().addLayout(status_layout)
    
    def setup_connections(self):
        """Configure les connexions des signaux."""
        # Connexions des contrôles
        self.centre_combo.currentTextChanged.connect(self.on_centre_changed)
        self.date_debut.dateChanged.connect(self.on_date_changed)
        self.date_fin.dateChanged.connect(self.on_date_changed)
        
        # Style de l'application
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
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
        
        # Synchroniser l'onglet avec la sélection
        index_map = {
            get_text("overview"): 0,
            get_text("by_machine"): 1,
            get_text("by_site"): 2,
            get_text("by_team"): 3,
            get_text("preventive_corrective"): 4,
            get_text("advanced_analysis"): 5
        }
        
        if text in index_map:
            self.tab_widget.setCurrentIndex(index_map[text])
        
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
                
            # Widget avancé
            if hasattr(self, 'advanced_widget') and hasattr(self.advanced_widget, 'load_filtered_data'):
                # L'advanced widget gère ses propres données avec ses propres filtres
                pass
                
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
                    
                    self.lbl_cout_total.setText(f"{get_text('total_cost')}: {total_cost:,.0f} €")
                    self.lbl_nb_interventions.setText(f"{get_text('interventions')}: {nb_interventions}")
                    self.lbl_cout_moyen.setText(f"{get_text('average_cost')}: {cout_moyen:,.0f} €")
                    self.lbl_machines_actives.setText(f"{get_text('machines')}: {nb_machines}")
                else:
                    self.lbl_cout_total.setText(f"{get_text('total_cost')}: --")
                    self.lbl_nb_interventions.setText(f"{get_text('interventions')}: --")
                    self.lbl_cout_moyen.setText(f"{get_text('average_cost')}: --")
                    self.lbl_machines_actives.setText(f"{get_text('machines')}: --")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du résumé: {e}")
    
    def show_error_message(self, message: str):
        """Affiche un message d'erreur."""
        QMessageBox.critical(self, "Erreur", message)
    
    def close_dashboard(self):
        """Ferme le dashboard KPI."""
        try:
            logger.info("Fermeture du dashboard KPI demandée par l'utilisateur")
            
            # Demander confirmation si des données sont en cours de traitement
            if hasattr(self, 'progress_bar') and self.progress_bar.isVisible():
                reply = QMessageBox.question(
                    self, 
                    "Confirmer la fermeture", 
                    "Des opérations sont en cours. Voulez-vous vraiment fermer le dashboard ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # Fermer la fenêtre
            self.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture du dashboard: {e}")
            # Forcer la fermeture même en cas d'erreur
            self.close()
    
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
