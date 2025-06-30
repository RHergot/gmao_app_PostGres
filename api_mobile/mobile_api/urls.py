"""
URLs pour l'API mobile GMAO
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r"ordres-travail", views.OrdreTravailViewSet)
router.register(r"techniciens", views.TechnicienViewSet)
router.register(r"pieces", views.PieceViewSet)
router.register(r"machines", views.MachineViewSet)
router.register(r"maintenance", views.MaintenanceViewSet)

urlpatterns = [
    # Endpoints des ViewSets
    path("", include(router.urls)),
    # Endpoints personnalisés
    path("status/", views.api_status, name="api_status"),
    # path('pieces/reserver/', views.reserver_piece, name='reserver_piece'),
    # path('technicien/profile/', views.technicien_profile, name='technicien_profile'),
]
