from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decimal import Decimal
import logging
import json
from datetime import date, datetime

# Importar modelos
from core_data.models import Productosproduccion, Producto, Usuario, Empleado

# Importar manager y formularios
from .models import ProduccionManager
from .forms import ProduccionForm, DetalleProduccionFormSet, ProduccionSearchForm

# Importar decoradores (ajustar según tu implementación)
try:
    from AuthLogin.decorators import nexo_login_required, nexo_role_required
except ImportError:
    # Fallback si no existen los decoradores
    def nexo_login_required(view_func):
        return view_func
    
    def nexo_role_required(roles):
        def decorator(view_func):
            return view_func
        return decorator

logger = logging.getLogger('nexo.produccion')

def clear_messages(request):
    list(messages.get_messages(request))


# Configuración de colores NEXO
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
    'warning': '#F2CE16',
    'danger': '#F28627',
    'info': '#2752F2'
}

@nexo_login_required
def produccion_list(request):
    """
    Vista corregida para listar producciones con filtros mejorados
    """
    # Inicializar formulario de búsqueda
    search_form = ProduccionSearchForm(request.GET or None)
    
    # Preparar filtros (SIN filtro de estado)
    filtros = {}
    if search_form.is_valid():
        if search_form.cleaned_data.get('fecha_desde'):
            filtros['fecha_desde'] = search_form.cleaned_data['fecha_desde']
        if search_form.cleaned_data.get('fecha_hasta'):
            filtros['fecha_hasta'] = search_form.cleaned_data['fecha_hasta']
        if search_form.cleaned_data.get('usuario'):
            filtros['usuario'] = search_form.cleaned_data['usuario'].nombreusuario
    
    # Obtener número de página
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    try:
        # Obtener producciones con filtros
        resultado = ProduccionManager.obtener_producciones_con_filtros(
            filtros=filtros,
            page=page,
            per_page=10
        )
        
        # Crear objeto similar a Paginator para compatibilidad con template
        class MockPage:
            def __init__(self, data):
                self.object_list = data['results']
                self.number = data['page']
                self.paginator = type('MockPaginator', (), {
                    'count': data['total_count'],
                    'num_pages': data['total_pages'],
                    'page_range': range(1, max(1, data['total_pages']) + 1)
                })()
                self.has_previous = lambda: data['has_previous']
                self.has_next = lambda: data['has_next']
                self.previous_page_number = lambda: data['previous_page_number']
                self.next_page_number = lambda: data['next_page_number']
                self.has_other_pages = lambda: data['total_pages'] > 1
                self.start_index = lambda: (data['page'] - 1) * data['per_page'] + 1 if data['total_count'] > 0 else 0
                self.end_index = lambda: min(data['page'] * data['per_page'], data['total_count'])
        
        page_obj = MockPage(resultado)
        
    except Exception as e:
        logger.error(f"Error al cargar producciones: {str(e)}")
        clear_messages(request)
        messages.error(request, f"Error al cargar las producciones: {str(e)}")
        page_obj = MockPage({
            'results': [], 'total_count': 0, 'page': 1, 'total_pages': 1,
            'has_previous': False, 'has_next': False, 
            'previous_page_number': None, 'next_page_number': None, 'per_page': 10
        })
    
    context = {
        'page_obj': page_obj,
        'filtro_form': search_form,
        'total_count': page_obj.paginator.count,
        'page_title': 'Gestión de Producción',
        'page_subtitle': 'Administra los registros de producción del taller.',
        'user': getattr(request, 'nexo_user', None),
        'colores': COLORES_NEXO,
    }
    
    return render(request, 'produccion/list.html', context)

