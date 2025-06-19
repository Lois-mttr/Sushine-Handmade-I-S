from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from .forms import LoginForm
from core_data.models import Usuario, Empleado, Persona
import logging
import hashlib

# Create your views here.
logger = logging.getLogger('nexo.auth')

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Vista principal para el inicio de sesión
    """
    # Verificar si el usuario ya está autenticado
    if request.session.get('user_id'):
        logger.info(f"Usuario ya autenticado redirigido: {request.session.get('username')}")
        return redirect('/dashboard/')
    
    if request.method == 'GET':
        # Mostrar formulario de login
        form = LoginForm()
        context = {
            'form': form,
            'title': 'Iniciar Sesión - NEXO',
            'page_name': 'login',
            'system_name': 'NEXO - Sistema de Inventario y Ventas'
        }
        return render(request, 'AuthLogin/login.html', context)
    
    elif request.method == 'POST':
        # Verificar si es una petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return process_ajax_login(request)
        else:
            return process_traditional_login(request)

def process_ajax_login(request):
    """
    Procesar login via AJAX con respuesta JSON
    """
    try:
        # Obtener IP del cliente para control de intentos
        client_ip = get_client_ip(request)
        
        # Verificar si la IP está bloqueada
        if is_ip_blocked(client_ip):
            logger.warning(f"Intento de login desde IP bloqueada: {client_ip}")
            return JsonResponse({
                'success': False,
                'message': 'IP bloqueada temporalmente. Intenta más tarde.',
                'blocked': True,
                'attempts_remaining': 0
            })
        
        # Manejar tanto JSON como FormData
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()  # Recibimos el hash desde el frontend
        else:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
        
        # Validación básica
        if not username or not password:
            return handle_failed_login(request, client_ip, 'Usuario y contraseña son obligatorios')
        
        if len(username) > 15:
            return handle_failed_login(request, client_ip, 'Usuario no puede tener más de 15 caracteres')
        
        # Intentar autenticación directa (password ya viene hasheado)
        user = authenticate_user_direct(username, password)
        
        if user:
            # Login exitoso
            return handle_successful_login(request, user, client_ip)
        else:
            # Credenciales incorrectas
            return handle_failed_login(request, client_ip, 'Usuario o contraseña incorrectos')
            
    except Exception as e:
        logger.error(f"Error en process_ajax_login: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor. Intenta nuevamente.',
            'blocked': False,
            'attempts_remaining': get_remaining_attempts(get_client_ip(request))
        })

def authenticate_user_direct(username, password_hash):
    """
    Autenticación directa con la base de datos
    Ahora recibe el hash directamente (ya hasheado en el frontend)
    """
    try:
        # Buscar usuario en la base de datos
        user = Usuario.objects.get(nombreusuario=username, activo=True)
        
        # Comparar directamente con el hash almacenado
        if user.passusuario == password_hash:
            logger.info(f"Autenticación exitosa para usuario: {username}")
            return user
        else:
            logger.warning(f"Contraseña incorrecta para usuario: {username}")
            return None
            
    except Usuario.DoesNotExist:
        logger.warning(f"Usuario no encontrado: {username}")
        return None
    except Exception as e:
        logger.error(f"Error en autenticación para usuario {username}: {e}")
        return None

def process_traditional_login(request):
    """
    Procesar el intento de inicio de sesión (método tradicional sin AJAX)
    """
    # Obtener IP del cliente para control de intentos
    client_ip = get_client_ip(request)
    
    # Verificar si la IP está bloqueada
    if is_ip_blocked(client_ip):
        messages.error(request, 'IP bloqueada temporalmente. Intenta más tarde.')
        return render(request, 'AuthLogin/login.html', {'form': LoginForm()})
    
    # Crear formulario con datos POST
    form = LoginForm(request.POST)
    
    if form.is_valid():
        # Credenciales válidas
        user = form.get_user()
        
        if user:
            # Login exitoso
            response_data = handle_successful_login(request, user, client_ip)
            if response_data.get('success'):
                messages.success(request, 'Inicio de sesión exitoso')
                return redirect(response_data.get('redirect_url', '/dashboard/'))
        else:
            # Credenciales incorrectas
            handle_failed_login(request, client_ip, 'Credenciales incorrectas')
            messages.error(request, 'Credenciales incorrectas')
    else:
        # Errores de validación
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{error}")
    
    return render(request, 'AuthLogin/login.html', {'form': form})

def handle_successful_login(request, user, client_ip):
    """
    Manejar login exitoso
    """
    try:
        # Limpiar intentos fallidos
        clear_failed_attempts(client_ip)
        
        # Crear sesión de usuario
        request.session['user_id'] = user.idusuario
        request.session['username'] = user.nombreusuario
        request.session['user_role'] = user.rol or 'Usuario'
        request.session['employee_id'] = user.idempusuario.idempleado if user.idempusuario else None
        request.session['login_time'] = timezone.now().isoformat()
        
        # Configurar expiración de sesión (8 horas)
        request.session.set_expiry(28800)
        
        # Registrar login exitoso en logs
        log_login_attempt(user.nombreusuario, client_ip, True, 'Login exitoso')
        
        return JsonResponse({
            'success': True,
            'message': '¡Inicio de sesión exitoso!',
            'redirect_url': '/dashboard/',
            'user': {
                'username': user.nombreusuario,
                'role': user.rol or 'Usuario',
                'employee_name': user.empleado_nombre
            }
        })
        
    except Exception as e:
        logger.error(f"Error en handle_successful_login: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al procesar el login exitoso',
            'blocked': False,
            'attempts_remaining': 3
        })

def handle_failed_login(request, client_ip, error_message):
    """
    Manejar login fallido
    """
    try:
        # Incrementar intentos fallidos
        attempts = increment_failed_attempts(client_ip)
        
        # Verificar si se debe bloquear la IP
        if attempts >= 3:
            import json
            block_ip(client_ip)
            username = request.POST.get('username') or (json.loads(request.body).get('username') if request.content_type == 'application/json' else 'unknown')
            log_login_attempt(
                username, 
                client_ip, 
                False, 
                f'IP bloqueada después de {attempts} intentos fallidos'
            )
            return JsonResponse({
                'success': False,
                'message': 'Demasiados intentos fallidos. IP bloqueada por 20 segundos.',
                'blocked': True,
                'attempts_remaining': 0
            })
        
        # Registrar intento fallido en logs
        import json
        username = request.POST.get('username') or (json.loads(request.body).get('username') if request.content_type == 'application/json' else 'unknown')
        log_login_attempt(username, client_ip, False, f'Intento fallido: {error_message}')
        
        return JsonResponse({
            'success': False,
            'message': error_message,
            'attempts_remaining': 3 - attempts,
            'blocked': False
        })
        
    except Exception as e:
        logger.error(f"Error en handle_failed_login: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al procesar el intento fallido',
            'blocked': False,
            'attempts_remaining': 2
        })

def get_client_ip(request):
    """
    Obtener la IP real del cliente considerando proxies y load balancers
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_ip_blocked(ip):
    """
    Verificar si una IP está bloqueada
    """
    block_key = f"nexo_blocked_ip_{ip}"
    return cache.get(block_key, False)

