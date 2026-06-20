# Create your views here.
# ventas/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.db import connection, transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.messages import get_messages

import json
import logging
from datetime import date, timedelta
from decimal import Decimal

# Importar decoradores de autenticación
from AuthLogin.decorators import nexo_login_required, nexo_role_required, ajax_login_required

# Importar modelos y formularios
from .models import (
    Venta, Detalleventa, Cliente, Producto, Usuario,
    obtener_productos_disponibles, obtener_clientes_activos,
    obtener_ventas_del_dia, calcular_estadisticas_ventas
)
from .forms import VentaForm, DetalleVentaForm, FiltroVentasForm, BusquedaRapidaForm

logger = logging.getLogger('nexo.ventas')

# Utilidad para limpiar mensajes
def clear_messages(request):
    list(get_messages(request))

@nexo_login_required
@require_http_methods(["GET"])
def lista_ventas(request):
    """
    Vista principal que muestra la lista de ventas con filtros
    """
    try:
        logger.info(f"Usuario {request.nexo_user.nombreusuario} accedió a lista de ventas")
        filtro_form = FiltroVentasForm(request.GET)
        busqueda_form = BusquedaRapidaForm(request.GET)
        ventas = Venta.objects.select_related(
            'codcliente__idpersonacliente',
            'idusuarioventa'
        ).exclude(id_venta__isnull=True).order_by('-fechaventa')
        if filtro_form.is_valid():
            if filtro_form.cleaned_data['fecha_inicio']:
                ventas = ventas.filter(fechaventa__date__gte=filtro_form.cleaned_data['fecha_inicio'])
            if filtro_form.cleaned_data['fecha_fin']:
                ventas = ventas.filter(fechaventa__date__lte=filtro_form.cleaned_data['fecha_fin'])
            if filtro_form.cleaned_data['cliente']:
                ventas = ventas.filter(codcliente=filtro_form.cleaned_data['cliente'])
            if filtro_form.cleaned_data['estado']:
                ventas = ventas.filter(estado=filtro_form.cleaned_data['estado'])
        if busqueda_form.is_valid() and busqueda_form.cleaned_data['q']:
            query = busqueda_form.cleaned_data['q']
            ventas = ventas.filter(
                Q(id_venta__icontains=query) |
                Q(codcliente__idpersonacliente__primernombre__icontains=query) |
                Q(codcliente__idpersonacliente__primerapellido__icontains=query)
            )
        paginator = Paginator(ventas, 15)
        page = request.GET.get('page', 1)
        ventas_paginadas = paginator.get_page(page)
        estadisticas = calcular_estadisticas_ventas()
        ventas_hoy_total = estadisticas.get('ventas_hoy', {}).get('total', 0) or 0
        ventas_ayer_total = estadisticas.get('ventas_ayer', {}).get('total', 0) or 0
        diferencia_ventas = ventas_hoy_total - ventas_ayer_total
        usuario_actual = request.nexo_user
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        user_rol = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        nexo_user_role = user_rol
        # Permisos para acciones
        puede_editar = nexo_user_role in ['admin', 'encargado_sucursal']
        puede_anular = nexo_user_role in ['admin', 'encargado_sucursal']
        # Pasar permisos al contexto para cada venta
        context = {
            'page_title': 'Gestión de Ventas - NEXO',
            'ventas': ventas_paginadas,
            'filtro_form': filtro_form,
            'busqueda_form': busqueda_form,
            'estadisticas': estadisticas,
            'diferencia_ventas': diferencia_ventas,
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'nexo_user_role': nexo_user_role,
            'puede_editar': puede_editar,
            'puede_anular': puede_anular,
        }
        # Eliminar ventas_crudo del contexto y usar solo ventas paginadas
        # Los datos de cliente y vendedor ya están disponibles por select_related
        # Si se requiere iniciales, se puede agregar con annotate o en el template
        # context['ventas_crudo'] = ventas_crudo  # ELIMINADO

        # Obtener fechas crudas de MySQL para todas las ventas listadas en la página
        ventas_ids = [v.id_venta for v in ventas_paginadas]
        fechas_crudas = {}
        if ventas_ids:
            with connection.cursor() as cursor:
                format_strings = ','.join(['%s'] * len(ventas_ids))
                cursor.execute(f"SELECT id_venta, fechaVenta FROM venta WHERE id_venta IN ({format_strings})", ventas_ids)
                for row in cursor.fetchall():
                    fechas_crudas[row[0]] = row[1]
        # Asignar la fecha cruda como atributo a cada venta para uso directo en el template
        for v in ventas_paginadas:
            v.fechaventa_cruda = fechas_crudas.get(v.id_venta)
            # Cliente
            if v.codcliente and v.codcliente.idpersonacliente:
                v.cliente_nombre = v.codcliente.idpersonacliente.nombre_completo
                v.cliente_iniciales = f"{v.codcliente.idpersonacliente.primernombre[:1]}{v.codcliente.idpersonacliente.primerapellido[:1]}"
            else:
                v.cliente_nombre = None
                v.cliente_iniciales = None
            # Vendedor
            if v.idusuarioventa:
                v.vendedor_nombre = v.idusuarioventa.nombreusuario
            else:
                v.vendedor_nombre = None

        return render(request, 'ventas/lista_ventas.html', context)
    except Exception as e:
        logger.error(f"Error en lista_ventas: {str(e)}")
        clear_messages(request)
        messages.error(request, 'No se pudo cargar la lista de ventas. Por favor, intente nuevamente o contacte a soporte si el problema persiste.')
        usuario_actual = getattr(request, 'nexo_user', None)
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        user_rol = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        nexo_user_role = user_rol
        return render(request, 'ventas/lista_ventas.html', {
            'page_title': 'Error - Ventas',
            'ventas': [],
            'filtro_form': FiltroVentasForm(),
            'busqueda_form': BusquedaRapidaForm(),
            'estadisticas': {'ventas_hoy': {'total': 0, 'cantidad': 0}, 'ventas_ayer': {'total': 0, 'cantidad': 0}},
            'diferencia_ventas': 0,
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'nexo_user_role': nexo_user_role,
            'puede_editar': False,
            'puede_anular': False,
        })

