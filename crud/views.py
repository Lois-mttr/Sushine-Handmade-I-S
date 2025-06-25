from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse # No se usa directamente aquí, pero es útil
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import logging 
from django.db import connection # Para el dashboard

# Importar modelos de core_data
from core_data.models import Productosproduccion, Producto, Usuario, Empleado # Asegúrate que estos modelos existen
# Importar el manager de crud.models
from crud.models import ProduccionManager # Ajusta la ruta si crud.models está en otro lugar
# Importar formularios locales
from .forms import ProduccionForm, DetalleProduccionFormSet, ProduccionSearchForm
# Importar decoradores de AuthLogin (ajustar ruta si es necesario)
from .decorators import nexo_login_required, nexo_role_required, ajax_login_required

logger = logging.getLogger(__name__)

colores_nexo = {
    'primary': '#39bfb2', 'secondary_yellow': '#F2CE16', 'accent_orange': '#F29D35',
    'accent_dark_orange': '#F28627', 'bg_light': '#eaeef3', 'bg_very_light': '#F2F2F2',
    'white': '#ffffff', 'text_dark': '#374151', 'text_medium': '#6b7280',
    'text_light': '#9ca3af', 'success': '#39bfb2', 'warning': '#F2CE16',
    'danger': '#F28627', 'info': '#2752F2'
}

@nexo_login_required
def produccion_list(request):
    search_form = ProduccionSearchForm(request.GET or None)
    producciones_list_raw = []

    try:
        producciones_list_raw = ProduccionManager.obtener_producciones_activas_simple()
    except Exception as e:
        logger.error(f"Error al cargar producciones en produccion_list: {str(e)}")

        messages.error(request, f"No se pudieron cargar los registros de producción: {str(e)}")

    if search_form.is_valid():
        fecha_desde = search_form.cleaned_data.get('fecha_desde')
        fecha_hasta = search_form.cleaned_data.get('fecha_hasta')
        usuario_obj = search_form.cleaned_data.get('usuario')
        estado_str = search_form.cleaned_data.get('estado')

        if fecha_desde:
            producciones_list_raw = [p for p in producciones_list_raw if p.get('fechaEntrada') and p['fechaEntrada'] >= fecha_desde]
        if fecha_hasta:
            producciones_list_raw = [p for p in producciones_list_raw if p.get('fechaEntrada') and p['fechaEntrada'] <= fecha_hasta]
        if usuario_obj:
            producciones_list_raw = [p for p in producciones_list_raw if p.get('nombreUsuario') == usuario_obj.nombreusuario]
        if estado_str:
            estado_bool = True if estado_str == '1' else False
            producciones_list_raw = [p for p in producciones_list_raw if p.get('EstadoRegistro') == estado_bool]
            
    paginator = Paginator(producciones_list_raw, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filtro_form': search_form,
        'total_count': paginator.count,
        'page_title': 'Gestión de Producción',
        'page_subtitle': 'Administra los registros de producción del taller.',
        'user': request.nexo_user,
        'colores': colores_nexo,
        'producciones': page_obj.object_list # Para la plantilla que itera sobre 'producciones'
    }
    return render(request, 'produccion/list.html', context)


