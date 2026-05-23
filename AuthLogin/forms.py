from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
            'max_length': 'El usuario no puede tener mas de 15 caracteres'
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input password-input',
            'id': 'password',
            'placeholder': 'Contrasena',
            'required': True,
            'autocomplete': 'current-password',
            'aria-describedby': 'password-error'
        }),
        error_messages={'required': 'El campo contrasena es obligatorio'}
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('El usuario es obligatorio')
        if len(username) > 15:
            raise ValidationError('El usuario no puede tener mas de 15 caracteres')
        try:
            user = Usuario.objects.get(nombreusuario=username)
            if not user.activo:
                raise ValidationError('Esta cuenta esta desactivada')
        except Usuario.DoesNotExist:
            raise ValidationError('Usuario no encontrado')
        return username.strip()

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError('La contrasena es obligatoria')
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
                logger.info(f"Autenticacion exitosa para usuario: {username}")
                return user
            logger.warning(f"Contrasena incorrecta para usuario: {username}")
            return False
        except Usuario.DoesNotExist:
            logger.warning(f"Intento de login con usuario inexistente: {username}")
            return False
        except Exception as e:
            logger.error(f"Error en autenticacion para usuario {username}: {e}")
            return False

    def generate_password_hash(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def get_user(self):
        return getattr(self, '_authenticated_user', None)

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return hashlib.sha256(plain_password.encode('utf-8')).hexdigest() == hashed_password


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
                message='El nombre de usuario solo puede contener letras, numeros y guiones bajos.'
            )
        ]
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Correo electronico',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input password-input',
            'placeholder': 'Contrasena',
            'required': True
        }),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input password-input',
            'placeholder': 'Confirmar contrasena',
            'required': True
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if Usuario.objects.filter(nombreusuario=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya esta en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if Usuario.objects.filter(correo=email).exists():
            raise forms.ValidationError('Este correo electronico ya esta registrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Las contrasenas no coinciden.')
        return cleaned_data

    def save(self):
        usuario = Usuario(
            nombreusuario=self.cleaned_data['username'],
            correo=self.cleaned_data['email'],
            passusuario=hashlib.sha256(self.cleaned_data['password'].encode('utf-8')).hexdigest(),
            rol='usuario',
            activo=True,
            idempusuario=None
        )
        usuario.save()
        return usuario


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Correo electronico',
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if not Usuario.objects.filter(correo=email).exists():
            raise forms.ValidationError('No existe una cuenta con este correo electronico.')
        return email


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label='Nueva contrasena',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ingresa tu nueva contrasena',
            'minlength': '8',
            'required': True,
            'autocomplete': 'new-password'
        }),
        min_length=8,
        error_messages={
            'required': 'La nueva contrasena es obligatoria',
            'min_length': 'La contrasena debe tener al menos 8 caracteres'
        }
    )
    confirm_password = forms.CharField(
        label='Confirmar contrasena',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirma tu nueva contrasena',
            'minlength': '8',
            'required': True,
            'autocomplete': 'new-password'
        }),
        error_messages={'required': 'Debes confirmar la nueva contrasena'}
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('Las contrasenas no coinciden.')
        return cleaned_data


class PerfilUsuarioForm(forms.Form):
    base_class = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'

    nombreusuario = forms.CharField(label='Nombre de usuario', max_length=15, widget=forms.TextInput(attrs={'class': base_class, 'maxlength': '15'}))
    correo = forms.EmailField(label='Correo electronico', required=False, widget=forms.EmailInput(attrs={'class': base_class}))
    primernombre = forms.CharField(label='Primer nombre', max_length=15, required=False, widget=forms.TextInput(attrs={'class': base_class}))
    segundonombre = forms.CharField(label='Segundo nombre', max_length=15, required=False, widget=forms.TextInput(attrs={'class': base_class}))
    primerapellido = forms.CharField(label='Primer apellido', max_length=15, required=False, widget=forms.TextInput(attrs={'class': base_class}))
    segundoapellido = forms.CharField(label='Segundo apellido', max_length=15, required=False, widget=forms.TextInput(attrs={'class': base_class}))
    direccion = forms.CharField(label='Direccion', max_length=50, required=False, widget=forms.TextInput(attrs={'class': base_class}))

    def __init__(self, *args, user=None, persona=None, **kwargs):
        self.user = user
        self.persona = persona
        super().__init__(*args, **kwargs)

    def clean_nombreusuario(self):
        nombreusuario = (self.cleaned_data.get('nombreusuario') or '').strip()
        if not nombreusuario:
            raise forms.ValidationError('El nombre de usuario es obligatorio.')
        query = Usuario.objects.filter(nombreusuario=nombreusuario)
        if self.user:
            query = query.exclude(idusuario=self.user.idusuario)
        if query.exists():
            raise forms.ValidationError('Este nombre de usuario ya esta en uso.')
        return nombreusuario

    def clean_correo(self):
        correo = (self.cleaned_data.get('correo') or '').strip().lower()
        if correo:
            query = Usuario.objects.filter(correo=correo)
            if self.user:
                query = query.exclude(idusuario=self.user.idusuario)
            if query.exists():
                raise forms.ValidationError('Este correo ya esta en uso.')
        return correo

    def save(self):
        self.user.nombreusuario = self.cleaned_data['nombreusuario']
        self.user.correo = self.cleaned_data.get('correo') or None
        self.user.save(update_fields=['nombreusuario', 'correo'])
        if self.persona:
            self.persona.primernombre = self.cleaned_data.get('primernombre') or self.persona.primernombre
            self.persona.segundonombre = self.cleaned_data.get('segundonombre') or None
            self.persona.primerapellido = self.cleaned_data.get('primerapellido') or self.persona.primerapellido
            self.persona.segundoapellido = self.cleaned_data.get('segundoapellido') or None
            self.persona.direccion = self.cleaned_data.get('direccion') or self.persona.direccion
            self.persona.save(update_fields=['primernombre', 'segundonombre', 'primerapellido', 'segundoapellido', 'direccion'])
        return self.user


class ConfiguracionCuentaForm(forms.Form):
    base_class = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'

    current_password = forms.CharField(label='Contrasena actual', required=False, widget=forms.PasswordInput(attrs={'class': base_class, 'autocomplete': 'current-password'}))
    new_password = forms.CharField(label='Nueva contrasena', required=False, min_length=8, widget=forms.PasswordInput(attrs={'class': base_class, 'autocomplete': 'new-password'}))
    confirm_password = forms.CharField(label='Confirmar nueva contrasena', required=False, widget=forms.PasswordInput(attrs={'class': base_class, 'autocomplete': 'new-password'}))

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if any([current_password, new_password, confirm_password]):
            if not all([current_password, new_password, confirm_password]):
                raise forms.ValidationError('Complete los tres campos para cambiar la contrasena.')
            if hashlib.sha256(current_password.encode('utf-8')).hexdigest() != self.user.passusuario:
                raise forms.ValidationError('La contrasena actual no es correcta.')
            if new_password != confirm_password:
                raise forms.ValidationError('Las contrasenas no coinciden.')
        return cleaned_data

    def save(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            self.user.set_password(new_password)
        return self.user
