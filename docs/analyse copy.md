# Analyse du projet GMAO - Version mise à jour 2025

## Vue d'ensemble
**Application GMAO Industrielle** - Système complet de Gestion de Maintenance Assistée par Ordinateur avec **KPI financiers intégrés**.

## 🏆 Fonctionnalités principales
- ✅ Gestion complète du parc machines
- ✅ Maintenance curative et préventive
- ✅ Gestion des stocks et achats
- ✅ **Système KPI financier complet** (nouveau)
- ✅ Dashboard KPI avec données temps réel (nouveau)
- ✅ Interface multilingue (FR/EN/DE)
- ✅ Connexion PostgreSQL optimisée

## Structure complète du projet
```
📁 gmao_app_PostGres/                 # 🏠 RACINE DU PROJET
├── 📁 .git/                          # Git repository
├── 📁 .vscode/                       # Configuration VS Code
├── 📁 .qodo/                         # Configuration Qodo
├── 📁 __pycache__/                   # Cache Python racine
├── 📄 .env                           # Variables d'environnement
├── 📄 .gitignore                     # Exclusions Git
├── 📄 .windsurfrules                 # Règles Windsurf
├── 📄 analyse.md                     # 📊 CE DOCUMENT
├── 📄 accueil.py                     # 🏠 Interface d'accueil alternative
├── 📄 commandes.md                   # 📝 Commandes utiles
├── 📄 procedure Git.md               # 📝 Procédures Git
├── 📄 plan_api_mobile.md             # 📱 Plan API mobile
├── 📄 plan_kpi_finance_ia.md         # 🤖 Plan KPI IA
├── 📄 plan_phase_1_4_ui.md          # 🎨 Plan interface UI
├── 📄 PHASE_1_4_INTERFACE_KPI_COMPLETE.md # 📋 Phase KPI complète
├── 📄 audit_donnees_financieres_kpi.md # 💰 Audit données KPI
├── 📄 statut_kpi_financier.md        # 📊 Statut KPI financier
├── 📄 sql_vues_kpi_financiers.sql    # 🗄️ Vues PostgreSQL KPI
├── 🧪 test_*.py                      # 🔬 TESTS GLOBAUX (voir détails)
├── 📄 rapport_final_kpi.py           # 📊 Rapport final KPI
│
├── 📁 app/                           # 🎯 APPLICATION PRINCIPALE
│   ├── 📁 __pycache__/               # Cache Python app
│   ├── 📁 .venv/                     # Environnement virtuel Python
│   ├── 📄 access_control.py          # 🔐 Contrôle d'accès
│   ├── 📄 clean_project.py           # 🧹 Nettoyage projet
│   ├── 📄 config.py                  # ⚙️ Configuration principale
│   ├── 📄 init_db.py                 # 🗄️ Initialisation base
│   ├── 📄 main.py                    # 🚀 Point d'entrée principal
│   ├── 📄 requirements.txt           # 📦 Dépendances Python
│   ├── 📄 README_KPI.md              # 📖 Documentation KPI
│   ├── 📄 sql_vues_kpi_financiers.sql # 🗄️ Vues SQL KPI
│   │
│   ├── 📁 assets/                    # 🎨 RESSOURCES VISUELLES
│   │   └── 📄 company_logo.png       # 🏢 Logo entreprise
│   │
│   ├── 📁 core/                      # 🧠 LOGIQUE MÉTIER
│   │   ├── 📁 __pycache__/           # Cache Python core
│   │   ├── 📁 logic/                 # 📐 Logique applicative
│   │   ├── 📁 models/                # 📊 MODÈLES DE DONNÉES
│   │   │   ├── 📄 commande.py        # 💰 Modèle commandes
│   │   │   ├── 📄 compteur.py        # 📊 Modèle compteurs
│   │   │   ├── 📄 equipe.py          # 👥 Modèle équipes
│   │   │   ├── 📄 fabricant.py       # 🏭 Modèle fabricants
│   │   │   ├── 📄 fournisseur.py     # 🤝 Modèle fournisseurs
│   │   │   ├── 📄 gamme_entretien.py # 🔧 Modèle gammes entretien
│   │   │   ├── 📄 gamme_etape.py     # 📋 Modèle étapes gamme
│   │   │   ├── 📄 gamme_piece_type.py # 🔩 Modèle pièces gamme
│   │   │   ├── 📄 historique_compteur.py # 📈 Historique compteurs
│   │   │   ├── 📄 intervention_piece.py # 🔧 Pièces interventions
│   │   │   ├── 📄 ligne_commande.py  # 📝 Lignes commandes
│   │   │   ├── 📄 machine.py         # 🏭 Modèle machines
│   │   │   ├── 📄 maintenance.py     # 🔧 Modèle maintenance
│   │   │   ├── 📄 maintenance_frais_externe.py # 💸 Frais externes
│   │   │   ├── 📄 maintenance_intervenant.py # 👷 Intervenants
│   │   │   ├── 📄 mouvement_stock.py # 📦 Mouvements stock
│   │   │   ├── 📄 ordre_travail.py   # 📋 Ordres de travail
│   │   │   ├── 📄 piece.py           # 🔩 Modèle pièces
│   │   │   ├── 📄 site.py            # 🏢 Modèle sites
│   │   │   ├── 📄 technicien.py      # 👷 Modèle techniciens
│   │   │   ├── 📄 type_machine.py    # 🏭 Types machines
│   │   │   └── 📄 utilisateur.py     # 👤 Modèle utilisateurs
│   │   │
│   │   └── 📁 services/              # 🎛️ SERVICES MÉTIER
│   │       ├── 📁 __pycache__/       # Cache Python services
│   │       ├── 📄 achat_service.py   # 💰 Service achats
│   │       ├── 📄 compteur_service.py # 📊 Service compteurs
│   │       ├── 📄 finance_service.py # 💰 Service finances
│   │       ├── 📄 kpi_service.py     # 📊 🔥 SERVICE KPI PRINCIPAL
│   │       ├── 📄 machine_service.py # 🏭 Service machines
│   │       ├── 📄 maintenance_service.py # 🔧 Service maintenance
│   │       ├── 📄 preventive_service.py # 🛡️ Service préventif
│   │       ├── 📄 stock_service.py   # 📦 Service stock
│   │       └── 📄 user_service.py    # 👤 Service utilisateurs
│   │
│   ├── 📁 data/                      # 🗄️ ACCÈS DONNÉES
│   │   ├── 📁 __pycache__/           # Cache Python data
│   │   ├── 📄 database.py            # 🗄️ ⭐ Connexion DB + test_connection()
│   │   ├── 📄 schemas.py             # 📊 Schémas données
│   │   ├── 📄 schemas copy.py        # 📊 Sauvegarde schémas
│   │   │
│   │   └── 📁 repositories/          # 📚 référentiels de données
│   │       ├── 📁 __pycache__/       # Cache Python repositories
│   │       ├── 📄 commande_repository.py # 💰 Repo commandes
│   │       ├── 📄 compteur_repository.py # 📊 Repo compteurs
│   │       ├── 📄 equipe_repository.py # 👥 Repo équipes
│   │       ├── 📄 fabricant_repository.py # 🏭 Repo fabricants
│   │       ├── 📄 fournisseur_repository.py # 🤝 Repo fournisseurs
│   │       ├── 📄 gamme_entretien_repository.py # 🔧 Repo gammes
│   │       ├── 📄 gamme_etape_repository.py # 📋 Repo étapes
│   │       ├── 📄 gamme_piece_type_repository.py # 🔩 Repo pièces gamme
│   │       ├── 📄 historique_compteur_repository.py # 📈 Repo historique
│   │       ├── 📄 intervention_piece_repository.py # 🔧 Repo pièces intervention
│   │       ├── 📄 ligne_commande_repository.py # 📝 Repo lignes commande
│   │       ├── 📄 machine_repository.py # 🏭 Repo machines
│   │       ├── 📄 maintenance_frais_externe_repository.py # 💸 Repo frais
│   │       ├── 📄 maintenance_intervenant_repository.py # 👷 Repo intervenants
│   │       ├── 📄 maintenance_repository.py # 🔧 Repo maintenance
│   │       ├── 📄 mouvement_stock_repository.py # 📦 Repo mouvements
│   │       ├── 📄 ordre_travail_repository.py # 📋 Repo OT
│   │       ├── 📄 piece_repository.py # 🔩 Repo pièces
│   │       ├── 📄 site_repository.py # 🏢 Repo sites
│   │       ├── 📄 technicien_repository.py # 👷 Repo techniciens
│   │       ├── 📄 type_machine_repository.py # 🏭 Repo types machines
│   │       └── 📄 user_repository.py # 👤 Repo utilisateurs
│   │
│   ├── 📁 templates/                 # 📄 TEMPLATES DOCUMENTS
│   │   ├── 📄 commande_document_template.html # 💰 Template commandes
│   │   ├── 📄 maintenance_report_template.html # 🔧 Template maintenance
│   │   └── 📄 ot_document_template.html # 📋 Template OT
│   │
│   ├── 📁 ui/                        # 🎨 INTERFACE UTILISATEUR
│   │   ├── 📁 __pycache__/           # Cache Python UI
│   │   ├── 📄 main_window.py         # 🏠 ⭐ Fenêtre principale + KPI
│   │   │
│   │   ├── 📁 dialogs/               # 💬 BOÎTES DE DIALOGUE
│   │   │   ├── 📁 __pycache__/       # Cache Python dialogs
│   │   │   ├── 📄 commande_dialog.py # 💰 Dialog commandes
│   │   │   ├── 📄 compteur_dialog.py # 📊 Dialog compteurs
│   │   │   ├── 📄 db_connection_dialog.py # 🗄️ Dialog connexion DB
│   │   │   ├── 📄 equipe_dialog.py   # 👥 Dialog équipes
│   │   │   ├── 📄 fabricant_dialog.py # 🏭 Dialog fabricants
│   │   │   ├── 📄 fournisseur_dialog.py # 🤝 Dialog fournisseurs
│   │   │   ├── 📄 frais_externe_dialog.py # 💸 Dialog frais externes
│   │   │   ├── 📄 gamme_dialog.py    # 🔧 Dialog gammes
│   │   │   ├── 📄 gamme_etape_dialog.py # 📋 Dialog étapes gamme
│   │   │   ├── 📄 gamme_piece_dialog.py # 🔩 Dialog pièces gamme
│   │   │   ├── 📄 historique_compteur_dialog.py # 📈 Dialog historique
│   │   │   ├── 📄 historique_compteur_view.py # 📈 Vue historique
│   │   │   ├── 📄 intervenant_dialog.py # 👷 Dialog intervenants
│   │   │   ├── 📄 login_dialog.py    # 🔐 Dialog login
│   │   │   ├── 📄 machine_counters_dialog.py # 📊 Dialog compteurs machine
│   │   │   ├── 📄 machine_dialog.py  # 🏭 Dialog machines
│   │   │   ├── 📄 maintenance_detail_dialog.py # 🔧 Dialog détail maintenance
│   │   │   ├── 📄 maintenance_report_dialog.py # 📊 Dialog rapport maintenance
│   │   │   ├── 📄 ot_dialog.py       # 📋 Dialog ordres travail
│   │   │   ├── 📄 piece_dialog.py    # 🔩 Dialog pièces
│   │   │   ├── 📄 piece_reference_dialog.py # 🔍 Dialog référence pièce
│   │   │   ├── 📄 piece_selection_dialog.py # ✅ Dialog sélection pièce
│   │   │   ├── 📄 reception_dialog.py # 📦 Dialog réception
│   │   │   ├── 📄 site_dialog.py     # 🏢 Dialog sites
│   │   │   ├── 📄 stock_adjustment_dialog.py # 📦 Dialog ajustement stock
│   │   │   ├── 📄 technicien_dialog.py # 👷 Dialog techniciens
│   │   │   ├── 📄 type_machine_dialog.py # 🏭 Dialog types machines
│   │   │   └── 📄 user_dialog.py     # 👤 Dialog utilisateurs
│   │   │
│   │   ├── 📁 kpi/                   # 📊 🔥 SYSTÈME KPI COMPLET
│   │   │   ├── 📁 __pycache__/       # Cache Python KPI
│   │   │   ├── 📄 kpi_dashboard_clean.py # 🔥 DASHBOARD PRINCIPAL (OPÉRATIONNEL)
│   │   │   ├── 📄 demo_kpi_dialogs.py # 🎬 Démonstrations KPI
│   │   │   ├── 📄 kpi_dashboard.py   # 🔧 Version développement
│   │   │   ├── 📄 kpi_dashboard_backup.py # 💾 Sauvegarde dashboard
│   │   │   ├── 📄 kpi_dashboard_new.py # 🆕 Tests nouveaux
│   │   │   ├── 📄 test_integration.py # 🧪 Tests intégration
│   │   │   ├── 📄 test_kpi_dialogs.py # 🧪 Tests dialogs
│   │   │   ├── 📄 test_simple.py     # 🧪 Tests simples
│   │   │   │
│   │   │   ├── 📁 dialogs/           # 💬 ⭐ DIALOGS KPI SPÉCIALISÉS
│   │   │   │   ├── 📁 __pycache__/   # Cache Python dialogs KPI
│   │   │   │   ├── 📄 base_kpi_dialog.py # 🔥 Classe base commune
│   │   │   │   ├── 📄 machine_kpi_dialog.py # 🏭 Analyse par machine
│   │   │   │   ├── 📄 site_kpi_dialog.py # 🏢 Analyse par site
│   │   │   │   ├── 📄 team_kpi_dialog.py # 👥 Analyse par équipe
│   │   │   │   ├── 📄 preventive_kpi_dialog.py # 🛡️ Préventif vs curatif
│   │   │   │   └── 📄 advanced_kpi_dialog.py # 🎯 Analyses avancées
│   │   │   │
│   │   │   └── 📁 widgets/           # 🎛️ ⭐ WIDGETS KPI SPÉCIALISÉS
│   │   │       ├── 📁 __pycache__/   # Cache Python widgets KPI
│   │   │       ├── 📄 global_summary_widget.py # 🌍 Résumé global temps réel
│   │   │       ├── 📄 machine_kpi_widget.py # 🏭 Métriques machines
│   │   │       ├── 📄 site_kpi_widget.py # 🏢 Métriques sites
│   │   │       ├── 📄 equipe_kpi_widget.py # 👥 Métriques équipes
│   │   │       ├── 📄 preventif_curatif_widget.py # 🛡️ Comparaisons maintenance
│   │   │       └── 📄 advanced_kpi_widget.py # 🎯 Analyses complexes
│   │   │
│   │   ├── 📁 resources/             # 🎨 Ressources UI
│   │   │
│   │   ├── 📁 views/                 # 👁️ VUES PRINCIPALES
│   │   │   ├── 📁 __pycache__/       # Cache Python views
│   │   │   ├── 📄 commande_view.py   # 💰 Vue commandes
│   │   │   ├── 📄 equipe_view.py     # 👥 Vue équipes
│   │   │   ├── 📄 fabricant_view.py  # 🏭 Vue fabricants
│   │   │   ├── 📄 fournisseur_view.py # 🤝 Vue fournisseurs
│   │   │   ├── 📄 gamme_view.py      # 🔧 Vue gammes
│   │   │   ├── 📄 intervention_request_view.py # 🔧 Vue demandes intervention
│   │   │   ├── 📄 machine_view.py    # 🏭 Vue machines
│   │   │   ├── 📄 maintenance_detail_view.py # 🔧 Vue détail maintenance
│   │   │   ├── 📄 ot_view.py         # 📋 Vue ordres travail
│   │   │   ├── 📄 piece_view.py      # 🔩 Vue pièces
│   │   │   ├── 📄 site_view.py       # 🏢 Vue sites
│   │   │   ├── 📄 technicien_view.py # 👷 Vue techniciens
│   │   │   ├── 📄 type_machine_view.py # 🏭 Vue types machines
│   │   │   ├── 📄 user_view.py       # 👤 Vue utilisateurs
│   │   │   └── 📄 welcome_view.py    # 🏠 Vue accueil
│   │   │
│   │   └── 📁 widgets/               # 🎛️ WIDGETS MÉTIER
│   │       ├── 📁 __pycache__/       # Cache Python widgets
│   │       ├── 📄 finance_couts_widget.py # 💰 Widget coûts financiers
│   │       ├── 📄 maintenance_couts_widget.py # 🔧 Widget coûts maintenance
│   │       └── 📄 maintenance_pieces_widget.py # 🔩 Widget pièces maintenance
│   │
│   └── 📁 utils/                     # 🛠️ UTILITAIRES
│       ├── 📁 __pycache__/           # Cache Python utils
│       ├── 📄 pdf_maintenance.py     # � Génération PDF maintenance
│       └── 📄 pdf_ot.py              # 📄 Génération PDF OT
│
├── 📁 api_mobile/                    # 📱 API MOBILE DJANGO
│   ├── 📄 .flake8                    # Configuration linter
│   ├── 📄 README.md                  # Documentation API
│   ├── 📄 check_statuts.py           # Vérification statuts
│   ├── 📄 manage.py                  # Manager Django
│   ├── 📄 requirements.txt           # Dépendances API
│   ├── 📄 schemas.py                 # Schémas API
│   │
│   ├── 📁 gmao_api/                  # Configuration Django principale
│   │   ├── 📄 asgi.py                # Configuration ASGI
│   │   ├── 📄 settings.py            # Paramètres Django
│   │   ├── 📄 urls.py                # URLs principales
│   │   └── 📄 wsgi.py                # Configuration WSGI
│   │
│   ├── 📁 gmao_web/                  # Application web Django
│   │   ├── 📄 admin.py               # Interface admin
│   │   ├── 📄 apps.py                # Configuration app
│   │   ├── 📄 maintenance_serializers.py # Sérialiseurs maintenance
│   │   ├── 📄 serializers.py         # Sérialiseurs généraux
│   │   ├── 📄 tests.py               # Tests Django
│   │   ├── 📄 urls.py                # URLs app
│   │   └── 📄 views.py               # Vues Django
│   │
│   ├── 📁 mobile_api/                # API mobile spécialisée
│   │   ├── 📄 admin.py               # Interface admin mobile
│   │   ├── 📄 apps.py                # Configuration app mobile
│   │   ├── 📄 models.py              # Modèles mobile
│   │   ├── 📄 serializers.py         # Sérialiseurs mobile
│   │   ├── 📄 tests.py               # Tests mobile
│   │   ├── 📄 urls.py                # URLs mobile
│   │   └── 📄 views.py               # Vues mobile
│   │
│   ├── 📁 web_interface/             # Interface web
│   │   ├── 📄 admin.py               # Admin interface web
│   │   ├── 📄 apps.py                # Config interface web
│   │   ├── 📄 models.py              # Modèles interface web
│   │   ├── 📄 tests.py               # Tests interface web
│   │   └── 📄 views.py               # Vues interface web
│   │
│   └── 📁 web_ui/                    # Interface utilisateur web
│       ├── 📄 admin.py               # Admin UI web
│       ├── 📄 apps.py                # Config UI web
│       ├── 📄 models.py              # Modèles UI web
│       ├── 📄 tests.py               # Tests UI web
│       └── 📄 views.py               # Vues UI web
│
├── 📁 docs/                          # 📚 DOCUMENTATION
│   ├── 📄 DOCUMENTATION.md           # Documentation principale
│   ├── 📄 KPI_REFACTORING_SUMMARY.md # Résumé refactoring KPI
│   ├── 📄 OPTIMISATION_PERFORMANCE.md # Guide optimisation
│   ├── 📄 SYSTEME_LANGUE.md          # Système multilingue
│   ├── 📄 procedure_api_django.md    # Procédure API Django
│   ├── 📄 procedure_app_mobile.md    # Procédure app mobile
│   ├── 📄 procedure_app_mobile .txt  # Procédure app mobile (texte)
│   └── 📄 roadmap_technique.md       # Roadmap technique
│
├── 📁 en_translations/               # 🌍 TRADUCTIONS ANGLAISES
│   ├── 📄 en.ts/.qm                  # Fichier traduction principal
│   └── 📄 [module]_[type].ts/.qm     # Traductions par module (80+ fichiers)
│
├── 📁 scripts/                       # 🔧 SCRIPTS UTILITAIRES
│   ├── 📄 add_bulk_test_data.py      # Ajout données test en masse
│   ├── 📄 check_db_structure.py      # Vérification structure DB
│   ├── 📄 check_views.py             # Vérification vues SQL
│   ├── 📄 fix_sql_timestamps.py      # Correction timestamps SQL
│   ├── 📄 generate_simple_test_data.py # Génération données test simples
│   ├── 📄 generate_simple_test_data_add.py # Ajout données test
│   ├── 📄 generate_test_data.py      # Génération données test
│   ├── 📄 generate_test_data_schema.py # Génération schéma test
│   ├── 📄 init_db.py                 # Initialisation base données
│   ├── 📄 init_kpi_views.py          # Initialisation vues KPI
│   └── 📄 __init__.py                # Module scripts
│
├── 📁 tests/                         # 🧪 TESTS UNITAIRES
│   └── 📄 __init__.py                # Module tests
│
├── 📁 tools/                         # 🛠️ OUTILS DÉVELOPPEMENT
│   ├── 📄 accueil_back.py            # Sauvegarde accueil
│   ├── 📄 add_missing_column.py      # Ajout colonnes manquantes
│   ├── 📄 check_real_schema.py       # Vérification schéma réel
│   ├── 📄 check_table_structure.py   # Vérification structure tables
│   ├── 📄 check_type_mouvement.py    # Vérification types mouvement
│   ├── 📄 compile_translations.py    # Compilation traductions
│   ├── 📄 compile_ts.py              # Compilation TypeScript
│   ├── 📄 fix_model_imports.py       # Correction imports modèles
│   ├── 📄 fix_mouvement_stock.py     # Correction mouvements stock
│   ├── 📄 fix_sqlite_models.py       # Correction modèles SQLite
│   ├── 📄 fix_sqlite_models_improved.py # Correction modèles améliorée
│   ├── 📄 installation.md            # Guide installation
│   ├── 📄 main copy.py               # Copie main
│   ├── 📄 main_bu.py                 # Sauvegarde main
│   ├── 📄 menus_access_control.md    # Contrôle accès menus
│   ├── 📄 procedure_translation.md   # Procédure traduction
│   ├── 📄 simple_db_check.py         # Vérification DB simple
│   ├── 📄 simple_schema_check.py     # Vérification schéma simple
│   ├── 📄 start_wireguard.sh         # Script WireGuard
│   └── 📄 update_translations.py     # Mise à jour traductions
│
└── 🧪 TESTS GLOBAUX KPI              # 🔬 TESTS SYSTÈME KPI
    ├── 📄 test_final_integration.py  # Test intégration finale
    ├── 📄 test_integration_langue.py # Test intégration langue
    ├── 📄 test_kpi_dashboard_complete.py # 🔥 Test dashboard complet
    ├── 📄 test_kpi_final_integration.py # 🔥 Test intégration finale KPI
    ├── 📄 test_kpi_final_report.py   # Test rapport final KPI
    ├── 📄 test_kpi_final_validation.py # Test validation finale KPI
    ├── 📄 test_kpi_import.py          # Test imports KPI
    ├── 📄 test_kpi_service_integration.py # 🔥 Test service KPI
    ├── 📄 test_langue.py              # Test système langue
    ├── 📄 test_preventif_curatif.py   # Test préventif/curatif
    └── 📄 test_stock_fix.py           # Test correction stock
```

