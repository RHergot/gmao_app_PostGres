#!/usr/bin/env python3
"""
Démonstration des dialogs KPI modularisés.
Script pour tester la nouvelle architecture modulaire.
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin racine au sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class KPIDialogDemo(QMainWindow):
    """Fenêtre de démonstration des dialogs KPI."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Démonstration KPI Dialogs Modularisés")
        self.setGeometry(100, 100, 500, 700)
        
        # Widget central
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("📊 Architecture KPI Modularisée")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2C3E50; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Description
        description = QLabel("""
🎯 <b>Objectif :</b> Réduire la surcharge cognitive en séparant chaque analyse dans sa propre fenêtre modale.

✨ <b>Avantages :</b>
• Focus sur un aspect spécifique
• Navigation plus intuitive
• Interface moins encombrée
• Code plus modulaire et maintenable

🔧 <b>Architecture :</b>
• Dashboard principal : Vue d'ensemble uniquement
• Dialogs spécialisés : Analyses détaillées
• Classe de base commune : Fonctionnalités partagées
        """)
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                padding: 15px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                color: #495057;
            }
        """)
        layout.addWidget(description)
        
        # Boutons de test
        self.create_demo_buttons(layout)
        
        self.setCentralWidget(central_widget)
    
    def create_demo_buttons(self, layout):
        """Crée les boutons de démonstration."""
        
        # Style commun pour les boutons
        button_style = """
            QPushButton {
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                text-align: left;
                min-height: 20px;
            }
            QPushButton:hover {
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """
        
        # Boutons pour chaque dialog
        buttons_config = [
            {
                "text": "📊 Dashboard Principal (Vue d'Ensemble)",
                "callback": self.test_dashboard,
                "color": "#3498DB",
                "hover_color": "#2980B9",
                "description": "Modal principal avec résumé global et navigation"
            },
            {
                "text": "🏭 Analyse par Machine",
                "callback": self.test_machine_dialog,
                "color": "#E74C3C",
                "hover_color": "#C0392B",
                "description": "KPI détaillés par machine avec filtres avancés"
            },
            {
                "text": "🏢 Analyse par Site",
                "callback": self.test_site_dialog,
                "color": "#F39C12",
                "hover_color": "#E67E22",
                "description": "Comparaison des performances entre sites"
            },
            {
                "text": "👥 Analyse par Équipe",
                "callback": self.test_team_dialog,
                "color": "#9B59B6",
                "hover_color": "#8E44AD",
                "description": "Performance et charge de travail des équipes"
            },
            {
                "text": "🔧 Préventif vs Curatif",
                "callback": self.test_preventive_dialog,
                "color": "#1ABC9C",
                "hover_color": "#16A085",
                "description": "Comparaison coûts/efficacité préventif/curatif"
            },
            {
                "text": "🔬 Analyse Avancée",
                "callback": self.test_advanced_dialog,
                "color": "#34495E",
                "hover_color": "#2C3E50",
                "description": "Statistiques avancées et prédictions"
            }
        ]
        
        for config in buttons_config:
            # Container pour le bouton et la description
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(5)
            container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Bouton principal
            btn = QPushButton(config["text"])
            btn.clicked.connect(config["callback"])
            btn.setStyleSheet(f"""
                {button_style}
                QPushButton {{
                    background-color: {config["color"]};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: {config["hover_color"]};
                }}
            """)
            
            # Description
            desc_label = QLabel(config["description"])
            desc_label.setStyleSheet("""
                QLabel {
                    color: #6C757D;
                    font-size: 12px;
                    font-style: italic;
                    margin-left: 10px;
                }
            """)
            
            container_layout.addWidget(btn)
            container_layout.addWidget(desc_label)
            layout.addWidget(container)
    
    def test_dashboard(self):
        """Test du dashboard principal."""
        try:
            from app.ui.kpi.kpi_dashboard_clean import KPIDashboard
            dialog = KPIDashboard(parent=self)
            dialog.exec()
        except Exception as e:
            self.show_error("Dashboard Principal", str(e))
    
    def test_machine_dialog(self):
        """Test du dialog machine."""
        try:
            from app.ui.kpi.dialogs.machine_kpi_dialog import MachineKPIDialog
            dialog = MachineKPIDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.show_error("Dialog Machine", str(e))
    
    def test_site_dialog(self):
        """Test du dialog site."""
        try:
            from app.ui.kpi.dialogs.site_kpi_dialog import SiteKPIDialog
            dialog = SiteKPIDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.show_error("Dialog Site", str(e))
    
    def test_team_dialog(self):
        """Test du dialog équipe."""
        try:
            from app.ui.kpi.dialogs.team_kpi_dialog import TeamKPIDialog
            dialog = TeamKPIDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.show_error("Dialog Équipe", str(e))
    
    def test_preventive_dialog(self):
        """Test du dialog préventif."""
        try:
            from app.ui.kpi.dialogs.preventive_kpi_dialog import PreventiveKPIDialog
            dialog = PreventiveKPIDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.show_error("Dialog Préventif", str(e))
    
    def test_advanced_dialog(self):
        """Test du dialog avancé."""
        try:
            from app.ui.kpi.dialogs.advanced_kpi_dialog import AdvancedKPIDialog
            dialog = AdvancedKPIDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.show_error("Dialog Avancé", str(e))
    
    def show_error(self, dialog_name, error_message):
        """Affiche une erreur de façon conviviale."""
        QMessageBox.warning(
            self, 
            f"Erreur - {dialog_name}",
            f"Une erreur est survenue lors du test de {dialog_name}:\n\n{error_message}\n\nCela peut être normal si certaines dépendances ne sont pas encore disponibles."
        )

def main():
    """Lance la démonstration."""
    app = QApplication(sys.argv)
    
    # Configuration de l'application
    app.setApplicationName("KPI Dialogs Demo")
    app.setApplicationVersion("1.0")
    
    # Fenêtre principale
    demo = KPIDialogDemo()
    demo.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
