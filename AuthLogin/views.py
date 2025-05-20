from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('main')
        else:
            messages.error(request, 'Usuario o Contraseña Incorrecta')
    
    return render(request, 'pages/login.html')

def forgot_password(request):
    return render(request, 'pages/forgot_password.html')

@login_required
def main(request):
    return render(request, 'pages/main.html')