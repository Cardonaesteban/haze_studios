from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import Cliente, DetallePedido, Pedido, Producto
from tienda.models import Personalizacion, PrendaComunidad


class TiendaTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre='Ana',
            apellido='Lopez',
            correo='ana@example.com',
            telefono='3001234567',
            direccion='Calle 10 #20-30',
            contraseña=make_password('ClaveSegura123'),
            estado='activo',
        )
        self.producto = Producto.objects.create(
            nombre='Hoodie Haze',
            descripcion='Buzo oversize algodón',
            precio=120000,
            stock=3,
            stock_minimo=1,
            estado='activo',
        )

    def _login_cliente(self):
        session = self.client.session
        session['cliente_id'] = self.cliente.pk
        session['cliente_nombre'] = self.cliente.nombre
        session['cliente_correo'] = self.cliente.correo
        session.save()

    def test_carrito_limita_stock_y_exige_post(self):
        url_agregar = reverse('tienda_agregar_carrito', args=[self.producto.pk])
        self.assertEqual(self.client.get(url_agregar).status_code, 405)

        self.client.post(url_agregar, {'cantidad': 5, 'talla': 'L (Oversize)'})
        carrito = self.client.session['carrito']
        total = sum(item['cantidad'] for item in carrito.values())
        self.assertEqual(total, 3)

        url_vaciar = reverse('tienda_vaciar_carrito')
        self.assertEqual(self.client.get(url_vaciar).status_code, 405)
        self.client.post(url_vaciar)
        self.assertEqual(self.client.session['carrito'], {})

    def test_checkout_bloquea_producto_inactivo(self):
        self._login_cliente()
        self.client.post(
            reverse('tienda_agregar_carrito', args=[self.producto.pk]),
            {'cantidad': 1, 'talla': 'L (Oversize)'},
        )
        self.producto.estado = 'inactivo'
        self.producto.save()

        resp = self.client.post(reverse('tienda_checkout'), {
            'departamento': 'Antioquia',
            'ciudad': 'Medellin',
            'direccion_envio': 'Carrera 50 # 40-10',
            'telefono_contacto': '3001234567',
            'notas': '',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_cancelar_pedido_por_post_restaura_stock(self):
        self._login_cliente()
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha_pedido=timezone.now().date(),
            estado='pendiente',
            total=120000,
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=120000,
        )
        self.producto.stock = 1
        self.producto.save()

        url_cancelar = reverse('tienda_pedido_cancelar', args=[pedido.pk])
        self.assertEqual(self.client.get(url_cancelar).status_code, 405)

        self.client.post(url_cancelar)
        pedido.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(pedido.estado, 'cancelado')
        self.assertEqual(self.producto.stock, 3)

    def test_no_permite_eliminar_personalizacion_publicada_y_sincroniza_estado(self):
        self._login_cliente()
        pers = Personalizacion.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            nombre_personalizacion='Mi Hoodie',
            detalle='Estampado trasero',
            estado='publicada',
        )
        prenda = PrendaComunidad.objects.create(
            autor=self.cliente,
            personalizacion=pers,
            nombre='Mi Hoodie',
            descripcion='Estampado trasero',
            color='Negro Obsidiana',
            talla='L (Oversize)',
            estampado='Acid Butterfly',
            tipografia='Brutalism Bold Sans',
            estado='activo',
        )

        self.client.post(reverse('tienda_personalizacion_eliminar', args=[pers.pk]))
        self.assertTrue(Personalizacion.objects.filter(pk=pers.pk).exists())

        self.client.post(reverse('tienda_comunidad_editar', args=[prenda.pk]), {
            'nombre': 'Mi Hoodie Editado',
            'descripcion': 'Nuevo detalle',
            'color': 'Negro Obsidiana',
            'talla': 'L (Oversize)',
            'estampado': 'Acid Butterfly',
            'tipografia': 'Brutalism Bold Sans',
            'estado': 'inactivo',
            'motivo_inactivacion': 'Pausado por el autor',
        })
        pers.refresh_from_db()
        self.assertEqual(pers.estado, 'en_proceso')