@nexo_role_required(['admin'])
def produccion_create(request):
    """
    Vista corregida para crear nueva producción
    """
    if request.method == 'POST':
        form = ProduccionForm(request.POST)
        detalle_formset = DetalleProduccionFormSet(request.POST, prefix='detalles')

        if form.is_valid() and detalle_formset.is_valid():
            try:
                usuario_seleccionado = form.cleaned_data['id_usuario']
                detalles_data = []
                
                for detalle_form_cleaned in detalle_formset.cleaned_data:
                    if detalle_form_cleaned and not detalle_form_cleaned.get('DELETE', False):
                        detalles_data.append({
                            'id_producto': detalle_form_cleaned['id_producto'].id_producto,
                            'cantidad': detalle_form_cleaned['cantidad'],
                            'costo_unitario': float(detalle_form_cleaned['costo_unitario']),
                            'idFabricante': detalle_form_cleaned['idFabricante'].idempleado
                        })
                
                if not detalles_data:
                    clear_messages(request)
                    messages.error(request, 'Debe agregar al menos un producto válido a la producción.')
                else:
                    success, message_pm, id_produccion = ProduccionManager.registrar_produccion(
                        fechaEntrada=form.cleaned_data['fechaEntrada'],
                        observacion=form.cleaned_data['observacion'],
                        id_usuario=usuario_seleccionado.idusuario,
                        detalles=detalles_data
                    )
                    if success:
                        nexo_user = getattr(request, 'nexo_user', None)
                        if isinstance(nexo_user, dict):
                            user_name = nexo_user.get('nombreusuario', 'Usuario')
                        elif hasattr(nexo_user, 'nombreusuario'):
                            user_name = nexo_user.nombreusuario
                        else:
                            user_name = 'Usuario'
                        clear_messages(request)
                        messages.success(request, f'{message_pm} (Registrado por: {user_name})')
                        return redirect('crud:produccion_detail', pk=id_produccion)
                    else:
                        clear_messages(request)
                        messages.error(request, f'Error al registrar: {message_pm}')
            except Exception as e:
                logger.error(f"Error inesperado en produccion_create: {str(e)}")
                clear_messages(request)
                messages.error(request, f'Error inesperado: {str(e)}')
        else:
            # Solo un mensaje general de error
            clear_messages(request)
            messages.error(request, 'Formulario inválido. Por favor, corrija los errores en los campos resaltados.')
    else:
        # Inicializar formularios para GET
        initial_data = {
            'fechaEntrada': timezone.now().date()
        }
        form = ProduccionForm(initial=initial_data)
        detalle_formset = DetalleProduccionFormSet(prefix='detalles')

    context = {
        'form': form,
        'detalle_formset': detalle_formset,
        'page_title': 'Registrar Producción',
        'page_subtitle': 'Crear nuevo registro de producción en el taller.',
        'user': getattr(request, 'nexo_user', None),
        'colores': COLORES_NEXO,
        'is_create': True
    }
    return render(request, 'produccion/create.html', context)

@nexo_login_required
@nexo_role_required(['admin'])
def produccion_detail(request, pk):
    """
    Vista para mostrar detalle de una producción con validaciones mejoradas
    """
    try:
        # Obtener producción
        produccion = get_object_or_404(Productosproduccion, idproduccion=pk)
        
        # Obtener detalles
        detalles = ProduccionManager.obtener_detalle_produccion(pk)
        
        # Calcular totales
        total_cantidad_items = sum(d.get('cantidad', 0) for d in detalles)
        total_costo_produccion = sum(
            Decimal(str(d.get('subtotal', '0.00'))) for d in detalles
        )
        
        # USAR EL MANAGER PARA OBTENER EL ESTADO REAL
        estado_real, _ = ProduccionManager.verificar_estado_produccion(pk)

        context = {
            'produccion': produccion,
            'detalles': detalles,
            'total_cantidad_items': total_cantidad_items,
            'total_costo_produccion': total_costo_produccion,
            'page_title': f'Detalle Producción #{pk}',
            'page_subtitle': f'Información completa del registro de producción del {produccion.fechaentrada.strftime("%d de %B de %Y")}.',
            'user': getattr(request, 'nexo_user', None),
            'colores': COLORES_NEXO,
            'estado_real': estado_real,  
        }
        
        return render(request, 'produccion/detail.html', context)
        
    except Exception as e:
        logger.error(f"Error al cargar detalle de producción {pk}: {str(e)}")
        clear_messages(request)
        messages.error(request, f'Error al cargar el detalle: {str(e)}')
        return redirect('crud:produccion_list')

