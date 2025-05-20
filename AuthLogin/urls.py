from django.urls import path
from .views import login_view, main, forgot_password

urlpatterns = [
    path('', login_view, name='login'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('main/', main, name='main'),
]