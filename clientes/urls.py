from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.listar_clientes, name='list'),
    path('crear/', views.crear_cliente, name='create'),
    path('<int:pk>/', views.detalle_cliente, name='detail'),
    path('<int:pk>/editar/', views.editar_cliente, name='edit'),
    path('<int:pk>/eliminar/', views.desactivar_cliente, name='delete'),
    path('api/validar-cedula/', views.validar_cedula, name='api_validar_cedula'),
]