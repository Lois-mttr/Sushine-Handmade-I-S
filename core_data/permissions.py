import json
from pathlib import Path

from django.conf import settings


MODULE_CHOICES = [
    ('dashboard', 'Dashboard'),
    ('inventario', 'Inventario'),
    ('produccion', 'Producción'),
    ('ventas', 'Ventas'),
    ('devolucion', 'Devoluciones'),
    ('clientes', 'Clientes'),
    ('reportes', 'Reportes'),
    ('configuracion', 'Configuración'),
]

DEFAULT_MENU_PERMISSIONS = {
    'admin': [module for module, _label in MODULE_CHOICES],
    'gerente': ['dashboard', 'inventario', 'reportes', 'configuracion'],
    'encargado_inventario': ['dashboard', 'inventario', 'reportes', 'configuracion'],
    'encargado_sucursal': ['dashboard', 'inventario', 'ventas', 'reportes', 'configuracion'],
    'vendedor': ['dashboard', 'ventas', 'clientes', 'configuracion'],
    'cajero': ['dashboard', 'ventas', 'configuracion'],
    'ventas': ['dashboard', 'ventas', 'clientes', 'configuracion'],
    'usuario': ['dashboard', 'configuracion'],
}

CONFIG_PATH = Path(settings.BASE_DIR) / 'config' / 'menu_permissions.json'


def load_menu_permissions_config():
    config = {role: list(modules) for role, modules in DEFAULT_MENU_PERMISSIONS.items()}
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open('r', encoding='utf-8') as file:
                stored = json.load(file)
            for role, modules in stored.items():
                if isinstance(modules, list):
                    valid_modules = {module for module, _label in MODULE_CHOICES}
                    config[role] = [module for module in modules if module in valid_modules]
    except (OSError, json.JSONDecodeError):
        pass
    return config


def save_menu_permissions_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    valid_modules = {module for module, _label in MODULE_CHOICES}
    clean_config = {}
    for role, modules in config.items():
        clean_config[role] = [module for module in modules if module in valid_modules]
    with CONFIG_PATH.open('w', encoding='utf-8') as file:
        json.dump(clean_config, file, ensure_ascii=False, indent=2)


def get_role_modules(role):
    role = role or 'usuario'
    config = load_menu_permissions_config()
    return set(config.get(role, config.get('usuario', [])))


def get_menu_permissions_for_role(role, authenticated=False):
    modules = get_role_modules(role)
    return {
        module: authenticated and module in modules
        for module, _label in MODULE_CHOICES
    }


def module_from_request(request):
    resolver = getattr(request, 'resolver_match', None)
    namespace = getattr(resolver, 'namespace', '') or ''
    app_name = getattr(resolver, 'app_name', '') or ''
    url_name = getattr(resolver, 'url_name', '') or ''
    route_name = namespace or app_name

    mapping = {
        'dashboard': 'dashboard',
        'inventario': 'inventario',
        'crud': 'produccion',
        'ventas': 'ventas',
        'devolucion': 'devolucion',
        'clientes': 'clientes',
        'informes': 'reportes',
        'Informes': 'reportes',
        'auth': 'configuracion',
    }

    if route_name in mapping:
        return mapping[route_name]
    if url_name in ('configuracion', 'perfil', 'editar_perfil'):
        return 'configuracion'
    return None


def role_has_module_permission(role, module):
    if not module:
        return False
    return module in get_role_modules(role)
