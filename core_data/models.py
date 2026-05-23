import hashlib

from django.db import models
from django.conf import settings

class Categoria(models.Model):
    idcategoria = models.AutoField(db_column='idCategoria', primary_key=True)
    nombrecategoria = models.CharField(db_column='nombreCategoria', max_length=25)
    descripcioncategoria = models.CharField(db_column='descripcionCategoria', max_length=100, blank=True, null=True)
    estadocategoria = models.BooleanField(db_column='estadoCategoria', default=True)

    class Meta:
        managed = False
        db_table = 'categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombrecategoria

class Ubicacion(models.Model):
    id_ubicacion = models.AutoField(primary_key=True)
    nombreubicacion = models.CharField(db_column='nombreUbicacion', max_length=15)
    direccion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ubicacion'
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'

    def __str__(self):
        return self.nombreubicacion

class Persona(models.Model):
    cedula = models.CharField(primary_key=True, max_length=16)
    primernombre = models.CharField(db_column='primerNombre', max_length=15)
    segundonombre = models.CharField(db_column='segundoNombre', max_length=15, blank=True, null=True)
    primerapellido = models.CharField(db_column='primerApellido', max_length=15)
    segundoapellido = models.CharField(db_column='segundoApellido', max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=50)
    estadopersona = models.BooleanField(db_column='estadoPersona', default=True)

    class Meta:
        managed = False
        db_table = 'persona'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        return f"{self.primernombre} {self.primerapellido}"

    @property
    def nombre_completo(self):
        nombres = [self.primernombre]
        if self.segundonombre:
            nombres.append(self.segundonombre)
        apellidos = [self.primerapellido]
        if self.segundoapellido:
            apellidos.append(self.segundoapellido)
        return f"{' '.join(nombres)} {' '.join(apellidos)}"

class Empleado(models.Model):
    idempleado = models.AutoField(db_column='idEmpleado', primary_key=True)
    rolempleado = models.CharField(db_column='rolEmpleado', max_length=30, blank=True, null=True)
    fechacontratacion = models.DateTimeField(db_column='fechaContratacion', blank=True, null=True)
    salario = models.FloatField(blank=True, null=True)
    correo = models.CharField(max_length=30, blank=True, null=True)
    idpersonaemp = models.ForeignKey(
        Persona,
        models.DO_NOTHING,
        db_column='idPersonaEmp',
        blank=True,
        null=True
    )
    estadoempleado = models.BooleanField(db_column='estadoEmpleado', default=True)

    class Meta:
        managed = False
        db_table = 'empleado'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        if self.idpersonaemp:
            return f"{self.idpersonaemp.nombre_completo} - {self.rolempleado or 'Sin rol'}"
        return f"Empleado {self.idempleado}"


import hashlib
from django.db import models


