from django.db.models import Sum, Count, Q, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from core_data.models import *
from decimal import Decimal
import logging

logger = logging.getLogger('nexo.informes')

class InformeService:
    """
    Servicio principal para generar datos de informes
    Centraliza toda la lógica de negocio para evitar sobrecargar las vistas
    """
    
    @staticmethod
    def obtener_inventario_general(filtros=None):
        """
        Genera datos para el informe de inventario general
        Muestra existencias actuales por producto y ubicación
        """
        try:
            queryset = Producto.objects.select_related(
                'idcategoriapro', 'idubicacionpro'
            ).filter(estado=True)
            
            # Aplicar filtros si existen
            if filtros:
                if filtros.get('categoria'):
                    queryset = queryset.filter(idcategoriapro_id=filtros['categoria'])
                if filtros.get('ubicacion'):
                    queryset = queryset.filter(idubicacionpro_id=filtros['ubicacion'])
                if filtros.get('stock_bajo'):
                    queryset = queryset.filter(
                        existenciaproducto__lte=F('existenciaminima')
                    )
            
            productos = queryset.order_by('nombreproducto')
            
            # Calcular totales
            total_productos = productos.count()
            total_existencias = productos.aggregate(
                total=Sum('existenciaproducto')
            )['total'] or 0
            
            productos_bajo_stock = productos.filter(
                existenciaproducto__lte=F('existenciaminima')
            ).count()
            
            valor_total_inventario = sum([
                (p.existenciaproducto * (p.precioproducto or 0)) 
                for p in productos
            ])
            
            return {
                'productos': productos,
                'resumen': {
                    'total_productos': total_productos,
                    'total_existencias': total_existencias,
                    'productos_bajo_stock': productos_bajo_stock,
                    'valor_total': valor_total_inventario
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_inventario_general: {str(e)}")
            raise
    
    @staticmethod
    def obtener_produccion(fecha_inicio=None, fecha_fin=None, filtros=None):
        """
        Genera datos para el informe de producción
        Detalla productos elaborados en taller, fechas y responsables
        """
        try:
            queryset = Productosproduccion.objects.select_related(
                'id_usuario', 'id_usuario__idempusuario', 
                'id_usuario__idempusuario__idpersonaemp'
            ).filter(estadoregistro=True)
            
            # Filtrar por fechas
            if fecha_inicio:
                queryset = queryset.filter(fechaentrada__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fechaentrada__lte=fecha_fin)
            
            producciones = queryset.order_by('-fechaentrada')
            
            # Obtener detalles de producción
            detalles = []
            total_productos_producidos = 0
            costo_total_produccion = Decimal('0.00')
            
            for produccion in producciones:
                detalles_prod = Detalleproduccion.objects.select_related(
                    'id_producto', 'idfabricante', 'idfabricante__idpersonaemp'
                ).filter(id_produccion=produccion)
                
                for detalle in detalles_prod:
                    total_productos_producidos += detalle.cantidad
                    costo_total_produccion += (detalle.cantidad * detalle.costo_unitario)
                    
                    detalles.append({
                        'produccion': produccion,
                        'detalle': detalle
                    })
            
            return {
                'producciones': producciones,
                'detalles': detalles,
                'resumen': {
                    'total_ordenes': producciones.count(),
                    'total_productos_producidos': total_productos_producidos,
                    'costo_total': costo_total_produccion
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_produccion: {str(e)}")
            raise
    
    @staticmethod
    def obtener_ventas(fecha_inicio=None, fecha_fin=None, filtros=None):
        """
        Genera datos para el informe de ventas
        Registra ventas realizadas, filtrables por cliente, fecha y vendedor
        """
        try:
            queryset = Venta.objects.select_related(
                'idusuarioventa', 'codcliente', 'codcliente__idpersonacliente'
            ).filter(estado='REALIZADA')
            
            # Aplicar filtros de fecha
            if fecha_inicio:
                queryset = queryset.filter(fechaventa__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fechaventa__lte=fecha_fin)
            
            # Aplicar otros filtros
            if filtros:
                if filtros.get('cliente'):
                    queryset = queryset.filter(codcliente_id=filtros['cliente'])
                if filtros.get('vendedor'):
                    queryset = queryset.filter(idusuarioventa_id=filtros['vendedor'])
            
            ventas = queryset.order_by('-fechaventa')
            
            # Calcular resumen
            total_ventas = ventas.count()
            monto_total = ventas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            promedio_venta = monto_total / total_ventas if total_ventas > 0 else Decimal('0.00')
            
            # Obtener detalles de ventas
            detalles_ventas = []
            for venta in ventas:
                detalles = Detalleventa.objects.select_related(
                    'idproventa'
                ).filter(idventa=venta)
                
                for detalle in detalles:
                    detalles_ventas.append({
                        'venta': venta,
                        'detalle': detalle
                    })
            
            return {
                'ventas': ventas,
                'detalles': detalles_ventas,
                'resumen': {
                    'total_ventas': total_ventas,
                    'monto_total': monto_total,
                    'promedio_venta': promedio_venta
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_ventas: {str(e)}")
            raise
    
    @staticmethod
    def obtener_devoluciones(fecha_inicio=None, fecha_fin=None):
        """
        Genera datos para el informe de devoluciones
        Enumera devoluciones procesadas, causas y productos implicados
        """
        try:
            queryset = Devolucion.objects.select_related(
                'idventadev', 'idventadev__codcliente', 
                'idventadev__codcliente__idpersonacliente'
            )
            
            # Filtrar por fechas
            if fecha_inicio:
                queryset = queryset.filter(fechadevolucion__gte=fecha_inicio)
            if fecha_fin:
                queryset = queryset.filter(fechadevolucion__lte=fecha_fin)
            
            devoluciones = queryset.order_by('-fechadevolucion')
            
            # Obtener detalles de devoluciones
            detalles_devoluciones = []
            total_productos_devueltos = 0
            
            for devolucion in devoluciones:
                detalles = Detalledevolucion.objects.select_related(
                    'id_producto'
                ).filter(id_devolucion=devolucion)
                
                for detalle in detalles:
                    total_productos_devueltos += detalle.cantidaddevuelta
                    detalles_devoluciones.append({
                        'devolucion': devolucion,
                        'detalle': detalle
                    })
            
            return {
                'devoluciones': devoluciones,
                'detalles': detalles_devoluciones,
                'resumen': {
                    'total_devoluciones': devoluciones.count(),
                    'total_productos_devueltos': total_productos_devueltos
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_devoluciones: {str(e)}")
            raise
    
    @staticmethod
    def obtener_clientes(filtros=None):
        """
        Genera datos para el informe de clientes
        Presenta el estado actual de los clientes del sistema
        """
        try:
            queryset = Cliente.objects.select_related(
                'idpersonacliente'
            ).filter(estadocliente=True)
            
            # Aplicar filtros si existen
            if filtros and filtros.get('activos_solo'):
                # Clientes con ventas en los últimos 6 meses
                fecha_limite = timezone.now() - timedelta(days=180)
                clientes_activos = Venta.objects.filter(
                    fechaventa__gte=fecha_limite,
                    estado='REALIZADA'
                ).values_list('codcliente', flat=True).distinct()
                queryset = queryset.filter(idcliente__in=clientes_activos)
            
            clientes = queryset.order_by('idpersonacliente__primernombre')
            
            # Calcular estadísticas por cliente
            clientes_con_stats = []
            for cliente in clientes:
                ventas_cliente = Venta.objects.filter(
                    codcliente=cliente, estado='REALIZADA'
                )
                
                total_compras = ventas_cliente.count()
                monto_total = ventas_cliente.aggregate(
                    total=Sum('total')
                )['total'] or Decimal('0.00')
                
                ultima_compra = ventas_cliente.order_by('-fechaventa').first()
                
                clientes_con_stats.append({
                    'cliente': cliente,
                    'total_compras': total_compras,
                    'monto_total': monto_total,
                    'ultima_compra': ultima_compra.fechaventa if ultima_compra else None
                })
            
            return {
                'clientes': clientes_con_stats,
                'resumen': {
                    'total_clientes': len(clientes_con_stats),
                    'clientes_activos': len([c for c in clientes_con_stats if c['ultima_compra']])
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_clientes: {str(e)}")
            raise
    
    @staticmethod
    def obtener_usuarios_empleados():
        """
        Genera datos para el informe de usuarios y empleados
        Lista roles, accesos y relación con personal activo
        """
        try:
            usuarios = Usuario.objects.select_related(
                'idempusuario', 'idempusuario__idpersonaemp'
            ).filter(activo=True).order_by('nombreusuario')
            
            empleados = Empleado.objects.select_related(
                'idpersonaemp'
            ).filter(estadoempleado=True).order_by('idpersonaemp__primernombre')
            
            # Estadísticas de roles
            roles_count = usuarios.values('rol').annotate(
                count=Count('rol')
            ).order_by('rol')
            
            return {
                'usuarios': usuarios,
                'empleados': empleados,
                'roles_count': roles_count,
                'resumen': {
                    'total_usuarios': usuarios.count(),
                    'total_empleados': empleados.count(),
                    'usuarios_activos': usuarios.filter(activo=True).count()
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_usuarios_empleados: {str(e)}")
            raise
    
    @staticmethod
    def obtener_productos_por_categoria():
        """
        Genera datos para el informe de productos por categoría
        Muestra la distribución y rotación de productos según categoría
        """
        try:
            categorias = Categoria.objects.filter(
                estadocategoria=True
            ).prefetch_related('producto_set')
            
            datos_categorias = []
            
            for categoria in categorias:
                productos = categoria.producto_set.filter(estado=True)
                
                total_productos = productos.count()
                total_existencias = productos.aggregate(
                    total=Sum('existenciaproducto')
                )['total'] or 0
                
                valor_categoria = sum([
                    (p.existenciaproducto * (p.precioproducto or 0)) 
                    for p in productos
                ])
                
                # Calcular rotación (ventas de los últimos 30 días)
                fecha_limite = timezone.now() - timedelta(days=30)
                productos_ids = productos.values_list('id_producto', flat=True)
                
                ventas_categoria = Detalleventa.objects.filter(
                    idproventa_id__in=productos_ids,
                    idventa__fechaventa__gte=fecha_limite,
                    idventa__estado='REALIZADA'
                ).aggregate(
                    total_vendido=Sum('cantidadventa')
                )['total_vendido'] or 0
                
                datos_categorias.append({
                    'categoria': categoria,
                    'productos': productos,
                    'total_productos': total_productos,
                    'total_existencias': total_existencias,
                    'valor_categoria': valor_categoria,
                    'rotacion_30_dias': ventas_categoria
                })
            
            return {
                'categorias': datos_categorias,
                'resumen': {
                    'total_categorias': len(datos_categorias),
                    'total_productos_sistema': sum([c['total_productos'] for c in datos_categorias])
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_productos_por_categoria: {str(e)}")
            raise
