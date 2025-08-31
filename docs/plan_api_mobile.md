# Plan: Développement API Django pour GMAO Mobile

- ✅ Validation utilisateur de l'interface web responsive pour le rapport de maintenance.
- ✅ Problèmes Git résolus lors du déploiement Linux : authentification GitHub via token d'accès personnel, gestion des conflits locaux (reset/stash), dépôt synchronisé avec succès sur le serveur cible. Prêt pour la suite du déploiement et des tests Django.
- ✅ Completion majeure de l'interface maintenance_report.html : ajout du modal d'ajout de pièces, amélioration de tous les champs à choix multiple (techniciens, types, résultats, évaluations, impacts), validation côté client renforcée, notifications toast Bootstrap, gestion d'erreurs améliorée, et correction complète de l'enregistrement des rapports de maintenance avec mapping correct des champs du formulaire vers le modèle Django.
- ✅ Résolution du problème d'imports Django REST Framework : installation correcte des dépendances dans l'environnement virtuel api_mobile/.venv, création du fichier .vscode/settings.json pour configurer l'interpréteur Python, validation du fonctionnement de l'API Django (django check sans erreurs).
- 📦 Prochaine étape : tester le déploiement et l'intégration sur le serveur Linux après enrichissement des données.Notes
- L'application mobile doit permettre :
  1. Réception des ordres de travail pour un technicien
  2. Réservation de pièces au magasin
  3. Saisie du rapport d'intervention
