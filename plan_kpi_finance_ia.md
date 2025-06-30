# Plan: KPI Financiers par Centre de Frais & Outil d'Interrogation IA

## 🎯 Vision Stratégique
Développer un système d'analyse financière avancé pour la GMAO permettant :
- **Suivi des coûts par centre de frais** (machines, sites, bâtiments, équipes)
- **Analyse des tendances** temporelles et comparatives
- **Outil d'interrogation intelligent** (SQL + IA) pour explorer les données
- **Tableaux de bord exécutifs** pour la prise de décision

## 📊 Phase 1 - KPI Financiers par Centre de Frais (Priorité Haute)

### Étape 1.1 - Analyse et Conception
- [ ] **Audit des données financières existantes**
  - [ ] Identifier toutes les sources de coûts (MOD, pièces, frais externes)
  - [ ] Analyser les tables maintenance_intervenant et maintenance_frais_externe
  - [ ] Mapper les relations avec machines, sites, équipes
  - [ ] Documenter les règles de calcul actuelles

- [ ] **Définition des centres de frais**
  - [ ] **Par Machine** : Coûts individuels par équipement
  - [ ] **Par Site** : Agrégation par localisation géographique
  - [ ] **Par Bâtiment/Zone** : Découpage par secteur
  - [ ] **Par Équipe** : Coûts par groupe de techniciens
  - [ ] **Par Type de Machine** : Analyse par famille d'équipements
  - [ ] **Par Type d'Intervention** : Préventif vs Curatif vs Urgence

- [ ] **Conception des métriques KPI**
  - [ ] Coût total par centre de frais
  - [ ] Coût moyen par intervention
  - [ ] Évolution temporelle (mensuelle, trimestrielle, annuelle)
  - [ ] Ratios coût/heure de fonctionnement
  - [ ] Top/Flop des centres les plus coûteux
  - [ ] Indicateurs de dérive budgétaire

### Étape 1.2 - Architecture Base de Données
- [ ] **Création des vues métier**
  - [ ] Vue consolidée des coûts par maintenance
  - [ ] Vue agrégée par machine/période
  - [ ] Vue agrégée par site/période
  - [ ] Vue comparative préventif/curatif

- [ ] **Tables de synthèse (optionnel)**
  - [ ] Table kpi_couts_machine (cache des calculs)
  - [ ] Table kpi_couts_site (cache des calculs)
  - [ ] Index optimisés pour les requêtes d'agrégation

- [ ] **Procédures stockées d'agrégation**
  - [ ] Calcul des coûts mensuels par centre
  - [ ] Calcul des tendances et moyennes mobiles
  - [ ] Mise à jour incrémentale des KPI

### Étape 1.3 - Services Backend
- [ ] **Extension du FinanceService**
  - [ ] Méthodes de calcul par centre de frais
  - [ ] Calculs de tendances et comparaisons
  - [ ] Gestion des périodes et filtres

- [ ] **Nouveau KPIService**
  - [ ] Service dédié aux calculs de KPI
  - [ ] Cache intelligent des résultats
  - [ ] Export des données (Excel, CSV, PDF)

```python
class KPIService:
    def get_couts_par_machine(self, periode_debut, periode_fin)
    def get_couts_par_site(self, periode_debut, periode_fin)
    def get_tendances_couts(self, centre_frais, nb_periodes)
    def get_top_machines_couteuses(self, limite=10)
    def get_ratio_preventif_curatif(self, centre_frais)
```

### Étape 1.4 - Interface Utilisateur
- [ ] **Nouveau module KPI Dashboard**
  - [ ] Écran principal avec sélection de centre de frais
  - [ ] Graphiques interactifs (Chart.js/Plotly)
  - [ ] Filtres par période, site, type d'intervention
  - [ ] Export des rapports

- [ ] **Widgets de visualisation**
  - [ ] Graphiques en barres (coûts par machine)
  - [ ] Graphiques en courbes (évolution temporelle)
  - [ ] Camemberts (répartition par type)
  - [ ] Tableaux de bord avec KPI clés

- [ ] **Intégration dans MainWindow**
  - [ ] Nouvel onglet "Analyse Financière"
  - [ ] Menu "Rapports KPI"
  - [ ] Raccourcis vers les vues principales

## 🤖 Phase 2 - Outil d'Interrogation Base de Données (Priorité Moyenne)

### Étape 2.1 - Interface SQL Expert
- [ ] **Éditeur SQL avancé**
  - [ ] Coloration syntaxique
  - [ ] Auto-complétion (tables, colonnes)
  - [ ] Validation de syntaxe en temps réel
  - [ ] Historique des requêtes

- [ ] **Catalogue de données**
  - [ ] Explorer de schéma interactif
  - [ ] Documentation des tables et colonnes
  - [ ] Exemples de requêtes types
  - [ ] Relations visuelles entre tables

- [ ] **Résultats et Export**
  - [ ] Affichage tabulaire avec pagination
  - [ ] Export Excel/CSV/PDF
  - [ ] Graphiques automatiques si pertinent
  - [ ] Sauvegarde des requêtes favorites

### Étape 2.2 - Agent IA d'Interrogation
- [ ] **Architecture IA**
  - [ ] Choix de la solution (OpenAI API, Ollama local, ou autre)
  - [ ] Modèle de prompt engineering pour SQL
  - [ ] Context knowledge base (schéma DB + exemples)
  - [ ] Validation et sécurisation des requêtes générées

