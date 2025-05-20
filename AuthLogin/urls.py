from django.urls import path
from .views import login_view, dashboard, validate_login, logout_view

urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('validate_login/', validate_login, name='validate_login'),
    path('logout/', logout_view, name='logout'),
]