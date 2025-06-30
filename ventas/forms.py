# ventas/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Venta, Cliente, Producto, Usuario
import json

class VentaForm(forms.ModelForm):
    """
    Formulario para crear/editar ventas
    """
    
    class Meta:
        model = Venta
        fields = ['codcliente']
        
    codcliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estadocliente=True).select_related('idpersonacliente'),
        empty_label="Seleccionar cliente...",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'required': True
        }),
        label='Cliente'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar la representación de clientes
        self.fields['codcliente'].queryset = Cliente.objects.filter(
            estadocliente=True
        ).select_related('idpersonacliente')

class DetalleVentaForm(forms.Form):
    """
    Formulario para agregar productos a la venta
    """
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(
            estado=True,
            idubicacionpro_id=2,  # Solo productos de sucursal
            existenciaproducto__gt=0
        ).select_related('idcategoriapro'),
        empty_label="Seleccionar producto...",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'id': 'id_producto',
            'onchange': 'actualizarInfoProducto(this.value)'
        }),
        label='Producto'
    )
    
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Cantidad',
            'id': 'id_cantidad',
            'onchange': 'calcularSubtotal()'
        }),
        label='Cantidad'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad:
            if cantidad > producto.existenciaproducto:
                raise ValidationError(
                    f'Stock insuficiente. Disponible: {producto.existenciaproducto}'
                )
        
        return cleaned_data

class FiltroVentasForm(forms.Form):
    """
    Formulario para filtrar ventas
    """
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Fecha Inicio'
    )
    
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Fecha Fin'
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estadocliente=True).select_related('idpersonacliente'),
        required=False,
        empty_label="Todos los clientes",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Cliente'
    )
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('REALIZADA', 'Realizada'),
        ('ANULADA', 'Anulada'),
    ]
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        label='Estado'
    )

class BusquedaRapidaForm(forms.Form):
    """
    Formulario para búsqueda rápida de ventas
    """
    q = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Buscar por ID de venta, cliente...',
            'autocomplete': 'off'
        }),
        label=''
    )