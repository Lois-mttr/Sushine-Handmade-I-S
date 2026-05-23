# inventario/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, F
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import csv
import os
from datetime import datetime

# Importar decoradores de autenticación personalizados
from AuthLogin.decorators import (
    nexo_login_required,
    nexo_role_required,
    ajax_login_required,
    get_authenticated_user
)

# Importar modelos desde el módulo local
from .models import (
    Producto, 
    Ubicacion, 
    Categoria,
    obtener_productos_activos,
    obtener_productos_por_ubicacion,
    obtener_productos_bajo_stock,
    obtener_estadisticas_inventario,
    obtener_ubicaciones_con_productos,
    obtener_categorias_activas
)
from .forms import ProductoImagenForm

import logging

# Configurar logger para el módulo de inventario
logger = logging.getLogger('nexo.inventario')

@nexo_role_required(['admin', 'gerente', 'encargado_inventario', 'encargado_sucursal'])
def inventario_general(request):
    """
    Vista principal del inventario que muestra todos los productos
    con filtros por ubicación y búsqueda
    Requiere autenticación NEXO
    """
    try:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        rol_usuario = getattr(usuario_actual, 'rol', 'encargado_sucursal')
        logger.info(f"Usuario {nombreusuario} accedió al inventario general")

        # Restricción de ubicaciones según rol
        ubicaciones = obtener_ubicaciones_con_productos()
        if rol_usuario == 'encargado_sucursal':
            ubicaciones = [u for u in ubicaciones if u.nombreubicacion.lower() == 'sucursal']
        elif rol_usuario == 'gerente':
            ubicaciones = [u for u in ubicaciones if u.nombreubicacion.lower() in ['sucursal', 'taller']]
        # admin y otros ven todo

        # Obtener parámetros de filtrado desde la URL
        ubicacion_id = request.GET.get('ubicacion', '')
        busqueda = request.GET.get('busqueda', '')
        categoria_id = request.GET.get('categoria', '')
        orden = request.GET.get('orden', 'nombreproducto')
        page = request.GET.get('page', 1)

        # Query base de productos activos con relaciones optimizadas
        productos = obtener_productos_activos().select_related(
            'idubicacionpro', 'idcategoriapro'
        )
        # Aplicar restricción de ubicación por rol
        if rol_usuario == 'encargado_sucursal':
            productos = productos.filter(idubicacionpro__nombreubicacion__iexact='sucursal')
        elif rol_usuario == 'gerente':
            productos = productos.filter(idubicacionpro__nombreubicacion__in=['Sucursal', 'Taller'])

        # Aplicar filtros según los parámetros recibidos
        if ubicacion_id:
            try:
                ubicacion_id = int(ubicacion_id)
                productos = productos.filter(idubicacionpro_id=ubicacion_id)
                logger.debug(f"Filtro aplicado - Ubicación: {ubicacion_id}")
            except (ValueError, TypeError):
                messages.warning(request, 'ID de ubicación inválido')
                logger.warning(f"ID de ubicación inválido: {ubicacion_id}")

        if busqueda:
            productos = productos.filter(
                Q(nombreproducto__icontains=busqueda) |
                Q(descripcionproducto__icontains=busqueda) |
                Q(id_producto__icontains=busqueda)
            )
            logger.debug(f"Filtro aplicado - Búsqueda: {busqueda}")

        if categoria_id:
            try:
                categoria_id = int(categoria_id)
                productos = productos.filter(idcategoriapro_id=categoria_id)
                logger.debug(f"Filtro aplicado - Categoría: {categoria_id}")
            except (ValueError, TypeError):
                messages.warning(request, 'ID de categoría inválido')
                logger.warning(f"ID de categoría inválido: {categoria_id}")

        # Aplicar ordenamiento
        orden_mapping = {
            'nombre_asc': 'nombreproducto',
            'nombre_desc': '-nombreproducto',
            'existencia_asc': 'existenciaproducto',
            'existencia_desc': '-existenciaproducto',
            'precio_asc': 'precioproducto',
            'precio_desc': '-precioproducto',
        }
        
        orden_field = orden_mapping.get(orden, 'nombreproducto')
        productos = productos.order_by(orden_field)
        
        # Paginación
        paginator = Paginator(productos, 12)  # 12 productos por página
        productos_paginados = paginator.get_page(page)
        
        # Obtener datos para los filtros
        #ubicaciones = obtener_ubicaciones_con_productos()
        categorias = obtener_categorias_activas()
        
        # Calcular estadísticas generales
        stats = obtener_estadisticas_inventario(ubicacion_id if ubicacion_id else None)
        
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        nexo_user_role = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        
        context = {
            'page_title': 'Gestión de Inventario - NEXO',
            'productos': productos_paginados,
            'ubicaciones': ubicaciones,
            'categorias': categorias,
            'filtros': {
                'ubicacion_seleccionada': ubicacion_id,
                'busqueda': busqueda,
                'categoria_seleccionada': categoria_id,
                'orden': orden,
            },
            'estadisticas': stats,
            'total_paginas': paginator.num_pages,
            'pagina_actual': productos_paginados.number,
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'nexo_user_role': nexo_user_role,
        }
        
        return render(request, 'inventario/inventario_general.html', context)
        
    except Exception as e:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.error(f"Error en inventario_general para usuario {nombreusuario}: {str(e)}")
        messages.error(request, f'Error al cargar el inventario: {str(e)}')
        return render(request, 'inventario/inventario_general.html', {
            'page_title': 'Error - Inventario',
            'productos': [],
            'ubicaciones': [],
            'categorias': [],
            'filtros': {},
            'estadisticas': {},
            'usuario_actual': usuario_actual,
            'user_iniciales': obtener_iniciales_usuario(request),
        })

