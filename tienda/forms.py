from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password, make_password
from dashboard.models import Cliente, Producto
from .models import Personalizacion, PrendaComunidad, ComentarioComunidad


def validar_texto_descriptivo(valor, campo_label, min_len=10, max_len=500):
    """Valida longitud y que el texto incluya palabras reales (no solo puntos o símbolos)."""
    texto = (valor or '').strip()
    if len(texto) < min_len:
        raise ValidationError(f'Ingresa {campo_label} de al menos {min_len} caracteres.')
    if max_len and len(texto) > max_len:
        raise ValidationError(f'{campo_label.capitalize()} no puede superar los {max_len} caracteres.')
    letras = [c for c in texto if c.isalpha()]
    if len(letras) < 3 or len({c.lower() for c in letras}) < 2:
        raise ValidationError('Escribe una descripción válida con palabras.')
    return texto


def validar_nombre_con_letras(valor, campo_label, min_len=3):
    """Valida longitud mínima y que el nombre incluya letras reales."""
    texto = (valor or '').strip()
    if len(texto) < min_len:
        raise ValidationError(f'{campo_label} debe tener al menos {min_len} caracteres.')
    if sum(1 for c in texto if c.isalpha()) < 2:
        raise ValidationError('Ingresa un nombre válido con letras.')
    return texto


def validar_comentario_texto(valor, max_len=400):
    """Valida que el comentario no esté vacío, no exceda max_len y contenga texto válido."""
    texto = (valor or '').strip()
    if not texto:
        raise ValidationError('El comentario no puede estar vacío.')
    if len(texto) > max_len:
        raise ValidationError(f'El comentario no puede superar los {max_len} caracteres.')
    if not any(c.isalnum() for c in texto):
        raise ValidationError('Escribe un comentario válido.')
    return texto


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
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        if len(nombre) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        if any(c.isdigit() for c in nombre):
            raise ValidationError('El nombre no puede contener números.')
        if sum(1 for c in nombre if c.isalpha()) < 2:
            raise ValidationError('Ingresa un nombre válido con letras.')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if not apellido:
            raise ValidationError('El apellido es obligatorio.')
        if len(apellido) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        if any(c.isdigit() for c in apellido):
            raise ValidationError('El apellido no puede contener números.')
        if sum(1 for c in apellido if c.isalpha()) < 2:
            raise ValidationError('Ingresa un apellido válido con letras.')
        return apellido

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip().lower()
        if not correo:
            raise ValidationError('El correo electrónico es obligatorio.')
        if Cliente.objects.filter(correo__iexact=correo).exists():
            raise ValidationError('Ya existe una cuenta registrada con este correo electrónico.')
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not telefono:
            raise ValidationError('El teléfono es obligatorio.')
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

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '').strip()
        if not direccion:
            raise ValidationError('La dirección es obligatoria.')
        if len(direccion) < 10:
            raise ValidationError('La dirección debe tener al menos 10 caracteres.')
        if not any(c.isalpha() for c in direccion):
            raise ValidationError('Ingresa una dirección válida.')
        return direccion

    def clean_contraseña(self):
        contraseña = self.cleaned_data.get('contraseña', '').strip()
        if not contraseña:
            raise ValidationError('La contraseña es obligatoria.')
        if len(contraseña) < 6:
            raise ValidationError('La contraseña debe tener al menos 6 caracteres.')
        if ' ' in contraseña:
            raise ValidationError('La contraseña no puede contener espacios.')
        return contraseña

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
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        if len(nombre) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        if any(c.isdigit() for c in nombre):
            raise ValidationError('El nombre no puede contener números.')
        if sum(1 for c in nombre if c.isalpha()) < 2:
            raise ValidationError('Ingresa un nombre válido con letras.')
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '').strip()
        if not apellido:
            raise ValidationError('El apellido es obligatorio.')
        if len(apellido) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        if any(c.isdigit() for c in apellido):
            raise ValidationError('El apellido no puede contener números.')
        if sum(1 for c in apellido if c.isalpha()) < 2:
            raise ValidationError('Ingresa un apellido válido con letras.')
        return apellido

    def clean_correo(self):
        return self.instance.correo if self.instance and self.instance.pk else self.cleaned_data.get('correo')

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not telefono:
            raise ValidationError('El teléfono es obligatorio.')
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

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '').strip()
        if not direccion:
            raise ValidationError('La dirección es obligatoria.')
        if len(direccion) < 10:
            raise ValidationError('La dirección debe tener al menos 10 caracteres.')
        if not any(c.isalpha() for c in direccion):
            raise ValidationError('Ingresa una dirección válida.')
        return direccion


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
        nuevo = self.cleaned_data.get('nuevo_password', '').strip()
        if not nuevo:
            raise ValidationError('La nueva contraseña es obligatoria.')
        if len(nuevo) < 6:
            raise ValidationError('La nueva contraseña debe tener al menos 6 caracteres.')
        if ' ' in nuevo:
            raise ValidationError('La nueva contraseña no puede contener espacios.')
        return nuevo

    def clean(self):
        cleaned_data = super().clean()
        actual = cleaned_data.get('password_actual')
        nuevo = cleaned_data.get('nuevo_password')
        confirmar = cleaned_data.get('confirmar_nuevo_password')
        if nuevo and confirmar and nuevo != confirmar:
            self.add_error('confirmar_nuevo_password', 'Las nuevas contraseñas no coinciden.')
        if actual and nuevo and actual == nuevo:
            self.add_error('nuevo_password', 'La nueva contraseña debe ser diferente a la contraseña actual.')
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
        p1 = cleaned_data.get('password1', '').strip() if cleaned_data.get('password1') else ''
        p2 = cleaned_data.get('password2', '').strip() if cleaned_data.get('password2') else ''
        if not p1:
            self.add_error('password1', 'La contraseña es obligatoria.')
        elif len(p1) < 6:
            self.add_error('password1', 'La contraseña debe tener al menos 6 caracteres.')
        elif ' ' in p1:
            self.add_error('password1', 'La contraseña no puede contener espacios.')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        return cleaned_data


