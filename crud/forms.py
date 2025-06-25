from django import forms
from django.core.exceptions import ValidationError
from .models import ProductosProduccion, Producto, Usuario, Empleado
from decimal import Decimal
import json

class ProduccionForm(forms.Form):
    fechaEntrada = forms.DateField(
        label='Fecha de Entrada',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    observacion = forms.CharField(
        label='Observación',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200 resize-none',
            'style': 'border-color: #eaeef3;',
            'placeholder': 'Observaciones adicionales sobre la producción...'
        })
    )
    
    id_usuario = forms.ModelChoiceField(
        label='Usuario',
        queryset=Usuario.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_usuario'].queryset = Usuario.objects.filter(activo=True).order_by('nombreusuario')

class DetalleProduccionForm(forms.Form):
    id_producto = forms.ModelChoiceField(
        label='Producto',
        queryset=Producto.objects.filter(estado=True, idubicacionpro=1),  # Campos corregidos aquí
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    cantidad = forms.IntegerField(
        label='Cantidad',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;',
            'min': '1',
            'placeholder': '0'
        })
    )
    
    costo_unitario = forms.DecimalField(
        label='Costo Unitario',
        min_value=Decimal('0.01'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        })
    )
    
    idFabricante = forms.ModelChoiceField(
        label='Fabricante',
        queryset=Empleado.objects.filter(estadoempleado=True),  # Campo corregido aquí
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_producto'].queryset = Producto.objects.filter(
            estado=True,  # Corregido
            idubicacionpro=1  # Corregido
        ).order_by('nombreproducto')  # Corregido
        
        self.fields['idFabricante'].queryset = Empleado.objects.filter(
            estadoempleado=True  # Corregido
        ).order_by('idpersonaemp__primernombre', 'idpersonaemp__primerapellido')  # Corregido

class ProduccionSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;',
            'placeholder': 'Buscar por ID, fecha, usuario...',
            'autocomplete': 'off'
        })
    )
    
    fecha_desde = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )
    
    usuario = forms.ModelChoiceField(
        required=False,
        queryset=Usuario.objects.filter(activo=True),
        empty_label="Todos los usuarios",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )

# FormSet para manejar múltiples detalles de producción
from django.forms import formset_factory

DetalleProduccionFormSet = formset_factory(
    DetalleProduccionForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)