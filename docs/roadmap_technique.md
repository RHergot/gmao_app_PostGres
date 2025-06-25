# Roadmap Technique GMAO Industrielle

## Table des matières
1. [Introduction et objectifs](#introduction)
2. [Phases de développement](#phases)
3. [Synthèse technique par phase](#synthese)
4. [Modèles de données clés](#modeles)
5. [Principaux choix d'architecture](#architecture)
6. [Sécurité et Permissions](#securite)
7. [Tests et Qualité](#tests)
8. [Annexes](#annexes)

---

## 1. Introduction et objectifs <a name="introduction"></a>
Ce document synthétise la feuille de route technique du projet GMAO, pour garantir une vision claire et partagée de l'évolution fonctionnelle et technique.

## 2. Phases de développement <a name="phases"></a>
- **Phase 8** : Compteurs & Maintenance Conditionnelle
- **Phase 9** : Gestion Documentaire
- **Phase 10** : Analyse Pannes & Alertes
- **Phase 11** : Gestion Financière & Coûts
- **Phase 12** : Reporting & Dashboards
- **Phase 13** : Logs d'Audit
- **Phase 14** : Permissions & Rôles avancés
- **Phase 15+** : UI/UX, Optimisations, Packaging, Intégrations

## 3. Synthèse technique par phase <a name="synthese"></a>
### Phase 8 : Compteurs & Maintenance Conditionnelle
- Gestion des compteurs (création, édition, suppression)
- Historique des relevés
- Déclenchement automatique d'OT si seuil atteint (alerte ou OT préventif)
- UI : Saisie relevé, visualisation historique, alertes
- Modèles : Compteur, HistoriqueCompteur, RègleDéclenchement

### Phase 9 : Gestion Documentaire
- Modèle Document (fichier, type, date, description...)
- Tables de liaison (Document <-> OT, Machine, etc.)
- UI : Upload, consultation, suppression, lien avec objets métier

### Phase 10 : Analyse Pannes & Alertes
- ✅ Génération d'alertes automatique sur deux seuils implémentée
- Statistiques sur pannes (par machine, type, cause...) - reporté ultérieurement (données insuffisantes)
- Génération de rapports de fiabilité - prévu pour une version ultérieure
- UI : Tableaux et filtres d'analyse - à développer avec plus de données

### Phase 11 : Gestion Financière & Coûts
#### Système de calcul des coûts d'intervention (✅ Implémenté)

**Structure mise en place**
Pour permettre un calcul précis des coûts d'intervention, le système considère plusieurs sources de coûts :

1. **Main d'œuvre** (✅ Implémenté)
   - Le technicien assigné à l'OT est le responsable de l'intervention
   - Possibilité d'avoir plusieurs intervenants (internes ou externes) sous sa supervision
   - Chaque intervenant a un temps passé et un coût horaire spécifique

2. **Pièces et matériel** (✅ Implémenté)
   - Pièces provenant du stock interne (valorisées au prix d'achat ou moyen pondéré)
   - Pièces provenant de sources externes (achat direct pour l'intervention)
   - Traçabilité des coûts par source d'approvisionnement

3. **Frais additionnels** (✅ Implémenté)
   - Centre de frais pour coûts indéfinis/divers
   - Description et montant pour chaque frais additionnel

**Modèles de données implémentés**
- Table MAINTENANCE_INTERVENANT : lien intervenant-maintenance avec temps passé
- Table MAINTENANCE_FRAIS_EXTERNE : pour pièces hors stock et frais divers
- Champs additionnels dans MAINTENANCE pour totaux calculés:
  - cout_main_oeuvre: Somme des coûts des intervenants
  - cout_pieces_internes: Somme des coûts des pièces du stock
  - cout_pieces_externes: Somme des frais externes de type 'PIECE_EXTERNE'
  - cout_autres_frais: Autres frais
  - cout_total: Somme de tous les coûts

**Calcul du coût total** (✅ Implémenté)
Coût Total = Σ(Coût Main d'œuvre) + Σ(Coût Pièces internes) + Σ(Coût Pièces externes) + Σ(Frais additionnels)

**Interface utilisateur** (✅ Implémenté)
- Ajout de sections dans le rapport d'intervention pour saisir les intervenants et frais
- Récapitulatif financier dans les détails de maintenance
- Calcul automatique des coûts lors de l'ajout/modification des intervenants et frais

**Considérations techniques**
- Conservation de l'historique des prix pour analyse rétrospective (⏳ Planifié)
- Mise en place d'un système de validation des coûts pour contrôle (⏳ Planifié)
- Export des données financières vers systèmes comptables (🔜 Future évolution)

Cette structure permet une analyse fine des coûts et une valorisation précise des interventions tout en s'adaptant à la réalité opérationnelle où le technicien responsable peut faire appel à diverses ressources pour compléter une intervention.

- V1 : ✅ Saisie manuelle des coûts (OT, pièces, MO)
- V2 : ⏳ Calculs automatiques avancés (valorisation, marges, historiques)

### Phase 12 : Reporting & Dashboards
- Rapports personnalisés (PDF, Excel...)
- Dashboards dynamiques (KPI, graphiques)

### Phase 13 : Logs d'Audit
- Traçabilité des actions utilisateurs (CRUD, connexions, exports...)
- Stockage sécurisé, consultation filtrée

### Phase 14 : Permissions & Rôles avancés
- Gestion fine des droits (par écran, action, objet)
- UI d'administration des rôles
- Sécurité renforcée (audit, logs)

### Phase 15+ : UI/UX, Optimisations, Packaging, Intégrations
- Améliorations ergonomiques, performances, packaging (exécutable), API, intégrations externes

## 4. Modèles de données clés <a name="modeles"></a>
- **Compteur** : id, machine_id, nom, unite, valeur_actuelle, seuil_alerte, seuil_prev_ot, actif, ...
- **HistoriqueCompteur** : id, compteur_id, date_releve, valeur, utilisateur_id, maintenance_id
- **Document** : id, chemin, type, date, description, ...
- **RègleDéclenchement** : id, compteur_id, seuil, type_declenchement, action (alerte/OT), actif
- **LogAudit** : id, user_id, action, date, cible, details
- **Coût** : id, ot_id, type, montant, date, commentaire

## 5. Principaux choix d'architecture <a name="architecture"></a>
- Architecture MVC (séparation UI, services métier, accès données)
- Services métiers réutilisables, injection de dépendances
- UI modulaire (dialogs, vues)
- Base de données SQLite (dev), évolutive vers PostgreSQL/MySQL (prod)
- Logging centralisé, gestion des exceptions

## 6. Sécurité et Permissions <a name="securite"></a>
- Authentification centralisée (login/password, rôles)
- Permissions par rôle, écran, action
- Logs d'audit complets
- Protection des données sensibles

## 7. Tests et Qualité <a name="tests"></a>
- Tests unitaires (services, modèles)
- Tests d'intégration (UI, DB)
- Procédures de recette et validation utilisateur

## 8. Annexes <a name="annexes"></a>
- Diagrammes UML (modèles, séquences)
- Exemples d'écrans/UI
- Exemples de requêtes SQL

---

**Ce document est évolutif : chaque phase sera détaillée au fil de l’implémentation.**

Pour chaque phase, il sera possible d’ajouter :
- Diagrammes de classes/relations
- Cas d’usage détaillés
- Spécifications techniques ou fonctionnelles
- Checklist de validation

*À jour au : 2025-04-20*

Voici un plan d’action simplifié pour migrer de SQLite3 vers PostgreSQL, en tenant compte que vous pouvez vider les tables :

Analyse de l’existant
Identifier tous les fichiers utilisant sqlite3 (connexion, requêtes, initialisation, etc.).
Préparation de l’environnement PostgreSQL
Installer PostgreSQL Server.
Créer une base de données vide.
Installer le driver Python pour PostgreSQL (psycopg2).
Migration du schéma
Exporter le schéma SQLite.
Adapter le schéma au format PostgreSQL (types de données, auto-increment, contraintes).
Créer les tables dans PostgreSQL (pas besoin de migrer les données).
Refactorisation du code Python
Remplacer les imports sqlite3 par psycopg2.
Adapter la chaîne de connexion.
Adapter les requêtes SQL si nécessaire (syntaxe, placeholders, types).
Modifier la gestion des transactions et exceptions si besoin.
Mise à jour de la configuration
Modifier les fichiers de configuration pour stocker les paramètres PostgreSQL.
Tests et validation
Tester toutes les fonctionnalités utilisant la base de données.
On va commencer par l’identification des fichiers utilisant sqlite3 dans votre projet ?


Voilà c'est fait db : gmao_industrie_data // user gmao_app_user :: password  mot_de_passe_fort

OK c'est fait