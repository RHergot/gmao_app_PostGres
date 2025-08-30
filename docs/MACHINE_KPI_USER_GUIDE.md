# 🎯 Guide d'utilisation - Machine KPI Dialog v2.0

## 🚀 Lancement Rapide

### Option 1 : Test Simple
```bash
python test_machine_kpi_simple.py
```
- ✅ Interface autonome avec données de test
- 🔧 Aucune dépendance base de données
- 📊 50 machines simulées pour démonstration

### Option 2 : Test Complet  
```bash
python test_machine_kpi_dialog.py
```
- 🔗 Interface intégrée avec le système
- 🗄️ Connexion base de données requise
- 📈 Données réelles si disponibles

### Option 3 : Installation automatique
```bash
# Windows
install_machine_kpi_deps.bat
launch_machine_kpi_test.bat

# Linux/Mac  
chmod +x install_machine_kpi_deps.sh
./install_machine_kpi_deps.sh
python test_machine_kpi_simple.py
```

## 🎨 Nouvelles Fonctionnalités

### 📊 Cartes de Métriques Visuelles
- **🏭 Total Machines** - Nombre de machines analysées
- **✅ Machines Actives** - Machines avec activité récente
- **⚠️ Machines Critiques** - Machines nécessitant attention
- **💰 Coût Total** - Somme des coûts de maintenance
- **📊 Coût Moyen** - Coût moyen par machine
- **⚡ Efficacité** - Pourcentage d'interventions préventives

### 🔍 Filtres Avancés
```
🔍 Recherche Rapide    : Texte libre sur nom/type/série
⚙️ Type de Machine     : Filtrage par catégorie
🏭 Machine Spécifique  : Sélection d'une machine
🎚️ Statut            : Actif, Attention, Inactif
⚠️ Machines Critiques : Checkbox pour filtrage rapide
📊 Limite Résultats   : Slider 10-100 machines
```

### 📈 Tableau Enrichi (12 colonnes)
| # | Colonne | Description | Format |
|---|---------|-------------|--------|
| 1 | Machine | Nom de la machine | Texte |
| 2 | Type | Catégorie/Type | Texte |
| 3 | Statut | État actuel | Coloré |
| 4 | Coût Total | Coût cumulé | 1,234.56€ |
| 5 | Interventions | Nombre total | 42 |
| 6 | Préventif | Interventions préventives | 28 |
| 7 | Correctif | Interventions correctives | 12 |
| 8 | Urgence | Interventions d'urgence | 2 |
| 9 | Temps Total | Durée cumulative | 125.5h |
| 10 | Dernière Maint. | Date dernière intervention | YYYY-MM-DD |
| 11 | Criticité | Niveau de criticité | Standard/Élevée/Critique |
| 12 | Ratio P/C | Ratio Préventif/Correctif | 2.33 |

### 🎯 Interactions Utilisateur
- **Double-clic** sur une ligne → Popup détails machine
- **Tri configurable** → 6 critères de tri disponibles
- **Sélection multiple** → Statistiques de sélection temps réel
- **Recherche instantanée** → Délai 300ms pour performance

## 📤 Export des Données

### Formats Supportés
```python
# Excel (si pandas disponible)
export_data('excel')  # → machines_kpi_20250706_161423.xlsx

# CSV (natif Python)
export_data('csv')    # → machines_kpi_20250706_161423.csv

# Fallback automatique
# Excel → CSV si pandas absent
```

### Contenu Exporté
✅ Toutes les colonnes du tableau  
✅ Données filtrées uniquement  
✅ Métadonnées horodatées  
✅ Encodage UTF-8 pour CSV  
✅ Formatage Excel avec en-têtes  

## 🛠️ Intégration dans l'Application

### Import et Utilisation
```python
from app.ui.kpi.dialogs.machine_kpi_dialog import MachineKPIDialog

# Utilisation basique
dialog = MachineKPIDialog(parent_widget)
dialog.exec()

# Utilisation avec service KPI
dialog = MachineKPIDialog(parent_widget)
dialog.kpi_service = your_kpi_service_instance
dialog.load_data()  # Charge depuis la base
dialog.exec()

# Utilisation avec données personnalisées
dialog = MachineKPIDialog(parent_widget)
dialog.machines_data = your_custom_data
dialog.filtered_data = dialog.machines_data.copy()
dialog.update_initial_filters()
dialog.apply_filters_and_update_views()
dialog.exec()
```

