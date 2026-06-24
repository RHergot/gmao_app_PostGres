# 📊 VUES KPI FINANCIÈRES

## Fichier: `sql_vues_kpi_financiers.sql`

Ce fichier contient toutes les vues SQL optimisées pour le calcul des KPI financiers de la GMAO.

### Vues créées :

1. **`v_maintenance_couts_detaille`** - Vue consolidée principale
   - Agrège toutes les informations de maintenance avec contexte (machine, site, équipe, etc.)
   - Calcule les ratios et pourcentages de coûts
   - Base pour toutes les autres vues KPI

2. **`v_kpi_machine_mensuel`** - KPI par machine et période
   - Agrégation mensuelle des coûts par machine
   - Compteurs d'interventions par type
   - Ratios préventif/curatif par machine

3. **`v_kpi_site_mensuel`** - KPI par site et période
   - Agrégation mensuelle des coûts par site
   - Coût moyen par machine du site
   - Performance comparative inter-sites

4. **`v_kpi_equipe_mensuel`** - KPI par équipe et période
   - Performance financière par équipe
   - Productivité (coût par technicien, interventions par technicien)
   - Heures totales et coût par heure

5. **`v_kpi_type_machine_mensuel`** - KPI par type de machine
   - Analyse des coûts par catégorie de machines
   - Comparaison des types pour identification des problèmes

6. **`v_kpi_preventif_curatif`** - Comparaison préventif vs curatif
   - Ratios et pourcentages par période
   - Détection des dérives de maintenance

7. **`v_top_machines_couteuses`** - Classement machines coûteuses
   - Top machines sur 12 mois
   - Tendances d'évolution des coûts
   - Identification des machines problématiques

### Initialisation :

```bash
# Créer toutes les vues dans la base de données
python scripts/init_kpi_views.py

# Tester le fonctionnement 
python scripts/test_kpi_service.py
```

### Utilisation depuis le code :

```python
from app.core.services.kpi_service import KPIService

kpi = KPIService()
machines = kpi.get_couts_par_machine(periode_debut, periode_fin)
```

### Index de performance :

Le fichier inclut également des index optimisés pour améliorer les performances des requêtes KPI.

---
**Dernière mise à jour:** 30 juin 2025  
**Phase:** 1.2 - Architecture Base de Données