- Approche technique retenue : API REST Django + Interface web responsive + Future app mobile Kivy
- Architecture en 3 phases : API REST → Interface Web → Application Mobile Native
- Réutilisation maximale de la logique métier existante (services, repositories)
- Base de données PostgreSQL partagée avec l'application GMAO desktop existante
- Authentification JWT pour sécuriser l'API
- Documentation automatique avec Swagger/OpenAPI
- Tests automatisés et CI/CD pour assurer la qualité
- Interface web responsive comme première étape avant l'app mobile
- Procédure complète documentée dans docs/procedure_app_mobile.md
- Chaque application (app et api_mobile) doit avoir son propre dossier .venv et requirements.txt pour isoler proprement les dépendances Python, conformément à la structure recommandée.
- Avant de démarrer la Phase 1 (API), refactoriser le dossier app pour y migrer config.py, main.py, init_db.py et corriger les imports, afin de rendre l'application desktop autonome et testable localement.
- Lors de la migration, ajouter la gestion dynamique du sys.path dans les fichiers principaux pour garantir la compatibilité des imports sans modifier tout le code existant.
- Problèmes d'import résolus dans app/ grâce à l'ajout de la gestion du sys.path et à la définition des objets manquants (app_config, Language). Toutes les langues utilisées dans le code ont été ajoutées à l'énumération Language.
- Refactorisation du dossier app validée : application desktop testée et fonctionnelle après migration et corrections.
- ✅ Problème de téléscopage résolu : ViewSets et serializers alignés sur la structure réelle des modèles (Piece, Technicien, Machine). Les endpoints sont maintenant exposés et testables.
- ✅ Problèmes de téléscopage/références de champs dans les ViewSets (OrdreTravail, Maintenance) corrigés : tous les champs de filtrage et d'ordering utilisent désormais les noms réels des modèles Django, plus d'erreur 500 sur les endpoints REST.
- ✅ Problèmes de téléscopage/références de champs dans les serializers (OrdreTravailSerializer, MaintenanceSerializer) corrigés : tous les champs exposés correspondent strictement aux champs réels des modèles Django, plus d'erreur d'exposition d'API.
- ⚠️ Le schéma défini dans schemas.py ne correspond PAS à la structure réelle de la table mouvement_stock. Utiliser impérativement la structure réelle (colonnes : type_mouvement_id, commentaire, utilisateur_id, etc. — pas de colonne raison, user_id, ot_id) pour tout développement, en particulier l'API Django.
- ⚠️ Téléscopage identifié : deux structures différentes pour la table mouvement_stock (schemas.py vs base réelle). Toujours se baser sur la structure réelle de la DB (id, piece_id, type_mouvement_id, quantite, commentaire, utilisateur_id, etc.) pour le code, les requêtes SQL et les modèles Django. Corriger schemas.py ou documenter cette différence pour éviter toute confusion future.
- ✅ Correction appliquée : schemas.py mis à jour pour refléter la structure réelle de la table mouvement_stock (plus de confusion possible avec les anciennes colonnes ou types).
- ✅ Correction appliquée : mapping automatique des types de mouvements textuels ('ENTREE', 'SORTIE', etc.) en IDs numériques dans le repository MouvementStock.
- 📁 Les outils/scripts de test ont été déplacés dans un dossier tools pour garder le projet propre.
- 💡 Suggestion pour le futur : intégrer une IA locale (ex : Code Llama, SQLCoder, Ollama) pour générer, valider ou optimiser les requêtes SQL directement depuis l'application, afin d'améliorer la productivité et la robustesse.
- ⚠️ Ne jamais modifier la structure des tables existantes dans la base partagée en production (server 45.140.165.228). Créer de nouvelles tables ou une nouvelle base si besoin. Trois applications partagent actuellement la même DB (gmao, stocks, purchases).
- 🛡️ Stratégie validée : Option A (base partagée, pas de modification de structure existante). Utiliser managed=False pour les modèles Django sur les tables existantes, et inclure toute nouvelle table créée pour l'API mobile dans schemas.py pour garantir la cohérence de l'initialisation automatique.
- 💡 Les notions d'intervenant extérieur et de pièce hors stock sont déjà gérées dans les repositories et n'ont pas besoin d'être exposées individuellement dans l'API mobile, ce qui simplifie le modèle de données pour l'API.
- ✅ Correction appliquée : la configuration de la base de données dans `.env` correspond bien à la base PostgreSQL cible (gmao_industrie_data, user gmao_app_user).
- ℹ️ Tous les environnements sont maintenant corrects (développement, production, GitHub, accès RDP). Le transfert de la variable langage reste à corriger lors de la prochaine session de développement.
- ✅ Clé secrète Django générée et configurée dans `.env` (plus de placeholder).
- ✅ Endpoint de test `/api/status/` validé : l'API répond avec succès (HTTP 200, message OK).
- ✅ Génération automatique des modèles Django réalisée avec inspectdb (mobile_api/models_generated.py généré).
- ⚠️ Problème détecté : la génération inspectdb était tronquée à 504 lignes, mais a été régénérée avec succès (831 lignes, fichier complet). Tous les modèles clés pour l'API mobile sont maintenant présents et validés.
- ✅ Modèles Django adaptés créés dans models.py : structure alignée sur la base PostgreSQL réelle, relations et Meta corrigées, propriétés utiles ajoutées. Prêt pour serializers et vues.
- 🌐 Début de la Phase 2 : créer une vue web read-only pour les ordres de travail "En cours" (statut = "Encours"), interface en anglais, tous les textes visibles traduisibles via QTranslator/self.tr().
- ✅ Interface web responsive "Work Orders In Progress" : templates, vues, endpoints API et URLs créés. Warning Django (namespace URL) résolu.
- ✅ Correction du chargement des OT côté client : filtrage JS sur statut "EnCours" après récupération brute via l'API (contourne le problème de filtrage serveur).
- ✅ Interface web responsive validée côté utilisateur : affichage des OT "EnCours" testé, modal de détails fonctionnel, filtrage JS, design responsive Bootstrap, prêt pour extension rapport de maintenance.
- ✅ Création de la vue Django pour le formulaire de rapport de maintenance (MaintenanceReportView), ajout de l'URL correspondante et connexion du bouton "Start Maintenance Report" dans l'UI des OT.
- ✅ Correction des erreurs de lint dans le template maintenance_report.html (JS).
- ✅ Correction JS : passage des variables Django au JS via json_script dans maintenance_report.html, ce qui corrige les erreurs de lint et sécurise le transfert de données de contexte.
- ✅ Endpoint API GET /api/maintenance/form-data/<ot_id>/ implémenté pour fournir toutes les données nécessaires au formulaire de rapport de maintenance (techniciens actifs, pièces disponibles, infos OT).
- ✅ Correction : chargement explicite des tags d'internationalisation Django ({% load i18n %}) dans tous les templates utilisant {% trans %} (work_orders.html, maintenance_report.html, base.html).
- ✅ Correction : l'ordre des tags Django dans les templates est respecté (`{% extends %}` doit toujours être le premier tag, suivi de `{% load i18n %}` si nécessaire) pour éviter les TemplateSyntaxError.
- ✅ Interface web responsive pour rapports de maintenance validée par l'utilisateur (navigation, calculs, JS, internationalisation). Tests réels en attente d'enrichissement des données via GMAO desktop.
- ✅ Validation utilisateur de l'interface web responsive pour le rapport de maintenance.
- ✅ Problèmes Git résolus lors du déploiement Linux : authentification GitHub via token d'accès personnel, gestion des conflits locaux (reset/stash), dépôt synchronisé avec succès sur le serveur cible. Prêt pour la suite du déploiement et des tests Django.
- 📦 Prochaine étape : tester le déploiement et l'intégration sur le serveur Linux après enrichissement des données.
- ℹ️ Pour toutes les commandes Python (création/activation du venv, migrations, etc.) sous Linux, se placer dans le dossier `/app` du projet (ex : `/opt/Projets/gmao_app_PostGres/app`) pour respecter la structure du projet et éviter les erreurs d'environnement.
- ℹ️ Il est crucial de respecter cette étape pour garantir la compatibilité et la réussite des commandes Python, notamment pour les migrations et la création de l'environnement virtuel.

