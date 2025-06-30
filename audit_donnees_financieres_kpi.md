# Audit des Données Financières - Base pour KPI par Centre de Frais

## 📊 **Synthèse Exécutive**
Document d'audit des données financières existantes de l'application GMAO pour servir de base au développement des KPI par centre de frais selon le plan `plan_kpi_finance_ia.md`.

**Date de l'audit :** 30 juin 2025  
**Statut :** Phase 1.1 - Analyse et Conception ✅

---

## 🔍 **1. Sources de Coûts Identifiées**

### **1.1 Main d'Œuvre (MOD)**
**Table:** `MAINTENANCE_INTERVENANT`
- **Structure complète ✅**
  - `id_intervenant` (PK)
  - `maintenance_id` (FK vers MAINTENANCE)
  - `technicien_id` (FK vers TECHNICIEN, nullable si externe)
  - `nom_intervenant_externe` (nullable si interne)
  - `heures_travaillees` (DOUBLE PRECISION)
  - `cout_horaire` (DOUBLE PRECISION)
  - `notes` (TEXT)
  - `created_at` (TIMESTAMP)

**Calcul:** `heures_travaillees × cout_horaire = cout_total`

### **1.2 Pièces Internes (Stock)**
**Table:** `INTERVENTION_PIECE`
- **Structure complète ✅**
  - `id` (PK)
  - `maintenance_id` (FK vers MAINTENANCE)
  - `piece_id` (FK vers PIECE)
  - `quantite` (INTEGER)
  - `lot` (TEXT)

**Table liée:** `PIECE`
- `prix_unitaire` (DOUBLE PRECISION)
- `reference`, `nom`, `categorie`

**Calcul:** `quantite × piece.prix_unitaire = cout_piece`

### **1.3 Frais Externes**
**Table:** `MAINTENANCE_FRAIS_EXTERNE`
- **Structure complète ✅**
  - `id_frais` (PK)
  - `maintenance_id` (FK vers MAINTENANCE)
  - `type_frais` (ENUM: 'PIECE_EXTERNE', 'DEPLACEMENT', 'SOUS_TRAITANCE', 'AUTRE')
  - `description` (TEXT)
  - `montant` (DOUBLE PRECISION - montant unitaire)
  - `quantite` (INTEGER, default 1)
  - `reference_piece`, `fournisseur`, `facture_reference`

**Calcul:** `montant × quantite = montant_total`

---

## 🏭 **2. Centres de Frais Identifiés et Relations**

### **2.1 Par Machine**
**Table principale:** `MACHINE`
- **Clé primaire :** `id_machine`
- **Relations :**
  - `MAINTENANCE.machine_id` → Lien direct vers les coûts
  - `ORDRE_TRAVAIL.machine_id` → Planification

**Champs pour analyse :**
- `nom`, `serial`, `etat`, `criticite`
- `site_id`, `type_machine_id`, `fabricant_id`
- `date_installation`, `localisation`

### **2.2 Par Site**
**Table principale:** `SITE`
- **Clé primaire :** `id_site`
- **Relations :**
  - `MACHINE.site_id` → Agrégation par localisation
  - Calcul : SUM(coûts) WHERE machine.site_id = X

**Champs pour analyse :**
- `nom`, `ville`, `pays`, `adresse`
- `contact_principal`

### **2.3 Par Équipe**
**Table principale :** `EQUIPE`
- **Clé primaire :** `id_equipe`
- **Relations :**
  - `TECHNICIEN.equipe_id` → Lien vers équipes
  - `MAINTENANCE_INTERVENANT.technicien_id` → Coûts MOD
  - `MAINTENANCE.technicien_id` → Responsable intervention

**Champs pour analyse :**
- `nom`, `domaine_expertise`
- `responsable_id`

### **2.4 Par Type de Machine**
**Table principale :** `TYPE_MACHINE`
- **Clé primaire :** `id_type_machine`
- **Relations :**
  - `MACHINE.type_machine_id` → Classification équipements

**Champs pour analyse :**
- `nom`, `categorie`, `description`

### **2.5 Par Type d'Intervention**
**Table principale :** `MAINTENANCE`
- **Champ discriminant :** `type_reel`
- **Valeurs typiques :** 'Preventif', 'Correctif', 'Urgence'

---

## 💰 **3. Structure Financière Consolidée**

### **3.1 Table MAINTENANCE (Consolidation)**
**Champs financiers existants ✅**
- `cout_main_oeuvre` (DOUBLE PRECISION)
- `cout_pieces_internes` (DOUBLE PRECISION) 
- `cout_pieces_externes` (DOUBLE PRECISION)
- `cout_autres_frais` (DOUBLE PRECISION)
- `cout_total` (DOUBLE PRECISION)