@nexo_role_required(['admin', 'supervisor', 'empleado'])
def produccion_create(request):
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
                    messages.error(request, 'Debe agregar al menos un producto válido a la producción.')
                else:
                    success, message_pm = ProduccionManager.registrar_produccion(
                        fechaEntrada=form.cleaned_data['fechaEntrada'],
                        observacion=form.cleaned_data['observacion'],
                        id_usuario=usuario_seleccionado.idusuario,
                        detalles=detalles_data
                    )
                    if success:
                        messages.success(request, f'{message_pm} (Registrado por: {request.nexo_user.nombreusuario})')
                        return redirect('crud:produccion_list')
                    else:
                        messages.error(request, f'Error al registrar: {message_pm}')
            except Exception as e:
                logger.error(f"Error inesperado en produccion_create: {str(e)}")
                messages.error(request, f'Error inesperado: {str(e)}')
        else:
            messages.error(request, 'Formulario inválido. Por favor, corrija los errores.')
            if not form.is_valid(): logger.warning(f"Errores en ProduccionForm: {form.errors.as_json()}")
            if not detalle_formset.is_valid(): logger.warning(f"Errores en DetalleProduccionFormSet: {detalle_formset.errors}")
    else:
        form = ProduccionForm(initial={
            'id_usuario': request.nexo_user, 
            'fechaEntrada': timezone.now().date()
        })
        detalle_formset = DetalleProduccionFormSet(prefix='detalles')

    context = {
        'form': form,
        'detalle_formset': detalle_formset,
        'page_title': 'Registrar Producción',
        'page_subtitle': 'Crear nuevo registro de producción en el taller.',
        'user': request.nexo_user,
        'colores': colores_nexo
    }
    return render(request, 'produccion/create.html', context)


@nexo_login_required
def produccion_detail(request, pk):
    try:
        produccion_cabecera = get_object_or_404(Productosproduccion, idproduccion=pk)
        detalles_produccion = ProduccionManager.obtener_detalle_produccion(pk)
        
        total_cantidad_items = sum(d.get('cantidad', 0) for d in detalles_produccion) if detalles_produccion else 0
        total_costo_produccion = sum(Decimal(str(d.get('subtotal', '0.00'))) for d in detalles_produccion) if detalles_produccion else Decimal('0.00')

        context = {
            'produccion': produccion_cabecera,
            'detalles': detalles_produccion,
            'total_cantidad_items': total_cantidad_items,
            'total_costo_produccion': total_costo_produccion,
            'page_title': f'Detalle Producción #{pk}',
            'page_subtitle': f'Producción registrada el {produccion_cabecera.fechaentrada.strftime("%d/%m/%Y")}',
            'user': request.nexo_user,
            'colores': colores_nexo
        }
        return render(request, 'produccion/detail.html', context)
    except Exception as e:
        logger.error(f"Error al cargar detalle de producción {pk}: {str(e)}")
        messages.error(request, f'Error al cargar el detalle: {str(e)}')
        return redirect('crud:produccion_list')


