# Procédure : exposer les OT et rapports de maintenance via une API Django REST Framework

Procédure pas-à-pas pour exposer vos « OT » (ordres de travail) et rapports de maintenance via une API Django REST Framework (DRF).

Étape 0 – Inventaire du code existant • Schéma SQL : 
app/data/schemas.py

– tables clés : ORDRE_TRAVAIL, MAINTENANCE, INTERVENTION_PIECE, TECHNICIEN, PIECE…
• Logique métier :
– app/core/services/maintenance_service.py (création / mise à jour d’un rapport, ajustement stock…)
– autres services + repos dans app/core/services/ et app/data/repositories/
• Génération PDF : app/utils/pdf_maintenance.py
Ces fichiers contiennent déjà la “business logic” qu’il vaut mieux réutiliser au lieu de la recopier côté Django.

Étape 1 – Créer le squelette Django

bash
django-admin startproject gmao_api .
python -m pip install django djangorestframework psycopg[binary]
Ajoutez DRF dans INSTALLED_APPS, configurez la connexion à la même base Postgres que l’app bureau.

Étape 2 – Générer les modèles Django Deux approches :

python manage.py inspectdb ORDRE_TRAVAIL MAINTENANCE … > api/models.py
• Rapide, correspond 100 % aux tables actuelles.
• Nettoyez ensuite les Meta options (managed = False, db_table=…).
Modèles manuels (recommandé si vous souhaitez faire évoluer le schéma).
• Reprenez les colonnes des tables ci-dessus.
• Définissez les relations avec ForeignKey/OneToOneField.
Étape 3 – Brancher la logique métier existante Dans l’app Django (« api »), créez un module services.py qui importe vos services existants :

python
from app.core.services.maintenance_service import create_maintenance_report, update_maintenance_report
# etc.
Le code DRF appellera ces fonctions pour garder un seul endroit où la logique évolue.

Étape 4 – Serializers

python
class OrdreTravailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdreTravail
        fields = "__all__"

class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = "__all__"
Étape 5 – ViewSets / Endpoints

python
class OTViewSet(viewsets.ModelViewSet):
    queryset = OrdreTravail.objects.all()
    serializer_class = OrdreTravailSerializer

    # GET /api/techniciens/{id}/ots/ – OT affectés à un technicien
    @action(detail=False, url_path="techniciens/(?P<tech_id>[^/.]+)/ots")
    def by_technicien(self, request, tech_id=None):
        qs = self.get_queryset().filter(technicien_id=tech_id, statut__in=["Planifié","En cours"])
        return self.list(request, queryset=qs)

    # POST /api/ots/{id}/reserve_piece/
    @action(methods=["post"], detail=True)
    def reserve_piece(self, request, pk=None):
        piece_id = request.data["piece_id"]
        qt = int(request.data["quantite"])
        reserve_piece_logic(pk, piece_id, qt)  # appelez service existant
        return Response(status=204)
python
class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
Router :

python
router = DefaultRouter()
router.register(r"ots", OTViewSet)
router.register(r"maintenance", MaintenanceViewSet)
urlpatterns = [path("api/", include(router.urls))]
Étape 6 – Sécurité & Authentification • Activez rest_framework.authtoken ou mieux : JWT (djangorestframework-simplejwt).
• Protégez les endpoints par permission (ex. IsAuthenticated + filtrage par technicien connecté).

Étape 7 – Tests rapides

python manage.py runserver
curl -H "Authorization: Token xxx" http://localhost:8000/api/ots/
Étape 8 – Documentation interactive Installez drf-spectacular ou drf-yasg pour générer OpenAPI.
L’app mobile consommera la doc via /schema/swagger-ui/.

Étape 9 – CI/CD Ajoutez un job GitHub-Actions qui :

lance python manage.py test,
applique flake8,
déploie (Heroku, Dokku, ou VPS) quand la branche main passe au vert.
Fichiers principaux à modifier / créer • gmao_api/settings.py (DB + DRF)
• api/models.py (ou génération inspectdb)
• api/serializers.py, api/views.py, api/urls.py
• éventuellement adapter les services existants pour qu’ils ne dépendent pas de PySide/Qt.

Avec cette structure vous obtenez une API propre, testable et pérenne ; l’app mobile (Kivy, Flutter, React Native ou simple PWA) n’aura plus qu’à consommer les endpoints.

Feedback submitted> 

Cette procédure décrit, pas à pas, la mise en place d’une API REST pour la GMAO afin d’alimenter une interface web/mobile. Les exemples supposent PostgreSQL comme SGBD et utilisent Django + DRF.

