from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging
import json
from django.db import connection

from core_data.models import Devolucion, Producto, Usuario, Venta, Detalleventa
from .models import DevolucionManager
from .forms import DevolucionForm, DetalleDevolucionFormSet, DevolucionSearchForm

try:
    from AuthLogin.decorators import nexo_login_required, nexo_role_required
except ImportError:
    def nexo_login_required(view_func): return view_func
    def nexo_role_required(roles):
        def decorator(view_func): return view_func
        return decorator

logger = logging.getLogger('nexo.devolucion')

COLORES_NEXO = {
    'primary': '#39bfb2', 'secondary_yellow': '#F2CE16', 'accent_orange': '#F29D35',
    'accent_dark_orange': '#F28627', 'bg_light': '#eaeef3', 'bg_very_light': '#F2F2F2',
    'white': '#ffffff', 'text_dark': '#374151', 'text_medium': '#6b7280', 'text_light': '#9ca3af',
    'success': '#39bfb2', 'warning': '#F2CE16', 'danger': '#F28627', 'info': '#2752F2'
}

def get_sale_products_map(include_sale_id=None, exclude_devolucion_id=None):
    params = []
    sale_filter = "v.estado = 'REALIZADA'"
    exclude_filter = ""
    if exclude_devolucion_id:
        exclude_filter = "AND d.idDevolucion <> %s"
        params.append(exclude_devolucion_id)
    if include_sale_id:
        sale_filter = "(v.estado = 'REALIZADA' OR dv.idVenta = %s)"
        params.append(include_sale_id)

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT
                dv.idVenta AS sale_id,
                dv.idProVenta AS product_id,
                COALESCE((
                    SELECT p.nombreProducto
                    FROM Producto p
                    WHERE p.id_producto = dv.idProVenta
                    ORDER BY p.idUbicacionPro DESC
                    LIMIT 1
                ), dv.idProVenta) AS product_name,
                dv.cantidadVenta AS sold_quantity,
                GREATEST(dv.cantidadVenta - COALESCE(SUM(dd.cantidadDevuelta), 0), 0) AS available_quantity
            FROM DetalleVenta dv
            JOIN Venta v ON dv.idVenta = v.id_venta
            LEFT JOIN Devolucion d ON d.idVentaDev = dv.idVenta {exclude_filter}
            LEFT JOIN DetalleDevolucion dd
                ON dd.id_devolucion = d.idDevolucion
               AND dd.id_producto = dv.idProVenta
            WHERE {sale_filter}
            GROUP BY dv.idVenta, dv.idProVenta, dv.cantidadVenta
            ORDER BY dv.idVenta, dv.idProVenta
        """, params)
        columns = [column[0] for column in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    products_by_sale = {}
    seen = set()
    for row in rows:
        sale_id = str(row['sale_id'])
        product_id = str(row['product_id'])
        key = (sale_id, product_id)
        if key in seen:
            continue
        seen.add(key)
        products_by_sale.setdefault(sale_id, []).append({
            'id': row['product_id'],
            'nombre': row['product_name'],
            'vendido': int(row['sold_quantity'] or 0),
            'disponible': int(row['available_quantity'] or 0)
        })

    return products_by_sale


def get_return_limits(id_venta, exclude_devolucion_id=None):
    products_by_sale = get_sale_products_map(
        include_sale_id=id_venta,
        exclude_devolucion_id=exclude_devolucion_id
    )
    return {
        str(product['id']): product
        for product in products_by_sale.get(str(id_venta), [])
    }


def validate_return_quantities(id_venta, detalles, exclude_devolucion_id=None):
    limits = get_return_limits(id_venta, exclude_devolucion_id)
    errors = []
    for detalle in detalles:
        product_id = str(detalle['id_producto'])
        cantidad = int(detalle['cantidadDevuelta'] or 0)
        limit = limits.get(product_id)
        if not limit:
            errors.append(f'El producto {product_id} no pertenece a la venta seleccionada.')
            continue
        if cantidad > limit['disponible']:
            errors.append(
                f"{limit['nombre']}: solo puede devolver {limit['disponible']} "
                f"de {limit['vendido']} vendido(s)."
            )
    return errors

@nexo_login_required
@nexo_role_required(['admin'])
def devolucion_list(request):
    search_form = DevolucionSearchForm(request.GET or None)
    filtros = {}
    if search_form.is_valid():
        if search_form.cleaned_data.get('fecha_desde'):
            filtros['fecha_desde'] = search_form.cleaned_data['fecha_desde']
        if search_form.cleaned_data.get('fecha_hasta'):
            filtros['fecha_hasta'] = search_form.cleaned_data['fecha_hasta']
        if search_form.cleaned_data.get('usuario'):
            filtros['persona_id'] = search_form.cleaned_data['usuario'].idusuario

    page = request.GET.get('page', 1)
    try:
        resultado = DevolucionManager.obtener_devoluciones_con_filtros(filtros, int(page), 10)
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
        logger.error(f"Error al cargar devoluciones: {str(e)}")
        messages.error(request, f"Error al cargar las devoluciones: {str(e)}")
        page_obj = MockPage({'results': [], 'total_count': 0, 'page': 1, 'total_pages': 1,
                             'has_previous': False, 'has_next': False, 'previous_page_number': None,
                             'next_page_number': None, 'per_page': 10})

    usuario_actual = getattr(request, 'nexo_user', None)
    context = {
        'page_obj': page_obj,
        'filtro_form': search_form,
        'total_count': page_obj.paginator.count,
        'page_title': 'Gestión de Devoluciones',
        'page_subtitle': 'Administra los registros de devolución de ventas.',
        'usuario_actual': usuario_actual,
        'user_iniciales': usuario_actual.nombreusuario[:2].upper() if usuario_actual else "IN",
        'nexo_user_role': usuario_actual.rol if usuario_actual else 'Usuario',
        'colores': COLORES_NEXO
    }
    return render(request, 'cdevolucion/list.html', context)

@nexo_login_required
@nexo_role_required(['admin'])
def devolucion_create(request):
    if request.method == 'POST':
        form = DevolucionForm(request.POST)
        detalle_formset = DetalleDevolucionFormSet(request.POST, prefix='detalles')
        if form.is_valid() and detalle_formset.is_valid():
            try:
                venta = form.cleaned_data['idVentaDev']
                productos_venta = set(
                    Detalleventa.objects.filter(idventa=venta).order_by('idproventa_id').values_list('idproventa_id', flat=True)
                )
                detalles_data = []
                detalles_validos = True
                for detalle_form in detalle_formset.cleaned_data:
                    if detalle_form and not detalle_form.get('DELETE', False):
                        producto_id = detalle_form['id_producto']
                        if producto_id not in productos_venta:
                            messages.error(request, 'Solo puede devolver productos incluidos en la venta seleccionada.')
                            detalles_validos = False
                            break
                        detalles_data.append({
                            'id_producto': producto_id,
                            'cantidadDevuelta': detalle_form['cantidadDevuelta']
                        })
                if detalles_validos:
                    productos_ids = [d['id_producto'] for d in detalles_data]
                    if len(productos_ids) != len(set(productos_ids)):
                        messages.error(request, 'No se permiten productos duplicados en la devolución.')
                        detalles_validos = False
                        detalles_data = []
                    for error in validate_return_quantities(venta.id_venta, detalles_data):
                        messages.error(request, error)
                        detalles_validos = False

                if not detalles_validos:
                    pass
                elif not detalles_data:
                    messages.error(request, 'Debe agregar al menos un producto devuelto válido.')
                else:
                    success, mensaje, id_devolucion = DevolucionManager.registrar_devolucion(
                        id_venta=venta.id_venta,
                        fecha_devolucion=form.cleaned_data['fechaDevolucion'],
                        motivo=form.cleaned_data['motivo'],
                        detalles=detalles_data,
                        id_usuario=getattr(request.nexo_user, 'idusuario', None)
                    )
                    if success:
                        messages.success(request, mensaje)
                        return redirect('devolucion:devolucion_list')
                    else:
                        messages.error(request, f'Error al registrar: {mensaje}')
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
        else:
            messages.error(request, 'Formulario inválido. Corrija los errores indicados.')
    else:
        form = DevolucionForm()
        detalle_formset = DetalleDevolucionFormSet(prefix='detalles', initial=[{}])

    usuario_actual = getattr(request, 'nexo_user', None)
    context = {
        'form': form,
        'detalle_formset': detalle_formset,
        'page_title': 'Registrar Devolución',
        'page_subtitle': 'Crear nuevo registro de devolución de productos.',
        'usuario_actual': usuario_actual,
        'user_iniciales': usuario_actual.nombreusuario[:2].upper() if usuario_actual else "IN",
        'nexo_user_role': usuario_actual.rol if usuario_actual else 'Usuario',
        'colores': COLORES_NEXO,
        'is_create': True,
        'sale_products_json': json.dumps(get_sale_products_map())
    }
    return render(request, 'cdevolucion/create.html', context)
 

@nexo_login_required
@nexo_role_required(['admin'])
def devolucion_detail(request, pk):
    messages.info(request, 'La consulta de devoluciones se realiza desde el listado.')
    return redirect('devolucion:devolucion_list')

    try:
        devolucion = get_object_or_404(Devolucion, iddevolucion=pk)

        # Traer todos los detalles asociados a esta devolución
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    dd.id_producto,
                    COALESCE((
                        SELECT p.nombreProducto
                        FROM Producto p
                        WHERE p.id_producto = dd.id_producto
                        ORDER BY p.idUbicacionPro DESC
                        LIMIT 1
                    ), dd.id_producto) AS nombreproducto,
                    dd.cantidadDevuelta,
                    (
                        SELECT p.existenciaProducto
                        FROM Producto p
                        WHERE p.id_producto = dd.id_producto
                          AND p.idUbicacionPro = 2
                        LIMIT 1
                    ) AS existenciaProducto
                FROM DetalleDevolucion dd
                WHERE dd.id_devolucion = %s
                ORDER BY dd.id_producto
            """, [pk])

            columns = [col[0] for col in cursor.description]
            detalles = [dict(zip(columns, row)) for row in cursor.fetchall()]

        usuario_actual = getattr(request, 'nexo_user', None)
        context = {
            'devolucion': devolucion,
            'detalles': detalles,
            'total_items': sum(d['cantidadDevuelta'] for d in detalles),
            'page_title': f'Detalle Devolución #{pk}',
            'page_subtitle': f'Registro de devolución del {devolucion.fechadevolucion.strftime("%d/%m/%Y")}',
            'usuario_actual': usuario_actual,
            'user_iniciales': usuario_actual.nombreusuario[:2].upper() if usuario_actual else "IN",
            'nexo_user_role': usuario_actual.rol if usuario_actual else 'Usuario',
            'colores': COLORES_NEXO,
        }
        return render(request, 'cdevolucion/detail.html', context)

    except Exception as e:
        logger.error(f"Error al cargar detalle de devolución {pk}: {str(e)}")
        messages.error(request, f'Error al cargar el detalle de la devolución: {str(e)}')
        return redirect('devolucion:devolucion_list')


