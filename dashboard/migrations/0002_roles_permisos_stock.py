from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Permiso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=100, unique=True)),
                ('nombre', models.CharField(max_length=150)),
                ('descripcion', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Permiso',
                'verbose_name_plural': 'Permisos',
                'db_table': 'permisos',
                'ordering': ['codigo'],
            },
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(choices=[('admin', 'Administrador'), ('usuario', 'Usuario')], max_length=20, unique=True)),
                ('descripcion', models.TextField(blank=True, default='')),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roles',
                'db_table': 'roles',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
                ('rol', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios', to='dashboard.Rol')),
            ],
            options={
                'verbose_name': 'Perfil de usuario',
                'verbose_name_plural': 'Perfiles de usuario',
                'db_table': 'perfiles_usuario',
            },
        ),
        migrations.CreateModel(
            name='MovimientoStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('entrada', 'Entrada'), ('salida', 'Salida'), ('ajuste', 'Ajuste')], max_length=10)),
                ('cantidad', models.PositiveIntegerField()),
                ('stock_anterior', models.IntegerField()),
                ('stock_posterior', models.IntegerField()),
                ('motivo', models.CharField(blank=True, default='', max_length=255)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos', db_column='id_producto', to='dashboard.Producto')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimientos_stock', to=settings.AUTH_USER_MODEL)),
                ('pedido', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimientos_stock', to='dashboard.Pedido')),
            ],
            options={
                'verbose_name': 'Movimiento de stock',
                'verbose_name_plural': 'Movimientos de stock',
                'db_table': 'movimientos_stock',
                'ordering': ['-fecha'],
            },
        ),
        migrations.AddField(
            model_name='rol',
            name='permisos',
            field=models.ManyToManyField(blank=True, related_name='roles', to='dashboard.Permiso'),
        ),
    ]
