"""
URLs para el módulo de reportes NEXO
"""
from django.urls import path
from . import views

app_name = 'informes'

urlpatterns = [
    # Vista principal de informes
    path('', views.lista_informes, name='lista_informes'),
    
    # Informes específicos
    path('inventario-general/', views.inventario_general, name='inventario_general'),
    path('produccion/', views.produccion, name='produccion'),
    path('ventas/', views.ventas, name='ventas'),
    path('devoluciones/', views.devoluciones, name='devoluciones'),
    path('clientes/', views.clientes, name='clientes'),
    path('usuarios-empleados/', views.usuarios_empleados, name='usuarios_empleados'),
    path('productos-categoria/', views.productos_categoria, name='productos_categoria'),
    
    # Exportación
    path('exportar/pdf/<str:tipo_informe>/', views.exportar_pdf, name='exportar_pdf'),
    path('exportar/excel/<str:tipo_informe>/', views.exportar_excel, name='exportar_excel'),
]