## 🔥 NOUVEAU - Système KPI Financier

### Service KPI (`/core/services/kpi_service.py`)
**Service central pour tous les calculs KPI financiers :**
- ✅ KPI par machine (coûts, interventions, tendances)
- ✅ KPI par site (agrégation géographique)
- ✅ KPI par équipe (performance MOD)
- ✅ Comparaisons préventif vs curatif
- ✅ Évolution temporelle et tendances
- ✅ Connexion PostgreSQL optimisée avec vues spécialisées

### Dashboard KPI (`/ui/kpi/kpi_dashboard_clean.py`)
**Interface principale du système KPI :**
- 📊 Vue d'ensemble temps réel
- 📅 Filtres temporels configurables
- 🎛️ Navigation vers analyses spécialisées
- 🌐 Support multilingue (FR/EN/DE)
- ⚡ Chargement de données réelles

### Dialogs spécialisés (`/ui/kpi/dialogs/`)
**Analyses détaillées par domaine :**
- `base_kpi_dialog.py` - Classe de base commune
- `machine_kpi_dialog.py` - Analyse par machine
- `site_kpi_dialog.py` - Analyse par site
- `team_kpi_dialog.py` - Analyse par équipe
- `preventive_kpi_dialog.py` - Préventif vs curatif
- `advanced_kpi_dialog.py` - Analyses avancées

