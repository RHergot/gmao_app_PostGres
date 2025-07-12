
# Plan de Refonte du Module KPI

## Description fonctionnelle

### Synthèse de la démarche UI/technique (juillet 2025)

- Objectif : Se concentrer sur les coûts et interventions, en gardant la structure visuelle actuelle (Overview + Chart), mais avec un code modernisé et épuré.
- À faire :
  - Reprendre uniquement la partie affichage (tableau + chart) de l'ancien module (`app/ui/KPI/machine_kpi_dialog.py`), pour Overview et Graphiques.
  - Dans l’onglet Graphiques (Trends), ne garder que le mode Visualisation (Bar ou Lines).
  - S’inspirer du style si utile (`machine_kpi_styles.py`), mais ne pas hésiter à simplifier.
  - Repartir d’un nouveau script (ex : `machine_kpi_dialog_new.py`) pour éviter les dettes techniques.
  - Les données à afficher sont les coûts et interventions (tableau Overview actuel).
  - Utiliser le moins de code legacy possible, juste le strict nécessaire pour l’UI et la présentation des données.
- Étapes :
  1. Analyser l’affichage actuel (colonnes, graphiques, code UI utile).
  2. Créer un nouveau script dialog (squelette, UI moderne, Overview + Chart, filtres, boutons).
  3. Nettoyer l’onglet Graphiques (garder seulement Bar/Lines).
  4. Évaluer l’utilité du style.

---

La nouvelle page KPI propose une interface moderne et unifiée pour l’analyse des indicateurs de performance des machines. Elle se compose des éléments suivants :

1. **Sélection de la période**
   - Un cadre permet de choisir une date de début et une date de fin.
   - La logique doit empêcher la sélection d’une date de fin antérieure à la date de début.

2. **Filtres disponibles** (communs aux deux onglets)
   - **Par machine** : ComboBox pour sélectionner "Toutes les machines" ou une machine précise (données issues de la table `machine`).
   - **Par type de machine** : ComboBox pour "Tous les types" ou un type précis (table `type_machine`).
   - **Par équipe** : ComboBox pour "Toutes les équipes" ou une équipe précise (table `equipe`).
   - **Par site** : ComboBox pour "Tous les sites" ou un site précis (table `site`).

3. **Actions globales**
   - Bouton de fermeture de la page
   - Bouton de réinitialisation des filtres
   - Bouton d’export de la sélection

4. **Présentation des résultats**
   - **Onglet 1 : Overview**
     - Affiche la sélection filtrée dans un tableau.
   - **Onglet 2 : Graphiques**
     - Présente la même sélection sous forme de graphiques :
       - Graphique linéaire
       - Graphique en rectangles (barres)

---

## 1. Architecture cible

```text
kpi/
├── repositories/   # Accès SQL, extraction brute → DataFrame
│   └── kpi_repository.py
├── models/         # Dataclasses ou objets simples
│   └── kpi_models.py
├── services/       # Logique métier, filtrage, calculs (pandas)
│   └── kpi_service.py
├── ui/             # Dialogues, widgets, graphiques (PySide6, matplotlib)
│   └── machine_kpi_dialog.py
└── tests/          # Tests unitaires sur chaque couche
    └── test_kpi_service.py
```

---

## 2. Étapes du pipeline et jalons de test

### Étape 1 - [ ] Extraction SQL → DataFrame
- data base : app/data/schemas.py
- Écrire les requêtes SQL nécessaires (une ou plusieurs selon les besoins) : éviter les requêtes trop complexes et qui portent à des erreurs silencieuses
- Utiliser des requêtes paramétrées pour éviter les injections SQL, 
- on peut utiliser des requêtes préparées à tester sur pgAdmin
- Charger les résultats dans un DataFrame pandas : 
- OK il faut vérifier que les données sont correctes 
- et essayer autant que faire se peut de charger le backend avec les données brutes
- **Pause/Test :** Vérifier la cohérence des données extraites (affichage, shape, types)

### Étape 2 – [ ] Chaque fonction de filtrage/calcul pandas
- Implémenter chaque filtre (période, site, équipe, machine, type, préventif/correctif/urgence) comme fonction pandas
- Ajouter les agrégations/calculs nécessaires (`groupby`, `sum`, `mean`, etc.)
- **Pause/Test :** Pour chaque fonction de filtrage/calcul, écrire un test unitaire ou notebook de validation

### Étape 3 – [ ] Préparation des données pour l’UI
- Convertir les DataFrames filtrés en listes/dicts pour alimenter les tableaux (`QTableWidget`)
- Préparer les séries de données pour les graphiques (matplotlib)
- **Pause/Test :** Vérifier la compatibilité des formats avec l’UI (affichage, valeurs, labels)

### Étape 4 – [ ] Génération des graphiques (matplotlib)
- Créer les fonctions de génération de graphiques à partir des DataFrames filtrés
- Intégrer les graphiques dans l’UI (PySide6)
- **Pause/Test :** Vérifier l’affichage correct des tableaux, des graphiques pour différents jeux de filtres. Ne pas oublier les reset des graphiques et des tableaux !!!

### Étape 5 – [ ] Intégration MVC et indépendance
- S’assurer que la couche service (pandas) est totalement indépendante de l’UI
- Permettre l’exécution de la logique KPI en “stand-alone” (ex : script ou notebook)
- **Pause/Test :** Lancer la pipeline complète sans UI, valider les résultats

---

## 3. Bonnes pratiques

- **Documentation :** commenter chaque fonction clé, documenter le pipeline global
- **Tests :** écrire des tests unitaires pour chaque filtre/calcul
- **Modularité :** chaque couche (repo, service, ui) doit être indépendante
- **CRUD :** appliquer le principe CRUD pour les modèles métiers si besoin (création, lecture, mise à jour, suppression de KPI)
- **Prototypage rapide :** utiliser des notebooks Jupyter pour expérimenter et valider les fonctions pandas (filtrage, agrégations, graphiques)
- **Jeux de données de test :** prévoir un script ou des utilitaires pour importer/exporter des jeux de données de test (CSV, Excel, SQL dump)

---

## 4. Livrables attendus

- Arborescence de code propre et documentée
- Pipeline de traitement des KPI testable et exécutable en stand-alone
- UI ergonomique et découplée de la logique métier
- Jeux de tests unitaires et/ou notebooks de validation
- Exemples d’utilisation en mode script ou CLI (pour faciliter la prise en main hors UI)

---

## 5. Points de consolidation (pauses/test)

- [x] Après extraction SQL → DataFrame
- [ ] Après chaque fonction de filtrage/calcul pandas
- [ ] Après préparation des données pour l’UI
- [ ] Après génération des graphiques (matplotlib)
- [ ] Après intégration des tableaux

---
Après intégration complète MVC veuiller à ce que le .venv soit bien activé dans app\ et accessible par KPI

---

## Points d’amélioration ou de vigilance

- **Gestion des erreurs SQL** :
  - Prévoyez une gestion explicite des exceptions lors de l’extraction SQL pour éviter les erreurs silencieuses.

- **Performance** :
  - Sur de gros volumes, surveillez l’impact mémoire des DataFrames et privilégiez des extractions paginées si besoin.

- **Tests automatisés** :
  - Intégrez une exécution automatique des tests (CI) pour valider chaque push.

- **Activation de l’environnement virtuel** :
  - Pensez à fournir un script ou une documentation claire pour l’activation du .venv, surtout si le module KPI doit être utilisé dans différents contextes (app, script, notebook).