### **3.2 Services de Calcul Existants**
- **FinanceService ✅** : Calculs automatisés
- **MaintenanceService.recalculer_et_maj_couts() ✅** : Mise à jour consolidée
- **Architecture propre** : Séparation calcul/persistance

---

## 🎯 **4. Centres de Frais - Faisabilité Technique**

### **✅ RÉALISABLE IMMÉDIATEMENT**

#### **4.1 Par Machine**
```sql
-- Exemple requête
SELECT 
    m.id_machine,
    m.nom AS machine_nom,
    s.nom AS site_nom,
    tm.nom AS type_machine,
    SUM(maint.cout_total) AS cout_total_machine,
    COUNT(maint.id_maintenance) AS nb_interventions,
    AVG(maint.cout_total) AS cout_moyen_intervention
FROM MACHINE m
LEFT JOIN MAINTENANCE maint ON m.id_machine = maint.machine_id
LEFT JOIN SITE s ON m.site_id = s.id_site
LEFT JOIN TYPE_MACHINE tm ON m.type_machine_id = tm.id_type_machine
WHERE maint.date_fin_reelle >= '2024-01-01'
GROUP BY m.id_machine, m.nom, s.nom, tm.nom
ORDER BY cout_total_machine DESC;
```

#### **4.2 Par Site**
```sql
-- Agrégation par site
SELECT 
    s.id_site,
    s.nom AS site_nom,
    s.ville,
    COUNT(DISTINCT m.id_machine) AS nb_machines,
    SUM(maint.cout_total) AS cout_total_site,
    AVG(maint.cout_total) AS cout_moyen_intervention
FROM SITE s
LEFT JOIN MACHINE m ON s.id_site = m.site_id
LEFT JOIN MAINTENANCE maint ON m.id_machine = maint.machine_id
WHERE maint.date_fin_reelle >= '2024-01-01'
GROUP BY s.id_site, s.nom, s.ville
ORDER BY cout_total_site DESC;
```

#### **4.3 Par Équipe**
```sql
-- Coûts par équipe (via techniciens)
SELECT 
    e.id_equipe,
    e.nom AS equipe_nom,
    e.domaine_expertise,
    COUNT(DISTINCT t.id_technicien) AS nb_techniciens,
    SUM(maint.cout_total) AS cout_total_equipe,
    SUM(maint.cout_main_oeuvre) AS cout_mod_equipe
FROM EQUIPE e
LEFT JOIN TECHNICIEN t ON e.id_equipe = t.equipe_id
LEFT JOIN MAINTENANCE maint ON t.id_technicien = maint.technicien_id
WHERE maint.date_fin_reelle >= '2024-01-01'
GROUP BY e.id_equipe, e.nom, e.domaine_expertise
ORDER BY cout_total_equipe DESC;
```

#### **4.4 Par Type de Machine**
```sql
-- Coûts par famille d'équipements
SELECT 
    tm.id_type_machine,
    tm.categorie,
    tm.nom AS type_nom,
    COUNT(DISTINCT m.id_machine) AS nb_machines,
    SUM(maint.cout_total) AS cout_total_type,
    AVG(maint.cout_total) AS cout_moyen_type
FROM TYPE_MACHINE tm
LEFT JOIN MACHINE m ON tm.id_type_machine = m.type_machine_id
LEFT JOIN MAINTENANCE maint ON m.id_machine = maint.machine_id
WHERE maint.date_fin_reelle >= '2024-01-01'
GROUP BY tm.id_type_machine, tm.categorie, tm.nom
ORDER BY cout_total_type DESC;
```

#### **4.5 Par Type d'Intervention**
```sql
-- Répartition Préventif vs Curatif
SELECT 
    maint.type_reel,
    COUNT(*) AS nb_interventions,
    SUM(maint.cout_total) AS cout_total,
    AVG(maint.cout_total) AS cout_moyen,
    SUM(maint.cout_main_oeuvre) AS total_mod,
    SUM(maint.cout_pieces_internes) AS total_pieces,
    SUM(maint.cout_pieces_externes + maint.cout_autres_frais) AS total_frais_externes
FROM MAINTENANCE maint
WHERE maint.date_fin_reelle >= '2024-01-01'
GROUP BY maint.type_reel
ORDER BY cout_total DESC;
```

---

## 📈 **5. Métriques KPI Prioritaires**

### **5.1 KPI Machine (Priorité 1)**
- **Coût total par machine** (période)
- **Nombre d'interventions par machine**
- **Coût moyen par intervention**
- **Ratio préventif/curatif** par machine
- **Évolution temporelle** (mensuelle)
- **Top 10 machines coûteuses**