## Task List

### Phase 1 - API REST Django (Priorité Haute)
- [ ] **Étape préliminaire - Refactorisation de l'application desktop**
  - [x] Migrer config.py, main.py, init_db.py dans app/
  - [x] Corriger les imports dans tout app/
  - [x] Tester l'application desktop localement dans app/
  - [x] Mettre à jour schemas.py pour refléter la structure réelle
  - [x] Corriger le mapping type_mouvement (texte → ID numérique) dans le repository
  - [ ] Mettre à jour la documentation si besoin
- [ ] **Étape 0 - Analyse et Préparation**
  - [ ] Analyser le schéma de données (app/data/schemas.py)
  - [ ] Identifier la logique métier à réutiliser (services, repositories)
  - [ ] Vérifier les relations entre tables après inspectdb

- [x] **Étape 1 - Initialisation Projet Django**
  - [x] Créer environnement virtuel et installer dépendances
  - [x] Créer projet Django et app API
  - [x] Configurer settings.py (DRF, JWT, CORS, PostgreSQL)
  - [x] Créer requirements.txt et .env
  - [x] Configurer les URLs principales et endpoint de test
  - [x] Vérifier la connexion à la base PostgreSQL
  - [x] Générer une clé secrète Django sécurisée
  - [x] Valider le endpoint de test /api/status/

- [ ] **Étape 2 - Modèles Django**
  - [x] Générer modèles avec inspectdb ou créer manuellement
  - [x] Adapter les modèles pour Django (Meta, relations)
  - [x] Créer et appliquer les migrations

- [ ] **Étape 3 - Serializers**
  - [x] Créer serializers pour OT, Maintenance, Technicien, Piece
  - [x] Implémenter validation métier dans les serializers
  - [x] Ajouter serializers pour actions spécifiques (réservation)
  - [x] Corriger les téléscopages/références de champs dans les serializers

- [x] **Étape 4 - Vues et ViewSets**
  - [x] Créer ViewSets alignés sur la structure réelle
    - [x] TechnicienViewSet (filtrage actif)
    - [x] PieceViewSet (statut 'ACTIF')
    - [x] MachineViewSet (champs réels)
    - [x] OrdreTravailViewSet/ MaintenanceViewSet
  - [x] Configurer les routes API avec DefaultRouter et activer les endpoints

- [x] **Étape 5 - Routing et URLs**
  - [x] Configurer les routes API avec DefaultRouter
  - [ ] Ajouter endpoints JWT (login, refresh, logout)
  - [ ] Configurer documentation Swagger

