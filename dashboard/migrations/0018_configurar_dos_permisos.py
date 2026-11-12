from django.db import migrations


def configurar_dos_permisos(apps, schema_editor):
    Permiso = apps.get_model('dashboard', 'Permiso')
    Rol = apps.get_model('dashboard', 'Rol')

    # 1. Crear / obtener los 2 permisos oficiales
    permiso_admin, _ = Permiso.objects.get_or_create(
        codigo='administrador',
        defaults={
            'nombre': 'Administrador',
            'descripcion': 'Permiso de administrador con acceso completo al panel y módulos del Dashboard.',
        }
    )
    # Actualizar por si existía con otros valores
    permiso_admin.nombre = 'Administrador'
    permiso_admin.descripcion = 'Permiso de administrador con acceso completo al panel y módulos del Dashboard.'
    permiso_admin.save()

    permiso_cliente, _ = Permiso.objects.get_or_create(
        codigo='cliente',
        defaults={
            'nombre': 'Cliente',
            'descripcion': 'Permiso de cliente / usuario estándar. Sin acceso al panel administrativo.',
        }
    )
    permiso_cliente.nombre = 'Cliente'
    permiso_cliente.descripcion = 'Permiso de cliente / usuario estándar. Sin acceso al panel administrativo.'
    permiso_cliente.save()

    # 2. Eliminar permisos residuales para que solo existan 'administrador' y 'cliente'
    Permiso.objects.exclude(codigo__in=['administrador', 'cliente']).delete()

    # 3. Asignar 'administrador' al rol admin
    for rol_admin in Rol.objects.filter(nombre__in=['admin', 'administrador', 'Administrador']):
        rol_admin.permisos.add(permiso_admin)

    # 4. Asignar 'cliente' al rol usuario
    for rol_usuario in Rol.objects.filter(nombre__in=['usuario', 'cliente', 'Usuario', 'Cliente']):
        rol_usuario.permisos.add(permiso_cliente)


def revertir_permisos(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_alter_rol_nombre'),
    ]

    operations = [
        migrations.RunPython(configurar_dos_permisos, revertir_permisos),
    ]
