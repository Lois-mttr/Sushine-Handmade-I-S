from django import forms
from django.core.exceptions import ValidationError
from core_data.models import Usuario
import hashlib
import logging

from django import forms
from django.core.validators import validate_email, RegexValidator
from core_data.models import Usuario, Empleado
import hashlib


logger = logging.getLogger('nexo.auth')

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'id': 'username',
            'placeholder': 'Usuario',
            'required': True,
            'maxlength': '15',
            'autocomplete': 'username',
            'aria-describedby': 'username-error'
        }),
        error_messages={
            'required': 'El campo usuario es obligatorio',
            'max_length': 'El usuario no puede tener más de 15 caracteres'
        }
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input password-input',
            'id': 'password',
            'placeholder': 'Contraseña',
            'required': True,
            'autocomplete': 'current-password',
            'aria-describedby': 'password-error'
        }),
        error_messages={
            'required': 'El campo contraseña es obligatorio'
        }
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('El usuario es obligatorio')
        
        if len(username) > 15:
            raise ValidationError('El usuario no puede tener más de 15 caracteres')
        
        try:
            user = Usuario.objects.get(nombreusuario=username)
            print(f"Valor crudo de _activo_raw: {repr(user._activo_raw)}")  # línea nueva
            print(f"Resultado de .activo: {user.activo}")  # línea nueva
            if not user.activo:
                raise ValidationError('Esta cuenta está desactivada')
        except Usuario.DoesNotExist:
            raise ValidationError('Usuario no encontrado')
        
        return username.strip()

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if not password:
            raise ValidationError('La contraseña es obligatoria')
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = self.authenticate_user(username, password)
            if not user:
                raise ValidationError('Credenciales incorrectas')
            
            self._authenticated_user = user

        return cleaned_data

    def authenticate_user(self, username, password):
        try:
            user = Usuario.objects.get(nombreusuario=username)
            
            if not user.activo:
                logger.warning(f"Intento de login con usuario inactivo: {username}")
                return False
            
            password_hash = self.generate_password_hash(password)
            
            if user.passusuario == password_hash:
                logger.info(f"Autenticación exitosa para usuario: {username}")
                return user
            else:
                logger.warning(f"Contraseña incorrecta para usuario: {username}")
                return False
                
        except Usuario.DoesNotExist:
            logger.warning(f"Intento de login con usuario inexistente: {username}")
            return False
        except Exception as e:
            logger.error(f"Error en autenticación para usuario {username}: {e}")
            return False

    def generate_password_hash(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def get_user(self):
        return getattr(self, '_authenticated_user', None)

    @staticmethod
    def verify_password(plain_password, hashed_password):
        password_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return password_hash == hashed_password


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nombre de usuario',
            'required': True,
            'maxlength': '15'
        }),
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='El nombre de usuario solo puede contener letras, números y guiones bajos.'
            )
        ]
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Correo electrónico',
            'required': True
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input password-input',
            'placeholder': 'Contraseña',
            'required': True
        }),
        min_length=8
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input password-input',
            'placeholder': 'Confirmar contraseña',
            'required': True
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if Usuario.objects.filter(nombreusuario=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if Usuario.objects.filter(correo=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        # Hashear la contraseña
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        # Crear el usuario con los campos correctos según tu modelo
        usuario = Usuario(
            nombreusuario=username,
            passusuario=password_hash,
            correo=email,
            # Los siguientes campos tienen valores por defecto o son opcionales
            rol='usuario',  # Asignamos un rol por defecto aunque el campo permita null
            activo=True,  # Por defecto ya es True, pero lo explicitamos
            idempusuario=None  # Dejamos null como especifica tu modelo
        )

        usuario.save()
        return usuario

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Correo electrónico',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        
        if not Usuario.objects.filter(correo=email).exists():
            raise forms.ValidationError('No existe una cuenta con este correo electrónico.')
            
        return email


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ingresa tu nueva contraseña',
            'minlength': '8',
            'required': True,
            'autocomplete': 'new-password'
        }),
        min_length=8,
        error_messages={
            'required': 'La nueva contraseña es obligatoria',
            'min_length': 'La contraseña debe tener al menos 8 caracteres'
        }
    )

    confirm_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirma tu nueva contraseña',
            'minlength': '8',
            'required': True,
            'autocomplete': 'new-password'
        }),
        error_messages={
            'required': 'Debes confirmar la nueva contraseña'
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden")

        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Las contraseñas no coinciden.')

        return cleaned_data
    