### Widgets KPI (`/ui/kpi/widgets/`)
**Composants UI spécialisés :**
- `global_summary_widget.py` - Résumé global
- `machine_kpi_widget.py` - Métriques machines
- `site_kpi_widget.py` - Métriques sites
- `equipe_kpi_widget.py` - Métriques équipes
- `preventif_curatif_widget.py` - Comparaisons maintenance
- `advanced_kpi_widget.py` - Analyses complexes

## 📋 Description détaillée des fichiers

### 🏠 Fichiers racine du projet
- **analyse.md** - 📊 Documentation complète du projet (CE DOCUMENT)
- **accueil.py** - 🏠 Interface d'accueil alternative à main.py
- **commandes.md** - 📝 Liste des commandes utiles pour le développement
- **procedure Git.md** - 📝 Procédures et bonnes pratiques Git
- **plan_api_mobile.md** - 📱 Planification de l'API mobile Django
- **plan_kpi_finance_ia.md** - 🤖 Plan d'intégration IA pour les KPI financiers
- **plan_phase_1_4_ui.md** - 🎨 Plan de développement interface utilisateur
- **PHASE_1_4_INTERFACE_KPI_COMPLETE.md** - 📋 Documentation phase KPI complète
- **audit_donnees_financieres_kpi.md** - 💰 Audit des données financières KPI
- **statut_kpi_financier.md** - 📊 Statut actuel du système KPI financier
- **sql_vues_kpi_financiers.sql** - 🗄️ Vues PostgreSQL optimisées pour les KPI
- **rapport_final_kpi.py** - 📊 Script de génération du rapport final KPI