- [ ] **Étape 6 - Sécurité et Permissions**
  - [ ] Configurer authentification JWT
  - [ ] Implémenter permissions par rôle (technicien)
  - [ ] Sécuriser les endpoints sensibles

- [ ] **Étape 7 - Tests API**
  - [ ] Tests unitaires des serializers et vues
  - [ ] Tests d'intégration des endpoints
  - [ ] Tests de sécurité et permissions

### Phase 2 - Interface Web Responsive (Priorité Moyenne)
- [ ] **Étape 1 - Structure Frontend**
  - [ ] Choisir approche (Django templates + JS léger vs SPA)
  - [ ] Créer app Django pour l'interface web
  - [ ] Configurer templates et fichiers statiques

- [ ] **Étape 2 - Pages Principales**
  - [ ] Page de connexion avec JWT
  - [ ] Dashboard technicien (liste OT assignés)
  - [ ] Page détail OT avec formulaire rapport
  - [ ] Page réservation de pièces
  - [x] Créer une vue read-only pour les OT "En cours" (statut = "Encours"), interface en anglais, textes traduisables (QTranslator/self.tr())
  - [x] Intégrer/tester l'UI web responsive pour la liste des OT "EnCours"
  - [x] Valider l'interface web responsive côté utilisateur
  - [x] Création de la vue Django pour le formulaire de rapport de maintenance (MaintenanceReportView), ajout de l'URL correspondante et connexion du bouton "Start Maintenance Report" dans l'UI des OT.
  - [x] Correction des erreurs de lint dans le template maintenance_report.html (JS).
  - [x] Intégration de l'endpoint API pour les données du formulaire de maintenance (maintenance_form_data_api)

- [ ] **Étape 3 - UI/UX Responsive**
  - [ ] Intégrer framework CSS (Bootstrap/Tailwind)
  - [ ] Optimiser pour mobile (responsive design)
  - [ ] Ajouter interactions JavaScript (AJAX)

- [ ] **Étape 4 - Intégration API**
  - [ ] Consommer endpoints API depuis le frontend
  - [ ] Gérer authentification JWT côté client
  - [ ] Implémenter gestion d'erreurs

### Phase 3 - Application Mobile Native Kivy (Priorité Basse)
- [ ] **Étape 1 - Architecture Mobile**
  - [ ] Installer et configurer Kivy
  - [ ] Créer structure de l'app mobile
  - [ ] Configurer navigation entre écrans

- [ ] **Étape 2 - Écrans Principaux**
  - [ ] Écran de connexion
  - [ ] Liste des ordres de travail
  - [ ] Formulaire de rapport d'intervention
  - [ ] Interface de réservation de pièces

- [ ] **Étape 3 - Fonctionnalités Avancées**
  - [ ] Mode hors-ligne avec synchronisation
  - [ ] Stockage sécurisé des tokens JWT
  - [ ] Notifications push (optionnel)

- [ ] **Étape 4 - Packaging et Déploiement**
  - [ ] Configuration Buildozer pour Android
  - [ ] Tests sur appareils réels
  - [ ] Publication sur stores (optionnel)

## Current Goal
- Tester l'UI web et l'intégration API

## Livrables Attendus
- **Phase 1** : API REST Django fonctionnelle, documentée et testée
- **Phase 2** : Interface web responsive consommant l'API
- **Phase 3** : Application mobile native Kivy (future)

## Dépendances Techniques
- Python 3.8+
- Django 4.x + Django REST Framework
- PostgreSQL (base existante)
- JWT pour l'authentification
- Swagger/OpenAPI pour la documentation
- Bootstrap/Tailwind pour l'UI web
- Kivy pour l'app mobile (Phase 3)

## Risques Identifiés
- Complexité d'intégration avec la logique métier existante
- Gestion des permissions et sécurité multi-utilisateurs
- Performance de l'API avec montée en charge
- Synchronisation hors-ligne pour l'app mobile

## Métriques de Succès
- API fonctionnelle avec tous les endpoints requis
- Interface web utilisable sur mobile et desktop
- Tests automatisés avec couverture > 80%
- Documentation complète pour les développeurs
- Temps de réponse API < 500ms pour les requêtes standard