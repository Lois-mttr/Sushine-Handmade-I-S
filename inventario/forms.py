# inventario/forms.py
from django import forms
from core_data.models import Ubicacion, Categoria

class FiltroInventarioForm(forms.Form):
    """
    Formulario para filtrar el inventario por diferentes criterios
    """
    busqueda = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, descripción o código...',
            'autocomplete': 'off'
        }),
        label='Búsqueda'
    )
    
    ubicacion = forms.ModelChoiceField(
        queryset=Ubicacion.objects.all(),
        required=False,
        empty_label="Todas las ubicaciones",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Ubicación'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estadocategoria=True),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Categoría'
    )
    
    ORDEN_CHOICES = [
        ('nombre_asc', 'Nombre (A-Z)'),
        ('nombre_desc', 'Nombre (Z-A)'),
        ('existencia_asc', 'Existencia (Menor a Mayor)'),
        ('existencia_desc', 'Existencia (Mayor a Menor)'),
        ('precio_asc', 'Precio (Menor a Mayor)'),
        ('precio_desc', 'Precio (Mayor a Menor)'),
    ]
    
    orden = forms.ChoiceField(
        choices=ORDEN_CHOICES,
        required=False,
        initial='nombre_asc',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Ordenar por'
    )
    
    STOCK_CHOICES = [
        ('', 'Todos los niveles'),
        ('alto', 'Stock Alto'),
        ('medio', 'Stock Medio'),
        ('bajo', 'Stock Bajo'),
        ('agotado', 'Agotado'),
    ]
    
    nivel_stock = forms.ChoiceField(
        choices=STOCK_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Nivel de Stock'
    )

class BusquedaRapidaForm(forms.Form):
    """
    Formulario simplificado para búsqueda rápida
    """
    q = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Buscar productos...',
            'autocomplete': 'off',
            'autofocus': True
        }),
        label=''
    )