@nexo_login_required
def inventario_por_ubicacion(request, ubicacion_id):
    """
    Vista detallada del inventario para una ubicación específica
    Requiere autenticación NEXO
    """
    try:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        rol_usuario = getattr(usuario_actual, 'rol', 'encargado_sucursal')
        logger.info(f"Usuario {nombreusuario} accedió al inventario de ubicación {ubicacion_id}")

        # Obtener la ubicación o mostrar 404
        ubicacion = get_object_or_404(Ubicacion, id_ubicacion=ubicacion_id)

        # Validar acceso para encargado_sucursal
        if rol_usuario == 'encargado_sucursal' and ubicacion.nombreubicacion.lower() != 'sucursal':
            messages.error(request, 'No tiene permiso para ver productos fuera de la sucursal.')
            return redirect('inventario:inventario_general')

        # Obtener productos de la ubicación con optimización de consultas
        productos = obtener_productos_por_ubicacion(ubicacion_id)
        
        # Parámetros de filtrado
        busqueda = request.GET.get('busqueda', '')
        categoria_id = request.GET.get('categoria', '')
        orden = request.GET.get('orden', 'nombreproducto')
        
        # Aplicar filtros adicionales
        if busqueda:
            productos = productos.filter(
                Q(nombreproducto__icontains=busqueda) |
                Q(descripcionproducto__icontains=busqueda) |
                Q(id_producto__icontains=busqueda)
            )
            logger.debug(f"Filtro de búsqueda aplicado en ubicación {ubicacion_id}: {busqueda}")
        
        if categoria_id:
            try:
                categoria_id = int(categoria_id)
                productos = productos.filter(idcategoriapro_id=categoria_id)
                logger.debug(f"Filtro de categoría aplicado en ubicación {ubicacion_id}: {categoria_id}")
            except (ValueError, TypeError):
                messages.warning(request, 'ID de categoría inválido')
                logger.warning(f"ID de categoría inválido en ubicación {ubicacion_id}: {categoria_id}")
        
        # Ordenamiento
        orden_mapping = {
            'nombre_asc': 'nombreproducto',
            'nombre_desc': '-nombreproducto',
            'existencia_asc': 'existenciaproducto',
            'existencia_desc': '-existenciaproducto',
            'precio_asc': 'precioproducto',
            'precio_desc': '-precioproducto',
        }
        
        orden_field = orden_mapping.get(orden, 'nombreproducto')
        productos = productos.order_by(orden_field)
        
        # Obtener productos con bajo stock en esta ubicación
        productos_bajo_stock = productos.filter(
            existenciaproducto__lte=F('existenciaminima')
        )
        
        # Estadísticas específicas de la ubicación
        total_productos = productos.count()
        valor_total_inventario = productos.aggregate(
            total=Sum(F('existenciaproducto') * F('precioproducto'))
        )['total'] or 0
        
        # Productos por categoría en esta ubicación
        productos_por_categoria = productos.values(
            'idcategoriapro__nombrecategoria'
        ).annotate(
            cantidad=Count('id_producto'),
            total_existencia=Sum('existenciaproducto')
        ).order_by('-cantidad')
        
        # Categorías disponibles
        categorias = obtener_categorias_activas()
        
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        nexo_user_role = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        
        context = {
            'page_title': f'Inventario - {ubicacion.nombreubicacion}',
            'ubicacion': ubicacion,
            'productos': productos,
            'categorias': categorias,
            'productos_bajo_stock': productos_bajo_stock,
            'filtros': {
                'busqueda': busqueda,
                'categoria_seleccionada': categoria_id,
                'orden': orden,
            },
            'estadisticas': {
                'total_productos': total_productos,
                'valor_total': valor_total_inventario,
                'productos_bajo_stock': productos_bajo_stock.count(),
                'productos_por_categoria': productos_por_categoria,
            },
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'nexo_user_role': nexo_user_role,
        }
        
        return render(request, 'inventario/inventario_ubicacion.html', context)
        
    except Exception as e:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.error(f"Error en inventario_por_ubicacion para usuario {nombreusuario}: {str(e)}")
        messages.error(request, f'Error al cargar inventario de ubicación: {str(e)}')
        return redirect('inventario:inventario_general')

