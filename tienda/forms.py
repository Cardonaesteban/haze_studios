from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password
from dashboard.models import Cliente


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
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if len(apellido) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        return apellido

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip().lower()
        if Cliente.objects.filter(correo=correo).exists():
            raise ValidationError('Ya existe una cuenta registrada con este correo electrónico.')
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono:
            digitos = ''.join(c for c in telefono if c.isdigit())
            if len(digitos) < 7:
                raise ValidationError('Ingresa un teléfono válido (mínimo 7 dígitos).')
        return telefono

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
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if len(apellido) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        return apellido

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono:
            digitos = ''.join(c for c in telefono if c.isdigit())
            if len(digitos) < 7:
                raise ValidationError('Ingresa un teléfono válido (mínimo 7 dígitos).')
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

    def clean(self):
        cleaned_data = super().clean()
        nuevo = cleaned_data.get('nuevo_password')
        confirmar = cleaned_data.get('confirmar_nuevo_password')
        if nuevo and confirmar and nuevo != confirmar:
            self.add_error('confirmar_nuevo_password', 'Las nuevas contraseñas no coinciden.')
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
        return direccion

    def clean_telefono_contacto(self):
        telefono = self.cleaned_data.get('telefono_contacto', '').strip()
        digitos = ''.join(c for c in telefono if c.isdigit())
        if len(digitos) < 7:
            raise ValidationError('Ingresa un teléfono válido (mínimo 7 dígitos).')
        return telefono
