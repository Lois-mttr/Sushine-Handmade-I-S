# Create your views here.
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q, Avg, F
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import transaction
from AuthLogin.views import check_session
from AuthLogin.decorators import (
    nexo_login_required,
    nexo_role_required,
    ajax_login_required,
    get_authenticated_user
)
from core_data.models import (
    Usuario, Producto, Venta, Devolucion, 
    Detalleventa, Detalledevolucion, Cliente, 
    Empleado, Productosproduccion, Detalleproduccion,
    Categoria, Ubicacion
)
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar logging
logger = logging.getLogger(__name__)

class DashboardService:
    """Servicio mejorado para manejar la lógica del dashboard con ubicaciones"""
    
    @staticmethod
    def get_date_ranges():
        """Obtener rangos de fechas comunes"""
        today = timezone.now().date()
        return {
            'today': today,
            'yesterday': today - timedelta(days=1),
            'week_ago': today - timedelta(days=7),
            'month_ago': today - timedelta(days=30),
            'year_ago': today - timedelta(days=365)
        }
    
    @staticmethod
    def get_ubicaciones():
        """Obtener ubicaciones disponibles"""
        return {
            'taller': {'id': 1, 'nombre': 'Taller'},
            'sucursal': {'id': 2, 'nombre': 'Sucursal'}
        }
    
    @staticmethod
    def decimal_to_float(obj):
        """Convertir Decimal a float para serialización JSON"""
        if isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    @staticmethod
    def get_dashboard_metrics():
        """Obtener métricas principales del dashboard separadas por ubicación"""
        dates = DashboardService.get_date_ranges()
        ubicaciones = DashboardService.get_ubicaciones()
        
        # Cache key único por día
        cache_key = f"dashboard_metrics_{dates['today']}"
        cached_metrics = cache.get(cache_key)
        
        if cached_metrics:
            logger.info("Métricas obtenidas desde cache")
            return cached_metrics
        
        try:
            with transaction.atomic():
                # Métricas generales
                total_productos = Producto.objects.filter(estado=True).count()
                total_clientes = Cliente.objects.filter(estadocliente=True).count()
                
                # Métricas por ubicación
                metrics = {
                    'total_productos': total_productos,
                    'total_clientes': total_clientes,
                    'ubicaciones': {}
                }
                
                for key, ubicacion in ubicaciones.items():
                    ubicacion_id = ubicacion['id']
                    
                    # Productos por ubicación
                    productos_ubicacion = Producto.objects.filter(
                        estado=True,
                        idubicacionpro_id=ubicacion_id
                    )
                    
                    productos_bajo_stock = productos_ubicacion.filter(
                        existenciaproducto__lte=F('existenciaminima')
                    ).count()
                    
                    productos_agotados = productos_ubicacion.filter(
                        existenciaproducto=0
                    ).count()
                    
                    # Ventas por ubicación (productos de esa ubicación)
                    ventas_mes = Venta.objects.filter(
                        fechaventa__gte=dates['month_ago'],
                        estado='REALIZADA',
                        detalleventa__idproventa__idubicacionpro_id=ubicacion_id
                    ).distinct().count()
                    
                    ventas_hoy = Venta.objects.filter(
                        fechaventa__date=dates['today'],
                        estado='REALIZADA',
                        detalleventa__idproventa__idubicacionpro_id=ubicacion_id
                    ).distinct().count()
                    
                    # Ingresos por ubicación
                    ingresos_mes = Detalleventa.objects.filter(
                        idventa__fechaventa__gte=dates['month_ago'],
                        idventa__estado='REALIZADA',
                        idproventa__idubicacionpro_id=ubicacion_id
                    ).aggregate(total=Sum('subtotal'))['total'] or Decimal('0.00')
                    
                    # Producciones por ubicación
                    producciones_mes = Productosproduccion.objects.filter(
                        fechaentrada__gte=dates['month_ago'],
                        estadoregistro=True,
                        detalleproduccion__id_producto__idubicacionpro_id=ubicacion_id
                    ).distinct().count()
                    
                    # Devoluciones por ubicación
                    devoluciones_mes = Devolucion.objects.filter(
                        fechadevolucion__gte=dates['month_ago'],
                        detalledevolucion__id_producto__idubicacionpro_id=ubicacion_id
                    ).distinct().count()
                    
                    metrics['ubicaciones'][key] = {
                        'nombre': ubicacion['nombre'],
                        'total_productos': productos_ubicacion.count(),
                        'productos_bajo_stock': productos_bajo_stock,
                        'productos_agotados': productos_agotados,
                        'ventas_mes': ventas_mes,
                        'ventas_hoy': ventas_hoy,
                        'ingresos_mes': DashboardService.decimal_to_float(ingresos_mes),
                        'producciones_mes': producciones_mes,
                        'devoluciones_mes': devoluciones_mes,
                        'promedio_ventas_diarias': ventas_mes // 30 if ventas_mes > 0 else 0,
                        'tasa_devoluciones': (devoluciones_mes / ventas_mes * 100) if ventas_mes > 0 else 0,
                        'porcentaje_productos_bajo_stock': (productos_bajo_stock / productos_ubicacion.count() * 100) if productos_ubicacion.count() > 0 else 0
                    }
                
                # Métricas globales
                metrics.update({
                    'productos_bajo_stock': sum(ub['productos_bajo_stock'] for ub in metrics['ubicaciones'].values()),
                    'productos_agotados': sum(ub['productos_agotados'] for ub in metrics['ubicaciones'].values()),
                    'ventas_mes': sum(ub['ventas_mes'] for ub in metrics['ubicaciones'].values()),
                    'ventas_hoy': sum(ub['ventas_hoy'] for ub in metrics['ubicaciones'].values()),
                    'ingresos_mes': sum(ub['ingresos_mes'] for ub in metrics['ubicaciones'].values()),
                    'producciones_mes': sum(ub['producciones_mes'] for ub in metrics['ubicaciones'].values()),
                    'devoluciones_mes': sum(ub['devoluciones_mes'] for ub in metrics['ubicaciones'].values()),
                })
                
                # Cache por 10 minutos
                cache.set(cache_key, metrics, 600)
                logger.info("Métricas calculadas y guardadas en cache")
                return metrics
                
        except Exception as e:
            logger.error(f"Error calculando métricas del dashboard: {str(e)}")
            # Retornar métricas por defecto en caso de error
            return {
                'total_productos': 0,
                'total_clientes': 0,
                'productos_bajo_stock': 0,
                'productos_agotados': 0,
                'ventas_mes': 0,
                'ventas_hoy': 0,
                'ingresos_mes': 0,
                'producciones_mes': 0,
                'devoluciones_mes': 0,
                'ubicaciones': {
                    'taller': {'nombre': 'Taller', 'total_productos': 0, 'productos_bajo_stock': 0, 'ventas_mes': 0, 'ingresos_mes': 0},
                    'sucursal': {'nombre': 'Sucursal', 'total_productos': 0, 'productos_bajo_stock': 0, 'ventas_mes': 0, 'ingresos_mes': 0}
                }
            }

    @staticmethod
    def get_recent_activities():
        """Obtener actividades recientes por ubicación"""
        dates = DashboardService.get_date_ranges()
        
        # Entradas recientes por ubicación
        entradas_recientes = Productosproduccion.objects.filter(
            fechaentrada__gte=dates['week_ago'],
            estadoregistro=True
        ).select_related('id_usuario').order_by('-fechaentrada')[:10]
        
        # Ventas recientes por ubicación
        ventas_recientes = Venta.objects.filter(
            fechaventa__gte=dates['week_ago'],
            estado='REALIZADA'
        ).select_related(
            'codcliente__idpersonacliente',
            'idusuarioventa'
        ).order_by('-fechaventa')[:10]
        
        return {
            'entradas_recientes': entradas_recientes,
            'ventas_recientes': ventas_recientes
        }
    
    @staticmethod
    def get_chart_data():
        """Obtener datos para gráficos por ubicación"""
        dates = DashboardService.get_date_ranges()
        ubicaciones = DashboardService.get_ubicaciones()
        
        chart_data = {'ubicaciones': {}}
        
        for key, ubicacion in ubicaciones.items():
            ubicacion_id = ubicacion['id']
            
            # Productos más vendidos por ubicación
            productos_vendidos = Detalleventa.objects.filter(
                idventa__fechaventa__gte=dates['month_ago'],
                idventa__estado='REALIZADA',
                idproventa__idubicacionpro_id=ubicacion_id
            ).values(
                'idproventa__nombreproducto',
                'idproventa__idcategoriapro__nombrecategoria'
            ).annotate(
                total_vendido=Sum('cantidadventa'),
                ingresos=Sum('subtotal')
            ).order_by('-total_vendido')[:5]
            
            # Productos con más devoluciones por ubicación
            productos_devueltos = Detalledevolucion.objects.filter(
                id_devolucion__fechadevolucion__gte=dates['month_ago'],
                id_producto__idubicacionpro_id=ubicacion_id
            ).values(
                'id_producto__nombreproducto',
                'id_producto__idcategoriapro__nombrecategoria'
            ).annotate(
                total_devuelto=Sum('cantidaddevuelta')
            ).order_by('-total_devuelto')[:5]
            
            chart_data['ubicaciones'][key] = {
                'nombre': ubicacion['nombre'],
                'productos_mas_vendidos': list(productos_vendidos),
                'productos_mas_devueltos': list(productos_devueltos)
            }
        
        return chart_data