def block_ip(ip):
    """
    Bloquear una IP por 20 segundos
    """
    block_key = f"nexo_blocked_ip_{ip}"
    cache.set(block_key, True, 20)  # 20 segundos
    logger.warning(f"IP bloqueada por 20 segundos: {ip}")

def increment_failed_attempts(ip):
    """
    Incrementar contador de intentos fallidos para una IP
    """
    attempts_key = f"nexo_failed_attempts_{ip}"
    attempts = cache.get(attempts_key, 0)
    attempts += 1
    cache.set(attempts_key, attempts, 300)  # 5 minutos
    return attempts

def get_remaining_attempts(ip):
    """
    Obtener intentos restantes para una IP
    """
    attempts_key = f"nexo_failed_attempts_{ip}"
    attempts = cache.get(attempts_key, 0)
    return max(0, 3 - attempts)

def clear_failed_attempts(ip):
    """
    Limpiar intentos fallidos para una IP
    """
    attempts_key = f"nexo_failed_attempts_{ip}"
    cache.delete(attempts_key)

def log_login_attempt(username, ip, success, details=''):
    """
    Registrar intento de login en logs con detalles adicionales
    """
    try:
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        status = 'EXITOSO' if success else 'FALLIDO'
        
        log_message = f"[{timestamp}] LOGIN {status} - Usuario: {username}, IP: {ip}"
        if details:
            log_message += f", Detalles: {details}"
        
        if success:
            logger.info(log_message)
        else:
            logger.warning(log_message)
            
    except Exception as e:
        logger.error(f"Error al registrar log de login: {e}")

@require_http_methods(["POST"])
def logout_view(request):
    """
    Vista para cerrar sesión
    """
    try:
        username = request.session.get('username', 'unknown')
        client_ip = get_client_ip(request)
        
        # Limpiar sesión
        request.session.flush()
        
        # Registrar logout
        log_login_attempt(username, client_ip, True, 'Logout exitoso')
        
        # Verificar si es petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Sesión cerrada exitosamente',
                'redirect_url': '/login/'
            })
        else:
            messages.success(request, 'Sesión cerrada exitosamente')
            return redirect('auth:login')
            
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error al cerrar sesión'
            })
        else:
            messages.error(request, 'Error al cerrar sesión')
            return redirect('auth:login')

def check_session(request):
    """
    Verificar si la sesión del usuario es válida
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return False
    
    try:
        # Verificar que el usuario aún existe y está activo
        user = Usuario.objects.get(idusuario=user_id, activo=True)
        return user
    except Usuario.DoesNotExist:
        # Usuario no existe o está inactivo, limpiar sesión
        request.session.flush()
        logger.warning(f"Sesión limpiada para usuario inexistente o inactivo: {user_id}")
        return False

@require_http_methods(["GET"])
def check_session_ajax(request):
    """
    Endpoint AJAX para verificar estado de sesión
    """
    user = check_session(request)
    
    if user:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'username': user.nombreusuario,
                'role': user.rol,
                'employee_name': user.empleado_nombre
            },
            'session_info': {
                'login_time': request.session.get('login_time'),
                'expires_at': request.session.get_expiry_date().isoformat() if request.session.get_expiry_date() else None
            }
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'message': 'Sesión no válida o expirada'
        })