from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from core_data.models import Producto, Usuario, Venta
from decimal import Decimal
import logging
from datetime import date, datetime
from django.forms import formset_factory

logger = logging.getLogger('nexo.devolucion')

class DevolucionForm(forms.Form):
    """
    Formulario principal para crear/editar devoluciones
    """
    idVentaDev = forms.ModelChoiceField(
        label='Venta Relacionada',
        queryset=Venta.objects.filter(estado='REALIZADA'),
        help_text='Seleccione la venta que desea devolver',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200',
            'style': 'border-color: #eaeef3;'
        })
    )

    fechaDevolucion = forms.DateField(
        label="Fecha de Devolución",
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )

    motivo = forms.CharField(
        label='Motivo de la Devolución',
        required=True,
        max_length=500,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 resize-none',
            'style': 'border-color: #eaeef3;',
            'placeholder': 'Explique brevemente el motivo de la devolución...',
            'maxlength': '500'
        })
    )

    def __init__(self, *args, include_venta_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        ventas = Venta.objects.filter(estado='REALIZADA')
        if include_venta_id:
            ventas = Venta.objects.filter(Q(estado='REALIZADA') | Q(id_venta=include_venta_id))
        self.fields['idVentaDev'].queryset = ventas.order_by('-fechaventa')
        fecha_inicial = self.initial.get('fechaDevolucion')
        if isinstance(fecha_inicial, datetime):
            self.initial['fechaDevolucion'] = fecha_inicial.date()
        if not self.initial.get('fechaDevolucion'):
            self.initial['fechaDevolucion'] = timezone.now().date()
        self.fields['fechaDevolucion'].widget.attrs['onkeydown'] = 'return false;'

    def clean_motivo(self):
        motivo = self.cleaned_data.get('motivo', '').strip()
        if len(motivo) > 500:
            raise ValidationError('El motivo no puede exceder 500 caracteres.')
        return motivo

class DetalleDevolucionForm(forms.Form):
    """
    Formulario para cada producto devuelto
    """
    id_producto = forms.ChoiceField(
        label='Producto Devuelto',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 producto-select',
            'style': 'border-color: #eaeef3;',
            'data-url': '/crud/api/producto/'
        })
    )

    cantidadDevuelta = forms.IntegerField(
        label='Cantidad Devuelta',
        min_value=1,
        max_value=999999,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 cantidad-input',
            'style': 'border-color: #eaeef3;',
            'min': '1',
            'max': '999',
            'placeholder': 'Cantidad Devuelta'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        productos = Producto.objects.filter(estado=True).order_by(
            'id_producto',
            'nombreproducto'
        ).values(
            'id_producto',
            'nombreproducto'
        ).distinct()

        choices = [('', '---------')]
        seen = set()
        for producto in productos:
            product_id = producto['id_producto']
            if product_id in seen:
                continue
            seen.add(product_id)
            choices.append((product_id, f"{producto['nombreproducto']} ({product_id})"))

        self.fields['id_producto'].choices = choices

    def clean_id_producto(self):
        product_id = self.cleaned_data.get('id_producto')
        if not product_id:
            raise ValidationError('Debe seleccionar un producto devuelto.')
        if not Producto.objects.filter(id_producto=product_id, estado=True).exists():
            raise ValidationError('El producto seleccionado no está activo.')
        return product_id

    def clean_cantidadDevuelta(self):
        cantidad = self.cleaned_data.get('cantidadDevuelta')
        if cantidad is None:
            return cantidad
        if cantidad <= 0:
            raise ValidationError('La cantidad devuelta debe ser mayor a cero.')
        return cantidad


DetalleDevolucionFormSet = formset_factory(
    DetalleDevolucionForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
    max_num=50
)

class DevolucionSearchForm(forms.Form):
    fecha_desde = forms.DateField(
        required=False,
        label='Fecha Desde',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    fecha_hasta = forms.DateField(
        required=False,
        label='Fecha Hasta',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    usuario = forms.ModelChoiceField(
        required=False,
        queryset=Usuario.objects.all().order_by('nombreusuario'),
        empty_label="Todas las personas",
        label='Persona'
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha final no puede ser menor que la inicial.')

            hoy = timezone.now().date()
            if fecha_desde > hoy or fecha_hasta > hoy:
                raise ValidationError('Las fechas no pueden ser futuras.')

        return cleaned_data
