# crud/models.py - Solo importamos y re-exportamos los modelos de core_data
from core_data.models import (
    Productosproduccion,
    Detalleproduccion,
    Producto,
    Usuario,
    Empleado,
    Ubicacion
)

# Re-exportamos para mantener compatibilidad
ProductosProduccion = Productosproduccion
DetalleProduccion = Detalleproduccion
UbicacionProducto = Ubicacion

# Manager personalizado para manejar stored procedures
from django.db import connection
import json

class ProduccionManager:
    @staticmethod
    def registrar_produccion(fechaEntrada, observacion, id_usuario, detalles):
        """
        Registra una nueva producción usando el stored procedure
        detalles debe ser una lista de diccionarios con:
        - id_producto
        - cantidad
        - costo_unitario
        - idFabricante
        """
        try:
            with connection.cursor() as cursor:
                detalles_json = json.dumps(detalles)
                cursor.callproc('RegistrarProduccion', [
                    fechaEntrada,
                    observacion,
                    id_usuario,
                    detalles_json
                ])
                cursor.execute("SELECT LAST_INSERT_ID()")
                id_produccion = cursor.fetchone()[0]
                return True, "Producción registrada exitosamente", id_produccion
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def editar_produccion(idProduccion, fechaEntrada, observacion, id_usuario, detalles):
        """
        Edita una producción existente usando el stored procedure
        """
        try:
            with connection.cursor() as cursor:
                detalles_json = json.dumps(detalles)
                cursor.callproc('EditarProduccion', [
                    idProduccion,
                    fechaEntrada,
                    observacion,
                    id_usuario,
                    detalles_json
                ])
                return True, "Producción editada exitosamente"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def dar_de_baja_produccion(id_produccion):
        """
        Da de baja una producción usando el stored procedure
        """
        try:
            with connection.cursor() as cursor:
                cursor.callproc('DarDeBajaProduccion', [id_produccion])
                return True, "Producción dada de baja exitosamente"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def obtener_producciones_activas():
        """
        Obtiene todas las producciones activas con sus detalles
        CORREGIDO: Usar nombres de columnas correctos
        """
        with connection.cursor() as cursor:
            # Primero verificamos qué columnas existen en la tabla
            cursor.execute("DESCRIBE Productosproduccion")
            columns_info = cursor.fetchall()
            print("Columnas disponibles en Productosproduccion:", [col[0] for col in columns_info])
            
            # Consulta corregida con nombres de columnas probables
            cursor.execute("""
                SELECT 
                    pp.idproduccion,
                    pp.fechaEntrada,
                    pp.observacion,
                    u.nombreusuario,
                    pp.fechaEntrada as fechaEntrada,
                    COUNT(dp.id_produccion) as total_productos,
                    COALESCE(SUM(dp.cantidad), 0) as total_cantidad,
                    COALESCE(SUM(dp.cantidad * dp.costo_unitario), 0) as total_costo
                FROM Productosproduccion pp
                LEFT JOIN Detalleproduccion dp ON pp.idproduccion = dp.id_produccion
                LEFT JOIN Usuario u ON pp.id_usuario = u.idusuario
                WHERE pp.estadoregistro = 1
                GROUP BY pp.idproduccion, pp.fechaEntrada, pp.observacion, u.nombreusuario, pp.fechaEntrada
                ORDER BY pp.fechaEntrada DESC
            """)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    @staticmethod
    def obtener_producciones_activas_simple():
        """
        Versión simplificada sin fechaCreacion si no existe
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pp.idProduccion,
                    pp.fechaEntrada,
                    pp.observacion,
                    u.nombreusuario,
                    COUNT(dp.id_produccion) as total_productos,
                    COALESCE(SUM(dp.cantidad), 0) as total_cantidad,
                    COALESCE(SUM(dp.cantidad * dp.costo_unitario), 0) as total_costo
                FROM Productosproduccion pp
                LEFT JOIN Detalleproduccion dp ON pp.idproduccion = dp.id_produccion
                LEFT JOIN Usuario u ON pp.id_usuario = u.idusuario
                WHERE pp.estadoregistro = 1
                GROUP BY pp.idproduccion, pp.fechaentrada, pp.observacion, u.nombreusuario
                ORDER BY pp.fechaentrada DESC
            """)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    @staticmethod
    def obtener_detalle_produccion(id_produccion):
        """
        Obtiene el detalle completo de una producción
        CORREGIDO: Usar nombres de columnas correctos
        """
        with connection.cursor() as cursor:
            # Primero verificamos las columnas de Detalleproduccion
            cursor.execute("DESCRIBE Detalleproduccion")
            columns_info = cursor.fetchall()
            print("Columnas disponibles en Detalleproduccion:", [col[0] for col in columns_info])
            cursor.execute("""
            SELECT 
                dp.id_produccion,
                dp.id_producto,
                p.nombreProducto,
                dp.cantidad,
                dp.costo_unitario,
                (dp.cantidad * dp.costo_unitario) AS total,
                CONCAT(per.primerNombre, ' ', per.primerApellido) AS nombreFabricante,
                dp.idFabricante
            FROM DetalleProduccion dp
            JOIN Producto p ON dp.id_producto = p.id_producto
            JOIN Empleado e ON dp.idFabricante = e.idEmpleado
            JOIN Persona per ON e.idPersonaEmp = per.cedula
            WHERE dp.id_produccion = %s
            ORDER BY dp.id_producto
            """, [id_produccion])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def verificar_estructura_tablas():
        """
        Método para verificar la estructura de las tablas
        """
        with connection.cursor() as cursor:
            # Verificar Productosproduccion
            cursor.execute("DESCRIBE Productosproduccion")
            produccion_columns = cursor.fetchall()
            
            # Verificar Detalleproduccion
            cursor.execute("DESCRIBE Detalleproduccion")
            detalle_columns = cursor.fetchall()
            
            return {
                'productosproduccion': [col[0] for col in produccion_columns],
                'detalleproduccion': [col[0] for col in detalle_columns]
            }