@nexo_login_required
def detalle_producto(request, producto_id, ubicacion_id=None):
    """
    Vista detallada de un producto específico por ubicación
    Requiere autenticación NEXO
    """
    try:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        rol_usuario = getattr(usuario_actual, 'rol', 'encargado_sucursal')
        logger.info(f"Usuario {nombreusuario} accedió al detalle del producto {producto_id} en ubicación {ubicacion_id or 'general'}")

        productos = Producto.objects.filter(id_producto=producto_id, estado=True).select_related('idubicacionpro', 'idcategoriapro')
        if ubicacion_id is not None:
            productos = productos.filter(idubicacionpro_id=ubicacion_id)

        # Validar acceso para encargado_sucursal
        if rol_usuario == 'encargado_sucursal':
            productos = productos.filter(idubicacionpro__nombreubicacion__iexact='sucursal')

        if productos.count() == 0:
            messages.error(request, 'No se encontró el producto solicitado o no tiene permiso para verlo.')
            return redirect('inventario:inventario_general')
        producto = productos.first()

        # Calcular información adicional
        valor_total_stock = 0
        if producto.precioproducto:
            valor_total_stock = producto.existenciaproducto * producto.precioproducto

        # Determinar el estado del stock
        stock_status = 'alto'
        if producto.existenciaproducto == 0:
            stock_status = 'agotado'
        elif producto.existenciaproducto <= (producto.existenciaminima or 5):
            stock_status = 'bajo'
        elif producto.existenciaproducto <= 20:
            stock_status = 'medio'

        # Productos relacionados (misma categoría, diferente producto)
        productos_relacionados = []
        if producto.idcategoriapro:
            productos_relacionados = Producto.objects.filter(
                idcategoriapro=producto.idcategoriapro,
                estado=True
            ).exclude(
                id_producto=producto.id_producto
            ).select_related('idubicacionpro')[:4]

        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        nexo_user_role = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'

        context = {
            'page_title': f'Producto - {producto.nombreproducto}',
            'producto': producto,
            'valor_total_stock': valor_total_stock,
            'stock_status': stock_status,
            'productos_relacionados': productos_relacionados,
            'necesita_reposicion': producto.necesita_reposicion,
            'imagen_form': ProductoImagenForm(),
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'nexo_user_role': nexo_user_role,
        }

        return render(request, 'inventario/detalle_producto.html', context)

    except Exception as e:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.error(f"Error en detalle_producto para usuario {nombreusuario}: {str(e)}")
        messages.error(request, f'Error al cargar detalle del producto: {str(e)}')
        return redirect('inventario:inventario_general')

