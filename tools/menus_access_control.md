# Table des droits d'accès aux menus (GMAO)

Ce fichier sert de référence collaborative pour définir et modifier les droits d'accès aux différents menus de l'application. **Modifiez-le librement lors des évolutions du projet.**

| Menu                        | Admin | Responsable | Technicien | Gestionnaire Stock | Lecteur |
|-----------------------------|:-----:|:-----------:|:----------:|:------------------:|:-------:|
| Gérer les Utilisateurs      |  OK   |     OK      |    NOK     |        NOK         |   NOK   |
| Gérer les OTs               |  OK   |     OK      |    OK      |        NOK         |   NOK   |
| Gérer les pièces détachées  |  OK   |     OK      |    OK      |        OK          |   OK    |
| Gérer les Machines          |  OK   |     OK      |    NOK     |        NOK         |   NOK   |
| Gérer le Stock              |  OK   |     OK      |    NOK     |        OK          |   NOK   |
| Gérer les fournisseurs      |  OK   |     OK      |    OK      |        OK          |   OK    |

| Configuration               |  OK   |     OK      |    NOK     |        NOK         |   NOK   |
| Gérer Games d'entretien     |  OK   |     OK      |    NOK     |        NOK         |   NOK   |
| Gérer Commandes             |  OK   |     OK      |    NOK     |        OK          |   NOK   |



**Règle générale :**
- Les menus non accessibles selon le rôle sont **masqués** dans l'interface.
- Pour toute modification ou ajout de menu, éditez ce fichier.

---

## Historique des modifications
- 2025-04-23 : Création initiale (Cascade & utilisateur)

---

> **Astuce :** Pour les développeurs, ce fichier peut être utilisé comme source unique de vérité pour automatiser le contrôle d'accès dans le code (par parsing YAML/Markdown ou conversion en table de droits).
