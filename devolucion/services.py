import json
import logging
from django.db import connection
from django.core.exceptions import ValidationError

logger = logging.getLogger('nexo.devolucion')

class DevolucionService:
    """
    Servicio para manejar operaciones de devolución usando procedimientos almacenados
    """

    @staticmethod
    def registrar_devolucion(id_venta, fecha_devolucion, motivo, detalles):
        try:
            with connection.cursor() as cursor:
                detalles_json = json.dumps(detalles)
                cursor.callproc('RegistrarDevolucion', [
                    id_venta,
                    fecha_devolucion,
                    motivo,
                    detalles_json
                ])

                cursor.execute("SELECT LAST_INSERT_ID()")
                id_devolucion = cursor.fetchone()[0]

                logger.info(f'Devolución registrada exitosamente. ID: {id_devolucion}')
                return id_devolucion

        except Exception as e:
            logger.error(f'Error al registrar devolución: {str(e)}')
            raise ValidationError(f'Error al registrar devolución: {str(e)}')

    @staticmethod
    def editar_devolucion(id_devolucion, nueva_fecha, nuevo_motivo, nuevos_detalles):
        try:
            with connection.cursor() as cursor:
                detalles_json = json.dumps(nuevos_detalles)
                cursor.callproc('EditarDevolucion', [
                    id_devolucion,
                    nueva_fecha,
                    nuevo_motivo,
                    detalles_json
                ])

                logger.info(f'Devolución editada exitosamente. ID: {id_devolucion}')
                return True

        except Exception as e:
            logger.error(f'Error al editar devolución {id_devolucion}: {str(e)}')
            raise ValidationError(f'Error al editar devolución: {str(e)}')

    @staticmethod
    def obtener_lista_devolucion(filtros=None, page=1, per_page=20):
        try:
            query = """
                SELECT 
                    d.idDevolucion,
                    d.fechaDevolucion,
                    d.motivo,
                    u.nombreusuario,
                    COUNT(dd.id_producto) as total_productos,
                    SUM(dd.cantidadDevuelta) as total_cantidad
                FROM Devolucion d
                JOIN Venta v ON d.idVentaDev = v.id_venta
                JOIN Usuario u ON v.idUsuarioVenta = u.idusuario
                LEFT JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                WHERE 1=1
            """

            params = []

            if filtros:
                if filtros.get('fecha_desde'):
                    query += " AND d.fechaDevolucion >= %s"
                    params.append(filtros['fecha_desde'])
                if filtros.get('fecha_hasta'):
                    query += " AND d.fechaDevolucion <= %s"
                    params.append(filtros['fecha_hasta'])
                if filtros.get('usuario'):
                    query += " AND u.nombreusuario LIKE %s"
                    params.append(f"%{filtros['usuario']}%")

            query += """
                GROUP BY d.idDevolucion, d.fechaDevolucion, d.motivo, u.nombreusuario
                ORDER BY d.fechaDevolucion DESC, d.idDevolucion DESC
            """

            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"

            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

                count_query = """
                    SELECT COUNT(DISTINCT d.idDevolucion)
                    FROM Devolucion d
                    JOIN Venta v ON d.idVentaDev = v.id_venta
                    JOIN Usuario u ON v.idUsuarioVenta = u.idusuario
                    WHERE 1=1
                """

                count_params = []
                if filtros:
                    if filtros.get('fecha_desde'):
                        count_query += " AND d.fechaDevolucion >= %s"
                        count_params.append(filtros['fecha_desde'])
                    if filtros.get('fecha_hasta'):
                        count_query += " AND d.fechaDevolucion <= %s"
                        count_params.append(filtros['fecha_hasta'])
                    if filtros.get('usuario'):
                        count_query += " AND u.nombreusuario LIKE %s"
                        count_params.append(f"%{filtros['usuario']}%")

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
            logger.error(f'Error al obtener lista de devoluciones: {str(e)}')
            raise ValidationError(f'Error al obtener lista de devoluciones: {str(e)}')

    @staticmethod
    def obtener_detalle_devolucion(id_devolucion):
        try:
            query = """
                SELECT 
                    d.idDevolucion,
                    d.fechaDevolucion,
                    d.motivo,
                    v.id_venta,
                    u.nombreusuario,
                    dd.id_producto,
                    p.nombreproducto,
                    dd.cantidadDevuelta,
                    p.existenciaProducto
                FROM Devolucion d
                JOIN Venta v ON d.idVentaDev = v.id_venta
                JOIN Usuario u ON v.idUsuarioVenta = u.idusuario
                LEFT JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                LEFT JOIN Producto p ON dd.id_producto = p.id_producto
                WHERE d.idDevolucion = %s
                ORDER BY dd.id_producto
            """

            with connection.cursor() as cursor:
                cursor.execute(query, [id_devolucion])
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                if not rows:
                    return None

                devolucion = {
                    'idDevolucion': rows[0][0],
                    'fechaDevolucion': rows[0][1],
                    'motivo': rows[0][2],
                    'idVentaDev': rows[0][3],
                    'nombreusuario': rows[0][4],
                    'detalles': []
                }

                for row in rows:
                    if row[5]:
                        detalle = {
                            'id_producto': row[5],
                            'nombreproducto': row[6],
                            'cantidadDevuelta': row[7],
                            'existenciaProducto': row[8]
                        }
                        devolucion['detalles'].append(detalle)

                return devolucion

        except Exception as e:
            logger.error(f'Error al obtener detalle de devolución {id_devolucion}: {str(e)}')
            raise ValidationError(f'Error al obtener detalle de devolución: {str(e)}')
