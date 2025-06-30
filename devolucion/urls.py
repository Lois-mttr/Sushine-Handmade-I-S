from django.urls import path
from . import views

app_name = 'devolucion' 

urlpatterns = [
# URLs para el CRUD de Producción
    path('produccion/', views.produccion_list, name='devolucion_list'),
    path('produccion/crear/', views.produccion_create, name='produccion_create'),
    path('produccion/<int:pk>/', views.produccion_detail, name='produccion_detail'),
    path('produccion/<int:pk>/editar/', views.produccion_edit, name='produccion_edit'), # 'produccion_edit' en lugar de 'produccion_update'
    path('produccion/<int:pk>/eliminar/', views.produccion_delete, name='produccion_delete'), # Para dar de baja (soft delete)
    
    # URL para el Dashboard de Producción
    path('produccion/dashboard/', views.produccion_dashboard, name='produccion_dashboard'),
    
    # URLs para API (si se usan para AJAX desde las plantillas)
    path('api/producto/<str:producto_id>/', views.api_producto_info, name='api_producto_info'),
    path('api/empleado/<int:empleado_id>/', views.api_empleado_info, name='api_empleado_info'),
    path('api/check-session/', views.api_check_session, name='api_check_session'), # Para verificar la sesión
]