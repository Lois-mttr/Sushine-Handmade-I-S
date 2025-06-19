from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-session/', views.check_session_ajax, name='check_session'),
]
