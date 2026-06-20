from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F, Avg
from datetime import datetime, timedelta
from AuthLogin.decorators import nexo_login_required, nexo_role_required
from .services import InformeService
from .utils import ExportadorInformes
from core_data.models import Categoria, Ubicacion, Cliente, Usuario, Producto, Venta
import logging

logger = logging.getLogger('nexo.informes')

@nexo_login_required
def lista_informes(request):
    """
    Vista principal mejorada que muestra la lista de informes disponibles con métricas reales
    """
    usuario = request.nexo_user
    rol = usuario.rol or 'encargado_sucursal'
    
    # Obtener métricas del dashboard
    metricas = InformeService.obtener_metricas_dashboard()
    
    # Preparar datos del usuario para el header
    user_iniciales = "IN"
    usuario_actual = None
    nexo_user_role = "Usuario"
    
    if usuario:
        usuario_actual = usuario
        if usuario.nombreusuario:
            user_iniciales = usuario.nombreusuario[:2].upper()
        
        nexo_user_role = {
            'admin': 'Administrador',
            'encargado_sucursal': 'Encargado de Sucursal',
            'vendedor': 'Vendedor',
            'cajero': 'Cajero'
        }.get(rol, 'Usuario')
    
    # Definir informes disponibles según el rol del usuario
    informes_disponibles = []
    
    # Informes básicos para todos los roles
    informes_basicos = [
        {
            'id': 'inventario_general',
            'nombre': 'Inventario General',
            'descripcion': 'Existencias actuales por producto y ubicación',
            'icono': 'boxes',
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
            'icono': 'undo',
            'url': 'informes:devoluciones'
        }
    ]
    
    # Informes adicionales para administradores
    informes_admin = [
        {
            'id': 'produccion',
            'nombre': 'Producción',
            'descripcion': 'Productos elaborados en taller',
            'icono': 'cogs',
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
            'icono': 'user-cog',
            'url': 'informes:usuarios_empleados'
        },
        {
            'id': 'productos_categoria',
            'nombre': 'Productos por Categoría',
            'descripcion': 'Distribución y rotación por categoría',
            'icono': 'layer-group',
            'url': 'informes:productos_categoria'
        }
    ]
    
    # Asignar informes según el rol
    informes_disponibles = informes_basicos
    if rol == 'admin':
        informes_disponibles.extend(informes_admin)
    
    # Manejar solicitudes AJAX para actualización de métricas
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            **metricas
        })
    
    context = {
        'informes': informes_disponibles,
        'usuario': usuario,
        'page_title': 'Dashboard',
        'system_name': 'Sistema NEXO',
        'user_iniciales': user_iniciales,
        'usuario_actual': usuario_actual,
        'nexo_user_role': nexo_user_role,
        
        # Métricas del dashboard
        **metricas
    }
    
    return render(request, 'informes/lista_informes.html', context)

@nexo_login_required
def inventario_general(request):
    """
    Vista mejorada para el informe de inventario general
    """
    try:
        # Obtener filtros del request con validación
        filtros = {}
        if request.GET.get('categoria'):
            try:
                filtros['categoria'] = int(request.GET.get('categoria'))
            except (ValueError, TypeError):
                pass
                
        if request.GET.get('ubicacion'):
            try:
                filtros['ubicacion'] = int(request.GET.get('ubicacion'))
            except (ValueError, TypeError):
                pass
                
        if request.GET.get('stock_bajo') == '1':
            filtros['stock_bajo'] = True
            
        if request.GET.get('buscar'):
            filtros['buscar'] = request.GET.get('buscar').strip()
        
        # Obtener datos del servicio
        datos = InformeService.obtener_inventario_general(filtros)
        
        # Paginación
        paginator = Paginator(datos['productos'], 25)
        page_number = request.GET.get('page')
        productos_paginados = paginator.get_page(page_number)
        
        # Datos para filtros
        try:
            categorias = Categoria.objects.filter(estadocategoria=True).order_by('nombrecategoria')
            ubicaciones = Ubicacion.objects.all().order_by('nombreubicacion')
        except Exception as e:
            logger.warning(f"Error obteniendo datos para filtros: {str(e)}")
            categorias = []
            ubicaciones = []
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'productos': productos_paginados,
            'resumen': datos['resumen'],
            'categorias': categorias,
            'ubicaciones': ubicaciones,
            'filtros_aplicados': filtros,
            'titulo_informe': 'Inventario General',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Inventario General',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador' if usuario.rol == 'admin' else 'Usuario'
        }
        
        return render(request, 'informes/inventario_general.html', context)
        
    except Exception as e:
        logger.error(f"Error en inventario_general: {str(e)}")
        messages.error(request, f'Error al generar el informe de inventario: {str(e)}')
        return redirect('informes:lista_informes')