@nexo_role_required(['admin', 'supervisor'])
def produccion_edit(request, pk):
    try:
        produccion_obj = get_object_or_404(Productosproduccion, idproduccion=pk)
        if not produccion_obj.estadoregistro:
             messages.warning(request, 'No se puede editar una producción inactiva.')
             return redirect('crud:produccion_detail', pk=pk)
    except Productosproduccion.DoesNotExist:
        messages.error(request, 'La producción que intenta editar no existe.')
        return redirect('crud:produccion_list')

    if request.method == 'POST':
        form = ProduccionForm(request.POST)
        detalle_formset = DetalleProduccionFormSet(request.POST, prefix='detalles')

        if form.is_valid() and detalle_formset.is_valid():
            try:
                usuario_seleccionado = form.cleaned_data['id_usuario']
                detalles_data = []
                for df_cleaned in detalle_formset.cleaned_data:
                    if df_cleaned and not df_cleaned.get('DELETE', False):
                        detalles_data.append({
                            'id_producto': df_cleaned['id_producto'].id_producto,
                            'cantidad': df_cleaned['cantidad'],
                            'costo_unitario': float(df_cleaned['costo_unitario']),
                            'idFabricante': df_cleaned['idFabricante'].idempleado
                        })
                if not detalles_data:
                    messages.error(request, 'Debe agregar al menos un producto válido.')
                else:
                    success, msg_pm = ProduccionManager.editar_produccion(
                        pk, form.cleaned_data['fechaEntrada'], form.cleaned_data['observacion'],
                        usuario_seleccionado.idusuario, detalles_data
                    )
                    if success:
                        messages.success(request, f'{msg_pm} (Editado por: {request.nexo_user.nombreusuario})')
                        return redirect('crud:produccion_detail', pk=pk)
                    else:
                        messages.error(request, f'Error al editar: {msg_pm}')
            except Exception as e:
                logger.error(f"Error inesperado en produccion_edit (ID: {pk}): {str(e)}")
                messages.error(request, f'Error inesperado al editar: {str(e)}')
        else:
            messages.error(request, 'Formulario inválido.')
            if not form.is_valid(): logger.warning(f"Errores Form: {form.errors.as_json()}")
            if not detalle_formset.is_valid(): logger.warning(f"Errores FormSet: {detalle_formset.errors}")
    else:
        form = ProduccionForm(initial={
            'fechaEntrada': produccion_obj.fechaentrada,
            'observacion': produccion_obj.observacion,
            'id_usuario': produccion_obj.id_usuario
        })
        det_actuales = ProduccionManager.obtener_detalle_produccion(pk)
        initial_detalles = []
        if det_actuales:
            for det in det_actuales:
                try:
                    prod_inst = Producto.objects.get(id_producto=det['id_producto'])
                    fab_inst = Empleado.objects.get(idempleado=det['idFabricante'])
                    initial_detalles.append({
                        'id_producto': prod_inst, 'cantidad': det['cantidad'],
                        'costo_unitario': Decimal(str(det['costo_unitario'])),
                        'idFabricante': fab_inst
                    })
                except (Producto.DoesNotExist, Empleado.DoesNotExist) as item_err:
                     logger.warning(f"Item omitido en formset edit {pk}: {str(item_err)}")
                     messages.warning(request, f"Item detalle no cargado: {str(item_err)}")
        detalle_formset = DetalleProduccionFormSet(prefix='detalles', initial=initial_detalles)

    context = {
        'form': form, 'detalle_formset': detalle_formset, 'produccion': produccion_obj,
        'page_title': f'Editar Producción #{pk}',
        'page_subtitle': f'Modificar prod. del {produccion_obj.fechaentrada.strftime("%d/%m/%Y")}',
        'user': request.nexo_user, 'colores': colores_nexo, 'is_edit_mode': True
    }
    return render(request, 'produccion/edit.html', context)


@nexo_role_required(['admin', 'supervisor'])
def produccion_delete(request, pk):
    if request.method == 'POST':
        try:
            success, message_pm = ProduccionManager.dar_de_baja_produccion(pk)
            if success:
                messages.success(request, f'{message_pm} (Acción por: {request.nexo_user.nombreusuario})')
            else:
                messages.error(request, f'Error al dar de baja: {message_pm}')
        except Exception as e:
            logger.error(f"Error inesperado en produccion_delete (ID: {pk}): {str(e)}")
            messages.error(request, f'Error inesperado al dar de baja: {str(e)}')
    else:
        messages.error(request, "Acción no permitida por este método.")
    return redirect('crud:produccion_list')

