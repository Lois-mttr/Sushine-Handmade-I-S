# Archivo generado automáticamente: views_devolucion.py
# Adaptación completa del views.py de Producción al módulo de Devolución

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
from django.db import connection

from core_data.models import Devolucion, Producto, Usuario, Venta
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
            filtros['usuario'] = search_form.cleaned_data['usuario'].nombreusuario

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

@nexo_role_required(['admin'])
def devolucion_create(request):
    if request.method == 'POST':
        form = DevolucionForm(request.POST)
        detalle_formset = DetalleDevolucionFormSet(request.POST, prefix='detalles')
        if form.is_valid() and detalle_formset.is_valid():
            try:
                detalles_data = []
                for detalle_form in detalle_formset.cleaned_data:
                    if detalle_form and not detalle_form.get('DELETE', False):
                        detalles_data.append({
                            'id_producto': detalle_form['id_producto'].id_producto,
                            'cantidadDevuelta': detalle_form['cantidadDevuelta']
                        })
                if not detalles_data:
                    messages.error(request, 'Debe agregar al menos un producto devuelto válido.')
                else:
                    success, mensaje, id_devolucion = DevolucionManager.registrar_devolucion(
                        id_venta=form.cleaned_data['idVentaDev'].id_venta,
                        fecha_devolucion=form.cleaned_data['fechaDevolucion'],
                        motivo=form.cleaned_data['motivo'],
                        detalles=detalles_data
                    )
                    if success:
                        messages.success(request, mensaje)
                        return redirect('crud:devolucion_detail', pk=id_devolucion)
                    else:
                        messages.error(request, f'Error al registrar: {mensaje}')
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
        else:
            messages.error(request, 'Formulario inválido. Corrija los errores indicados.')
    else:
        form = DevolucionForm()
        detalle_formset = DetalleDevolucionFormSet(prefix='detalles')

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
        'is_create': True
    }
    return render(request, 'cdevolucion/create.html', context)
 

@nexo_login_required
@nexo_role_required(['admin'])
def devolucion_detail(request, pk):
    try:
        devolucion = get_object_or_404(Devolucion, idDevolucion=pk)

        # Traer todos los detalles asociados a esta devolución
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    dd.id_producto,
                    p.nombreproducto,
                    dd.cantidadDevuelta
                FROM DetalleDevolucion dd
                JOIN Producto p ON dd.id_producto = p.id_producto
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
            'page_subtitle': f'Registro de devolución del {devolucion.fechaDevolucion.strftime("%d/%m/%Y")}',
            'usuario_actual': usuario_actual,
            'user_iniciales': usuario_actual.nombreusuario[:2].upper() if usuario_actual else "IN",
            'nexo_user_role': usuario_actual.rol if usuario_actual else 'Usuario',
            'colores': COLORES_NEXO,
        }
        return render(request, 'devolucion/detail.html', context)

    except Exception as e:
        logger.error(f"Error al cargar detalle de devolución {pk}: {str(e)}")
        messages.error(request, f'Error al cargar el detalle de la devolución: {str(e)}')
        return redirect('devolucion:devolucion_list')


@nexo_role_required(['admin'])
def devolucion_edit(request, pk):
    devolucion = get_object_or_404(Devolucion, idDevolucion=pk)
    if request.method == 'POST':
        form = DevolucionForm(request.POST)
        detalle_formset = DetalleDevolucionFormSet(request.POST, prefix='detalles')
        if form.is_valid() and detalle_formset.is_valid():
            try:
                detalles_data = []
                for detalle_form in detalle_formset.cleaned_data:
                    if detalle_form and not detalle_form.get('DELETE', False):
                        detalles_data.append({
                            'id_producto': detalle_form['id_producto'].id_producto,
                            'cantidadDevuelta': detalle_form['cantidadDevuelta']
                        })
                productos_ids = [d['id_producto'] for d in detalles_data]
                if len(productos_ids) != len(set(productos_ids)):
                    messages.error(request, 'No se permiten productos duplicados en la devolución.')
                elif not detalles_data:
                    messages.error(request, 'Debe agregar al menos un producto devuelto válido.')
                else:
                    success, mensaje = DevolucionManager.editar_devolucion(
                        pk,
                        form.cleaned_data['fechaDevolucion'],
                        form.cleaned_data['motivo'],
                        detalles_data
                    )
                    if success:
                        messages.success(request, mensaje)
                        return redirect('crud:devolucion_detail', pk=pk)
                    else:
                        messages.error(request, f'Error al editar: {mensaje}')
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
        else:
            messages.error(request, 'Formulario inválido. Corrija los errores.')
    else:
        form = DevolucionForm(initial={
            'idVentaDev': devolucion.idVentaDev,
            'fechaDevolucion': devolucion.fechaDevolucion,
            'motivo': devolucion.motivo
        })
        detalles_actuales = DevolucionManager.obtener_detalle_devolucion(pk)
        initial_detalles = []
        for detalle in detalles_actuales:
            producto = Producto.objects.filter(id_producto=detalle['id_producto'], estado=True).first()
            if producto:
                initial_detalles.append({
                    'id_producto': producto,
                    'cantidadDevuelta': detalle['cantidadDevuelta']
                })
        detalle_formset = DetalleDevolucionFormSet(prefix='detalles', initial=initial_detalles)

    usuario_actual = getattr(request, 'nexo_user', None)
    context = {
        'form': form,
        'detalle_formset': detalle_formset,
        'devolucion': devolucion,
        'page_title': f'Editar Devolución #{pk}',
        'page_subtitle': f'Modifica los datos de la devolución registrada el {devolucion.fechaDevolucion.strftime("%d/%m/%Y")}.',
        'usuario_actual': usuario_actual,
        'user_iniciales': usuario_actual.nombreusuario[:2].upper() if usuario_actual else "IN",
        'nexo_user_role': usuario_actual.rol if usuario_actual else 'Usuario',
        'colores': COLORES_NEXO,
        'is_edit': True
    }
    return render(request, 'cdevolucion/edit.html', context)