@nexo_login_required
def ventas(request):
    """
    Vista mejorada para el informe de ventas con validación robusta
    """
    try:
        # Obtener y validar filtros
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        filtros = {}
        if request.GET.get('cliente'):
            try:
                filtros['cliente'] = int(request.GET.get('cliente'))
            except (ValueError, TypeError):
                pass
                
        if request.GET.get('vendedor'):
            try:
                filtros['vendedor'] = int(request.GET.get('vendedor'))
            except (ValueError, TypeError):
                pass
        
        # Convertir fechas con manejo de errores
        try:
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"Error en formato de fecha: {str(e)}")
            messages.warning(request, 'Formato de fecha inválido. Usando fechas por defecto.')
            fecha_inicio = fecha_fin = None
        
        # Fechas por defecto (último mes)
        if not fecha_inicio and not fecha_fin:
            fecha_fin = timezone.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30)
        
        # Obtener datos
        datos = InformeService.obtener_ventas(fecha_inicio, fecha_fin, filtros)
        
        # Paginación
        paginator = Paginator(datos['ventas'], 20)
        page_number = request.GET.get('page')
        ventas_paginadas = paginator.get_page(page_number)
        
        # Datos para filtros
        try:
            clientes = Cliente.objects.filter(estadocliente=True).select_related('idpersonacliente').order_by('idpersonacliente__primernombre')
            vendedores = Usuario.objects.filter(activo=True).order_by('nombreusuario')
        except Exception as e:
            logger.warning(f"Error obteniendo datos para filtros: {str(e)}")
            clientes = []
            vendedores = []
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'ventas': ventas_paginadas,
            'resumen': datos['resumen'],
            'clientes': clientes,
            'vendedores': vendedores,
            'filtros_aplicados': filtros,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'titulo_informe': 'Reporte de Ventas',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Reporte de Ventas',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador' if usuario.rol == 'admin' else 'Usuario'
        }
        
        return render(request, 'informes/ventas.html', context)
        
    except Exception as e:
        logger.error(f"Error en ventas: {str(e)}")
        messages.error(request, f'Error al generar el informe de ventas: {str(e)}')
        return redirect('informes:lista_informes')

@nexo_login_required
def devoluciones(request):
    """
    Vista para el informe de devoluciones con validación mejorada
    """
    try:
        # Obtener y validar filtros de fecha
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        try:
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"Error en formato de fecha: {str(e)}")
            messages.warning(request, 'Formato de fecha inválido.')
            fecha_inicio = fecha_fin = None
        
        # Obtener datos
        datos = InformeService.obtener_devoluciones(fecha_inicio, fecha_fin)
        
        # Paginación
        paginator = Paginator(datos['devoluciones'], 15)
        page_number = request.GET.get('page')
        devoluciones_paginadas = paginator.get_page(page_number)
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'devoluciones': devoluciones_paginadas,
            'detalles': datos['detalles'],
            'resumen': datos['resumen'],
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'titulo_informe': 'Reporte de Devoluciones',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Reporte de Devoluciones',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador' if usuario.rol == 'admin' else 'Usuario'
        }
        
        return render(request, 'informes/devoluciones.html', context)
        
    except Exception as e:
        logger.error(f"Error en devoluciones: {str(e)}")
        messages.error(request, f'Error al generar el informe de devoluciones: {str(e)}')
        return redirect('informes:lista_informes')

@nexo_role_required(['admin'])
def produccion(request):
    """
    Vista para el informe de producción (solo administradores)
    """
    try:
        # Obtener y validar filtros de fecha
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        try:
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"Error en formato de fecha: {str(e)}")
            messages.warning(request, 'Formato de fecha inválido. Usando fechas por defecto.')
            fecha_inicio = fecha_fin = None
        
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
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'producciones': datos['producciones'],
            'detalles': detalles_paginados,
            'resumen': datos['resumen'],
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'titulo_informe': 'Reporte de Producción',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Reporte de Producción',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador'
        }
        
        return render(request, 'informes/produccion.html', context)
        
    except Exception as e:
        logger.error(f"Error en produccion: {str(e)}")
        messages.error(request, f'Error al generar el informe de producción: {str(e)}')
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
            
        if request.GET.get('buscar'):
            filtros['buscar'] = request.GET.get('buscar').strip()
        
        # Obtener datos
        datos = InformeService.obtener_clientes(filtros)
        
        # Paginación
        paginator = Paginator(datos['clientes'], 25)
        page_number = request.GET.get('page')
        clientes_paginados = paginator.get_page(page_number)
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'clientes': clientes_paginados,
            'resumen': datos['resumen'],
            'filtros_aplicados': filtros,
            'titulo_informe': 'Reporte de Clientes',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Reporte de Clientes',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador'
        }
        
        return render(request, 'informes/clientes.html', context)
        
    except Exception as e:
        logger.error(f"Error en clientes: {str(e)}")
        messages.error(request, f'Error al generar el informe de clientes: {str(e)}')
        return redirect('informes:lista_informes')