@ajax_login_required
def api_producto_info(request, producto_id):
    try:
        producto = Producto.objects.get(id_producto=producto_id, estado=True)
        data = {
            'id_producto': producto.id_producto,
            'nombreproducto': producto.nombreproducto,
            'precioproducto': float(producto.precioproducto) if producto.precioproducto else 0.0,
            'existenciaproducto': producto.existenciaproducto,
            'existenciaminima': producto.existenciaminima if producto.existenciaminima else 0,
            'bajo_stock': producto.necesita_reposicion
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado o inactivo.'}, status=404)

@ajax_login_required
def api_empleado_info(request, empleado_id):
    try:
        empleado = Empleado.objects.get(idempleado=empleado_id, estadoempleado=True)
        data = {
            'idempleado': empleado.idempleado,
            'nombre_completo': empleado.nombre_completo_empleado,
            'rolempleado': empleado.rolempleado
        }
        return JsonResponse(data)
    except Empleado.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado o inactivo.'}, status=404)

@ajax_login_required
def api_check_session(request):
    user_data = {
        'id': request.nexo_user.idusuario,
        'username': request.nexo_user.nombreusuario,
        'role': request.nexo_user.rol,
        'employee_name': request.nexo_user.empleado_nombre
    }
    return JsonResponse({
        'authenticated': True, 'user': user_data,
        'session_info': {
            'login_time': request.session.get('login_time'), 
            'expires_at': request.session.get_expiry_date().isoformat() if request.session.get_expiry_date() else None
        }
    })

@nexo_login_required
def produccion_dashboard(request):
    stats_data = {'total_producciones': 0, 'producciones_hoy': 0, 'producciones_semana': 0, 'producciones_mes': 0}
    productos_top_data = []
    empleados_top_data = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(pp.idProduccion) as total_producciones,
                    SUM(CASE WHEN DATE(pp.fechaEntrada) = CURDATE() THEN 1 ELSE 0 END) as producciones_hoy,
                    SUM(CASE WHEN WEEK(pp.fechaEntrada, 1) = WEEK(CURDATE(), 1) AND YEAR(pp.fechaEntrada) = YEAR(CURDATE()) THEN 1 ELSE 0 END) as producciones_semana,
                    SUM(CASE WHEN MONTH(pp.fechaEntrada) = MONTH(CURDATE()) AND YEAR(pp.fechaEntrada) = YEAR(CURDATE()) THEN 1 ELSE 0 END) as producciones_mes
                FROM ProductosProduccion pp WHERE pp.EstadoRegistro = 1
            """)
            stats_row = cursor.fetchone()
            if stats_row:
                stats_data = {'total_producciones': stats_row[0] or 0, 'producciones_hoy': stats_row[1] or 0, 
                            'producciones_semana': stats_row[2] or 0, 'producciones_mes': stats_row[3] or 0}
            
            cursor.execute("""
                SELECT p.nombreProducto, SUM(dp.cantidad) as total_producido
                FROM DetalleProduccion dp
                JOIN Producto p ON dp.id_producto = p.id_producto
                JOIN ProductosProduccion pp ON dp.id_produccion = pp.idProduccion
                WHERE pp.EstadoRegistro = 1
                GROUP BY p.id_producto, p.nombreProducto ORDER BY total_producido DESC LIMIT 5
            """)
            productos_top_data = [{'nombre': row[0], 'total': row[1]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT 
                    CONCAT(per.primerNombre, ' ', per.primerApellido) as nombre_completo,
                    COUNT(DISTINCT dp.id_produccion) as total_ordenes_produccion,
                    SUM(dp.cantidad) as total_unidades_fabricadas
                FROM DetalleProduccion dp
                JOIN Empleado e ON dp.idFabricante = e.idEmpleado
                JOIN Persona per ON e.idPersonaEmp = per.cedula
                JOIN ProductosProduccion pp ON dp.id_produccion = pp.idProduccion
                WHERE pp.EstadoRegistro = 1 AND e.estadoempleado = 1
                GROUP BY e.idEmpleado, nombre_completo ORDER BY total_unidades_fabricadas DESC LIMIT 5
            """)
            empleados_top_data = [{'nombre': row[0], 'ordenes': row[1], 'unidades': row[2]} for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error al cargar dashboard de producción: {str(e)}")
        messages.warning(request, f"Error al cargar estadísticas del dashboard: {str(e)}")

    context = {
        'stats': stats_data, 'productos_top': productos_top_data, 'empleados_top': empleados_top_data,
        'page_title': 'Dashboard de Producción',
        'page_subtitle': 'Estadísticas y métricas clave del área de producción.',
        'user': request.nexo_user, 'colores': colores_nexo
    }
    return render(request, 'produccion/dashboard.html', context)