@nexo_login_required
def dashboard_view(request):
    """Vista principal del dashboard mejorada con ubicaciones"""
    usuario_actual = getattr(request, 'nexo_user', None)
    if not usuario_actual:
        messages.error(request, 'Debes iniciar sesión para acceder al dashboard')
        return redirect('auth:login')
    user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
    try:
        logger.info(f"Usuario {usuario_actual.nombreusuario} accedió al dashboard")
        
        # Obtener datos del dashboard usando el servicio
        metrics = DashboardService.get_dashboard_metrics()
        activities = DashboardService.get_recent_activities()
        chart_data = DashboardService.get_chart_data()
        
        # Preparar datos para los gráficos por ubicación
        chart_data_json = {}
        for ubicacion_key, ubicacion_data in chart_data['ubicaciones'].items():
            productos_vendidos_chart = [
                {
                    'nombre': item['idproventa__nombreproducto'] or 'Sin nombre',
                    'cantidad': item['total_vendido'] or 0,
                    'categoria': item['idproventa__idcategoriapro__nombrecategoria'] or 'Sin categoría',
                    'ingresos': DashboardService.decimal_to_float(item['ingresos'] or 0)
                }
                for item in ubicacion_data['productos_mas_vendidos']
            ]
            
            productos_devueltos_chart = [
                {
                    'nombre': item['id_producto__nombreproducto'] or 'Sin nombre',
                    'cantidad': item['total_devuelto'] or 0,
                    'categoria': item['id_producto__idcategoriapro__nombrecategoria'] or 'Sin categoría'
                }
                for item in ubicacion_data['productos_mas_devueltos']
            ]
            
            chart_data_json[ubicacion_key] = {
                'productos_mas_vendidos': productos_vendidos_chart,
                'productos_mas_devueltos': productos_devueltos_chart
            }
        
        # Obtener usuario autenticado de forma segura
        usuario_actual = getattr(request, 'nexo_user', None)
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        
        context = {
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'page_title': 'Dashboard - NEXO',
            'system_name': 'Sistema de Inventario y ventas NEXO - Sunshine Handmade',
            
            # Métricas principales
            **metrics,
            
            # Actividades recientes
            **activities,
            
            # Datos para gráficos por ubicación (JSON para JavaScript)
            'chart_data_by_location': json.dumps(chart_data_json),
            
            # Información adicional
            'current_date': timezone.now().date(),
            'current_time': timezone.now().time(),
            'current_datetime': timezone.now(),
            'nexo_user_role': usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario',
            'employee_name': usuario_actual.empleado_nombre if hasattr(usuario_actual, 'empleado_nombre') and usuario_actual.empleado_nombre else (usuario_actual.nombreusuario if usuario_actual else 'Invitado'),
            'user_full_name': usuario_actual.empleado_nombre if hasattr(usuario_actual, 'empleado_nombre') and usuario_actual.empleado_nombre else (usuario_actual.nombreusuario if usuario_actual else 'Invitado'),
            
            # Configuración para JavaScript
            'dashboard_config': json.dumps({
                'refresh_interval': 30000,
                'chart_animation_duration': 1000,
                'notification_duration': 5000,
                'user_id': usuario_actual.idusuario if usuario_actual else '',
                'user_role': usuario_actual.rol if usuario_actual else '',
                'ubicaciones': DashboardService.get_ubicaciones()
            })
        }
        
        return render(request, 'dashboard/dashboard.html', context)
        
    except Exception as e:
        logger.error(f'Error al cargar el dashboard para usuario {getattr(usuario_actual, 'nombreusuario', 'Invitado')}: {str(e)}')
        messages.error(request, f'Error al cargar el dashboard: {str(e)}')
        return render(request, 'dashboard/dashboard.html', {
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'error': True,
            'error_message': str(e),
            'page_title': 'Dashboard - Error',
            'system_name': 'Sistema de Inventario y ventas NEXO',
            'nexo_user_role': usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario',
        })

