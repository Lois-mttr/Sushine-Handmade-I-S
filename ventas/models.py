# ventas/models.py
"""
Modelos para el módulo de ventas
Reexporta los modelos necesarios desde core_data
"""

from core_data.models import (
    Venta,  # Usar SIEMPRE este modelo, no el de ventas.models
    Detalleventa,
    Cliente,
    Producto,
    Usuario,
    Persona,
    Ubicacion,
    Categoria
)
from django.utils import timezone
from django.db import connection, transaction, IntegrityError

# Reexportar para uso en el módulo ventas
__all__ = [
    'Venta',
    'Detalleventa', 
    'Cliente',
    'Producto',
    'Usuario',
    'Persona',
    'Ubicacion',
    'Categoria'
]

# Funciones auxiliares para ventas
def obtener_productos_disponibles():
    """
    Obtiene productos disponibles para venta (ubicación sucursal = 2)
    """
    return Producto.objects.filter(
        estado=True,
        idubicacionpro_id=2,  # Sucursal
        existenciaproducto__gt=0
    ).select_related('idcategoriapro')

def obtener_clientes_activos():
    """
    Obtiene clientes activos
    """
    return Cliente.objects.filter(
        estadocliente=True
    ).select_related('idpersonacliente')

def obtener_ventas_del_dia():
    """
    Obtiene ventas realizadas hoy (usando zona horaria local de Django)
    """
    from django.utils import timezone
    hoy = timezone.localdate()
    return Venta.objects.filter(
        fechaventa__date=hoy,
        estado='REALIZADA'
    ).select_related('codcliente__idpersonacliente', 'idusuarioventa')

def calcular_estadisticas_ventas():
    """
    Calcula estadísticas de ventas usando SQL crudo para mayor precisión.
    Retorna un diccionario con ventas_hoy y ventas_ayer (total y cantidad).
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    import logging
    logger = logging.getLogger('nexo.ventas')
    hoy = timezone.localdate()
    ayer = hoy - timedelta(days=1)
    # Convertir fechas a string para SQL (YYYY-MM-DD)
    hoy_str = hoy.strftime('%Y-%m-%d')
    ayer_str = ayer.strftime('%Y-%m-%d')
    resultado = {
        'ventas_hoy': {'total': 0.0, 'cantidad': 0},
        'ventas_ayer': {'total': 0.0, 'cantidad': 0}
    }
    try:
        with connection.cursor() as cursor:
            # Ventas de hoy
            cursor.execute("""
                SELECT COALESCE(SUM(total),0), COUNT(id_venta)
                FROM venta
                WHERE DATE(fechaventa) = %s AND estado = 'REALIZADA' AND total IS NOT NULL
            """, [hoy_str])
            row = cursor.fetchone()
            resultado['ventas_hoy']['total'] = float(row[0]) if row and row[0] is not None else 0.0
            resultado['ventas_hoy']['cantidad'] = int(row[1]) if row and row[1] is not None else 0
            # Ventas de ayer
            cursor.execute("""
                SELECT COALESCE(SUM(total),0), COUNT(id_venta)
                FROM venta
                WHERE DATE(fechaventa) = %s AND estado = 'REALIZADA' AND total IS NOT NULL
            """, [ayer_str])
            row = cursor.fetchone()
            resultado['ventas_ayer']['total'] = float(row[0]) if row and row[0] is not None else 0.0
            resultado['ventas_ayer']['cantidad'] = int(row[1]) if row and row[1] is not None else 0
    except Exception as e:
        logger.error(f'Error SQL al calcular estadísticas de ventas: {str(e)}')
    return resultado

def get_detalleventa_or_404(idventa, idproventa):
    """
    Devuelve una instancia de Detalleventa usando la clave compuesta.
    Lanza Http404 si no existe.
    Uso:
        detalle = get_detalleventa_or_404(idventa, idproventa)
    """
    from django.shortcuts import get_object_or_404
    from core_data.models import Detalleventa
    return get_object_or_404(Detalleventa, idventa=idventa, idproventa=idproventa)

class VentaManager:
    @staticmethod
    def verificar_estado_venta(venta_id):
        """
        Verifica el estado de una venta específica (REALIZADA, ANULADA, etc.) usando SQL crudo.
        Devuelve (estado, mensaje). Si no existe, estado=None.
        """
        import logging
        logger = logging.getLogger('nexo.ventas')
        # Validar el ID antes de consultar
        if not venta_id or str(venta_id).strip() == '':
            logger.warning(f'[ANULAR] ID de venta vacío o None recibido: {venta_id!r}')
            return None, "ID de venta vacío o inválido"
        try:
            venta_id_int = int(venta_id)
        except Exception:
            logger.warning(f'[ANULAR] ID de venta no convertible a int: {venta_id!r}')
            return None, "ID de venta inválido"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT estado FROM venta WHERE id_venta = %s", [venta_id_int])
                row = cursor.fetchone()
                if not row:
                    return None, "Venta no encontrada"
                estado_val = row[0]
                if estado_val is None:
                    return None, "Estado no definido"
                return str(estado_val).strip().upper(), "OK"
        except Exception as e:
            logger.error(f'Error SQL al verificar estado de venta {venta_id}: {str(e)}')
            return None, f"Error al verificar estado: {str(e)}"

    @staticmethod
    def anular(venta_id):
        """
        Anula una venta solo si está REALIZADA. Lanza excepción si no es posible.
        """
        estado, msg = VentaManager.verificar_estado_venta(venta_id)
        if estado is None:
            raise Exception(f"No se puede anular: {msg}")
        if estado != 'REALIZADA':
            raise Exception(f"Solo se pueden anular ventas en estado REALIZADA. Estado actual: {estado}")
        try:
            with connection.cursor() as cursor:
                cursor.callproc('AnularVenta', [int(venta_id)])
        except Exception as e:
            raise Exception(str(e))

    @staticmethod
    def editar(venta_id, usuario_id, detalles_json):
        """
        Edita una venta solo si está REALIZADA. Lanza excepción si no es posible.
        """
        estado, msg = VentaManager.verificar_estado_venta(venta_id)
        if estado is None:
            raise Exception(f"No se puede editar: {msg}")
        if estado != 'REALIZADA':
            raise Exception(f"Solo se pueden editar ventas en estado REALIZADA. Estado actual: {estado}")
        try:
            with connection.cursor() as cursor:
                cursor.callproc('EditarVenta', [int(venta_id), int(usuario_id), detalles_json])
        except Exception as e:
            raise Exception(str(e))

# Monkey patch para acceso fácil desde views
Venta.anular = VentaManager.anular
Venta.editar = VentaManager.editar
Venta.verificar_estado_venta = staticmethod(VentaManager.verificar_estado_venta)
