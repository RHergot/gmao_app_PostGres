# Machine KPI Dialog - Version Améliorée

## 🚀 Nouvelles Fonctionnalités

### 🎨 Interface Moderne
- **Design Material-like** avec couleurs cohérentes
- **Cartes de métriques visuelles** avec icônes et animations
- **Thème sombre/clair** adaptatif
- **Transitions fluides** et animations d'interface

### 🔍 Filtres Avancés
- **Recherche textuelle** en temps réel
- **Filtres multiples** (type, statut, criticité)
- **Slider de limitation** des résultats
- **Checkbox pour machines critiques** uniquement
- **Filtres en cascade** avec mise à jour automatique

### 📊 Visualisation des Données
- **Cartes de métriques** avec indicateurs colorés :
  - 🏭 Total des machines
  - ✅ Machines actives
  - ⚠️ Machines critiques
  - 💰 Coût total
  - 📊 Coût moyen
  - ⚡ Efficacité maintenance

### 📈 Tableau Amélioré
- **12 colonnes détaillées** au lieu de 10
- **Formatage conditionnel** des celleurs (statuts colorés)
- **Tri multi-critères** configurable
- **Double-clic** pour détails machine
- **Sélection visuelle** améliorée

### 📤 Export Multiple
- **Excel** (.xlsx) avec formatage
- **CSV** (.csv) avec encodage UTF-8
- **PDF** (en développement)
- **Données filtrées** uniquement

### ⚡ Performance
- **Chargement asynchrone** des données
- **Filtrage optimisé** avec délais
- **Cache intelligent** des résultats
- **Pagination** automatique

## 🛠️ Structure Technique

### Nouvelles Méthodes

#### Interface
- `setup_modern_style()` - Configuration du thème moderne
- `create_metric_card()` - Création des cartes visuelles
- `create_metrics_cards()` - Génération de toutes les cartes
- `create_overview_tab()` - Onglet principal amélioré
- `create_performance_tab()` - Onglet de performance
- `create_details_tab()` - Onglet de détails techniques

#### Filtrage
- `on_search_changed()` - Gestion de la recherche
- `on_limit_changed()` - Gestion de la limite de résultats
- `_update_dependent_filters()` - Mise à jour des filtres dépendants
- `_sort_data()` - Tri intelligent des données

#### Affichage
- `update_metrics_cards()` - Mise à jour des cartes
- `_update_card_value()` - Animation des valeurs
- `_update_selection_stats()` - Statistiques de sélection
- `show_machine_details()` - Popup de détails

#### Export
- `export_data(format_type)` - Export multi-format
- Support pandas pour Excel/CSV

## 📋 Colonnes du Tableau

| Colonne | Description | Type |
|---------|-------------|------|
| Machine | Nom de la machine | Texte |
| Type | Type/Catégorie | Texte |
| Statut | État actuel | Coloré |
| Coût Total | Coût cumulé (€) | Numérique |
| Interventions | Nombre total | Numérique |
| Préventif | Interventions préventives | Numérique |
| Correctif | Interventions correctives | Numérique |
| Urgence | Interventions d'urgence | Numérique |
| Temps Total | Durée cumulative (h) | Numérique |
| Dernière Maint. | Date dernière intervention | Date |
| Criticité | Niveau de criticité | Texte |
| Ratio P/C | Ratio Préventif/Correctif | Numérique |

## 🎯 Indicateurs de Performance

### Cartes de Métriques
1. **🏭 Total Machines** - Nombre de machines analysées
2. **✅ Machines Actives** - Machines avec interventions récentes
3. **⚠️ Machines Critiques** - Machines nécessitant attention
4. **💰 Coût Total** - Somme des coûts de maintenance
5. **📊 Coût Moyen** - Coût moyen par machine
6. **⚡ Efficacité** - Pourcentage d'interventions préventives

### Statistiques de Sélection
- Résumé dynamique selon les filtres appliqués
- Calculs en temps réel des moyennes
- Indicateurs de performance globale

## 🔧 Installation et Utilisation

### Prérequis
```bash
pip install PySide6 pandas
```

### Test de l'Interface
```bash
python test_machine_kpi_dialog.py
```

### Intégration
```python
from app.ui.kpi.dialogs.machine_kpi_dialog import MachineKPIDialog

dialog = MachineKPIDialog(parent)
dialog.exec()
```

## 🎨 Personnalisation

### Couleurs des Cartes
- **Bleu** (#3498db) - Informations générales
- **Vert** (#27ae60) - États positifs
- **Rouge** (#e74c3c) - Alertes/Critiques
- **Orange** (#f39c12) - Coûts
- **Violet** (#9b59b6) - Moyennes
- **Turquoise** (#1abc9c) - Performance

### Styles CSS
Le style moderne utilise :
- Bordures arrondies (8px)
- Ombres subtiles
- Gradients pour les cartes
- Couleurs cohérentes Material Design

## 📈 Améliorations Futures

### Version 2.0
- [ ] Graphiques interactifs (matplotlib/plotly)
- [ ] Drill-down par machine
- [ ] Alertes configurables
- [ ] Tableaux de bord personnalisables

### Version 2.1
- [ ] Export PDF formaté
- [ ] Rapports automatisés
- [ ] Intégration email
- [ ] API REST pour données externes

## 🐛 Débogage

### Logs
- Utilisation du logger `machine_kpi_dialog`
- Niveaux : DEBUG, INFO, WARNING, ERROR
- Fichiers de log rotatifs

### Tests
- Données de test générées automatiquement
- 50 machines simulées avec données réalistes
- Tests de performance avec gros volumes

## 📞 Support

Pour toute question ou suggestion d'amélioration :
- Créer une issue dans le projet
- Documenter les bugs avec captures d'écran
- Proposer des améliorations UX/UI
