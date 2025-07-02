#!/usr/bin/env python3
"""
Classe de base pour les dialogs KPI spécialisés.
Fournit une structure commune et des fonctionnalités partagées.
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Imports PySide6
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDateEdit, QPushButton, QFrame,
    QScrollArea, QGroupBox, QSplitter, QTabWidget,
    QMessageBox, QProgressBar, QStatusBar, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QIcon

# Ajouter le chemin pour les imports de l'app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from app.config import APP_NAME, APP_VERSION, LOG_LEVEL
    from app.config import app_config, Language
    from app.core.services.kpi_service import KPIService
    from app.utils.logging_config import setup_logging
except ImportError as e:
    print(f"Erreur d'import dans BaseKPIDialog: {e}")
    APP_NAME = "GMAO Industrielle"
    APP_VERSION = "1.0"
    LOG_LEVEL = "INFO"
    KPIService = None

import logging
logger = logging.getLogger(__name__)

# === TRADUCTIONS PARTAGÉES ===
SHARED_TRANSLATIONS = {
    Language.FRENCH: {
        "close": "❌ Fermer",
        "refresh": "🔄 Actualiser",
        "export": "📊 Exporter",
        "loading": "Chargement en cours...",
        "no_data": "Aucune donnée disponible pour cette période",
        "error": "Erreur",
        "success": "Succès",
        "from": "Du:",
        "to": "Au:",
        "period": "Période",
        "analysis_period": "Période d'Analyse",
        "filters": "Filtres"
    },
    Language.ENGLISH: {
        "close": "❌ Close",
        "refresh": "🔄 Refresh",
        "export": "📊 Export",
        "loading": "Loading...",
        "no_data": "No data available for this period",
        "error": "Error",
        "success": "Success",
        "from": "From:",
        "to": "To:",
        "period": "Period",
        "analysis_period": "Analysis Period",
        "filters": "Filters"
    },
    Language.GERMAN: {
        "close": "❌ Schließen",
        "refresh": "🔄 Aktualisieren",
        "export": "📊 Exportieren",
        "loading": "Wird geladen...",
        "no_data": "Keine Daten für diesen Zeitraum verfügbar",
        "error": "Fehler",
        "success": "Erfolg",
        "from": "Von:",
        "to": "Bis:",
        "period": "Zeitraum",
        "analysis_period": "Analysezeitraum",
        "filters": "Filter"
    }
}

def get_shared_text(key: str) -> str:
    """Récupère le texte traduit selon la langue configurée."""
    try:
        current_lang = app_config.language if 'app_config' in globals() else Language.FRENCH
        return SHARED_TRANSLATIONS.get(current_lang, SHARED_TRANSLATIONS[Language.FRENCH]).get(key, key)
    except:
        return SHARED_TRANSLATIONS[Language.FRENCH].get(key, key)


class BaseKPIDialog(QDialog):
    """
    Classe de base pour tous les dialogs KPI spécialisés.
    
    Fournit:
    - Structure UI commune (barre d'outils, zone de contenu, barre de statut)
    - Gestion des dates
    - Méthodes d'export et de rafraîchissement
    - Raccourcis clavier standards
    - Système de traduction
    """
    
    def __init__(self, parent=None, title="KPI Analysis"):
        super().__init__(parent)
        self.kpi_service = None
        self.current_data = {}
        self.start_date = date.today() - timedelta(days=90)
        self.end_date = date.today()
        
        # Configuration de base
        self.setWindowTitle(f"{title} - {APP_NAME}")
        self.setMinimumSize(1000, 700)
        self.setModal(True)
        
        # Configuration du logging
        if setup_logging:
            setup_logging()
        
        # Initialisation
        self.setup_ui()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Chargement initial des données
        QTimer.singleShot(100, self.load_initial_data)
    
    def setup_ui(self):
        """Configure l'interface utilisateur de base."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # === BARRE D'OUTILS ===
        self.create_toolbar(main_layout)
        
        # === ZONE DE CONTENU PRINCIPALE ===
        self.create_content_area(main_layout)
        
        # === BARRE DE STATUT ===
        self.create_status_bar(main_layout)
    
    def create_toolbar(self, parent_layout):
        """Crée la barre d'outils commune."""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.StyledPanel)
        toolbar_frame.setStyleSheet("QFrame { background-color: #F8F9FA; }")
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # === SÉLECTION DE PÉRIODE ===
        period_group = QGroupBox(get_shared_text("analysis_period"))
        period_layout = QHBoxLayout(period_group)
        
        period_layout.addWidget(QLabel(get_shared_text("from")))
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate.fromString(self.start_date.isoformat(), "yyyy-MM-dd"))
        self.date_debut.setCalendarPopup(True)
        period_layout.addWidget(self.date_debut)
        
        period_layout.addWidget(QLabel(get_shared_text("to")))
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.fromString(self.end_date.isoformat(), "yyyy-MM-dd"))
        self.date_fin.setCalendarPopup(True)
        period_layout.addWidget(self.date_fin)
        
        toolbar_layout.addWidget(period_group)
        
        # === FILTRES SPÉCIFIQUES (à implémenter par les sous-classes) ===
        self.add_specific_filters(toolbar_layout)
        
        # === BOUTONS D'ACTIONS ===
        toolbar_layout.addStretch()
        
        btn_refresh = QPushButton(get_shared_text("refresh"))
        btn_refresh.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(btn_refresh)
        
        btn_export = QPushButton(get_shared_text("export"))
        btn_export.clicked.connect(self.export_data)
        toolbar_layout.addWidget(btn_export)
        
        btn_close = QPushButton(get_shared_text("close"))
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        btn_close.clicked.connect(self.close)
        toolbar_layout.addWidget(btn_close)
        
        parent_layout.addWidget(toolbar_frame)
        self.toolbar = toolbar_frame
    
    def create_content_area(self, parent_layout):
        """Crée la zone de contenu principal."""
        # Scroll area pour le contenu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { background-color: #FFFFFF; border: 1px solid #E0E0E0; }")
        
        # Widget de contenu
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        # Appel de la méthode abstraite pour créer le contenu spécifique
        self.create_specific_content()
        
        scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(scroll_area)
        self.scroll_area = scroll_area
    
    def create_status_bar(self, parent_layout):
        """Crée la barre de statut."""
        status_frame = QFrame()
        status_frame.setMaximumHeight(30)
        status_frame.setStyleSheet("QFrame { background-color: #F8F9FA; border-top: 1px solid #E0E0E0; }")
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Prêt")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Indicateur de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(status_frame)
        self.status_frame = status_frame
    
    def setup_shortcuts(self):
        """Configure les raccourcis clavier."""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Escape pour fermer
        escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        escape_shortcut.activated.connect(self.close)
        
        # Ctrl+W pour fermer
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close)
        
        # F5 pour actualiser
        refresh_shortcut = QShortcut(QKeySequence(Qt.Key_F5), self)
        refresh_shortcut.activated.connect(self.refresh_data)
    
    def setup_connections(self):
        """Configure les connexions de signaux."""
        self.date_debut.dateChanged.connect(self.on_date_changed)
        self.date_fin.dateChanged.connect(self.on_date_changed)
    
    # === MÉTHODES À SURCHARGER ===
    
    def create_specific_content(self):
        """Crée le contenu spécifique au dialog. À surcharger par les sous-classes."""
        placeholder = QLabel("Contenu spécifique non implémenté")
        placeholder.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(placeholder)
    
    def load_data(self):
        """Charge les données spécifiques. À surcharger par les sous-classes."""
        self.set_status("Chargement des données...", success=True)
    
    def add_specific_filters(self, toolbar_layout):
        """Ajoute des filtres spécifiques. Peut être surchargée par les sous-classes."""
        pass
    
    # === MÉTHODES COMMUNES ===
    
    def set_date_range(self, start_date: date, end_date: date):
        """Définit la plage de dates."""
        self.start_date = start_date
        self.end_date = end_date
        
        self.date_debut.setDate(QDate.fromString(start_date.isoformat(), "yyyy-MM-dd"))
        self.date_fin.setDate(QDate.fromString(end_date.isoformat(), "yyyy-MM-dd"))
    
    def get_date_range(self) -> tuple[date, date]:
        """Récupère la plage de dates actuelle."""
        start = self.date_debut.date().toPython()
        end = self.date_fin.date().toPython()
        return start, end
    
    def on_date_changed(self):
        """Gère le changement de dates."""
        logger.debug("Dates modifiées dans le dialog")
        # Auto-refresh après 1 seconde d'inactivité
        if hasattr(self, '_date_timer'):
            self._date_timer.stop()
        
        self._date_timer = QTimer()
        self._date_timer.setSingleShot(True)
        self._date_timer.timeout.connect(self.refresh_data)
        self._date_timer.start(1000)
    
    def load_initial_data(self):
        """Charge les données initiales."""
        logger.info(f"Chargement des données initiales pour {self.__class__.__name__}")
        self.load_data()
    
    def refresh_data(self):
        """Actualise les données."""
        logger.info(f"Actualisation des données pour {self.__class__.__name__}")
        self.show_loading(True)
        
        try:
            self.load_data()
            self.set_status("Données actualisées", success=True)
        except Exception as e:
            logger.error(f"Erreur lors de l'actualisation: {e}")
            self.set_status(f"Erreur: {e}", success=False)
        finally:
            self.show_loading(False)
    
    def export_data(self):
        """Exporte les données. À surcharger par les sous-classes."""
        QMessageBox.information(self, get_shared_text("success"), 
                              "Export non implémenté pour ce dialog")
    
    def show_loading(self, show: bool):
        """Affiche/masque l'indicateur de chargement."""
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Mode indéterminé
            self.set_status(get_shared_text("loading"))
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
    
    def set_status(self, message: str, success: bool = None):
        """Met à jour le message de statut."""
        if success is True:
            self.status_label.setStyleSheet("QLabel { color: #28a745; }")
        elif success is False:
            self.status_label.setStyleSheet("QLabel { color: #dc3545; }")
        else:
            self.status_label.setStyleSheet("QLabel { color: #6c757d; }")
        
        self.status_label.setText(message)