@nexo_role_required(['admin'])
def usuarios_empleados(request):
    """
    Vista para el informe de usuarios y empleados (solo administradores)
    """
    try:
        # Obtener datos
        datos = InformeService.obtener_usuarios_empleados()
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'usuarios': datos['usuarios'],
            'empleados': datos['empleados'],
            'roles_count': datos['roles_count'],
            'resumen': datos['resumen'],
            'titulo_informe': 'Usuarios y Empleados',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Usuarios y Empleados',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador'
        }
        
        return render(request, 'informes/usuarios_empleados.html', context)
        
    except Exception as e:
        logger.error(f"Error en usuarios_empleados: {str(e)}")
        messages.error(request, f'Error al generar el informe de usuarios y empleados: {str(e)}')
        return redirect('informes:lista_informes')

@nexo_login_required
def productos_categoria(request):
    """
    Vista para el informe de productos por categoría
    """
    try:
        # Obtener datos
        datos = InformeService.obtener_productos_por_categoria()
        
        # Preparar datos del usuario para el header
        usuario = request.nexo_user
        user_iniciales = "IN"
        empleado_nombre = "Usuario"
        
        if usuario:
            if usuario.nombreusuario:
                user_iniciales = usuario.nombreusuario[:2].upper()
                empleado_nombre = usuario.nombreusuario
        
        context = {
            'categorias': datos['categorias'],
            'resumen': datos['resumen'],
            'titulo_informe': 'Productos por Categoría',
            'usuario_generador': empleado_nombre,
            'fecha_generacion': timezone.now(),
            
            # Para el header
            'page_title': 'Productos por Categoría',
            'system_name': 'Sistema NEXO',
            'user_iniciales': user_iniciales,
            'usuario_actual': usuario,
            'nexo_user_role': 'Administrador' if usuario.rol == 'admin' else 'Usuario'
        }
        
        return render(request, 'informes/productos_categoria.html', context)
        
    except Exception as e:
        logger.error(f"Error en productos_categoria: {str(e)}")
        messages.error(request, f'Error al generar el informe de productos por categoría: {str(e)}')
        return redirect('informes:lista_informes')

@nexo_login_required
def exportar_pdf(request, tipo_informe):
    """
    Vista mejorada para exportar informes a PDF con filtros preservados
    """
    try:
        exportador = ExportadorInformes()
        
        # Obtener todos los filtros aplicados (preservar estado de la vista)
        filtros = {}
        for key, value in request.GET.items():
            if key != 'page':  # Excluir parámetro de paginación
                filtros[key] = value
        
        # Generar PDF según el tipo de informe con manejo robusto de errores
        if tipo_informe == 'inventario_general':
            datos = InformeService.obtener_inventario_general(filtros)
            pdf_content = exportador.generar_pdf_inventario(datos, request.nexo_user)
            filename = f"inventario_general_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif tipo_informe == 'ventas':
            # Procesar fechas con validación
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            try:
                if fecha_inicio:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                if fecha_fin:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = fecha_fin = None
            
            # Fechas por defecto si no se especifican
            if not fecha_inicio and not fecha_fin:
                fecha_fin = timezone.now().date()
                fecha_inicio = fecha_fin - timedelta(days=30)
            
            datos = InformeService.obtener_ventas(fecha_inicio, fecha_fin, filtros)
            pdf_content = exportador.generar_pdf_ventas(datos, request.nexo_user, fecha_inicio, fecha_fin)
            filename = f"ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif tipo_informe == 'devoluciones':
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            try:
                if fecha_inicio:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                if fecha_fin:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = fecha_fin = None
            
            datos = InformeService.obtener_devoluciones(fecha_inicio, fecha_fin)
            pdf_content = exportador.generar_pdf_devoluciones(datos, request.nexo_user, fecha_inicio, fecha_fin)
            filename = f"devoluciones_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif tipo_informe == 'produccion':
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            try:
                if fecha_inicio:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                if fecha_fin:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = fecha_fin = None
            
            datos = InformeService.obtener_produccion(fecha_inicio, fecha_fin)
            pdf_content = exportador.generar_pdf_produccion(datos, request.nexo_user, fecha_inicio, fecha_fin)
            filename = f"produccion_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif tipo_informe == 'clientes':
            datos = InformeService.obtener_clientes(filtros)
            pdf_content = exportador.generar_pdf_clientes(datos, request.nexo_user)
            filename = f"clientes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif tipo_informe == 'usuarios_empleados':
            datos = InformeService.obtener_usuarios_empleados()
            pdf_content = exportador.generar_pdf_usuarios_empleados(datos, request.nexo_user)
            filename = f"usuarios_empleados_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        elif tipo_informe == 'productos_categoria':
            datos = InformeService.obtener_productos_por_categoria()
            pdf_content = exportador.generar_pdf_productos_categoria(datos, request.nexo_user)
            filename = f"productos_categoria_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
        else:
            messages.error(request, f'Tipo de informe "{tipo_informe}" no válido para exportación PDF.')
            return redirect('informes:lista_informes')
        
        # Crear respuesta HTTP con el PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_content)
        
        logger.info(f"PDF generado exitosamente: {filename} por usuario {request.nexo_user.nombreusuario}")
        return response
        
    except Exception as e:
        logger.error(f"Error en exportar_pdf para {tipo_informe}: {str(e)}")
        messages.error(request, f'Error al exportar el informe "{tipo_informe}" a PDF. Intenta nuevamente.')
        return redirect('informes:lista_informes')