@nexo_login_required
@require_http_methods(["GET", "POST"])
def crear_venta(request):
    """
    Vista para crear una nueva venta
    """
    try:
        if request.method == 'POST':
            # Procesar la venta usando el procedimiento almacenado
            return procesar_venta_nueva(request)
        
        # GET - Mostrar formulario
        venta_form = VentaForm()
        detalle_form = DetalleVentaForm()
        
        # Obtener datos necesarios
        productos_disponibles = obtener_productos_disponibles()
        clientes_activos = obtener_clientes_activos()
        
        usuario_actual = request.nexo_user
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        user_rol = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        context = {
            'page_title': 'Nueva Venta - NEXO',
            'venta_form': venta_form,
            'detalle_form': detalle_form,
            'productos_disponibles': productos_disponibles,
            'clientes_activos': clientes_activos,
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'user_rol': user_rol,
        }
        
        return render(request, 'ventas/crear_venta.html', context)
        
    except Exception as e:
        logger.error(f"Error en crear_venta: {str(e)}")
        clear_messages(request)
        messages.error(request, 'Ocurrió un error al intentar registrar la venta. Revise los datos e intente nuevamente.')
        return redirect('ventas:lista_ventas')

def procesar_venta_nueva(request):
    """
    Procesa una nueva venta usando el procedimiento almacenado RealizarVenta
    """
    try:
        # Obtener datos del formulario
        cliente_id = request.POST.get('codcliente')
        detalles_json = request.POST.get('detalles_venta')
        
        if not cliente_id or not detalles_json:
            clear_messages(request)
            messages.error(request, 'Debe seleccionar un cliente y agregar al menos un producto para registrar la venta.')
            return redirect('ventas:crear_venta')
        
        # Validar JSON de detalles
        try:
            detalles = json.loads(detalles_json)
        except json.JSONDecodeError:
            clear_messages(request)
            messages.error(request, 'El formato de los productos es inválido. Por favor, revise la información e intente de nuevo.')
            return redirect('ventas:crear_venta')
        
        # Ejecutar procedimiento almacenado
        with connection.cursor() as cursor:
            cursor.callproc('RealizarVenta', [
                request.nexo_user.idusuario,  # ID del usuario
                int(cliente_id),              # ID del cliente
                detalles_json                 # JSON con detalles
            ])
        logger.info(f"Venta creada exitosamente por usuario {request.nexo_user.nombreusuario}")
        # Obtener el último ID de venta creada
        nueva_venta = Venta.objects.filter(idusuarioventa=request.nexo_user).order_by('-id_venta').first()
        clear_messages(request)
        if nueva_venta:
            messages.success(request, f'Venta #{nueva_venta.id_venta} registrada exitosamente.')
        else:
            messages.success(request, 'Venta registrada exitosamente.')
        return redirect('ventas:lista_ventas')
    except Exception as e:
        logger.error(f"Error al procesar venta nueva: {str(e)}")
        clear_messages(request)
        messages.error(request, 'No se pudo registrar la venta. Por favor, revise los datos e intente nuevamente.')
        return redirect('ventas:crear_venta')

