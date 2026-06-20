from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils.html import strip_tags
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
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from .forms import RegisterForm, ForgotPasswordForm, ResetPasswordForm, PerfilUsuarioForm, ConfiguracionCuentaForm
from core_data.models import Usuario
import hashlib
import secrets
import logging

# Create your views here.
logger = logging.getLogger('nexo.auth')

def obtener_persona_usuario(user):
    if user and user.idempusuario and user.idempusuario.idpersonaemp:
        return user.idempusuario.idpersonaemp
    return None

def contexto_usuario_base(user, page_title):
    nombre = user.nombreusuario if user and user.nombreusuario else 'Invitado'
    return {
        'page_title': page_title,
        'usuario_actual': user,
        'user_iniciales': nombre[:2].upper(),
        'nexo_user_role': user.rol if user and user.rol else 'Usuario',
    }

def usuario_requerido(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        user = Usuario.objects.select_related('idempusuario__idpersonaemp').get(
            idusuario=user_id,
            activo=True
        )
        request.nexo_user = user
        return user
    except Usuario.DoesNotExist:
        request.session.flush()
        return None

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Vista principal para el inicio de sesiÃ³n - COMPLETAMENTE CORREGIDA
    """
    logger.debug(f"Login view called - Method: {request.method}, Path: {request.path}")
    
    # IMPORTANTE: Verificar si el usuario ya estÃ¡ autenticado
    user_id = request.session.get('user_id')
    if user_id:
        try:
            # Verificar que el usuario aÃºn existe y estÃ¡ activo
            user = Usuario.objects.get(idusuario=user_id, activo=True)
            logger.info(f"Usuario ya autenticado redirigido: {user.nombreusuario}")
            return redirect('/dashboard/')
        except Usuario.DoesNotExist:
            # Usuario no existe, limpiar sesiÃ³n
            request.session.flush()
            logger.warning(f"SesiÃ³n limpiada para usuario inexistente: {user_id}")
    
    if request.method == 'GET':
        # Mostrar formulario de login
        logger.debug("Mostrando formulario de login")
        form = LoginForm()
        context = {
            'form': form,
            'title': 'Iniciar SesiÃ³n - NEXO',
            'page_name': 'login',
            'system_name': 'NEXO - Sistema de Inventario y Ventas'
        }
        return render(request, 'AuthLogin/login.html', context)
    
    elif request.method == 'POST':
        logger.debug("Procesando POST de login")
        # Verificar si es una peticiÃ³n AJAX
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
        
        # Verificar si la IP estÃ¡ bloqueada
        if is_ip_blocked(client_ip):
            logger.warning(f"Intento de login desde IP bloqueada: {client_ip}")
            return JsonResponse({
                'success': False,
                'message': 'IP bloqueada temporalmente. Intenta mÃ¡s tarde.',
                'blocked': True,
                'lock_seconds': 20,
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
        
        # ValidaciÃ³n bÃ¡sica
        if not username or not password:
            return handle_failed_login(request, client_ip, 'Usuario y contraseña son obligatorios')
        
        if len(username) > 15:
            return handle_failed_login(request, client_ip, 'Usuario no puede tener mas de 15 caracteres')
        
        # Intentar autenticaciÃ³n directa (password ya viene hasheado)
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
    AutenticaciÃ³n directa con la base de datos
    Ahora recibe el hash directamente (ya hasheado en el frontend)
    """
    try:
        # Buscar usuario en la base de datos
        user = Usuario.objects.get(nombreusuario=username, activo=True)
        
        # Comparar directamente con el hash almacenado
        if user.passusuario == password_hash:
            logger.info(f"AutenticaciÃ³n exitosa para usuario: {username}")
            return user
        else:
            logger.warning(f"Contraseña incorrecta para usuario: {username}")
            return None
            
    except Usuario.DoesNotExist:
        logger.warning(f"Usuario no encontrado: {username}")
        return None
    except Exception as e:
        logger.error(f"Error en autenticaciÃ³n para usuario {username}: {e}")
        return None

def process_traditional_login(request):
    """
    Procesar el intento de inicio de sesiÃ³n (mÃ©todo tradicional sin AJAX)
    """
    # Obtener IP del cliente para control de intentos
    client_ip = get_client_ip(request)
    
    # Verificar si la IP estÃ¡ bloqueada
    if is_ip_blocked(client_ip):
        messages.error(request, 'IP bloqueada temporalmente. Intenta mÃ¡s tarde.')
        return render(request, 'AuthLogin/login.html', {'form': LoginForm()})
    
    # Crear formulario con datos POST
    form = LoginForm(request.POST)
    
    if form.is_valid():
        # Credenciales vÃ¡lidas
        user = form.get_user()
        
        if user:
            # Login exitoso
            response_data = handle_successful_login(request, user, client_ip, as_json=False)
            if response_data.get('success'):
                messages.success(request, 'Inicio de sesiÃ³n exitoso')
                return redirect(response_data.get('redirect_url', '/dashboard/'))
        else:
            # Credenciales incorrectas
            handle_failed_login(request, client_ip, 'Credenciales incorrectas')
            messages.error(request, 'Credenciales incorrectas')
    else:
        # Errores de validaciÃ³n
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{error}")
    
    return render(request, 'AuthLogin/login.html', {'form': form})

def handle_successful_login(request, user, client_ip, as_json=True):
    """
    Manejar login exitoso
    """
    try:
        # Limpiar intentos fallidos
        clear_failed_attempts(client_ip)
        
        # Crear sesiÃ³n de usuario
        request.session['user_id'] = user.idusuario
        request.session['username'] = user.nombreusuario
        request.session['user_role'] = user.rol or 'Usuario'
        request.session['employee_id'] = user.idempusuario.idempleado if user.idempusuario else None
        request.session['login_time'] = timezone.now().isoformat()
        
        # Configurar expiraciÃ³n de sesiÃ³n (8 horas)
        request.session.set_expiry(28800)
        
        # Registrar login exitoso en logs
        log_login_attempt(user.nombreusuario, client_ip, True, 'Login exitoso')
        
        response_data = {
            'success': True,
            'message': 'Inicio de sesion exitoso.',
            'redirect_url': '/dashboard/',
            'user': {
                'username': user.nombreusuario,
                'role': user.rol or 'Usuario',
                'employee_name': user.empleado_nombre
            }
        }

        if as_json:
            return JsonResponse(response_data)
        return response_data
        
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
                f'IP bloqueada despuÃ©s de {attempts} intentos fallidos'
            )
            return JsonResponse({
                'success': False,
                'message': 'Demasiados intentos fallidos. IP bloqueada por 20 segundos.',
                'blocked': True,
                'lock_seconds': 20,
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
    Verificar si una IP estÃ¡ bloqueada
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
        timestamp = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %I:%M:%S %p')
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
    Vista para cerrar sesiÃ³n
    """
    try:
        username = request.session.get('username', 'unknown')
        client_ip = get_client_ip(request)
        
        # Limpiar sesiÃ³n
        request.session.flush()
        
        # Registrar logout
        log_login_attempt(username, client_ip, True, 'Logout exitoso')
        
        # Verificar si es peticiÃ³n AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'SesiÃ³n cerrada exitosamente',
                'redirect_url': '/login/'
            })
        else:
            messages.success(request, 'SesiÃ³n cerrada exitosamente')
            return redirect('auth:login')
            
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error al cerrar sesiÃ³n'
            })
        else:
            messages.error(request, 'Error al cerrar sesiÃ³n')
            return redirect('auth:login')

def check_session(request):
    """
    Verificar si la sesiÃ³n del usuario es vÃ¡lida
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return False
    
    try:
        # Verificar que el usuario aÃºn existe y estÃ¡ activo
        user = Usuario.objects.get(idusuario=user_id, activo=True)
        return user
    except Usuario.DoesNotExist:
        # Usuario no existe o estÃ¡ inactivo, limpiar sesiÃ³n
        request.session.flush()
        logger.warning(f"SesiÃ³n limpiada para usuario inexistente o inactivo: {user_id}")
        return False

@require_http_methods(["GET"])
def check_session_ajax(request):
    """
    Endpoint AJAX para verificar estado de sesiÃ³n
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
            'message': 'SesiÃ³n no vÃ¡lida o expirada'
        })
    

@never_cache
@require_http_methods(["GET"])
def perfil_view(request):
    user = usuario_requerido(request)
    if not user:
        messages.warning(request, 'Debes iniciar sesion para ver tu perfil.')
        return redirect('auth:login')

    persona = obtener_persona_usuario(user)
    context = contexto_usuario_base(user, 'Mi Perfil')
    context.update({'persona': persona, 'empleado': user.idempusuario})
    return render(request, 'AuthLogin/profile.html', context)

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def editar_perfil_view(request):
    user = usuario_requerido(request)
    if not user:
        messages.warning(request, 'Debes iniciar sesion para editar tu perfil.')
        return redirect('auth:login')

    persona = obtener_persona_usuario(user)
    initial = {'nombreusuario': user.nombreusuario, 'correo': user.correo or ''}
    if persona:
        initial.update({
            'primernombre': persona.primernombre,
            'segundonombre': persona.segundonombre or '',
            'primerapellido': persona.primerapellido,
            'segundoapellido': persona.segundoapellido or '',
            'direccion': persona.direccion,
        })

    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, user=user, persona=persona)
        if form.is_valid():
            form.save()
            request.session['username'] = user.nombreusuario
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('auth:perfil')
        messages.error(request, 'Revise los campos marcados antes de guardar.')
    else:
        form = PerfilUsuarioForm(initial=initial, user=user, persona=persona)

    context = contexto_usuario_base(user, 'Editar Perfil')
    context.update({'form': form, 'persona': persona})
    return render(request, 'AuthLogin/edit_profile.html', context)

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def configuracion_view(request):
    user = usuario_requerido(request)
    if not user:
        messages.warning(request, 'Debes iniciar sesion para ver la configuracion.')
        return redirect('auth:login')

    if request.method == 'POST':
        form = ConfiguracionCuentaForm(request.POST, user=user)
        if form.is_valid():
            if form.cleaned_data.get('new_password'):
                form.save()
                messages.success(request, 'Contraseña actualizada correctamente. Usala en tu proximo inicio de sesion.')
            else:
                messages.info(request, 'No se realizaron cambios en la configuracion.')
            return redirect('auth:configuracion')
        messages.error(request, 'No se pudo actualizar la configuracion.')
    else:
        form = ConfiguracionCuentaForm(user=user)

    context = contexto_usuario_base(user, 'Configuracion')
    context.update({
        'form': form,
        'session_expiry': request.session.get_expiry_date(),
        'login_time': request.session.get('login_time'),
    })
    return render(request, 'AuthLogin/settings.html', context)

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request,
                    'Â¡Registro exitoso! Ahora puedes iniciar sesiÃ³n.'
                )
                return redirect('auth:login')
            except IntegrityError as e:
                logger.error(f"Error de integridad al registrar: {str(e)}")
                messages.error(
                    request,
                    'Error al registrar. El usuario o correo ya existen.'
                )
            except Exception as e:
                logger.error(f"Error al registrar usuario: {str(e)}", exc_info=True)
                messages.error(
                    request,
                    'OcurriÃ³ un error inesperado. Por favor intenta nuevamente.'
                )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'AuthLogin/register.html', {
        'form': form,
        'title': 'Registro - NEXO',
        'page_name': 'register'
    })

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    """
    Vista para solicitar recuperaciÃ³n de contraseña
    """
    if request.method == 'GET':
        # Verificar si el usuario ya estÃ¡ autenticado
        if request.session.get('user_id'):
            return redirect('/dashboard/')
            
        form = ForgotPasswordForm()
        return render(request, 'AuthLogin/forgot_password.html', {
            'form': form,
            'title': 'Recuperar Contraseña - NEXO',
            'page_name': 'forgot_password'
        })
    
    elif request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Procesamiento AJAX
            if form.is_valid():
                email = form.cleaned_data['email']
                try:
                    send_password_reset_email(request, email)
                    return JsonResponse({
                        'success': True,
                        'message': 'Revisa tu correo para continuar.'
                    })
                except Exception as e:
                    logger.error(f"Error al enviar correo de recuperaciÃ³n: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Error al enviar el correo. Intenta nuevamente.'
                    })
            else:
                errors = {}
                for field in form.errors:
                    errors[field] = form.errors[field][0]
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
        else:
            # Procesamiento tradicional
            if form.is_valid():
                email = form.cleaned_data['email']
                try:
                    send_password_reset_email(request, email)
                    messages.success(request, 'Revisa tu correo para continuar.')
                    return redirect('auth:login')
                except Exception as e:
                    logger.error(f"Error al enviar correo de recuperaciÃ³n: {e}")
                    messages.error(request, 'Error al enviar el correo. Intenta nuevamente.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
            
            return render(request, 'AuthLogin/forgot_password.html', {
                'form': form,
                'title': 'Recuperar Contraseña - NEXO',
                'page_name': 'forgot_password'
            })

@never_cache
@csrf_protect
@require_http_methods(["GET", "POST"])
def reset_password_view(request, uidb64, token):
    """
    Vista completa para restablecer contraseña con manejo de errores
    """
    # VerificaciÃ³n inicial del token
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(idusuario=uid)

        if not validate_password_reset_token(user, token):
            raise ValueError("Token invÃ¡lido o expirado")

    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist) as e:
        logger.error(f"Error en validaciÃ³n de token: {str(e)}")
        messages.error(request, 'El enlace de recuperaciÃ³n no es vÃ¡lido o ha expirado.')
        return redirect('auth:forgot_password')

    # Procesamiento del formulario
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                new_password = form.cleaned_data['new_password']

                # ValidaciÃ³n adicional de contraseÃ±a
                if len(new_password) < 8:
                    raise ValueError("La contraseña debe tener al menos 8 caracteres")

                # Actualizar contraseÃ±a usando el mÃ©todo del modelo
                user.set_password(new_password)

                # Limpiar token y resetear intentos fallidos
                cache.delete(f"pw_reset_{user.idusuario}")
                user.intentos_fallidos = 0
                user.save()

                # Registrar el cambio
                logger.info(f"Contraseña actualizada para usuario ID {user.idusuario}")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Contraseña actualizada correctamente',
                        'redirect_url': reverse('auth:login')
                    })

                messages.success(request, 'Â¡Contraseña actualizada! Ya puedes iniciar sesiÃ³n.')
                return redirect('auth:login')

            except Exception as e:
                logger.error(f"Error al actualizar contraseña: {str(e)}")
                error_msg = f"Error al actualizar la contraseña: {str(e)}"

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })

                messages.error(request, error_msg)
        else:
            # Manejar errores de validaciÃ³n del formulario
            errors = {f: e[0] for f, e in form.errors.items()}
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })

            for field, error in errors.items():
                messages.error(request, f"{field.capitalize()}: {error}")

    # Mostrar formulario (GET request o formulario invÃ¡lido)
    form = ResetPasswordForm()
    return render(request, 'AuthLogin/reset_password.html', {
        'form': form,
        'title': 'Restablecer Contraseña',
        'page_name': 'reset_password',
        'valid_link': True
    })


def generate_password_reset_token(user):
    """
    Genera un token seguro para recuperación de contraseña
    """
    if not user or not user.idusuario:
        raise ValueError("Usuario inválido para generar token")

    # Usamos datos del usuario + timestamp + secret key
    timestamp = str(int(timezone.now().timestamp()))
    raw_token = f"{user.idusuario}{user.passusuario}{timestamp}{settings.SECRET_KEY}"

    # Generar hash SHA-256
    token = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    # Guardar en cache con prefijo único
    cache_key = f"pw_reset_{user.idusuario}"
    cache.set(cache_key, token, 86400)  # 24 horas de expiración

    return token


def validate_password_reset_token(user, token):
    """
    Valida si el token de recuperación es válido
    """
    if not user or not token:
        return False

    cache_key = f"pw_reset_{user.idusuario}"
    stored_token = cache.get(cache_key)

    # Verificar coincidencia y limpiar si no coincide
    if stored_token != token:
        cache.delete(cache_key)
        return False
    return True


def get_user_for_password_reset(email):
    normalized_email = (email or '').strip().lower()
    user = Usuario.objects.filter(
        correo__iexact=normalized_email,
        activo=True
    ).order_by('idusuario').first()

    if user:
        return user

    return Usuario.objects.filter(
        idempusuario__correo__iexact=normalized_email,
        activo=True
    ).order_by('idusuario').first()


def send_password_reset_email(request, email):
    """
    Envía correo con enlace para restablecer contraseña
    """
    try:
        user = get_user_for_password_reset(email)
        if not user:
            raise Usuario.DoesNotExist

        # Generar token seguro
        token = generate_password_reset_token(user)

        # Construir URL absoluta usando reverse
        uid = urlsafe_base64_encode(force_bytes(user.idusuario))
        reset_url = request.build_absolute_uri(
            reverse('auth:reset_password', kwargs={
                'uidb64': uid,
                'token': token
            })
        )

        # Renderizar contenido del correo
        mail_subject = 'Restablecer tu contraseña en NEXO'
        message = render_to_string('AuthLogin/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': 24
        })

        send_mail(
            mail_subject,
            strip_tags(message),
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=message
        )

        logger.info(f"Correo de recuperación enviado a {email}")
        return True

    except Usuario.DoesNotExist:
        logger.warning(f"Intento de recuperación para email no registrado: {email}")
        raise ValueError("No existe usuario con este correo electrónico")
    except Exception as e:
        if 'user' in locals() and user:
            cache.delete(f"pw_reset_{user.idusuario}")
        logger.error(f"Error al enviar correo de recuperación: {str(e)}")
        raise


def update_user_password(request):
    """Vista segura para actualizar contraseñas"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Validaciones básicas
        if not all([user_id, new_password, confirm_password]):
            raise ValueError("Todos los campos son requeridos")

        if new_password != confirm_password:
            raise ValueError("Las contraseñas no coinciden")

        if len(new_password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        # Obtener usuario
        user = Usuario.objects.get(idusuario=user_id)

        # Actualizar contraseña
        if not user.save_password(new_password):
            raise ValueError("No se pudo actualizar la contraseña")

        # Limpiar cachés
        cache.delete_many([
            f"user_{user.idusuario}_auth",
            f"pw_reset_{user.idusuario}",
            f"login_attempts_{user.nombreusuario}"
        ])

        return JsonResponse({
            'success': True,
            'message': 'Contraseña actualizada exitosamente'
        })

    except Usuario.DoesNotExist:
        logger.warning(f"Intento de actualizar contraseña para usuario inexistente: {user_id}")
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except ValueError as ve:
        logger.warning(f"Error de validaciÃ³n: {str(ve)}")
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'OcurriÃ³ un error al procesar la solicitud'}, status=500)
