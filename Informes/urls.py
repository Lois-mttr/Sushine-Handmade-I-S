"""
URLs para el módulo de reportes NEXO
"""
from django.urls import path
from . import views

app_name = 'Informes'

urlpatterns = [
    # Dashboard principal de reportes
    path('', views.reports_dashboard, name='reports_dashboard'),
    
    # Reportes individuales
    path('inventario-general/', views.inventario_general, name='inventario_general'),
    path('produccion/', views.produccion, name='produccion'),
    path('reabastecimientos/', views.reabastecimientos, name='reabastecimientos'),
    path('ventas/', views.ventas, name='ventas'),
    path('devoluciones/', views.devoluciones, name='devoluciones'),
    path('clientes/', views.clientes, name='clientes'),
    path('usuarios-empleados/', views.usuarios_empleados, name='usuarios_empleados'),
    path('productos-categoria/', views.productos_categoria, name='productos_categoria'),
    path('auditoria/', views.auditoria, name='auditoria'),

    # API para estadísticas del dashboard
    path('dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
]
