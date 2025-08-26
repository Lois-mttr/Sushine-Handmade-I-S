from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging

logger = logging.getLogger('nexo.informes')

class InformeService:
    """
    Servicio corregido para generar informes usando SQL crudo según la estructura real de la base de datos
    """
    
    @staticmethod
    def obtener_metricas_dashboard():
        """
        Obtener todas las métricas necesarias para el dashboard principal usando SQL crudo
        """
        try:
            with connection.cursor() as cursor:
                hoy = timezone.now().date()
                inicio_mes = hoy.replace(day=1)
                
                # Métricas de productos
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_productos,
                        SUM(existenciaProducto) as total_existencias,
                        SUM(CASE WHEN existenciaProducto <= existenciaMinima THEN 1 ELSE 0 END) as productos_stock_bajo,
                        SUM(existenciaProducto * precioProducto) as valor_inventario
                    FROM Producto 
                    WHERE estado = 1
                """)
                productos_stats = cursor.fetchone()
                
                total_productos = productos_stats[0] or 0
                total_existencias = productos_stats[1] or 0
                productos_stock_bajo = productos_stats[2] or 0
                valor_inventario = Decimal(str(productos_stats[3] or 0))
                
                # Métricas de ventas del mes
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_ventas,
                        SUM(total) as monto_total,
                        SUM(CASE WHEN DATE(fechaVenta) = %s THEN 1 ELSE 0 END) as ventas_hoy,
                        SUM(CASE WHEN DATE(fechaVenta) = %s THEN total ELSE 0 END) as facturado_hoy
                    FROM Venta 
                    WHERE fechaVenta >= %s AND estado = 'REALIZADA'
                """, [hoy, hoy, inicio_mes])
                ventas_stats = cursor.fetchone()
                
                ventas_realizadas = ventas_stats[0] or 0
                ventas_mes_total = Decimal(str(ventas_stats[1] or 0))
                ventas_hoy = ventas_stats[2] or 0
                facturado_hoy = Decimal(str(ventas_stats[3] or 0))
                
                # Métricas de clientes
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT c.idCliente) as total_clientes,
                        COUNT(DISTINCT CASE WHEN v.fechaVenta >= %s THEN c.idCliente END) as clientes_activos
                    FROM Cliente c
                    LEFT JOIN Venta v ON c.idCliente = v.codCliente AND v.estado = 'REALIZADA'
                    WHERE c.estadoCliente = 1
                """, [inicio_mes])
                clientes_stats = cursor.fetchone()
                
                total_clientes = clientes_stats[0] or 0
                clientes_activos = clientes_stats[1] or 0
                clientes_nuevos = 0
                
                # Métricas de producción
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_producciones,
                        SUM(dp.cantidad * dp.costo_unitario) as costo_total
                    FROM ProductosProduccion pp
                    JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                    WHERE pp.fechaEntrada >= %s AND pp.EstadoRegistro = 1
                """, [inicio_mes])
                produccion_stats = cursor.fetchone()
                
                producciones_mes = produccion_stats[0] or 0
                costo_produccion = Decimal(str(produccion_stats[1] or 0))
                
                # Métricas de devoluciones
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_devoluciones,
                        SUM(dd.cantidadDevuelta * p.precioProducto) as monto_devoluciones
                    FROM Devolucion d
                    JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                    JOIN Producto p ON dd.id_producto = p.id_producto
                    WHERE d.fechaDevolucion >= %s
                """, [inicio_mes])
                devoluciones_stats = cursor.fetchone()
                
                devoluciones_mes = devoluciones_stats[0] or 0
                monto_devoluciones = Decimal(str(devoluciones_stats[1] or 0))
                
                # Métricas de usuarios
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_usuarios,
                        SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) as usuarios_activos
                    FROM Usuario
                """)
                usuarios_stats = cursor.fetchone()
                
                total_usuarios = usuarios_stats[0] or 0
                usuarios_activos = usuarios_stats[1] or 0
                
                # Métricas de categorías
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT c.idCategoria) as total_categorias,
                        COUNT(p.id_producto) as productos_categoria
                    FROM Categoria c
                    LEFT JOIN Producto p ON c.idCategoria = p.idCategoriaPro AND p.estado = 1
                    WHERE c.estadoCategoria = 1
                """)
                categorias_stats = cursor.fetchone()
                
                total_categorias = categorias_stats[0] or 0
                productos_categoria = categorias_stats[1] or 0
                
                reportes_hoy = 0
                
                # Promedio de venta
                promedio_venta = Decimal('0.00')
                if ventas_realizadas > 0:
                    promedio_venta = ventas_mes_total / ventas_realizadas
                
                return {
                    'reportes_hoy': reportes_hoy,
                    'total_productos': total_productos,
                    'productos_stock_bajo': productos_stock_bajo,
                    'total_existencias': total_existencias,
                    'valor_inventario': valor_inventario,
                    'ventas_mes_total': ventas_mes_total,
                    'ventas_realizadas': ventas_realizadas,
                    'ventas_hoy': ventas_hoy,
                    'facturado_hoy': facturado_hoy,
                    'clientes_activos': clientes_activos,
                    'total_clientes': total_clientes,
                    'clientes_nuevos': clientes_nuevos,
                    'producciones_mes': producciones_mes,
                    'costo_produccion': costo_produccion,
                    'devoluciones_mes': devoluciones_mes,
                    'monto_devoluciones': monto_devoluciones,
                    'total_usuarios': total_usuarios,
                    'usuarios_activos': usuarios_activos,
                    'total_categorias': total_categorias,
                    'productos_categoria': productos_categoria,
                    'promedio_venta': promedio_venta,
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo métricas del dashboard: {str(e)}")
            return {
                'reportes_hoy': 0,
                'total_productos': 0,
                'productos_stock_bajo': 0,
                'total_existencias': 0,
                'valor_inventario': Decimal('0.00'),
                'ventas_mes_total': Decimal('0.00'),
                'ventas_realizadas': 0,
                'ventas_hoy': 0,
                'facturado_hoy': Decimal('0.00'),
                'clientes_activos': 0,
                'total_clientes': 0,
                'clientes_nuevos': 0,
                'producciones_mes': 0,
                'costo_produccion': Decimal('0.00'),
                'devoluciones_mes': 0,
                'monto_devoluciones': Decimal('0.00'),
                'total_usuarios': 0,
                'usuarios_activos': 0,
                'total_categorias': 0,
                'productos_categoria': 0,
                'promedio_venta': Decimal('0.00'),
            }
    
    @staticmethod
    def obtener_inventario_general(filtros=None):
        """
        Obtener datos del inventario general usando SQL crudo corregido
        """
        if filtros is None:
            filtros = {}
        
        try:
            with connection.cursor() as cursor:
                # Query corregida con nombres de campos exactos
                base_query = """
                    SELECT 
                        p.id_producto,
                        p.nombreProducto,
                        p.descripcionProducto,
                        p.existenciaProducto,
                        p.precioProducto,
                        p.existenciaMinima,
                        p.imagenProductoRuta,
                        c.nombreCategoria,
                        u.nombreUbicacion,
                        (p.existenciaProducto * p.precioProducto) as valor_total
                    FROM Producto p
                    LEFT JOIN Categoria c ON p.idCategoriaPro = c.idCategoria
                    LEFT JOIN Ubicacion u ON p.idUbicacionPro = u.id_ubicacion
                    WHERE p.estado = 1
                """
                
                params = []
                
                # Aplicar filtros
                if filtros.get('categoria'):
                    base_query += " AND p.idCategoriaPro = %s"
                    params.append(filtros['categoria'])
                
                if filtros.get('ubicacion'):
                    base_query += " AND p.idUbicacionPro = %s"
                    params.append(filtros['ubicacion'])
                
                if filtros.get('stock_bajo'):
                    base_query += " AND p.existenciaProducto <= p.existenciaMinima"
                
                if filtros.get('buscar'):
                    base_query += " AND (p.nombreProducto LIKE %s OR p.descripcionProducto LIKE %s)"
                    buscar_param = f"%{filtros['buscar']}%"
                    params.extend([buscar_param, buscar_param])
                
                base_query += " ORDER BY p.nombreProducto"
                
                cursor.execute(base_query, params)
                productos_raw = cursor.fetchall()
                
                # Convertir a objetos similares a los del ORM
                productos = []
                for row in productos_raw:
                    producto = type('Producto', (), {
                        'id_producto': row[0],
                        'nombreproducto': row[1],
                        'descripcionproducto': row[2] or '',
                        'existenciaproducto': row[3] or 0,
                        'precioproducto': Decimal(str(row[4] or 0)),
                        'existenciaminima': row[5] or 5,
                        'imagenproductoruta': row[6],
                        'categoria_nombre': row[7] or 'Sin categoría',
                        'ubicacion_nombre': row[8] or 'Sin ubicación',
                        'valor_total': Decimal(str(row[9] or 0)),
                        'necesita_reposicion': (row[3] or 0) <= (row[5] or 5),
                        # Objetos mock para compatibilidad con templates
                        'idcategoriapro': type('Categoria', (), {
                            'nombrecategoria': row[7] or 'Sin categoría'
                        })() if row[7] else None,
                        'idubicacionpro': type('Ubicacion', (), {
                            'nombreubicacion': row[8] or 'Sin ubicación'
                        })()
                    })()
                    productos.append(producto)
                
                # Calcular resumen
                if productos:
                    total_productos = len(productos)
                    total_existencias = sum(p.existenciaproducto for p in productos)
                    productos_bajo_stock = sum(1 for p in productos if p.necesita_reposicion)
                    valor_total = sum(p.valor_total for p in productos)
                    porcentaje_stock_bajo = round((productos_bajo_stock / total_productos * 100) if total_productos > 0 else 0, 2)
                else:
                    total_productos = total_existencias = productos_bajo_stock = 0
                    valor_total = Decimal('0.00')
                    porcentaje_stock_bajo = 0
                
                resumen = {
                    'total_productos': total_productos,
                    'total_existencias': total_existencias,
                    'productos_bajo_stock': productos_bajo_stock,
                    'valor_total': valor_total,
                    'porcentaje_stock_bajo': porcentaje_stock_bajo
                }
                
                return {
                    'productos': productos,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_inventario_general: {str(e)}")
            return {
                'productos': [],
                'resumen': {
                    'total_productos': 0,
                    'total_existencias': 0,
                    'productos_bajo_stock': 0,
                    'valor_total': Decimal('0.00'),
                    'porcentaje_stock_bajo': 0
                }
            }
    
    @staticmethod
    def obtener_ventas(fecha_inicio=None, fecha_fin=None, filtros=None):
        """
        Obtener datos de ventas usando SQL crudo corregido
        """
        if filtros is None:
            filtros = {}
        
        try:
            with connection.cursor() as cursor:
                # Query corregida
                base_query = """
                    SELECT 
                        v.id_venta,
                        v.fechaVenta,
                        v.total,
                        v.estado,
                        CONCAT(COALESCE(p.primerNombre, ''), ' ', 
                               COALESCE(p.segundoNombre, ''), ' ', 
                               COALESCE(p.primerApellido, ''), ' ', 
                               COALESCE(p.segundoApellido, '')) as cliente_nombre,
                        p.cedula as cliente_cedula,
                        c.correo as cliente_correo,
                        u.nombreUsuario as vendedor_nombre,
                        CONCAT(COALESCE(pe.primerNombre, ''), ' ', 
                               COALESCE(pe.primerApellido, '')) as empleado_nombre
                    FROM Venta v
                    LEFT JOIN Cliente c ON v.codCliente = c.idCliente
                    LEFT JOIN Persona p ON c.idPersonaCliente = p.cedula
                    LEFT JOIN Usuario u ON v.idUsuarioVenta = u.idUsuario
                    LEFT JOIN Empleado e ON u.idEmpUsuario = e.idEmpleado
                    LEFT JOIN Persona pe ON e.idPersonaEmp = pe.cedula
                    WHERE v.estado = 'REALIZADA'
                """
                
                params = []
                
                # Aplicar filtros de fecha
                if fecha_inicio:
                    base_query += " AND DATE(v.fechaVenta) >= %s"
                    params.append(fecha_inicio)
                if fecha_fin:
                    base_query += " AND DATE(v.fechaVenta) <= %s"
                    params.append(fecha_fin)
                
                # Aplicar otros filtros
                if filtros.get('cliente'):
                    base_query += " AND v.codCliente = %s"
                    params.append(filtros['cliente'])
                
                if filtros.get('vendedor'):
                    base_query += " AND v.idUsuarioVenta = %s"
                    params.append(filtros['vendedor'])
                
                if filtros.get('monto_minimo'):
                    base_query += " AND v.total >= %s"
                    params.append(filtros['monto_minimo'])
                
                if filtros.get('monto_maximo'):
                    base_query += " AND v.total <= %s"
                    params.append(filtros['monto_maximo'])
                
                base_query += " ORDER BY v.fechaVenta DESC"
                
                cursor.execute(base_query, params)
                ventas_raw = cursor.fetchall()
                
                # Convertir a objetos
                ventas = []
                for row in ventas_raw:
                    venta = type('Venta', (), {
                        'id_venta': row[0],
                        'fechaventa': row[1],
                        'total': Decimal(str(row[2] or 0)),
                        'estado': row[3],
                        'cliente_nombre': row[4].strip() if row[4] else 'Cliente no especificado',
                        'vendedor_nombre': row[7] or 'No especificado',
                        'empleado_nombre': row[8] or row[7] or 'No especificado',
                        # Objetos mock para compatibilidad
                        'codcliente': type('Cliente', (), {
                            'idpersonacliente': type('Persona', (), {
                                'nombre_completo': row[4].strip() if row[4] else 'Cliente no especificado',
                                'primernombre': row[4].split()[0] if row[4] and row[4].strip() else '',
                                'primerapellido': row[4].split()[-1] if row[4] and len(row[4].split()) > 1 else ''
                            })() if row[4] else None,
                            'correo': row[6]
                        })() if row[4] else None,
                        'idusuarioventa': type('Usuario', (), {
                            'nombreusuario': row[7] or 'No especificado',
                            'empleado_nombre': row[8] or row[7] or 'No especificado',
                            'rol': 'vendedor'
                        })() if row[7] else None
                    })()
                    ventas.append(venta)
                
                # Calcular resumen
                if ventas:
                    total_ventas = len(ventas)
                    monto_total = sum(v.total for v in ventas)
                    promedio_venta = monto_total / total_ventas if total_ventas > 0 else Decimal('0.00')
                    
                    montos = [v.total for v in ventas]
                    venta_maxima = max(montos) if montos else Decimal('0.00')
                    venta_minima = min(montos) if montos else Decimal('0.00')
                else:
                    total_ventas = 0
                    monto_total = promedio_venta = venta_maxima = venta_minima = Decimal('0.00')
                
                # Formatear período
                periodo = "Sin filtro de fechas"
                if fecha_inicio and fecha_fin:
                    periodo = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
                elif fecha_inicio:
                    periodo = f"Desde {fecha_inicio.strftime('%d/%m/%Y')}"
                elif fecha_fin:
                    periodo = f"Hasta {fecha_fin.strftime('%d/%m/%Y')}"
                
                resumen = {
                    'total_ventas': total_ventas,
                    'monto_total': monto_total,
                    'promedio_venta': promedio_venta,
                    'venta_maxima': venta_maxima,
                    'venta_minima': venta_minima,
                    'periodo': periodo
                }
                
                return {
                    'ventas': ventas,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_ventas: {str(e)}")
            return {
                'ventas': [],
                'resumen': {
                    'total_ventas': 0,
                    'monto_total': Decimal('0.00'),
                    'promedio_venta': Decimal('0.00'),
                    'venta_maxima': Decimal('0.00'),
                    'venta_minima': Decimal('0.00'),
                    'periodo': 'Error en consulta'
                }
            }
    
    @staticmethod
    def obtener_devoluciones(fecha_inicio=None, fecha_fin=None):
        """
        Obtener datos de devoluciones usando SQL crudo corregido
        """
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        d.idDevolucion,
                        d.fechaDevolucion,
                        d.motivo,
                        d.idVentaDev,
                        p.nombreProducto,
                        p.id_producto,
                        dd.cantidadDevuelta,
                        p.precioProducto,
                        CONCAT(COALESCE(pe.primerNombre, ''), ' ', 
                               COALESCE(pe.segundoNombre, ''), ' ', 
                               COALESCE(pe.primerApellido, ''), ' ', 
                               COALESCE(pe.segundoApellido, '')) as cliente_nombre
                    FROM Devolucion d
                    JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                    JOIN Producto p ON dd.id_producto = p.id_producto
                    LEFT JOIN Venta v ON d.idVentaDev = v.id_venta
                    LEFT JOIN Cliente c ON v.codCliente = c.idCliente
                    LEFT JOIN Persona pe ON c.idPersonaCliente = pe.cedula
                    WHERE 1=1
                """
                
                params = []
                
                if fecha_inicio:
                    base_query += " AND d.fechaDevolucion >= %s"
                    params.append(fecha_inicio)
                if fecha_fin:
                    base_query += " AND d.fechaDevolucion <= %s"
                    params.append(fecha_fin)
                
                base_query += " ORDER BY d.fechaDevolucion DESC"
                
                cursor.execute(base_query, params)
                devoluciones_raw = cursor.fetchall()
                
                # Agrupar por devolución
                devoluciones_dict = {}
                detalles = []
                
                for row in devoluciones_raw:
                    dev_id = row[0]
                    if dev_id not in devoluciones_dict:
                        devoluciones_dict[dev_id] = {
                            'iddevolucion': row[0],
                            'fechadevolucion': row[1],
                            'motivo': row[2] or 'No especificado',
                            'id_venta_dev': row[3],
                            'cliente_nombre': row[8].strip() if row[8] else 'No especificado',
                            'productos': []
                        }
                    
                    # Agregar producto a la devolución
                    producto_info = {
                        'nombre': row[4],
                        'id_producto': row[5],
                        'cantidad': row[6] or 0,
                        'precio': Decimal(str(row[7] or 0)),
                        'monto_devuelto': Decimal(str(row[6] or 0)) * Decimal(str(row[7] or 0))
                    }
                    devoluciones_dict[dev_id]['productos'].append(producto_info)
                
                # Convertir a objetos
                devoluciones = []
                for dev_data in devoluciones_dict.values():
                    devolucion = type('Devolucion', (), {
                        'iddevolucion': dev_data['iddevolucion'],
                        'fechadevolucion': dev_data['fechadevolucion'],
                        'motivo': dev_data['motivo'],
                        'productos_devueltos': dev_data['productos'],
                        'monto_total_devuelto': sum(p['monto_devuelto'] for p in dev_data['productos']),
                        # Objeto mock para compatibilidad
                        'idventadev': type('Venta', (), {
                            'id_venta': dev_data['id_venta_dev'],
                            'codcliente': type('Cliente', (), {
                                'idpersonacliente': type('Persona', (), {
                                    'nombre_completo': dev_data['cliente_nombre']
                                })() if dev_data['cliente_nombre'] != 'No especificado' else None
                            })() if dev_data['cliente_nombre'] != 'No especificado' else None
                        })()
                    })()
                    devoluciones.append(devolucion)
                
                # Calcular resumen
                if devoluciones:
                    total_devoluciones = len(devoluciones)
                    monto_devuelto = sum(d.monto_total_devuelto for d in devoluciones)
                    total_productos_devueltos = sum(len(d.productos_devueltos) for d in devoluciones)
                    
                    # Agrupar por motivo
                    motivos = {}
                    for devolucion in devoluciones:
                        motivo = devolucion.motivo
                        motivos[motivo] = motivos.get(motivo, 0) + 1
                else:
                    total_devoluciones = 0
                    monto_devuelto = Decimal('0.00')
                    total_productos_devueltos = 0
                    motivos = {}
                
                resumen = {
                    'total_devoluciones': total_devoluciones,
                    'monto_devuelto': monto_devuelto,
                    'total_productos_devueltos': total_productos_devueltos,
                    'motivos_principales': motivos,
                    'productos_mas_devueltos': {}
                }
                
                return {
                    'devoluciones': devoluciones,
                    'detalles': detalles,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_devoluciones: {str(e)}")
            return {
                'devoluciones': [],
                'detalles': [],
                'resumen': {
                    'total_devoluciones': 0,
                    'monto_devuelto': Decimal('0.00'),
                    'total_productos_devueltos': 0,
                    'motivos_principales': {},
                    'productos_mas_devueltos': {}
                }
            }
    
    @staticmethod
    def obtener_produccion(fecha_inicio=None, fecha_fin=None):
        """
        Obtener datos de producción usando SQL crudo corregido
        """
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        pp.idProduccion,
                        pp.fechaEntrada,
                        pp.observacion,
                        pp.EstadoRegistro,
                        p.nombreProducto,
                        p.id_producto,
                        dp.cantidad,
                        dp.costo_unitario,
                        CONCAT(COALESCE(pe.primerNombre, ''), ' ', 
                               COALESCE(pe.primerApellido, '')) as fabricante_nombre,
                        u.nombreUsuario as usuario_nombre
                    FROM ProductosProduccion pp
                    JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                    JOIN Producto p ON dp.id_producto = p.id_producto
                    LEFT JOIN Empleado e ON dp.idFabricante = e.idEmpleado
                    LEFT JOIN Persona pe ON e.idPersonaEmp = pe.cedula
                    LEFT JOIN Usuario u ON pp.id_usuario = u.idUsuario
                    WHERE pp.EstadoRegistro = 1
                """
                
                params = []
                
                if fecha_inicio:
                    base_query += " AND pp.fechaEntrada >= %s"
                    params.append(fecha_inicio)
                if fecha_fin:
                    base_query += " AND pp.fechaEntrada <= %s"
                    params.append(fecha_fin)
                
                base_query += " ORDER BY pp.fechaEntrada DESC"
                
                cursor.execute(base_query, params)
                producciones_raw = cursor.fetchall()
                
                # Convertir a objetos
                producciones = []
                for row in producciones_raw:
                    produccion = type('Produccion', (), {
                        'idproduccion': row[0],
                        'fechaentrada': row[1],
                        'observacion': row[2] or '',
                        'estadoregistro': bool(row[3]),
                        'producto_nombre': row[4],
                        'producto_id': row[5],
                        'cantidadproducida': row[6] or 0,
                        'costo': Decimal(str(row[7] or 0)),
                        'fabricante_nombre': row[8] or 'No especificado',
                        'usuario_nombre': row[9] or 'No especificado',
                        # Objeto mock para compatibilidad
                        'idproducto': type('Producto', (), {
                            'nombreproducto': row[4],
                            'id_producto': row[5]
                        })()
                    })()
                    producciones.append(produccion)
                
                # Calcular resumen
                if producciones:
                    total_producciones = len(producciones)
                    cantidad_total = sum(p.cantidadproducida for p in producciones)
                    costo_total = sum(p.costo * p.cantidadproducida for p in producciones)
                    promedio_diario = cantidad_total / 30 if cantidad_total > 0 else 0
                else:
                    total_producciones = cantidad_total = promedio_diario = 0
                    costo_total = Decimal('0.00')
                
                resumen = {
                    'total_producciones': total_producciones,
                    'cantidad_total': cantidad_total,
                    'costo_total': costo_total,
                    'promedio_diario': promedio_diario
                }
                
                return {
                    'producciones': producciones,
                    'detalles': producciones,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_produccion: {str(e)}")
            return {
                'producciones': [],
                'detalles': [],
                'resumen': {
                    'total_producciones': 0,
                    'cantidad_total': 0,
                    'costo_total': Decimal('0.00'),
                    'promedio_diario': 0
                }
            }
    
    @staticmethod
    def obtener_clientes(filtros=None):
        """
        Obtener datos de clientes usando SQL crudo corregido
        """
        if filtros is None:
            filtros = {}
        
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        c.idCliente,
                        c.estadoCliente,
                        CONCAT(COALESCE(p.primerNombre, ''), ' ', 
                               COALESCE(p.segundoNombre, ''), ' ', 
                               COALESCE(p.primerApellido, ''), ' ', 
                               COALESCE(p.segundoApellido, '')) as nombre_completo,
                        p.cedula,
                        p.direccion,
                        COUNT(v.id_venta) as total_compras,
                        COALESCE(SUM(v.total), 0) as monto_total,
                        MAX(v.fechaVenta) as ultima_compra
                    FROM Cliente c
                    LEFT JOIN Persona p ON c.idPersonaCliente = p.cedula
                    LEFT JOIN Venta v ON c.idCliente = v.codCliente AND v.estado = 'REALIZADA'
                    WHERE 1=1
                """
                
                params = []
                
                if filtros.get('activos_solo'):
                    base_query += " AND c.estadoCliente = 1"
                
                if filtros.get('buscar'):
                    base_query += """ AND (
                        p.primerNombre LIKE %s OR 
                        p.primerApellido LIKE %s OR 
                        p.cedula LIKE %s OR 
                        c.correo LIKE %s
                    )"""
                    buscar_param = f"%{filtros['buscar']}%"
                    params.extend([buscar_param, buscar_param, buscar_param, buscar_param])
                
                base_query += " GROUP BY c.idCliente, c.correo, c.estadoCliente, p.cedula, p.direccion, nombre_completo"
                base_query += " ORDER BY nombre_completo"
                
                cursor.execute(base_query, params)
                clientes_raw = cursor.fetchall()
                
                # Convertir a objetos
                clientes = []
                for row in clientes_raw:
                    cliente_data = {
                        'cliente': type('Cliente', (), {
                            'idcliente': row[0],
                            'id_cliente': row[0],
                            'correo': row[1] or '',
                            'estadocliente': bool(row[2]),
                            'cedula': row[4] or '',
                            'direccion': row[5] or '',
                            # Objeto mock para compatibilidad
                            'idpersonacliente': type('Persona', (), {
                                'nombre_completo': row[3].strip() if row[3] else 'No especificado',
                                'primernombre': row[3].split()[0] if row[3] and row[3].strip() else '',
                                'primerapellido': row[3].split()[-1] if row[3] and len(row[3].split()) > 1 else '',
                                'cedula': row[4] or '',
                                'direccion': row[5] or ''
                            })() if row[3] else None
                        })(),
                        'total_compras': row[6] or 0,
                        'monto_total': Decimal(str(row[7] or 0)),
                        'ultima_compra': row[8]
                    }
                    clientes.append(cliente_data)
                
                # Calcular resumen
                if clientes:
                    total_clientes = len(clientes)
                    clientes_activos = sum(1 for c in clientes if c['cliente'].estadocliente)
                    clientes_inactivos = total_clientes - clientes_activos
                    porcentaje_activos = round((clientes_activos / total_clientes * 100) if total_clientes > 0 else 0, 2)
                else:
                    total_clientes = clientes_activos = clientes_inactivos = 0
                    porcentaje_activos = 0
                
                resumen = {
                    'total_clientes': total_clientes,
                    'clientes_activos': clientes_activos,
                    'clientes_inactivos': clientes_inactivos,
                    'porcentaje_activos': porcentaje_activos
                }
                
                return {
                    'clientes': clientes,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_clientes: {str(e)}")
            return {
                'clientes': [],
                'resumen': {
                    'total_clientes': 0,
                    'clientes_activos': 0,
                    'clientes_inactivos': 0,
                    'porcentaje_activos': 0
                }
            }
    
    @staticmethod
    def obtener_usuarios_empleados():
        """
        Obtener datos de usuarios y empleados usando SQL crudo corregido
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        u.idUsuario,
                        u.nombreUsuario,
                        u.rol,
                        u.activo,
                        u.correo as usuario_correo,
                        u.ultimo_login,
                        CONCAT(COALESCE(p.primerNombre, ''), ' ', 
                               COALESCE(p.primerApellido, '')) as empleado_nombre,
                        e.rolEmpleado,
                        e.salario,
                        e.fechaContratacion
                    FROM Usuario u
                    LEFT JOIN Empleado e ON u.idEmpUsuario = e.idEmpleado
                    LEFT JOIN Persona p ON e.idPersonaEmp = p.cedula
                    ORDER BY u.nombreUsuario
                """)
                usuarios_raw = cursor.fetchall()
                
                # Convertir a objetos
                usuarios = []
                for row in usuarios_raw:
                    usuario = type('Usuario', (), {
                        'id': row[0],
                        'idusuario': row[0],
                        'nombreusuario': row[1],
                        'rol': row[2] or 'usuario',
                        'activo': bool(row[3]),
                        'correo': row[4] or '',
                        'ultimo_login': row[5],
                        'last_login': row[5],
                        'empleado_nombre': row[6].strip() if row[6] else 'No especificado',
                        'rol_empleado': row[7] or '',
                        'salario': row[8] or 0,
                        'fecha_contratacion': row[9]
                    })()
                    usuarios.append(usuario)
                
                # Calcular resumen
                if usuarios:
                    total_usuarios = len(usuarios)
                    usuarios_activos = sum(1 for u in usuarios if u.activo)
                    usuarios_inactivos = total_usuarios - usuarios_activos
                    
                    # Contar por roles
                    roles_count = {}
                    for usuario in usuarios:
                        rol = usuario.rol or 'sin_rol'
                        roles_count[rol] = roles_count.get(rol, 0) + 1
                else:
                    total_usuarios = usuarios_activos = usuarios_inactivos = 0
                    roles_count = {}
                
                resumen = {
                    'total_usuarios': total_usuarios,
                    'usuarios_activos': usuarios_activos,
                    'usuarios_inactivos': usuarios_inactivos,
                    'roles_count': roles_count
                }
                
                return {
                    'usuarios': usuarios,
                    'empleados': usuarios,
                    'roles_count': roles_count,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_usuarios_empleados: {str(e)}")
            return {
                'usuarios': [],
                'empleados': [],
                'roles_count': {},
                'resumen': {
                    'total_usuarios': 0,
                    'usuarios_activos': 0,
                    'usuarios_inactivos': 0,
                    'roles_count': {}
                }
            }
    
    @staticmethod
    def obtener_productos_por_categoria():
        """
        Obtener productos agrupados por categoría usando SQL crudo corregido
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        c.idCategoria,
                        c.nombreCategoria,
                        c.descripcionCategoria,
                        COUNT(p.id_producto) as cantidad_productos,
                        SUM(p.existenciaProducto * p.precioProducto) as valor_total
                    FROM Categoria c
                    LEFT JOIN Producto p ON c.idCategoria = p.idCategoriaPro AND p.estado = 1
                    WHERE c.estadoCategoria = 1
                    GROUP BY c.idCategoria, c.nombreCategoria, c.descripcionCategoria
                    ORDER BY cantidad_productos DESC
                """)
                categorias_raw = cursor.fetchall()
                
                # Convertir a objetos y calcular totales
                categorias_data = []
                total_productos = 0
                
                for row in categorias_raw:
                    cantidad = row[3] or 0
                    valor_total = Decimal(str(row[4] or 0))
                    
                    categoria_data = {
                        'categoria': type('Categoria', (), {
                            'idcategoria': row[0],
                            'nombrecategoria': row[1],
                            'descripcioncategoria': row[2] or ''
                        })(),
                        'cantidad_productos': cantidad,
                        'valor_total': valor_total,
                        'productos': []
                    }
                    
                    categorias_data.append(categoria_data)
                    total_productos += cantidad
                
                # Calcular porcentajes
                for cat_data in categorias_data:
                    cat_data['porcentaje'] = round(
                        (cat_data['cantidad_productos'] / total_productos * 100) 
                        if total_productos > 0 else 0, 2
                    )
                
                # Encontrar categoría con más productos
                categoria_mayor = 'N/A'
                if categorias_data:
                    cat_mayor = max(categorias_data, key=lambda x: x['cantidad_productos'])
                    categoria_mayor = cat_mayor['categoria'].nombrecategoria
                
                valor_total_inventario = sum(cat['valor_total'] for cat in categorias_data)
                
                resumen = {
                    'total_categorias': len(categorias_data),
                    'total_productos': total_productos,
                    'categoria_mayor': categoria_mayor,
                    'valor_total_inventario': valor_total_inventario
                }
                
                return {
                    'categorias': categorias_data,
                    'resumen': resumen
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_productos_por_categoria: {str(e)}")
            return {
                'categorias': [],
                'resumen': {
                    'total_categorias': 0,
                    'total_productos': 0,
                    'categoria_mayor': 'N/A',
                    'valor_total_inventario': Decimal('0.00')
                }
            }