class CheckoutForm(forms.Form):
    departamento = forms.CharField(
        label='Departamento',
        max_length=100,
        required=True,
        widget=forms.Select(attrs={'class': 'select-departamento'})
    )
    ciudad = forms.CharField(
        label='Ciudad',
        max_length=100,
        required=True,
        widget=forms.Select(attrs={'class': 'select-ciudad'})
    )
    direccion_envio = forms.CharField(
        label='Dirección (calle/carrera, número, barrio)',
        max_length=300,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej. Cra 45 #10-20, Barrio Laureles'}),
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

    def clean_departamento(self):
        depto = self.cleaned_data.get('departamento', '').strip()
        if not depto:
            raise ValidationError('Selecciona un departamento.')
        return depto

    def clean_ciudad(self):
        ciudad = self.cleaned_data.get('ciudad', '').strip()
        if not ciudad:
            raise ValidationError('Selecciona una ciudad.')
        return ciudad

    def clean_direccion_envio(self):
        direccion = self.cleaned_data.get('direccion_envio', '').strip()
        if not direccion:
            raise ValidationError('La dirección es obligatoria.')
        if len(direccion) < 10:
            raise ValidationError('La dirección debe tener al menos 10 caracteres.')
        if not any(c.isalpha() for c in direccion):
            raise ValidationError('Ingresa una dirección válida.')
        return direccion

    def clean_notas(self):
        notas = (self.cleaned_data.get('notas') or '').strip()
        if notas and not any(c.isalnum() for c in notas):
            raise ValidationError('Escribe notas válidas.')
        return notas

    def clean(self):
        cleaned_data = super().clean()
        depto = cleaned_data.get('departamento')
        ciudad = cleaned_data.get('ciudad')
        detalle = cleaned_data.get('direccion_envio')
        if depto and ciudad and detalle:
            cleaned_data['direccion_envio'] = f"{detalle}, {ciudad}, {depto}"
        return cleaned_data

    def clean_telefono_contacto(self):
        telefono = self.cleaned_data.get('telefono_contacto', '').strip()
        if not telefono:
            raise ValidationError('El teléfono de contacto es obligatorio.')
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


# ──────────────────────────────────────────────
# PERSONALIZACIÓN Y COMUNIDAD
# ──────────────────────────────────────────────

class PersonalizacionForm(forms.ModelForm):
    class Meta:
        model = Personalizacion
        fields = [
            'producto', 'nombre_personalizacion', 'tipo', 'talla',
            'color', 'estampado', 'tipografia', 'detalle'
        ]
        widgets = {
            'nombre_personalizacion': forms.TextInput(attrs={
                'placeholder': 'Ej. Hoodie Cyber Acid V1'
            }),
            'detalle': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': '500',
                'placeholder': 'Describe el concepto, ubicación del estampado o detalles de tu diseño personalizado...'
            }),
        }
        labels = {
            'producto': 'Producto base disponible',
            'nombre_personalizacion': 'Nombre de la personalización',
            'tipo': 'Tipo de corte / silueta',
            'talla': 'Talla',
            'color': 'Color base',
            'estampado': 'Estampado oficial Haze Studios',
            'tipografia': 'Tipografía oficial Haze Studios',
            'detalle': 'Detalle de la personalización',
        }

    def __init__(self, *args, **kwargs):
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.all().order_by(
            '-estado', '-stock', 'nombre'
        )
        self.fields['producto'].empty_label = 'Selecciona una prenda base del catálogo'

    def clean_producto(self):
        producto = self.cleaned_data.get('producto')
        if not producto:
            raise ValidationError('Debes seleccionar un producto base.')
        if producto.estado != 'activo' or producto.stock <= 0:
            raise ValidationError(
                'No puedes personalizar productos que no están disponibles o están agotados.'
            )
        return producto

    def clean_nombre_personalizacion(self):
        return validar_nombre_con_letras(
            self.cleaned_data.get('nombre_personalizacion'),
            'El nombre de la personalización',
            min_len=3,
        )

    def clean_detalle(self):
        return validar_texto_descriptivo(
            self.cleaned_data.get('detalle'),
            'un detalle descriptivo',
            min_len=10,
            max_len=500,
        )

    def clean(self):
        cleaned_data = super().clean()
        if self.cliente:
            producto = cleaned_data.get('producto')
            nombre = (cleaned_data.get('nombre_personalizacion') or '').strip()
            tipo = cleaned_data.get('tipo')
            talla = cleaned_data.get('talla')
            color = cleaned_data.get('color')
            estampado = cleaned_data.get('estampado')
            tipografia = cleaned_data.get('tipografia')

            if producto and nombre and tipo and talla and color and estampado and tipografia:
                qs = Personalizacion.objects.filter(
                    cliente=self.cliente,
                    estado='en_proceso',
                    producto=producto,
                    nombre_personalizacion__iexact=nombre,
                    tipo=tipo,
                    talla=talla,
                    color=color,
                    estampado=estampado,
                    tipografia=tipografia,
                )
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise ValidationError(
                        'Ya tienes una personalización en proceso igual a esta.'
                    )
        return cleaned_data


