# Système de Passage de Langue - GMAO Multi-Applications

## Vue d'ensemble

Le système permet de passer la langue sélectionnée depuis le launcher multi-applications (`meta_portail/accueil.py`) vers l'application GMAO principale (`app/main.py`).

## Architecture

```
meta_portail/accueil.py (Launcher)
    ↓ --lang argument
app/main.py (GMAO App)
    ↓ app_config.language + QTranslator
Interface utilisateur traduite
```

## Systèmes de traduction

### 1. Système principal : QTranslator + self.tr()

La majorité de l'application utilise le système standard Qt :
- Fichiers `.ts` pour les traductions sources
- Fichiers `.qm` compilés pour l'exécution
- Méthode `self.tr("Text to translate")` dans le code
- Gestion automatique via `QTranslator`

**Avantages :**
- Standard Qt recommandé
- Outils Qt Linguist pour les traducteurs
- Pluralisation automatique
- Changement de langue à chaud possible

### 2. Système alternatif : Dictionnaire (Dashboard KPI uniquement)

Le module `app/ui/kpi/kpi_dashboard_clean.py` utilise un système de dictionnaire :
- Dictionnaire `TRANSLATIONS` avec toutes les langues
- Fonction `get_text(key)` pour récupérer les traductions
- Configuration basée sur `app_config.language`

**Pourquoi cette exception :**
- Module développé de manière isolée
- Système déjà fonctionnel et testé
- Facilité de maintenance pour ce module spécifique
- Évite une migration complexe

## Fonctionnement

### 1. Launcher (`meta_portail/accueil.py`)

Le launcher permet à l'utilisateur de :
- Sélectionner une langue (Français, Anglais, Allemand, Espagnol, Italien)
- Lancer l'application GMAO avec la langue sélectionnée

**Code clé :**
```python
def start_gmao(self):
    lang = self.get_selected_language()
    subprocess.Popen([gmao_python_absolute, gmao_path_absolute, "--lang", lang])
```

### 2. Application principale (`app/main.py`)

L'application principale :
- Parse l'argument `--lang` depuis la ligne de commande
- Configure `app_config.language` avec la langue sélectionnée
- Charge le traducteur Qt approprié

**Code clé :**
```python
parser.add_argument("--lang", type=str, default="Français", help="Langue de l'application")
args, unknown = parser.parse_known_args()
selected_language_str = args.lang

language_map = {
    "Français": Language.FRENCH,
    "Anglais": Language.ENGLISH,
    "Allemand": Language.GERMAN,
    "Espagnol": Language.SPANISH,
    "Italien": Language.ITALIAN
}

app_config.language = language_map.get(selected_language_str, Language.FRENCH)
```

### 3. Dashboard KPI (`app/ui/kpi/kpi_dashboard_clean.py`)

Le dashboard KPI :
- Utilise la fonction `get_text()` pour récupérer les textes traduits
- Adapte automatiquement l'interface selon la langue configurée

**Code clé :**
```python
def get_text(key: str) -> str:
    """Récupère le texte traduit selon la langue configurée."""
    current_lang = app_config.language if 'app_config' in globals() else Language.FRENCH
    return TRANSLATIONS.get(current_lang, TRANSLATIONS[Language.FRENCH]).get(key, key)

# Utilisation
self.setWindowTitle(f"{get_text('dashboard_title')} - {APP_NAME}")
```

## Langues supportées

| Langue    | Code | Status |
|-----------|------|--------|
| Français  | fr   | ✅ Complet |
| Anglais   | en   | ✅ Complet |
| Allemand  | de   | ✅ Complet |
| Espagnol  | es   | 🔄 En cours |
| Italien   | it   | 🔄 En cours |

## Configuration

### Ajout d'une nouvelle langue

1. **Dans `app/config.py`** :
```python
class Language(Enum):
    NOUVELLE_LANGUE = "code_iso"
```

2. **Dans `app/ui/kpi/kpi_dashboard_clean.py`** :
```python
TRANSLATIONS = {
    # ...
    Language.NOUVELLE_LANGUE: {
        "dashboard_title": "Traduction du titre",
        # ... autres traductions
    }
}
```

3. **Dans `meta_portail/accueil.py`** :
```python
self.lang_combo.addItems([..., "Nouvelle Langue"])
```

### Ajout de nouvelles traductions

Pour ajouter une nouvelle clé de traduction :

1. Ajouter la clé dans toutes les langues du dictionnaire `TRANSLATIONS`
2. Utiliser `get_text('nouvelle_cle')` dans le code

## Tests

### Test manuel
1. Lancer `meta_portail/accueil.py`
2. Sélectionner une langue
3. Cliquer sur "Start CMMS"
4. Vérifier que l'interface GMAO s'affiche dans la bonne langue

### Test automatisé
```bash
cd "G:\Mon Drive\Projets\gmao_app_PostGres"
python test_integration_langue.py
```

## Dépannage

### L'application ne démarre pas
- Vérifier que l'environnement virtuel existe : `app\.venv\Scripts\python.exe`
- Vérifier les chemins dans le launcher
- Vérifier les logs de l'application

### La langue ne change pas
- Vérifier que l'argument `--lang` est bien passé
- Vérifier que la langue est dans le mapping `language_map`
- Vérifier les logs de configuration dans `app/main.py`

### Traductions manquantes
- Vérifier que la clé existe dans `TRANSLATIONS`
- Vérifier que la langue est supportée
- Utiliser la langue par défaut (Français) en cas d'erreur

## Évolutions futures

- [ ] Ajout de traductions pour les autres modules (gestion, maintenance, etc.)
- [ ] Support des traductions Qt (.qm files) pour les éléments standard
- [ ] Persistance de la langue sélectionnée
- [ ] Changement de langue à chaud (sans redémarrage)
- [ ] Support de langues RTL (droite à gauche)
