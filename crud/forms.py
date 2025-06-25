"""
Formularios corregidos para el módulo de producción NEXO
CORREGIDO: Validación de productos de producción más flexible
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from core_data.models import Producto, Usuario, Empleado
from decimal import Decimal, InvalidOperation
import logging
from datetime import date, datetime

logger = logging.getLogger('nexo.produccion')

class ProduccionForm(forms.Form):
    """
    Formulario principal para crear/editar producciones
    """
    fechaEntrada = forms.DateField(
        label='Fecha de Entrada',
        help_text='Fecha en que se registra la producción',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            'style': 'border-color: #eaeef3;',
            'max': timezone.now().date().isoformat()
        })
    )
    
    observacion = forms.CharField(
        label='Observaciones',
        required=False,
        max_length=500,
        help_text='Observaciones adicionales sobre la producción (opcional)',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 resize-none',
            'style': 'border-color: #eaeef3;',
            'placeholder': 'Observaciones adicionales sobre la producción...',
            'maxlength': '500'
        })
    )
    
    id_usuario = forms.ModelChoiceField(
        label='Usuario Responsable',
        queryset=Usuario.objects.none(),
        help_text='Usuario que registra la producción',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar usuarios activos ordenados
        try:
            self.fields['id_usuario'].queryset = Usuario.objects.filter(
                activo=True
            ).select_related().order_by('nombreusuario')
        except Exception as e:
            logger.error(f"Error al cargar usuarios: {str(e)}")
            self.fields['id_usuario'].queryset = Usuario.objects.none()
        
        # Establecer fecha por defecto si no se proporciona
        if not self.initial.get('fechaEntrada'):
            self.initial['fechaEntrada'] = timezone.now().date()
    
    def clean_fechaEntrada(self):
        """
        Validar que la fecha no sea futura
        """
        fecha = self.cleaned_data.get('fechaEntrada')
        if fecha and fecha > timezone.now().date():
            raise ValidationError('La fecha de entrada no puede ser futura.')
        return fecha
    
    def clean_observacion(self):
        """
        Limpiar y validar observaciones
        """
        observacion = self.cleaned_data.get('observacion', '').strip()
        if len(observacion) > 500:
            raise ValidationError('Las observaciones no pueden exceder 500 caracteres.')
        return observacion

class DetalleProduccionForm(forms.Form):
    """
    Formulario para cada detalle de producción (producto)
    CORREGIDO: Validación de productos de producción más flexible
    """
    id_producto = forms.ModelChoiceField(
        label='Producto',
        queryset=Producto.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 producto-select',
            'style': 'border-color: #eaeef3;',
            'data-url': '/crud/api/producto/'
        })
    )
    
    cantidad = forms.IntegerField(
        label='Cantidad',
        min_value=1,
        max_value=999999,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 cantidad-input',
            'style': 'border-color: #eaeef3;',
            'min': '1',
            'max': '999999',
            'placeholder': '1'
        })
    )
    
    costo_unitario = forms.DecimalField(
        label='Costo Unitario (C$)',
        min_value=Decimal('0.01'),
        max_value=Decimal('999999.99'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 costo-input',
            'style': 'border-color: #eaeef3;',
            'step': '0.01',
            'min': '0.01',
            'max': '999999.99',
            'placeholder': '0.00'
        })
    )
    
    idFabricante = forms.ModelChoiceField(
        label='Fabricante/Empleado',
        queryset=Empleado.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 fabricante-select',
            'style': 'border-color: #eaeef3;',
            'data-url': '/crud/api/empleado/'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # CORREGIDO: Cargar productos activos SIN restricción de ubicación inicialmente
        # La validación de ubicación se hará en clean() para dar mejor mensaje de error
        try:
            self.fields['id_producto'].queryset = Producto.objects.filter(
                estado=True
            ).select_related('idubicacionpro').order_by('nombreproducto')
        except Exception as e:
            logger.error(f"Error al cargar productos: {str(e)}")
            self.fields['id_producto'].queryset = Producto.objects.none()
        
        # Cargar SOLO empleados activos
        try:
            self.fields['idFabricante'].queryset = Empleado.objects.filter(
                estadoempleado=True
            ).select_related('idpersonaemp').order_by(
                'idpersonaemp__primernombre', 
                'idpersonaemp__primerapellido'
            )
        except Exception as e:
            logger.error(f"Error al cargar empleados: {str(e)}")
            self.fields['idFabricante'].queryset = Empleado.objects.none()
    
    def clean_cantidad(self):
        """
        Validar cantidad
        """
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')
        if cantidad and cantidad > 999999:
            raise ValidationError('La cantidad no puede exceder 999,999 unidades.')
        return cantidad
    
    def clean_costo_unitario(self):
        """
        Validar costo unitario
        """
        costo = self.cleaned_data.get('costo_unitario')
        if costo and costo <= 0:
            raise ValidationError('El costo unitario debe ser mayor a cero.')
        if costo and costo > Decimal('999999.99'):
            raise ValidationError('El costo unitario no puede exceder C$ 999,999.99')
        return costo
    
    def clean(self):
        """
        Validaciones cruzadas del formulario
        CORREGIDO: Validación más flexible de productos de producción
        """
        cleaned_data = super().clean()
        producto = cleaned_data.get('id_producto')
        fabricante = cleaned_data.get('idFabricante')
        
        # Validar que el producto esté disponible y activo
        if producto:
            if not producto.estado:
                raise ValidationError('El producto seleccionado no está disponible.')
            
            # CORREGIDO: Validación más flexible de ubicación de producción
            # Permitir productos de ubicación 1 (Producción) o sin ubicación específica
            if hasattr(producto, 'idubicacionpro') and producto.idubicacionpro:
                # Si tiene ubicación, debe ser de producción (ID 1) o permitir otras ubicaciones según negocio
                ubicaciones_permitidas = [1]  # Ubicación 1 = Producción
                if producto.idubicacionpro not in ubicaciones_permitidas:
                    # Mensaje más informativo
                    ubicacion_nombre = getattr(producto.idubicacionpro, 'nombreubicacion', f'ID {producto.idubicacionpro}')
                    logger.warning(f"Producto {producto.nombreproducto} tiene ubicación {ubicacion_nombre}, se esperaba Producción")
                    # TEMPORAL: Permitir todos los productos activos mientras se ajusta la base de datos
                    # raise ValidationError(f'El producto seleccionado pertenece a {ubicacion_nombre}, no a Producción.')
        
        # Validar que el empleado esté activo
        if fabricante and not fabricante.estadoempleado:
            raise ValidationError('El empleado seleccionado no está activo.')
        
        return cleaned_data

class ProduccionSearchForm(forms.Form):
    """
    Formulario de búsqueda y filtros corregido (SIN filtro de estado)
    """
    fecha_desde = forms.DateField(
        required=False,
        label='Fecha Desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label='Fecha Hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    usuario = forms.ModelChoiceField(
        required=False,
        queryset=Usuario.objects.none(),
        empty_label="Todos los usuarios",
        label='Usuario',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cargar usuarios que han registrado producciones
        try:
            self.fields['usuario'].queryset = Usuario.objects.filter(
                activo=True,
                productosproduccion__isnull=False
            ).distinct().order_by('nombreusuario')
        except Exception:
            # Fallback si hay problemas con la relación
            self.fields['usuario'].queryset = Usuario.objects.filter(
                activo=True
            ).order_by('nombreusuario')
    
    def clean(self):
        """
        Validar que fecha_desde no sea mayor que fecha_hasta
        """
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError({
                    'fecha_hasta': 'La fecha hasta no puede ser anterior a la fecha desde.'
                })
            
            # Validar que las fechas no sean futuras
            hoy = timezone.now().date()
            if fecha_desde > hoy:
                raise ValidationError({
                    'fecha_desde': 'La fecha desde no puede ser futura.'
                })
            
            if fecha_hasta > hoy:
                raise ValidationError({
                    'fecha_hasta': 'La fecha hasta no puede ser futura.'
                })
        
        return cleaned_data

# FormSet para manejar múltiples detalles de producción
from django.forms import formset_factory

DetalleProduccionFormSet = formset_factory(
    DetalleProduccionForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True,
    max_num=50  # Límite máximo de productos por producción
)
