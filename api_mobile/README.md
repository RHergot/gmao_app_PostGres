# API Mobile pour GMAO

Ce projet est une application Django qui fournit une API RESTful et une interface web pour une application de Gestion de la Maintenance Assistée par Ordinateur (GMAO).

L'objectif est de permettre aux techniciens de maintenance de recevoir leurs ordres de travail et de soumettre leurs rapports d'intervention depuis une interface web simple et responsive.

## Architecture

Le projet est structuré en plusieurs applications Django :

-   `gmao_api`: Le cœur de l'application Django, contient les configurations globales (`settings.py`, `urls.py`).
-   `mobile_api`: **(Application principale)** Définit les modèles de données (OT, Techniciens, Pièces, etc.) et expose l'API RESTful principale pour les clients mobiles ou externes.
-   `gmao_web`: Fournit une interface web pour les techniciens. Elle consomme l'API de `mobile_api` et ne possède pas ses propres modèles de données.
-   `web_interface` / `web_ui`: (Rôle à clarifier, semblent redondants avec `gmao_web`).

## Prérequis

-   Python 3.10+ (vérifier la version avec `python --version`)
-   PostgreSQL (ou un autre moteur de base de données compatible avec Django)

## Installation

1.  **Cloner le projet :**

    ```bash
    git clone <URL_DU_PROJET>
    cd api_mobile
    ```

2.  **Créer un environnement virtuel :**

    ```bash
    python -m venv .venv
    ```

3.  **Activer l'environnement virtuel :**

    -   **Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Installer les dépendances :**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Créer un fichier `.env`** à la racine du projet en vous basant sur le modèle ci-dessous. Ce fichier contiendra les informations sensibles.

    ```env
    # Fichier .env.example

    # Clé secrète de Django (générez une nouvelle clé pour la production)
    SECRET_KEY='votre_super_cle_secrete_ici'

    # Configuration de la base de données (exemple pour PostgreSQL)
    DB_NAME='gmao_db'
    DB_USER='gmao_user'
    DB_PASSWORD='votre_mot_de_passe_db'
    DB_HOST='localhost'
    DB_PORT='5432'

    # Mode débogage (Mettre à False en production)
    DEBUG=True

    # Hôtes autorisés (séparés par une virgule)
    ALLOWED_HOSTS='127.0.0.1,localhost'
    ```

2.  **Appliquer les migrations** pour créer le schéma de la base de données :

    ```bash
    python manage.py migrate
    ```

## Utilisation

-   **Lancer le serveur de développement :**

    ```bash
    python manage.py runserver
    ```

    L'application sera accessible à l'adresse `http://127.0.0.1:8000`.

-   **Créer un superutilisateur** pour accéder à l'interface d'administration de Django :

    ```bash
    python manage.py createsuperuser
    ```

## Qualité du code

Ce projet utilise `black` pour le formatage du code et `flake8` pour le linting.

-   **Formater le code :**

    ```bash
    black .
    ```

-   **Vérifier les erreurs de style :**

    ```bash
    flake8 .
    ```
