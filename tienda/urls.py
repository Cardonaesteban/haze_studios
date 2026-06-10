from django.urls import path
from . import views

urlpatterns = [
    #Login cliente
    path('login/', views.login_cliente, name='tienda_login'),
    path('logout/', views.logout_cliente, name='tienda_logout'),

    #Inicio tienda
    path('inicio/', views.inicio, name='tienda_inicio'),
    path('', views.inicio, name='tienda_inicio'),

    #Productos tienda (en desarrollo)
    # path('productos/', views.productos, name='tienda_productos'),
    # path('productos/<int:pk>/', views.producto_detalle, name='tienda_producto_detalle'),
    # path('categorias/', views.categorias, name='tienda_categorias'),
    # path('ventas/', views.ventas, name='tienda_ventas'),
    # path('buscar_productos/', views.buscar_productos, name='tienda_buscar_productos'),
    # path('filtrar_productos/', views.filtrar_productos, name='tienda_filtrar_productos'),
    # path('ordenar_productos/', views.ordenar_productos, name='tienda_ordenar_productos'),
    # path('añadir_al_carrito/<int:producto_id>/', views.añadir_al_carrito, name='tienda_añadir_al_carrito'),
    # path('eliminar_del_carrito/<int:producto_id>/', views.eliminar_del_carrito, name='tienda_eliminar_del_carrito'),
    # path('cerrar_sesion_productos/', views.cerrar_sesion_productos, name='tienda_cerrar_sesion_productos'),

    #Carrito tienda (en desarrollo)
    # path('carrito/', views.carrito, name='tienda_carrito'),
    
    # path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='tienda_agregar_carrito'),
    # path('carrito/remover/<int:producto_id>/', views.remover_del_carrito, name='tienda_remover_carrito'),
    # path('carrito/vaciar/', views.vaciar_carrito, name='tienda_vaciar_carrito'),
    # path('carrito/compras/<int:pedido_id>/comprar_producto_carrito/<int:producto_id>/', views.comprar_producto_carrito, name='tienda_comprar_producto_carrito'),    
    # path('carrito/ir_a_detalle_pedido/', views.ir_a_detalle_pedido, name='tienda_ir_a_detalle_pedido'),
    # path('carrito/compras/<int:pedido_id>/', views.detalle_compra, name='tienda_detalle_compra'),
    # path('carrito/compras/<int:pedido_id>/repetir/', views.repetir_compra, name='tienda_repetir_compra'),
    # path('carrito/compras/<int:pedido_id>/cancelar/', views.cancelar_compra, name='tienda_cancelar_compra'),
    # path('carrito/compras/<int:pedido_id>/cantidad/<int:cantidad>/', views.actualizar_cantidad_carrito, name='tienda_actualizar_cantidad_carrito'),
    # path('carrito/compras/<int:pedido_id>/calcular_total/', views.calcular_total_carrito, name='tienda_calcular_total_carrito'),
    # path('cerrar_sesion_carrito/', views.cerrar_sesion_carrito, name='tienda_cerrar_sesion_carrito'),

    #Categorias tienda (en desarrollo)
    # path('categorias/', views.categorias, name='tienda_categorias'),
    # path('categorias/<int:categoria_id>/', views.categoria_detalle, name='tienda_categoria_detalle'),
    # path('categorias/<int:categoria_id>/productos/', views.categoria_productos, name='tienda_categoria_productos'),
    # path('categorias/<int:categoria_id>/productos/<int:producto_id>/', views.categoria_producto_detalle, name='tienda_categoria_producto_detalle'),
    # path('categorias/<int:categoria_id>/productos/<int:producto_id>/agregar/', views.categoria_agregar_producto, name='tienda_categoria_agregar_producto'),
    # path('categorias/<int:categoria_id>/productos/<int:producto_id>/remover/', views.categoria_remover_producto, name='tienda_categoria_remover_producto'),
    # path('categorias/<int:categoria_id>/productos/<int:producto_id>/editar/', views.categoria_editar_producto, name='tienda_categoria_editar_producto'),
    # path('cerrar_sesion_categorias/', views.cerrar_sesion_categorias, name='tienda_cerrar_sesion_categorias'),

    #Detalle compra (en desarrollo)
    # path('detalle_compra/<int:pedido_id>/', views.detalle_compra, name='tienda_detalle_compra'),
    # path('detalle_compra/<int:pedido_id>/repetir/', views.repetir_compra, name='tienda_repetir_compra'),
    # path('detalle_compra/<int:pedido_id>/cancelar/', views.cancelar_compra, name='tienda_cancelar_compra'),
    # path('confirmar_compra/<int:pedido_id>/', views.confirmar_compra, name='tienda_confirmar_compra'),
    # path('compras_realizadas/', views.compras_realizadas, name='tienda_compras_realizadas'),
    # path('total_compra/', views.total_compra, name='tienda_total_compra'),
    # path('cantidad_productos_compra/<int:pedido_id>/', views.cantidad_productos_compra, name='tienda_cantidad_productos_compra'),
    # path('aplicar_cupon_descuento_compra/<int:pedido_id>/<str:codigo>/', views.aplicar_cupon_descuento_compra, name='tienda_aplicar_cupon_descuento_compra'),
    # path('cerrar_sesion_detalle_compra/', views.cerrar_sesion_detalle_compra, name='tienda_cerrar_sesion_detalle_compra'),

    #Compras realizadas (en desarrollo)
    # path('compras_realizadas/', views.compras_realizadas, name='tienda_compras_realizadas'),
    # path('total_compras_realizadas/', views.total_compras_realizadas, name='tienda_total_compras_realizadas'),
    # path('detalle_compras_realizadas/<int:pedido_id>/', views.detalle_compras_realizadas, name='tienda_detalle_compras_realizadas'),
    # path('repetir_compras_realizadas/<int:pedido_id>/', views.repetir_compras_realizadas, name='tienda_repetir_compras_realizadas'),
    # path('eliminar_compras_realizadas/<int:pedido_id>/', views.eliminar_compras_realizadas, name='tienda_eliminar_compras_realizadas'),
    # path('categorias_compras_realizadas/<int:pedido_id>/', views.categorias_compras_realizadas, name='tienda_categorias_compras_realizadas'),
    # path('cerrar_sesion_compras_realizadas/', views.cerrar_sesion_compras_realizadas, name='tienda_cerrar_sesion_compras_realizadas'),

    #Ropa hombre (en desarrollo)
    # path('ropa_hombre/', views.ropa_hombre, name='tienda_ropa_hombre'),
    # path('ropa_hombre/<int:producto_id>/', views.ropa_hombre_detalle, name='tienda_ropa_hombre_detalle'),
    # path('ropa_hombre/<int:producto_id>/agregar_al_carrito/', views.ropa_hombre_agregar_al_carrito, name='tienda_ropa_hombre_agregar_al_carrito'),
    # path('ropa_hombre/<int:producto_id>/ver_categorias/', views.ropa_hombre_ver_categorias, name='tienda_ropa_hombre_ver_categorias'),
    # path('ropa_hombre/<int:producto_id>/ver_detalle/', views.ropa_hombre_ver_detalle, name='tienda_ropa_hombre_ver_detalle'),
    # path('ropa_hombre/<int:producto_id>/comprar/', views.ropa_hombre_comprar, name='tienda_ropa_hombre_comprar'),
    # path('ropa_hombre/<int:producto_id>/precio/', views.ropa_hombre_precio, name='tienda_ropa_hombre_precio'),
    # path('ropa_hombre/<int:producto_id>/estado/', views.ropa_hombre_estado, name='tienda_ropa_hombre_estado'),
    # path('ropa_hombre/<int:producto_id>/filtrar_ropa_hombre/', views.ropa_hombre_filtrar, name='tienda_ropa_hombre_filtrar'),
    # path('ropa_hombre/<int:producto_id>/ordenar_ropa_hombre/', views.ropa_hombre_ordenar, name='tienda_ropa_hombre_ordenar'),
    # path('ropa_hombre/<int:producto_id>/buscar_ropa_hombre/', views.ropa_hombre_buscar, name='tienda_ropa_hombre_buscar'),
    # path('ropa_hombre/<int:producto_id>/tallas_ropa_hombre/', views.ropa_hombre_tallas, name='tienda_ropa_hombre_tallas'),
    # path('ropa_hombre/<int:producto_id>/colores_ropa_hombre/', views.ropa_hombre_colores, name='tienda_ropa_hombre_colores'),
    # path('ropa_hombre/<int:producto_id>/materiales_ropa_hombre/', views.ropa_hombre_materiales, name='tienda_ropa_hombre_materiales'),
]