### 🧪 Tests globaux KPI (racine)
- **test_kpi_service_integration.py** - 🔥 Tests service KPI avec base de données réelle
- **test_kpi_dashboard_complete.py** - 🔥 Tests dashboard complet avec données temps réel
- **test_kpi_final_integration.py** - 🔥 Tests d'intégration finale du système KPI
- **test_final_integration.py** - 🧪 Tests généraux d'intégration
- **test_integration_langue.py** - 🌍 Tests du système multilingue
- **test_kpi_final_validation.py** - ✅ Validation finale du système KPI
- **test_kpi_final_report.py** - 📊 Tests du rapport final KPI
- **test_kpi_import.py** - 📦 Tests des imports KPI
- **test_langue.py** - 🌍 Tests du système de langues
- **test_preventif_curatif.py** - 🛡️ Tests comparaisons préventif/curatif
- **test_stock_fix.py** - 📦 Tests corrections stock

### 📁 /app - Application principale

#### Fichiers racine /app
- **access_control.py** - 🔐 Système de contrôle d'accès utilisateurs/rôles
- **clean_project.py** - 🧹 Script de nettoyage des fichiers temporaires
- **config.py** - ⚙️ Configuration principale (DB, chemins, constantes)
- **init_db.py** - 🗄️ Script d'initialisation de la base de données
- **main.py** - 🚀 Point d'entrée principal de l'application
- **requirements.txt** - 📦 Dépendances Python (PySide6, psycopg2, matplotlib, pandas, openpyxl)
- **README_KPI.md** - 📖 Documentation spécifique du système KPI
- **sql_vues_kpi_financiers.sql** - 🗄️ Vues PostgreSQL optimisées pour les KPI

#### 📁 /assets - Ressources visuelles
- **company_logo.png** - 🏢 Logo de l'entreprise pour l'interface

#### 📁 /core - Logique métier centrale

##### /core/logic
- Logique applicative métier (vide actuellement)

##### /core/models - Modèles de données
- **commande.py** - 💰 Modèle des commandes fournisseurs
- **compteur.py** - 📊 Modèle des compteurs machines (heures, cycles)
- **equipe.py** - 👥 Modèle des équipes de maintenance
- **fabricant.py** - 🏭 Modèle des fabricants de machines/pièces
- **fournisseur.py** - 🤝 Modèle des fournisseurs de pièces/services
- **gamme_entretien.py** - 🔧 Modèle des gammes d'entretien préventif
- **gamme_etape.py** - 📋 Modèle des étapes dans les gammes
- **gamme_piece_type.py** - 🔩 Modèle des types de pièces par gamme
- **historique_compteur.py** - 📈 Historique des relevés de compteurs
- **intervention_piece.py** - 🔧 Pièces utilisées lors des interventions
- **ligne_commande.py** - 📝 Lignes détail des commandes
- **machine.py** - 🏭 Modèle principal des machines industrielles
- **maintenance.py** - 🔧 Modèle des interventions de maintenance
- **maintenance_frais_externe.py** - 💸 Frais externes liés à la maintenance
- **maintenance_intervenant.py** - 👷 Intervenants participants aux maintenances
- **mouvement_stock.py** - 📦 Mouvements d'entrée/sortie de stock
- **ordre_travail.py** - 📋 Ordres de travail planifiés
- **piece.py** - 🔩 Modèle des pièces détachées
- **site.py** - 🏢 Modèle des sites industriels
- **technicien.py** - 👷 Modèle des techniciens de maintenance
- **type_machine.py** - 🏭 Types/catégories de machines
- **utilisateur.py** - 👤 Modèle des utilisateurs système

##### /core/services - Services métier
- **achat_service.py** - 💰 Service gestion des achats et commandes
- **compteur_service.py** - 📊 Service gestion des compteurs machines
- **finance_service.py** - 💰 Service calculs financiers généraux
- **kpi_service.py** - 📊 🔥 SERVICE KPI PRINCIPAL - Calculs financiers KPI
- **machine_service.py** - 🏭 Service gestion du parc machines
- **maintenance_service.py** - 🔧 Service gestion des maintenances
- **preventive_service.py** - 🛡️ Service maintenance préventive
- **stock_service.py** - 📦 Service gestion des stocks
- **user_service.py** - 👤 Service gestion des utilisateurs

#### 📁 /data - Accès aux données

##### Fichiers principaux /data
- **database.py** - 🗄️ ⭐ Gestionnaire connexions PostgreSQL + test_connection()
- **schemas.py** - 📊 Schémas de validation des données
- **schemas copy.py** - 📊 Sauvegarde des schémas

##### /data/repositories - Couche d'accès données (Pattern Repository)
- **commande_repository.py** - 💰 Repository des commandes
- **compteur_repository.py** - 📊 Repository des compteurs
- **equipe_repository.py** - 👥 Repository des équipes
- **fabricant_repository.py** - 🏭 Repository des fabricants
- **fournisseur_repository.py** - 🤝 Repository des fournisseurs
- **gamme_entretien_repository.py** - 🔧 Repository des gammes entretien
- **gamme_etape_repository.py** - 📋 Repository des étapes gamme
- **gamme_piece_type_repository.py** - 🔩 Repository des pièces gamme
- **historique_compteur_repository.py** - 📈 Repository historique compteurs
- **intervention_piece_repository.py** - 🔧 Repository pièces interventions
- **ligne_commande_repository.py** - 📝 Repository lignes commandes
- **machine_repository.py** - 🏭 Repository des machines
- **maintenance_frais_externe_repository.py** - 💸 Repository frais externes
- **maintenance_intervenant_repository.py** - 👷 Repository intervenants
- **maintenance_repository.py** - 🔧 Repository des maintenances
- **mouvement_stock_repository.py** - 📦 Repository mouvements stock
- **ordre_travail_repository.py** - 📋 Repository ordres de travail
- **piece_repository.py** - 🔩 Repository des pièces
- **site_repository.py** - 🏢 Repository des sites
- **technicien_repository.py** - 👷 Repository des techniciens
- **type_machine_repository.py** - 🏭 Repository types machines
- **user_repository.py** - 👤 Repository des utilisateurs

