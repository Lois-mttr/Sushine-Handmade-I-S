"""
Modelos y managers corregidos para el módulo de producción NEXO
Corrección completa de errores de inserción y validaciones
"""
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from core_data.models import (
    Productosproduccion,
    Detalleproduccion, 
    Producto,
    Usuario,
    Empleado,
    Ubicacion
)
import json
import logging
from decimal import Decimal
from datetime import datetime, date

logger = logging.getLogger('nexo.produccion')

# Re-exportar modelos para compatibilidad
ProductosProduccion = Productosproduccion
DetalleProduccion = Detalleproduccion
UbicacionProducto = Ubicacion

class ProduccionManager:
    """
    Manager corregido para operaciones de producción con manejo robusto de errores
    """
    
    @staticmethod
    def registrar_produccion(fechaEntrada, observacion, id_usuario, detalles):
        """
        Registra una nueva producción con validaciones completas y manejo de errores mejorado
        """
        try:
            # Convertir fecha a formato correcto para evitar timezone warnings
            if isinstance(fechaEntrada, date) and not isinstance(fechaEntrada, datetime):
                # Convertir date a datetime con timezone
                fecha_datetime = timezone.make_aware(
                    datetime.combine(fechaEntrada, datetime.min.time())
                )
            else:
                fecha_datetime = fechaEntrada
            
            with connection.cursor() as cursor:
                detalles_json = json.dumps(detalles, default=str)
                cursor.callproc('RegistrarProduccion', [
                    fecha_datetime,
                    observacion or '',
                    id_usuario,
                    detalles_json
                ])
                cursor.execute("SELECT LAST_INSERT_ID()")
                result = cursor.fetchone()
                id_produccion = result[0] if result else None
                
                if id_produccion and id_produccion > 0:
                    logger.info(f'Producción registrada exitosamente. ID: {id_produccion}')
                    return True, f"Producción #{id_produccion} registrada exitosamente", id_produccion
                else:
                    return False, "Error al obtener ID de la producción creada", None
                    
        except Exception as e:
            logger.error(f'Error al registrar producción: {str(e)}')
            return False, f"Error al registrar producción: {str(e)}", None
    
    @staticmethod
    def editar_produccion(id_produccion, fechaentrada, observacion, id_usuario, detalles):
        import json
        try:
            detalles_json = json.dumps(detalles)
            with connection.cursor() as cursor:
                cursor.callproc('EditarProduccion', [
                    id_produccion,
                    fechaentrada,
                    observacion,
                    id_usuario,
                    detalles_json
                ])
            return True, "Producción actualizada correctamente"
        except Exception as e:
            logger.error(f"Error en editar_produccion: {str(e)}")
            # Detectar error de duplicado MySQL
            if "Duplicate entry" in str(e):
                return False, "No se puede agregar productos duplicados"
            return False, f"Error al editar producción: {str(e)}"
    
    @staticmethod
    def dar_de_baja_produccion(id_produccion):
        """
        Da de baja una producción con reversión de inventario
        """
        try:
            # Verificar estado ANTES de la transacción
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT estadoregistro FROM Productosproduccion WHERE idproduccion = %s",
                    [id_produccion]
                )
                result = cursor.fetchone()
                
                if not result:
                    return False, "La producción no existe"
                
                if not result[0]:
                    return False, "La producción ya está inactiva"
            
            # Usar una sola transacción atómica
            with transaction.atomic():
                with connection.cursor() as cursor:
                    try:
                        # Llamar procedimiento almacenado
                        cursor.callproc('DarDeBajaProduccion', [id_produccion])
                        
                        logger.info(f'Producción {id_produccion} dada de baja exitosamente')
                        return True, f"Producción #{id_produccion} dada de baja exitosamente"
                        
                    except Exception as db_error:
                        logger.error(f'Error en procedimiento almacenado DarDeBajaProduccion: {str(db_error)}')
                        return False, f"Error en base de datos: {str(db_error)}"
                    
        except Exception as e:
            logger.error(f'Error al dar de baja producción {id_produccion}: {str(e)}')
            return False, f"Error al dar de baja producción: {str(e)}"
    
    @staticmethod
    def obtener_producciones_con_filtros(filtros=None, page=1, per_page=10):
        """
        Obtiene producciones con filtros corregidos y paginación
        """
        try:
            with connection.cursor() as cursor:
                # Query base corregida - IMPORTANTE: Convertir estadoregistro a boolean explícitamente
                base_query = """
                    SELECT 
                        pp.idproduccion as idProduccion,
                        pp.fechaentrada as fechaEntrada,
                        pp.observacion,
                        CASE WHEN pp.estadoregistro = 1 THEN true ELSE false END as EstadoRegistro,
                        u.nombreusuario as nombreUsuario,
                        COUNT(DISTINCT dp.id_producto) as total_productos,
                        COALESCE(SUM(dp.cantidad), 0) as total_cantidad,
                        COALESCE(SUM(dp.cantidad * dp.costo_unitario), 0) as total_costo
                    FROM Productosproduccion pp
                    LEFT JOIN Usuario u ON pp.id_usuario = u.idusuario
                    LEFT JOIN Detalleproduccion dp ON pp.idproduccion = dp.id_produccion
                    WHERE 1=1
                """
                
                # Query para contar total
                count_query = """
                    SELECT COUNT(DISTINCT pp.idproduccion)
                    FROM Productosproduccion pp
                    LEFT JOIN Usuario u ON pp.id_usuario = u.idusuario
                    WHERE 1=1
                """
                
                params = []
                count_params = []
                
                # Aplicar filtros (SIN filtro de estado)
                if filtros:
                    if filtros.get('fecha_desde'):
                        filter_clause = " AND DATE(pp.fechaentrada) >= %s"
                        base_query += filter_clause
                        count_query += filter_clause
                        params.append(filtros['fecha_desde'])
                        count_params.append(filtros['fecha_desde'])
                    
                    if filtros.get('fecha_hasta'):
                        filter_clause = " AND DATE(pp.fechaentrada) <= %s"
                        base_query += filter_clause
                        count_query += filter_clause
                        params.append(filtros['fecha_hasta'])
                        count_params.append(filtros['fecha_hasta'])
                    
                    if filtros.get('usuario'):
                        filter_clause = " AND u.nombreusuario LIKE %s"
                        base_query += filter_clause
                        count_query += filter_clause
                        search_term = f"%{filtros['usuario']}%"
                        params.append(search_term)
                        count_params.append(search_term)
                
                # Agregar GROUP BY y ORDER BY
                base_query += """
                    GROUP BY pp.idproduccion, pp.fechaentrada, pp.observacion, 
                             pp.estadoregistro, u.nombreusuario
                    ORDER BY pp.fechaentrada DESC, pp.idproduccion DESC
                """
                
                # Obtener total de registros
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
                
                # Calcular paginación
                offset = (page - 1) * per_page
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
                
                # Agregar LIMIT y OFFSET
                base_query += " LIMIT %s OFFSET %s"
                params.extend([per_page, offset])
                
                # Ejecutar query principal
                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    # CORREGIR: Asegurar que EstadoRegistro sea boolean
                    if 'EstadoRegistro' in row_dict:
                        row_dict['EstadoRegistro'] = bool(row_dict['EstadoRegistro'])
                    results.append(row_dict)
                
                return {
                    'results': results,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'has_previous': page > 1,
                    'has_next': page < total_pages,
                    'previous_page_number': page - 1 if page > 1 else None,
                    'next_page_number': page + 1 if page < total_pages else None
                }
                
        except Exception as e:
            logger.error(f'Error al obtener producciones con filtros: {str(e)}')
            return {
                'results': [],
                'total_count': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 1,
                'has_previous': False,
                'has_next': False,
                'previous_page_number': None,
                'next_page_number': None
            }
    
    @staticmethod
    def obtener_detalle_produccion(id_produccion):
        """
        Obtiene el detalle completo de una producción usando ORM
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        dp.id_produccion,
                        dp.id_producto,
                        COALESCE(p.nombreproducto, 'Producto no encontrado') as nombreProducto,
                        dp.cantidad,
                        dp.costo_unitario,
                        (dp.cantidad * dp.costo_unitario) as subtotal,
                        dp.idfabricante as idFabricante,
                        COALESCE(per.primernombre, '') as nombreFabricante,
                        COALESCE(per.primerapellido, '') as apellidoFabricante,
                        p.estado as estado_producto
                    FROM Detalleproduccion dp
                    LEFT JOIN Producto p ON dp.id_producto = p.id_producto
                    LEFT JOIN Empleado e ON dp.idfabricante = e.idempleado
                    LEFT JOIN Persona per ON e.idpersonaemp = per.cedula
                    WHERE dp.id_produccion = %s
                    ORDER BY dp.id_producto
                """, [id_produccion])
                
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Convertir estado_producto a booleano
                for r in results:
                    estado_val = r.get('estado_producto', 0)
                    try:
                        r['estado_producto'] = bool(int(estado_val))
                    except (ValueError, TypeError):
                        r['estado_producto'] = False
                
                return results
                
        except Exception as e:
            logger.error(f'Error al obtener detalle de producción {id_produccion}: {str(e)}')
            return []
    
    @staticmethod
    def verificar_estado_produccion(id_produccion):
        """
        Verifica el estado de una producción específica
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT estadoregistro FROM Productosproduccion WHERE idproduccion = %s",
                    [id_produccion]
                )
                result = cursor.fetchone()
                
                if not result:
                    return None, "Producción no encontrada"
                
                # CORREGIDO: Manejar BIT como bytes
                estado_val = result[0]
                try:
                    if isinstance(estado_val, (bytes, bytearray)):
                        estado_activo = int.from_bytes(estado_val, byteorder='little') == 1
                    else:
                        estado_activo = int(estado_val) == 1
                except (ValueError, TypeError):
                    estado_activo = False
                return estado_activo, "OK"
                
        except Exception as e:
            logger.error(f'Error al verificar estado de producción {id_produccion}: {str(e)}')
            return None, f"Error al verificar estado: {str(e)}"
    
    @staticmethod
    def obtener_estadisticas_dashboard():
        """
        Obtiene estadísticas para el dashboard
        """
        try:
            with connection.cursor() as cursor:
                # Estadísticas generales
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_producciones,
                        SUM(CASE WHEN DATE(pp.fechaentrada) = CURDATE() THEN 1 ELSE 0 END) as producciones_hoy,
                        SUM(CASE WHEN YEARWEEK(pp.fechaentrada, 1) = YEARWEEK(CURDATE(), 1) THEN 1 ELSE 0 END) as producciones_semana,
                        SUM(CASE WHEN YEAR(pp.fechaentrada) = YEAR(CURDATE()) AND MONTH(pp.fechaentrada) = MONTH(CURDATE()) THEN 1 ELSE 0 END) as producciones_mes
                    FROM Productosproduccion pp
                    WHERE pp.estadoregistro = 1
                """)
                
                stats_row = cursor.fetchone()
                stats = {
                    'total_producciones': stats_row[0] or 0,
                    'producciones_hoy': stats_row[1] or 0,
                    'producciones_semana': stats_row[2] or 0,
                    'producciones_mes': stats_row[3] or 0
                }
                
                # Productos más producidos
                cursor.execute("""
                    SELECT 
                        COALESCE(p.nombreproducto, 'Producto no encontrado') as nombre,
                        SUM(dp.cantidad) as total_producido
                    FROM Detalleproduccion dp
                    LEFT JOIN Producto p ON dp.id_producto = p.id_producto
                    JOIN Productosproduccion pp ON dp.id_produccion = pp.idproduccion
                    WHERE pp.estadoregistro = 1
                    GROUP BY p.id_producto, p.nombreproducto
                    HAVING total_producido > 0
                    ORDER BY total_producido DESC
                    LIMIT 5
                """)
                
                productos_top = [(row[0], row[1]) for row in cursor.fetchall()]
                
                # Empleados más productivos
                cursor.execute("""
                    SELECT 
                        CONCAT(
                            COALESCE(per.primernombre, ''), 
                            CASE WHEN per.primernombre IS NOT NULL AND per.primerapellido IS NOT NULL THEN ' ' ELSE '' END,
                            COALESCE(per.primerapellido, '')
                        ) as nombre_completo,
                        COUNT(DISTINCT dp.id_produccion) as total_producciones,
                        SUM(dp.cantidad) as total_unidades
                    FROM Detalleproduccion dp
                    LEFT JOIN Empleado e ON dp.idfabricante = e.idempleado
                    LEFT JOIN Persona per ON e.idpersonaemp = per.cedula
                    JOIN Productosproduccion pp ON dp.id_produccion = pp.idproduccion
                    WHERE pp.estadoregistro = 1 AND (e.estadoempleado = 1 OR e.estadoempleado IS NULL)
                    GROUP BY e.idempleado, nombre_completo
                    HAVING total_unidades > 0
                    ORDER BY total_unidades DESC
                    LIMIT 5
                """)
                
                empleados_top = [(row[0] or 'Empleado no encontrado', row[1], row[2]) for row in cursor.fetchall()]
                
                return {
                    'stats': stats,
                    'productos_top': productos_top,
                    'empleados_top': empleados_top
                }
                
        except Exception as e:
            logger.error(f'Error al obtener estadísticas del dashboard: {str(e)}')
            return {
                'stats': {'total_producciones': 0, 'producciones_hoy': 0, 'producciones_semana': 0, 'producciones_mes': 0},
                'productos_top': [],
                'empleados_top': []
            }