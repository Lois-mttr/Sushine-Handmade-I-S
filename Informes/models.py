

# Create your models here.
"""
Modelos para el módulo de reportes NEXO
"""
from django.db import models
from django.utils import timezone
from core_data.models import Usuario

class ReportLog(models.Model):
    """
    Modelo para registrar la generación de reportes (auditoría)
    """
    REPORT_TYPES = [
        ('inventario_general', 'Inventario General'),
        ('produccion', 'Producción'),
        ('reabastecimientos', 'Reabastecimientos a Sucursal'),
        ('ventas', 'Ventas'),
        ('devoluciones', 'Devoluciones'),
        ('clientes', 'Clientes'),
        ('usuarios_empleados', 'Usuarios y Empleados'),
        ('productos_categoria', 'Productos por Categoría'),
        ('auditoria_sistema', 'Actividad del Sistema'),
    ]
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('view', 'Vista en Pantalla'),
    ]
    
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario'
    )
    tipo_reporte = models.CharField(max_length=50, choices=REPORT_TYPES)
    formato_exportacion = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    filtros_aplicados = models.JSONField(default=dict, blank=True)
    fecha_generacion = models.DateTimeField(default=timezone.now)
    total_registros = models.IntegerField(default=0)
    tiempo_generacion = models.FloatField(default=0.0)  # en segundos
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'report_log'
        verbose_name = 'Log de Reporte'
        verbose_name_plural = 'Logs de Reportes'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        fecha_local = timezone.localtime(self.fecha_generacion)
        return f"{self.get_tipo_reporte_display()} - {self.usuario.nombreusuario} - {fecha_local.strftime('%d/%m/%Y %I:%M %p')}"

class SystemActivity(models.Model):
    """
    Modelo para registrar actividades del sistema (auditoría)
    """
    ACTION_TYPES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('LOGIN', 'Iniciar Sesión'),
        ('LOGOUT', 'Cerrar Sesión'),
        ('EXPORT', 'Exportar'),
        ('IMPORT', 'Importar'),
        ('VIEW', 'Ver'),
    ]
    
    MODULE_TYPES = [
        ('inventario', 'Inventario'),
        ('produccion', 'Producción'),
        ('ventas', 'Ventas'),
        ('devoluciones', 'Devoluciones'),
        ('clientes', 'Clientes'),
        ('usuarios', 'Usuarios'),
        ('reportes', 'Reportes'),
        ('sistema', 'Sistema'),
    ]
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='idUsuario'
    )
    accion = models.CharField(max_length=20, choices=ACTION_TYPES)
    modulo = models.CharField(max_length=20, choices=MODULE_TYPES)
    descripcion = models.TextField()
    objeto_id = models.CharField(max_length=50, null=True, blank=True)
    datos_anteriores = models.JSONField(default=dict, blank=True)
    datos_nuevos = models.JSONField(default=dict, blank=True)
    fecha_actividad = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_activity'
        verbose_name = 'Actividad del Sistema'
        verbose_name_plural = 'Actividades del Sistema'
        ordering = ['-fecha_actividad']
    
    def __str__(self):
        usuario_str = self.usuario.nombreusuario if self.usuario else 'Sistema'
        fecha_local = timezone.localtime(self.fecha_actividad)
        return f"{usuario_str} - {self.get_accion_display()} - {self.get_modulo_display()} - {fecha_local.strftime('%d/%m/%Y %I:%M %p')}"
