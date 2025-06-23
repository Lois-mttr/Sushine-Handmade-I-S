from django.urls import path
from . import views

app_name = 'dashboard' 

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/stats/', views.get_dashboard_stats_ajax, name='dashboard_stats'),
    path('api/recent-data/', views.get_recent_data_ajax, name='recent_data'),
    path('api/refresh/', views.refresh_dashboard_data, name='refresh_dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