@staticmethod
def obtener_producciones_todas():
    """
    Obtiene todas las producciones (activas e inactivas) con sus detalles
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                pp.idproduccion,
                pp.fechaEntrada,
                pp.observacion,
                u.nombreusuario,
                COUNT(dp.id_produccion) as total_productos,
                COALESCE(SUM(dp.cantidad), 0) as total_cantidad,
                COALESCE(SUM(dp.cantidad * dp.costo_unitario), 0) as total_costo,
                pp.estadoregistro
            FROM Productosproduccion pp
            LEFT JOIN Detalleproduccion dp ON pp.idproduccion = dp.id_produccion
            LEFT JOIN Usuario u ON pp.id_usuario = u.idusuario
            GROUP BY pp.idproduccion, pp.fechaentrada, pp.observacion, u.nombreusuario, pp.estadoregistro
            ORDER BY pp.fechaentrada DESC
        """)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

@staticmethod
def obtener_producciones_por_estado(activo=True):
    """
    Obtiene producciones por estado (activas o inactivas)
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                pp.idProduccion,
                pp.fechaEntrada,
                pp.observacion,
                u.nombreusuario,
                COUNT(dp.id_produccion) as total_productos,
                COALESCE(SUM(dp.cantidad), 0) as total_cantidad,
                COALESCE(SUM(dp.cantidad * dp.costo_unitario), 0) as total_costo,
                pp.estadoregistro
            FROM Productosproduccion pp
            LEFT JOIN Detalleproduccion dp ON pp.idproduccion = dp.id_produccion
            LEFT JOIN Usuario u ON pp.id_usuario = u.idusuario
            WHERE pp.estadoregistro = %s
            GROUP BY pp.idproduccion, pp.fechaentrada, pp.observacion, u.nombreusuario, pp.estadoregistro
            ORDER BY pp.fechaentrada DESC
        """, [1 if activo else 0])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]