#### 📁 /templates - Templates de documents
- **commande_document_template.html** - 💰 Template PDF commandes
- **maintenance_report_template.html** - 🔧 Template rapport maintenance
- **ot_document_template.html** - 📋 Template ordres de travail

#### 📁 /ui - Interface utilisateur

##### Fichier principal /ui
- **main_window.py** - 🏠 ⭐ Fenêtre principale + intégration KPI dashboard

##### /ui/dialogs - Boîtes de dialogue
- **commande_dialog.py** - 💰 Dialog création/édition commandes
- **compteur_dialog.py** - 📊 Dialog saisie compteurs machines
- **db_connection_dialog.py** - 🗄️ Dialog configuration connexion DB
- **equipe_dialog.py** - 👥 Dialog gestion équipes
- **fabricant_dialog.py** - 🏭 Dialog gestion fabricants
- **fournisseur_dialog.py** - 🤝 Dialog gestion fournisseurs
- **frais_externe_dialog.py** - 💸 Dialog saisie frais externes
- **gamme_dialog.py** - 🔧 Dialog gestion gammes entretien
- **gamme_etape_dialog.py** - 📋 Dialog étapes des gammes
- **gamme_piece_dialog.py** - 🔩 Dialog pièces par gamme
- **historique_compteur_dialog.py** - 📈 Dialog historique compteurs
- **historique_compteur_view.py** - 📈 Vue historique compteurs
- **intervenant_dialog.py** - 👷 Dialog gestion intervenants
- **login_dialog.py** - 🔐 Dialog authentification
- **machine_counters_dialog.py** - 📊 Dialog compteurs par machine
- **machine_dialog.py** - 🏭 Dialog création/édition machines
- **maintenance_detail_dialog.py** - 🔧 Dialog détails maintenance
- **maintenance_report_dialog.py** - 📊 Dialog génération rapports
- **ot_dialog.py** - 📋 Dialog gestion ordres travail
- **piece_dialog.py** - 🔩 Dialog gestion pièces détachées
- **piece_reference_dialog.py** - 🔍 Dialog référence pièce
- **piece_selection_dialog.py** - ✅ Dialog sélection pièces
- **reception_dialog.py** - 📦 Dialog réception commandes
- **site_dialog.py** - 🏢 Dialog gestion sites
- **stock_adjustment_dialog.py** - 📦 Dialog ajustements stock
- **technicien_dialog.py** - 👷 Dialog gestion techniciens
- **type_machine_dialog.py** - 🏭 Dialog types de machines
- **user_dialog.py** - 👤 Dialog gestion utilisateurs

##### /ui/kpi 🔥 SYSTÈME KPI COMPLET

###### Fichiers principaux /ui/kpi
- **kpi_dashboard_clean.py** - 🔥 DASHBOARD KPI PRINCIPAL (OPÉRATIONNEL)
- **demo_kpi_dialogs.py** - 🎬 Démonstrations et tests KPI
- **kpi_dashboard.py** - 🔧 Version développement dashboard
- **kpi_dashboard_backup.py** - 💾 Sauvegarde dashboard
- **kpi_dashboard_new.py** - 🆕 Tests nouvelles fonctionnalités
- **test_integration.py** - 🧪 Tests d'intégration KPI
- **test_kpi_dialogs.py** - 🧪 Tests des dialogs KPI
- **test_simple.py** - 🧪 Tests simples KPI

###### /ui/kpi/dialogs ⭐ DIALOGS KPI SPÉCIALISÉS
- **base_kpi_dialog.py** - 🔥 Classe de base commune pour tous les dialogs KPI
- **machine_kpi_dialog.py** - 🏭 Dialog analyse KPI par machine
- **site_kpi_dialog.py** - 🏢 Dialog analyse KPI par site
- **team_kpi_dialog.py** - 👥 Dialog analyse KPI par équipe
- **preventive_kpi_dialog.py** - 🛡️ Dialog comparaison préventif vs curatif
- **advanced_kpi_dialog.py** - 🎯 Dialog analyses KPI avancées

###### /ui/kpi/widgets ⭐ WIDGETS KPI SPÉCIALISÉS
- **global_summary_widget.py** - 🌍 Widget résumé global temps réel
- **machine_kpi_widget.py** - 🏭 Widget métriques machines
- **site_kpi_widget.py** - 🏢 Widget métriques sites
- **equipe_kpi_widget.py** - 👥 Widget métriques équipes
- **preventif_curatif_widget.py** - 🛡️ Widget comparaisons maintenance
- **advanced_kpi_widget.py** - 🎯 Widget analyses complexes

##### /ui/resources
- Ressources UI (icônes, styles) - actuellement vide

##### /ui/views - Vues principales
- **commande_view.py** - 💰 Vue liste/gestion commandes
- **equipe_view.py** - 👥 Vue liste/gestion équipes
- **fabricant_view.py** - 🏭 Vue liste/gestion fabricants
- **fournisseur_view.py** - 🤝 Vue liste/gestion fournisseurs
- **gamme_view.py** - 🔧 Vue liste/gestion gammes
- **intervention_request_view.py** - 🔧 Vue demandes d'intervention
- **machine_view.py** - 🏭 Vue liste/gestion machines
- **maintenance_detail_view.py** - 🔧 Vue détails maintenance
- **ot_view.py** - 📋 Vue liste/gestion ordres travail
- **piece_view.py** - 🔩 Vue liste/gestion pièces
- **site_view.py** - 🏢 Vue liste/gestion sites
- **technicien_view.py** - 👷 Vue liste/gestion techniciens
- **type_machine_view.py** - 🏭 Vue liste/gestion types machines
- **user_view.py** - 👤 Vue liste/gestion utilisateurs
- **welcome_view.py** - 🏠 Vue page d'accueil

##### /ui/widgets - Widgets métier
- **finance_couts_widget.py** - 💰 Widget affichage coûts financiers
- **maintenance_couts_widget.py** - 🔧 Widget coûts maintenance
- **maintenance_pieces_widget.py** - 🔩 Widget pièces maintenance

#### 📁 /utils - Utilitaires
- **pdf_maintenance.py** - 📄 Génération de PDF pour la maintenance
- **pdf_ot.py** - 📄 Génération de PDF pour les ordres de travail

### 📁 /api_mobile - API Mobile Django

#### Configuration principale
- **.flake8** - Configuration du linter Python
- **README.md** - Documentation de l'API mobile
- **check_statuts.py** - Script de vérification des statuts
- **manage.py** - Gestionnaire Django standard
- **requirements.txt** - Dépendances Django/API
- **schemas.py** - Schémas de l'API mobile

#### /gmao_api - Configuration Django
- **asgi.py** - Configuration ASGI pour déploiement asynchrone
- **settings.py** - Configuration Django (base de données, apps, middleware)
- **urls.py** - Configuration des URLs principales
- **wsgi.py** - Configuration WSGI pour déploiement traditionnel

#### /gmao_web - Application web Django
- **admin.py** - Interface d'administration Django
- **apps.py** - Configuration de l'application Django
- **maintenance_serializers.py** - Sérialiseurs spécifiques maintenance
- **serializers.py** - Sérialiseurs généraux Django REST
- **tests.py** - Tests unitaires Django
- **urls.py** - URLs de l'application web
- **views.py** - Vues Django REST

#### /mobile_api - API mobile spécialisée
- **admin.py** - Administration interface mobile
- **apps.py** - Configuration app mobile
- **models.py** - Modèles spécifiques mobile
- **serializers.py** - Sérialiseurs mobile
- **tests.py** - Tests API mobile
- **urls.py** - URLs API mobile
- **views.py** - Vues API mobile

