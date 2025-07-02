# Create your views here.
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from AuthLogin.decorators import nexo_login_required, nexo_role_required
from .services import InformeService
from .utils import ExportadorInformes
from core_data.models import Categoria, Ubicacion, Cliente, Usuario
import logging

logger = logging.getLogger('nexo.informes')

@nexo_login_required
def lista_informes(request):
    """
    Vista principal que muestra la lista de informes disponibles
    """
    # Definir informes disponibles según el rol del usuario
    usuario = request.nexo_user
    rol = usuario.rol or 'encargado_sucursal'
    
    informes_disponibles = []
    
    # Informes básicos para todos los roles
    informes_basicos = [
        {
            'id': 'inventario_general',
            'nombre': 'Inventario General',
            'descripcion': 'Existencias actuales por producto y ubicación',
            'icono': 'package',
            'url': 'informes:inventario_general'
        },
        {
            'id': 'ventas',
            'nombre': 'Ventas',
            'descripcion': 'Registro de ventas realizadas',
            'icono': 'shopping-cart',
            'url': 'informes:ventas'
        },
        {
            'id': 'devoluciones',
            'nombre': 'Devoluciones',
            'descripcion': 'Devoluciones procesadas y sus causas',
            'icono': 'rotate-ccw',
            'url': 'informes:devoluciones'
        }
    ]
    
    # Informes adicionales para administradores
    informes_admin = [
        {
            'id': 'produccion',
            'nombre': 'Producción',
            'descripcion': 'Productos elaborados en taller',
            'icono': 'settings',
            'url': 'informes:produccion'
        },
        {
            'id': 'clientes',
            'nombre': 'Clientes',
            'descripcion': 'Estado actual de clientes del sistema',
            'icono': 'users',
            'url': 'informes:clientes'
        },
        {
            'id': 'usuarios_empleados',
            'nombre': 'Usuarios y Empleados',
            'descripcion': 'Roles, accesos y personal activo',
            'icono': 'user-check',
            'url': 'informes:usuarios_empleados'
        },
        {
            'id': 'productos_categoria',
            'nombre': 'Productos por Categoría',
            'descripción': 'Distribución y rotación por categoría',
            'icono': 'grid',
            'url': 'informes:productos_categoria'
        }
    ]
    
    # Asignar informes según el rol
    informes_disponibles = informes_basicos
    if rol == 'admin':
        informes_disponibles.extend(informes_admin)
    
    context = {
        'informes': informes_disponibles,
        'usuario': usuario,
        'titulo_pagina': 'Informes del Sistema'
    }
    
    return render(request, 'informes/lista_informes.html', context)

