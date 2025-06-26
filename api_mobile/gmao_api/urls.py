"""
Configuration des URLs principales du projet GMAO API
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def api_status(request):
    """Endpoint de test pour vérifier que l'API fonctionne"""
    return JsonResponse({
        'status': 'OK',
        'message': 'GMAO API is running',
        'version': '1.0.0'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API REST
    path('api/', include('mobile_api.urls')),
    path('api/status/', api_status, name='api_status'),
    
    # Interface Web Responsive (page d'accueil)
    path('', include('gmao_web.urls')),
]