class Usuario(models.Model):
    idusuario = models.AutoField(db_column='idUsuario', primary_key=True)
    nombreusuario = models.CharField(db_column='nombreUsuario', unique=True, max_length=15)
    passusuario = models.CharField(db_column='passUsuario', max_length=64)
    rol = models.CharField(max_length=30, blank=True, null=True, default='usuario')
    correo = models.EmailField(max_length=50, blank=True, null=True)

    # Campo activo como BooleanField (ya que en la BD es TINYINT(1))
    activo = models.BooleanField(db_column='activo', default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)
    intentos_fallidos = models.SmallIntegerField(default=0)
    idempusuario = models.ForeignKey(
        'Empleado',
        on_delete=models.DO_NOTHING,
        db_column='idEmpUsuario',
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.nombreusuario

    @property
    def is_active(self):
        return self.activo

    @property
    def empleado_nombre(self):
        if self.idempusuario and self.idempusuario.idpersonaemp:
            return self.idempusuario.idpersonaemp.nombre_completo
        return None

    def set_password(self, raw_password):
        """Actualiza la contraseña evitando problemas con el ORM"""
        if not raw_password or len(raw_password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")

        password_hash = hashlib.sha256(raw_password.encode('utf-8')).hexdigest()

        # Actualización directa con SQL crudo
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE usuario SET passUsuario = %s, intentos_fallidos = 0 WHERE idUsuario = %s",
                [password_hash, self.idusuario]
            )

        # Actualizar los atributos en memoria
        self.passusuario = password_hash
        self.intentos_fallidos = 0

    def verify_password(self, raw_password):
        """Verifica si una contraseña en texto plano coincide con el hash almacenado"""
        return hashlib.sha256(raw_password.encode('utf-8')).hexdigest() == self.passusuario

class Cliente(models.Model):
    idcliente = models.AutoField(db_column='idCliente', primary_key=True)
    correo = models.CharField(max_length=30, blank=True, null=True)
    idpersonacliente = models.ForeignKey(
        Persona,
        models.DO_NOTHING,
        db_column='idPersonaCliente',
        blank=True,
        null=True
    )
    estadocliente = models.BooleanField(db_column='estadoCliente', default=True)

    class Meta:
        managed = False
        db_table = 'cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        if self.idpersonacliente:
            return self.idpersonacliente.nombre_completo
        return f"Cliente {self.idcliente}"

class Producto(models.Model):
    id_producto = models.CharField(max_length=15, primary_key=True)
    idubicacionpro = models.ForeignKey(
        Ubicacion,
        models.DO_NOTHING,
        db_column='idUbicacionPro'
    )
    nombreproducto = models.CharField(db_column='nombreProducto', max_length=30)
    descripcionproducto = models.CharField(
        db_column='descripcionProducto',
        max_length=70,
        blank=True,
        null=True
    )
    existenciaproducto = models.IntegerField(db_column='existenciaProducto')
    imagenproductoruta = models.CharField(
        db_column='imagenProductoRuta',
        max_length=250,
        blank=True,
        null=True
    )
    idcategoriapro = models.ForeignKey(
        Categoria,
        models.DO_NOTHING,
        db_column='idCategoriaPro',
        blank=True,
        null=True
    )
    precioproducto = models.DecimalField(
        db_column='precioProducto',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    estado = models.BooleanField(default=True)
    existenciaminima = models.IntegerField(
        db_column='existenciaMinima',
        blank=True,
        null=True,
        default=5
    )

    class Meta:
        managed = False
        db_table = 'producto'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.nombreproducto} ({self.id_producto})"

    @property
    def necesita_reposicion(self):
        return self.existenciaproducto <= (self.existenciaminima or 5)

    @property
    def imagen_url(self):
        ruta = (self.imagenproductoruta or '').strip()
        if not ruta:
            return ''
        if ruta.startswith(('http://', 'https://', '/')):
            return ruta
        if ruta.startswith('static/'):
            return f"{settings.STATIC_URL}{ruta[len('static/'):].lstrip('/')}"
        if ruta.startswith('images/'):
            return f"{settings.STATIC_URL}{ruta}"
        return f"{settings.MEDIA_URL}{ruta.lstrip('/')}"

class Venta(models.Model):
    ESTADO_CHOICES = [
        ('REALIZADA', 'Realizada'),
        ('ANULADA', 'Anulada'),
    ]
    
    id_venta = models.AutoField(primary_key=True)
    fechaventa = models.DateTimeField(db_column='fechaVenta', blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=9, choices=ESTADO_CHOICES, default='REALIZADA')
    idusuarioventa = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column='idUsuarioVenta',
        blank=True,
        null=True
    )
    codcliente = models.ForeignKey(
        Cliente,
        models.DO_NOTHING,
        db_column='codCliente',
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'venta'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"Venta {self.id_venta} - {self.fechaventa}"

# ATENCIÓN: Este modelo NO tiene campo 'id' ni 'pk'.
# Usar SIEMPRE ambos campos (idventa, idproventa) para búsquedas y acceso.
# Ejemplo correcto: Detalleventa.objects.get(idventa=..., idproventa=...)
class Detalleventa(models.Model):
    idventa = models.ForeignKey(
        Venta,
        db_column='idVenta',
        to_field='id_venta',  # Relaciona con el campo correcto de Venta
        on_delete=models.CASCADE, # Cambiado a clave primaria
    )
    idproventa = models.ForeignKey(
        Producto,
        db_column='idProVenta',
        on_delete=models.CASCADE,

    )
    cantidadventa = models.IntegerField(db_column='cantidadVenta')
    subtotal = models.DecimalField(db_column='subtotal', max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'DetalleVenta'
        unique_together = (('idventa', 'idproventa'),)
        managed = False 

    def __str__(self):
        return f"Venta {self.idventa_id} - Producto {self.idproventa_id}"

    @property
    def id(self):
        """Compatibilidad: retorna una tupla única como identificador."""
        return (self.idventa_id, self.idproventa_id)

class Devolucion(models.Model):
    iddevolucion = models.AutoField(db_column='idDevolucion', primary_key=True)
    idventadev = models.ForeignKey(Venta, models.DO_NOTHING, db_column='idVentaDev')
    fechadevolucion = models.DateField(db_column='fechaDevolucion', blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'devolucion'
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'

    def __str__(self):
        return f"Devolución {self.iddevolucion} - Venta {self.idventadev.id_venta}"

class Detalledevolucion(models.Model):
    id_devolucion = models.ForeignKey(Devolucion, models.DO_NOTHING, db_column='id_devolucion')
    id_producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='id_producto')
    cantidaddevuelta = models.IntegerField(db_column='cantidadDevuelta')

    class Meta:
        managed = False
        db_table = 'detalledevolucion'
        unique_together = (('id_devolucion', 'id_producto'),)
        verbose_name = 'Detalle de Devolución'
        verbose_name_plural = 'Detalles de Devolución'

    def __str__(self):
        return f"Detalle Dev. {self.id_devolucion.iddevolucion} - {self.id_producto.nombreproducto}"

class Productosproduccion(models.Model):
    idproduccion = models.AutoField(db_column='idProduccion', primary_key=True)
    fechaentrada = models.DateField(db_column='fechaEntrada')
    observacion = models.TextField(blank=True, null=True)
    id_usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    estadoregistro = models.BooleanField(db_column='EstadoRegistro', default=True)

    class Meta:
        managed = False
        db_table = 'productosproduccion'
        verbose_name = 'Producción'
        verbose_name_plural = 'Producciones'

    def __str__(self):
        return f"Producción {self.idproduccion} - {self.fechaentrada}"

class Detalleproduccion(models.Model):
    id_produccion = models.ForeignKey(Productosproduccion, models.DO_NOTHING, db_column='id_produccion')
    id_producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='id_producto')
    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    idfabricante = models.ForeignKey(
        Empleado,
        models.DO_NOTHING,
        db_column='idFabricante',
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'detalleproduccion'
        unique_together = (('id_produccion', 'id_producto'),)
        verbose_name = 'Detalle de Producción'
        verbose_name_plural = 'Detalles de Producción'

    def __str__(self):
        return f"Det. Prod. {self.id_produccion.idproduccion} - {self.id_producto.nombreproducto}"
