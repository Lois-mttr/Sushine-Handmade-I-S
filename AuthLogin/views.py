from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Usuario
from django.contrib.auth.hashers import check_password
import json

def login_view(request):
    """Vista para mostrar el formulario de login"""
    return render(request, 'pages/login.html')

def dashboard(request):
    """Vista para mostrar el dashboard después de iniciar sesión"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = Usuario.objects.get(idUsuario=request.session['user_id'])
    return render(request, 'pages/dashboard.html', {'user': user})

@csrf_exempt
def validate_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'status': 'error', 'message': 'Los campos no pueden estar vacíos'})
        
        try:
            user = Usuario.objects.get(nombreUsuario=username, activo=True)
            
            # Verificar contraseña con SHA-256
            if not Usuario.verificar_contrasena(password, user.passUsuario):
                raise Usuario.DoesNotExist
            
            request.session['user_id'] = user.idUsuario
            request.session['username'] = user.nombreUsuario
            request.session['role'] = user.rol
            
            return JsonResponse({'status': 'success', 'redirect': '/dashboard/'})
        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario o contraseña incorrectos'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

def logout_view(request):
    """Vista para cerrar sesión"""
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['username']
        del request.session['role']
    
    return redirect('login')