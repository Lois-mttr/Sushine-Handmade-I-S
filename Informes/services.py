"""
Servicios mejorados para el módulo de reportes NEXO con SQL crudo
"""
import logging
from django.db import connection
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta, date
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger('nexo.reports')

class ReportService:
    """
    Servicio principal para generar reportes con SQL crudo optimizado
    """
    
    @staticmethod
    def get_inventario_general(filtros: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtiene datos para el reporte de inventario general con SQL optimizado
        """
        try:
            base_query = """
                SELECT 
                p.id_producto,
                p.idUbicacionPro,
                p.nombreProducto,
                p.descripcionProducto,
                p.existenciaProducto,
                p.existenciaMinima,
                p.precioProducto,
                p.estado as producto_estado,
                c.idCategoria,
                c.nombreCategoria,
                c.descripcionCategoria,
                u.id_ubicacion,
                u.nombreUbicacion,
                u.direccion,
                CASE 
            WHEN p.existenciaProducto <= 0 THEN 'SIN_STOCK'
            WHEN p.existenciaProducto <= p.existenciaMinima THEN 'CRITICO'
            WHEN p.existenciaProducto <= (p.existenciaMinima * 2) THEN 'BAJO'
            WHEN p.existenciaProducto <= (p.existenciaMinima * 5) THEN 'NORMAL'
            ELSE 'ALTO'
        END as nivel_stock,
        (p.existenciaProducto * COALESCE(p.precioProducto, 0)) as valor_total_stock,
        DATEDIFF(CURDATE(), (SELECT MIN(pp.fechaEntrada) 
        FROM ProductosProduccion pp
        JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
        WHERE dp.id_producto = p.id_producto)) as dias_desde_creacion,(
        SELECT COUNT(*) 
        FROM DetalleVenta dv 
        JOIN Venta v ON dv.idVenta = v.id_venta
        WHERE dv.idProVenta = p.id_producto 
        AND v.fechaVenta >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)) as ventas_ultimo_mes
            FROM Producto p
            LEFT JOIN Categoria c ON p.idCategoriaPro = c.idCategoria
            LEFT JOIN Ubicacion u ON p.idUbicacionPro = u.id_ubicacion
        WHERE p.estado = 1
            """
            
            params = []
            conditions = []
            
            if filtros:
                if filtros.get('ubicacion'):
                    conditions.append("p.idUbicacionPro = %s")
                    params.append(filtros['ubicacion'])
                
                if filtros.get('categoria'):
                    conditions.append("p.idCategoriaPro = %s")
                    params.append(filtros['categoria'])
                
                if filtros.get('stock_estado'):
                    if filtros['stock_estado'] == 'bajo':
                        conditions.append("p.existenciaProducto <= p.existenciaMinima")
                    elif filtros['stock_estado'] == 'critico':
                        conditions.append("p.existenciaProducto <= 0")
                    elif filtros['stock_estado'] == 'normal':
                        conditions.append("p.existenciaProducto > p.existenciaMinima AND p.existenciaProducto <= (p.existenciaMinima * 5)")
                    elif filtros['stock_estado'] == 'alto':
                        conditions.append("p.existenciaProducto > (p.existenciaMinima * 5)")
                
                if filtros.get('buscar'):
                    conditions.append("(p.nombreProducto LIKE %s OR p.descripcionProducto LIKE %s)")
                    search_term = f"%{filtros['buscar']}%"
                    params.extend([search_term, search_term])
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " ORDER BY u.nombreUbicacion, c.nombreCategoria, p.nombreProducto"
            
            with connection.cursor() as cursor:
                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Calcular estadísticas avanzadas
                stats_query = """
                    SELECT 
                        COUNT(DISTINCT p.id_producto) as total_productos,
                        COUNT(DISTINCT c.idCategoria) as total_categorias,
                        COUNT(DISTINCT u.id_ubicacion) as total_ubicaciones,
                        SUM(p.existenciaProducto) as total_unidades,
                        SUM(p.existenciaProducto * COALESCE(p.precioProducto, 0)) as valor_total_inventario,
                        COUNT(CASE WHEN p.existenciaProducto <= 0 THEN 1 END) as productos_sin_stock,
                        COUNT(CASE WHEN p.existenciaProducto <= p.existenciaMinima THEN 1 END) as productos_stock_critico,
                        COUNT(CASE WHEN p.existenciaProducto <= (p.existenciaMinima * 2) THEN 1 END) as productos_stock_bajo,
                        AVG(p.precioProducto) as precio_promedio,
                        MAX(p.precioProducto) as precio_maximo,
                        MIN(p.precioProducto) as precio_minimo
                    FROM Producto p
                    LEFT JOIN Categoria c ON p.idCategoriaPro = c.idCategoria
                    LEFT JOIN Ubicacion u ON p.idUbicacionPro = u.id_ubicacion
                    WHERE p.estado = 1
                """
                
                if conditions:
                    stats_query += " AND " + " AND ".join(conditions)
                
                cursor.execute(stats_query, params)
                stats_row = cursor.fetchone()
                stats_columns = [col[0] for col in cursor.description]
                stats = dict(zip(stats_columns, stats_row))
                
                # Calcular porcentajes
                total_productos = stats['total_productos'] or 1
                stats['porcentaje_sin_stock'] = round((stats['productos_sin_stock'] / total_productos) * 100, 2)
                stats['porcentaje_stock_critico'] = round((stats['productos_stock_critico'] / total_productos) * 100, 2)
                stats['porcentaje_stock_bajo'] = round((stats['productos_stock_bajo'] / total_productos) * 100, 2)
                
                return {
                    'data': results,
                    'stats': stats,
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Error en get_inventario_general: {str(e)}")
            return {
                'data': [],
                'stats': {},
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_ventas(filtros: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtiene datos para el reporte de ventas con análisis detallado
        """
        try:
            base_query = """
                SELECT 
                    v.id_venta,
                    v.fechaVenta,
                    v.subtotal,
                    v.descuento,
                    v.total,
                    v.estado as estado_venta,
                    v.observaciones,
                    u.idUsuario as vendedor_id,
                    u.nombreUsuario as vendedor_nombre,
                    u.rol as vendedor_rol,
                    c.idCliente as cliente_id,
                    CONCAT(COALESCE(per.primerNombre, ''), ' ', 
                        COALESCE(per.segundoNombre, ''), ' ',
                        COALESCE(per.primerApellido, ''), ' ',
                        COALESCE(per.segundoApellido, '')) as cliente_nombre,
                    per.cedula as cliente_cedula,
                    per.telefono as cliente_telefono,
                    c.correo as cliente_correo,
                    c.estadoCliente,
                    COUNT(dv.idProVenta) as total_productos_venta,
                    SUM(dv.cantidadVenta) as total_unidades_vendidas,
                    CASE 
                        WHEN v.estado = 'REALIZADA' THEN 'success'
                        WHEN v.estado = 'ANULADA' THEN 'danger'
                        WHEN v.estado = 'PENDIENTE' THEN 'warning'
                        ELSE 'secondary'
                    END as estado_color,
                    DATEDIFF(CURDATE(), v.fechaVenta) as dias_desde_venta
                FROM Venta v
                LEFT JOIN Usuario u ON v.idUsuarioVenta = u.idUsuario
                LEFT JOIN Cliente c ON v.codCliente = c.idCliente
                LEFT JOIN Persona per ON c.idPersonaCliente = per.cedula
                LEFT JOIN DetalleVenta dv ON v.id_venta = dv.idVenta
                WHERE 1=1
            """
            
            params = []
            conditions = []
            
            if filtros:
                if filtros.get('fecha_desde'):
                    conditions.append("DATE(v.fechaVenta) >= %s")
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    conditions.append("DATE(v.fechaVenta) <= %s")
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('cliente'):
                    conditions.append("v.codCliente = %s")
                    params.append(filtros['cliente'])
                
                if filtros.get('vendedor'):
                    conditions.append("v.idUsuarioVenta = %s")
                    params.append(filtros['vendedor'])
                
                if filtros.get('estado'):
                    conditions.append("v.estado = %s")
                    params.append(filtros['estado'])
                
                if filtros.get('monto_minimo'):
                    conditions.append("v.total >= %s")
                    params.append(filtros['monto_minimo'])
                
                if filtros.get('monto_maximo'):
                    conditions.append("v.total <= %s")
                    params.append(filtros['monto_maximo'])
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += """
                GROUP BY v.id_venta, v.fechaVenta, v.subtotal, v.descuento, v.total, 
                         v.estado, v.observaciones, u.idUsuario, u.nombreUsuario, u.rol,
                         c.idCliente, per.primerNombre, per.segundoNombre, per.primerApellido, 
                         per.segundoApellido, per.cedula, per.telefono, c.correo, c.estadoCliente
                ORDER BY v.fechaVenta DESC, v.id_venta DESC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Obtener detalles de productos para cada venta
                for venta in results:
                    productos_query = """
                        SELECT 
                            dv.idProVenta,
                            p.nombreProducto,
                            dv.cantidadVenta,
                            dv.precioUnitario,
                            dv.subtotal,
                            c.nombreCategoria
                        FROM DetalleVenta dv
                        LEFT JOIN Producto p ON dv.idProVenta = p.id_producto
                        LEFT JOIN Categoria c ON p.idCategoriaPro = c.idCategoria
                        WHERE dv.idVenta = %s
                        ORDER BY dv.cantidadVenta DESC
                    """
                    cursor.execute(productos_query, [venta['id_venta']])
                    productos_columns = [col[0] for col in cursor.description]
                    venta['productos'] = [dict(zip(productos_columns, row)) for row in cursor.fetchall()]
                
                # Estadísticas avanzadas
                stats_query = """
                    SELECT 
                        COUNT(DISTINCT v.id_venta) as total_ventas,
                        COUNT(DISTINCT CASE WHEN v.estado = 'REALIZADA' THEN v.id_venta END) as ventas_realizadas,
                        COUNT(DISTINCT CASE WHEN v.estado = 'ANULADA' THEN v.id_venta END) as ventas_anuladas,
                        COUNT(DISTINCT CASE WHEN v.estado = 'PENDIENTE' THEN v.id_venta END) as ventas_pendientes,
                        COUNT(DISTINCT v.codCliente) as clientes_unicos,
                        COUNT(DISTINCT v.idUsuarioVenta) as vendedores_activos,
                        SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.total ELSE 0 END) as total_facturado,
                        SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.subtotal ELSE 0 END) as total_subtotal,
                        SUM(CASE WHEN v.estado = 'REALIZADA' THEN COALESCE(v.descuento, 0) ELSE 0 END) as total_descuentos,
                        AVG(CASE WHEN v.estado = 'REALIZADA' THEN v.total END) as promedio_venta,
                        MAX(CASE WHEN v.estado = 'REALIZADA' THEN v.total END) as venta_maxima,
                        MIN(CASE WHEN v.estado = 'REALIZADA' THEN v.total END) as venta_minima,
                        SUM(dv.cantidadVenta) as total_productos_vendidos
                    FROM Venta v
                    LEFT JOIN DetalleVenta dv ON v.id_venta = dv.idVenta
                    WHERE 1=1
                """
                
                if conditions:
                    stats_query += " AND " + " AND ".join(conditions)
                
                cursor.execute(stats_query, params)
                stats_row = cursor.fetchone()
                stats_columns = [col[0] for col in cursor.description]
                stats = dict(zip(stats_columns, stats_row))
                
                # Calcular métricas adicionales
                if stats['total_ventas'] > 0:
                    stats['tasa_conversion'] = round((stats['ventas_realizadas'] / stats['total_ventas']) * 100, 2)
                    stats['tasa_cancelacion'] = round((stats['ventas_anuladas'] / stats['total_ventas']) * 100, 2)
                else:
                    stats['tasa_conversion'] = 0
                    stats['tasa_cancelacion'] = 0
                
                return {
                    'data': results,
                    'stats': stats,
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Error en get_ventas: {str(e)}")
            return {
                'data': [],
                'stats': {},
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_produccion(filtros: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtiene datos para el reporte de producción con análisis de costos
        """
        try:
            base_query = """
                SELECT 
                    pp.idProduccion,
                    pp.fechaEntrada,
                    pp.observacion,
                    pp.EstadoRegistro,
                    u.idUsuario as usuario_id,
                    u.nombreUsuario as usuario_responsable,
                    u.rol as usuario_rol,
                    dp.id_detalle,
                    dp.id_producto,
                    p.nombreProducto,
                    p.descripcionProducto,
                    dp.cantidad,
                    dp.costo_unitario,
                    (dp.cantidad * dp.costo_unitario) as costo_total_item,
                    e.idEmpleado as fabricante_id,
                    CONCAT(COALESCE(per.primerNombre, ''), ' ', 
                           COALESCE(per.primerApellido, '')) as fabricante_nombre,
                    per.cedula as fabricante_cedula,
                    e.rolEmpleado as fabricante_rol,
                    e.salario as fabricante_salario,
                    c.nombreCategoria,
                    ub.nombreUbicacion,
                    p.existenciaProducto as stock_actual,
                    p.existenciaMinima as stock_minimo,
                    DATEDIFF(CURDATE(), pp.fechaEntrada) as dias_desde_produccion,
                    (dp.cantidad * dp.costo_unitario) / NULLIF(dp.cantidad, 0) as costo_unitario_calculado
                FROM ProductosProduccion pp
                LEFT JOIN Usuario u ON pp.id_usuario = u.idUsuario
                LEFT JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                LEFT JOIN Producto p ON dp.id_producto = p.id_producto
                LEFT JOIN Categoria c ON p.idCategoriaPro = c.idCategoria
                LEFT JOIN Ubicacion ub ON p.idUbicacionPro = ub.id_ubicacion
                LEFT JOIN Empleado e ON dp.idFabricante = e.idEmpleado
                LEFT JOIN Persona per ON e.idPersonaEmp = per.cedula
                WHERE pp.EstadoRegistro = 1
            """
            
            params = []
            conditions = []
            
            if filtros:
                if filtros.get('fecha_desde'):
                    conditions.append("DATE(pp.fechaEntrada) >= %s")
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    conditions.append("DATE(pp.fechaEntrada) <= %s")
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('usuario'):
                    conditions.append("pp.id_usuario = %s")
                    params.append(filtros['usuario'])
                
                if filtros.get('producto'):
                    conditions.append("dp.id_producto = %s")
                    params.append(filtros['producto'])
                
                if filtros.get('fabricante'):
                    conditions.append("dp.idFabricante = %s")
                    params.append(filtros['fabricante'])
                
                if filtros.get('categoria'):
                    conditions.append("p.idCategoriaPro = %s")
                    params.append(filtros['categoria'])
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " ORDER BY pp.fechaEntrada DESC, pp.idProduccion DESC"
            
            with connection.cursor() as cursor:
                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Estadísticas de producción
                stats_query = """
                    SELECT 
                        COUNT(DISTINCT pp.idProduccion) as total_producciones,
                        COUNT(DISTINCT dp.id_producto) as productos_diferentes,
                        COUNT(DISTINCT dp.idFabricante) as fabricantes_activos,
                        COUNT(DISTINCT pp.id_usuario) as usuarios_registradores,
                        SUM(dp.cantidad) as total_unidades_producidas,
                        SUM(dp.cantidad * dp.costo_unitario) as costo_total_produccion,
                        AVG(dp.costo_unitario) as costo_unitario_promedio,
                        MAX(dp.costo_unitario) as costo_unitario_maximo,
                        MIN(dp.costo_unitario) as costo_unitario_minimo,
                        AVG(dp.cantidad) as cantidad_promedio_por_lote
                    FROM ProductosProduccion pp
                    LEFT JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                    LEFT JOIN Producto p ON dp.id_producto = p.id_producto
                    WHERE pp.EstadoRegistro = 1
                """
                
                if conditions:
                    stats_query += " AND " + " AND ".join(conditions)
                
                cursor.execute(stats_query, params)
                stats_row = cursor.fetchone()
                stats_columns = [col[0] for col in cursor.description]
                stats = dict(zip(stats_columns, stats_row))
                
                # Análisis de eficiencia por fabricante
                fabricantes_query = """
                    SELECT 
                        e.idEmpleado,
                        CONCAT(per.primerNombre, ' ', per.primerApellido) as nombre,
                        COUNT(DISTINCT pp.idProduccion) as producciones_realizadas,
                        SUM(dp.cantidad) as total_unidades,
                        SUM(dp.cantidad * dp.costo_unitario) as costo_total,
                        AVG(dp.cantidad) as promedio_unidades_por_produccion
                    FROM ProductosProduccion pp
                    LEFT JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                    LEFT JOIN Empleado e ON dp.idFabricante = e.idEmpleado
                    LEFT JOIN Persona per ON e.idPersonaEmp = per.cedula
                    WHERE pp.EstadoRegistro = 1
                """
                
                if conditions:
                    fabricantes_query += " AND " + " AND ".join(conditions)
                
                fabricantes_query += """
                    GROUP BY e.idEmpleado, per.primerNombre, per.primerApellido
                    ORDER BY total_unidades DESC
                """
                
                cursor.execute(fabricantes_query, params)
                fabricantes_columns = [col[0] for col in cursor.description]
                stats['fabricantes_performance'] = [dict(zip(fabricantes_columns, row)) for row in cursor.fetchall()]
                
                return {
                    'data': results,
                    'stats': stats,
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Error en get_produccion: {str(e)}")
            return {
                'data': [],
                'stats': {},
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_clientes(filtros: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtiene datos para el reporte de clientes con análisis de comportamiento
        """
        try:
            base_query = """
                SELECT 
                    c.idCliente,
                    CONCAT(COALESCE(per.primerNombre, ''), ' ', 
                           COALESCE(per.segundoNombre, ''), ' ',
                           COALESCE(per.primerApellido, ''), ' ',
                           COALESCE(per.segundoApellido, '')) as nombre_completo,
                    per.cedula,
                    per.telefono,
                    per.direccion,
                    c.correo,
                    c.estadoCliente,
                    c.fechaRegistro,
                    COUNT(DISTINCT v.id_venta) as total_compras,
                    COUNT(DISTINCT CASE WHEN v.estado = 'REALIZADA' THEN v.id_venta END) as compras_exitosas,
                    COUNT(DISTINCT CASE WHEN v.estado = 'ANULADA' THEN v.id_venta END) as compras_anuladas,
                    COALESCE(SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.total ELSE 0 END), 0) as total_gastado,
                    COALESCE(AVG(CASE WHEN v.estado = 'REALIZADA' THEN v.total END), 0) as promedio_compra,
                    MAX(v.fechaVenta) as ultima_compra,
                    MIN(v.fechaVenta) as primera_compra,
                    DATEDIFF(CURDATE(), MAX(v.fechaVenta)) as dias_sin_comprar,
                    DATEDIFF(CURDATE(), c.fechaRegistro) as dias_como_cliente,
                    SUM(dv.cantidadVenta) as total_productos_comprados,
                    CASE 
                        WHEN COUNT(DISTINCT v.id_venta) = 0 THEN 'INACTIVO'
                        WHEN DATEDIFF(CURDATE(), MAX(v.fechaVenta)) <= 30 THEN 'ACTIVO'
                        WHEN DATEDIFF(CURDATE(), MAX(v.fechaVenta)) <= 90 THEN 'REGULAR'
                        WHEN DATEDIFF(CURDATE(), MAX(v.fechaVenta)) <= 180 THEN 'OCASIONAL'
                        ELSE 'PERDIDO'
                    END as categoria_cliente,
                    CASE 
                        WHEN COALESCE(SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.total ELSE 0 END), 0) >= 10000 THEN 'VIP'
                        WHEN COALESCE(SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.total ELSE 0 END), 0) >= 5000 THEN 'PREMIUM'
                        WHEN COALESCE(SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.total ELSE 0 END), 0) >= 1000 THEN 'REGULAR'
                        ELSE 'NUEVO'
                    END as nivel_cliente
                FROM Cliente c
                LEFT JOIN Persona per ON c.idPersonaCliente = per.cedula
                LEFT JOIN Venta v ON c.idCliente = v.codCliente
                LEFT JOIN DetalleVenta dv ON v.id_venta = dv.idVenta
                WHERE 1=1
            """
            
            params = []
            conditions = []
            
            if filtros:
                if filtros.get('estado') != '':
                    conditions.append("c.estadoCliente = %s")
                    params.append(int(filtros['estado']))
                
                if filtros.get('buscar'):
                    conditions.append("""(
                        per.primerNombre LIKE %s OR 
                        per.segundoNombre LIKE %s OR 
                        per.primerApellido LIKE %s OR 
                        per.segundoApellido LIKE %s OR 
                        per.cedula LIKE %s OR 
                        c.correo LIKE %s
                    )""")
                    search_term = f"%{filtros['buscar']}%"
                    params.extend([search_term] * 6)
                
                if filtros.get('categoria_cliente'):
                    # Esta condición se aplicará después de la consulta principal
                    pass
                
                if filtros.get('nivel_cliente'):
                    # Esta condición se aplicará después de la consulta principal
                    pass
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += """
                GROUP BY c.idCliente, per.primerNombre, per.segundoNombre, per.primerApellido, 
                         per.segundoApellido, per.cedula, per.telefono, per.direccion, 
                         c.correo, c.estadoCliente, c.fechaRegistro
                ORDER BY total_gastado DESC, nombre_completo
            """
            
            with connection.cursor() as cursor:
                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Aplicar filtros post-consulta si es necesario
                if filtros:
                    if filtros.get('categoria_cliente'):
                        results = [r for r in results if r['categoria_cliente'] == filtros['categoria_cliente']]
                    
                    if filtros.get('nivel_cliente'):
                        results = [r for r in results if r['nivel_cliente'] == filtros['nivel_cliente']]
                
                # Estadísticas de clientes
                stats_query = """
                    SELECT 
                        COUNT(DISTINCT c.idCliente) as total_clientes,
                        COUNT(DISTINCT CASE WHEN c.estadoCliente = 1 THEN c.idCliente END) as clientes_activos,
                        COUNT(DISTINCT CASE WHEN c.estadoCliente = 0 THEN c.idCliente END) as clientes_inactivos,
                        COUNT(DISTINCT CASE WHEN v.id_venta IS NOT NULL THEN c.idCliente END) as clientes_con_compras,
                        COUNT(DISTINCT CASE WHEN v.id_venta IS NULL THEN c.idCliente END) as clientes_sin_compras,
                        COALESCE(SUM(CASE WHEN v.estado = 'REALIZADA' THEN v.total ELSE 0 END), 0) as total_facturado_clientes,
                        COALESCE(AVG(CASE WHEN v.estado = 'REALIZADA' THEN v.total END), 0) as promedio_compra_general,
                        COUNT(DISTINCT CASE WHEN DATEDIFF(CURDATE(), c.fechaRegistro) <= 30 THEN c.idCliente END) as clientes_nuevos_mes,
                        COUNT(DISTINCT CASE WHEN DATEDIFF(CURDATE(), MAX(v.fechaVenta)) <= 30 THEN c.idCliente END) as clientes_activos_mes
                    FROM Cliente c
                    LEFT JOIN Persona per ON c.idPersonaCliente = per.cedula
                    LEFT JOIN Venta v ON c.idCliente = v.codCliente
                    WHERE 1=1
                """
                
                if conditions:
                    stats_query += " AND " + " AND ".join(conditions)
                
                cursor.execute(stats_query, params)
                stats_row = cursor.fetchone()
                stats_columns = [col[0] for col in cursor.description]
                stats = dict(zip(stats_columns, stats_row))
                
                # Calcular métricas adicionales
                if stats['total_clientes'] > 0:
                    stats['porcentaje_activos'] = round((stats['clientes_activos'] / stats['total_clientes']) * 100, 2)
                    stats['porcentaje_con_compras'] = round((stats['clientes_con_compras'] / stats['total_clientes']) * 100, 2)
                else:
                    stats['porcentaje_activos'] = 0
                    stats['porcentaje_con_compras'] = 0
                
                # Análisis por categorías
                categorias_stats = {}
                for cliente in results:
                    categoria = cliente['categoria_cliente']
                    nivel = cliente['nivel_cliente']
                    
                    if categoria not in categorias_stats:
                        categorias_stats[categoria] = 0
                    categorias_stats[categoria] += 1
                
                stats['distribucion_categorias'] = categorias_stats
                
                return {
                    'data': results,
                    'stats': stats,
                    'success': True
                }
                
        except Exception as e:
            logger.error(f"Error en get_clientes: {str(e)}")
            return {
                'data': [],
                'stats': {},
                'success': False,
                'error': str(e)
            }
    # @staticmethod
    # def log_report_generation(usuario, tipo_reporte: str, formato: str, filtros: Dict, 
    #                         total_registros: int, tiempo_generacion: float, ip_address: str = None):
    #     """
    #     Registra la generación de un reporte para auditoría
    #     """
    #     try:
    #         from .models import ReportLog
    #         
    #         ReportLog.objects.create(
    #             usuario=usuario,
    #             tipo_reporte=tipo_reporte,
    #             formato_exportacion=formato,
    #             filtros_aplicados=json.dumps(filtros) if filtros else '{}',
    #             total_registros=total_registros,
    #             tiempo_generacion=round(tiempo_generacion, 3),
    #             ip_address=ip_address or 'Unknown'
    #         )
    #         
    #         logger.info(f"Reporte {tipo_reporte} generado por {usuario.nombreusuario if usuario else 'Sistema'}")
    #         
    #     except Exception as e:
    #         logger.error(f"Error al registrar log de reporte: {str(e)}")
    
    @staticmethod
    def get_dashboard_stats():
        """
        Devuelve estadísticas agregadas para el dashboard usando SQL crudo y la estructura de tus tablas MySQL.
        """
        stats = {
            'reportes_hoy': 0,
            'incremento_reportes': 0,
            'total_productos': 0,
            'productos_stock_bajo': 0,
            'valor_inventario': 0,
            'ventas_mes': 0,
            'ventas_realizadas': 0,
            'ventas_hoy': 0,
            'total_facturado': 0,
            'clientes_activos': 0,
            'clientes_nuevos': 0,
            'total_clientes': 0,
            'devoluciones_mes': 0,
            'valor_devuelto': 0,
            'producciones_mes': 0,
            'costo_produccion': 0,
            'eventos_hoy': 0,
            'errores_sistema': 0,
        }
        try:
            with connection.cursor() as cursor:
                hoy = date.today()
                ayer = hoy - timedelta(days=1)
                primer_dia_mes = hoy.replace(day=1)

                # Reportes generados hoy y ayer
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN DATE(fecha_generacion) = %s THEN 1 ELSE 0 END) as reportes_hoy,
                        SUM(CASE WHEN DATE(fecha_generacion) = %s THEN 1 ELSE 0 END) as reportes_ayer
                    FROM report_log
                """, [hoy, ayer])
                row = cursor.fetchone()
                stats['reportes_hoy'] = row[0] or 0
                reportes_ayer = row[1] or 0
                stats['incremento_reportes'] = (
                    int(((stats['reportes_hoy'] - reportes_ayer) / reportes_ayer) * 100) if reportes_ayer else (100 if stats['reportes_hoy'] else 0)
                )

                # Productos en inventario y stock bajo
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_productos,
                        SUM(CASE WHEN existenciaProducto <= existenciaMinima THEN 1 ELSE 0 END) as productos_stock_bajo,
                        SUM(existenciaProducto * IFNULL(precioProducto, 0)) as valor_inventario
                    FROM Producto
                    WHERE estado = 1
                """)
                row = cursor.fetchone()
                stats['total_productos'] = row[0] or 0
                stats['productos_stock_bajo'] = row[1] or 0
                stats['valor_inventario'] = float(row[2] or 0)

                # Ventas del mes, ventas realizadas, ventas hoy y total facturado
                cursor.execute("""
                    SELECT 
                        COUNT(*) as ventas_mes,
                        SUM(CASE WHEN estado = 'REALIZADA' THEN 1 ELSE 0 END) as ventas_realizadas,
                        SUM(CASE WHEN estado = 'REALIZADA' AND DATE(fechaVenta) = %s THEN 1 ELSE 0 END) as ventas_hoy,
                        SUM(CASE WHEN estado = 'REALIZADA' THEN total ELSE 0 END) as total_facturado
                    FROM Venta
                    WHERE fechaVenta >= %s
                """, [hoy, primer_dia_mes])
                row = cursor.fetchone()
                stats['ventas_mes'] = row[0] or 0
                stats['ventas_realizadas'] = row[1] or 0
                stats['ventas_hoy'] = row[2] or 0
                stats['total_facturado'] = float(row[3] or 0)

                # Clientes activos, nuevos este mes y total
                cursor.execute("""
                    SELECT 
                    COUNT(*) as total_clientes,
                    SUM(CASE WHEN c.estadoCliente = 1 THEN 1 ELSE 0 END) as clientes_activos,
                    SUM(CASE WHEN c.estadoCliente = 1 AND 
                    c.idCliente IN (
                    SELECT codCliente 
                    FROM Venta 
                    GROUP BY codCliente 
                    HAVING MIN(fechaVenta) >= %s) THEN 1 ELSE 0 END) as clientes_nuevos 
                    FROM Cliente c
                """, [primer_dia_mes])
                row = cursor.fetchone()
                stats['total_clientes'] = row[0] or 0
                stats['clientes_activos'] = row[1] or 0
                stats['clientes_nuevos'] = row[2] or 0

                # Devoluciones del mes y valor devuelto
                cursor.execute("""
                    SELECT 
                        COUNT(*) as devoluciones_mes
                    FROM Devolucion
                    WHERE fechaDevolucion >= %s
                """, [primer_dia_mes])
                row = cursor.fetchone()
                stats['devoluciones_mes'] = row[0] or 0

                cursor.execute("""
                    SELECT 
                        SUM(dd.cantidadDevuelta * IFNULL(p.precioProducto, 0)) as valor_devuelto
                    FROM Devolucion d
                    JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                    JOIN Producto p ON dd.id_producto = p.id_producto
                    WHERE d.fechaDevolucion >= %s
                """, [primer_dia_mes])
                row = cursor.fetchone()
                stats['valor_devuelto'] = float(row[0] or 0)

                # Producción del mes y costo total
                cursor.execute("""
                    SELECT 
                        COUNT(*) as producciones_mes
                    FROM ProductosProduccion
                    WHERE fechaEntrada >= %s AND EstadoRegistro = 1
                """, [primer_dia_mes])
                row = cursor.fetchone()
                stats['producciones_mes'] = row[0] or 0

                cursor.execute("""
                    SELECT 
                        SUM(dp.cantidad * dp.costo_unitario) as costo_produccion
                    FROM ProductosProduccion pp
                    JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                    WHERE pp.fechaEntrada >= %s AND pp.EstadoRegistro = 1
                """, [primer_dia_mes])
                row = cursor.fetchone()
                stats['costo_produccion'] = float(row[0] or 0)



                ##### QUITARE ACTIVIDAD 
                # Auditoría: eventos hoy y errores
                cursor.execute("""
                    SELECT 
                        COUNT(*) as eventos_hoy,
                        SUM(CASE WHEN accion = 'ERROR' THEN 1 ELSE 0 END) as errores_sistema
                    FROM system_activity
                    WHERE DATE(fecha_actividad) = %s
                """, [hoy])
                row = cursor.fetchone()
                stats['eventos_hoy'] = row[0] or 0
                stats['errores_sistema'] = row[1] or 0

        except Exception as e:
            logger = logging.getLogger('nexo.Informes')
            logger.error(f"Error obteniendo stats dashboard: {str(e)}")
        return stats
