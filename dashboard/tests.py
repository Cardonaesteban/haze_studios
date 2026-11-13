from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from dashboard.models import (
    Cliente, Producto, Categoria, Pedido, DetallePedido,
    Rol, PerfilUsuario, Mensaje, Proveedor
)
from dashboard.forms import (
    MensajeForm, ClienteForm, ProductoForm, ProductoEditarForm,
    ProveedorForm, UsuarioDashboardForm
)
from tienda.forms import (
    RegistroClienteForm, PerfilClienteForm, CambiarPasswordClienteForm,
    ConfirmarPasswordClienteForm, CheckoutForm
)
from tienda.models import Personalizacion
from dashboard.emails import enviar_notificacion_estado_pedido


class MensajesModuloTests(TestCase):
    def setUp(self):
        # Configurar usuario admin para el dashboard (la señal crea el perfil y rol admin automáticamente)
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@haze.com',
            password='password123'
        )
        self.perfil_admin = self.admin_user.perfil

        # Configurar clientes
        self.cliente1 = Cliente.objects.create(
            nombre='Carlos',
            apellido='Gómez',
            correo='carlos@example.com',
            telefono='3001234567',
            direccion='Calle 123 #45-67',
            contraseña='hashed_pass_123',
            estado='activo'
        )
        self.cliente2 = Cliente.objects.create(
            nombre='Ana',
            apellido='Martínez',
            correo='ana@example.com',
            telefono='3109876543',
            direccion='Carrera 78 #12-34',
            contraseña='hashed_pass_456',
            estado='activo'
        )

        # Configurar categoría, producto y pedido
        self.categoria = Categoria.objects.create(nombre='Ropa Urbana', descripcion='Moda urbana')
        self.producto = Producto.objects.create(
            nombre='Oversized Hoodie Black',
            descripcion='Saco urbano premium',
            precio=Decimal('180000.00'),
            stock=20,
            stock_minimo=5,
            estado='activo',
            categoria=self.categoria
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente1,
            fecha_pedido=date.today(),
            estado='pendiente',
            total=Decimal('180000.00')
        )
        self.detalle_pedido = DetallePedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal('180000.00')
        )

        self.client = Client()

    def test_validacion_longitud_maxima_contenido_modelo(self):
        """No debe permitir guardar mensajes con más de 500 caracteres a nivel de modelo."""
        contenido_501 = 'A' * 501
        mensaje = Mensaje(
            destinatario=self.cliente1,
            remitente='Haze Studios',
            tipo='informativo',
            contenido=contenido_501,
            estado='enviado'
        )
        with self.assertRaises(ValidationError):
            mensaje.save()

        # Mensaje con exactamente 500 caracteres debe guardarse exitosamente
        contenido_500 = 'B' * 500
        mensaje_valido = Mensaje(
            destinatario=self.cliente1,
            remitente='Haze Studios',
            tipo='informativo',
            contenido=contenido_500,
            estado='enviado'
        )
        mensaje_valido.save()
        self.assertIsNotNone(mensaje_valido.pk)
        self.assertEqual(len(mensaje_valido.contenido), 500)

    def test_validacion_longitud_maxima_formulario(self):
        """El formulario debe rechazar contenidos que superen 500 caracteres."""
        form_invalido = MensajeForm(data={
            'destinatario': self.cliente1.pk,
            'remitente': 'Haze Studios',
            'tipo': 'promocional',
            'contenido': 'X' * 501,
            'estado': 'enviado',
        })
        self.assertFalse(form_invalido.is_valid())
        self.assertIn('contenido', form_invalido.errors)

        form_valido = MensajeForm(data={
            'destinatario': self.cliente1.pk,
            'remitente': 'Haze Studios',
            'tipo': 'promocional',
            'contenido': 'X' * 500,
            'estado': 'enviado',
        })
        self.assertTrue(form_valido.is_valid())

    def test_validacion_destinatario_existente(self):
        """No debe permitir guardar mensajes si el usuario destinatario no existe."""
        # A nivel de modelo con destinatario inexistente
        mensaje_sin_destinatario = Mensaje(
            destinatario_id=999999,
            remitente='Haze Studios',
            tipo='soporte',
            contenido='Mensaje para usuario inexistente',
            estado='enviado'
        )
        with self.assertRaises(ValidationError):
            mensaje_sin_destinatario.save()

        # A nivel de formulario con ID de cliente inexistente
        form_inexistente = MensajeForm(data={
            'destinatario': 999999,
            'remitente': 'Haze Studios',
            'tipo': 'soporte',
            'contenido': 'Consulta de prueba',
            'estado': 'enviado',
        })
        self.assertFalse(form_inexistente.is_valid())
        self.assertIn('destinatario', form_inexistente.errors)

    def test_integracion_notificacion_pedido_crea_mensaje(self):
        """Al cambiar el estado de un pedido y notificar al cliente, se crea el mensaje correspondiente."""
        estado_anterior = self.pedido.estado
        self.pedido.estado = 'enviado'
        self.pedido.save()

        resultado = enviar_notificacion_estado_pedido(self.pedido, estado_anterior)
        self.assertTrue(resultado)

        # Verificar que el mensaje se registró en la base de datos
        mensaje = Mensaje.objects.filter(pedido=self.pedido).first()
        self.assertIsNotNone(mensaje)
        self.assertEqual(mensaje.destinatario, self.cliente1)
        self.assertEqual(mensaje.remitente, 'Haze Studios')
        self.assertEqual(mensaje.tipo, 'notificacion_pedido')
        self.assertEqual(mensaje.estado, 'enviado')
        self.assertIsNotNone(mensaje.fecha_envio)
        self.assertLessEqual(len(mensaje.contenido), 500)
        # Verificar que el contenido incluye el nuevo estado y el producto
        self.assertIn('Enviado', mensaje.contenido)
        self.assertIn('Oversized Hoodie Black', mensaje.contenido)

    def test_consulta_mensajes_list_y_campos(self):
        """La consulta de mensajes debe listar todos los campos requeridos y permitir filtrar por cliente."""
        # Crear mensajes de prueba
        m1 = Mensaje.objects.create(
            destinatario=self.cliente1,
            remitente='Haze Studios',
            tipo='notificacion_pedido',
            contenido='Tu pedido #1 ha sido enviado.',
            estado='enviado',
            pedido=self.pedido
        )
        m2 = Mensaje.objects.create(
            destinatario=self.cliente2,
            remitente='Atención al Cliente',
            tipo='promocional',
            contenido='¡Descuento especial de temporada!',
            estado='entregado'
        )

        self.client.force_login(self.admin_user)
        url = reverse('mensajes_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/mensajes/list.html')
        self.assertEqual(response.context['total_mensajes'], 2)

        # Verificar presencia de campos requeridos en la respuesta HTML
        self.assertContains(response, 'Carlos Gómez')
        self.assertContains(response, 'Ana Martínez')
        self.assertContains(response, 'Haze Studios')
        self.assertContains(response, 'Atención al Cliente')
        self.assertContains(response, 'Notificación de Pedido')
        self.assertContains(response, 'Promocional')
        self.assertContains(response, 'Tu pedido #1 ha sido enviado.')
        self.assertContains(response, '¡Descuento especial de temporada!')

        # Probar filtrado por cliente 1
        response_filtrado = self.client.get(url, {'cliente': self.cliente1.pk})
        self.assertEqual(response_filtrado.status_code, 200)
        self.assertEqual(response_filtrado.context['total_mensajes'], 1)
        self.assertEqual(response_filtrado.context['cliente_seleccionado'], self.cliente1.pk)
        mensajes_filtrados = list(response_filtrado.context['mensajes'])
        self.assertEqual(len(mensajes_filtrados), 1)
        self.assertEqual(mensajes_filtrados[0].pk, m1.pk)

    def test_mensajes_detalle_view(self):
        """La vista de detalle debe mostrar toda la información completa del mensaje."""
        m = Mensaje.objects.create(
            destinatario=self.cliente1,
            remitente='Haze Studios',
            tipo='soporte',
            contenido='Contenido detallado para soporte técnico sobre talla y material.',
            estado='entregado',
            pedido=self.pedido
        )

        self.client.force_login(self.admin_user)
        url = reverse('mensajes_detalle', args=[m.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/mensajes/detalle.html')
        self.assertContains(response, f'Mensaje #{m.pk}')
        self.assertContains(response, 'Carlos Gómez')
        self.assertContains(response, 'carlos@example.com')
        self.assertContains(response, 'Haze Studios')
        self.assertContains(response, 'Soporte')
        self.assertContains(response, 'Entregado')
        self.assertContains(response, 'Contenido detallado para soporte técnico sobre talla y material.')
        self.assertContains(response, f'Pedido #{self.pedido.pk}')

    def test_mensajes_crear_view(self):
        """Debe permitir registrar y enviar un mensaje manual a un usuario existente."""
        self.client.force_login(self.admin_user)
        url = reverse('mensajes_crear')

        datos = {
            'destinatario': self.cliente2.pk,
            'remitente': 'Soporte Haze',
            'tipo': 'soporte',
            'contenido': 'Hola Ana, respondiendo a tu consulta sobre tu envío.',
            'estado': 'enviado',
        }
        response = self.client.post(url, datos)
        self.assertRedirects(response, reverse('mensajes_list'))

        nuevo_mensaje = Mensaje.objects.filter(destinatario=self.cliente2, tipo='soporte').first()
        self.assertIsNotNone(nuevo_mensaje)
        self.assertEqual(nuevo_mensaje.remitente, 'Soporte Haze')
        self.assertEqual(nuevo_mensaje.contenido, 'Hola Ana, respondiendo a tu consulta sobre tu envío.')

    def test_navbar_contiene_enlace_mensajes(self):
        """La barra de navegación debe contener el enlace a Mensajes."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('mensajes_list'))
        self.assertContains(response, '>Mensajes</a>')

    def test_filtros_en_todos_los_modulos(self):
        """Verifica que todos los módulos del dashboard cuenten con el filtro uniforme implementado."""
        self.client.force_login(self.admin_user)

        # 1. Usuarios / Clientes (filtro por estado)
        resp = self.client.get(reverse('usuarios_list'), {'estado': 'activo'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('estados', resp.context)
        self.assertIn('total_clientes', resp.context)
        self.assertContains(resp, 'Filtrar por estado:')

        # 2. Productos (filtro por categoría)
        resp = self.client.get(reverse('productos_list'), {'categoria': self.categoria.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('categorias', resp.context)
        self.assertIn('total_productos', resp.context)
        self.assertContains(resp, 'Filtrar por categoría:')

        # 3. Stock / Movimientos (filtro por tipo)
        resp = self.client.get(reverse('stock_list'), {'tipo': 'entrada'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('tipos', resp.context)
        self.assertIn('total_movimientos', resp.context)
        self.assertContains(resp, 'Filtrar por tipo de movimiento:')

        # 4. Categorías (filtro por categoría)
        resp = self.client.get(reverse('categorias_list'), {'categoria': self.categoria.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('todas_categorias', resp.context)
        self.assertIn('total_categorias', resp.context)
        self.assertContains(resp, 'Filtrar por categoría:')

        # 5. Pedidos (filtro por estado)
        resp = self.client.get(reverse('pedidos_list'), {'estado': 'pendiente'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('estados', resp.context)
        self.assertIn('total_pedidos', resp.context)
        self.assertContains(resp, 'Filtrar por estado:')

        # 6. Proveedores (filtro por proveedor)
        resp = self.client.get(reverse('proveedores_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('todos_proveedores', resp.context)
        self.assertIn('total_proveedores', resp.context)
        self.assertContains(resp, 'Filtrar por proveedor:')

        # 7. Diseñadores (filtro por diseñador)
        resp = self.client.get(reverse('disenadores_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('todos_disenadores', resp.context)
        self.assertIn('total_disenadores', resp.context)
        self.assertContains(resp, 'Filtrar por diseñador:')

        # 8. Roles (filtro por estado)
        resp = self.client.get(reverse('roles_list'), {'estado': 'activo'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('estados', resp.context)
        self.assertIn('total_roles', resp.context)
        self.assertContains(resp, 'Filtrar por estado:')

        # 9. Permisos (filtro por rol)
        resp = self.client.get(reverse('permisos_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('roles', resp.context)
        self.assertIn('total_permisos', resp.context)
        self.assertContains(resp, 'Filtrar por rol:')

        # 10. Dashboard Users (filtro por rol)
        resp = self.client.get(reverse('dashboard_users_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('roles', resp.context)
        self.assertIn('total_users', resp.context)
        self.assertContains(resp, 'Filtrar por rol:')


class ValidacionesUnificadasTests(TestCase):
    def test_telefono_unificado_obligatorio_y_formato(self):
        """Verifica que el teléfono tenga las mismas reglas de validación en todos los formularios."""
        # 1. Teléfono con espacios rechazado
        cf = ClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test1@test.com', 'telefono': '300 1234567', 'direccion': 'Calle 1234567890', 'contraseña': 'password123'})
        self.assertFalse(cf.is_valid())
        self.assertIn('El teléfono no puede contener espacios.', cf.errors.get('telefono', []))

        rf = RegistroClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test2@test.com', 'telefono': '300 1234567', 'direccion': 'Calle 1234567890', 'contraseña': 'password123', 'confirmar_contraseña': 'password123'})
        self.assertFalse(rf.is_valid())
        self.assertIn('El teléfono no puede contener espacios.', rf.errors.get('telefono', []))

        pf = PerfilClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test3@test.com', 'telefono': '300 1234567', 'direccion': 'Calle 1234567890'})
        self.assertFalse(pf.is_valid())
        self.assertIn('El teléfono no puede contener espacios.', pf.errors.get('telefono', []))

        ch = CheckoutForm(data={'departamento': 'Antioquia', 'ciudad': 'Medellín', 'direccion_envio': 'Calle 1234567890', 'telefono_contacto': '300 1234567'})
        self.assertFalse(ch.is_valid())
        self.assertIn('El teléfono no puede contener espacios.', ch.errors.get('telefono_contacto', []))

        # 2. Teléfono obligatorio en ClienteForm, RegistroClienteForm y PerfilClienteForm
        cf_empty = ClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test1@test.com', 'telefono': '', 'direccion': 'Calle 1234567890', 'contraseña': 'password123'})
        self.assertFalse(cf_empty.is_valid())
        self.assertIn('El teléfono es obligatorio.', cf_empty.errors.get('telefono', []))

        rf_empty = RegistroClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test2@test.com', 'telefono': '', 'direccion': 'Calle 1234567890', 'contraseña': 'password123', 'confirmar_contraseña': 'password123'})
        self.assertFalse(rf_empty.is_valid())
        self.assertIn('El teléfono es obligatorio.', rf_empty.errors.get('telefono', []))

        pf_empty = PerfilClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test3@test.com', 'telefono': '', 'direccion': 'Calle 1234567890'})
        self.assertFalse(pf_empty.is_valid())
        self.assertIn('El teléfono es obligatorio.', pf_empty.errors.get('telefono', []))

    def test_direccion_unificada_longitud(self):
        """Verifica que la dirección requiera al menos 10 caracteres en todos los formularios."""
        pf_short = PerfilClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test3@test.com', 'telefono': '3001234567', 'direccion': 'Corta'})
        self.assertFalse(pf_short.is_valid())
        self.assertIn('La dirección debe tener al menos 10 caracteres.', pf_short.errors.get('direccion', []))

        rf_short = RegistroClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test2@test.com', 'telefono': '3001234567', 'direccion': 'Corta', 'contraseña': 'password123', 'confirmar_contraseña': 'password123'})
        self.assertFalse(rf_short.is_valid())
        self.assertIn('La dirección debe tener al menos 10 caracteres.', rf_short.errors.get('direccion', []))

        cf_short = ClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test1@test.com', 'telefono': '3001234567', 'direccion': 'Corta', 'contraseña': 'password123'})
        self.assertFalse(cf_short.is_valid())
        self.assertIn('La dirección debe tener al menos 10 caracteres.', cf_short.errors.get('direccion', []))

    def test_nombre_apellido_sin_numeros_en_perfil(self):
        """PerfilClienteForm no debe admitir números en nombre ni apellido."""
        pf_num = PerfilClienteForm(data={'nombre': 'Juan123', 'apellido': 'Perez456', 'correo': 'test3@test.com', 'telefono': '3001234567', 'direccion': 'Calle 1234567890'})
        self.assertFalse(pf_num.is_valid())
        self.assertIn('El nombre no puede contener números.', pf_num.errors.get('nombre', []))
        self.assertIn('El apellido no puede contener números.', pf_num.errors.get('apellido', []))

    def test_passwords_sin_espacios_en_todos_los_formularios(self):
        """Las contraseñas no deben admitir espacios en ninguno de los formularios."""
        cf = ClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test1@test.com', 'telefono': '3001234567', 'direccion': 'Calle 1234567890', 'contraseña': 'pass word'})
        self.assertFalse(cf.is_valid())
        self.assertIn('La contraseña no puede contener espacios.', cf.errors.get('contraseña', []))

        rf = RegistroClienteForm(data={'nombre': 'Test', 'apellido': 'User', 'correo': 'test2@test.com', 'telefono': '3001234567', 'direccion': 'Calle 1234567890', 'contraseña': 'pass word', 'confirmar_contraseña': 'pass word'})
        self.assertFalse(rf.is_valid())
        self.assertIn('La contraseña no puede contener espacios.', rf.errors.get('contraseña', []))

        cpf = CambiarPasswordClienteForm(data={'password_actual': 'oldpass', 'nuevo_password': 'pass word', 'confirmar_nuevo_password': 'pass word'})
        self.assertFalse(cpf.is_valid())
        self.assertIn('La nueva contraseña no puede contener espacios.', cpf.errors.get('nuevo_password', []))

        conf = ConfirmarPasswordClienteForm(data={'password1': 'pass word', 'password2': 'pass word'})
        self.assertFalse(conf.is_valid())
        self.assertIn('La contraseña no puede contener espacios.', conf.errors.get('password1', []))

        udf = UsuarioDashboardForm(data={'username': 'testadmin', 'password1': 'pass word', 'password2': 'pass word'})
        self.assertFalse(udf.is_valid())
        self.assertIn('La contraseña no puede contener espacios.', udf.errors.get('password1', []))

    def test_proveedor_nombre_unico(self):
        """ProveedorForm debe rechazar nombres duplicados sin importar mayúsculas."""
        Proveedor.objects.create(nombre='Textiles SAS', telefono='3001112233')
        form = ProveedorForm(data={'nombre': 'textiles sas', 'telefono': '3004445566'})
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un proveedor con ese nombre.', form.errors.get('nombre', []))

    def test_editar_personalizacion_en_proceso(self):
        """Permite editar una personalización propia en estado en_proceso y verifica botón en mis personalizaciones."""
        cliente = Cliente.objects.create(
            nombre='Carlos',
            apellido='Gómez',
            correo='carlos_pers1@example.com',
            telefono='3001234567',
            direccion='Calle 123 #45-67',
            contraseña='hashed_pass_123',
            estado='activo'
        )
        session = self.client.session
        session['cliente_id'] = cliente.pk
        session.save()

        prod = Producto.objects.create(
            nombre='Hoodie Test Base',
            precio=Decimal('150000.00'),
            stock=10,
            estado='activo'
        )
        pers = Personalizacion.objects.create(
            cliente=cliente,
            producto=prod,
            nombre_personalizacion='Custom Inicial V1',
            tipo='Hoodie Oversize',
            talla='L (Oversize)',
            color='Negro Obsidiana',
            estampado='Acid Butterfly',
            tipografia='Brutalism Bold Sans',
            detalle='Detalle inicial de prueba de personalización',
            estado='en_proceso'
        )

        # GET a la página de edición
        resp_get = self.client.get(reverse('tienda_personalizacion_editar', args=[pers.pk]))
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, 'Editar Personalización')
        self.assertContains(resp_get, 'Custom Inicial V1')

        # POST actualizando campos
        post_data = {
            'producto': prod.pk,
            'nombre_personalizacion': 'Custom Modificado V2',
            'tipo': 'T-Shirt Heavyweight',
            'talla': 'XL (Oversize)',
            'color': 'Gris Carbón',
            'estampado': 'Gothic Cross Haze',
            'tipografia': 'Modern Cyber Tech',
            'detalle': 'Detalle actualizado de la prenda modificada',
            'accion': 'guardar'
        }
        resp_post = self.client.post(reverse('tienda_personalizacion_editar', args=[pers.pk]), data=post_data)
        self.assertRedirects(resp_post, reverse('tienda_mis_personalizaciones'))

        pers.refresh_from_db()
        self.assertEqual(pers.nombre_personalizacion, 'Custom Modificado V2')
        self.assertEqual(pers.tipo, 'T-Shirt Heavyweight')
        self.assertEqual(pers.color, 'Gris Carbón')
        self.assertEqual(pers.estampado, 'Gothic Cross Haze')
        self.assertEqual(pers.tipografia, 'Modern Cyber Tech')
        self.assertEqual(pers.estado, 'en_proceso')

        # Verificar que en mis personalizaciones aparezca 'Editar Prenda'
        resp_list = self.client.get(reverse('tienda_mis_personalizaciones'))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, 'Editar Prenda')
        self.assertContains(resp_list, reverse('tienda_personalizacion_editar', args=[pers.pk]))

    def test_bloqueo_edicion_personalizacion_publicada(self):
        """No permite editar una personalización que ya fue publicada."""
        cliente = Cliente.objects.create(
            nombre='Ana',
            apellido='Martínez',
            correo='ana_pers2@example.com',
            telefono='3109876543',
            direccion='Carrera 78 #12-34',
            contraseña='hashed_pass_456',
            estado='activo'
        )
        session = self.client.session
        session['cliente_id'] = cliente.pk
        session.save()

        prod = Producto.objects.create(
            nombre='Hoodie Test Base 2',
            precio=Decimal('150000.00'),
            stock=10,
            estado='activo'
        )
        pers_pub = Personalizacion.objects.create(
            cliente=cliente,
            producto=prod,
            nombre_personalizacion='Custom Publicado',
            tipo='Hoodie Oversize',
            talla='L (Oversize)',
            color='Negro Obsidiana',
            estampado='Acid Butterfly',
            tipografia='Brutalism Bold Sans',
            detalle='Detalle inicial de prueba',
            estado='publicada'
        )

        resp = self.client.get(reverse('tienda_personalizacion_editar', args=[pers_pub.pk]))
        self.assertRedirects(resp, reverse('tienda_mis_personalizaciones'))