@nexo_role_required(['admin', 'gerente', 'encargado_inventario'])
@require_http_methods(["POST"])
def actualizar_foto_producto(request, ubicacion_id, producto_id):
    """
    Sube una foto del producto y guarda la ruta relativa en imagenProductoRuta.
    La tabla ya tiene esa columna como texto, por eso no hace falta migrar la BD.
    """
    producto = get_object_or_404(
        Producto,
        id_producto=producto_id,
        idubicacionpro_id=ubicacion_id,
        estado=True
    )
    form = ProductoImagenForm(request.POST, request.FILES)

    if not form.is_valid():
        messages.error(request, 'Seleccione una imagen valida para el producto.')
        return redirect('inventario:detalle_producto_ubicacion', ubicacion_id, producto_id)

    imagen = form.cleaned_data['imagen']
    extension = os.path.splitext(imagen.name)[1].lower() or '.jpg'
    nombre_archivo = f"{producto.id_producto}{extension}"
    ruta_relativa = f"inventario/productos/{nombre_archivo}"
    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)

    if storage.exists(ruta_relativa):
        storage.delete(ruta_relativa)

    ruta_guardada = storage.save(ruta_relativa, imagen)
    producto.imagenproductoruta = ruta_guardada.replace('\\', '/')
    producto.save(update_fields=['imagenproductoruta'])

    messages.success(request, f'Foto actualizada para {producto.nombreproducto}.')
    return redirect('inventario:detalle_producto_ubicacion', ubicacion_id, producto_id)

@ajax_login_required
@require_http_methods(["GET"])
def inventario_stats_ajax(request):
    """
    Vista AJAX para obtener estadísticas del inventario en tiempo real
    Requiere autenticación NEXO para peticiones AJAX
    """
    try:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.debug(f"Solicitud AJAX de estadísticas por usuario {nombreusuario}")
        
        ubicacion_id = request.GET.get('ubicacion')
        
        # Obtener estadísticas usando la función auxiliar
        stats = obtener_estadisticas_inventario(ubicacion_id)
        
        # Formatear los datos para JSON
        response_data = {
            'success': True,
            'stats': {
                'total_productos': stats['total_productos'],
                'productos_bajo_stock': stats['productos_bajo_stock'],
                'productos_sin_stock': stats['productos_sin_stock'],
                'valor_total': float(stats['valor_total_inventario']),
                'categorias': list(stats['productos_por_categoria'])
            },
            'timestamp': timezone.now().isoformat(),
            'usuario': nombreusuario
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.error(f"Error en inventario_stats_ajax para usuario {nombreusuario}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error al obtener estadísticas del inventario'
        }, status=500)

@ajax_login_required
def busqueda_rapida_ajax(request):
    """
    Vista AJAX para búsqueda rápida de productos
    Requiere autenticación NEXO para peticiones AJAX
    """
    try:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        query = request.GET.get('q', '').strip()
        logger.debug(f"Búsqueda rápida por usuario {nombreusuario}: {query}")
        
        if len(query) < 2:
            return JsonResponse({
                'success': False,
                'message': 'La búsqueda debe tener al menos 2 caracteres'
            })
        
        # Buscar productos que coincidan
        productos = Producto.objects.filter(
            Q(nombreproducto__icontains=query) |
            Q(id_producto__icontains=query) |
            Q(descripcionproducto__icontains=query),
            estado=True
        ).select_related('idubicacionpro', 'idcategoriapro')[:10]
        
        # Formatear resultados
        resultados = []
        for producto in productos:
            resultados.append({
                'id': producto.id_producto,
                'nombre': producto.nombreproducto,
                'descripcion': producto.descripcionproducto or '',
                'existencia': producto.existenciaproducto,
                'precio': float(producto.precioproducto) if producto.precioproducto else 0,
                'ubicacion': producto.idubicacionpro.nombreubicacion,
                'categoria': producto.idcategoriapro.nombrecategoria if producto.idcategoriapro else '',
                'url': reverse('inventario:detalle_producto', args=[producto.id_producto]),
                'necesita_reposicion': producto.necesita_reposicion,
            })
        
        return JsonResponse({
            'success': True,
            'resultados': resultados,
            'total': len(resultados),
            'usuario': nombreusuario
        })
        
    except Exception as e:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.error(f"Error en busqueda_rapida_ajax para usuario {nombreusuario}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error en la búsqueda'
        }, status=500)

