# 🎨 Phase 1.4 - Interface Utilisateur KPI Dashboard

## 🎯 Objectifs de la Phase 1.4

Créer une interface utilisateur moderne et intuitive pour visualiser et explorer les KPI financiers de la GMAO.

### Prérequis ✅ VALIDÉS
- ✅ KPIService opérationnel et testé
- ✅ 7 vues SQL fonctionnelles  
- ✅ Données réelles disponibles (6,850€ détectés)
- ✅ Backend stable et performant

---

## 📊 Composants UI à Développer

### 1. 🏠 Dashboard Principal (`KPIDashboard`)

**Fichier:** `app/ui/kpi/kpi_dashboard.py`

```python
class KPIDashboard(QWidget):
    """Widget principal du dashboard KPI financier"""
    def __init__(self):
        # Layout principal avec sidebar + zone de contenu
        # Sélecteur de centre de frais (machine, site, équipe)  
        # Sélecteur de période (mois, trimestre, année)
        # Zone d'affichage des widgets KPI
```

**Fonctionnalités:**
- [ ] Layout responsive avec sidebar de navigation
- [ ] Sélecteur de centre de frais (ComboBox)
- [ ] Sélecteur de période avec date picker
- [ ] Zone principale avec widgets KPI interchangeables
- [ ] Barre de statut avec résumé rapide

### 2. 📈 Widget Coûts par Machine (`MachineKPIWidget`)

**Fichier:** `app/ui/kpi/widgets/machine_kpi_widget.py`

```python
class MachineKPIWidget(QWidget):
    """Widget d'analyse des coûts par machine"""
    def load_data(self, periode_debut, periode_fin, site_id=None)
    def update_chart(self, data)
    def export_to_excel(self)
```

**Visualisations:**
- [ ] Graphique en barres : Top 10 machines coûteuses
- [ ] Tableau détaillé avec tri et filtre  
- [ ] Indicateur de tendance (↗️ ↘️)
- [ ] Bouton export Excel/CSV

### 3. 🏢 Widget Coûts par Site (`SiteKPIWidget`)

**Fichier:** `app/ui/kpi/widgets/site_kpi_widget.py`

**Visualisations:**
- [ ] Graphique en secteurs (camembert) : Répartition par site
- [ ] Carte géographique si coordonnées disponibles
- [ ] Tableau comparatif inter-sites
- [ ] Évolution mensuelle par site

### 4. 👥 Widget Coûts par Équipe (`EquipeKPIWidget`)

**Fichier:** `app/ui/kpi/widgets/equipe_kpi_widget.py`

**Visualisations:**
- [ ] Graphique en barres horizontales par équipe
- [ ] Métriques de productivité (coût/technicien, interventions/technicien)
- [ ] Comparaison des domaines d'expertise
- [ ] Heures totales vs coûts

### 5. 🔧 Widget Préventif vs Curatif (`PreventifCuratifWidget`)

**Fichier:** `app/ui/kpi/widgets/preventif_curatif_widget.py`

**Visualisations:**
- [ ] Graphique en secteurs : Ratio préventif/curatif
- [ ] Courbe d'évolution temporelle du ratio
- [ ] **Alerte visuelle** si ratio curatif > 80%
- [ ] Recommandations d'amélioration

### 6. 📊 Widget Résumé Global (`GlobalSummaryWidget`)

**Fichier:** `app/ui/kpi/widgets/global_summary_widget.py`

**Métriques clés:**
- [ ] Coût total période avec évolution
- [ ] Nombre d'interventions avec évolution  
- [ ] Coût moyen par intervention
- [ ] Nombre de machines actives
- [ ] **Indicateurs d'alerte** (dépassements, dérives)

### 7. 📈 Widget Tendances (`TrendsWidget`)

**Fichier:** `app/ui/kpi/widgets/trends_widget.py`

**Visualisations:**
- [ ] Graphique linéaire : Évolution des coûts sur 12 mois
- [ ] Sélection machine/site pour drill-down
- [ ] Moyennes mobiles (3 mois, 6 mois)
- [ ] Prédiction tendance (régression linéaire simple)

---

## 🎨 Design System

### Couleurs
```python
# Palette couleurs KPI
COLORS = {
    'primary': '#2E86AB',      # Bleu principal
    'success': '#A23B72',      # Vert pour tendances positives  
    'warning': '#F18F01',      # Orange pour alertes
    'danger': '#C73E1D',       # Rouge pour problèmes
    'neutral': '#6C757D',      # Gris pour données neutres
    'background': '#F8F9FA',   # Fond clair
    'text': '#212529'          # Texte principal
}
```

### Typographie
- **Titres KPI** : Bold, 18px
- **Valeurs** : Bold, 24px, couleur selon contexte
- **Labels** : Regular, 14px
- **Descriptions** : Light, 12px

### Icons
- 🏭 Machines
- 🏢 Sites  
- 👥 Équipes
- 🔧 Préventif
- 🚨 Curatif
- 📊 Tendances

---

## 🔌 Intégration avec l'Application

### 1. Nouveau Menu Principal

**Fichier:** `app/ui/main_window.py`