class PrendaComunidadPublicarForm(forms.ModelForm):
    personalizacion = forms.ModelChoiceField(
        queryset=Personalizacion.objects.none(),
        required=True,
        label='Personalización a publicar',
        empty_label='— Selecciona una de tus personalizaciones —'
    )

    class Meta:
        model = PrendaComunidad
        fields = [
            'personalizacion', 'nombre', 'descripcion',
            'color', 'talla', 'estampado', 'tipografia'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre de la prenda personalizada'}),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': '600',
                'placeholder': 'Cuéntale a la comunidad la inspiración y detalles de tu prenda...'
            }),
        }
        labels = {
            'nombre': 'Nombre de la prenda',
            'descripcion': 'Descripción',
            'color': 'Color',
            'talla': 'Talla',
            'estampado': 'Estampado usado',
            'tipografia': 'Tipografía usada',
        }

    def __init__(self, *args, **kwargs):
        self.cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        if self.cliente:
            self.fields['personalizacion'].queryset = Personalizacion.objects.filter(
                cliente=self.cliente
            ).select_related('producto').order_by('-fecha_creacion')
            self.fields['personalizacion'].label_from_instance = (
                lambda obj: f"{obj.nombre_personalizacion} — {obj.producto.nombre} ({obj.color} · {obj.talla})"
            )

    def clean_nombre(self):
        return validar_nombre_con_letras(
            self.cleaned_data.get('nombre'),
            'El nombre de la prenda',
            min_len=3,
        )

    def clean_descripcion(self):
        return validar_texto_descriptivo(
            self.cleaned_data.get('descripcion'),
            'una descripción',
            min_len=10,
            max_len=600,
        )

    def clean_personalizacion(self):
        pers = self.cleaned_data.get('personalizacion')
        if not pers:
            raise ValidationError('Debes seleccionar una personalización para publicar en la comunidad.')
        if self.cliente and pers.cliente_id != self.cliente.pk:
            raise ValidationError('No puedes publicar una personalización que no te pertenece.')
        if hasattr(pers, 'publicacion_comunidad') and pers.publicacion_comunidad is not None:
            raise ValidationError(
                'Esta personalización ya se encuentra publicada en la comunidad. Puedes editarla desde tu perfil o en la comunidad.'
            )
        if pers.producto and (pers.producto.estado != 'activo' or pers.producto.stock <= 0):
            raise ValidationError(
                'El producto base de esta personalización ya no está disponible o está agotado.'
            )
        return pers

    def clean(self):
        cleaned_data = super().clean()
        if self.cliente:
            nombre = (cleaned_data.get('nombre') or '').strip()
            color = (cleaned_data.get('color') or '').strip()
            talla = (cleaned_data.get('talla') or '').strip()
            estampado = (cleaned_data.get('estampado') or '').strip()
            tipografia = (cleaned_data.get('tipografia') or '').strip()

            if nombre and color and talla and estampado and tipografia:
                duplicado = PrendaComunidad.objects.filter(
                    autor=self.cliente,
                    estado='activo',
                    nombre__iexact=nombre,
                    color__iexact=color,
                    talla__iexact=talla,
                    estampado__iexact=estampado,
                    tipografia__iexact=tipografia,
                ).exists()
                if duplicado:
                    raise ValidationError(
                        'No es posible crear esta publicación: ya tienes una publicación activa con las mismas especificaciones (nombre, color, talla, estampado y tipografía).'
                    )
        return cleaned_data


