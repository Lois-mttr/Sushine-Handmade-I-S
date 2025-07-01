"""
Formularios mejorados para el módulo de reportes NEXO con validaciones avanzadas
"""
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from core_data.models import Usuario, Cliente, Categoria, Ubicacion
from datetime import date, timedelta
import re

class BaseReportForm(forms.Form):
    """
    Formulario base mejorado para todos los reportes con validaciones
    """
    fecha_desde = forms.DateField(
        required=False,
        label='Fecha Desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'max': timezone.now().date().isoformat(),
        }),
        help_text='Fecha de inicio del período a consultar'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label='Fecha Hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'max': timezone.now().date().isoformat(),
        }),
        help_text='Fecha de fin del período a consultar'
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
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fechas por defecto (último mes)
        if not self.initial.get('fecha_hasta'):
            self.initial['fecha_hasta'] = timezone.now().date()
        if not self.initial.get('fecha_desde'):
            self.initial['fecha_desde'] = timezone.now().date() - timedelta(days=30)
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha desde no puede ser mayor que la fecha hasta.')
            
            # Validar que no sea un rango muy amplio (más de 2 años)
            if (fecha_hasta - fecha_desde).days > 730:
                raise ValidationError('El rango de fechas no puede ser mayor a 2 años.')
            
            # Validar que las fechas no sean futuras
            if fecha_desde > timezone.now().date():
                raise ValidationError('La fecha desde no puede ser futura.')
            
            if fecha_hasta > timezone.now().date():
                raise ValidationError('La fecha hasta no puede ser futura.')
        
        return cleaned_data

class InventarioGeneralForm(BaseReportForm):
    """
    Formulario mejorado para reporte de inventario general
    """
    ubicacion = forms.ModelChoiceField(
        queryset=Ubicacion.objects.all(),
        required=False,
        empty_label="🏢 Todas las ubicaciones",
        label='Ubicación',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por ubicación específica'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estadocategoria=True),
        required=False,
        empty_label="🏷️ Todas las categorías",
        label='Categoría',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por categoría de producto'
    )
    
    stock_estado = forms.ChoiceField(
        choices=[
            ('', '📊 Todos los estados'),
            ('sin_stock', '🔴 Sin Stock'),
            ('critico', '🟠 Stock Crítico'),
            ('bajo', '🟡 Stock Bajo'),
            ('normal', '🟢 Stock Normal'),
            ('alto', '🔵 Stock Alto'),
        ],
        required=False,
        label='Estado de Stock',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por nivel de stock'
    )
    
    buscar = forms.CharField(
        required=False,
        max_length=100,
        label='Buscar Producto',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por nombre o descripción...',
            'autocomplete': 'off'
        }),
        help_text='Buscar productos por nombre o descripción'
    )
    
    def clean_buscar(self):
        buscar = self.cleaned_data.get('buscar')
        if buscar:
            # Validar que no contenga caracteres especiales peligrosos
            if re.search(r'[<>"\';]', buscar):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            
            # Validar longitud mínima
            if len(buscar.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        
        return buscar.strip() if buscar else None

class VentasForm(BaseReportForm):
    """
    Formulario mejorado para reporte de ventas
    """
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estadocliente=True),
        required=False,
        empty_label="👥 Todos los clientes",
        label='Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por cliente específico'
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True),
        required=False,
        empty_label="👨‍💼 Todos los vendedores",
        label='Vendedor',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por vendedor específico'
    )
    
    estado = forms.ChoiceField(
        choices=[
            ('', '📋 Todos los estados'),
            ('REALIZADA', '✅ Realizadas'),
            ('ANULADA', '❌ Anuladas'),
            ('PENDIENTE', '⏳ Pendientes'),
        ],
        required=False,
        label='Estado de Venta',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por estado de la venta'
    )
    
    monto_minimo = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label='Monto Mínimo',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '💰 Monto mínimo...',
            'step': '0.01',
            'min': '0'
        }),
        help_text='Filtrar ventas con monto mayor o igual'
    )
    
    monto_maximo = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label='Monto Máximo',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '💰 Monto máximo...',
            'step': '0.01',
            'min': '0'
        }),
        help_text='Filtrar ventas con monto menor o igual'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        monto_minimo = cleaned_data.get('monto_minimo')
        monto_maximo = cleaned_data.get('monto_maximo')
        
        if monto_minimo and monto_maximo:
            if monto_minimo > monto_maximo:
                raise ValidationError('El monto mínimo no puede ser mayor que el monto máximo.')
        
        return cleaned_data