- [ ] **Natural Language to SQL**
```python
class SQLAssistant:
    def translate_to_sql(self, question_naturelle: str) -> str
    def validate_sql_security(self, sql: str) -> bool
    def explain_query(self, sql: str) -> str
    def suggest_optimizations(self, sql: str) -> List[str]
```

- [ ] **Interface conversationnelle**
  - [ ] Chat bot intégré
  - [ ] Historique des conversations
  - [ ] Possibilité de raffiner les requêtes
  - [ ] Explication des résultats

### Étape 2.3 - Exemples d'Utilisation IA
- [ ] **Questions types supportées**
  - "Quelles sont les 5 machines les plus coûteuses ce mois ?"
  - "Évolution des coûts de maintenance du site A sur 6 mois"
  - "Comparaison préventif/curatif par type de machine"
  - "Prédiction des coûts pour le prochain trimestre"

- [ ] **Analyses prédictives**
  - [ ] Détection des machines à risque de panne
  - [ ] Prévision des budgets maintenance
  - [ ] Recommandations d'optimisation
  - [ ] Alertes sur les dérives

## 🔧 Phase 3 - Intégration et Optimisation (Priorité Basse)

### Étape 3.1 - Performance et Cache
- [ ] **Optimisation des requêtes**
  - [ ] Index sur les colonnes de filtrage
  - [ ] Vues matérialisées pour gros volumes
  - [ ] Cache Redis pour résultats fréquents

- [ ] **Calcul en arrière-plan**
  - [ ] Tâches planifiées pour mise à jour KPI
  - [ ] Notifications de fin de calcul
  - [ ] Versioning des données historiques

### Étape 3.2 - Sécurité et Gouvernance
- [ ] **Contrôle d'accès**
  - [ ] Permissions par niveau utilisateur
  - [ ] Audit des requêtes SQL exécutées
  - [ ] Limitation des ressources (timeout, rows)

- [ ] **Protection des données**
  - [ ] Anonymisation pour requêtes IA
  - [ ] Chiffrement des données sensibles
  - [ ] Logs d'accès détaillés

## 📋 Planning et Jalons

### Sprint 1 (2 semaines) - Fondations KPI
- Audit des données existantes
- Conception des centres de frais
- Première version FinanceService étendu

### Sprint 2 (2 semaines) - Interface KPI Basic
- Vues de base par machine/site
- Graphiques simples
- Export Excel/CSV

### Sprint 3 (2 semaines) - Dashboard Avancé
- Interface complète avec filtres
- Graphiques interactifs
- Intégration dans MainWindow

### Sprint 4 (2 semaines) - SQL Expert
- Éditeur SQL avec auto-complétion
- Catalogue de données
- Sauvegarde requêtes

### Sprint 5 (3 semaines) - Agent IA
- Intégration modèle IA (local/cloud)
- Natural Language to SQL
- Interface conversationnelle

### Sprint 6 (1 semaine) - Polish & Deploy
- Tests, optimisations
- Documentation utilisateur
- Déploiement production

## 🛠️ Stack Technique

### Backend
- **Python** : Calculs et services métier
- **PostgreSQL** : Base de données avec vues optimisées
- **Redis** : Cache pour performances (optionnel)

### Frontend
- **Qt/PySide6** : Interface desktop intégrée
- **Chart.js/Plotly** : Graphiques interactifs
- **Monaco Editor** : Éditeur SQL avancé

### IA
- **Option A - Cloud** : OpenAI GPT-4 API (payant, performant)
- **Option B - Local** : Ollama + Code Llama/SQLCoder (gratuit, confidentialité)
- **Option C - Hybride** : Local par défaut, cloud en fallback

### DevOps
- **Docker** : Conteneurisation pour IA locale
- **Pytest** : Tests automatisés
- **GitHub Actions** : CI/CD

## 🎯 Métriques de Succès

### KPI Techniques
- Temps de réponse < 2s pour calculs KPI standards
- Capacité à traiter 100k+ lignes de données historiques
- 95% de précision sur génération SQL via IA

### KPI Métier
- Identification des 20% machines causant 80% des coûts
- Réduction de 15% du temps d'analyse financière
- Satisfaction utilisateur > 8/10 sur interface

## 🚨 Risques et Mitigation

### Risques Techniques
- **Performance** : Optimiser avec index et cache
- **Complexité SQL** : Commencer simple, itérer
- **Fiabilité IA** : Validation humaine obligatoire

### Risques Métier
- **Résistance au changement** : Formation et accompagnement
- **Données incomplètes** : Audit et nettoyage préalable
- **Coût IA** : Commencer par solution locale gratuite

## 📚 Documentation

### Pour Développeurs
- Architecture des services KPI
- Guide d'intégration IA
- Référence API des nouveaux services

### Pour Utilisateurs
- Guide d'utilisation dashboard KPI
- Tutoriel requêtes SQL
- FAQ outil IA

---

## 📝 Notes et Évolutions

- **Version 1.0** : KPI de base + SQL expert
- **Version 1.1** : Agent IA simple (questions prédéfinies)
- **Version 2.0** : IA avancée + analyses prédictives
- **Version 2.1** : API REST pour intégration externe

---

*Plan créé le 30/06/2025 - À enrichir au fur et à mesure du développement*
