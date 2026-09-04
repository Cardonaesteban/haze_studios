from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from dashboard.models import (
    Cliente, Producto, Categoria, Pedido, DetallePedido,
    Rol, PerfilUsuario, Mensaje
)
from dashboard.forms import MensajeForm
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
            estado='leido',
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
        self.assertContains(response, 'Leído')
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

