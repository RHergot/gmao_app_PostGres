# Documentation Technique - Application GMAO

## 1. Introduction

Cette application est un système de Gestion de la Maintenance Assistée par Ordinateur (GMAO) conçu pour un environnement industriel. Elle permet de gérer les équipements, la maintenance préventive et corrective, les techniciens, les pièces de rechange et les ordres de travail.

**Technologies utilisées :**

*   **Langage :** Python 3.x
*   **Interface Graphique :** PySide6 (bindings Python pour Qt 6)
*   **Base de Données :** SQLite (via le module `sqlite3` de Python)
*   **Configuration :** Fichiers `.env` (via `python-dotenv`)
*   **Gestion des dépendances :** `requirements.txt`

## 2. Architecture

L'application adopte une architecture en couches pour séparer les responsabilités et améliorer la maintenabilité :

*   **`app/ui/` (Couche Présentation) :** Contient toutes les classes relatives à l'interface utilisateur (fenêtres, dialogues, widgets personnalisés). Elle interagit avec la couche Core pour afficher les données et déclencher les actions utilisateur.
*   **`app/core/` (Couche Métier/Services) :** Renferme la logique métier de l'application. Les `Services` orchestrent les opérations, valident les données et communiquent avec la couche Data. Ils sont injectés dans la couche UI.
*   **`app/data/` (Couche Accès aux Données) :** Responsable de la communication avec la base de données. Elle comprend :
    *   `database.py` : Gestion de la connexion et initialisation de la base de données.
    *   `repositories/` : Contient les `Repositories`, qui encapsulent les requêtes SQL (ou ORM) pour chaque entité métier (Utilisateur, Machine, OrdreTravail, etc.).
*   **`app/utils/` (Utilitaires) :** Modules transverses utilisés par les autres couches (ex: configuration du logging, fonctions d'aide).
*   **`main.py` (Point d'entrée) :** Initialise l'application, configure le logging, établit la connexion DB, instancie et injecte les dépendances (Repositories -> Services -> UI), et lance la boucle d'événements Qt.
*   **`config.py` :** Charge les paramètres de configuration depuis l'environnement ou le fichier `.env`.

## 3. Installation et Lancement

**Prérequis :**

*   Python 3.6 ou supérieur
*   `pip` (gestionnaire de paquets Python)

**Étapes :**

1.  **Cloner le dépôt** (si applicable) ou copier les fichiers du projet.
2.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    .\venv\Scripts\activate  # Windows
    ```
3.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configuration :** Créer un fichier `.env` à la racine du projet si des configurations spécifiques sont nécessaires (ex: chemin de la base de données différent). Voir la section Configuration ci-dessous. Par défaut, une base de données `gmao_data.db` sera utilisée/créée à la racine.
5.  **Lancer l'application :**
    ```bash
    python main.py
    ```

## 4. Configuration

La configuration est gérée par `config.py` qui lit les variables d'environnement. Un fichier `.env` à la racine du projet peut être utilisé pour définir ces variables localement.

**Variables principales :**

*   `DATABASE_TYPE` : Type de base de données (actuellement 'sqlite' uniquement supporté). *Valeur par défaut :* `sqlite`.
*   `DATABASE_PATH` : Chemin vers le fichier de base de données SQLite. *Valeur par défaut :* `./gmao_data.db` (relatif à la racine du projet).
*   `LOG_LEVEL` : Niveau de criticité des logs (DEBUG, INFO, WARNING, ERROR, CRITICAL). *Valeur par défaut :* `INFO`.

**Exemple de fichier `.env` :**

```dotenv
# .env
DATABASE_PATH=C:/Data/GMAO/production.db
LOG_LEVEL=DEBUG
```

## 5. Description des Modules Principaux

*   **`main.py`** : Orchestre le démarrage. Gère l'initialisation, l'injection des dépendances (Repositories, Services) dans `MainWindow` et lance l'application Qt.
*   **`config.py`** : Centralise la lecture des paramètres de configuration.
*   **`app/ui/main_window.py`** : Définit la fenêtre principale de l'application, ses menus, barres d'outils et la zone centrale où s'afficheront les différents modules (gestion des machines, OT, etc.). Reçoit les services nécessaires via son constructeur.
*   **`app/core/services/`** : Chaque fichier `.py` correspond généralement à un domaine métier (ex: `user_service.py`, `machine_service.py`, `maintenance_service.py`, `stock_service.py`, `preventive_service.py`). Ils contiennent la logique métier et utilisent les repositories pour accéder aux données.
*   **`app/data/repositories/`** : Chaque fichier `.py` implémente les opérations CRUD (Create, Read, Update, Delete) et autres requêtes spécifiques pour une entité de la base de données (ex: `user_repository.py`, `machine_repository.py`).
*   **`app/data/database.py`** : Contient les fonctions pour obtenir la connexion à la base de données (`get_connection`), la fermer (`close_connection`) et initialiser le schéma (`initialize_database`, qui crée les tables si elles n'existent pas).
*   **`app/utils/logging_config.py`** : Configure le système de logging de Python (format des messages, destination des logs - console/fichier).

## 6. Base de Données

L'application utilise une base de données SQLite. Le schéma est défini et initialisé dans `app/data/database.py` (`_create_tables` fonction interne).

**Tables principales (liste non exhaustive) :**

*   `utilisateurs`
*   `sites`
*   `fabricants`
*   `types_machines`
*   `machines`
*   `equipes`
*   `techniciens`
*   `ordres_travail`
*   `maintenances` (interventions)
*   `fournisseurs`
*   `pieces`
*   `interventions_pieces`
*   `mouvements_stock`
*   `gammes_entretien`
*   `gammes_etapes`
*   `gammes_pieces_types`

*(Pour un schéma détaillé, inspecter la fonction `_create_tables` dans `app/data/database.py`)*

---
*Documentation générée par Cascade le 2025-04-14.*
