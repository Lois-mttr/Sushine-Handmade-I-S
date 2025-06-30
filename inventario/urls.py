# inventario/urls.py
from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Vista principal del inventario (requiere autenticación)
    path('', views.inventario_general, name='inventario_general'),
    
    # Vista de inventario por ubicación específica (requiere autenticación)
    path('ubicacion/<int:ubicacion_id>/', views.inventario_por_ubicacion, name='inventario_ubicacion'),
    
    # Vista de detalle de producto (requiere autenticación)
    path('producto/<str:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('producto/<int:ubicacion_id>/<str:producto_id>/', views.detalle_producto, name='detalle_producto_ubicacion'),
    
    # API endpoints para AJAX (requieren autenticación AJAX)
    path('api/stats/', views.inventario_stats_ajax, name='inventario_stats_ajax'),
    path('api/busqueda/', views.busqueda_rapida_ajax, name='busqueda_rapida_ajax'),
    
    # Configuración de alertas (solo administradores y gerentes)
    path('alertas/', views.configurar_alertas_stock, name='configurar_alertas'),
]