@require_http_methods(["POST"])
@csrf_exempt
def logout_view(request):
    """Vista para cerrar sesión"""
    try:
        # Limpiar la sesión
        if 'user_id' in request.session:
            user_id = request.session['user_id']
            logger.info(f"Usuario {user_id} cerró sesión")
            request.session.flush()
        
        return JsonResponse({
            'success': True,
            'message': 'Sesión cerrada exitosamente',
            'redirect_url': '/login/'
        })
    except Exception as e:
        logger.error(f'Error al cerrar sesión: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': f'Error al cerrar sesión: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_dashboard_stats_ajax(request):
    """Endpoint AJAX mejorado para obtener estadísticas por ubicación"""
    user = check_session(request)
    if not user:
        return JsonResponse({'error': 'Sesión no válida'}, status=401)
    
    try:
        # Obtener métricas actualizadas
        metrics = DashboardService.get_dashboard_metrics()
        chart_data = DashboardService.get_chart_data()
        
        # Preparar datos para gráficos por ubicación
        chart_data_formatted = {}
        for ubicacion_key, ubicacion_data in chart_data['ubicaciones'].items():
            productos_vendidos = [
                {
                    'nombre': item['idproventa__nombreproducto'] or 'Sin nombre',
                    'cantidad': item['total_vendido'] or 0,
                    'ingresos': DashboardService.decimal_to_float(item['ingresos'] or 0),
                    'categoria': item['idproventa__idcategoriapro__nombrecategoria'] or 'Sin categoría'
                }
                for item in ubicacion_data['productos_mas_vendidos']
            ]
            
            productos_devueltos = [
                {
                    'nombre': item['id_producto__nombreproducto'] or 'Sin nombre',
                    'cantidad': item['total_devuelto'] or 0,
                    'categoria': item['id_producto__idcategoriapro__nombrecategoria'] or 'Sin categoría'
                }
                for item in ubicacion_data['productos_mas_devueltos']
            ]
            
            chart_data_formatted[ubicacion_key] = {
                'nombre': ubicacion_data['nombre'],
                'productos_mas_vendidos': productos_vendidos,
                'productos_mas_devueltos': productos_devueltos
            }
        
        return JsonResponse({
            'success': True,
            'data': {
                'metrics': metrics,
                'chart_data_by_location': chart_data_formatted,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'Error al obtener estadísticas AJAX: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener estadísticas: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=500)

@require_http_methods(["GET"])
def get_recent_data_ajax(request):
    """Endpoint AJAX para obtener datos recientes con ubicación"""
    user = check_session(request)
    if not user:
        return JsonResponse({'error': 'Sesión no válida'}, status=401)
    
    try:
        activities = DashboardService.get_recent_activities()
        
        # Formatear entradas recientes
        entradas_data = []
        for entrada in activities['entradas_recientes']:
            entradas_data.append({
                'id': entrada.idproduccion,
                'fecha': entrada.fechaentrada.strftime('%d/%m/%Y'),
                'descripcion': f"Producción #{entrada.idproduccion}",
                'detalle': entrada.observacion or 'Sin observaciones',
                'usuario': entrada.id_usuario.nombreusuario if entrada.id_usuario else 'Sistema'
            })
        
        # Formatear ventas recientes
        ventas_data = []
        for venta in activities['ventas_recientes']:
            ventas_data.append({
                'id': venta.id_venta,
                'fecha': venta.fechaventa.strftime('%d/%m/%Y') if venta.fechaventa else 'N/A',
                'hora': venta.fechaventa.strftime('%H:%M') if venta.fechaventa else 'N/A',
                'cliente': str(venta.codcliente) if venta.codcliente else 'Cliente general',
                'total': DashboardService.decimal_to_float(venta.total) if venta.total else 0.0,
                'usuario': venta.idusuarioventa.nombreusuario if venta.idusuarioventa else 'Sistema'
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'entradas_recientes': entradas_data,
                'ventas_recientes': ventas_data,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'Error al obtener datos recientes AJAX: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': f'Error al obtener datos recientes: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def refresh_dashboard_data(request):
    """Endpoint para refrescar todos los datos del dashboard"""
    user = check_session(request)
    if not user:
        return JsonResponse({'error': 'Sesión no válida'}, status=401)
    
    try:
        # Limpiar cache relacionado con el dashboard
        cache_keys = [
            f"dashboard_metrics_{timezone.now().date()}",
            'dashboard_chart_data',
            'dashboard_activities'
        ]
        cache.delete_many(cache_keys)
        
        # Obtener datos frescos
        metrics = DashboardService.get_dashboard_metrics()
        
        return JsonResponse({
            'success': True,
            'message': 'Dashboard actualizado correctamente',
            'data': {
                'metrics': metrics,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'Error al refrescar dashboard AJAX: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': f'Error al refrescar dashboard: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=500)