@nexo_login_required
def inventario_general(request):
    """
    Vista para el informe de inventario general
    """
    try:
        # Obtener filtros del request
        filtros = {}
        if request.GET.get('categoria'):
            filtros['categoria'] = request.GET.get('categoria')
        if request.GET.get('ubicacion'):
            filtros['ubicacion'] = request.GET.get('ubicacion')
        if request.GET.get('stock_bajo') == '1':
            filtros['stock_bajo'] = True
        
        # Obtener datos del servicio
        datos = InformeService.obtener_inventario_general(filtros)
        
        # Paginación
        paginator = Paginator(datos['productos'], 25)
        page_number = request.GET.get('page')
        productos_paginados = paginator.get_page(page_number)
        
        # Datos para filtros
        categorias = Categoria.objects.filter(estadocategoria=True)
        ubicaciones = Ubicacion.objects.all()
        
        context = {
            'productos': productos_paginados,
            'resumen': datos['resumen'],
            'categorias': categorias,
            'ubicaciones': ubicaciones,
            'filtros_aplicados': filtros,
            'titulo_informe': 'Inventario General',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/inventario_general.html', context)
        
    except Exception as e:
        logger.error(f"Error en inventario_general: {str(e)}")
        messages.error(request, 'Error al generar el informe de inventario.')
        return redirect('informes:lista_informes')

@nexo_role_required(['admin'])
def produccion(request):
    """
    Vista para el informe de producción (solo administradores)
    """
    try:
        # Obtener filtros de fecha
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        # Convertir fechas si existen
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Si no hay fechas, usar últimos 30 días
        if not fecha_inicio and not fecha_fin:
            fecha_fin = timezone.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30)
        
        # Obtener datos del servicio
        datos = InformeService.obtener_produccion(fecha_inicio, fecha_fin)
        
        # Paginación
        paginator = Paginator(datos['detalles'], 20)
        page_number = request.GET.get('page')
        detalles_paginados = paginator.get_page(page_number)
        
        context = {
            'producciones': datos['producciones'],
            'detalles': detalles_paginados,
            'resumen': datos['resumen'],
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'titulo_informe': 'Reporte de Producción',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/produccion.html', context)
        
    except Exception as e:
        logger.error(f"Error en produccion: {str(e)}")
        messages.error(request, 'Error al generar el informe de producción.')
        return redirect('informes:lista_informes')

@nexo_login_required
def ventas(request):
    """
    Vista para el informe de ventas
    """
    try:
        # Obtener filtros
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        filtros = {}
        if request.GET.get('cliente'):
            filtros['cliente'] = request.GET.get('cliente')
        if request.GET.get('vendedor'):
            filtros['vendedor'] = request.GET.get('vendedor')
        
        # Convertir fechas
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Fechas por defecto (último mes)
        if not fecha_inicio and not fecha_fin:
            fecha_fin = timezone.now()
            fecha_inicio = fecha_fin - timedelta(days=30)
        
        # Obtener datos
        datos = InformeService.obtener_ventas(fecha_inicio, fecha_fin, filtros)
        
        # Paginación
        paginator = Paginator(datos['ventas'], 20)
        page_number = request.GET.get('page')
        ventas_paginadas = paginator.get_page(page_number)
        
        # Datos para filtros
        clientes = Cliente.objects.filter(estadocliente=True).select_related('idpersonacliente')
        vendedores = Usuario.objects.filter(activo=True)
        
        context = {
            'ventas': ventas_paginadas,
            'resumen': datos['resumen'],
            'clientes': clientes,
            'vendedores': vendedores,
            'filtros_aplicados': filtros,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'titulo_informe': 'Reporte de Ventas',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/ventas.html', context)
        
    except Exception as e:
        logger.error(f"Error en ventas: {str(e)}")
        messages.error(request, 'Error al generar el informe de ventas.')
        return redirect('informes:lista_informes')

@nexo_login_required
def devoluciones(request):
    """
    Vista para el informe de devoluciones
    """
    try:
        # Obtener filtros de fecha
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Obtener datos
        datos = InformeService.obtener_devoluciones(fecha_inicio, fecha_fin)
        
        # Paginación
        paginator = Paginator(datos['devoluciones'], 15)
        page_number = request.GET.get('page')
        devoluciones_paginadas = paginator.get_page(page_number)
        
        context = {
            'devoluciones': devoluciones_paginadas,
            'detalles': datos['detalles'],
            'resumen': datos['resumen'],
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'titulo_informe': 'Reporte de Devoluciones',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/devoluciones.html', context)
        
    except Exception as e:
        logger.error(f"Error en devoluciones: {str(e)}")
        messages.error(request, 'Error al generar el informe de devoluciones.')
        return redirect('informes:lista_informes')

@nexo_role_required(['admin'])
def clientes(request):
    """
    Vista para el informe de clientes (solo administradores)
    """
    try:
        # Obtener filtros
        filtros = {}
        if request.GET.get('activos_solo') == '1':
            filtros['activos_solo'] = True
        
        # Obtener datos
        datos = InformeService.obtener_clientes(filtros)
        
        # Paginación
        paginator = Paginator(datos['clientes'], 25)
        page_number = request.GET.get('page')
        clientes_paginados = paginator.get_page(page_number)
        
        context = {
            'clientes': clientes_paginados,
            'resumen': datos['resumen'],
            'filtros_aplicados': filtros,
            'titulo_informe': 'Reporte de Clientes',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/clientes.html', context)
        
    except Exception as e:
        logger.error(f"Error en clientes: {str(e)}")
        messages.error(request, 'Error al generar el informe de clientes.')
        return redirect('informes:lista_informes')

@nexo_role_required(['admin'])
def usuarios_empleados(request):
    """
    Vista para el informe de usuarios y empleados (solo administradores)
    """
    try:
        # Obtener datos
        datos = InformeService.obtener_usuarios_empleados()
        
        context = {
            'usuarios': datos['usuarios'],
            'empleados': datos['empleados'],
            'roles_count': datos['roles_count'],
            'resumen': datos['resumen'],
            'titulo_informe': 'Usuarios y Empleados',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/usuarios_empleados.html', context)
        
    except Exception as e:
        logger.error(f"Error en usuarios_empleados: {str(e)}")
        messages.error(request, 'Error al generar el informe de usuarios y empleados.')
        return redirect('informes:lista_informes')

@nexo_login_required
def productos_categoria(request):
    """
    Vista para el informe de productos por categoría
    """
    try:
        # Obtener datos
        datos = InformeService.obtener_productos_por_categoria()
        
        context = {
            'categorias': datos['categorias'],
            'resumen': datos['resumen'],
            'titulo_informe': 'Productos por Categoría',
            'usuario_generador': request.nexo_user.empleado_nombre or request.nexo_user.nombreusuario,
            'fecha_generacion': timezone.now()
        }
        
        return render(request, 'informes/productos_categoria.html', context)
        
    except Exception as e:
        logger.error(f"Error en productos_categoria: {str(e)}")
        messages.error(request, 'Error al generar el informe de productos por categoría.')
        return redirect('informes:lista_informes')

# Vistas para exportación
@nexo_login_required
def exportar_pdf(request, tipo_informe):
    """
    Vista para exportar informes a PDF
    """
    try:
        exportador = ExportadorInformes()
        
        # Obtener los mismos filtros que se usaron en la vista
        filtros = dict(request.GET)
        
        # Generar PDF según el tipo de informe
        if tipo_informe == 'inventario_general':
            datos = InformeService.obtener_inventario_general(filtros)
            pdf_content = exportador.generar_pdf_inventario(datos, request.nexo_user)
        elif tipo_informe == 'ventas':
            # Procesar fechas y filtros para ventas
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            
            datos = InformeService.obtener_ventas(fecha_inicio, fecha_fin, filtros)
            pdf_content = exportador.generar_pdf_ventas(datos, request.nexo_user, fecha_inicio, fecha_fin)
        # Agregar más tipos según sea necesario
        else:
            messages.error(request, 'Tipo de informe no válido para exportación.')
            return redirect('informes:lista_informes')
        
        # Crear respuesta HTTP con el PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="informe_{tipo_informe}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error en exportar_pdf: {str(e)}")
        messages.error(request, 'Error al exportar el informe a PDF.')
        return redirect('informes:lista_informes')

@nexo_login_required
def exportar_excel(request, tipo_informe):
    """
    Vista para exportar informes a Excel
    """
    try:
        exportador = ExportadorInformes()
        
        # Obtener los mismos filtros que se usaron en la vista
        filtros = dict(request.GET)
        
        # Generar Excel según el tipo de informe
        if tipo_informe == 'inventario_general':
            datos = InformeService.obtener_inventario_general(filtros)
            excel_content = exportador.generar_excel_inventario(datos)
        elif tipo_informe == 'ventas':
            # Procesar fechas y filtros para ventas
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            
            datos = InformeService.obtener_ventas(fecha_inicio, fecha_fin, filtros)
            excel_content = exportador.generar_excel_ventas(datos)
        # Agregar más tipos según sea necesario
        else:
            messages.error(request, 'Tipo de informe no válido para exportación.')
            return redirect('informes:lista_informes')
        
        # Crear respuesta HTTP con el Excel
        response = HttpResponse(
            excel_content, 
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="informe_{tipo_informe}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error en exportar_excel: {str(e)}")
        messages.error(request, 'Error al exportar el informe a Excel.')
        return redirect('informes:lista_informes')
