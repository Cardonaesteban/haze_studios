from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import (
    Cliente, Producto, Categoria, Proveedor, Disenador,
    Pedido, DetallePedido, MovimientoStock,
    Rol, Permiso, PerfilUsuario
)


# ──────────────────────────────────────────────
# CLIENTES
# ──────────────────────────────────────────────

class ClienteForm(forms.ModelForm):
    contraseña = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        label='Contraseña',
        help_text='Mínimo 6 caracteres. Dejar en blanco para mantener la actual al editar.',
        min_length=6
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'direccion', 'contraseña', 'estado']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_nombre(self):
        v = self.cleaned_data.get('nombre', '').strip()
        if not v:
            raise ValidationError('El nombre es obligatorio.')
        if len(v) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return v

    def clean_apellido(self):
        v = self.cleaned_data.get('apellido', '').strip()
        if not v:
            raise ValidationError('El apellido es obligatorio.')
        if len(v) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        return v

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip().lower()
        if not correo:
            raise ValidationError('El correo es obligatorio.')
        qs = Cliente.objects.filter(correo=correo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un cliente con este correo.')
        return correo

    def clean_contraseña(self):
        pwd = self.cleaned_data.get('contraseña', '')
        # Si es edición y viene vacío, OK (mantiene la actual)
        if not pwd and self.instance.pk:
            return ''
        # Si es creación, la contraseña es obligatoria
        if not pwd and not self.instance.pk:
            raise ValidationError('La contraseña es obligatoria para nuevos usuarios.')
        if pwd and len(pwd) < 6:
            raise ValidationError('La contraseña debe tener al menos 6 caracteres.')
        return pwd

    def save(self, commit=True):
        cliente = super().save(commit=False)
        pwd = self.cleaned_data.get('contraseña')
        if pwd:
            cliente.contraseña = make_password(pwd)
        elif not cliente.pk:
            cliente.contraseña = make_password('')
        if commit:
            cliente.save()
        return cliente


# ──────────────────────────────────────────────
# PRODUCTOS
# ──────────────────────────────────────────────

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'precio', 'stock',
            'stock_minimo', 'estado', 'categoria', 'proveedor', 'disenador'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre del producto es obligatorio.')
        return nombre

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None:
            raise ValidationError('El precio es obligatorio.')
        if precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise ValidationError('El stock no puede ser negativo.')
        return stock


# ──────────────────────────────────────────────
# CATEGORÍAS
# ──────────────────────────────────────────────

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre de la categoría es obligatorio.')
        qs = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe una categoría con ese nombre.')
        return nombre


# ──────────────────────────────────────────────
# PROVEEDORES
# ──────────────────────────────────────────────

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'correo', 'direccion']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre del proveedor es obligatorio.')
        return nombre

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip()
        # correo es opcional en proveedor, pero si viene debe ser válido (el campo EmailField ya lo valida)
        return correo


# ──────────────────────────────────────────────
# DISEÑADORES
# ──────────────────────────────────────────────

class DisenadorForm(forms.ModelForm):
    class Meta:
        model = Disenador
        fields = ['nombre']

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        qs = Disenador.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un diseñador con ese nombre.')
        return nombre


# ──────────────────────────────────────────────
# PEDIDOS
# ──────────────────────────────────────────────

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'fecha_pedido', 'estado', 'notas']
        widgets = {
            'fecha_pedido': forms.DateInput(attrs={'type': 'date'}),
            'notas': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_cliente(self):
        cliente = self.cleaned_data.get('cliente')
        if not cliente:
            raise ValidationError('El cliente es obligatorio.')
        return cliente

    def clean_fecha_pedido(self):
        fecha = self.cleaned_data.get('fecha_pedido')
        if not fecha:
            raise ValidationError('La fecha del pedido es obligatoria.')
        return fecha


class DetallePedidoForm(forms.ModelForm):
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1, 'placeholder': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad <= 0:
            raise ValidationError('La cantidad debe ser al menos 1.')
        return cantidad

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio is not None and precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get('producto')
        cantidad = cleaned.get('cantidad')
        if producto and cantidad and cantidad > producto.stock:
            raise ValidationError(
                f'Stock insuficiente para "{producto.nombre}". Disponible: {producto.stock}'
            )
        return cleaned


DetallePedidoFormSet = forms.inlineformset_factory(
    Pedido, DetallePedido,
    form=DetallePedidoForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


# ──────────────────────────────────────────────
# MOVIMIENTOS DE STOCK
# ──────────────────────────────────────────────

class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ['producto', 'cantidad', 'motivo']
        widgets = {
            'motivo': forms.TextInput(attrs={'placeholder': 'Ej: Compra a proveedor, devolución, ajuste...'}),
            'cantidad': forms.NumberInput(attrs={'min': 1}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is None or cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor que cero.')
        return cantidad

    def clean_producto(self):
        producto = self.cleaned_data.get('producto')
        if not producto:
            raise ValidationError('Selecciona un producto.')
        return producto


# ──────────────────────────────────────────────
# ROLES Y PERMISOS
# ──────────────────────────────────────────────

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'estado', 'permisos']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
            'permisos': forms.CheckboxSelectMultiple(),
        }

    def save(self, commit=True):
        rol = super().save(commit=False)
        if commit:
            rol.save()
            self.save_m2m()
        return rol


class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['codigo', 'nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().lower().replace(' ', '_')
        if not codigo:
            raise ValidationError('El código es obligatorio.')
        qs = Permiso.objects.filter(codigo=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un permiso con ese código.')
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre del permiso es obligatorio.')
        return nombre


class AsignarRolForm(forms.ModelForm):
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(), required=False, label='Rol',
        empty_label='— Sin rol —'
    )

    class Meta:
        model = PerfilUsuario
        fields = ['rol']


class UsuarioDashboardForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput, required=False,
        help_text='Mínimo 8 caracteres. Dejar en blanco para no cambiar.'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña', widget=forms.PasswordInput, required=False
    )
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.all(), required=False, label='Rol',
        empty_label='— Sin rol —'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        qs = User.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 or p2:
            if not p1:
                raise ValidationError({'password1': 'Ingresa la contraseña.'})
            if len(p1) < 8:
                raise ValidationError({'password1': 'La contraseña debe tener al menos 8 caracteres.'})
            if p1 != p2:
                raise ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password1')
        if pwd:
            user.set_password(pwd)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
            rol = self.cleaned_data.get('rol')
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rol = rol
            perfil.save()
        return user


# ──────────────────────────────────────────────
# FORMULARIOS RECUPERACIÓN DE CONTRASEÑA
# ──────────────────────────────────────────────

class SolicitarRecuperacionForm(forms.Form):
    username = forms.CharField(
        label='Usuario',
        max_length=150,
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Nombre de usuario'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(username=username, is_staff=True)
        except User.DoesNotExist:
            raise forms.ValidationError('No se encontró un administrador con ese nombre de usuario.')
        return username


class CambiarContrasenaForm(forms.Form):
    password1 = forms.CharField(
        label='Nueva contraseña',
        min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la contraseña'})
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1', '')
        p2 = cleaned.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned
