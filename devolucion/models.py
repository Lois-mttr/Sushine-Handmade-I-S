from django.db import connection, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from core_data.models import (
    Devolucion,
    Detalledevolucion,
    Producto,
    Venta,
    Usuario
)
import json
import logging
from datetime import datetime, date

logger = logging.getLogger('nexo.devolucion')

class DevolucionManager:
    """
    Manager para operaciones de devoluciones con validaciones y manejo robusto de errores
    """

    @staticmethod
    def tiene_columna_usuario_registrador():
        try:
            with connection.cursor() as cursor:
                columnas = {
                    columna.name
                    for columna in connection.introspection.get_table_description(cursor, 'Devolucion')
                }
            return 'idUsuarioDev' in columnas
        except Exception as e:
            logger.warning(f'No se pudo verificar columna idUsuarioDev: {str(e)}')
            return False

    @staticmethod
    def registrar_devolucion(id_venta, fecha_devolucion, motivo, detalles, id_usuario=None):
        try:
            if isinstance(fecha_devolucion, date) and not isinstance(fecha_devolucion, datetime):
                fecha_datetime = timezone.make_aware(datetime.combine(fecha_devolucion, datetime.min.time()))
            elif isinstance(fecha_devolucion, datetime):
                fecha_datetime = timezone.make_aware(fecha_devolucion) if timezone.is_naive(fecha_devolucion) else fecha_devolucion
            else:
                fecha_datetime = fecha_devolucion

            detalles_json = json.dumps(detalles, default=str)

            with connection.cursor() as cursor:
                cursor.callproc('RegistrarDevolucion', [
                    id_venta,
                    fecha_datetime,
                    motivo or '',
                    detalles_json
                ])
                cursor.execute("SELECT LAST_INSERT_ID()")
                result = cursor.fetchone()
                id_devolucion = result[0] if result else None

                if id_devolucion and id_devolucion > 0:
                    if id_usuario and DevolucionManager.tiene_columna_usuario_registrador():
                        cursor.execute(
                            "UPDATE Devolucion SET idUsuarioDev = %s WHERE idDevolucion = %s",
                            [id_usuario, id_devolucion]
                        )
                    logger.info(f'Devolución registrada exitosamente. ID: {id_devolucion}')
                    return True, f"Devolución #{id_devolucion} registrada exitosamente", id_devolucion
                else:
                    return False, "Error al obtener ID de la devolución creada", None

        except Exception as e:
            logger.error(f'Error al registrar devolución: {str(e)}')
            return False, f"Error al registrar devolución: {str(e)}", None

    @staticmethod
    def editar_devolucion(id_devolucion, nueva_fecha, nuevo_motivo, nuevos_detalles):
        try:
            detalles_json = json.dumps(nuevos_detalles)
            with connection.cursor() as cursor:
                cursor.callproc('EditarDevolucion', [
                    id_devolucion,
                    nueva_fecha,
                    nuevo_motivo or '',
                    detalles_json
                ])
            return True, "Devolución actualizada correctamente"
        except Exception as e:
            logger.error(f"Error al editar devolución: {str(e)}")
            if "Duplicate entry" in str(e):
                return False, "No se puede agregar productos duplicados"
            return False, f"Error al editar devolución: {str(e)}"

    @staticmethod
    def obtener_devoluciones_con_filtros(filtros=None, page=1, per_page=10):
        try:
            with connection.cursor() as cursor:
                tiene_usuario_registrador = DevolucionManager.tiene_columna_usuario_registrador()
                persona_select = "COALESCE(ureg.nombreUsuario, u.nombreUsuario)" if tiene_usuario_registrador else "u.nombreUsuario"
                persona_id_select = "COALESCE(ureg.idUsuario, u.idUsuario)" if tiene_usuario_registrador else "u.idUsuario"
                usuario_join = "LEFT JOIN Usuario ureg ON d.idUsuarioDev = ureg.idusuario" if tiene_usuario_registrador else ""

                base_query = """
                    SELECT 
                        d.idDevolucion,
                        d.fechaDevolucion,
                        d.motivo,
                        d.idVentaDev,
                        {persona_select} AS persona,
                        GROUP_CONCAT(DISTINCT dd.id_producto ORDER BY dd.id_producto SEPARATOR ', ') AS productos,
                        COALESCE(SUM(dd.cantidadDevuelta), 0) AS cantidadDevuelta
                    FROM Devolucion d
                    LEFT JOIN DetalleDevolucion dd ON d.idDevolucion = dd.id_devolucion
                    JOIN Venta v ON d.idVentaDev = v.id_venta
                    JOIN Usuario u ON v.idUsuarioVenta = u.idusuario
                    {usuario_join}
                    WHERE 1=1
                """.format(persona_select=persona_select, usuario_join=usuario_join)

                count_query = """
                    SELECT COUNT(DISTINCT d.idDevolucion)
                    FROM Devolucion d
                    JOIN Venta v ON d.idVentaDev = v.id_venta
                    JOIN Usuario u ON v.idUsuarioVenta = u.idusuario
                    {usuario_join}
                    WHERE 1=1
                """.format(usuario_join=usuario_join)

                params = []
                count_params = []

                if filtros:
                    if filtros.get('fecha_desde'):
                        base_query += " AND DATE(d.fechaDevolucion) >= %s"
                        count_query += " AND DATE(d.fechaDevolucion) >= %s"
                        params.append(filtros['fecha_desde'])
                        count_params.append(filtros['fecha_desde'])

                    if filtros.get('fecha_hasta'):
                        base_query += " AND DATE(d.fechaDevolucion) <= %s"
                        count_query += " AND DATE(d.fechaDevolucion) <= %s"
                        params.append(filtros['fecha_hasta'])
                        count_params.append(filtros['fecha_hasta'])

                    if filtros.get('persona_id'):
                        base_query += f" AND {persona_id_select} = %s"
                        count_query += f" AND {persona_id_select} = %s"
                        params.append(filtros['persona_id'])
                        count_params.append(filtros['persona_id'])

                base_query += f"""
                    GROUP BY d.idDevolucion, d.fechaDevolucion, d.motivo, d.idVentaDev, {persona_select}
                    ORDER BY d.fechaDevolucion DESC, d.idDevolucion DESC
                """

                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]

                offset = (page - 1) * per_page
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

                base_query += " LIMIT %s OFFSET %s"
                params.extend([per_page, offset])

                cursor.execute(base_query, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

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
            logger.error(f'Error al obtener devoluciones con filtros: {str(e)}')
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
    def obtener_detalle_devolucion(id_devolucion):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        dd.id_producto,
                        dd.cantidadDevuelta
                    FROM DetalleDevolucion dd
                    WHERE dd.id_devolucion = %s
                    ORDER BY dd.id_producto
                """, [id_devolucion])

                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f'Error al obtener detalle de devolucion {id_devolucion}: {str(e)}')
            return []

    @staticmethod
    def anular_devolucion(id_devolucion):
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id_producto, cantidadDevuelta
                        FROM DetalleDevolucion
                        WHERE id_devolucion = %s
                    """, [id_devolucion])
                    detalles = cursor.fetchall()

                    cursor.execute(
                        "SELECT idVentaDev FROM Devolucion WHERE idDevolucion = %s",
                        [id_devolucion]
                    )
                    row = cursor.fetchone()
                    if not row:
                        return False, "La devolucion no existe."

                    id_venta = row[0]

                    for id_producto, cantidad in detalles:
                        cursor.execute("""
                            UPDATE Producto
                            SET existenciaProducto = GREATEST(existenciaProducto - %s, 0)
                            WHERE id_producto = %s
                              AND idUbicacionPro = 2
                        """, [cantidad, id_producto])

                    cursor.execute(
                        "DELETE FROM DetalleDevolucion WHERE id_devolucion = %s",
                        [id_devolucion]
                    )
                    cursor.execute(
                        "DELETE FROM Devolucion WHERE idDevolucion = %s",
                        [id_devolucion]
                    )
                    cursor.execute(
                        "UPDATE Venta SET estado = 'REALIZADA' WHERE id_venta = %s",
                        [id_venta]
                    )

            return True, "Devolucion anulada correctamente."
        except Exception as e:
            logger.error(f'Error al anular devolucion {id_devolucion}: {str(e)}')
            return False, f"Error al anular devolucion: {str(e)}"