```python
# Ajouter dans la méthode create_menu_bar()
finance_menu = self.menubar.addMenu("💰 Finance")
finance_menu.addAction("📊 Dashboard KPI", self.open_kpi_dashboard)
finance_menu.addAction("🏭 Analyse par Machine", self.open_machine_analysis)
finance_menu.addAction("🏢 Analyse par Site", self.open_site_analysis)
finance_menu.addSeparator()
finance_menu.addAction("📈 Rapports Avancés", self.open_advanced_reports)
```

### 2. Nouvel Onglet Central

**Option A:** Onglet dédié dans le TabWidget principal
**Option B:** Fenêtre modale plein écran
**Option C:** Dock widget ancrable

### 3. Raccourcis Clavier
- `Ctrl+F1` : Dashboard KPI
- `Ctrl+F2` : Analyse machines
- `Ctrl+F3` : Analyse sites
- `F5` : Actualiser données

---

## 📊 Bibliothèques de Graphiques

### Option 1: QtCharts (Recommandée)
```python
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QPieSeries

# Avantages: Intégration native Qt, performances
# Inconvénients: Moins de types de graphiques
```

### Option 2: Matplotlib + Qt
```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

# Avantages: Très flexible, nombreux types de graphiques
# Inconvénients: Plus lourd, style moins intégré
```

### Option 3: PyQtGraph
```python
import pyqtgraph as pg

# Avantages: Très performant, interactif
# Inconvénients: Style plus technique
```

**Recommandation: QtCharts** pour cohérence avec Qt + Matplotlib pour graphiques avancés

---

## 🔄 Gestion des Données

### Chargement Asynchrone
```python
class DataLoader(QThread):
    """Thread pour chargement des données KPI sans bloquer l'UI"""
    data_loaded = Signal(dict)
    error_occurred = Signal(str)
    
    def run(self):
        try:
            kpi_service = KPIService()
            data = kpi_service.get_couts_par_machine(...)
            self.data_loaded.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))
```

### Cache Local
```python
class KPICache:
    """Cache des données KPI pour éviter les requêtes répétitives"""
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    def get_cached_data(self, key):
        # Retourner données en cache si valides
    
    def set_cached_data(self, key, data):
        # Stocker avec timestamp
```

---

## 📱 Responsive Design

### Breakpoints
- **Large** (> 1200px) : Dashboard complet 3 colonnes
- **Medium** (800-1200px) : Dashboard 2 colonnes  
- **Small** (< 800px) : Dashboard 1 colonne avec navigation verticale

### Adaptation Mobile
- Graphiques redimensionnables
- Tableaux avec scroll horizontal
- Menu hamburger pour navigation

---

## 🚀 Plan de Développement

### Semaine 1: Infrastructure UI
- [x] Structure des dossiers `app/ui/kpi/`
- [ ] Classe `KPIDashboard` de base
- [ ] Système de layout responsive
- [ ] Intégration menu principal

### Semaine 2: Widgets de Base
- [ ] `MachineKPIWidget` avec graphique barres
- [ ] `GlobalSummaryWidget` avec métriques clés  
- [ ] Chargement données asynchrone
- [ ] Tests de base

### Semaine 3: Widgets Avancés
- [ ] `SiteKPIWidget` avec camembert
- [ ] `EquipeKPIWidget` avec comparaisons
- [ ] `PreventifCuratifWidget` avec alertes
- [ ] Export Excel/CSV

### Semaine 4: Polish & Intégration  
- [ ] `TrendsWidget` avec graphiques temporels
- [ ] Design system cohérent
- [ ] Documentation utilisateur
- [ ] Tests d'intégration

---

## 🧪 Tests Utilisateur

### Scénarios de Test
1. **Navigation** : Ouverture dashboard, changement de centre de frais
2. **Filtrage** : Sélection de période, filtres par site
3. **Export** : Génération Excel, vérification données
4. **Performance** : Temps de chargement, fluidité interaction
5. **Erreurs** : Gestion absence de données, perte connexion DB

### Métriques de Succès
- [ ] Temps d'ouverture dashboard < 3 secondes
- [ ] Changement de période < 2 secondes  
- [ ] Export Excel < 5 secondes
- [ ] Satisfaction utilisateur > 8/10

---

## 📋 Checklist de Validation

### Fonctionnel
- [ ] Toutes les données KPI s'affichent correctement
- [ ] Filtres par période fonctionnent
- [ ] Export Excel contient toutes les données
- [ ] Graphiques sont interactifs (zoom, sélection)

### Design
- [ ] Interface cohérente avec le reste de l'application
- [ ] Couleurs et typographie respectent le design system
- [ ] Responsive sur différentes tailles d'écran
- [ ] Accessibilité (contraste, navigation clavier)

### Performance  
- [ ] Chargement initial < 3s
- [ ] Interactions fluides (< 200ms)
- [ ] Pas de blocage UI lors du chargement
- [ ] Mémoire stable (pas de fuites)

---

**🎯 Objectif: Interface utilisateur moderne, performante et intuitive pour l'exploitation des KPI financiers GMAO**
