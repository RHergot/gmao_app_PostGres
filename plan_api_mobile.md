# Plan: Développement API Django pour GMAO Mobile

## Notes
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

## Task List

### Phase 1 - API REST Django (Priorité Haute)
- [ ] **Étape 0 - Analyse et Préparation**
  - [ ] Analyser le schéma de données (app/data/schemas.py)
  - [ ] Identifier la logique métier à réutiliser (services, repositories)
  - [ ] Vérifier les relations entre tables après inspectdb

- [ ] **Étape 1 - Initialisation Projet Django**
  - [ ] Créer environnement virtuel et installer dépendances
  - [ ] Créer projet Django et app API
  - [ ] Configurer settings.py (DRF, JWT, CORS, PostgreSQL)

- [ ] **Étape 2 - Modèles Django**
  - [ ] Générer modèles avec inspectdb ou créer manuellement
  - [ ] Adapter les modèles pour Django (Meta, relations)
  - [ ] Créer et appliquer les migrations

- [ ] **Étape 3 - Serializers**
  - [ ] Créer serializers pour OT, Maintenance, Technicien, Piece
  - [ ] Implémenter validation métier dans les serializers
  - [ ] Ajouter serializers pour actions spécifiques (réservation)

- [ ] **Étape 4 - Vues et ViewSets**
  - [ ] Créer ViewSets avec filtrage par technicien authentifié
  - [ ] Implémenter actions personnalisées (reserve_piece, submit_report)
  - [ ] Intégrer les services existants dans les vues

- [ ] **Étape 5 - Routing et URLs**
  - [ ] Configurer les routes API avec DefaultRouter
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
Commencer la Phase 1 - Étape 0 : Analyse et préparation des actifs existants

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