---

## Étape 0 – Inventaire du code existant

- **Schéma SQL** : `app/data/schemas.py`
  - Tables clés : `ORDRE_TRAVAIL`, `MAINTENANCE`, `INTERVENTION_PIECE`, `TECHNICIEN`, `PIECE`, …
- **Logique métier** :
  - `app/core/services/maintenance_service.py` (création/màj rapport, ajustement stock)
  - Services & repositories dans `app/core/services/` et `app/data/repositories/`
- **Génération PDF** : `app/utils/pdf_maintenance.py`

Ces modules seront réutilisés par l’API pour éviter la duplication de logique.

---

## Étape 1 – Créer le squelette Django

```bash
# À la racine du projet gmao_app_PostGres
python -m pip install django djangorestframework psycopg[binary]
django-admin startproject gmao_api .  # crée settings.py et manage.py
```

1. Ajoutez `rest_framework` (et plus tard `rest_framework.authtoken` ou JWT) dans `INSTALLED_APPS`.
2. Configurez la connexion Postgres dans `gmao_api/settings.py` pour pointer vers la même base que l’application bureau.

---

## Étape 2 – Générer les modèles Django

Deux options :

1. **inspectdb (rapide)**

```bash
python manage.py inspectdb ORDRE_TRAVAIL MAINTENANCE INTERVENTION_PIECE > api/models.py
```

Nettoyez ensuite `Meta.managed = False`, conservez `db_table`.

2. **Modèles manuels (recommandé)**

Créez les classes `OrdreTravail`, `Maintenance`, … avec `ForeignKey` / `OneToOneField` correspondant aux colonnes.

---

## Étape 3 – Brancher la logique métier existante

Dans l’app Django (ex : `api/services.py`) :

```python
from app.core.services.maintenance_service import (
    create_maintenance_report,
    update_maintenance_report,
)
# Les vues DRF appelleront ces fonctions.
```

---

## Étape 4 – Serializers

```python
from rest_framework import serializers
from .models import OrdreTravail, Maintenance

class OrdreTravailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdreTravail
        fields = "__all__"

class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = "__all__"
```

---

## Étape 5 – ViewSets / Endpoints

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import OrdreTravail, Maintenance
from .serializers import OrdreTravailSerializer, MaintenanceSerializer
from .services import reserve_piece_logic

class OTViewSet(viewsets.ModelViewSet):
    queryset = OrdreTravail.objects.all()
    serializer_class = OrdreTravailSerializer

    # GET /api/techniciens/{id}/ots/
    @action(detail=False, url_path="techniciens/(?P<tech_id>[^/.]+)/ots")
    def by_technicien(self, request, tech_id=None):
        qs = self.get_queryset().filter(technicien_id=tech_id, statut__in=["Planifié", "En cours"])
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # POST /api/ots/{id}/reserve_piece/
    @action(methods=["post"], detail=True)
    def reserve_piece(self, request, pk=None):
        piece_id = request.data["piece_id"]
        qt = int(request.data["quantite"])
        reserve_piece_logic(pk, piece_id, qt)
        return Response(status=204)

class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
```

Router :

```python
from rest_framework.routers import DefaultRouter
from .views import OTViewSet, MaintenanceViewSet

router = DefaultRouter()
router.register(r"ots", OTViewSet)
router.register(r"maintenance", MaintenanceViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]
```

---

## Étape 6 – Sécurité & Authentification

1. Activez `rest_framework.authtoken` ou `djangorestframework-simplejwt`.
2. Paramétrez les permissions : `REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"]}`.
3. Filtrez les OT par technicien connecté côté `OTViewSet`.

---

## Étape 7 – Tests rapides

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver  # http://localhost:8000
curl -H "Authorization: Token <token>" http://localhost:8000/api/ots/
```

---

## Étape 8 – Documentation interactive

```bash
python -m pip install drf-spectacular
```
Ajoutez dans `urls.py` :
```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
urlpatterns += [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
```
L’interface Swagger est accessible sur `/api/docs/`.

---

## Étape 9 – CI/CD

- **Lint & tests** : `flake8`, `pytest` + `pytest-django`.
- **GitHub Actions** : job qui lance les tests, puis déploie (Heroku/Dokku/VPS) quand `main` passe.

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python manage.py test
```

---

## Prochaines étapes

1. Créer des templates HTML responsives consommant l’API (ou démarrer une PWA).  
2. Embellir avec une feuille de style existante (Bootstrap / Bulma / Tailwind).
3. Implémenter la réservation de pièces et la saisie de rapports côté front.

*Bonne mise en œuvre !*