### Format des Données
```python
# Structure attendue pour machines_data
machine_data = {
    "machine_name": "MACH_001",
    "serial": "SN123456",
    "type": "Tour CNC",
    "criticite": "Standard",
    "status": "Actif",  # Actif, Attention, Inactif
    
    # Coûts (float)
    "total_cost": 12500.50,
    "avg_cost": 850.25,
    "cout_main_oeuvre": 3500.00,
    "cout_pieces": 7200.00,
    "cout_frais_externes": 1800.50,
    
    # Interventions (int)  
    "interventions": 15,
    "preventif": 10,
    "correctif": 4,
    "urgence": 1,
    
    # Temps (float, heures)
    "total_intervention_time": 125.5,
    "avg_intervention_time": 8.4,
    
    # Ratios et pourcentages (float)
    "ratio_preventif_curatif": 2.5,
    "pourcentage_mod": 28.0,
    "pourcentage_pieces": 57.6,
    "pourcentage_frais_externes": 14.4,
    
    # Dates (string YYYY-MM-DD)
    "last_maintenance": "2024-11-15",
    "next_maintenance": "2025-02-15"
}
```

## 🎨 Personnalisation

### Modification des Couleurs
```python
# Fichier: machine_kpi_styles.py
CARD_COLORS = {
    'total_machines': "#your_color",
    'active_machines': "#your_color", 
    'critical_machines': "#your_color",
    'total_cost': "#your_color",
    'avg_cost': "#your_color",
    'efficiency': "#your_color"
}
```

### Ajout de Nouvelles Métriques
```python
# Dans create_metrics_cards()
self.custom_card = self.create_metric_card(
    "Votre Métrique", "--", "🎯", "#custom_color"
)
self.metrics_layout.addWidget(self.custom_card)

# Dans update_metrics_cards()
custom_value = calculate_custom_metric(self.filtered_data)
self._update_card_value(self.custom_card, f"{custom_value:.1f}")
```

### Modification des Traductions
```python
# Dans MACHINE_TRANSLATIONS
Language.FRENCH: {
    "your_key": "Votre texte français",
    # ...
}
```

## 🐛 Résolution de Problèmes

### Erreur "Import pandas could not be resolved"
```bash
# Solution 1: Installer pandas
pip install pandas openpyxl

# Solution 2: Utiliser seulement CSV
# L'interface utilise automatiquement CSV si pandas absent
```

### Erreur "Service KPI non initialisé"
```python
# Solution: Mock du service pour tests
class MockKPIService:
    def get_couts_par_machine(self, **kwargs):
        return []

dialog.kpi_service = MockKPIService()
```

### Interface ne s'affiche pas
```bash
# Vérifier PySide6
pip install PySide6

# Vérifier les imports
python -c "from app.ui.kpi.dialogs.machine_kpi_dialog import MachineKPIDialog; print('OK')"
```

### Données ne s'affichent pas
```python
# Vérifier le format des données
print(f"Données: {len(dialog.machines_data)} machines")
print(f"Filtrées: {len(dialog.filtered_data)} machines")

# Forcer la mise à jour
dialog.apply_filters_and_update_views()
```

## 📊 Métriques de Performance

### Capacités Testées
- ✅ **50 machines** - Interface fluide
- ✅ **Recherche temps réel** - Délai 300ms
- ✅ **Filtrage multiple** - 6 critères simultanés
- ✅ **Export rapide** - <2s pour 50 machines
- ✅ **Tri intelligent** - 6 colonnes configurables

### Limites Recommandées
- **Machines affichées** : 10-100 (configurable)
- **Recherche** : Délai 300ms pour éviter surcharge
- **Export** : Pas de limite technique (dépend mémoire)
- **Filtres** : Aucune limite sur critères multiples

## 🚀 Prochaines Évolutions

### Version 2.1 (Prévue)
- [ ] Graphiques matplotlib intégrés
- [ ] Export PDF formaté avec logos
- [ ] Drill-down par machine (historique détaillé)
- [ ] Alertes configurables par seuils

### Version 2.2 (Future)
- [ ] Dashboard personnalisable par utilisateur
- [ ] Rapports automatisés programmables
- [ ] API REST pour données externes
- [ ] Mode hors-ligne avec cache local

## 📞 Support et Contributions

### Feedback et Améliorations
- 🐛 **Bugs** : Créer une issue avec capture d'écran
- 💡 **Suggestions** : Proposer des améliorations UX/UI
- 🔧 **Développement** : Fork et pull request
- 📚 **Documentation** : Améliorer ce guide

### Contact
- **Fichiers de log** : Vérifier le niveau DEBUG
- **Tests unitaires** : Ajouter pour nouvelles fonctionnalités
- **Performance** : Profiler avec gros volumes de données

---

🎉 **La nouvelle interface Machine KPI Dialog v2.0 est prête !**  
✨ Interface moderne, fonctionnalités avancées, performance optimisée
