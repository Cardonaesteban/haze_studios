from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password
from dashboard.models import Cliente


# ──────────────────────────────────────────────
# VALIDADORES REUTILIZABLES 
# ──────────────────────────────────────────────

def validar_nombre_persona(valor, campo):
    """Nombres/apellidos: sin números y con al menos 2 caracteres."""
    v = valor.strip()
    if len(v) < 2:
        raise ValidationError(f'El {campo} debe tener al menos 2 caracteres.')
    if any(c.isdigit() for c in v):
        raise ValidationError(f'El {campo} no puede contener números.')
    return v


def validar_telefono(telefono):
    """Teléfonos: solo dígitos, sin espacios ni puntos, entre 7 y 15."""
    telefono = telefono.strip()
    if ' ' in telefono:
        raise ValidationError('El teléfono no puede contener espacios.')
    if '.' in telefono:
        raise ValidationError('El teléfono no puede contener puntos.')
    if not telefono.isdigit():
        raise ValidationError('El teléfono debe contener solo números.')
    if len(telefono) < 7:
        raise ValidationError('Ingresa un teléfono válido (mínimo 7 dígitos).')
    if len(telefono) > 15:
        raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
    return telefono


def validar_contraseña_segura(password):
    """Contraseñas: mínimo 6 caracteres, con al menos una letra y un número."""
    if not any(c.isalpha() for c in password):
        raise ValidationError('La contraseña debe incluir al menos una letra.')
    if not any(c.isdigit() for c in password):
        raise ValidationError('La contraseña debe incluir al menos un número.')
    return password


class LoginClienteForm(forms.Form):
    correo = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com', 'autofocus': True})
    )
    contraseña = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )


class RegistroClienteForm(forms.ModelForm):
    contraseña = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 6 caracteres'}),
        min_length=6
    )
    confirmar_contraseña = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite tu contraseña'}),
        min_length=6
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'direccion', 'contraseña']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Juan'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Ej. Pérez'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej. 3001234567'}),
            'direccion': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Dirección de residencia para envíos'}),
        }

    def clean_nombre(self):
        return validar_nombre_persona(self.cleaned_data.get('nombre', ''), 'nombre')

    def clean_apellido(self):
        return validar_nombre_persona(self.cleaned_data.get('apellido', ''), 'apellido')

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip().lower()
        if Cliente.objects.filter(correo=correo).exists():
            raise ValidationError('Ya existe una cuenta registrada con este correo electrónico.')
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono:
            telefono = validar_telefono(telefono)
        return telefono

    def clean_contraseña(self):
        pwd = self.cleaned_data.get('contraseña', '')
        if pwd:
            pwd = validar_contraseña_segura(pwd)
        return pwd

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('contraseña')
        pwd_confirm = cleaned_data.get('confirmar_contraseña')
        if pwd and pwd_confirm and pwd != pwd_confirm:
            self.add_error('confirmar_contraseña', 'Las contraseñas no coinciden.')
        return cleaned_data


class PerfilClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'direccion']
        widgets = {
            'correo': forms.EmailInput(attrs={'readonly': 'readonly'}),
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_nombre(self):
        return validar_nombre_persona(self.cleaned_data.get('nombre', ''), 'nombre')

    def clean_apellido(self):
        return validar_nombre_persona(self.cleaned_data.get('apellido', ''), 'apellido')

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono:
            telefono = validar_telefono(telefono)
        return telefono


class CambiarPasswordClienteForm(forms.Form):
    password_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )
    nuevo_password = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 6 caracteres'}),
        min_length=6
    )
    confirmar_nuevo_password = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la nueva contraseña'}),
        min_length=6
    )

    def __init__(self, *args, **kwargs):
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)

    def clean_password_actual(self):
        actual = self.cleaned_data.get('password_actual')
        if self.cliente and not check_password(actual, self.cliente.contraseña):
            raise ValidationError('La contraseña actual no es correcta.')
        return actual

    def clean_nuevo_password(self):
        nuevo = self.cleaned_data.get('nuevo_password', '')
        if nuevo:
            nuevo = validar_contraseña_segura(nuevo)
        return nuevo

    def clean(self):
        cleaned_data = super().clean()
        nuevo = cleaned_data.get('nuevo_password')
        confirmar = cleaned_data.get('confirmar_nuevo_password')
        actual = cleaned_data.get('password_actual')
        if nuevo and confirmar and nuevo != confirmar:
            self.add_error('confirmar_nuevo_password', 'Las nuevas contraseñas no coinciden.')
        if nuevo and actual and nuevo == actual:
            self.add_error('nuevo_password', 'La nueva contraseña debe ser diferente a la actual.')
        return cleaned_data


class SolicitarRecuperacionClienteForm(forms.Form):
    correo = forms.EmailField(
        label='Correo electrónico registrado',
        widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com', 'autofocus': True})
    )

    def clean_correo(self):
        return self.cleaned_data.get('correo', '').strip().lower()


class ConfirmarPasswordClienteForm(forms.Form):
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 6 caracteres'}),
        min_length=6
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la contraseña'}),
        min_length=6
    )

    def clean_password1(self):
        p1 = self.cleaned_data.get('password1', '')
        if p1:
            p1 = validar_contraseña_segura(p1)
        return p1

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        return cleaned_data


class CheckoutForm(forms.Form):
    direccion_envio = forms.CharField(
        label='Dirección completa de entrega',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Calle/Carrera, Número, Barrio, Ciudad'}),
        required=True
    )
    telefono_contacto = forms.CharField(
        label='Teléfono de contacto',
        max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. 3001234567'}),
        required=True
    )
    notas = forms.CharField(
        label='Notas o instrucciones especiales (Opcional)',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej. Talla oversize holgada, dejar en portería...'}),
        required=False
    )

    def clean_direccion_envio(self):
        direccion = self.cleaned_data.get('direccion_envio', '').strip()
        if len(direccion) < 10:
            raise ValidationError('Ingresa una dirección completa (mínimo 10 caracteres).')
        if len(direccion) > 255:
            raise ValidationError('La dirección no puede superar los 255 caracteres.')
        return direccion

    def clean_telefono_contacto(self):
        telefono = self.cleaned_data.get('telefono_contacto', '').strip()
        return validar_telefono(telefono)

    def clean_notas(self):
        notas = self.cleaned_data.get('notas', '').strip()
        if len(notas) > 500:
            raise ValidationError('Las notas no pueden superar los 500 caracteres.')
        return notas
