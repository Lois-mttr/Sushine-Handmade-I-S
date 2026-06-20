from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging

logger = logging.getLogger('nexo.informes')

class InformeService:
    """
    Servicio final optimizado para reportes.
    Corrige coincidencia de totales en Producción y restaura lectura de idVenta.
    """
    
    @staticmethod
    def obtener_metricas_dashboard():
        metricas = {
            'reportes_hoy': 0, 'total_productos': 0, 'productos_stock_bajo': 0, 'total_existencias': 0,
            'valor_inventario': Decimal('0.00'), 'ventas_mes_total': Decimal('0.00'), 'ventas_realizadas': 0,
            'ventas_hoy': 0, 'facturado_hoy': Decimal('0.00'), 'clientes_activos': 0, 'total_clientes': 0,
            'clientes_nuevos': 0, 'producciones_mes': 0, 'costo_produccion': Decimal('0.00'),
            'devoluciones_mes': 0, 'monto_devoluciones': Decimal('0.00'), 'total_usuarios': 0,
            'usuarios_activos': 0, 'total_categorias': 0, 'productos_categoria': 0, 'promedio_venta': Decimal('0.00'),
        }
        
        hoy = timezone.now().date()
        hoy_str = hoy.strftime('%Y-%m-%d')
        inicio_mes = hoy.replace(day=1)
        
        with connection.cursor() as cursor:
            # 1. Métricas de productos
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*), 
                        SUM(existenciaProducto),
                        SUM(CASE WHEN existenciaProducto <= existenciaMinima THEN 1 ELSE 0 END),
                        SUM(existenciaProducto * precioProducto)
                    FROM Producto 
                    WHERE estado = 1
                """)
                row = cursor.fetchone()
                if row and row[0]:
                    metricas['total_productos'] = row[0] or 0
                    metricas['total_existencias'] = row[1] or 0
                    metricas['productos_stock_bajo'] = row[2] or 0
                    metricas['valor_inventario'] = Decimal(str(row[3] or 0))
            except Exception as e:
                logger.error(f"Error métricas Productos: {e}")

            # 2. Métricas de Ventas (Solucionado el fallo del formato de fecha)
            try:
                cursor.execute("""
                    SELECT 
                        COUNT(*), 
                        COALESCE(SUM(total), 0),
                        COALESCE(SUM(CASE WHEN fechaVenta >= %s THEN 1 ELSE 0 END), 0),
                        COALESCE(SUM(CASE WHEN fechaVenta >= %s THEN total ELSE 0 END), 0)
                    FROM Venta 
                    WHERE estado = 'REALIZADA'
                """, [hoy_str, hoy_str])
                row = cursor.fetchone()
                if row and row[0]:
                    metricas['ventas_realizadas'] = row[0] or 0
                    metricas['ventas_mes_total'] = Decimal(str(row[1] or 0))
                    metricas['ventas_hoy'] = row[2] or 0
                    metricas['facturado_hoy'] = Decimal(str(row[3] or 0))
                    
                    if metricas['ventas_realizadas'] > 0:
                        metricas['promedio_venta'] = metricas['ventas_mes_total'] / metricas['ventas_realizadas']
            except Exception as e:
                logger.error(f"Error métricas Ventas: {e}")

            # 3. Métricas de Clientes
            try:
                cursor.execute("SELECT COUNT(*) FROM Cliente WHERE estadoCliente = 1")
                metricas['total_clientes'] = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(DISTINCT codCliente) FROM Venta WHERE estado = 'REALIZADA'")
                metricas['clientes_activos'] = cursor.fetchone()[0] or 0
            except Exception as e:
                logger.error(f"Error métricas Clientes: {e}")

            # 4. Métricas de Producción (Se iguala COUNT(*) para que cuadre exacto con el detalle de la tabla)
            try:
                cursor.execute("""
                    SELECT COUNT(*), COALESCE(SUM(dp.cantidad * dp.costo_unitario), 0)
                    FROM ProductosProduccion pp
                    JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                    WHERE pp.EstadoRegistro = 1
                """)
                row = cursor.fetchone()
                if row and row[0]:
                    metricas['producciones_mes'] = row[0] or 0
                    metricas['costo_produccion'] = Decimal(str(row[1] or 0))
            except Exception as e:
                logger.error(f"Error métricas Producción: {e}")

            # 5. Métricas de Devoluciones
            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT d.idDevolucion), COALESCE(SUM(dd.cantidadDevuelta * p.precioProducto), 0)
                    FROM Devolucion d
                    JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                    JOIN Producto p ON dd.id_producto = p.id_producto
                """)
                row = cursor.fetchone()
                if row and row[0]:
                    metricas['devoluciones_mes'] = row[0] or 0
                    metricas['monto_devoluciones'] = Decimal(str(row[1] or 0))
            except Exception as e:
                logger.error(f"Error métricas Devoluciones: {e}")

            # 6. Métricas de Usuarios
            try:
                cursor.execute("SELECT COUNT(*), SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) FROM Usuario")
                row = cursor.fetchone()
                if row and row[0]:
                    metricas['total_usuarios'] = row[0] or 0
                    metricas['usuarios_activos'] = row[1] or 0
            except Exception as e:
                logger.error(f"Error métricas Usuarios: {e}")

            # 7. Métricas de Categorías
            try:
                cursor.execute("SELECT COUNT(*) FROM Categoria WHERE estadoCategoria = 1")
                metricas['total_categorias'] = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM Producto WHERE estado = 1 AND idCategoriaPro IS NOT NULL")
                metricas['productos_categoria'] = cursor.fetchone()[0] or 0
            except Exception as e:
                logger.error(f"Error métricas Categorías: {e}")

        return metricas

    @staticmethod
    def obtener_inventario_general(filtros=None):
        if filtros is None: filtros = {}
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        p.id_producto, p.nombreProducto, p.descripcionProducto, p.existenciaProducto, p.precioProducto,
                        p.existenciaMinima, p.imagenProductoRuta, c.nombreCategoria, u.nombreUbicacion,
                        (p.existenciaProducto * p.precioProducto) as valor_total
                    FROM Producto p
                    LEFT JOIN Categoria c ON p.idCategoriaPro = c.idCategoria
                    LEFT JOIN Ubicacion u ON p.idUbicacionPro = u.id_ubicacion
                    WHERE p.estado = 1
                """
                params = []
                
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
                        'idcategoriapro': type('Categoria', (), {'nombrecategoria': row[7] or 'Sin categoría'})() if row[7] else None,
                        'idubicacionpro': type('Ubicacion', (), {'nombreubicacion': row[8] or 'Sin ubicación'})()
                    })()
                    productos.append(producto)
                
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
                    'total_productos': total_productos, 'total_existencias': total_existencias,
                    'productos_bajo_stock': productos_bajo_stock, 'valor_total': valor_total,
                    'porcentaje_stock_bajo': porcentaje_stock_bajo
                }
                return {'productos': productos, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_inventario_general: {str(e)}")
            return {'productos': [], 'resumen': {'total_productos': 0, 'total_existencias': 0, 'productos_bajo_stock': 0, 'valor_total': Decimal('0.00'), 'porcentaje_stock_bajo': 0}}

    @staticmethod
    def obtener_ventas(fecha_inicio=None, fecha_fin=None, filtros=None):
        """
        Consulta de ventas ajustada para extraer idVenta correctamente y no dar error de columna.
        """
        if filtros is None: filtros = {}
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        v.idVenta, v.fechaVenta, v.total, v.estado,
                        p.primerNombre, p.primerApellido, p.cedula, c.correo,
                        u.nombreUsuario, pe.primerNombre as emp_nombre, pe.primerApellido as emp_apellido
                    FROM Venta v
                    LEFT JOIN Cliente c ON v.codCliente = c.idCliente
                    LEFT JOIN Persona p ON c.idPersonaCliente = p.cedula
                    LEFT JOIN Usuario u ON v.idUsuarioVenta = u.idUsuario
                    LEFT JOIN Empleado e ON u.idEmpUsuario = e.idEmpleado
                    LEFT JOIN Persona pe ON e.idPersonaEmp = pe.cedula
                    WHERE 1=1
                """
                params = []
                
                if filtros.get('estado') and filtros['estado'] != 'TODOS':
                    base_query += " AND v.estado = %s"
                    params.append(filtros['estado'])
                elif not filtros.get('estado'):
                    base_query += " AND v.estado = 'REALIZADA'"
                
                if fecha_inicio:
                    base_query += " AND DATE(v.fechaVenta) >= %s"
                    params.append(fecha_inicio)
                if fecha_fin:
                    base_query += " AND DATE(v.fechaVenta) <= %s"
                    params.append(fecha_fin)
                
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
                
                ventas = []
                for row in ventas_raw:
                    c_nombre = f"{row[4] or ''} {row[5] or ''}".strip()
                    e_nombre = f"{row[9] or ''} {row[10] or ''}".strip()
                    
                    venta = type('Venta', (), {
                        'id_venta': row[0],
                        'idVenta': row[0],
                        'fechaventa': row[1],
                        'total': Decimal(str(row[2] or 0)),
                        'estado': row[3],
                        'cliente_nombre': c_nombre if c_nombre else 'No especificado',
                        'vendedor_nombre': row[8] or 'No especificado',
                        'empleado_nombre': e_nombre if e_nombre else (row[8] or 'No especificado'),
                        'codcliente': type('Cliente', (), {
                            'idpersonacliente': type('Persona', (), {
                                'nombre_completo': c_nombre if c_nombre else 'No especificado',
                            })() if c_nombre else None,
                            'correo': row[7]
                        })() if row[6] else None,
                        'idusuarioventa': type('Usuario', (), {
                            'nombreusuario': row[8] or 'No especificado',
                        })() if row[8] else None
                    })()
                    ventas.append(venta)
                
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
                
                periodo = "Historial Completo"
                if fecha_inicio and fecha_fin:
                    periodo = f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
                elif fecha_inicio:
                    periodo = f"Desde {fecha_inicio.strftime('%d/%m/%Y')}"
                elif fecha_fin:
                    periodo = f"Hasta {fecha_fin.strftime('%d/%m/%Y')}"
                
                resumen = {
                    'total_ventas': total_ventas, 'monto_total': monto_total, 'promedio_venta': promedio_venta,
                    'venta_maxima': venta_maxima, 'venta_minima': venta_minima, 'periodo': periodo
                }
                return {'ventas': ventas, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_ventas: {str(e)}")
            return {'ventas': [], 'resumen': {'total_ventas': 0, 'monto_total': Decimal('0.00'), 'promedio_venta': Decimal('0.00'), 'venta_maxima': Decimal('0.00'), 'venta_minima': Decimal('0.00'), 'periodo': 'Error'}}

    @staticmethod
    def obtener_devoluciones(fecha_inicio=None, fecha_fin=None):
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        d.idDevolucion, d.fechaDevolucion, d.motivo, d.idVentaDev,
                        p.nombreProducto, p.id_producto, dd.cantidadDevuelta, p.precioProducto,
                        pe.primerNombre, pe.primerApellido
                    FROM Devolucion d
                    JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                    JOIN Producto p ON dd.id_producto = p.id_producto
                    LEFT JOIN Venta v ON d.idVentaDev = v.idVenta
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
                
                devoluciones_dict = {}
                detalles = []
                
                for row in devoluciones_raw:
                    dev_id = row[0]
                    c_nombre = f"{row[8] or ''} {row[9] or ''}".strip()
                    
                    if dev_id not in devoluciones_dict:
                        devoluciones_dict[dev_id] = {
                            'iddevolucion': row[0],
                            'fechadevolucion': row[1],
                            'motivo': row[2] or 'No especificado',
                            'id_venta_dev': row[3],
                            'cliente_nombre': c_nombre if c_nombre else 'No especificado',
                            'productos': []
                        }
                    
                    producto_info = {
                        'nombre': row[4],
                        'id_producto': row[5],
                        'cantidad': row[6] or 0,
                        'precio': Decimal(str(row[7] or 0)),
                        'monto_devuelto': Decimal(str(row[6] or 0)) * Decimal(str(row[7] or 0))
                    }
                    devoluciones_dict[dev_id]['productos'].append(producto_info)
                
                devoluciones = []
                for dev_data in devoluciones_dict.values():
                    devolucion = type('Devolucion', (), {
                        'iddevolucion': dev_data['iddevolucion'],
                        'fechadevolucion': dev_data['fechadevolucion'],
                        'motivo': dev_data['motivo'],
                        'productos_devueltos': dev_data['productos'],
                        'monto_total_devuelto': sum(p['monto_devuelto'] for p in dev_data['productos']),
                        'idventadev': type('Venta', (), {
                            'id_venta': dev_data['id_venta_dev'],
                            'codcliente': type('Cliente', (), {
                                'idpersonacliente': type('Persona', (), {
                                    'nombre_completo': dev_data['cliente_nombre']
                                })()
                            })()
                        })()
                    })()
                    devoluciones.append(devolucion)
                
                if devoluciones:
                    total_devoluciones = len(devoluciones)
                    monto_devuelto = sum(d.monto_total_devuelto for d in devoluciones)
                    total_productos_devueltos = sum(len(d.productos_devueltos) for d in devoluciones)
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
                    'total_devoluciones': total_devoluciones, 'monto_devuelto': monto_devuelto,
                    'total_productos_devueltos': total_productos_devueltos, 'motivos_principales': motivos,
                    'productos_mas_devueltos': {}
                }
                return {'devoluciones': devoluciones, 'detalles': detalles, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_devoluciones: {str(e)}")
            return {'devoluciones': [], 'detalles': [], 'resumen': {'total_devoluciones': 0, 'monto_devuelto': Decimal('0.00'), 'total_productos_devueltos': 0, 'motivos_principales': {}, 'productos_mas_devueltos': {}}}

    @staticmethod
    def obtener_produccion(fecha_inicio=None, fecha_fin=None):
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        pp.idProduccion, pp.fechaEntrada, pp.observacion, pp.EstadoRegistro,
                        p.nombreProducto, p.id_producto, dp.cantidad, dp.costo_unitario,
                        pe.primerNombre, pe.primerApellido, u.nombreUsuario
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
                
                producciones = []
                for row in producciones_raw:
                    fab_nombre = f"{row[8] or ''} {row[9] or ''}".strip()
                    produccion = type('Produccion', (), {
                        'idproduccion': row[0],
                        'id_produccion': row[0],
                        'fechaentrada': row[1],
                        'observacion': row[2] or '',
                        'estadoregistro': bool(row[3]),
                        'producto_nombre': row[4],
                        'producto_id': row[5],
                        'cantidadproducida': int(row[6] or 0),
                        'cantidad': int(row[6] or 0), 
                        'costo': Decimal(str(row[7] or 0)),
                        'costo_unitario': Decimal(str(row[7] or 0)),
                        'fabricante_nombre': fab_nombre if fab_nombre else 'No especificado',
                        'usuario_nombre': row[10] or 'No especificado',
                        'idproducto': type('Producto', (), {
                            'nombreproducto': row[4],
                            'id_producto': row[5]
                        })()
                    })()
                    producciones.append(produccion)
                
                if producciones:
                    total_producciones = int(len(producciones))
                    cantidad_total = int(sum(p.cantidadproducida for p in producciones))
                    costo_total = sum(p.costo * Decimal(str(p.cantidadproducida)) for p in producciones)
                    promedio_diario = float(cantidad_total / 30) if cantidad_total > 0 else 0.0
                else:
                    total_producciones = cantidad_total = 0
                    promedio_diario = 0.0
                    costo_total = Decimal('0.00')
                
                resumen = {
                    'total_producciones': total_producciones,
                    'total_ordenes': total_producciones,
                    'total': total_producciones if total_producciones > 0 else 1,
                    'cantidad_total': cantidad_total,
                    'total_productos_producidos': cantidad_total,
                    'total_producido': cantidad_total if cantidad_total > 0 else 1,
                    'costo_total': costo_total,
                    'promedio_diario': promedio_diario
                }
                return {'producciones': producciones, 'detalles': producciones, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_produccion: {str(e)}")
            return {'producciones': [], 'detalles': [], 'resumen': {'total_producciones': 0, 'total_ordenes': 0, 'total': 1, 'cantidad_total': 0, 'total_productos_producidos': 0, 'total_producido': 1, 'costo_total': Decimal('0.00'), 'promedio_diario': 0.0}}

    @staticmethod
    def obtener_clientes(filtros=None):
        if filtros is None: filtros = {}
        try:
            with connection.cursor() as cursor:
                base_query = """
                    SELECT 
                        c.idCliente, c.correo, c.estadoCliente,
                        p.cedula, p.primerNombre, p.primerApellido, p.direccion,
                        COUNT(v.idVenta) as total_compras,
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
                        p.primerNombre LIKE %s OR p.primerApellido LIKE %s OR p.cedula LIKE %s OR c.correo LIKE %s
                    )"""
                    buscar_param = f"%{filtros['buscar']}%"
                    params.extend([buscar_param, buscar_param, buscar_param, buscar_param])
                
                base_query += " GROUP BY c.idCliente, c.correo, c.estadoCliente, p.cedula, p.primerNombre, p.primerApellido, p.direccion"
                cursor.execute(base_query, params)
                clientes_raw = cursor.fetchall()
                
                clientes = []
                for row in clientes_raw:
                    c_nombre = f"{row[4] or ''} {row[5] or ''}".strip()
                    cliente_data = {
                        'cliente': type('Cliente', (), {
                            'idcliente': row[0],
                            'id_cliente': row[0],
                            'correo': row[1] or '',
                            'estadocliente': bool(row[2]),
                            'cedula': row[3] or '',
                            'direccion': row[6] or '',
                            'idpersonacliente': type('Persona', (), {
                                'nombre_completo': c_nombre if c_nombre else 'No especificado',
                                'primernombre': row[4] or '',
                                'primerapellido': row[5] or '',
                                'cedula': row[3] or '',
                                'direccion': row[6] or ''
                            })() if c_nombre else None
                        })(),
                        'total_compras': int(row[7] or 0),
                        'monto_total': Decimal(str(row[8] or 0)),
                        'ultima_compra': row[9]
                    }
                    clientes.append(cliente_data)
                
                if clientes:
                    total_clientes = len(clientes)
                    clientes_activos = sum(1 for c in clientes if c['cliente'].estadocliente)
                    clientes_inactivos = total_clientes - clientes_activos
                    porcentaje_activos = round((clientes_activos / total_clientes * 100) if total_clientes > 0 else 0, 2)
                else:
                    total_clientes = clientes_activos = clientes_inactivos = porcentaje_activos = 0
                
                resumen = {
                    'total_clientes': total_clientes, 'clientes_activos': clientes_activos,
                    'clientes_inactivos': clientes_inactivos, 'porcentaje_activos': porcentaje_activos
                }
                return {'clientes': clientes, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_clientes: {str(e)}")
            return {'clientes': [], 'resumen': {'total_clientes': 0, 'clientes_activos': 0, 'clientes_inactivos': 0, 'porcentaje_activos': 0}}

    @staticmethod
    def obtener_usuarios_empleados():
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        u.idUsuario, u.nombreUsuario, u.rol, u.activo, u.correo, u.ultimo_login,
                        pe.primerNombre, pe.primerApellido, e.rolEmpleado, e.salario, e.fechaContratacion
                    FROM Usuario u
                    LEFT JOIN Empleado e ON u.idEmpUsuario = e.idEmpleado
                    LEFT JOIN Persona pe ON e.idPersonaEmp = pe.cedula
                    ORDER BY u.nombreUsuario
                """)
                usuarios_raw = cursor.fetchall()
                
                usuarios = []
                for row in usuarios_raw:
                    e_nombre = f"{row[6] or ''} {row[7] or ''}".strip()
                    usuario = type('Usuario', (), {
                        'id': row[0], 'idusuario': row[0], 'nombreusuario': row[1], 'rol': row[2] or 'usuario',
                        'activo': bool(row[3]), 'correo': row[4] or '', 'ultimo_login': row[5], 'last_login': row[5],
                        'empleado_nombre': e_nombre if e_nombre else 'No especificado',
                        'rol_empleado': row[8] or '', 'salario': row[9] or 0, 'fecha_contratacion': row[10]
                    })()
                    usuarios.append(usuario)
                
                if usuarios:
                    total_usuarios = len(usuarios)
                    usuarios_activos = sum(1 for u in usuarios if u.activo)
                    usuarios_inactivos = total_usuarios - usuarios_activos
                    roles_count = {}
                    for usuario in usuarios:
                        rol = usuario.rol or 'sin_rol'
                        roles_count[rol] = roles_count.get(rol, 0) + 1
                else:
                    total_usuarios = usuarios_activos = usuarios_inactivos = 0
                    roles_count = {}
                
                resumen = {'total_usuarios': total_usuarios, 'usuarios_activos': usuarios_activos, 'usuarios_inactivos': usuarios_inactivos, 'roles_count': roles_count}
                return {'usuarios': usuarios, 'empleados': usuarios, 'roles_count': roles_count, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_usuarios_empleados: {str(e)}")
            return {'usuarios': [], 'empleados': [], 'roles_count': {}, 'resumen': {'total_usuarios': 0, 'usuarios_activos': 0, 'usuarios_inactivos': 0, 'roles_count': {}}}

    @staticmethod
    def obtener_productos_por_categoria():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT idCategoria, nombreCategoria, descripcionCategoria FROM Categoria WHERE estadoCategoria = 1")
                categorias_raw = cursor.fetchall()
                
                cursor.execute("SELECT id_producto, nombreProducto, idCategoriaPro, existenciaProducto, precioProducto FROM Producto WHERE estado = 1")
                productos_raw = cursor.fetchall()
                
                categorias_dict = {}
                for row in categorias_raw:
                    cat_id = row[0]
                    categorias_dict[cat_id] = {
                        'categoria': type('Categoria', (), {
                            'idcategoria': row[0],
                            'nombrecategoria': row[1],
                            'descripcioncategoria': row[2] or ''
                        })(),
                        'productos': [],
                        'cantidad_productos': 0,
                        'valor_total': Decimal('0.00')
                    }
                
                total_productos = 0
                for row in productos_raw:
                    cat_id = row[2]
                    if cat_id in categorias_dict:
                        prod = type('Producto', (), {
                            'id_producto': row[0],
                            'nombreproducto': row[1],
                            'existenciaproducto': row[3] or 0,
                            'precioproducto': Decimal(str(row[4] or 0)),
                            'valor_total': Decimal(str((row[3] or 0) * (row[4] or 0)))
                        })()
                        categorias_dict[cat_id]['productos'].append(prod)
                        categorias_dict[cat_id]['cantidad_productos'] += 1
                        categorias_dict[cat_id]['valor_total'] += prod.valor_total
                        total_productos += 1
                
                categorias_data = list(categorias_dict.values())
                categorias_data.sort(key=lambda x: x['cantidad_productos'], reverse=True)
                
                for cat_data in categorias_data:
                    cat_data['porcentaje'] = round((cat_data['cantidad_productos'] / total_productos * 100) if total_productos > 0 else 0, 2)
                
                categoria_mayor = 'N/A'
                if categorias_data and categorias_data[0]['cantidad_productos'] > 0:
                    categoria_mayor = categorias_data[0]['categoria'].nombrecategoria
                
                valor_total_inventario = sum(cat['valor_total'] for cat in categorias_data)
                
                resumen = {
                    'total_categorias': len(categorias_data),
                    'total_productos': total_productos,
                    'categoria_mayor': categoria_mayor,
                    'valor_total_inventario': valor_total_inventario
                }
                
                return {'categorias': categorias_data, 'resumen': resumen}
                
        except Exception as e:
            logger.error(f"Error en obtener_productos_por_categoria: {str(e)}")
            return {'categorias': [], 'resumen': {'total_categorias': 0, 'total_productos': 0, 'categoria_mayor': 'N/A', 'valor_total_inventario': Decimal('0.00')}}