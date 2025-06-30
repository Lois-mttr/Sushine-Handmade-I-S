from django import forms
from django.core.exceptions import ValidationError
from core_data.models import Usuario
import hashlib
import logging

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