@nexo_login_required
def exportar_excel(request, tipo_informe):
    """
    Vista mejorada para exportar informes a Excel con filtros preservados
    """
    try:
        exportador = ExportadorInformes()
        
        # Obtener todos los filtros aplicados (preservar estado de la vista)
        filtros = {}
        for key, value in request.GET.items():
            if key != 'page':  # Excluir parámetro de paginación
                filtros[key] = value
        
        # Generar Excel según el tipo de informe con manejo robusto de errores
        if tipo_informe == 'inventario_general':
            datos = InformeService.obtener_inventario_general(filtros)
            excel_content = exportador.generar_excel_inventario(datos)
            filename = f"inventario_general_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        elif tipo_informe == 'ventas':
            # Procesar fechas con validación
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            try:
                if fecha_inicio:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                if fecha_fin:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = fecha_fin = None
            
            # Fechas por defecto si no se especifican
            if not fecha_inicio and not fecha_fin:
                fecha_fin = timezone.now().date()
                fecha_inicio = fecha_fin - timedelta(days=30)
            
            datos = InformeService.obtener_ventas(fecha_inicio, fecha_fin, filtros)
            excel_content = exportador.generar_excel_ventas(datos)
            filename = f"ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        elif tipo_informe == 'devoluciones':
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            try:
                if fecha_inicio:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                if fecha_fin:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = fecha_fin = None
            
            datos = InformeService.obtener_devoluciones(fecha_inicio, fecha_fin)
            excel_content = exportador.generar_excel_devoluciones(datos)
            filename = f"devoluciones_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        elif tipo_informe == 'produccion':
            fecha_inicio = request.GET.get('fecha_inicio')
            fecha_fin = request.GET.get('fecha_fin')
            
            try:
                if fecha_inicio:
                    fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                if fecha_fin:
                    fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                fecha_inicio = fecha_fin = None
            
            datos = InformeService.obtener_produccion(fecha_inicio, fecha_fin)
            excel_content = exportador.generar_excel_produccion(datos)
            filename = f"produccion_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        elif tipo_informe == 'clientes':
            datos = InformeService.obtener_clientes(filtros)
            excel_content = exportador.generar_excel_clientes(datos)
            filename = f"clientes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        elif tipo_informe == 'usuarios_empleados':
            datos = InformeService.obtener_usuarios_empleados()
            excel_content = exportador.generar_excel_usuarios_empleados(datos)
            filename = f"usuarios_empleados_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        elif tipo_informe == 'productos_categoria':
            datos = InformeService.obtener_productos_por_categoria()
            excel_content = exportador.generar_excel_productos_categoria(datos)
            filename = f"productos_categoria_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        else:
            messages.error(request, f'Tipo de informe "{tipo_informe}" no válido para exportación Excel.')
            return redirect('informes:lista_informes')
        
        # Crear respuesta HTTP con el Excel
        response = HttpResponse(
            excel_content, 
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(excel_content)
        
        logger.info(f"Excel generado exitosamente: {filename} por usuario {request.nexo_user.nombreusuario}")
        return response
        
    except Exception as e:
        logger.error(f"Error en exportar_excel para {tipo_informe}: {str(e)}")
        messages.error(request, f'Error al exportar el informe "{tipo_informe}" a Excel. Intenta nuevamente.')
        return redirect('informes:lista_informes')
