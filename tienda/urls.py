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
    path('favoritos/comunidad/toggle-api/<int:prenda_id>/', views.favoritos_comunidad_toggle_api, name='tienda_favoritos_comunidad_toggle_api'),

    # Carrito de Compras
    path('carrito/', views.carrito, name='tienda_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_carrito, name='tienda_agregar_carrito'),
    path('carrito/actualizar/', views.actualizar_carrito, name='tienda_actualizar_carrito'),
    path('carrito/eliminar/<str:item_key>/', views.eliminar_carrito, name='tienda_eliminar_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='tienda_vaciar_carrito'),

    # Proceso de Compra (Checkout) y Pedidos
    path('checkout/', views.checkout, name='tienda_checkout'),
    path('pedidos/<int:pedido_id>/confirmar-pago/', views.confirmar_pago, name='tienda_confirmar_pago'),
    path('pedidos/<int:pedido_id>/paypal/crear-orden/', views.paypal_crear_orden, name='tienda_paypal_crear_orden'),
    path('pedidos/<int:pedido_id>/paypal/capturar-orden/', views.paypal_capturar_orden, name='tienda_paypal_capturar_orden'),
    path('pedidos/<int:pedido_id>/paypal/retorno/', views.paypal_retorno, name='tienda_paypal_retorno'),
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

    # Personalización de Prendas
    path('personalizar/', views.personalizar_producto, name='tienda_personalizar'),
    path('personalizar/<int:pk>/editar/', views.personalizacion_editar, name='tienda_personalizacion_editar'),
    path('mis-personalizaciones/', views.mis_personalizaciones, name='tienda_mis_personalizaciones'),
    path('personalizar/<int:pk>/eliminar/', views.personalizacion_eliminar, name='tienda_personalizacion_eliminar'),

    # Comunidad de Prendas Personalizadas
    path('comunidad/', views.comunidad_lista, name='tienda_comunidad_lista'),
    path('comunidad/publicar/', views.comunidad_publicar, name='tienda_comunidad_publicar'),
    path('comunidad/<int:pk>/', views.comunidad_detalle, name='tienda_comunidad_detalle'),
    path('comunidad/<int:pk>/editar/', views.comunidad_editar, name='tienda_comunidad_editar'),
    path('comunidad/<int:pk>/eliminar/', views.comunidad_eliminar, name='tienda_comunidad_eliminar'),
    path('comunidad/<int:pk>/reaccionar/', views.comunidad_reaccionar_api, name='tienda_comunidad_reaccionar_api'),
    path('comunidad/<int:pk>/comentar/', views.comunidad_comentar, name='tienda_comunidad_comentar'),
    path('comunidad/comentario/<int:comentario_id>/editar/', views.comunidad_comentario_editar, name='tienda_comunidad_comentario_editar'),
    path('comunidad/comentario/<int:comentario_id>/eliminar/', views.comunidad_comentario_eliminar, name='tienda_comunidad_comentario_eliminar'),
]