"""
Formularios para el módulo de reportes NEXO
"""
from django import forms
from django.utils import timezone
from core_data.models import Usuario, Cliente, Categoria, Ubicacion
from datetime import date, timedelta

class BaseReportForm(forms.Form):
    """
    Formulario base para todos los reportes
    """
    fecha_desde = forms.DateField(
        required=False,
        label='Fecha Desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label='Fecha Hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    formato_exportacion = forms.ChoiceField(
        choices=[
            ('view', 'Ver en Pantalla'),
            ('pdf', 'Exportar a PDF'),
            ('excel', 'Exportar a Excel'),
        ],
        initial='view',
        label='Formato de Exportación',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fechas por defecto (último mes)
        if not self.initial.get('fecha_hasta'):
            self.initial['fecha_hasta'] = timezone.now().date()
        if not self.initial.get('fecha_desde'):
            self.initial['fecha_desde'] = timezone.now().date() - timedelta(days=30)

class InventarioGeneralForm(BaseReportForm):
    """
    Formulario para reporte de inventario general
    """
    ubicacion = forms.ModelChoiceField(
        queryset=Ubicacion.objects.all(),
        required=False,
        empty_label="Todas las ubicaciones",
        label='Ubicación',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estadocategoria=True),
        required=False,
        empty_label="Todas las categorías",
        label='Categoría',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    stock_bajo = forms.BooleanField(
        required=False,
        label='Solo productos con stock bajo',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary bg-gray-100 border-gray-300 rounded focus:ring-primary focus:ring-2',
        })
    )

class ProduccionForm(BaseReportForm):
    """
    Formulario para reporte de producción
    """
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True, rol='admin'),
        required=False,
        empty_label="Todos los usuarios",
        label='Usuario Responsable',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )

class VentasForm(BaseReportForm):
    """
    Formulario para reporte de ventas
    """
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estadocliente=True),
        required=False,
        empty_label="Todos los clientes",
        label='Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True),
        required=False,
        empty_label="Todos los vendedores",
        label='Vendedor',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('REALIZADA', 'Realizadas'),
            ('ANULADA', 'Anuladas'),
        ],
        required=False,
        label='Estado de Venta',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )

class DevolucionesForm(BaseReportForm):
    """
    Formulario para reporte de devoluciones
    """
    motivo = forms.CharField(
        required=False,
        max_length=100,
        label='Motivo (contiene)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'placeholder': 'Buscar por motivo...'
        })
    )

class ClientesForm(forms.Form):
    """
    Formulario para reporte de clientes
    """
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('1', 'Activos'),
            ('0', 'Inactivos'),
        ],
        required=False,
        label='Estado del Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    formato_exportacion = forms.ChoiceField(
        choices=[
            ('view', 'Ver en Pantalla'),
            ('pdf', 'Exportar a PDF'),
            ('excel', 'Exportar a Excel'),
        ],
        initial='view',
        label='Formato de Exportación',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )

class UsuariosEmpleadosForm(forms.Form):
    """
    Formulario para reporte de usuarios y empleados
    """
    rol = forms.ChoiceField(
        choices=[
            ('', 'Todos los roles'),
            ('admin', 'Administrador'),
            ('encargado_sucursal', 'Encargado de Sucursal'),
            ('vendedor', 'Vendedor'),
        ],
        required=False,
        label='Rol de Usuario',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('1', 'Activos'),
            ('0', 'Inactivos'),
        ],
        required=False,
        label='Estado',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    formato_exportacion = forms.ChoiceField(
        choices=[
            ('view', 'Ver en Pantalla'),
            ('pdf', 'Exportar a PDF'),
            ('excel', 'Exportar a Excel'),
        ],
        initial='view',
        label='Formato de Exportación',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )

class ProductosCategoriaForm(BaseReportForm):
    """
    Formulario para reporte de productos por categoría
    """
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estadocategoria=True),
        required=False,
        empty_label="Todas las categorías",
        label='Categoría',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )

class AuditoriaForm(BaseReportForm):
    """
    Formulario para reporte de auditoría del sistema
    """
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True),
        required=False,
        empty_label="Todos los usuarios",
        label='Usuario',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    accion = forms.ChoiceField(
        choices=[
            ('', 'Todas las acciones'),
            ('CREATE', 'Crear'),
            ('UPDATE', 'Actualizar'),
            ('DELETE', 'Eliminar'),
            ('LOGIN', 'Iniciar Sesión'),
            ('LOGOUT', 'Cerrar Sesión'),
        ],
        required=False,
        label='Tipo de Acción',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
    
    modulo = forms.ChoiceField(
        choices=[
            ('', 'Todos los módulos'),
            ('inventario', 'Inventario'),
            ('produccion', 'Producción'),
            ('ventas', 'Ventas'),
            ('devoluciones', 'Devoluciones'),
            ('clientes', 'Clientes'),
            ('usuarios', 'Usuarios'),
            ('reportes', 'Reportes'),
        ],
        required=False,
        label='Módulo',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
        })
    )
