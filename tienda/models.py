import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
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
        Producto, on_delete=models.CASCADE, related_name='favoritos_clientes'
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favoritos'
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        ordering = ['-fecha_agregado']
        unique_together = ('cliente', 'producto')

    def __str__(self):
        return f'{self.cliente} — {self.producto.nombre}'
