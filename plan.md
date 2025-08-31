# Overview Page Refactoring Plan

## Notes
- L'utilisateur souhaite déplacer l'entête Analyse Period, Filtre Machine, Machine Type et Filtres Avancés dans le cadre de Overview.
- Les boutons Refresh et Export doivent aussi migrer dans Overview.
- La méthode add_specific_filters a été supprimée/rendue vide, les filtres sont désormais intégrés dans l'onglet Overview.
- Correction de la duplication de la section Language.ENGLISH dans le dictionnaire de traductions.
- L'utilisateur souhaite désormais que les trois cadres de filtres (période, machine, type/filtres avancés) soient alignés sur une seule ligne dans l'onglet Overview.
- L'utilisateur demande de supprimer le suffixe _label dans les libellés de statistiques affichés pour ne pas masquer la valeur du calcul.
- ✅ Mission Overview UI accomplie : interface ergonomique, fonctionnelle, code nettoyé et validé.
- L'utilisateur s'interroge sur la pertinence de garder la vue Site si un filtre Site est ajouté à la vue Machine (possibilité de fusionner ou simplifier).
- L'utilisateur souhaite ajouter un filtre Site dans le cadre "Machine Type" (qui sera renommé "Machine Type Sites") de l'onglet Overview, ce filtre existant déjà dans l'onglet Graphiques.
- ✅ Problème de boucle infinie corrigé après l'ajout du filtre Site.
- Nouvelle demande utilisateur : ajout d'un filtre "Équipe" dans Overview. Ce filtre nécessite de lier les OTs (technicien affecté) à la table Technicien pour retrouver l'équipe correspondante. Réflexion en cours sur la meilleure stratégie (jointure dynamique, index, ou cache en mémoire).
- ⚠️ Pour le filtre Équipe, il faut utiliser uniquement le technicien assigné dans l'Ordre de Travail (OT) (champ technicien_assigne_id), pas les intervenants de la table maintenance.
- ✅ Validation utilisateur : la règle d'association équipe/OT n'est pas inscrite en dur dans la base, la logique métier est appliquée côté service/KPI.
- ✅ Intégration du filtre "Équipe" dans l'UI Overview et la logique de filtrage (filtrage côté service KPI, centralisation via apply_filters_and_update_views).
- ✅ Suppression de la méthode update_chart_data, la mise à jour graphique est désormais centralisée.
- ✅ Intégration de KPIService dans l'initialisation de l'application (main.py) : import, instanciation, injection dans MainWindow.
- 🆕 Pour le filtre "Équipe" dans le dialog KPI Machine, il faut retrouver le technicien assigné dans chaque OT, puis faire une jointure avec la table Technicien pour obtenir l'équipe. L'information équipe n'est pas directement présente dans l'OT.
- 🔗 Structure de jointure pour filtre Équipe : ORDRE_TRAVAIL.technicien_assigne_id → TECHNICIEN.id_technicien → TECHNICIEN.equipe_id → EQUIPE.id_equipe
- 🐞 Bug actuel : le combo box "Équipe" se peuple, mais le filtrage ne fonctionne pas (tableau vide, combo box bloqué, nécessite un rafraîchissement).
- ✅ Correction appliquée : mapping du champ `equipe_nom` dans la conversion des données, correction des filtres côté UI, simplification de la requête SQL (filtrage équipe déplacé dans la sous-requête principale, cohérence période).
- 🆕 Nouvelle demande : intégrer le filtre "Équipe" dans l'onglet Graphiques (graph_kpi_tab).
- 🚩 Problème signalé : dans Overview, la sélection d'une machine affiche plusieurs lignes pour la même machine (3x à 5x). Une seule ligne par machine doit apparaître, avec tous les coûts agrégés. La requête est devenue trop complexe et doit être simplifiée/groupée correctement.
- ✅ Bug corrigé : la requête SQL de l'onglet Overview a été revue pour garantir qu'une seule ligne par machine est affichée (jointure équipe corrigée, agrégation correcte).

## Task List
- [x] Examiner la structure actuelle de la page Overview.
- [x] Déplacer tous les filtres et boutons mentionnés dans le cadre Overview.
- [x] Traduire tous les textes français restants en anglais (headers, labels, etc).
- [x] Vérifier que l'interface reste fonctionnelle et cohérente après modifications.
- [x] Aligner les trois cadres de filtres sur une seule ligne dans Overview.
- [x] Corriger les libellés de statistiques pour retirer le suffixe _label dans l'affichage des résultats.
- [x] Ajouter un filtre Site dans le cadre "Machine Type Sites" de l'onglet Overview (similaire à celui de l'onglet Graphiques).
- [x] Diagnostiquer et corriger la boucle infinie apparue après l'ajout du filtre Site.
- [x] Analyser la faisabilité et intégrer un filtre "Équipe" dans Overview (récupération des équipes via jointure entre OT (technicien_assigne_id) et Technicien).
- [x] Intégrer le filtre "Équipe" dans l'interface Overview et la logique de filtrage.
- [x] Implémenter la jointure côté service KPI pour filtrer par équipe dans le dialog KPI Machine
- [x] Ajouter le combo box "Équipe" dans l'UI du dialog KPI Machine
- [x] Gérer les dépendances et traductions du filtre équipe dans le dialog KPI Machine
- [x] Corriger le filtrage du tableau et le comportement du combo box équipe (éviter le blocage et l'affichage vide)
- [x] Ajouter le filtre "Équipe" dans l'onglet Graphiques (graph_kpi_tab)
- [x] Corriger la duplication des lignes machines dans Overview : simplifier la requête pour n'afficher qu'une seule ligne par machine avec tous les coûts agrégés

# Site KPI Refactoring Plan

## Notes
- Objectif : Éliminer tous les mocks et lire les données réelles dans la base de données.
- Le fichier app/data/schemas.py contient la structure des tables et relations.
- Prochaine étape : brancher la récupération des données KPI site sur la DB réelle.

## Task List
- [x] Supprimer les mocks dans le code KPI site et utiliser le service KPI réel.
- [x] Lire les données réelles depuis la base (en se basant sur schemas.py).
- [ ] Adapter les requêtes et la logique métier si besoin.
- [ ] Vérifier l'affichage et la cohérence des KPIs site avec données réelles.
- [ ] Analyser la pertinence de maintenir la vue Site si la vue Machine permet un filtrage efficace par site.

## Current Goal
Vérifier l'intégration finale et faire des tests UI.