#### /web_interface & /web_ui - Interfaces web
- Structure Django standard pour interfaces web supplémentaires

### 📁 /docs - Documentation
- **DOCUMENTATION.md** - Documentation technique principale
- **KPI_REFACTORING_SUMMARY.md** - Résumé de la refactorisation KPI
- **OPTIMISATION_PERFORMANCE.md** - Guide d'optimisation des performances
- **SYSTEME_LANGUE.md** - Documentation du système multilingue
- **procedure_api_django.md** - Procédures API Django
- **procedure_app_mobile.md** - Procédures application mobile
- **roadmap_technique.md** - Roadmap de développement technique

### 📁 /en_translations - Traductions anglaises
- **en.ts/.qm** - Fichier de traduction principal anglais
- **[module]_[type].ts/.qm** - Plus de 80 fichiers de traduction par module
  - .ts = fichiers source de traduction
  - .qm = fichiers compilés pour Qt

### 📁 /scripts - Scripts utilitaires
- **add_bulk_test_data.py** - Ajout de données de test en masse
- **check_db_structure.py** - Vérification de la structure base de données
- **check_views.py** - Vérification des vues SQL
- **fix_sql_timestamps.py** - Correction des timestamps SQL
- **generate_simple_test_data.py** - Génération de données test simples
- **generate_test_data.py** - Génération complète de données test
- **init_db.py** - Script d'initialisation base de données
- **init_kpi_views.py** - Initialisation des vues KPI

### 📁 /tests - Tests unitaires
- Structure pour les tests unitaires (actuellement basique)

### 📁 /tools - Outils de développement
- **accueil_back.py** - Sauvegarde de l'interface d'accueil
- **add_missing_column.py** - Ajout automatique de colonnes manquantes
- **check_real_schema.py** - Vérification du schéma réel de la base
- **compile_translations.py** - Compilation des fichiers de traduction
- **fix_model_imports.py** - Correction automatique des imports de modèles
- **installation.md** - Guide d'installation du projet
- **procedure_translation.md** - Procédure de gestion des traductions
- **simple_db_check.py** - Vérification simple de la base de données
- **start_wireguard.sh** - Script de démarrage VPN WireGuard

## 📊 État du système KPI - Validation complète

### ✅ **SYSTÈME 100% OPÉRATIONNEL**
- **Service KPI** : Connexion PostgreSQL + calculs financiers ✅
- **Dashboard principal** : Interface PySide6 + données réelles ✅  
- **Widgets spécialisés** : Machines, Sites, Équipes, Préventif/Curatif ✅
- **Dialogs d'analyse** : 5 dialogs spécialisés avec données temps réel ✅
- **Filtres temporels** : Périodes configurables (7j, 30j, 90j) ✅
- **Tests validés** : Suite complète de tests automatisés ✅

### 🎯 **MÉTRIQUES VALIDÉES**
- **Coût total période** : 14,628.59 € (données réelles)
- **Interventions actives** : 10 interventions
- **Machines surveillées** : 5 machines actives  
- **Sites couverts** : 4 sites
- **Filtres temporels** : 7j→7 machines, 90j→11 machines

### 🚀 **PROCHAINES ÉVOLUTIONS**
1. **Graphiques matplotlib** - Visualisations avancées
2. **Export Excel** - Rapports automatisés avec openpyxl
3. **Filtres avancés** - Par criticité, type machine, équipe
4. **API REST** - Accès mobile et intégrations tierces
5. **Alertes KPI** - Seuils et notifications automatiques

### 🔧 **ARCHITECTURE TECHNIQUE**
- **Base de données** : PostgreSQL avec vues KPI optimisées
- **Interface** : PySide6 (Qt6) moderne et responsive
- **Architecture** : Service Layer + Repository Pattern
- **Langues** : Support multilingue FR/EN/DE
- **Tests** : Suite automatisée avec validation continue

-----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------

## 🗺️ Cartographie des Classes et Appels - Point d'entrée `main.py`

### 📄 **Structure interne de `main.py`**

**Fichier**: `app/main.py` (504 lignes)  
**Rôle**: Point d'entrée principal et orchestrateur de l'application GMAO

#### 🎯 **Fonctions principales**
- **`main()`** - Fonction principale d'orchestration (lignes 115-450)
  - Gestion configuration langue
  - Initialisation base de données
  - Injection des dépendances (Repositories → Services)
  - Authentification utilisateur
  - Création et affichage fenêtre principale
  - Démarrage boucle Qt

#### 🏗️ **Architecture d'injection de dépendances**
```
🔄 FLUX D'INITIALISATION:
1. Configuration langue + logging
2. Connexion PostgreSQL + schéma
3. Instanciation Repositories (15 repositories)
4. Instanciation Services (7 services)
5. Injection croisée services (résolution dépendances circulaires)
6. Authentification utilisateur
7. Création MainWindow avec tous les services
8. Boucle événements Qt
```

### 📊 **Table des imports et appels aux classes externes**

#### 🔧 **Modules système et configuration**
| Module/Classe | Origine | Usage | Ligne |
|---------------|---------|-------|-------|
| `sys`, `os`, `logging` | Standard Python | Système, fichiers, logs | 22-25 |
| `Optional` | `typing` | Type hints | 43 |
| `QApplication`, `QMessageBox`, `QDialog` | `PySide6.QtWidgets` | Interface Qt | 44 |
| `QFont`, `QTranslator` | `PySide6.QtGui/Core` | Interface Qt | 45-46 |
| `clean_project` | `clean_project.py` | Nettoyage cache | 25 |
| `APP_NAME`, `APP_VERSION`, `app_config`, `Language` | `app.config` | Configuration | 127 |

#### 🎨 **Interface Utilisateur**
| Classe | Module | Usage | Ligne |
|--------|--------|-------|-------|
| `MainWindow` | `app.ui.main_window` | Fenêtre principale | 61 |
| `LoginDialog` | `app.ui.dialogs.login_dialog` | Authentification | 96 |

#### 🗄️ **Couche Data Access (15 Repositories)**
| Repository | Module | Entité gérée | Ligne |
|-----------|--------|---------------|-------|
| `UserRepository` | `app.data.repositories.user_repository` | Utilisateurs | 65 |
| `SiteRepository` | `app.data.repositories.site_repository` | Sites industriels | 66 |
| `FabricantRepository` | `app.data.repositories.fabricant_repository` | Fabricants | 67 |
| `TypeMachineRepository` | `app.data.repositories.type_machine_repository` | Types machines | 68 |
| `MachineRepository` | `app.data.repositories.machine_repository` | Machines | 69 |
| `EquipeRepository` | `app.data.repositories.equipe_repository` | Équipes | 70 |
| `TechnicienRepository` | `app.data.repositories.technicien_repository` | Techniciens | 71 |
| `OrdreTravailRepository` | `app.data.repositories.ordre_travail_repository` | Ordres travail | 72 |
| `MaintenanceRepository` | `app.data.repositories.maintenance_repository` | Interventions | 73 |
| `FournisseurRepository` | `app.data.repositories.fournisseur_repository` | Fournisseurs | 74 |
| `PieceRepository` | `app.data.repositories.piece_repository` | Pièces détachées | 75 |
| `InterventionPieceRepository` | `app.data.repositories.intervention_piece_repository` | Pièces/interventions | 76 |
| `MouvementStockRepository` | `app.data.repositories.mouvement_stock_repository` | Mouvements stock | 77 |
| `CompteurRepository` | `app.data.repositories.compteur_repository` | Compteurs machines | 82 |
| `HistoriqueCompteurRepository` | `app.data.repositories.historique_compteur_repository` | Historique compteurs | 83 |

#### 🧠 **Couche Services Métier (7 Services)**
| Service | Module | Responsabilité | Ligne |
|---------|--------|----------------|-------|
| `UserService` | `app.core.services.user_service` | Gestion utilisateurs | 97 |
| `MachineService` | `app.core.services.machine_service` | Gestion parc machines | 90 |
| `MaintenanceService` | `app.core.services.maintenance_service` | Maintenance curative | 91 |
| `StockService` | `app.core.services.stock_service` | Gestion des stocks | 92 |
| `PreventiveMaintenanceService` | `app.core.services.preventive_service` | Maintenance préventive | 93 |
| `AchatService` | `app.core.services.achat_service` | Gestion des achats | 94 |
| `CompteurService` | `app.core.services.compteur_service` | Gestion des compteurs | 86 |
| `FinanceService` | `app.core.services.finance_service` | Calculs financiers | 87 |

