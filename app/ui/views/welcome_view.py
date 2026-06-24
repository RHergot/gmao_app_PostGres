# gmao_app/app/ui/views/welcome_view.py
"""
Vue d'accueil avec KPIs et logo d'entreprise pour la GMAO.
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QTableView, QHeaderView, QPushButton, QFrame
from PySide6.QtCore import Qt
import os
from PySide6.QtGui import QPixmap, QFont, QStandardItemModel, QStandardItem

from app.access_control import MENU_RIGHTS, normalize_role, can_access
from app.ui.views.intervention_request_view import InterventionRequestView

# Dictionnaire de traduction des noms de menus (français -> anglais)
MENU_TRANSLATIONS = {
    "Gérer les Utilisateurs": "Manage Users",
    "Gérer les OTs": "Manage Work Orders",
    "Gérer les Pièces Détachées": "Manage Spare Parts",
    "Gérer les Machines": "Manage Machines",
    "Gérer le Stock": "Manage Inventory",
    "Gérer les Fournisseurs": "Manage Suppliers",
    "Configuration": "Configuration",
    "Gérer les Gammes d'Entretien": "Manage Maintenance Plans",
    "Gérer Commandes": "Manage Orders",
}

class WelcomeView(QWidget):
    def __init__(self, parent=None, maintenance_service=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.kpi_value_labels = {}
        
        # Déterminer la langue de l'application
        self.app_language = "fr"  # Valeur par défaut
        if parent and hasattr(parent, 'app_language'):
            self.app_language = parent.app_language
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        # Récupérer le nombre d'OT ouverts via le service (si dispo)
        ot_ouverts = None
        if hasattr(self, 'maintenance_service') and self.maintenance_service:
            try:
                ot_ouverts = self.maintenance_service.get_open_ots_count()
            except Exception as e:
                ot_ouverts = '?'
        else:
            ot_ouverts = '?'

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), '../../assets/company_logo.png')
        logo_path = os.path.abspath(logo_path)
        logo_label = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaledToWidth(220, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            logo_label.setText(self.tr("[Logo entreprise]"))
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("font-size: 20px; color: #888;")
        layout.addWidget(logo_label)

        # Titre
        title = QLabel(self.tr("Bienvenue sur votre GMAO !"))
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --- Affichage du nom de la base de données ---
        # Recherche la chaîne de connexion (d'abord sur self, sinon parent)
        conn_str = getattr(self, 'db_connection_str', None)
        if not conn_str:
            parent = self.parent()
            if parent and hasattr(parent, 'db_connection_str'):
                conn_str = getattr(parent, 'db_connection_str', None)
        db_name = None
        if conn_str and '://' in conn_str and not conn_str.endswith('/dbname'):
            db_name = conn_str.rsplit('/', 1)[-1].split('?')[0]
        db_label = QLabel(self.tr("<b>Base de données :</b> %1").replace("%1", db_name if db_name else "[non renseignée]"))
        db_label.setAlignment(Qt.AlignCenter)
        db_label.setStyleSheet("font-size: 15px; color: #444; margin-bottom: 8px;")
        layout.addWidget(db_label)

        # --- Infos utilisateur connecté ---
        user_login = None
        user_role = None
        accessible_menus = []
        parent = self.parent()
        if parent and hasattr(parent, 'current_user'):
            user_login = getattr(parent.current_user, 'login', None)
            user_role = getattr(parent.current_user, 'role', None)
            role_norm = normalize_role(user_role)
            # Liste des menus accessibles
            accessible_menus = [menu for menu in MENU_RIGHTS.keys() if can_access(menu, role_norm)]
        else:
            user_login = "?"
            user_role = "?"
            accessible_menus = []
        user_info = QLabel(self.tr("<b>Login :</b> %1   |   <b>Rôle :</b> %2").replace("%1", str(user_login)).replace("%2", str(user_role)))
        user_info.setAlignment(Qt.AlignCenter)
        user_info.setStyleSheet("font-size: 16px; margin: 12px 0 4px 0;")
        layout.addWidget(user_info)
        # --- Section principale sous le bandeau ---
        main_section = QHBoxLayout()
        layout.addLayout(main_section)

        self.btn_intervention_request = QPushButton(self.tr("Demande d’intervention"))
        self.btn_intervention_request.setStyleSheet("font-size: 22px; padding: 16px; background-color: orange;")
        self.btn_intervention_request.clicked.connect(self.open_intervention_request)
        layout.addWidget(self.btn_intervention_request)

        # --- Tableaux côte à côte dans une box de largeur 2/3 ---
        tables_box = QFrame()
        tables_box.setStyleSheet("background: #f9f9f9; border-radius: 8px; padding: 24px 32px 24px 32px;")
        tables_box_layout = QHBoxLayout(tables_box)
        tables_box_layout.setSpacing(24)
        # --- Gestion des Accès ---
        menus_title = QLabel(self.tr("Gestion des Accès"))
        menus_title.setAlignment(Qt.AlignCenter)
        menus_title.setFont(QFont("Arial", 12, QFont.Bold))
        access_layout = QVBoxLayout()
        access_layout.addWidget(menus_title)
        access_table = QTableView()
        access_model = QStandardItemModel(len(MENU_RIGHTS), 3)
        access_model.setHorizontalHeaderLabels([self.tr("Menus"), self.tr("Utilisateur"), self.tr("Permission")])
        role_norm = normalize_role(user_role) if user_role else None
        for i, menu in enumerate(MENU_RIGHTS.keys()):
            # N'utiliser les traductions que si la langue est l'anglais
            if hasattr(self, 'app_language') and self.app_language == "en":
                # Traduire le nom du menu si une traduction existe, sinon utiliser self.tr() directement
                menu_text = MENU_TRANSLATIONS.get(menu, menu)
                yes_text = "Yes"
                no_text = "No"
            else:
                # Garder le nom du menu en français
                menu_text = menu
                yes_text = "Oui"
                no_text = "Non"
                
            # Appliquer self.tr() pour permettre la traduction par Qt
            menu_display = self.tr(menu_text)
            access_model.setItem(i, 0, QStandardItem(menu_display))
            access_model.setItem(i, 1, QStandardItem(str(role_norm)))
            status = can_access(menu, role_norm)
            access_model.setItem(i, 2, QStandardItem(self.tr(f"✅ {yes_text}") if status else self.tr(f"❌ {no_text}")))
        access_table.setModel(access_model)
        access_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        access_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        access_table.setStyleSheet("QHeaderView::section { background-color: #ddd; }")
        access_table.setEditTriggers(QTableView.NoEditTriggers)
        access_table.setMinimumWidth(340)
        access_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        access_layout.addWidget(access_table)
        access_widget = QWidget()
        access_widget.setLayout(access_layout)
        tables_box_layout.addWidget(access_widget, 1)

        # --- Coûts des Interventions ---
        costs_title = QLabel(self.tr("Les Coûts de Interventions"))
        costs_title.setAlignment(Qt.AlignCenter)
        costs_title.setFont(QFont("Arial", 12, QFont.Bold))
        costs_layout = QVBoxLayout()
        costs_layout.addWidget(costs_title)
        try:
            monthly_data = self.maintenance_service.get_monthly_completed_costs_and_counts()
        except Exception:
            monthly_data = []
        costs_table = QTableView()
        costs_table.setObjectName("costs_table")  # Donner un nom d'objet pour le retrouver facilement
        
        # Créer un modèle pour le tableau des coûts
        costs_model = QStandardItemModel(0, 3)  # Commencer avec 0 lignes
        costs_model.setHorizontalHeaderLabels([self.tr("Mois"), self.tr("Coût"), self.tr("Interventions")])
        
        # Ajouter les données si disponibles
        if monthly_data:
            for i, row in enumerate(monthly_data):
                costs_model.insertRow(i)
                costs_model.setItem(i, 0, QStandardItem(row.get('month', '')))
                costs_model.setItem(i, 1, QStandardItem(f"{row.get('cost', 0):.2f}"))
                costs_model.setItem(i, 2, QStandardItem(str(row.get('count', 0))))
        else:
            # Ajouter une ligne vide si aucune donnée n'est disponible
            costs_model.insertRow(0)
            costs_model.setItem(0, 0, QStandardItem(self.tr("Aucune donnée")))
            costs_model.setItem(0, 1, QStandardItem("0.00"))
            costs_model.setItem(0, 2, QStandardItem("0"))
            
        costs_table.setModel(costs_model)
        costs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        costs_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        costs_table.setStyleSheet("QHeaderView::section { background-color: #ddd; }")
        costs_table.setEditTriggers(QTableView.NoEditTriggers)
        costs_table.setMinimumWidth(260)
        costs_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        costs_layout.addWidget(costs_table)
        costs_widget = QWidget()
        costs_widget.setLayout(costs_layout)
        tables_box_layout.addWidget(costs_widget, 1)
        main_section.addWidget(tables_box, 5)

        # --- KPIs à droite (vertical) ---
        kpi_frame = QFrame()
        kpi_frame.setStyleSheet("background: #f5f5f5; border-radius: 8px; padding: 20px;")
        kpi_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        kpi_vlayout = QVBoxLayout(kpi_frame)
        kpi_vlayout.setSpacing(32)
        kpi_vlayout.setAlignment(Qt.AlignTop)
        maintenances_en_cours = None
        if hasattr(self, 'maintenance_service') and self.maintenance_service:
            try:
                maintenances_en_cours = self.maintenance_service.get_in_progress_ots_count()
            except Exception:
                maintenances_en_cours = '?'
        else:
            maintenances_en_cours = '?'
        kpis = [
            (self.tr("OT ouverts"), str(ot_ouverts)),
            (self.tr("OT en cours"), str(maintenances_en_cours)),
        ]
        for label, value in kpis:
            box = QVBoxLayout()
            kpi_value = QLabel(value)
            self.kpi_value_labels[label] = kpi_value
            kpi_value.setFont(QFont("Arial", 24, QFont.Bold))
            kpi_value.setStyleSheet("color: #006400;")
            kpi_label = QLabel(label)
            kpi_label.setFont(QFont("Arial", 12))
            kpi_label.setStyleSheet("color: #555;")
            box.addWidget(kpi_value, alignment=Qt.AlignCenter)
            box.addWidget(kpi_label, alignment=Qt.AlignCenter)
            kpi_vlayout.addLayout(box)
        main_section.addWidget(kpi_frame, 1)

        # Footer
        footer = QLabel(self.tr("© 2025 Votre Entreprise - GMAO"))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("margin-top: 40px; color: #999;")
        layout.addWidget(footer)

    def refresh_data(self):
        """Rafraîchit les données de la vue d'accueil."""
        if hasattr(self, 'maintenance_service') and self.maintenance_service:
            # Mise à jour des KPIs
            try:
                ot_ouverts = self.maintenance_service.get_open_ots_count()
            except Exception as e:
                print(f"Erreur lors de la récupération des OT ouverts: {e}")
                ot_ouverts = '?'
            try:
                maintenances_en_cours = self.maintenance_service.get_in_progress_ots_count()
            except Exception as e:
                print(f"Erreur lors de la récupération des OT en cours: {e}")
                maintenances_en_cours = '?'
                
            # Mise à jour du tableau des coûts
            try:
                # Récupérer les données de coûts mensuels
                monthly_data = self.maintenance_service.get_monthly_completed_costs_and_counts()
                print(f"Données mensuelles récupérées: {len(monthly_data)} mois")
                
                # Trouver le tableau des coûts
                costs_table = None
                for child in self.findChildren(QTableView):
                    if child.objectName() == "costs_table" or (hasattr(child, 'model') and 
                                                          child.model() and 
                                                          child.model().columnCount() == 3 and
                                                          child.model().rowCount() > 0):
                        costs_table = child
                        break
                
                # Mettre à jour le tableau si trouvé
                if costs_table and costs_table.model():
                    model = costs_table.model()
                    # Effacer les données existantes
                    model.removeRows(0, model.rowCount())
                    
                    # Ajouter les nouvelles données
                    for i, row in enumerate(monthly_data):
                        model.insertRow(i)
                        model.setItem(i, 0, QStandardItem(row['month']))
                        model.setItem(i, 1, QStandardItem(f"{row['cost']:.2f}"))
                        model.setItem(i, 2, QStandardItem(str(row['count'])))
                        
                    # Mettre à jour les en-têtes en fonction de la langue
                    if hasattr(self, 'app_language') and self.app_language == "en":
                        model.setHorizontalHeaderLabels([self.tr("Month"), self.tr("Cost"), self.tr("Interventions")])
                    else:
                        model.setHorizontalHeaderLabels([self.tr("Mois"), self.tr("Coût"), self.tr("Interventions")])
                    
                    print(f"Tableau des coûts mis à jour avec {len(monthly_data)} lignes")
            except Exception as e:
                print(f"Erreur lors de la mise à jour du tableau des coûts: {e}")
        else:
            ot_ouverts = '?'
            maintenances_en_cours = '?'
            
        # Mise à jour des labels KPI
        label_ot = self.kpi_value_labels.get(self.tr("OT ouverts"))
        if label_ot:
            label_ot.setText(str(ot_ouverts))
        label_maint = self.kpi_value_labels.get(self.tr("OT en cours"))
        if label_maint:
            label_maint.setText(str(maintenances_en_cours))

        # --- Bouton de demande d'intervention ---
    def open_intervention_request(self):
        # Récupérer la vraie liste des machines depuis le service
        print("[DEBUG] open_intervention_request called. self:", self)
        machine_list = []
        machine_id_map = {}
        mainwin = self.parent()
        # Remonter la hiérarchie si besoin
        if not hasattr(mainwin, 'machine_service') and hasattr(mainwin, 'parent'):
            mainwin = mainwin.parent()
        print("[DEBUG] mainwin:", mainwin)
        if hasattr(mainwin, 'machine_service'):
            try:
                machines = mainwin.machine_service.get_all_machines()
                print(f"[DEBUG] Machines récupérées: {machines}")
                for m in machines:
                    machine_list.append(m.nom)
                    machine_id_map[m.nom] = m.id_machine
            except Exception as e:
                print(f"Erreur lors de la récupération des machines: {e}")
        else:
            print("[DEBUG] machine_service non trouvé dans la hiérarchie des parents.")
            machine_list = ["Aucune machine disponible"]
            machine_id_map = {}

        # Passer aussi l'utilisateur courant
        current_user = getattr(mainwin, 'current_user', None)
        print("[DEBUG] current_user:", current_user)
        # --- DEBUG: Test direct traduction Qt pour "Demande d’intervention" ---
        from PySide6.QtCore import QCoreApplication
        print("[DEBUG][i18n] QCoreApplication.translate(InterventionRequestView, 'Demande d’intervention'):", QCoreApplication.translate("InterventionRequestView", "Demande d’intervention"))
        print("[DEBUG][i18n] self.tr('Demande d’intervention'):", self.tr("Demande d’intervention"))

        dialog = InterventionRequestView(machine_list=machine_list, machine_id_map=machine_id_map, current_user=current_user, parent=self)
        dialog.exec()
      
        