@nexo_role_required(['admin'])
def configurar_alertas_stock(request):
    """
    Vista para configurar alertas de stock bajo
    Solo para administradores y gerentes
    """
    try:
        usuario_actual = getattr(request, 'nexo_user', None)
        rol_usuario = getattr(usuario_actual, 'rol', 'encargado_sucursal')
        logger.info(f"Configuración de alertas accedida por usuario {usuario_actual.nombreusuario}")
        # Filtrar productos según rol
        if rol_usuario == 'encargado_sucursal':
            productos_bajo_stock = obtener_productos_bajo_stock().filter(idubicacionpro__nombreubicacion__iexact='sucursal')
        elif rol_usuario == 'gerente':
            productos_bajo_stock = obtener_productos_bajo_stock().filter(idubicacionpro__nombreubicacion__in=['Sucursal', 'Taller'])
        else:
            productos_bajo_stock = obtener_productos_bajo_stock()
        
        if request.method == 'POST':
            # Procesar configuración de alertas
            producto_id = request.POST.get('producto_id')
            stock_minimo = request.POST.get('stock_minimo')
            
            if producto_id and stock_minimo:
                try:
                    producto = get_object_or_404(Producto, id_producto=producto_id)
                    producto.existenciaminima = int(stock_minimo)
                    producto.save()
                    
                    logger.info(f"Stock mínimo actualizado para producto {producto_id} por usuario {usuario_actual.nombreusuario}")
                    messages.success(request, f'Stock mínimo actualizado para {producto.nombreproducto}')
                    
                except (ValueError, TypeError):
                    messages.error(request, 'Valor de stock mínimo inválido')
                    logger.warning(f"Valor de stock mínimo inválido: {stock_minimo}")
            
            return redirect('inventario:inventario_general')
        
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        nexo_user_role = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        
        context = {
            'page_title': 'Configurar Alertas de Stock',
            'productos_bajo_stock': productos_bajo_stock,
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'nexo_user_role': nexo_user_role,
        }
        
        return render(request, 'inventario/configurar_alertas.html', context)
        
    except Exception as e:
        usuario_actual = getattr(request, 'nexo_user', None)
        nombreusuario = getattr(usuario_actual, 'nombreusuario', 'Invitado')
        logger.error(f"Error en configurar_alertas_stock para usuario {nombreusuario}: {str(e)}")
        messages.error(request, f'Error al configurar alertas: {str(e)}')
        return redirect('inventario:inventario_general')

# Vista auxiliar para verificar permisos de usuario
def verificar_permisos_inventario(user, accion='ver'):
    """
    Función auxiliar para verificar permisos específicos del inventario
    """
    if not user or not user.activo:
        return False
    
    # Definir permisos por rol
    permisos_por_rol = {
        'admin': ['ver', 'editar', 'eliminar', 'exportar', 'configurar'],
        'gerente': ['ver', 'editar', 'exportar', 'configurar'],
        'encargado_inventario': ['ver', 'editar', 'exportar'],
        'encargado_sucursal': ['ver'],
        'vendedor': ['ver'],
    }
    
    rol_usuario = user.rol or 'encargado_sucursal'
    permisos_usuario = permisos_por_rol.get(rol_usuario, ['ver'])
    
    return accion in permisos_usuario

# Middleware personalizado para logging de acceso al inventario
class InventarioAccessMiddleware:
    """
    Middleware para registrar accesos al módulo de inventario
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si es una vista del inventario
        if request.path.startswith('/inventario/'):
            user = get_authenticated_user(request)
            if user:
                logger.info(f"Acceso al inventario - Usuario: {user.nombreusuario}, IP: {request.META.get('REMOTE_ADDR')}, Path: {request.path}")
        
        response = self.get_response(request)
        return response

def obtener_iniciales_usuario(request):
    """
    Devuelve las iniciales del usuario autenticado de forma segura para la plantilla.
    """
    user = getattr(request, 'nexo_user', None)
    if user and hasattr(user, 'nombreusuario') and user.nombreusuario:
        return user.nombreusuario[:2].upper()
    elif hasattr(user, 'username') and user.username:
        return user.username[:2].upper()
    return 'IN'