#### 🗄️ **Base de données**
| Fonction | Module | Usage | Ligne |
|----------|--------|-------|-------|
| `get_connection` | `app.data.database` | Connexion PostgreSQL | 64 |
| `close_connection` | `app.data.database` | Fermeture connexion | 64 |
| `initialize_database` | `app.data.database` | Init schéma DB | 64 |
| `DatabaseError` | `app.data.database` | Exception DB | 64 |

#### 📊 **Modèles**
| Modèle | Module | Usage | Ligne |
|--------|--------|-------|-------|
| `Utilisateur` | `app.core.models.utilisateur` | Type utilisateur connecté | 98 |

### 🔄 **Flux de dépendances et injections**

#### 📈 **Ordre d'instanciation (CRITIQUE)**
```
1️⃣ REPOSITORIES (lignes 218-261)
   └── Instanciation de 15 repositories

2️⃣ SERVICES BASIQUES (lignes 276-308)
   ├── StockService(piece_repo, fours_repo, mvt_stock_repo)
   ├── UserService(user_repo)
   ├── MachineService(machine_repo, site_repo, fab_repo, type_repo)
   └── AchatService(commande_repo, ligne_commande_repo, piece_repo, mvt_stock_repo)

3️⃣ SERVICES COMPLEXES (lignes 318-347)
   ├── MaintenanceService(7 repositories + stock_service)
   ├── PreventiveMaintenanceService(8 repositories)
   ├── CompteurService(4 repositories + maintenance_service)
   └── FinanceService(5 repositories)

4️⃣ RÉSOLUTION DÉPENDANCES CIRCULAIRES (lignes 358-365)
   ├── maintenance_service.set_finance_service(finance_service)
   └── maintenance_service.set_preventive_service(preventive_service)

5️⃣ MAIN WINDOW (lignes 433-447)
   └── MainWindow(8 services + logged_in_user + app_language)
```

#### 🔗 **Dépendances critiques identifiées**
- **MaintenanceService** ↔ **PreventiveService** (circulaire)
- **MaintenanceService** → **FinanceService** (injection tardive)
- **CompteurService** → **MaintenanceService** (déclenchement OT)
- **Tous Services** → **Repositories** (accès données)

-------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------

## 🗺️ Cartographie des Classes et Appels - Interface principale `MainWindow`

### 📄 **Structure interne de `MainWindow`**

**Fichier**: `app/ui/main_window.py` (1466 lignes)  
**Rôle**: Hub central de l'interface utilisateur - Orchestrateur de toutes les vues et services

#### 🎯 **Classe principale: `MainWindow(QMainWindow)`**

##### 🏗️ **Architecture générale**
```
🔄 FLUX D'INITIALISATION COMPLEXE:
1. Chargement préférences utilisateur (.gmao_app_config.json)
2. Injection de 8 services métier
3. Configuration interface Qt (fenêtre, police, langue)
4. Création de 12+ vues spécialisées (QStackedWidget)
5. Configuration menus/actions avec contrôle d'accès
6. Connexion signaux/slots
7. Intégration dashboard KPI
8. Affichage vue d'accueil
```

##### 🎛️ **Responsabilités principales**
- **Navigation** entre vues via `QStackedWidget`
- **Contrôle d'accès** basé sur rôles utilisateurs
- **Orchestration services** - Hub central de tous les services
- **Configuration UI** - Police, langue, résolution écran
- **Menu système** - 6 menus principaux avec 40+ actions
- **Dashboard KPI** - Intégration système KPI financier
- **Gestion utilisateur** - Session, préférences, authentification

#### 📊 **Méthodes principales (27 méthodes)**

##### 🚀 **Initialisation et configuration**
| Méthode | Responsabilité | Lignes |
|---------|----------------|---------|
| `__init__()` | Initialisation avec injection 8 services | 198-350 |
| `setup_views()` | Création de 12+ vues spécialisées | 580-730 |
| `create_actions()` | Création de 40+ actions Qt | 738-950 |
| `create_menu_bar()` | Création de 6 menus principaux | 958-1120 |

##### 🎨 **Gestion interface utilisateur**
| Méthode | Responsabilité | Usage |
|---------|----------------|-------|
| `switch_view()` | Navigation entre vues | QStackedWidget |
| `choose_font()` | Sélection police personnalisée | QFontDialog |
| `reset_font()` | Remise à zéro police | QApplication |
| `adapt_to_screen_resolution()` | Adaptation résolution écran | QScreen |
| `update_status_bar()` | Mise à jour barre statut | QStatusBar |

##### 🔐 **Gestion utilisateur et session**
| Méthode | Responsabilité | Intégration |
|---------|----------------|-------------|
| `logout()` | Déconnexion utilisateur | UserService |
| `show_db_connection_dialog()` | Configuration DB | DBConnectionDialog |

##### 📊 **Intégration KPI (6 méthodes)**
| Méthode KPI | Dialog associé | Service |
|-------------|----------------|---------|
| `show_kpi_dashboard()` | `KPIDashboard` | FinanceService |
| `show_kpi_machines()` | `MachineKPIDialog` | FinanceService |
| `show_kpi_sites()` | `SiteKPIDialog` | FinanceService |
| `show_kpi_teams()` | `TeamKPIDialog` | FinanceService |
| `show_kpi_preventive()` | `PreventiveKPIDialog` | FinanceService |
| `show_kpi_advanced()` | `AdvancedKPIDialog` | FinanceService |

##### 🛠️ **Utilitaires système**
| Méthode | Responsabilité | Usage |
|---------|----------------|-------|
| `save_user_config()` | Sauvegarde préférences | JSON file |
| `load_user_config()` | Chargement préférences | JSON file |
| `show_popup()` | Messages utilisateur | QMessageBox |
| `show_about_dialog()` | À propos application | QMessageBox |

### 📊 **Table des imports et dépendances**

#### 🔧 **Framework Qt (Interface)**
| Module/Classe | Origine | Usage | Quantité |
|---------------|---------|-------|----------|
| `QMainWindow`, `QStackedWidget`, `QStatusBar` | `PySide6.QtWidgets` | Structure principale | 3 |
| `QAction`, `QMessageBox`, `QDialog` | `PySide6.QtWidgets` | Actions/interactions | 3 |
| `QFont`, `QKeySequence` | `PySide6.QtGui` | Interface/raccourcis | 2 |
| `Slot` | `PySide6.QtCore` | Gestionnaires signaux | 1 |

#### 🎛️ **Services métier injectés (8 services)**
| Service | Module | Responsabilité | Usage dans MainWindow |
|---------|--------|----------------|----------------------|
| `UserService` | `app.core.services.user_service` | Gestion utilisateurs | UserView, authentification |
| `MachineService` | `app.core.services.machine_service` | Gestion machines | MachineView, SiteView, FabricantView |
| `MaintenanceService` | `app.core.services.maintenance_service` | Maintenance curative | WelcomeView, OTView |
| `StockService` | `app.core.services.stock_service` | Gestion stocks | PieceView |
| `PreventiveMaintenanceService` | `app.core.services.preventive_service` | Maintenance préventive | GammeView |
| `AchatService` | `app.core.services.achat_service` | Gestion achats | CommandeView |
| `CompteurService` | `app.core.services.compteur_service` | Gestion compteurs | MachineCountersDialog |
| `FinanceService` | `app.core.services.finance_service` | 🔥 Calculs financiers | **6 dialogs KPI** |

