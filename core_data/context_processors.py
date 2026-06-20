from core_data.models import Usuario


COLORES_NEXO = {
    'primary': '#39bfb2',
    'secondary_yellow': '#F2CE16',
    'accent_orange': '#F29D35',
    'accent_dark_orange': '#F28627',
    'bg_light': '#eaeef3',
    'bg_very_light': '#F2F2F2',
    'white': '#ffffff',
    'text_dark': '#374151',
    'text_medium': '#6b7280',
    'text_light': '#9ca3af',
    'success': '#39bfb2',
    'warning': '#f29d35',
    'danger': '#f28627',
    'info': '#4ecdc4',
}


def nexo_template_context(request):
    user = getattr(request, 'nexo_user', None)

    if not user:
        user_id = request.session.get('user_id')
        if user_id:
            try:
                user = Usuario.objects.get(idusuario=user_id, activo=True)
            except Usuario.DoesNotExist:
                user = None

    nombre = user.nombreusuario if user and user.nombreusuario else ''
    rol = user.rol if user and user.rol else ''

    menu_permissions = {
        'dashboard': bool(user),
        'inventario': rol in ['admin', 'gerente', 'encargado_inventario', 'encargado_sucursal'],
        'produccion': rol == 'admin',
        'reabastecimiento': False,
        'ventas': rol in ['admin', 'encargado_sucursal', 'vendedor', 'cajero', 'ventas'],
        'devolucion': rol == 'admin',
        'clientes': rol in ['admin', 'ventas'],
        'reportes': bool(user),
        'configuracion': bool(user),
    }

    return {
        'usuario_actual': user,
        'user_iniciales': nombre[:2].upper() if nombre else 'IN',
        'nexo_user_role': rol or 'Usuario',
        'menu_permissions': menu_permissions,
        'header_subtitle': 'Sistema NEXO',
        'colores': COLORES_NEXO,
    }
