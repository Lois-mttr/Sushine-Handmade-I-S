# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Vista principal de ventas
    path('', views.lista_ventas, name='lista_ventas'),
    
    # CRUD de ventas
    path('crear/', views.crear_venta, name='crear_venta'),
    path('detalle/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('editar/<int:venta_id>/', views.editar_venta, name='editar_venta'),
    path('anular/<int:venta_id>/', views.anular_venta, name='anular_venta'),
    
    # API endpoints AJAX
    path('api/producto-info/', views.obtener_info_producto, name='obtener_info_producto'),
    path('api/estadisticas/', views.estadisticas_ventas_ajax, name='estadisticas_ventas_ajax'),
]