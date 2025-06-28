"""
Modelos para el módulo de inventario
Reexporta los modelos necesarios desde core_data para mantener la organización
"""

# Importar modelos desde core_data
from core_data.models import (
    Producto,
    Ubicacion, 
    Categoria,
    Usuario,
    Empleado,
    Persona,
    Cliente,
    Venta,
    Detalleventa,
    Devolucion,
    Detalledevolucion,
    Productosproduccion,
    Detalleproduccion
)

# Reexportar para uso en el módulo inventario
__all__ = [
    'Producto',
    'Ubicacion',
    'Categoria', 
    'Usuario',
    'Empleado',
    'Persona',
    'Cliente',
    'Venta',
    'Detalleventa',
    'Devolucion',
    'Detalledevolucion',
    'Productosproduccion',
    'Detalleproduccion'
]

# Funciones auxiliares para el inventario
def obtener_productos_activos():
    """
    Obtiene todos los productos activos
    """
    return Producto.objects.filter(estado=True)

def obtener_productos_por_ubicacion(ubicacion_id):
    """
    Obtiene productos de una ubicación específica
    """
    return Producto.objects.filter(
        idubicacionpro_id=ubicacion_id,
        estado=True
    ).select_related('idcategoriapro', 'idubicacionpro')

def obtener_productos_bajo_stock():
    """
    Obtiene productos que necesitan reposición
    """
    from django.db.models import F
    return Producto.objects.filter(
        estado=True,
        existenciaproducto__lte=F('existenciaminima')
    )

def obtener_estadisticas_inventario(ubicacion_id=None):
    """
    Obtiene estadísticas generales del inventario
    """
    from django.db.models import Count, Sum, F
    
    productos = Producto.objects.filter(estado=True)
    
    if ubicacion_id:
        productos = productos.filter(idubicacionpro_id=ubicacion_id)
    
    stats = {
        'total_productos': productos.count(),
        'productos_bajo_stock': productos.filter(
            existenciaproducto__lte=F('existenciaminima')
        ).count(),
        'productos_sin_stock': productos.filter(existenciaproducto=0).count(),
        'valor_total_inventario': productos.aggregate(
            total=Sum(F('existenciaproducto') * F('precioproducto'))
        )['total'] or 0,
        'productos_por_categoria': productos.values(
            'idcategoriapro__nombrecategoria'
        ).annotate(
            cantidad=Count('id_producto'),
            existencia_total=Sum('existenciaproducto')
        ).order_by('-cantidad')[:5]
    }
    
    return stats

def obtener_ubicaciones_con_productos():
    """
    Obtiene ubicaciones que tienen productos
    """
    return Ubicacion.objects.filter(
        producto__estado=True
    ).distinct().order_by('nombreubicacion')

def obtener_categorias_activas():
    """
    Obtiene todas las categorías activas (no solo las que tienen productos)
    """
    return Categoria.objects.filter(estadocategoria=True).order_by('nombrecategoria')