### **5.2 KPI Site (Priorité 1)**
- **Coût total par site**
- **Coût par machine** (moyenne site)
- **Répartition des coûts** (MOD, pièces, frais)
- **Comparaison inter-sites**

### **5.3 KPI Équipe (Priorité 2)**
- **Coût MOD par équipe**
- **Productivité équipe** (coût/heure)
- **Spécialisation** (types interventions)

### **5.4 KPI Temporels (Priorité 1)**
- **Évolution mensuelle** des coûts
- **Saisonnalité** des interventions
- **Tendances** par centre de frais

---

## 🗄️ **6. Recommandations Architecture**

### **6.1 Vues Métier Proposées**

```sql
-- Vue consolidée des coûts par maintenance
CREATE VIEW v_maintenance_couts AS
SELECT 
    m.id_maintenance,
    m.ot_id,
    m.date_fin_reelle,
    m.type_reel,
    m.cout_total,
    m.cout_main_oeuvre,
    m.cout_pieces_internes,
    m.cout_pieces_externes,
    m.cout_autres_frais,
    -- Informations machine
    mach.id_machine,
    mach.nom AS machine_nom,
    mach.criticite,
    -- Informations site
    s.id_site,
    s.nom AS site_nom,
    s.ville,
    -- Informations type
    tm.id_type_machine,
    tm.categorie AS type_categorie,
    tm.nom AS type_nom,
    -- Informations équipe
    e.id_equipe,
    e.nom AS equipe_nom,
    e.domaine_expertise,
    -- Informations technicien
    t.id_technicien,
    t.nom AS technicien_nom,
    t.cout_horaire
FROM MAINTENANCE m
LEFT JOIN MACHINE mach ON m.machine_id = mach.id_machine
LEFT JOIN SITE s ON mach.site_id = s.id_site
LEFT JOIN TYPE_MACHINE tm ON mach.type_machine_id = tm.id_type_machine
LEFT JOIN TECHNICIEN t ON m.technicien_id = t.id_technicien
LEFT JOIN EQUIPE e ON t.equipe_id = e.id_equipe
WHERE m.cout_total IS NOT NULL;
```

### **6.2 Tables de Cache (Optionnel - Phase 2)**
- `kpi_couts_machine_mensuel`
- `kpi_couts_site_mensuel` 
- `kpi_tendances_generales`

### **6.3 Index Optimisés**
```sql
-- Index pour performances KPI
CREATE INDEX idx_maintenance_date_fin ON MAINTENANCE(date_fin_reelle);
CREATE INDEX idx_maintenance_machine_date ON MAINTENANCE(machine_id, date_fin_reelle);
CREATE INDEX idx_maintenance_cout_total ON MAINTENANCE(cout_total);
CREATE INDEX idx_machine_site ON MACHINE(site_id);
CREATE INDEX idx_machine_type ON MACHINE(type_machine_id);
CREATE INDEX idx_technicien_equipe ON TECHNICIEN(equipe_id);
```

---

## 📋 **7. Plan d'Implémentation Immédiat**

### **Sprint 1 - Fondations (2 semaines)**
✅ **Fait** : Audit données existantes
🔲 **À faire** :
- [ ] Créer vues métier de base
- [ ] Étendre FinanceService avec méthodes KPI
- [ ] Tests unitaires calculs KPI

### **Sprint 2 - Interface KPI Basic (2 semaines)**
- [ ] Nouveau module `KPIService`
- [ ] Premières vues par machine/site
- [ ] Export Excel/CSV basique

### **Sprint 3 - Dashboard Avancé (2 semaines)**
- [ ] Interface graphique complète
- [ ] Filtres par période/centre
- [ ] Intégration MainWindow

---

## ⚠️ **8. Points d'Attention**

### **8.1 Qualité des Données**
- **Vérifier** la complétude des coûts calculés
- **Valider** la cohérence temporelle des données
- **Nettoyer** les éventuelles données manquantes

### **8.2 Performance**
- Les requêtes d'agrégation peuvent être lentes sur gros volumes
- Prévoir une stratégie de cache si nécessaire
- Index sur colonnes de filtrage essentiels

### **8.3 Évolutions Futures**
- Gestion des **périodes comptables**
- **Budgets prévisionnels** par centre
- **Comparaisons** période N vs N-1
- **Alertes** dérive budgétaire

---

## ✅ **Conclusion**

**L'audit confirme que l'infrastructure financière existante est robuste et complète pour développer les KPI par centre de frais.**

**Points forts :**
- Structure de données cohérente ✅
- Services de calcul automatisés ✅
- Relations bien définies ✅
- Données historiques disponibles ✅

**Prêt pour démarrage Phase 1.2** : Architecture Base de Données (Vues métier)

---

*Audit réalisé le 30/06/2025 - Document de référence pour développement KPI*
