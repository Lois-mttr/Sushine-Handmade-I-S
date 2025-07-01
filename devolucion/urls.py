from django.urls import path
from . import views

app_name = 'devolucion' 

urlpatterns = [
# URLs para el CRUD de Producción
    path('devolucion/', views.devolucion_list, name='devolucion_list'),
    path('devolucion/crear/', views.devolucion_create, name='devolucion_create'),
    path('devolucion/<int:pk>/', views.devolucion_detail, name='devolucion_detail'),
    path('devolucion/<int:pk>/editar/', views.devolucion_edit, name='produccion_edit'), # 'produccion_edit' en lugar de 'produccion_update'
    
]