#### 🎨 **Vues spécialisées (12+ vues)**
| Vue | Module | Service associé | Index StackedWidget |
|-----|--------|-----------------|---------------------|
| `WelcomeView` | `app.ui.views.welcome_view` | MaintenanceService | 0 (VIEW_INDEX_WELCOME) |
| `UserView` | `app.ui.views.user_view` | UserService | 1 (VIEW_INDEX_USERS) |
| `MachineView` | `app.ui.views.machine_view` | MachineService | 2 (VIEW_INDEX_MACHINES) |
| `SiteView` | `app.ui.views.site_view` | MachineService | Dynamic |
| `FabricantView` | `app.ui.views.fabricant_view` | MachineService | Dynamic |
| `TypeMachineView` | `app.ui.views.type_machine_view` | MachineService | Dynamic |
| `OTView` | `app.ui.views.ot_view` | MaintenanceService | Dynamic |
| `EquipeView` | `app.ui.views.equipe_view` | MaintenanceService | Dynamic |
| `TechnicienView` | `app.ui.views.technicien_view` | MaintenanceService | Dynamic |
| `PieceView` | `app.ui.views.piece_view` | StockService | Dynamic |
| `FournisseurView` | `app.ui.views.fournisseur_view` | StockService | Dynamic |
| `GammeView` | `app.ui.views.gamme_view` | PreventiveService | Dynamic |
| `CommandeView` | `app.ui.views.commande_view` | AchatService | Dynamic |

#### 💬 **Dialogs spécialisés**
| Dialog | Module | Usage | Service |
|--------|--------|-------|---------|
| `MaintenanceDetailDialog` | `app.ui.dialogs.maintenance_detail_dialog` | Détails maintenance | MaintenanceService |
| `DBConnectionDialog` | `app.ui.dialogs.db_connection_dialog` | Config DB | Database |
| `MachineCountersDialog` | `app.ui.dialogs.machine_counters_dialog` | Compteurs machine | CompteurService |
| `InterventionRequestView` | `app.ui.views.intervention_request_view` | Demandes intervention | MaintenanceService |

#### 📊 **Dialogs KPI spécialisés (6 dialogs)**
| Dialog KPI | Module | Service | Analyse |
|------------|--------|---------|---------|
| `KPIDashboard` | `app.ui.kpi.kpi_dashboard_clean` | FinanceService | 🔥 Dashboard principal |
| `MachineKPIDialog` | `app.ui.kpi.dialogs.machine_kpi_dialog` | FinanceService | KPI par machine |
| `SiteKPIDialog` | `app.ui.kpi.dialogs.site_kpi_dialog` | FinanceService | KPI par site |
| `TeamKPIDialog` | `app.ui.kpi.dialogs.team_kpi_dialog` | FinanceService | KPI par équipe |
| `PreventiveKPIDialog` | `app.ui.kpi.dialogs.preventive_kpi_dialog` | FinanceService | Préventif vs curatif |
| `AdvancedKPIDialog` | `app.ui.kpi.dialogs.advanced_kpi_dialog` | FinanceService | Analyses avancées |

#### 🔧 **Modules système et configuration**
| Module | Origine | Usage | Fonction |
|--------|---------|-------|----------|
| `Utilisateur` | `app.core.models.utilisateur` | Modèle utilisateur | Session/contrôle accès |
| `APP_NAME`, `APP_VERSION` | `app.config` | Configuration app | Titre fenêtre |
| `can_access` | `app.access_control` | Contrôle d'accès | Menus/actions |
| `close_connection` | `app.data.database` | Base de données | Fermeture session |
| `backup_database` | `app.utils.backup_utils` | Utilitaires | Sauvegarde DB |

### 🏗️ **Architecture d'injection complexe**

#### 📈 **Constructeur surchargé (8 paramètres)**
```python
def __init__(self, 
    user_service: UserService,           # Gestion utilisateurs
    machine_service: MachineService,     # Gestion machines  
    maintenance_service: MaintenanceService,  # Maintenance curative
    stock_service: StockService,         # Gestion stocks
    preventive_service: PreventiveMaintenanceService,  # Maintenance préventive
    achat_service: AchatService,         # Gestion achats
    compteur_service: CompteurService,   # Gestion compteurs
    finance_service: FinanceService,     # 🔥 Calculs financiers KPI
    logged_in_user: Utilisateur,         # Utilisateur connecté
    app_language: str = "fr"             # Langue application
)
```

#### 🔄 **Flux de création des vues**
```
1️⃣ SERVICES INJECTÉS → STOCKAGE LOCAL
   └── 8 services stockés comme attributs

2️⃣ UTILISATEUR CONNECTÉ → CONTRÔLE D'ACCÈS
   ├── self.current_user: Utilisateur
   ├── self.logged_in_user_id: int
   └── self.user_role: str

3️⃣ CONFIGURATION UI → PRÉFÉRENCES
   ├── Font personnalisée (JSON config)
   ├── Keyboard layout
   └── Résolution écran

4️⃣ CRÉATION VUES → INJECTION SERVICES
   ├── WelcomeView(maintenance_service)
   ├── UserView(user_service)
   ├── MachineView(machine_service)
   └── [...12+ autres vues]

5️⃣ MENUS/ACTIONS → CONTRÔLE D'ACCÈS
   ├── can_access(role, action)
   ├── Menus dynamiques selon droits
   └── Actions conditionnelles

6️⃣ KPI INTEGRATION → FINANCE SERVICE
   └── 6 dialogs KPI utilisant FinanceService
```

### 🎛️ **Gestion de la navigation**

#### 📊 **QStackedWidget central**
- **Principe**: Une seule vue visible à la fois
- **Navigation**: `switch_view(view_widget)`
- **Index constants**: `VIEW_INDEX_WELCOME`, `VIEW_INDEX_USERS`, `VIEW_INDEX_MACHINES`
- **Index dynamiques**: Calculés lors de l'ajout

#### 🔗 **Connexions signaux/slots**
- **Actions Qt**: Connectées aux méthodes de navigation
- **Contrôle d'accès**: Validation avant affichage
- **Gestion erreurs**: Try/catch pour chaque vue

### 🔐 **Système de contrôle d'accès**

#### 🎭 **Rôles utilisateurs**
- **Admin**: Accès complet
- **Manager**: Accès gestion + consultation
- **Technician**: Accès opérationnel
- **User**: Accès consultation

#### 🛡️ **Contrôle des menus**
```python
if can_access(self.user_role, "action_name"):
    action.setVisible(True)
else:
    action.setVisible(False)
```

### 🌍 **Configuration multilingue**

#### 📝 **Support traduction**
- **Méthode**: `self.tr("text")` pour tous les textes
- **Configuration**: `app_language` injecté
- **Scope**: Interface complète traduite

### 💾 **Gestion des préférences**

#### 📄 **Fichier configuration**
- **Path**: `~/.gmao_app_config.json`
- **Contenu**: Police, layout clavier
- **Persistance**: Entre sessions

#### ⚙️ **Fonctions utilitaires**
- `save_user_config(font, keyboard_layout)`
- `load_user_config() -> dict`

### 🚨 **Gestion d'erreurs identifiée**

#### 🛡️ **Stratégie défensive**
- **Try/catch** pour chaque création de vue
- **Attributs None** si échec création
- **Logs détaillés** pour debugging
- **Interface dégradée** en cas d'erreur

### 📊 **Métriques du fichier**
- **🔢 Total lignes**: 1466
- **📦 Imports**: 38 modules/classes
- **🎛️ Services injectés**: 8 services
- **🎨 Vues gérées**: 12+ vues spécialisées
- **💬 Dialogs**: 10+ dialogs
- **🎯 Actions Qt**: 40+ actions
- **📋 Menus**: 6 menus principaux
- **📊 Dialogs KPI**: 6 dialogs KPI
- **⚡ Complexité**: Très élevée (hub central)

### 🔗 **Dépendances critiques identifiées**
- **FinanceService** → **6 dialogs KPI** (intégration majeure)
- **MachineService** → **4 vues** (machines, sites, fabricants, types)
- **MaintenanceService** → **3 vues** (welcome, OT, équipes)
- **UserService** → **Contrôle d'accès** (authentification/autorisation)
- **Tous services** → **MainWindow** (hub central obligatoire)

---
**Dernière mise à jour** : 3 juillet 2025
**Statut** : ✅ Production Ready - Système KPI complet et validé
