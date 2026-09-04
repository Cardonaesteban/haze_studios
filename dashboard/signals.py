from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Rol


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_superuser:
        rol_admin, _ = Rol.objects.get_or_create(
            nombre='admin',
            defaults={'descripcion': 'Administrador', 'estado': 'activo'}
        )
        PerfilUsuario.objects.get_or_create(user=instance, defaults={'rol': rol_admin})
    else:
        PerfilUsuario.objects.get_or_create(user=instance)