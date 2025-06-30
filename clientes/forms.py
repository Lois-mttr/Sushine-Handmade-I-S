from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import Persona, Cliente
import re


class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Quita el atributo readonly para permitir edición
        self.fields['cedula'].widget.attrs.update({
            'class': 'form-input',
            'title': 'Ingrese la cédula (13 dígitos + letra)'
        })
        self.fields['primer_nombre'].required = True
        self.fields['primer_apellido'].required = True
        self.fields['direccion'].required = True

        # Añadir clases y placeholders a todos los campos
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-input',
                'placeholder': f'Ingrese {self.fields[field].label.lower()}'
            })


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['correo']
        widgets = {
            'correo': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'ejemplo@dominio.com'
            })
        }