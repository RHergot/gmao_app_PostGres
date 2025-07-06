# Plan to Fix "Gérer les OTS" Menu Disabled for Admin

## Notes
- User reports that in main_window.py, the menu item "Gérer les OTS" is disabled (grisé) despite the user being an admin.
- All other menus are accessible.
- User is currently focused on MainWindow.__init__.
- Menu access is controlled by can_access from access_control.py.
- MENU_RIGHTS allows "Gérer les OTs" for "Admin".
- Need to check if user_role is set and normalized correctly, and if can_access is called with correct parameters.
- The value of user_role (normalization, case, synonyms) and the parameters passed to can_access must be checked. Debug logs in create_actions can help trace the role used for menu access.
- Correction appliquée : normalisation du rôle et logs de debug ajoutés dans create_actions. Correction de l'import manquant de normalize_role.
- Problème finalement résolu : la corruption du fichier ot_view.py empêchait la création de la vue OT, d'où le menu grisé malgré des droits corrects. La restauration du fichier a tout rétabli.
- Transition : prochaine étape = fiabilisation/finalisation des vues KPI, en commençant par la vue machine (app/ui/kpi/dialog/machine_kpi_dialog.py et app/ui/kpi/widgets/kpi_dashboard_clean.py)
- Pour la vue KPI machine : 4 filtres affichés (période, machine, site, type). Il faut : retirer le filtre site, connecter aux données réelles de la DB au lieu des données de test, vérifier le calcul des coûts.
- Priorité utilisateur : si la base de données n’est pas accessible, aucune donnée ne doit être affichée, seulement un message d’erreur explicite.
- Problème identifié : depuis le menu principal, les données mock s'affichaient car le service KPI n'était pas injecté dans MachineKPIDialog. Correction proposée et appliquée dans main_window.py pour garantir l'accès aux vraies données DB.
- Nouvelle demande : supprimer toutes les entrées du menu KPI (MainWindow) sauf le Dashboard KPI pour éviter la redondance et simplifier l'accès.
- Suppression effective de tout le code mort lié aux anciennes vues KPI spécialisées (machines, sites, équipes, préventif, avancées) dans MainWindow : méthodes, actions, et références supprimées. Seule show_kpi_dashboard subsiste.
- Répertoire de travail confirmé par l'utilisateur : d:\Projets\gmao_app_PostGres\app
- Suppression des menus KPI spécialisés finalisée.

## Task List
- [x] Review how the enabled/disabled state of the "Gérer les OTS" menu is set in main_window.py.
- [x] Check the logic that determines admin status and menu access.
- [x] Verify user_role value and normalization for admin users.
- [x] Propose and implement a fix.
- [x] Identifier pourquoi le menu reste désactivé si le problème persiste malgré la normalisation et l'import.
- [x] Test to confirm the menu is enabled for admin users.
- [ ] Pour la vue KPI machine :
  - [x] Retirer le filtre "site"
  - [x] Corriger l'injection du service KPI réel dans MachineKPIDialog depuis le menu principal
  - [x] Supprimer toutes les entrées du menu KPI dans MainWindow sauf le Dashboard KPI
  - [x] Connecter les filtres/données à la base réelle (plus de mock)
    - [ ] Si la DB n’est pas accessible, afficher uniquement un message d’erreur (aucune donnée affichée)
  - [ ] Vérifier/corriger le calcul des coûts affichés

## Current Goal
Corriger les filtres et fiabiliser les données KPI machine.