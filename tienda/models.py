import uuid
from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.templatetags.static import static
from dashboard.models import Cliente, Producto


class TokenRecuperacionCliente(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='tokens_recuperacion'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    class Meta:
        db_table = 'token_recuperacion_cliente'
        verbose_name = 'Token de recuperación (Cliente)'
        verbose_name_plural = 'Tokens de recuperación (Clientes)'
        ordering = ['-creado']

    def __str__(self):
        return f'Token de {self.cliente.correo} — {self.token}'

    def es_valido(self):
        limite = self.creado + timedelta(hours=2)
        return not self.usado and timezone.now() < limite


class Favorito(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='favoritos'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='favoritos_clientes',
        null=True, blank=True
    )
    prenda_comunidad = models.ForeignKey(
        'PrendaComunidad', on_delete=models.CASCADE, related_name='favoritos_clientes',
        null=True, blank=True
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favoritos'
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        ordering = ['-fecha_agregado']

    def __str__(self):
        if self.producto:
            return f'{self.cliente} — {self.producto.nombre}'
        elif self.prenda_comunidad:
            return f'{self.cliente} — {self.prenda_comunidad.nombre} (Comunidad)'
        return f'{self.cliente} — Favorito #{self.pk}'


# ──────────────────────────────────────────────
# CATÁLOGO OFICIAL DE PERSONALIZACIÓN Y COMUNIDAD
# ──────────────────────────────────────────────

TIPOS_PRENDA_CHOICES = [
    ('Hoodie Oversize', 'Hoodie Oversize (Algodón 450g)'),
    ('T-Shirt Heavyweight', 'T-Shirt Heavyweight (280g)'),
    ('Crewneck Sweatshirt', 'Crewneck Sweatshirt'),
    ('Bomber Jacket', 'Bomber Jacket Streetwear'),
    ('Cargo Pants', 'Cargo Pants Relaxed Fit'),
]

TALLAS_COMUNIDAD_CHOICES = [
    ('S (Oversize)', 'S (Oversize)'),
    ('M (Oversize)', 'M (Oversize)'),
    ('L (Oversize)', 'L (Oversize)'),
    ('XL (Oversize)', 'XL (Oversize)'),
]

COLORES_COMUNIDAD_CHOICES = [
    ('Negro Obsidiana', 'Negro Obsidiana'),
    ('Blanco Hueso', 'Blanco Hueso'),
    ('Gris Carbón', 'Gris Carbón'),
    ('Azul Cobalto Haze', 'Azul Cobalto Haze'),
    ('Púrpura Nocturno', 'Púrpura Nocturno'),
]

ESTAMPADOS_OFICIALES_CHOICES = [
    ('Acid Butterfly', 'Acid Butterfly — Gráfico Cyberpunk en espalda'),
    ('Gothic Cross Haze', 'Gothic Cross Haze — Cruz gótica urbana'),
    ('Distorted Cyber Skull', 'Distorted Cyber Skull — Arte Glitch frontal'),
    ('Minimal Studio Signature', 'Minimal Studio Signature — Emblema minimalista en pecho'),
    ('Tokyo Night Skyline', 'Tokyo Night Skyline — Ilustración neón nocturna'),
]

TIPOGRAFIAS_OFICIALES_CHOICES = [
    ('Oversize Heavy Metal', 'Oversize Heavy Metal — Gótica Blackletter'),
    ('Modern Cyber Tech', 'Modern Cyber Tech — Futurista Geométrica'),
    ('Brutalism Bold Sans', 'Brutalism Bold Sans — Sans-Serif Industrial'),
    ('Vintage Y2K Italic', 'Vintage Y2K Italic — Cursiva Retro 2000s'),
]


class Personalizacion(models.Model):
    ESTADO_CHOICES = [
        ('en_proceso', 'En proceso'),
        ('publicada', 'Publicada'),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='personalizaciones'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='personalizaciones'
    )
    nombre_personalizacion = models.CharField(max_length=150)
    tipo = models.CharField(
        max_length=80, choices=TIPOS_PRENDA_CHOICES, default='Hoodie Oversize'
    )
    talla = models.CharField(
        max_length=40, choices=TALLAS_COMUNIDAD_CHOICES, default='L (Oversize)'
    )
    color = models.CharField(
        max_length=60, choices=COLORES_COMUNIDAD_CHOICES, default='Negro Obsidiana'
    )
    detalle = models.TextField(
        max_length=500,
        help_text='Detalles y concepto de tu personalización'
    )
    estampado = models.CharField(
        max_length=100, choices=ESTAMPADOS_OFICIALES_CHOICES, default='Acid Butterfly'
    )
    tipografia = models.CharField(
        max_length=100, choices=TIPOGRAFIAS_OFICIALES_CHOICES, default='Brutalism Bold Sans'
    )
    imagen_preview = models.ImageField(
        upload_to='personalizaciones/', null=True, blank=True
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='en_proceso'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'personalizaciones_clientes'
        verbose_name = 'Personalización'
        verbose_name_plural = 'Personalizaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre_personalizacion} ({self.cliente.nombre})'

    def get_imagen_url(self):
        if self.imagen_preview:
            return self.imagen_preview.url
        if self.producto:
            return self.producto.get_imagen_url()
        return static('img/products/hoodie_black.jpg')

    def clean(self):
        super().clean()
        if self.producto_id:
            if self.producto.estado != 'activo' or self.producto.stock <= 0:
                raise ValidationError({
                    'producto': 'No se permite realizar personalizaciones para productos no disponibles o agotados.'
                })


class PrendaComunidad(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    autor = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='prendas_comunidad'
    )
    personalizacion = models.OneToOneField(
        Personalizacion, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='publicacion_comunidad'
    )
    producto_base = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='publicaciones_comunidad'
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(max_length=600)
    imagen = models.ImageField(upload_to='comunidad/', null=True, blank=True)
    color = models.CharField(max_length=60, choices=COLORES_COMUNIDAD_CHOICES)
    talla = models.CharField(max_length=40, choices=TALLAS_COMUNIDAD_CHOICES)
    estampado = models.CharField(max_length=100, choices=ESTAMPADOS_OFICIALES_CHOICES)
    tipografia = models.CharField(max_length=100, choices=TIPOGRAFIAS_OFICIALES_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    motivo_inactivacion = models.CharField(max_length=255, blank=True, default='')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prendas_comunidad'
        verbose_name = 'Prenda de la Comunidad'
        verbose_name_plural = 'Prendas de la Comunidad'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f'{self.nombre} por {self.autor}'

    def toggle_estado(self):
        self.estado = 'inactivo' if self.estado == 'activo' else 'activo'
        self.save(update_fields=['estado'])

    def get_imagen_url(self):
        if self.imagen:
            return self.imagen.url
        if self.personalizacion and self.personalizacion.imagen_preview:
            return self.personalizacion.imagen_preview.url
        if self.producto_base:
            return self.producto_base.get_imagen_url()
        if self.personalizacion and self.personalizacion.producto:
            return self.personalizacion.producto.get_imagen_url()
        color_lower = (self.color or '').lower()
        if 'blanco' in color_lower or 'hueso' in color_lower:
            return static('img/products/hoodie_cream.jpg')
        if 'gris' in color_lower:
            return static('img/products/crewneck_charcoal.jpg')
        return static('img/products/hoodie_black.jpg')

    def tiene_duplicado_activo(self):
        """
        Verifica si el mismo autor ya tiene otra publicación activa con las mismas especificaciones.
        """
        if not self.autor_id:
            return False
        qs = PrendaComunidad.objects.filter(
            autor_id=self.autor_id,
            estado='activo',
            nombre__iexact=(self.nombre or '').strip(),
            color__iexact=(self.color or '').strip(),
            talla__iexact=(self.talla or '').strip(),
            estampado__iexact=(self.estampado or '').strip(),
            tipografia__iexact=(self.tipografia or '').strip(),
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs.exists()

    def clean(self):
        super().clean()
        if self.estado == 'activo' and self.tiene_duplicado_activo():
            raise ValidationError(
                'Ya tienes una publicación activa en la comunidad con estas mismas especificaciones exactas.'
            )


class ComentarioComunidad(models.Model):
    prenda = models.ForeignKey(
        PrendaComunidad, on_delete=models.CASCADE, related_name='comentarios'
    )
    autor = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='comentarios_comunidad'
    )
    contenido = models.TextField(max_length=400)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_edicion = models.DateTimeField(auto_now=True)
    editado = models.BooleanField(default=False)

    class Meta:
        db_table = 'comentarios_comunidad'
        verbose_name = 'Comentario de Comunidad'
        verbose_name_plural = 'Comentarios de Comunidad'
        ordering = ['fecha_publicacion']

    def __str__(self):
        return f'Comentario de {self.autor} en {self.prenda.nombre}'


class ReaccionComunidad(models.Model):
    prenda = models.ForeignKey(
        PrendaComunidad, on_delete=models.CASCADE, related_name='reacciones'
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='reacciones_comunidad'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reacciones_comunidad'
        verbose_name = 'Reacción de Comunidad'
        verbose_name_plural = 'Reacciones de Comunidad'
        unique_together = ('prenda', 'cliente')

    def __str__(self):
        return f'Reacción de {self.cliente} a {self.prenda.nombre}'
