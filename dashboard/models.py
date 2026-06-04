from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


# ──────────────────────────────────────────────
# ROLES Y PERMISOS
# ──────────────────────────────────────────────

class Permiso(models.Model):
    codigo = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'permisos'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'


class Rol(models.Model):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('usuario', 'Usuario'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombre = models.CharField(
        max_length=20, choices=ROL_CHOICES, unique=True
    )
    descripcion = models.TextField(blank=True, default='')
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='activo'
    )
    permisos = models.ManyToManyField(Permiso, blank=True, related_name='roles')

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']

    def __str__(self):
        return self.get_nombre_display()

    def get_nombre_display(self):
        return dict(self.ROL_CHOICES).get(self.nombre, self.nombre)

    def toggle_estado(self):
        self.estado = 'inactivo' if self.estado == 'activo' else 'activo'
        self.save()


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.ForeignKey(
        Rol, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios'
    )

    class Meta:
        db_table = 'perfiles_usuario'
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'{self.user.username} — {self.rol}'

    def es_admin(self):
        return self.rol and self.rol.nombre == 'admin'

    def tiene_permiso(self, codigo):
        if not self.rol:
            return False
        return self.rol.permisos.filter(codigo=codigo).exists()


# ──────────────────────────────────────────────
# CATÁLOGO
# ──────────────────────────────────────────────

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True, default='')
    correo = models.EmailField(blank=True, default='')
    direccion = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Disenador(models.Model):
    nombre = models.CharField(max_length=150)

    class Meta:
        db_table = 'disenadores'
        verbose_name = 'Diseñador'
        verbose_name_plural = 'Diseñadores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, help_text='Stock disponible actual')
    stock_minimo = models.PositiveIntegerField(default=0, help_text='Alerta cuando el stock baje de este nivel')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_categoria', related_name='productos'
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_proveedor', related_name='productos'
    )
    disenador = models.ForeignKey(
        Disenador, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_disenador', related_name='productos'
    )

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def toggle_estado(self):
        self.estado = 'inactivo' if self.estado == 'activo' else 'activo'
        self.save()

    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    def clean(self):
        if self.precio is not None and self.precio < 0:
            raise ValidationError({'precio': 'El precio no puede ser negativo.'})


# ──────────────────────────────────────────────
# MOVIMIENTOS DE STOCK
# ──────────────────────────────────────────────

class MovimientoStock(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]

    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE,
        db_column='id_producto', related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    stock_anterior = models.IntegerField()
    stock_posterior = models.IntegerField()
    motivo = models.CharField(max_length=255, blank=True, default='')
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_stock'
    )
    pedido = models.ForeignKey(
        'Pedido', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_stock'
    )

    class Meta:
        db_table = 'movimientos_stock'
        verbose_name = 'Movimiento de stock'
        verbose_name_plural = 'Movimientos de stock'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.producto.nombre} ({self.cantidad})'

    def get_tipo_display(self):
        return dict(self.TIPO_CHOICES).get(self.tipo, self.tipo)

    def clean(self):
        if self.cantidad == 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor que cero.'})
        if self.tipo == 'salida' and self.producto is not None:
            producto = self.producto
            if self.cantidad > producto.stock:
                raise ValidationError({
                    'cantidad': f'Stock insuficiente. Disponible: {producto.stock}'
                })


# ──────────────────────────────────────────────
# CLIENTES
# ──────────────────────────────────────────────

class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True, default='')
    direccion = models.TextField(blank=True, default='')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    contraseña = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre', 'apellido']

    def __str__(self):
        return f'{self.nombre} {self.apellido}'

    def toggle_estado(self):
        self.estado = 'inactivo' if self.estado == 'activo' else 'activo'
        self.save()


# ──────────────────────────────────────────────
# PEDIDOS
# ──────────────────────────────────────────────

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE,
        db_column='id_cliente', related_name='pedidos'
    )
    fecha_pedido = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    notas = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f'Pedido #{self.pk} — {self.cliente}'

    def toggle_estado(self):
        estados = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
        idx = estados.index(self.estado)
        self.estado = estados[(idx + 1) % len(estados)]
        self.save()

    def calcular_total(self):
        total = sum(d.subtotal() for d in DetallePedido.objects.filter(pedido=self))
        self.total = total
        self.save(update_fields=['total'])
        return total


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='detalles_pedido'
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'detalles_pedido'
        verbose_name = 'Detalle de pedido'
        verbose_name_plural = 'Detalles de pedido'

    def __str__(self):
        return f'{self.producto.nombre} x {self.cantidad}'

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def clean(self):
        if self.cantidad is not None and self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser al menos 1.'})
        if self.precio_unitario is not None and self.precio_unitario < 0:
            raise ValidationError({'precio_unitario': 'El precio no puede ser negativo.'})


# ──────────────────────────────────────────────
# INVENTARIO (histórico / ajuste manual)
# ──────────────────────────────────────────────

class Inventario(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE,
        db_column='id_producto', related_name='inventario'
    )
    stock = models.PositiveIntegerField(default=0)
    fecha_actualizacion = models.DateField()

    class Meta:
        db_table = 'inventario'
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventario'
        ordering = ['producto__nombre']

    def __str__(self):
        return f'{self.producto.nombre} — stock: {self.stock}'


# ──────────────────────────────────────────────
# TOKEN RECUPERACIÓN DE CONTRASEÑA (Admin)
# ──────────────────────────────────────────────

import uuid as _uuid
from datetime import timedelta as _timedelta

class TokenRecuperacion(models.Model):
    usuario  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tokens_recuperacion')
    token    = models.UUIDField(default=_uuid.uuid4, editable=False, unique=True)
    creado   = models.DateTimeField(auto_now_add=True)
    usado    = models.BooleanField(default=False)

    class Meta:
        db_table = 'token_recuperacion'
        verbose_name = 'Token de recuperación'
        verbose_name_plural = 'Tokens de recuperación'
        ordering = ['-creado']

    def __str__(self):
        return f'Token de {self.usuario.username} — {self.token}'

    def es_valido(self):
        from django.utils import timezone
        limite = self.creado + _timedelta(hours=2)
        return not self.usado and timezone.now() < limite



