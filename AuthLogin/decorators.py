from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
from core_data.models import Usuario
import logging

logger = logging.getLogger('nexo.auth')

def nexo_login_required(view_func):
    """
    Decorador personalizado para requerir autenticación en el sistema NEXO
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar si el usuario está autenticado
        user = get_authenticated_user(request)
        
        if not user:
            # Usuario no autenticado
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Petición AJAX
                return JsonResponse({
                    'authenticated': False,
                    'message': 'Sesión expirada. Por favor, inicia sesión nuevamente.',
                    'redirect_url': 'auth:login'
                }, status=401)
            else:
                # Petición normal
                messages.warning(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('auth:login')
        
        # Agregar usuario al request
        request.nexo_user = user
        
        # Ejecutar la vista original
        return view_func(request, *args, **kwargs)
    
    return wrapper

def nexo_role_required(allowed_roles):
    """
    Decorador para requerir roles específicos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Primero verificar autenticación
            user = get_authenticated_user(request)
            
            if not user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'authenticated': False,
                        'message': 'Sesión expirada.',
                        'redirect_url': 'auth:login'
                    }, status=401)
                else:
                    return redirect('auth:login')
            
            # Verificar rol
            user_role = user.rol or 'empleado'
            if user_role not in allowed_roles:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'No tienes permisos para realizar esta acción.',
                        'insufficient_permissions': True
                    }, status=403)
                else:
                    messages.error(request, 'No tienes permisos para acceder a esta página.')
                    return redirect('/dashboard/')
            
            # Agregar usuario al request
            request.nexo_user = user
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def get_authenticated_user(request):
    """
    Obtener usuario autenticado desde la sesión
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return None
    
    try:
        # Verificar que el usuario aún existe y está activo
        user = Usuario.objects.get(idusuario=user_id, activo=True)
        return user
    except Usuario.DoesNotExist:
        # Usuario no existe o está inactivo, limpiar sesión
        request.session.flush()
        logger.warning(f"Sesión limpiada para usuario inexistente o inactivo: {user_id}")
        return None

def ajax_login_required(view_func):
    """
    Decorador específico para vistas AJAX que requieren autenticación
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = get_authenticated_user(request)
        
        if not user:
            return JsonResponse({
                'authenticated': False,
                'message': 'Sesión expirada. Por favor, inicia sesión nuevamente.',
                'redirect_url': 'auth:login'
            }, status=401)
        
        request.nexo_user = user
        return view_func(request, *args, **kwargs)
    
    return wrapper
