from django.urls import path
from . import views

urlpatterns = [
    # Portada y Catálogo Oversize
    path('', views.inicio, name='tienda_inicio'),
    path('productos/', views.productos, name='tienda_productos'),
    path('productos/<int:pk>/', views.producto_detalle, name='tienda_producto_detalle'),

    # Favoritos
    path('favoritos/', views.mis_favoritos, name='tienda_favoritos'),
    path('favoritos/toggle-api/<int:producto_id>/', views.favoritos_toggle_api, name='tienda_favoritos_toggle_api'),

    # Carrito de Compras
    path('carrito/', views.carrito, name='tienda_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_carrito, name='tienda_agregar_carrito'),
    path('carrito/actualizar/', views.actualizar_carrito, name='tienda_actualizar_carrito'),
    path('carrito/eliminar/<str:item_key>/', views.eliminar_carrito, name='tienda_eliminar_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='tienda_vaciar_carrito'),

    # Proceso de Compra (Checkout) y Pedidos
    path('checkout/', views.checkout, name='tienda_checkout'),
    path('pedidos/<int:pedido_id>/confirmar-pago/', views.confirmar_pago, name='tienda_confirmar_pago'),
    path('pedidos/confirmado/<int:pedido_id>/', views.pedido_confirmado, name='tienda_pedido_confirmado'),
    path('pedidos/mis-pedidos/', views.mis_pedidos, name='tienda_mis_pedidos'),
    path('pedidos/<int:pedido_id>/', views.pedido_detalle, name='tienda_pedido_detalle'),
    path('pedidos/<int:pedido_id>/cancelar/', views.pedido_cancelar, name='tienda_pedido_cancelar'),

    # Autenticación y Registro de Clientes
    path('login/', views.login_cliente, name='tienda_login'),
    path('registro/', views.registro_cliente, name='tienda_registro'),
    path('logout/', views.logout_cliente, name='tienda_logout'),

    # Perfil de Usuario y Contraseña
    path('perfil/', views.perfil_cliente, name='tienda_perfil'),
    path('perfil/cambiar-password/', views.cambiar_password_cliente, name='tienda_cambiar_password'),
    path('recuperar-password/', views.recuperar_password_cliente, name='tienda_recuperar_password'),
    path('recuperar-password/enviado/', views.recuperar_password_enviado, name='tienda_recuperar_password_enviado'),
    path('recuperar-password/confirmar/<uuid:token>/', views.recuperar_password_confirmar_cliente, name='tienda_recuperar_password_confirmar'),
]