class ProduccionForm(BaseReportForm):
    """
    Formulario mejorado para reporte de producción
    """
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True, rol__in=['admin', 'encargado_sucursal']),
        required=False,
        empty_label="👨‍💼 Todos los usuarios",
        label='Usuario Responsable',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Usuario que registró la producción'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estadocategoria=True),
        required=False,
        empty_label="🏷️ Todas las categorías",
        label='Categoría de Producto',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por categoría de productos producidos'
    )

class ClientesForm(forms.Form):
    """
    Formulario mejorado para reporte de clientes
    """
    estado = forms.ChoiceField(
        choices=[
            ('', '📊 Todos los estados'),
            ('1', '✅ Activos'),
            ('0', '❌ Inactivos'),
        ],
        required=False,
        label='Estado del Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por estado del cliente'
    )
    
    categoria_cliente = forms.ChoiceField(
        choices=[
            ('', '👥 Todas las categorías'),
            ('ACTIVO', '🟢 Activos (compras recientes)'),
            ('REGULAR', '🟡 Regulares (compras frecuentes)'),
            ('OCASIONAL', '🟠 Ocasionales (compras esporádicas)'),
            ('PERDIDO', '🔴 Perdidos (sin compras recientes)'),
            ('INACTIVO', '⚫ Inactivos (sin compras)'),
        ],
        required=False,
        label='Categoría de Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por comportamiento de compra'
    )
    
    nivel_cliente = forms.ChoiceField(
        choices=[
            ('', '💎 Todos los niveles'),
            ('VIP', '💎 VIP (>C$10,000)'),
            ('PREMIUM', '🥇 Premium (C$5,000-C$10,000)'),
            ('REGULAR', '🥈 Regular (C$1,000-C$5,000)'),
            ('NUEVO', '🥉 Nuevo (<C$1,000)'),
        ],
        required=False,
        label='Nivel de Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por nivel de gasto'
    )
    
    buscar = forms.CharField(
        required=False,
        max_length=100,
        label='Buscar Cliente',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por nombre, cédula o correo...',
            'autocomplete': 'off'
        }),
        help_text='Buscar clientes por nombre, cédula o correo'
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
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        })
    )
    
    def clean_buscar(self):
        buscar = self.cleaned_data.get('buscar')
        if buscar:
            # Validar que no contenga caracteres especiales peligrosos
            if re.search(r'[<>"\';]', buscar):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            
            # Validar longitud mínima
            if len(buscar.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        
        return buscar.strip() if buscar else None

class DevolucionesForm(BaseReportForm):
    """
    Formulario mejorado para reporte de devoluciones
    """
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estadocliente=True),
        required=False,
        empty_label="👥 Todos los clientes",
        label='Cliente',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por cliente que realizó la devolución'
    )

    producto = forms.CharField(
        required=False,
        max_length=100,
        label='Producto',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por nombre de producto...',
            'autocomplete': 'off'
        }),
        help_text='Buscar devoluciones por producto'
    )

    estado = forms.ChoiceField(
        choices=[
            ('', '📋 Todos los estados'),
            ('APROBADA', '✅ Aprobadas'),
            ('RECHAZADA', '❌ Rechazadas'),
            ('PENDIENTE', '⏳ Pendientes'),
        ],
        required=False,
        label='Estado de Devolución',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por estado de la devolución'
    )

    def clean_producto(self):
        producto = self.cleaned_data.get('producto')
        if producto:
            import re
            if re.search(r'[<>"\';]', producto):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            if len(producto.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        return producto.strip() if producto else None

class UsuariosEmpleadosForm(BaseReportForm):
    """
    Formulario mejorado para reporte de usuarios/empleados
    """
    rol = forms.ChoiceField(
        choices=[
            ('', '👤 Todos los roles'),
            ('admin', '🛡️ Administrador'),
            ('encargado_sucursal', '🏢 Encargado de Sucursal'),
            ('Obrero', '🔧 Obrero'),
        ],
        required=False,
        label='Rol',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por rol del usuario'
    )

    activo = forms.ChoiceField(
        choices=[
            ('', '📊 Todos'),
            ('1', '✅ Activos'),
            ('0', '❌ Inactivos'),
        ],
        required=False,
        label='Estado',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por estado del usuario'
    )

    buscar = forms.CharField(
        required=False,
        max_length=100,
        label='Buscar Usuario',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por nombre o usuario...',
            'autocomplete': 'off'
        }),
        help_text='Buscar usuarios por nombre o usuario'
    )

    def clean_buscar(self):
        buscar = self.cleaned_data.get('buscar')
        if buscar:
            import re
            if re.search(r'[<>"\';]', buscar):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            if len(buscar.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        return buscar.strip() if buscar else None

class ProductosCategoriaForm(BaseReportForm):
    """
    Formulario mejorado para reporte de productos por categoría
    """
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estadocategoria=True),
        required=False,
        empty_label="🏷️ Todas las categorías",
        label='Categoría',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar productos por categoría'
    )

    estado = forms.ChoiceField(
        choices=[
            ('', '📊 Todos los estados'),
            ('1', '✅ Activos'),
            ('0', '❌ Inactivos'),
        ],
        required=False,
        label='Estado del Producto',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar productos por estado'
    )

    buscar = forms.CharField(
        required=False,
        max_length=100,
        label='Buscar Producto',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por nombre o descripción...',
            'autocomplete': 'off'
        }),
        help_text='Buscar productos por nombre o descripción'
    )

    def clean_buscar(self):
        buscar = self.cleaned_data.get('buscar')
        if buscar:
            if re.search(r'[<>"\';]', buscar):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            if len(buscar.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        return buscar.strip() if buscar else None

class AuditoriaForm(BaseReportForm):
    """
    Formulario mejorado para reporte de auditoría
    """
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(activo=True),
        required=False,
        empty_label="👤 Todos los usuarios",
        label='Usuario',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
        }),
        help_text='Filtrar por usuario que realizó la acción'
    )

    accion = forms.CharField(
        required=False,
        max_length=100,
        label='Acción',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por tipo de acción...',
            'autocomplete': 'off'
        }),
        help_text='Buscar por tipo de acción (crear, editar, eliminar, etc.)'
    )

    modulo = forms.CharField(
        required=False,
        max_length=100,
        label='Módulo',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por módulo...',
            'autocomplete': 'off'
        }),
        help_text='Buscar por módulo o sección del sistema'
    )

    ip_address = forms.CharField(
        required=False,
        max_length=45,
        label='IP',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 bg-white',
            'placeholder': '🔍 Buscar por IP...',
            'autocomplete': 'off'
        }),
        help_text='Buscar por dirección IP'
    )

    def clean_accion(self):
        accion = self.cleaned_data.get('accion')
        if accion:
            if re.search(r'[<>"\';]', accion):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            if len(accion.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        return accion.strip() if accion else None

    def clean_modulo(self):
        modulo = self.cleaned_data.get('modulo')
        if modulo:
            if re.search(r'[<>"\';]', modulo):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            if len(modulo.strip()) < 2:
                raise ValidationError('El término de búsqueda debe tener al menos 2 caracteres.')
        return modulo.strip() if modulo else None

    def clean_ip_address(self):
        ip = self.cleaned_data.get('ip_address')
        if ip:
            if re.search(r'[<>"\';]', ip):
                raise ValidationError('El término de búsqueda contiene caracteres no permitidos.')
            if len(ip.strip()) < 4:
                raise ValidationError('El término de búsqueda debe tener al menos 4 caracteres.')
        return ip.strip() if ip else None
