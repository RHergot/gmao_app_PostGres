# Procédure de Gestion Git avec les Branches `develop` et `main`

Ce document décrit le flux de travail (workflow) Git pour le développement et le déploiement de l'application GMAO. L'objectif est de maintenir une branche `main` stable et de travailler sur une branche de développement `develop`.

## Principes des Branches

1.  **`main`** :
    *   Cette branche représente l'état **stable** et **en production** de l'application.
    *   On ne `commit` jamais directement sur `main`.
    *   Elle est mise à jour **uniquement** par des fusions (merges) depuis la branche `develop`.
    *   Le serveur de production se synchronise exclusivement avec cette branche.

2.  **`develop`** :
    *   C'est la branche de **développement principale**.
    *   Tout le nouveau code, les nouvelles fonctionnalités et les corrections sont intégrés ici.
    *   C'est la branche par défaut pour le travail quotidien.

---

## Workflow de Développement (Travail Quotidien)

Cette procédure est à suivre chaque jour pour développer de nouvelles fonctionnalités ou corriger des bugs.

**Étape 1 : Se mettre à jour**

Avant de commencer à travailler, assurez-vous que votre branche `develop` locale est à jour avec le dépôt distant.

```bash
# Assurez-vous d'être sur la branche develop
git checkout develop

# Récupérez les dernières modifications
git pull origin develop
```

**Étape 2 : Travailler sur le code**

Modifiez les fichiers, ajoutez-en de nouveaux, etc.

**Étape 3 : Sauvegarder les modifications (Commit)**

Une fois que vous avez terminé une tâche ou une modification cohérente, sauvegardez votre travail.

```bash
# Ajoutez les fichiers modifiés pour le commit
git add .

# Créez un commit avec un message descriptif
git commit -m "feat: Ajout de la fonctionnalité X"
# ou "fix: Correction du bug sur Y"
```

**Étape 4 : Pousser les modifications (Push)**

Partagez votre travail avec le reste de l'équipe en le poussant sur le dépôt distant.

```bash
git push origin develop
```

---

## Workflow de Mise en Production (Déploiement)

Lorsque les fonctionnalités sur la branche `develop` sont stables, testées et prêtes à être déployées, il est temps de les fusionner dans `main`.

**Étape 1 : Préparer la fusion**

Assurez-vous que votre branche `main` locale est à jour.

```bash
# Passez sur la branche main
git checkout main

# Récupérez les dernières modifications de main (sécurité)
git pull origin main
```

**Étape 2 : Fusionner `develop` dans `main`**

Intégrez toutes les modifications de `develop` dans `main`.

```bash
# Fusionne la branche 'develop' dans la branche actuelle ('main')
git merge develop
```

**Étape 3 : Pousser la nouvelle version de `main`**

Mettez à jour la branche `main` sur le dépôt distant. C'est cette action qui déclenchera la mise à jour en production.

```bash
git push origin main
```

---

## Procédure sur le Serveur de Production

Pour mettre à jour l'application sur le serveur de production, il suffit d'exécuter la commande suivante dans le dossier du projet :

```bash
# Récupère et applique les dernières modifications de la branche main
git pull origin main