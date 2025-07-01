"""
Servicios para el módulo de ventas
Integración con procedimientos almacenados de MySQL
"""
import json
import logging
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from core_data.models import Venta, Detalleventa, Cliente, Producto, Usuario

logger = logging.getLogger('nexo.ventas')

class VentaService:
    """
    Servicio para manejar operaciones de ventas usando procedimientos almacenados
    """
    
    @staticmethod
    def realizar_venta(id_usuario, id_cliente, detalles):
        """
        Realizar nueva venta usando el procedimiento almacenado RealizarVenta
        """
        try:
            with connection.cursor() as cursor:
                # Convertir detalles a JSON
                detalles_json = json.dumps(detalles)
                
                # Llamar al procedimiento almacenado
                cursor.callproc('RealizarVenta', [
                    id_usuario,
                    id_cliente,
                    detalles_json
                ])
                
                # Obtener el ID de la venta creada
                cursor.execute("SELECT LAST_INSERT_ID()")
                id_venta = cursor.fetchone()[0]
                
                logger.info(f'Venta registrada exitosamente. ID: {id_venta}')
                return id_venta
                
        except Exception as e:
            logger.error(f'Error al realizar venta: {str(e)}')
            raise ValidationError(f'Error al procesar la venta: {str(e)}')


@staticmethod
def editar_venta(id_venta, id_usuario, detalles):
        """
        Editar venta existente usando el procedimiento almacenado EditarVenta
        """
        try:
            with connection.cursor() as cursor:
                # Convertir detalles a JSON
                detalles_json = json.dumps(detalles)
                
                # Llamar al procedimiento almacenado
                cursor.callproc('EditarVenta', [
                    id_venta,
                    id_usuario,
                    detalles_json
                ])
                
                logger.info(f'Venta editada exitosamente. ID: {id_venta}')
                return True
                
        except Exception as e:
            logger.error(f'Error al editar venta {id_venta}: {str(e)}')
            raise ValidationError(f'Error al editar venta: {str(e)}')
    