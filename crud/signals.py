from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='core_data.Productosproduccion')
def invalidate_production_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica una producción"""
    cache.delete_many([
        'dashboard_stats_production',
        'production_list_cache',
        f'production_detail_{instance.idproduccion}'
    ])
    logger.info(f"Cache invalidado para producción {instance.idproduccion}")

@receiver(post_save, sender='core_data.Venta')
def invalidate_sales_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica una venta"""
    cache.delete_many([
        'dashboard_stats_sales',
        'sales_list_cache',
        f'sales_detail_{instance.id_venta}'
    ])
    logger.info(f"Cache invalidado para venta {instance.id_venta}")

@receiver(post_save, sender='core_data.Cliente')
def invalidate_clients_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica un cliente"""
    cache.delete_many([
        'clients_list_cache',
        f'client_detail_{instance.idcliente}'
    ])
    logger.info(f"Cache invalidado para cliente {instance.idcliente}")