@nexo_role_required(['admin'])
def produccion_edit(request, pk):
    """
    Vista corregida para editar una producción existente
    """
    try:
        produccion = get_object_or_404(Productosproduccion, idproduccion=pk)
        estado, mensaje = ProduccionManager.verificar_estado_produccion(pk)
        if estado is None:
            clear_messages(request)
            messages.error(request, mensaje)
            return redirect('crud:produccion_list')
        if not estado:
            clear_messages(request)
            messages.warning(request, 'No se puede editar una producción inactiva.')
            return redirect('crud:produccion_detail', pk=pk)
    except Productosproduccion.DoesNotExist:
        clear_messages(request)
        messages.error(request, 'La producción que intenta editar no existe.')
        return redirect('crud:produccion_list')
    except Exception as e:
        logger.error(f"Error al verificar producción {pk}: {str(e)}")
        clear_messages(request)
        messages.error(request, f'Error al verificar la producción: {str(e)}')
        return redirect('crud:produccion_list')
    
    if request.method == 'POST':
        form = ProduccionForm(request.POST)
        detalle_formset = DetalleProduccionFormSet(request.POST, prefix='detalles')
        if form.is_valid() and detalle_formset.is_valid():
            try:
                detalles_data = []
                for detalle_form in detalle_formset:
                    if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE', False):
                        detalles_data.append({
                            'id_producto': detalle_form.cleaned_data['id_producto'].id_producto,
                            'cantidad': detalle_form.cleaned_data['cantidad'],
                            'costo_unitario': float(detalle_form.cleaned_data['costo_unitario']),
                            'idFabricante': detalle_form.cleaned_data['idFabricante'].idempleado
                        })
                # VALIDACIÓN DE DUPLICADOS
                productos_ids = [d['id_producto'] for d in detalles_data]
                if len(productos_ids) != len(set(productos_ids)):
                    clear_messages(request)
                    messages.error(request, 'No se puede agregar productos duplicados.')
                    # Renderiza el formulario con los datos actuales y detiene el flujo
                    context = {
                        'form': form,
                        'detalle_formset': detalle_formset,
                        'produccion': produccion,
                        'page_title': f'Editar Producción #{pk}',
                        'page_subtitle': f'Modifica los datos de la producción registrada el {produccion.fechaentrada.strftime("%d/%m/%Y")}.',
                        'user': getattr(request, 'nexo_user', None),
                        'colores': COLORES_NEXO,
                        'is_edit': True
                    }
                    return render(request, 'produccion/edit.html', context)
                if not detalles_data:
                    clear_messages(request)
                    messages.error(request, 'Debe agregar al menos un producto válido.')
                else:
                    success, message = ProduccionManager.editar_produccion(
                        id_produccion=pk,
                        fechaentrada=form.cleaned_data['fechaEntrada'],
                        observacion=form.cleaned_data['observacion'],
                        id_usuario=form.cleaned_data['id_usuario'].idusuario,
                        detalles=detalles_data
                    )
                    if success:
                        nexo_user = getattr(request, 'nexo_user', None)
                        if isinstance(nexo_user, dict):
                            user_name = nexo_user.get('nombreusuario', 'Usuario')
                        elif hasattr(nexo_user, 'nombreusuario'):
                            user_name = nexo_user.nombreusuario
                        else:
                            user_name = 'Usuario'
                            clear_messages(request)
                        messages.success(request, f'{message} (Editado por: {user_name})')
                        return redirect('crud:produccion_detail', pk=pk)
                    else:
                        clear_messages(request)
                        messages.error(request, message)
            except Exception as e:
                logger.error(f"Error inesperado en produccion_edit (ID: {pk}): {str(e)}")
                messages.error(request, f'Error inesperado al editar: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        # Cargar datos existentes
        fecha_entrada = produccion.fechaentrada
        # Normalizar fecha_entrada a date puro (yyyy-MM-dd para input type="date")
        if isinstance(fecha_entrada, str):
            # Intentar varios formatos
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
                try:
                    fecha_entrada = datetime.strptime(fecha_entrada, fmt).date()
                    break
                except Exception:
                    continue
            else:
                fecha_entrada = timezone.now().date()
        elif isinstance(fecha_entrada, datetime):
            fecha_entrada = fecha_entrada.date()
        # Si es date, no se hace nada
        form = ProduccionForm(initial={
            'fechaEntrada': fecha_entrada,
            'observacion': produccion.observacion,
            'id_usuario': produccion.id_usuario
        })
        detalles_actuales = ProduccionManager.obtener_detalle_produccion(pk)
        initial_detalles = []
        for detalle in detalles_actuales:
            try:
                producto = Producto.objects.filter(
                    id_producto=detalle['id_producto'],
                    estado=True
                ).first()
                empleado = Empleado.objects.get(
                    idempleado=detalle['idFabricante'],
                    estadoempleado=True
                )
                initial_detalles.append({
                    'id_producto': producto,
                    'cantidad': detalle['cantidad'],
                    'costo_unitario': Decimal(str(detalle['costo_unitario'])),
                    'idFabricante': empleado
                })
            except (Producto.DoesNotExist, Empleado.DoesNotExist) as e:
                logger.warning(f"Item omitido en formset edit {pk}: {str(e)}")
                # Solo un mensaje de advertencia por omisión
                if not any('no pudieron cargarse' in m.message for m in messages.get_messages(request)):
                    messages.warning(request, "Algunos detalles no pudieron cargarse porque los productos o empleados están inactivos.")
        detalle_formset = DetalleProduccionFormSet(prefix='detalles', initial=initial_detalles)
    
    context = {
        'form': form,
        'detalle_formset': detalle_formset,
        'produccion': produccion,
        'page_title': f'Editar Producción #{pk}',
        'page_subtitle': f'Modifica los datos de la producción registrada el {produccion.fechaentrada.strftime("%d/%m/%Y")}.',
        'user': getattr(request, 'nexo_user', None),
        'colores': COLORES_NEXO,
        'is_edit': True
    }
    
    return render(request, 'produccion/edit.html', context)

@nexo_role_required(['admin'])
@require_http_methods(["POST"])
def produccion_delete(request, pk):
    """
    Vista corregida para dar de baja una producción (soft delete)
    """
    try:
        # Verificar estado antes de intentar dar de baja
        estado, mensaje = ProduccionManager.verificar_estado_produccion(pk)
        
        if estado is None:
            messages.error(request, mensaje)
        elif not estado:
            messages.warning(request, 'La producción ya está inactiva.')
        else:
            # Proceder con la baja
            success, message = ProduccionManager.dar_de_baja_produccion(pk)
            
            if success:
                nexo_user = getattr(request, 'nexo_user', None)
                if isinstance(nexo_user, dict):
                    user_name = nexo_user.get('nombreusuario', 'Usuario')
                elif hasattr(nexo_user, 'nombreusuario'):
                    user_name = nexo_user.nombreusuario
                else:
                    user_name = 'Usuario'
                messages.success(request, f'{message} (Acción realizada por: {user_name})')
            else:
                messages.error(request, f'Error al dar de baja: {message}')
            
    except Exception as e:
        logger.error(f"Error inesperado en produccion_delete (ID: {pk}): {str(e)}")
        messages.error(request, f'Error inesperado al dar de baja: {str(e)}')
    
    return redirect('crud:produccion_list')

@nexo_login_required
@nexo_role_required(['admin'])
def produccion_dashboard(request):
    """
    Vista del dashboard de producción con estadísticas
    """
    try:
        # Obtener estadísticas
        dashboard_data = ProduccionManager.obtener_estadisticas_dashboard()
        
        context = {
            'stats': dashboard_data['stats'],
            'productos_top': dashboard_data['productos_top'],
            'empleados_top': dashboard_data['empleados_top'],
            'page_title': 'Dashboard de Producción',
            'page_subtitle': 'Estadísticas y métricas clave del área de producción.',
            'user': getattr(request, 'nexo_user', None),
            'colores': COLORES_NEXO
        }
        
    except Exception as e:
        logger.error(f"Error al cargar dashboard de producción: {str(e)}")
        messages.warning(request, f"Error al cargar estadísticas del dashboard: {str(e)}")
        
        context = {
            'stats': {'total_producciones': 0, 'producciones_hoy': 0, 'producciones_semana': 0, 'producciones_mes': 0},
            'productos_top': [],
            'empleados_top': [],
            'page_title': 'Dashboard de Producción',
            'page_subtitle': 'Estadísticas y métricas clave del área de producción.',
            'user': getattr(request, 'nexo_user', None),
            'colores': COLORES_NEXO
        }
    
    return render(request, 'produccion/dashboard.html', context)

# APIs para AJAX corregidas
@nexo_login_required
def api_producto_info(request, producto_id):
    """
    API corregida para obtener información de un producto (solo activos)
    CORREGIDO: Validación de ubicación más flexible
    """
    try:
        # CORREGIDO: Buscar producto activo sin restricción de ubicación inicialmente
        producto = get_object_or_404(Producto, id_producto=producto_id, estado=True)
        
        # Verificar ubicación de forma más flexible
        es_produccion = True
        if hasattr(producto, 'idubicacionpro') and producto.idubicacionpro:
            # Si tiene ubicación, verificar si es de producción
            es_produccion = producto.idubicacionpro == 1
        
        data = {
            'id_producto': producto.id_producto,
            'nombreproducto': producto.nombreproducto,
            'precioproducto': float(producto.precioproducto) if producto.precioproducto else 0.0,
            'existenciaproducto': producto.existenciaproducto or 0,
            'existenciaminima': producto.existenciaminima or 0,
            'bajo_stock': (producto.existenciaproducto or 0) <= (producto.existenciaminima or 0),
            'activo': producto.estado,
            'es_produccion': es_produccion,
            'ubicacion_id': producto.idubicacionpro if hasattr(producto, 'idubicacionpro') else None
        }
        
        return JsonResponse(data)
        
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado o inactivo.'}, status=404)
    except Exception as e:
        logger.error(f"Error en api_producto_info: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor.'}, status=500)

@nexo_login_required
def api_empleado_info(request, empleado_id):
    """
    API para obtener información de un empleado (solo activos)
    """
    try:
        empleado = get_object_or_404(Empleado, idempleado=empleado_id, estadoempleado=True)
        
        # Obtener nombre completo
        nombre_completo = "Empleado"
        if hasattr(empleado, 'idpersonaemp') and empleado.idpersonaemp:
            nombre_completo = f"{empleado.idpersonaemp.primernombre or ''} {empleado.idpersonaemp.primerapellido or ''}".strip()
        
        data = {
            'idempleado': empleado.idempleado,
            'nombre_completo': nombre_completo,
            'rolempleado': getattr(empleado, 'rolempleado', 'N/A'),
            'activo': empleado.estadoempleado
        }
        
        return JsonResponse(data)
        
    except Empleado.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado o inactivo.'}, status=404)
    except Exception as e:
        logger.error(f"Error en api_empleado_info: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor.'}, status=500)

@nexo_login_required
def api_check_session(request):
    """
    API para verificar el estado de la sesión
    """
    try:
        user_data = getattr(request, 'nexo_user', {})
        
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': user_data.get('idusuario'),
                'username': user_data.get('nombreusuario'),
                'role': user_data.get('rol'),
                'employee_name': user_data.get('empleado_nombre')
            },
            'session_info': {
                'login_time': request.session.get('login_time'),
                'expires_at': request.session.get_expiry_date().isoformat() if request.session.get_expiry_date() else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error en api_check_session: {str(e)}")
        return JsonResponse({'error': 'Error al verificar sesión.'}, status=500)