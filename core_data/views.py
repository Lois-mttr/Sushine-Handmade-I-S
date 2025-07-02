
# Create your views here.
"""
Vistas personalizadas para manejo de errores
Sistema NEXO - Sunshine Handmade
"""
from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden, HttpResponseBadRequest

def custom_404_view(request, exception=None):
    """
    Vista personalizada para error 404 - Página no encontrada
    """
    context = {
        'page_title': 'Página No Encontrada - Error 404',
        'error_code': '404',
        'error_title': 'Página No Encontrada',
        'error_message': 'Lo sentimos, la página que está buscando no existe o ha sido movida.',
        'error_suggestions': [
            'Verifique que la URL esté escrita correctamente',
            'Regrese a la página anterior usando el botón de su navegador',
            'Vaya al inicio del sistema',
            'Contacte al administrador si el problema persiste'
        ],
        'show_search': True,
        'user_info': {
            'name': request.session.get('usuario_nombre', 'Usuario'),
            'role': request.session.get('usuario_rol', 'usuario'),
            'id': request.session.get('usuario_id')
        }
    }
    
    response = render(request, 'error/404.html', context)
    response.status_code = 404
    return response

def custom_500_view(request):
    """
    Vista personalizada para error 500 - Error interno del servidor
    """
    context = {
        'page_title': 'Error Interno del Servidor - Error 500',
        'error_code': '500',
        'error_title': 'Error Interno del Servidor',
        'error_message': 'Ha ocurrido un error interno en el servidor. Nuestro equipo técnico ha sido notificado.',
        'error_suggestions': [
            'Intente recargar la página en unos minutos',
            'Regrese a la página principal',
            'Si el problema persiste, contacte al administrador del sistema',
            'Guarde su trabajo antes de continuar'
        ],
        'show_search': False,
        'user_info': {
            'name': request.session.get('usuario_nombre', 'Usuario') if hasattr(request, 'session') else 'Usuario',
            'role': request.session.get('usuario_rol', 'usuario') if hasattr(request, 'session') else 'usuario',
            'id': request.session.get('usuario_id') if hasattr(request, 'session') else None
        }
    }
    
    response = render(request, 'error/500.html', context)
    response.status_code = 500
    return response

def custom_403_view(request, exception=None):
    """
    Vista personalizada para error 403 - Acceso denegado
    """
    context = {
        'page_title': 'Acceso Denegado - Error 403',
        'error_code': '403',
        'error_title': 'Acceso Denegado',
        'error_message': 'No tiene permisos suficientes para acceder a esta página o realizar esta acción.',
        'error_suggestions': [
            'Verifique que tenga los permisos necesarios',
            'Inicie sesión con una cuenta autorizada',
            'Contacte al administrador para solicitar acceso',
            'Regrese a una página autorizada'
        ],
        'show_search': False,
        'user_info': {
            'name': request.session.get('usuario_nombre', 'Usuario'),
            'role': request.session.get('usuario_rol', 'usuario'),
            'id': request.session.get('usuario_id')
        }
    }
    
    response = render(request, 'error/403.html', context)
    response.status_code = 403
    return response

def custom_400_view(request, exception=None):
    """
    Vista personalizada para error 400 - Solicitud incorrecta
    """
    context = {
        'page_title': 'Solicitud Incorrecta - Error 400',
        'error_code': '400',
        'error_title': 'Solicitud Incorrecta',
        'error_message': 'La solicitud enviada no pudo ser procesada debido a un error en los datos.',
        'error_suggestions': [
            'Verifique que todos los campos estén completos',
            'Asegúrese de que los datos sean válidos',
            'Intente enviar el formulario nuevamente',
            'Contacte al soporte técnico si el problema continúa'
        ],
        'show_search': False,
        'user_info': {
            'name': request.session.get('usuario_nombre', 'Usuario'),
            'role': request.session.get('usuario_rol', 'usuario'),
            'id': request.session.get('usuario_id')
        }
    }
    
    response = render(request, 'error/400.html', context)
    response.status_code = 400
    return response

def custom_csrf_failure_view(request, reason=""):
    """
    Vista personalizada para errores CSRF
    """
    context = {
        'page_title': 'Error de Seguridad - CSRF',
        'error_code': 'CSRF',
        'error_title': 'Error de Verificación de Seguridad',
        'error_message': 'La solicitud no pudo ser procesada por razones de seguridad. El token CSRF es inválido o ha expirado.',
        'error_suggestions': [
            'Recargue la página e intente nuevamente',
            'Asegúrese de que las cookies estén habilitadas',
            'No use el botón "Atrás" del navegador en formularios',
            'Si el problema persiste, cierre sesión e inicie nuevamente'
        ],
        'show_search': False,
        'csrf_reason': reason,
        'user_info': {
            'name': request.session.get('usuario_nombre', 'Usuario'),
            'role': request.session.get('usuario_rol', 'usuario'),
            'id': request.session.get('usuario_id')
        }
    }
    
    response = render(request, 'error/csrf.html', context)
    response.status_code = 403
    return response
