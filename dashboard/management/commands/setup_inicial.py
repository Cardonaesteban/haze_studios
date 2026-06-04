from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import Rol, PerfilUsuario


class Command(BaseCommand):
    help = 'Crea el rol admin y el superusuario inicial si no existen'

    def handle(self, *args, **kwargs):
        rol_admin, _ = Rol.objects.get_or_create(
            nombre='admin',
            defaults={'descripcion': 'Administrador con acceso total'}
        )
        Rol.objects.get_or_create(
            nombre='usuario',
            defaults={'descripcion': 'Usuario estándar'}
        )
        self.stdout.write('✓ Roles creados')

        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='admin@haze.com'
            )
            PerfilUsuario.objects.create(user=user, rol=rol_admin)
            self.stdout.write('✓ Usuario admin creado (contraseña: admin123)')
        else:
            user = User.objects.get(username='admin')
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rol = rol_admin
            perfil.save()
            self.stdout.write('✓ Usuario admin ya existía, rol asignado')

        self.stdout.write(self.style.SUCCESS('\nSetup completado. Entrá con admin / admin123'))