@nexo_login_required
@require_http_methods(["GET"])
def detalle_venta(request, venta_id):
    """
    Redirige al listado porque la vista de detalle ya no forma parte del flujo.
    """
    messages.info(request, 'Los detalles de venta se gestionan desde el listado.')
    return redirect('ventas:lista_ventas')

@nexo_login_required
def procesar_edicion_venta(request, venta_id):
    """
    Procesa la edición de una venta usando el procedimiento almacenado EditarVenta
    """
    try:
        detalles_json = request.POST.get('detalles_venta')
        if not detalles_json:
            clear_messages(request)
            messages.error(request, 'Debe agregar al menos un producto válido para editar la venta.')
            return redirect('ventas:editar_venta', venta_id=venta_id)
        try:
            Venta.editar(venta_id, request.nexo_user.idusuario, detalles_json)
            logger.info(f"Venta {venta_id} editada por usuario {request.nexo_user.nombreusuario}")
            clear_messages(request)
            messages.success(request, f'¡Venta #{venta_id} actualizada correctamente!')
            return redirect('ventas:lista_ventas')
        except Exception as e:
            clear_messages(request)
            messages.error(request, f'No se pudo actualizar la venta: {str(e)}')
            return redirect('ventas:editar_venta', venta_id=venta_id)
    except Exception as e:
        clear_messages(request)
        messages.error(request, f'No se pudo actualizar la venta. Detalle: {str(e)}')
        return redirect('ventas:editar_venta', venta_id=venta_id)

@nexo_role_required(['admin', 'encargado_sucursal'])
@require_http_methods(["POST"])
def anular_venta(request, venta_id):
    """
    Vista para anular una venta (solo POST, robusta y segura)
    Solo para administradores y gerentes
    """
    try:
        # Validación robusta del ID antes de cualquier lógica
        try:
            venta_id_int = int(venta_id)
            if venta_id_int <= 0:
                raise ValueError("ID de venta debe ser mayor que cero")
        except (TypeError, ValueError):
            logger.error(f"[ANULAR] ID de venta inválido recibido: {venta_id!r}")
            clear_messages(request)
            messages.error(request, 'No se puede anular: ID de venta vacío o inválido.')
            return redirect('ventas:lista_ventas')
        logger.info(f"[ANULAR] venta_id recibido en view: {venta_id!r} (tipo: {type(venta_id)})")
        estado, msg = Venta.verificar_estado_venta(venta_id_int)
        if estado is None:
            clear_messages(request)
            messages.error(request, f'No se puede anular: {msg}')
            return redirect('ventas:lista_ventas')
        if estado != 'REALIZADA':
            clear_messages(request)
            messages.error(request, f'Solo se pueden anular ventas en estado REALIZADA. Estado actual: {estado}')
            return redirect('ventas:lista_ventas')
        try:
            Venta.anular(venta_id_int)
            logger.info(f"Venta {venta_id_int} anulada por usuario {request.nexo_user.nombreusuario}")
            clear_messages(request)
            messages.success(request, f'<i class="fas fa-ban"></i> Venta <b>#{venta_id_int}</b> anulada correctamente. El stock fue restablecido.')
        except Exception as e:
            logger.error(f"Error SQL al anular venta {venta_id_int}: {str(e)}")
            clear_messages(request)
            messages.error(request, f'<i class="fas fa-times-circle"></i> {str(e)}')
        return redirect('ventas:lista_ventas')
    except Exception as e:
        logger.error(f"Error general en anular_venta: {str(e)}")
        clear_messages(request)
        messages.error(request, f'<i class="fas fa-times-circle"></i> No se pudo anular la venta: {str(e)}')
        return redirect('ventas:lista_ventas')

