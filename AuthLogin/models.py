from django.db import models
import hashlib

# Create your models here.

class Usuario(models.Model):
    idUsuario = models.AutoField(primary_key=True)
    nombreUsuario = models.CharField(max_length=15, unique=True)
    passUsuario = models.CharField(max_length=64)  # SHA-256 produce 64 caracteres
    rol = models.CharField(max_length=30, null=True, blank=True)
    activo = models.BooleanField(default=True)
    idEmpUsuario = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'Usuario'
        managed = False
        
    def __str__(self):
        return self.nombreUsuario
    
    @classmethod
    def verificar_contrasena(cls, contrasena_plana, contrasena_hash):
        """Compara una contraseña en texto plano con su versión hasheada SHA-256"""
        return hashlib.sha256(contrasena_plana.encode()).hexdigest() == contrasena_hash