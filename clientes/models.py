from django.db import models
from django.core.validators import RegexValidator

class Persona(models.Model):
    cedula = models.CharField(
        primary_key=True,
        max_length=16,
        validators=[
            RegexValidator(
                regex='^[0-9]{13}[A-Za-z]$',
                message='La cédula debe tener 13 dígitos seguidos de una letra'
            )
        ],
        verbose_name='Cédula'
    )
    primer_nombre = models.CharField(
        max_length=15,
        db_column='primerNombre',
        verbose_name='Primer Nombre'
    )
    segundo_nombre = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        db_column='segundoNombre',
        verbose_name='Segundo Nombre'
    )
    primer_apellido = models.CharField(
        max_length=15,
        db_column='primerApellido',
        verbose_name='Primer Apellido'
    )
    segundo_apellido = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        db_column='segundoApellido',
        verbose_name='Segundo Apellido'
    )
    direccion = models.CharField(
        max_length=50,
        verbose_name='Dirección'
    )
    estado = models.BooleanField(
        default=True,
        db_column='estadoPersona',
        verbose_name='Estado'
    )

    class Meta:
        db_table = 'Persona'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        nombres = f"{self.primer_nombre} {self.segundo_nombre or ''}".strip()
        apellidos = f"{self.primer_apellido} {self.segundo_apellido or ''}".strip()
        return f"{nombres} {apellidos}"

    @property
    def nombre_completo(self):
        return str(self)

class Cliente(models.Model):
    id = models.AutoField(
        primary_key=True,
        db_column='idCliente',
        verbose_name='ID Cliente'
    )
    persona = models.ForeignKey(
        Persona,
        on_delete=models.CASCADE,
        db_column='idPersonaCliente',
        verbose_name='Persona'
    )
    correo = models.EmailField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Correo Electrónico'
    )
    estado = models.BooleanField(
        default=True,
        db_column='estadoCliente',
        verbose_name='Estado'
    )

    class Meta:
        db_table = 'Cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"Cliente #{self.id} - {self.persona.nombre_completo}"