@ajax_login_required
def obtener_info_producto(request):
    """
    Vista AJAX para obtener información de un producto
    """
    try:
        producto_id = request.GET.get('producto_id')
        
        if not producto_id:
            return JsonResponse({'success': False, 'message': 'ID de producto requerido'})
        
        producto = get_object_or_404(
            Producto.objects.select_related('idcategoriapro'),
            id_producto=producto_id,
            estado=True,
            idubicacionpro_id=2  # Solo sucursal
        )
        
        data = {
            'success': True,
            'producto': {
                'id': producto.id_producto,
                'nombre': producto.nombreproducto,
                'precio': float(producto.precioproducto) if producto.precioproducto else 0,
                'stock': producto.existenciaproducto,
                'categoria': producto.idcategoriapro.nombrecategoria if producto.idcategoriapro else '',
                'precio_con_impuesto': float(producto.precioproducto * Decimal('1.15')) if producto.precioproducto else 0
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error en obtener_info_producto: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error al obtener información del producto'
        })

@ajax_login_required
def estadisticas_ventas_ajax(request):
    """
    Vista AJAX para obtener estadísticas de ventas en tiempo real
    """
    try:
        estadisticas = calcular_estadisticas_ventas()
        ventas_hoy = obtener_ventas_del_dia()
        data = {
            'success': True,
            'estadisticas': estadisticas,
            'ventas_hoy_count': ventas_hoy.count() if ventas_hoy else 0,
            'timestamp': timezone.now().isoformat()
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error en estadisticas_ventas_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error al obtener estadísticas'
        })

@nexo_role_required(['admin','encargado_sucursal'])
@require_http_methods(["GET", "POST"])
def editar_venta(request, venta_id):
    """
    Vista para editar una venta existente
    Solo para usuarios con permisos específicos y ventas en estado REALIZADA
    """
    try:
        estado, msg = Venta.verificar_estado_venta(venta_id)
        if estado is None:
            messages.error(request, f'No se puede editar: {msg}')
            return redirect('ventas:lista_ventas')
        if estado != 'REALIZADA':
            messages.error(request, f'Solo se pueden editar ventas en estado REALIZADA. Estado actual: {estado}')
            return redirect('ventas:lista_ventas')
        if request.method == 'POST':
            return procesar_edicion_venta(request, venta_id)
        # GET - Mostrar formulario de edición
        venta = get_object_or_404(Venta, id_venta=venta_id)
        venta_form = VentaForm(instance=venta)
        detalle_form = DetalleVentaForm()
        detalles_actuales = Detalleventa.objects.filter(idventa=venta, idproventa__idubicacionpro_id=2).select_related('idproventa')
        productos_disponibles = obtener_productos_disponibles()
        usuario_actual = request.nexo_user
        user_iniciales = usuario_actual.nombreusuario[:2].upper() if usuario_actual and usuario_actual.nombreusuario else "IN"
        user_rol = usuario_actual.rol if usuario_actual and usuario_actual.rol else 'Usuario'
        # Preparar detalles en formato JSON para el formulario
        detalles_json = json.dumps([
            {
                'idProVenta': str(d.idproventa.id_producto),
                'cantidadVenta': d.cantidadventa,
                'nombreProducto': d.idproventa.nombreproducto,
                'precioUnitario': float(d.idproventa.precioproducto) * 1.15  # o el precio con IVA que uses
            }
            for d in detalles_actuales
        ])
        context = {
            'page_title': f'Editar Venta #{venta.id_venta} - NEXO',
            'venta': venta,
            'venta_form': venta_form,
            'detalle_form': detalle_form,
            'detalles_actuales': detalles_actuales,
            'productos_disponibles': productos_disponibles,
            'usuario_actual': usuario_actual,
            'user_iniciales': user_iniciales,
            'user_rol': user_rol,
            'detalles_json': detalles_json,  # Agregar detalles en formato JSON
        }
        return render(request, 'ventas/editar_venta.html', context)
    except Exception as e:
        logger.error(f"Error en editar_venta: {str(e)}")
        clear_messages(request)
        messages.error(request, 'No se pudo cargar la edición de la venta.')
        return redirect('ventas:lista_ventas')
