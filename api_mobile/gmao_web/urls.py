"""
URLs pour l'interface web responsive GMAO Mobile
"""
from django.urls import path
from . import views

app_name = 'gmao_web'

urlpatterns = [
    # Pages principales
    path('', views.WorkOrdersView.as_view(), name='work_orders'),
    path('work-orders/', views.WorkOrdersView.as_view(), name='work_orders_list'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('maintenance-report/<int:ot_id>/', views.MaintenanceReportView.as_view(), name='maintenance_report'),
    
    # API endpoints pour l'interface web
    path('api/work-orders/', views.work_orders_api, name='work_orders_api'),
    path('api/work-orders/<int:ot_id>/', views.work_order_detail_api, name='work_order_detail_api'),
    path('api/technicians/', views.technicians_api, name='technicians_api'),
    
    # API endpoints pour le rapport de maintenance
    path('api/maintenance/form-data/<int:ot_id>/', views.maintenance_form_data_api, name='maintenance_form_data_api'),
    path('api/maintenance/calculate-cost/', views.calculate_maintenance_cost, name='calculate_maintenance_cost'),
    path('api/maintenance/create/<int:ot_id>/', views.create_maintenance_report, name='create_maintenance_report'),
]
