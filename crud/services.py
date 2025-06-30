"""
Servicios para el módulo de producción
Integración con procedimientos almacenados de MySQL
"""
import json
import logging
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from core_data.models import Productosproduccion, Detalleproduccion, Producto, Empleado, Usuario

logger = logging.getLogger('nexo.produccion')

class ProduccionService:
    """
    Servicio para manejar operaciones de producción usando procedimientos almacenados
    """
    
    @staticmethod
    def registrar_produccion(fecha_entrada, observacion, id_usuario, detalles):
        """
        Registrar nueva producción usando el procedimiento almacenado
        """
        try:
            with connection.cursor() as cursor:
                # Convertir detalles a JSON
                detalles_json = json.dumps(detalles)
                
                # Llamar al procedimiento almacenado
                cursor.callproc('RegistrarProduccion', [
                    fecha_entrada,
                    observacion,
                    id_usuario,
                    detalles_json
                ])
                
                # Obtener el ID de la producción creada
                cursor.execute("SELECT LAST_INSERT_ID()")
                id_produccion = cursor.fetchone()[0]
                
                logger.info(f'Producción registrada exitosamente. ID: {id_produccion}')
                return id_produccion
                
        except Exception as e:
            logger.error(f'Error al registrar producción: {str(e)}')
            raise ValidationError(f'Error al registrar producción: {str(e)}')
    
    @staticmethod
    def editar_produccion(id_produccion, fecha_entrada, observacion, id_usuario, detalles):
        """
        Editar producción existente usando el procedimiento almacenado
        """
        try:
            with connection.cursor() as cursor:
                # Convertir detalles a JSON
                detalles_json = json.dumps(detalles)
                
                # Llamar al procedimiento almacenado
                cursor.callproc('EditarProduccion', [
                    id_produccion,
                    fecha_entrada,
                    observacion,
                    id_usuario,
                    detalles_json
                ])
                
                logger.info(f'Producción editada exitosamente. ID: {id_produccion}')
                return True
                
        except Exception as e:
            logger.error(f'Error al editar producción {id_produccion}: {str(e)}')
            raise ValidationError(f'Error al editar producción: {str(e)}')
    
    @staticmethod
    def dar_baja_produccion(id_produccion):
        """
        Dar de baja producción usando el procedimiento almacenado
        """
        try:
            with connection.cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('DarDeBajaProduccion', [id_produccion])
                
                logger.info(f'Producción dada de baja exitosamente. ID: {id_produccion}')
                return True
                
        except Exception as e:
            logger.error(f'Error al dar de baja producción {id_produccion}: {str(e)}')
            raise ValidationError(f'Error al dar de baja producción: {str(e)}')
    
    @staticmethod
    def obtener_lista_produccion(filtros=None, page=1, per_page=20):
        """
        Obtener lista paginada de producciones con filtros
        """
        try:
            query = """
                SELECT 
                    pp.idProduccion,
                    pp.fechaEntrada,
                    pp.observacion,
                    pp.EstadoRegistro,
                    u.nombreUsuario,
                    COUNT(dp.id_producto) as total_productos,
                    SUM(dp.cantidad) as total_cantidad,
                    SUM(dp.cantidad * dp.costo_unitario) as total_costo
                FROM ProductosProduccion pp
                LEFT JOIN Usuario u ON pp.id_usuario = u.idUsuario
                LEFT JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if filtros:
                if filtros.get('fecha_desde'):
                    query += " AND pp.fechaEntrada >= %s"
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    query += " AND pp.fechaEntrada <= %s"
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('usuario'):
                    query += " AND u.nombreUsuario LIKE %s"
                    params.append(f"%{filtros['usuario']}%")
                
                if filtros.get('estado') is not None and filtros['estado'] != '':
                    query += " AND pp.EstadoRegistro = %s"
                    params.append(int(filtros['estado']))
            
            query += """
                GROUP BY pp.idProduccion, pp.fechaEntrada, pp.observacion, 
                         pp.EstadoRegistro, u.nombreUsuario
                ORDER BY pp.fechaEntrada DESC, pp.idProduccion DESC
            """
            
            # Calcular offset para paginación
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"
            
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Contar total de registros para paginación
                count_query = """
                    SELECT COUNT(DISTINCT pp.idProduccion)
                    FROM ProductosProduccion pp
                    LEFT JOIN Usuario u ON pp.id_usuario = u.idUsuario
                    WHERE 1=1
                """
                
                count_params = []
                if filtros:
                    if filtros.get('fecha_desde'):
                        count_query += " AND pp.fechaEntrada >= %s"
                        count_params.append(filtros['fecha_desde'])
                    
                    if filtros.get('fecha_hasta'):
                        count_query += " AND pp.fechaEntrada <= %s"
                        count_params.append(filtros['fecha_hasta'])
                    
                    if filtros.get('usuario'):
                        count_query += " AND u.nombreUsuario LIKE %s"
                        count_params.append(f"%{filtros['usuario']}%")
                    
                    if filtros.get('estado') is not None and filtros['estado'] != '':
                        count_query += " AND pp.EstadoRegistro = %s"
                        count_params.append(int(filtros['estado']))
                
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
                
                return {
                    'results': results,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
                
        except Exception as e:
            logger.error(f'Error al obtener lista de producción: {str(e)}')
            raise ValidationError(f'Error al obtener lista de producción: {str(e)}')
    
    @staticmethod
    def obtener_detalle_produccion(id_produccion):
        """
        Obtener detalle completo de una producción
        """
        try:
            query = """
                SELECT 
                    pp.idProduccion,
                    pp.fechaEntrada,
                    pp.observacion,
                    pp.EstadoRegistro,
                    u.nombreUsuario,
                    u.idUsuario,
                    dp.id_producto,
                    p.nombreProducto,
                    dp.cantidad,
                    dp.costo_unitario,
                    dp.idFabricante,
                    e.nombreEmpleado,
                    (dp.cantidad * dp.costo_unitario) as subtotal
                FROM ProductosProduccion pp
                LEFT JOIN Usuario u ON pp.id_usuario = u.idUsuario
                LEFT JOIN DetalleProduccion dp ON pp.idProduccion = dp.id_produccion
                LEFT JOIN Producto p ON dp.id_producto = p.id_producto AND p.idUbicacionPro = 1
                LEFT JOIN Empleado e ON dp.idFabricante = e.idEmpleado
                WHERE pp.idProduccion = %s
                ORDER BY dp.id_producto
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, [id_produccion])
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                if not rows:
                    return None
                
                # Organizar datos
                produccion = {
                    'idProduccion': rows[0][0],
                    'fechaEntrada': rows[0][1],
                    'observacion': rows[0][2],
                    'EstadoRegistro': rows[0][3],
                    'nombreUsuario': rows[0][4],
                    'idUsuario': rows[0][5],
                    'detalles': []
                }
                
                total_costo = 0
                for row in rows:
                    if row[6]:  # Si hay id_producto
                        detalle = {
                            'id_producto': row[6],
                            'nombreProducto': row[7],
                            'cantidad': row[8],
                            'costo_unitario': row[9],
                            'idFabricante': row[10],
                            'nombreEmpleado': row[11],
                            'subtotal': row[12]
                        }
                        produccion['detalles'].append(detalle)
                        total_costo += row[12] if row[12] else 0
                
                produccion['total_costo'] = total_costo
                return produccion
                
        except Exception as e:
            logger.error(f'Error al obtener detalle de producción {id_produccion}: {str(e)}')
            raise ValidationError(f'Error al obtener detalle de producción: {str(e)}')
