from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True, default='')),
            ],
            options={'verbose_name': 'Categoría', 'verbose_name_plural': 'Categorías', 'db_table': 'categorias', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('apellido', models.CharField(max_length=100)),
                ('correo', models.EmailField(unique=True)),
                ('telefono', models.CharField(blank=True, default='', max_length=30)),
                ('direccion', models.TextField(blank=True, default='')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('contraseña', models.CharField(max_length=255)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo', max_length=20)),
            ],
            options={'verbose_name': 'Cliente', 'verbose_name_plural': 'Clientes', 'db_table': 'clientes', 'ordering': ['nombre', 'apellido']},
        ),
        migrations.CreateModel(
            name='Disenador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
            ],
            options={'verbose_name': 'Diseñador', 'verbose_name_plural': 'Diseñadores', 'db_table': 'disenadores', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('telefono', models.CharField(blank=True, default='', max_length=30)),
                ('correo', models.EmailField(blank=True, default='')),
                ('direccion', models.TextField(blank=True, default='')),
            ],
            options={'verbose_name': 'Proveedor', 'verbose_name_plural': 'Proveedores', 'db_table': 'proveedores', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('precio', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo', max_length=20)),
                ('categoria', models.ForeignKey(blank=True, db_column='id_categoria', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='productos', to='dashboard.categoria')),
                ('proveedor', models.ForeignKey(blank=True, db_column='id_proveedor', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='productos', to='dashboard.proveedor')),
                ('disenador', models.ForeignKey(blank=True, db_column='id_disenador', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='productos', to='dashboard.disenador')),
            ],
            options={'verbose_name': 'Producto', 'verbose_name_plural': 'Productos', 'db_table': 'productos', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_pedido', models.DateField()),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('procesando', 'Procesando'), ('enviado', 'Enviado'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20)),
                ('total', models.DecimalField(decimal_places=2, max_digits=14)),
                ('cliente', models.ForeignKey(db_column='id_cliente', on_delete=django.db.models.deletion.CASCADE, related_name='pedidos', to='dashboard.cliente')),
            ],
            options={'verbose_name': 'Pedido', 'verbose_name_plural': 'Pedidos', 'db_table': 'pedidos', 'ordering': ['-fecha_pedido']},
        ),
        migrations.CreateModel(
            name='Inventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock', models.PositiveIntegerField(default=0)),
                ('fecha_actualizacion', models.DateField()),
                ('producto', models.ForeignKey(db_column='id_producto', on_delete=django.db.models.deletion.CASCADE, related_name='inventario', to='dashboard.producto')),
            ],
            options={'verbose_name': 'Inventario', 'db_table': 'inventario', 'ordering': ['producto__nombre']},
        ),
    ]
