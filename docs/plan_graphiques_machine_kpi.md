# Plan d'Implémentation - Onglet Graphiques Machine KPI

## Objectif
Refactoriser l'onglet "Graphiques & Tendances" pour créer une interface épurée et fonctionnelle avec un seul graphique unifié.

## Fonctionnalités Requises

### 1. Filtres Simplifiés
- **Filtre par Site** (dropdown) - RÉINTRODUIT
- **Filtre par Machine** (dropdown) 
- **Filtre par Type de Machine** (dropdown)
- ⚠️ **Suppression** des autres filtres complexes

### 2. Graphique Unifié
- **Données affichées** : Coûts (€) + Nombre d'interventions
- **Double axe Y** : 
  - Axe gauche : Coûts en euros
  - Axe droit : Nombre d'interventions
- **Légende claire** pour distinguer les deux métriques

### 3. Contrôles de Périodicité
- **Sélecteur de période** : 
  - Par jour (entre 2 dates)
  - Par semaine (entre 2 dates)
  - Par mois (entre 2 dates)
- **Sélecteur de dates** : Date début + Date fin

### 4. Type de Visualisation
- **Mode Barres** : Histogramme/Rectangles
- **Mode Courbes** : Lignes avec liaison entre points
- **Bouton de basculement** entre les deux modes

### 5. Support Multilingue
- **Langues supportées** : Français, Anglais, Allemand
- **Langue par défaut** : Anglais
- **Traductions** : Tous les textes de l'interface

## Architecture Technique

### Fichiers à Créer
1. `machine_kpi_chart_widget.py` - Widget graphique spécialisé
2. `machine_kpi_chart_translations.py` - Traductions spécifiques

### Fichiers à Modifier
1. `machine_kpi_dialog.py` - Refactorisation onglet graphiques
2. `machine_kpi_styles.py` - Styles pour le nouveau widget

## Étapes d'Implémentation

### Phase 1 : Préparation
- [x] Créer le plan détaillé
- [x] Créer les traductions multilingues
- [x] Créer le widget graphique de base

### Phase 2 : Interface Utilisateur
- [x] Créer les filtres (Site, Machine, Type)
- [x] Créer les contrôles de périodicité
- [x] Créer le sélecteur de visualisation

### Phase 3 : Graphique
- [x] Implémenter le graphique en mode barres
- [x] Implémenter le graphique en mode courbes
- [x] Gérer les doubles axes Y

### Phase 4 : Intégration
- [x] Intégrer le widget dans l'onglet graphiques
- [x] Connecter les filtres aux données
- [ ] Tester les différents modes

### Phase 5 : Finalisation
- [x] Tests multilingues (Anglais par défaut)
- [ ] Optimisation des performances
- [ ] Documentation utilisateur

## Spécifications Techniques

### Données d'Entrée
```python
chart_data = {
    'periods': ['2024-01', '2024-02', ...],  # Périodes selon granularité
    'costs': [1200.50, 1350.75, ...],       # Coûts par période
    'interventions': [5, 7, ...],           # Nombre d'interventions par période
    'machine_name': 'Machine ABC',          # Nom de la machine filtrée
    'site_name': 'Site XYZ',                # Nom du site filtré
    'type_name': 'Type DEF'                 # Type de machine filtré
}
```

### Configuration Graphique
```python
chart_config = {
    'chart_type': 'bars',  # 'bars' ou 'lines'
    'period_type': 'monthly',  # 'daily', 'weekly', 'monthly'
    'start_date': '2024-01-01',
    'end_date': '2024-12-31',
    'colors': {
        'costs': '#3498db',
        'interventions': '#e74c3c'
    }
}
```

## Notes d'Implémentation

### Dépendances
- `matplotlib` ou `plotly` pour les graphiques
- `pandas` pour la manipulation des données
- `PySide6` pour l'interface

### Optimisations
- Cache des données pour éviter les requêtes répétées
- Mise à jour incrémentale des graphiques
- Gestion des grandes quantités de données

### Gestion d'Erreurs
- Validation des plages de dates
- Gestion des données manquantes
- Messages d'erreur traduits

## Traductions Clés

### Français (par défaut actuel)
- "Graphiques & Tendances"
- "Filtrer par Site"
- "Coûts et Interventions"
- "Par jour / Par semaine / Par mois"
- "Barres / Courbes"

### Anglais (nouvelle langue par défaut)
- "Charts & Trends"
- "Filter by Site"
- "Costs and Interventions"
- "Daily / Weekly / Monthly"
- "Bars / Lines"

### Allemand
- "Diagramme & Trends"
- "Nach Standort filtern"
- "Kosten und Interventionen"
- "Täglich / Wöchentlich / Monatlich"
- "Balken / Linien"

---

**Statut**: Implémentation terminée - Phase de test
**Dernière mise à jour**: 2025-07-08

## Fichiers Créés/Modifiés

### Nouveaux Fichiers
1. `docs/plan_graphiques_machine_kpi.md` - Plan d'implémentation
2. `app/ui/kpi/dialogs/machine_kpi_chart_translations.py` - Traductions spécifiques
3. `app/ui/kpi/dialogs/machine_kpi_chart_widget.py` - Widget graphique spécialisé

### Fichiers Modifiés
1. `app/ui/kpi/dialogs/machine_kpi_dialog.py` - Intégration du nouveau widget graphique

## Points Clés de l'Implémentation

✅ **Interface épurée** avec filtres simplifiés (Site, Machine, Type)
✅ **Graphique unifié** coûts + interventions avec double axe Y
✅ **Contrôles de périodicité** (jour/semaine/mois) avec sélection de dates
✅ **Modes de visualisation** (barres/courbes) avec basculement
✅ **Support multilingue** avec anglais par défaut
✅ **Architecture modulaire** avec widget réutilisable

## Prochaines Étapes

1. **Test des fonctionnalités** - Vérifier tous les modes de graphique
2. **Optimisation** - Performance avec de gros volumes de données
3. **Documentation utilisateur** - Guide d'utilisation des graphiques
