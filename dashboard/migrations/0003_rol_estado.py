from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_roles_permisos_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='rol',
            name='estado',
            field=models.CharField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo', max_length=20),
        ),
    ]