@nexo_login_required
@nexo_role_required(['admin'])
def devolucion_edit(request, pk):
    devolucion = get_object_or_404(Devolucion, iddevolucion=pk)
    if request.method == 'POST':
        form = DevolucionForm(request.POST, include_venta_id=devolucion.idventadev_id)
        detalle_formset = DetalleDevolucionFormSet(request.POST, prefix='detalles')
        if form.is_valid() and detalle_formset.is_valid():
            try:
                detalles_data = []
                for detalle_form in detalle_formset.cleaned_data:
                    if detalle_form and not detalle_form.get('DELETE', False):
                        detalles_data.append({
                            'id_producto': detalle_form['id_producto'],
                            'cantidadDevuelta': detalle_form['cantidadDevuelta']
                        })
                productos_ids = [d['id_producto'] for d in detalles_data]
                if len(productos_ids) != len(set(productos_ids)):
                    messages.error(request, 'No se permiten productos duplicados en la devolución.')
                elif not detalles_data:
                    messages.error(request, 'Debe agregar al menos un producto devuelto válido.')
                else:
                    quantity_errors = validate_return_quantities(
                        devolucion.idventadev_id,
                        detalles_data,
                        exclude_devolucion_id=pk
                    )
                    if quantity_errors:
                        for error in quantity_errors:
                            messages.error(request, error)
                    else:
                        success, mensaje = DevolucionManager.editar_devolucion(
                            pk,
                            form.cleaned_data['fechaDevolucion'],
                            form.cleaned_data['motivo'],
                            detalles_data
                        )
                        if success:
                            messages.success(request, mensaje)
                            return redirect('devolucion:devolucion_list')
                        else:
                            messages.error(request, f'Error al editar: {mensaje}')
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
        else:
            for field_name, field_errors in form.errors.items():
                label = form.fields[field_name].label if field_name in form.fields else field_name
                messages.error(request, f'{label}: {" ".join(field_errors)}')
            for form_errors in detalle_formset.errors:
                for field_errors in form_errors.values():
                    messages.error(request, f'Detalle de devolución: {" ".join(field_errors)}')
            for error in detalle_formset.non_form_errors():
                messages.error(request, error)
            messages.error(request, 'Formulario inválido. Corrija los errores indicados.')
    else:
        form = DevolucionForm(include_venta_id=devolucion.idventadev_id, initial={
            'idVentaDev': devolucion.idventadev,
            'fechaDevolucion': devolucion.fechadevolucion,
            'motivo': devolucion.motivo
        })
        detalles_actuales = DevolucionManager.obtener_detalle_devolucion(pk)
        initial_detalles = []
        for detalle in detalles_actuales:
            if Producto.objects.filter(id_producto=detalle['id_producto'], estado=True).exists():
                initial_detalles.append({
                    'id_producto': detalle['id_producto'],
                    'cantidadDevuelta': detalle['cantidadDevuelta']
                })
        detalle_formset = DetalleDevolucionFormSet(prefix='detalles', initial=initial_detalles)

    usuario_actual = getattr(request, 'nexo_user', None)
    context = {
        'form': form,
        'detalle_formset': detalle_formset,
        'devolucion': devolucion,
        'page_title': f'Editar Devolución #{pk}',
        'page_subtitle': f'Modifica los datos de la devolución registrada el {devolucion.fechadevolucion.strftime("%d/%m/%Y")}.',
        'usuario_actual': usuario_actual,
        'user_iniciales': usuario_actual.nombreusuario[:2].upper() if usuario_actual else "IN",
        'nexo_user_role': usuario_actual.rol if usuario_actual else 'Usuario',
        'colores': COLORES_NEXO,
        'is_edit': True,
        'sale_products_json': json.dumps(get_sale_products_map(
            include_sale_id=devolucion.idventadev_id,
            exclude_devolucion_id=pk
        ))
    }
    return render(request, 'cdevolucion/edit.html', context)


@nexo_login_required
@nexo_role_required(['admin'])
@require_http_methods(["POST"])
def devolucion_anular(request, pk):
    success, mensaje = DevolucionManager.anular_devolucion(pk)
    if success:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)
    return redirect('devolucion:devolucion_list')