class PrendaComunidadEditarForm(forms.ModelForm):
    class Meta:
        model = PrendaComunidad
        fields = [
            'nombre', 'descripcion', 'color',
            'talla', 'estampado', 'tipografia', 'estado'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre de la prenda personalizada'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'maxlength': '600'}),
        }
        labels = {
            'nombre': 'Nombre de la prenda',
            'descripcion': 'Descripción',
            'color': 'Color',
            'talla': 'Talla',
            'estampado': 'Estampado usado',
            'tipografia': 'Tipografía usada',
            'estado': 'Estado de la publicación',
        }

    def clean_nombre(self):
        return validar_nombre_con_letras(
            self.cleaned_data.get('nombre'),
            'El nombre de la prenda',
            min_len=3,
        )

    def clean_descripcion(self):
        return validar_texto_descriptivo(
            self.cleaned_data.get('descripcion'),
            'una descripción',
            min_len=10,
            max_len=600,
        )

    def clean_estado(self):
        estado = self.cleaned_data.get('estado')
        if self.instance and self.instance.pk and self.instance.motivo_inactivacion and estado == 'activo':
            raise ValidationError('Esta publicación fue inactivada por administración y no puede reactivarse.')
        return estado

    def clean(self):
        cleaned_data = super().clean()
        autor = getattr(self.instance, 'autor', None)
        estado = cleaned_data.get('estado', 'activo')
        if autor and estado == 'activo':
            nombre = (cleaned_data.get('nombre') or '').strip()
            color = (cleaned_data.get('color') or '').strip()
            talla = (cleaned_data.get('talla') or '').strip()
            estampado = (cleaned_data.get('estampado') or '').strip()
            tipografia = (cleaned_data.get('tipografia') or '').strip()

            if nombre and color and talla and estampado and tipografia:
                qs = PrendaComunidad.objects.filter(
                    autor=autor,
                    estado='activo',
                    nombre__iexact=nombre,
                    color__iexact=color,
                    talla__iexact=talla,
                    estampado__iexact=estampado,
                    tipografia__iexact=tipografia,
                )
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise ValidationError(
                        'Ya tienes otra publicación activa con estas mismas especificaciones exactas.'
                    )
        return cleaned_data


class ComentarioComunidadForm(forms.ModelForm):
    class Meta:
        model = ComentarioComunidad
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'rows': 2,
                'maxlength': '400',
                'placeholder': 'Escribe un comentario sobre este diseño...'
            })
        }

    def clean_contenido(self):
        return validar_comentario_texto(self.cleaned_data.get('contenido'), max_len=400)

