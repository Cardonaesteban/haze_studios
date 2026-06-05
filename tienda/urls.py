from django.urls import path
from . import views

urlpatterns = [
    #Login cliente
    path('login/', views.login_cliente, name='tienda_login'),
    path('logout/', views.logout_cliente, name='tienda_logout'),
    path('inicio/', views.inicio, name='tienda_inicio'),

    #Inicio tienda
    path('inicio/', views.inicio, name='tienda_inicio'),
    path('', views.inicio, name='tienda_inicio'),  # Redirige la raíz de la tienda al inicio


    #Productos tienda
    path('productos/', views.productos, name='tienda_productos'),
    
    path('productos/<int:pk>/', views.producto_detalle, name='tienda_producto_detalle'),

    path('categorias/', views.categorias, name='tienda_categorias'),

    path('ventas/', views.ventas, name='tienda_ventas'),

    
    path('buscar_productos/', views.buscar_productos, name='tienda_buscar_productos'),
    path('filtrar_productos/', views.filtrar_productos, name='tienda_filtrar_productos'),
    path('ordenar_productos/', views.ordenar_productos, name='tienda_ordenar_productos'),

    path('añadir_al_carrito/<int:producto_id>/', views.añadir_al_carrito, name='tienda_añadir_al_carrito'),
    path('eliminar_del_carrito/<int:producto_id>/', views.eliminar_del_carrito, name='tienda_eliminar_del_carrito'),

    path('cerrar_sesion_productos/', views.cerrar_sesion_productos, name='tienda_cerrar_sesion_productos'),
    


    #Carrito tienda
    path('carrito/', views.carrito, name='tienda_carrito'),
    
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='tienda_agregar_carrito'),
    path('carrito/remover/<int:producto_id>/', views.remover_del_carrito, name='tienda_remover_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='tienda_vaciar_carrito'),

    path('carrito/compras/<int:pedido_id>/comprar_producto_carrito/<int:producto_id>/', views.comprar_producto_carrito, name='tienda_comprar_producto_carrito'),
    path('carrito/ir_a_detalle_pedido/', views.ir_a_detalle_pedido, name='tienda_ir_a_detalle_pedido'),
    path('carrito/compras/<int:pedido_id>/', views.detalle_compra, name='tienda_detalle_compra'),
    path('carrito/compras/<int:pedido_id>/repetir/', views.repetir_compra, name='tienda_repetir_compra'),
    path('carrito/compras/<int:pedido_id>/cancelar/', views.cancelar_compra, name='tienda_cancelar_compra'),

    path('carrito/compras/<int:pedido_id>/cantidad/<int:cantidad>/', views.actualizar_cantidad_carrito, name='tienda_actualizar_cantidad_carrito'),
    path('carrito/compras/<int:pedido_id>/calcular_total/', views.calcular_total_carrito, name='tienda_calcular_total_carrito'),
    
    path('cerrar_sesion_carrito/', views.cerrar_sesion_carrito, name='tienda_cerrar_sesion_carrito'),



    #Categorias tienda
    path('categorias/', views.categorias, name='tienda_categorias'),
    path('categorias/<int:categoria_id>/', views.categoria_detalle, name='tienda_categoria_detalle'),
    path('categorias/<int:categoria_id>/productos/', views.categoria_productos, name='tienda_categoria_productos'),
    path('categorias/<int:categoria_id>/productos/<int:producto_id>/', views.categoria_producto_detalle, name='tienda_categoria_producto_detalle'),
    path('categorias/<int:categoria_id>/productos/<int:producto_id>/agregar/', views.categoria_agregar_producto, name='tienda_categoria_agregar_producto'),
    path('categorias/<int:categoria_id>/productos/<int:producto_id>/remover/', views.categoria_remover_producto, name='tienda_categoria_remover_producto'),
    path('categorias/<int:categoria_id>/productos/<int:producto_id>/editar/', views.categoria_editar_producto, name='tienda_categoria_editar_producto'),
    path('cerrar_sesion_categorias/', views.cerrar_sesion_categorias, name='tienda_cerrar_sesion_categorias'),


    #Detalle compra
    path('detalle_compra/<int:pedido_id>/', views.detalle_compra, name='tienda_detalle_compra'),
    path('detalle_compra/<int:pedido_id>/repetir/', views.repetir_compra, name='tienda_repetir_compra'),
    path('detalle_compra/<int:pedido_id>/cancelar/', views.cancelar_compra, name='tienda_cancelar_compra'),
    path('confirmar_compra/<int:pedido_id>/', views.confirmar_compra, name='tienda_confirmar_compra'),
    path('compras_realizadas/', views.compras_realizadas, name='tienda_compras_realizadas'),
    path('total_compra/', views.total_compra, name='tienda_total_compra'),
    path('cantidad_productos_compra/<int:pedido_id>/', views.cantidad_productos_compra, name='tienda_cantidad_productos_compra'),
    path('aplicar_cupon_descuento_compra/<int:pedido_id>/<str:codigo>/', views.aplicar_cupon_descuento_compra, name='tienda_aplicar_cupon_descuento_compra'),
    path('cerrar_sesion_detalle_compra/', views.cerrar_sesion_detalle_compra, name='tienda_cerrar_sesion_detalle_compra'),

    
    #Compras realizadas
    path('compras_realizadas/', views.compras_realizadas, name='tienda_compras_realizadas'),
    path('total_compras_realizadas/', views.total_compras_realizadas, name='tienda_total_compras_realizadas'),
    path('detalle_compras_realizadas/<int:pedido_id>/', views.detalle_compras_realizadas, name='tienda_detalle_compras_realizadas'),
    path('repetir_compras_realizadas/<int:pedido_id>/', views.repetir_compras_realizadas, name='tienda_repetir_compras_realizadas'),
    path('eliminar_compras_realizadas/<int:pedido_id>/', views.eliminar_compras_realizadas, name='tienda_eliminar_compras_realizadas'),
    path('categorias_compras_realizadas/<int:pedido_id>/', views.categorias_compras_realizadas, name='tienda_categorias_compras_realizadas'),
    path('cerrar_sesion_compras_realizadas/', views.cerrar_sesion_compras_realizadas, name='tienda_cerrar_sesion_compras_realizadas'),

    #Ropa hombre
    path('ropa_hombre/', views.ropa_hombre, name='tienda_ropa_hombre'),
    path('ropa_hombre/<int:producto_id>/', views.ropa_hombre_detalle, name='tienda_ropa_hombre_detalle'),
    path('ropa_hombre/<int:producto_id>/agregar_al_carrito/', views.ropa_hombre_agregar_al_carrito, name='tienda_ropa_hombre_agregar_al_carrito'),
    path('ropa_hombre/<int:producto_id>/ver_categorias/', views.ropa_hombre_ver_categorias, name='tienda_ropa_hombre_ver_categorias'),
    path('ropa_hombre/<int:producto_id>/ver_detalle/', views.ropa_hombre_ver_detalle, name='tienda_ropa_hombre_ver_detalle'),
    path('ropa_hombre/<int:producto_id>/comprar/', views.ropa_hombre_comprar, name='tienda_ropa_hombre_comprar'),
    path('ropa_hombre/<int:producto_id>/precio/', views.ropa_hombre_precio, name='tienda_ropa_hombre_precio'),
    path('ropa_hombre/<int:producto_id>/estado/', views.ropa_hombre_estado, name='tienda_ropa_hombre_estado'),
    path('ropa_hombre/<int:producto_id>/filtrar_ropa_hombre/', views.ropa_hombre_filtrar, name='tienda_ropa_hombre_filtrar'),
    path('ropa_hombre/<int:producto_id>/ordenar_ropa_hombre/', views.ropa_hombre_ordenar, name='tienda_ropa_hombre_ordenar'),
    path('ropa_hombre/<int:producto_id>/buscar_ropa_hombre/', views.ropa_hombre_buscar, name='tienda_ropa_hombre_buscar'),
    path('ropa_hombre/<int:producto_id>/tallas_ropa_hombre/', views.ropa_hombre_tallas, name='tienda_ropa_hombre_tallas'),
    path('ropa_hombre/<int:producto_id>/colores_ropa_hombre/', views.ropa_hombre_colores, name='tienda_ropa_hombre_colores'),
    path('ropa_hombre/<int:producto_id>/materiales_ropa_hombre/', views.ropa_hombre_materiales, name='tienda_ropa_hombre_materiales'),
    path('ropa_hombre/<int:producto_id>/opiniones_ropa_hombre/', views.ropa_hombre_opiniones, name='tienda_ropa_hombre_opiniones'),
    path('ropa_hombre/<int:producto_id>/preguntas_ropa_hombre/', views.ropa_hombre_preguntas, name='tienda_ropa_hombre_preguntas'),
    path('ropa_hombre/<int:producto_id>/responder_preguntas_ropa_hombre/', views.ropa_hombre_responder_preguntas, name='tienda_ropa_hombre_responder_preguntas'),
    path('ropa_hombre/<int:producto_id>/reportar_producto_ropa_hombre/', views.ropa_hombre_reportar_producto, name='tienda_ropa_hombre_reportar_producto'),
    path('ropa_hombre/<int:producto_id>/compartir_producto_ropa_hombre/', views.ropa_hombre_compartir_producto, name='tienda_ropa_hombre_compartir_producto'),
    path('ropa_hombre/<int:producto_id>/favoritos_producto_ropa_hombre/', views.ropa_hombre_favoritos_producto, name='tienda_ropa_hombre_favoritos_producto'),
    path('ropa_hombre/<int:producto_id>/lista_deseados_producto_ropa_hombre/', views.ropa_hombre_lista_deseados_producto, name='tienda_ropa_hombre_lista_deseados_producto'),
    path('ropa_hombre/<int:producto_id>/comunidad_producto_ropa_hombre/', views.ropa_hombre_comunidad_producto, name='tienda_ropa_hombre_comunidad_producto'),
    path('ropa_hombre/<int:producto_id>/comparar_producto_ropa_hombre/', views.ropa_hombre_comparar_producto, name='tienda_ropa_hombre_comparar_producto'),
    path('ropa_hombre/<int:producto_id>/personalizacion_producto_ropa_hombre/', views.ropa_hombre_personalizacion_producto, name='tienda_ropa_hombre_personalizacion_producto'),
    path('cerrar_sesion_ropa_hombre/', views.cerrar_sesion_ropa_hombre, name='tienda_cerrar_sesion_ropa_hombre'),


    #Camisas hombre
    path('camisas_hombre/', views.camisas_hombre, name='tienda_camisas_hombre'),
    path('camisas_hombre_detalle/<int:producto_id>/', views.camisas_hombre_detalle, name='tienda_camisas_hombre_detalle'),
    path('camisas_hombre/<int:producto_id>/agregar_al_carrito/', views.camisas_hombre_agregar_al_carrito, name='tienda_camisas_hombre_agregar_al_carrito'),
    path('camisas_hombre/<int:producto_id>/ver_categorias/', views.camisas_hombre_ver_categorias, name='tienda_camisas_hombre_ver_categorias'),
    path('camisas_hombre/<int:producto_id>/ver_detalle/', views.camisas_hombre_ver_detalle, name='tienda_camisas_hombre_ver_detalle'),
    path('camisas_hombre/<int:producto_id>/comprar/', views.camisas_hombre_comprar, name='tienda_camisas_hombre_comprar'),
    path('camisas_hombre/<int:producto_id>/precio/', views.camisas_hombre_precio, name='tienda_camisas_hombre_precio'),
    path('camisas_hombre/<int:producto_id>/estado/', views.camisas_hombre_estado, name='tienda_camisas_hombre_estado'),
    path('camisas_hombre/<int:producto_id>/filtrar_camisas_hombre/', views.camisas_hombre_filtrar, name='tienda_camisas_hombre_filtrar'),
    path('camisas_hombre/<int:producto_id>/ordenar_camisas_hombre/', views.camisas_hombre_ordenar, name='tienda_camisas_hombre_ordenar'),
    path('camisas_hombre/<int:producto_id>/buscar_camisas_hombre/', views.camisas_hombre_buscar, name='tienda_camisas_hombre_buscar'),
    path('camisas_hombre/<int:producto_id>/tallas_camisas_hombre/', views.camisas_hombre_tallas, name='tienda_camisas_hombre_tallas'),
    path('camisas_hombre/<int:producto_id>/colores_camisas_hombre/', views.camisas_hombre_colores, name='tienda_camisas_hombre_colores'),
    path('camisas_hombre/<int:producto_id>/materiales_camisas_hombre/', views.camisas_hombre_materiales, name='tienda_camisas_hombre_materiales'),
    path('camisas_hombre/<int:producto_id>/opiniones_camisas_hombre/', views.camisas_hombre_opiniones, name='tienda_camisas_hombre_opiniones'),
    path('camisas_hombre/<int:producto_id>/preguntas_camisas_hombre/', views.camisas_hombre_preguntas, name='tienda_camisas_hombre_preguntas'),
    path('camisas_hombre/<int:producto_id>/responder_preguntas_camisas_hombre/', views.camisas_hombre_responder_preguntas, name='tienda_camisas_hombre_responder_preguntas'),
    path('camisas_hombre/<int:producto_id>/reportar_producto_camisas_hombre/', views.camisas_hombre_reportar_producto, name='tienda_camisas_hombre_reportar_producto'),
    path('camisas_hombre/<int:producto_id>/compartir_producto_camisas_hombre/', views.camisas_hombre_compartir_producto, name='tienda_camisas_hombre_compartir_producto'),
    path('camisas_hombre/<int:producto_id>/favoritos_producto_camisas_hombre/', views.camisas_hombre_favoritos_producto, name='tienda_camisas_hombre_favoritos_producto'),
    path('camisas_hombre/<int:producto_id>/lista_deseados_producto_camisas_hombre/', views.camisas_hombre_lista_deseados_producto, name='tienda_camisas_hombre_lista_deseados_producto'),
    path('camisas_hombre/<int:producto_id>/comunidad_producto_camisas_hombre/', views.camisas_hombre_comunidad_producto, name='tienda_camisas_hombre_comunidad_producto'),
    path('camisas_hombre/<int:producto_id>/comparar_producto_camisas_hombre/', views.camisas_hombre_comparar_producto, name='tienda_camisas_hombre_comparar_producto'),
    path('camisas_hombre/<int:producto_id>/personalizacion_producto_camisas_hombre/', views.camisas_hombre_personalizacion_producto, name='tienda_camisas_hombre_personalizacion_producto'),
    path('cerrar_sesion_camisas_hombre/', views.cerrar_sesion_camisas_hombre, name='tienda_cerrar_sesion_camisas_hombre'),



    #Ropa mujer
    path('ropa_mujer/', views.ropa_mujer, name='tienda_ropa_mujer'),
    path('ropa_mujer/<int:producto_id>/', views.ropa_mujer_detalle, name='tienda_ropa_mujer_detalle'),
    path('ropa_mujer/<int:producto_id>/agregar_al_carrito/', views.ropa_mujer_agregar_al_carrito, name='tienda_ropa_mujer_agregar_al_carrito'),
    path('ropa_mujer/<int:producto_id>/ver_categorias/', views.ropa_mujer_ver_categorias, name='tienda_ropa_mujer_ver_categorias'),
    path('ropa_mujer/<int:producto_id>/ver_detalle/', views.ropa_mujer_ver_detalle, name='tienda_ropa_mujer_ver_detalle'),
    path('ropa_mujer/<int:producto_id>/comprar/', views.ropa_mujer_comprar, name='tienda_ropa_mujer_comprar'),
    path('ropa_mujer/<int:producto_id>/precio/', views.ropa_mujer_precio, name='tienda_ropa_mujer_precio'),
    path('ropa_mujer/<int:producto_id>/estado/', views.ropa_mujer_estado, name='tienda_ropa_mujer_estado'),
    path('ropa_mujer/<int:producto_id>/filtrar_ropa_mujer/', views.ropa_mujer_filtrar, name='tienda_ropa_mujer_filtrar'),
    path('ropa_mujer/<int:producto_id>/ordenar_ropa_mujer/', views.ropa_mujer_ordenar, name='tienda_ropa_mujer_ordenar'),
    path('ropa_mujer/<int:producto_id>/buscar_ropa_mujer/', views.ropa_mujer_buscar, name='tienda_ropa_mujer_buscar'),
    path('ropa_mujer/<int:producto_id>/tallas_ropa_mujer/', views.ropa_mujer_tallas, name='tienda_ropa_mujer_tallas'),
    path('ropa_mujer/<int:producto_id>/colores_ropa_mujer/', views.ropa_mujer_colores, name='tienda_ropa_mujer_colores'),
    path('ropa_mujer/<int:producto_id>/materiales_ropa_mujer/', views.ropa_mujer_materiales, name='tienda_ropa_mujer_materiales'),
    path('ropa_mujer/<int:producto_id>/opiniones_ropa_mujer/', views.ropa_mujer_opiniones, name='tienda_ropa_mujer_opiniones'),
    path('ropa_mujer/<int:producto_id>/preguntas_ropa_mujer/', views.ropa_mujer_preguntas, name='tienda_ropa_mujer_preguntas'),
    path('ropa_mujer/<int:producto_id>/responder_preguntas_ropa_mujer/', views.ropa_mujer_responder_preguntas, name='tienda_ropa_mujer_responder_preguntas'),
    path('ropa_mujer/<int:producto_id>/reportar_producto_ropa_mujer/', views.ropa_mujer_reportar_producto, name='tienda_ropa_mujer_reportar_producto'),
    path('ropa_mujer/<int:producto_id>/compartir_producto_ropa_mujer/', views.ropa_mujer_compartir_producto, name='tienda_ropa_mujer_compartir_producto'),
    path('ropa_mujer/<int:producto_id>/favoritos_producto_ropa_mujer/', views.ropa_mujer_favoritos_producto, name='tienda_ropa_mujer_favoritos_producto'),
    path('ropa_mujer/<int:producto_id>/lista_deseados_producto_ropa_mujer/', views.ropa_mujer_lista_deseados_producto, name='tienda_ropa_mujer_lista_deseados_producto'),
    path('ropa_mujer/<int:producto_id>/comunidad_producto_ropa_mujer/', views.ropa_mujer_comunidad_producto, name='tienda_ropa_mujer_comunidad_producto'),
    path('ropa_mujer/<int:producto_id>/comparar_producto_ropa_mujer/', views.ropa_mujer_comparar_producto, name='tienda_ropa_mujer_comparar_producto'),
    path('ropa_mujer/<int:producto_id>/personalizacion_producto_ropa_mujer/', views.ropa_mujer_personalizacion_producto, name='tienda_ropa_mujer_personalizacion_producto'),
    path('cerrar_sesion_ropa_mujer/', views.cerrar_sesion_ropa_mujer, name='tienda_cerrar_sesion_ropa_mujer'),

    #Camisas mujer
    path('camisas_mujer/', views.camisas_mujer, name='tienda_camisas_mujer'),
    path('camisas_mujer_detalle/<int:producto_id>/', views.camisas_mujer_detalle, name='tienda_camisas_mujer_detalle'),
    path('camisas_mujer/<int:producto_id>/agregar_al_carrito/', views.camisas_mujer_agregar_al_carrito, name='tienda_camisas_mujer_agregar_al_carrito'),
    path('camisas_mujer/<int:producto_id>/ver_categorias/', views.camisas_mujer_ver_categorias, name='tienda_camisas_mujer_ver_categorias'),
    path('camisas_mujer/<int:producto_id>/ver_detalle/', views.camisas_mujer_ver_detalle, name='tienda_camisas_mujer_ver_detalle'),
    path('camisas_mujer/<int:producto_id>/comprar/', views.camisas_mujer_comprar, name='tienda_camisas_mujer_comprar'),
    path('camisas_mujer/<int:producto_id>/precio/', views.camisas_mujer_precio, name='tienda_camisas_mujer_precio'),
    path('camisas_mujer/<int:producto_id>/estado/', views.camisas_mujer_estado, name='tienda_camisas_mujer_estado'),
    path('camisas_mujer/<int:producto_id>/filtrar_camisas_mujer/', views.camisas_mujer_filtrar, name='tienda_camisas_mujer_filtrar'),
    path('camisas_mujer/<int:producto_id>/ordenar_camisas_mujer/', views.camisas_mujer_ordenar, name='tienda_camisas_mujer_ordenar'),
    path('camisas_mujer/<int:producto_id>/buscar_camisas_mujer/', views.camisas_mujer_buscar, name='tienda_camisas_mujer_buscar'),
    path('camisas_mujer/<int:producto_id>/tallas_camisas_mujer/', views.camisas_mujer_tallas, name='tienda_camisas_mujer_tallas'),
    path('camisas_mujer/<int:producto_id>/colores_camisas_mujer/', views.camisas_mujer_colores, name='tienda_camisas_mujer_colores'),
    path('camisas_mujer/<int:producto_id>/materiales_camisas_mujer/', views.camisas_mujer_materiales, name='tienda_camisas_mujer_materiales'),
    path('camisas_mujer/<int:producto_id>/opiniones_camisas_mujer/', views.camisas_mujer_opiniones, name='tienda_camisas_mujer_opiniones'),
    path('camisas_mujer/<int:producto_id>/preguntas_camisas_mujer/', views.camisas_mujer_preguntas, name='tienda_camisas_mujer_preguntas'),
    path('camisas_mujer/<int:producto_id>/responder_preguntas_camisas_mujer/', views.camisas_mujer_responder_preguntas, name='tienda_camisas_mujer_responder_preguntas'),
    path('camisas_mujer/<int:producto_id>/reportar_producto_camisas_mujer/', views.camisas_mujer_reportar_producto, name='tienda_camisas_mujer_reportar_producto'),
    path('camisas_mujer/<int:producto_id>/compartir_producto_camisas_mujer/', views.camisas_mujer_compartir_producto, name='tienda_camisas_mujer_compartir_producto'),
    path('camisas_mujer/<int:producto_id>/favoritos_producto_camisas_mujer/', views.camisas_mujer_favoritos_producto, name='tienda_camisas_mujer_favoritos_producto'),
    path('camisas_mujer/<int:producto_id>/lista_deseados_producto_camisas_mujer/', views.camisas_mujer_lista_deseados_producto, name='tienda_camisas_mujer_lista_deseados_producto'),
    path('camisas_mujer/<int:producto_id>/comunidad_producto_camisas_mujer/', views.camisas_mujer_comunidad_producto, name='tienda_camisas_mujer_comunidad_producto'),
    path('camisas_mujer/<int:producto_id>/comparar_producto_camisas_mujer/', views.camisas_mujer_comparar_producto, name='tienda_camisas_mujer_comparar_producto'),
    path('camisas_mujer/<int:producto_id>/personalizacion_producto_camisas_mujer/', views.camisas_mujer_personalizacion_producto, name='tienda_camisas_mujer_personalizacion_producto'),
    path('cerrar_sesion_camisas_mujer/', views.cerrar_sesion_camisas_mujer, name='tienda_cerrar_sesion_camisas_mujer'),

    #Personalizacion tienda
    path('personalizacion/', views.personalizacion, name='tienda_personalizacion'),
    path('personalizacion/<int:producto_id>/', views.personalizacion_producto, name='tienda_personalizacion_producto'),
    path('personalizacion/<int:producto_id>/agregar_al_carrito/', views.personalizacion_agregar_al_carrito, name='tienda_personalizacion_agregar_al_carrito'),
    path('personalizacion/<int:producto_id>/ver_categorias/', views.personalizacion_ver_categorias, name='tienda_personalizacion_ver_categorias'),
    path('personalizacion/<int:producto_id>/ver_detalle/', views.personalizacion_ver_detalle, name='tienda_personalizacion_ver_detalle'),
    path('personalizacion/<int:producto_id>/comprar/', views.personalizacion_comprar, name='tienda_personalizacion_comprar'),
    path('personalizacion/<int:producto_id>/precio/', views.personalizacion_precio, name='tienda_personalizacion_precio'),
    path('personalizacion/<int:producto_id>/estado/', views.personalizacion_estado, name='tienda_personalizacion_estado'),
    path('personalizacion/<int:producto_id>/filtrar_personalizacion/', views.personalizacion_filtrar, name='tienda_personalizacion_filtrar'),
    path('personalizacion/<int:producto_id>/ordenar_personalizacion/', views.personalizacion_ordenar, name='tienda_personalizacion_ordenar'),
    path('personalizacion/<int:producto_id>/buscar_personalizacion/', views.personalizacion_buscar, name='tienda_personalizacion_buscar'),
    path('personalizacion/<int:producto_id>/tallas_personalizacion/', views.personalizacion_tallas, name='tienda_personalizacion_tallas'),
    path('personalizacion/<int:producto_id>/colores_personalizacion/', views.personalizacion_colores, name='tienda_personalizacion_colores'),
    path('personalizacion/<int:producto_id>/materiales_personalizacion/', views.personalizacion_materiales, name='tienda_personalizacion_materiales'),
    path('personalizacion/<int:producto_id>/estampados_personalizacion/', views.personalizacion_estampados, name='tienda_personalizacion_estampados'),
    path('personalizacion/<int:producto_id>/opiniones_personalizacion/', views.personalizacion_opiniones, name='tienda_personalizacion_opiniones'),
    path('personalizacion/<int:producto_id>/preguntas_personalizacion/', views.personalizacion_preguntas, name='tienda_personalizacion_preguntas'),
    path('personalizacion/<int:producto_id>/responder_preguntas_personalizacion/', views.personalizacion_responder_preguntas, name='tienda_personalizacion_responder_preguntas'),
    path('personalizacion/<int:producto_id>/reportar_producto_personalizacion/', views.personalizacion_reportar_producto, name='tienda_personalizacion_reportar_producto'),
    path('personalizacion/<int:producto_id>/compartir_producto_personalizacion/', views.personalizacion_compartir_producto, name='tienda_personalizacion_compartir_producto'),
    path('personalizacion/<int:producto_id>/favoritos_producto_personalizacion/', views.personalizacion_favoritos_producto, name='tienda_personalizacion_favoritos_producto'),
    path('personalizacion/<int:producto_id>/lista_deseados_producto_personalizacion/', views.personalizacion_lista_deseados_producto, name='tienda_personalizacion_lista_deseados_producto'),
    path('personalizacion/<int:producto_id>/añadir_producto_comunidad_personalizacion/', views.personalizacion_añadir_producto_comunidad, name='tienda_personalizacion_añadir_producto_comunidad'),
    path('personalizacion/<int:producto_id>/eliminar_producto_comunidad_personalizacion/', views.personalizacion_eliminar_producto_comunidad, name='tienda_personalizacion_eliminar_producto_comunidad'),
    path('personalizacion/<int:producto_id>/ver_producto_comunidad_personalizacion/', views.personalizacion_ver_producto_comunidad, name='tienda_personalizacion_ver_producto_comunidad'),
    path('personalizacion/<int:producto_id>/comparar_producto_personalizacion/', views.personalizacion_comparar_producto, name='tienda_personalizacion_comparar_producto'),
    path('personalizacion/<int:producto_id>/buscar_producto_comunidad_personalizacion/', views.personalizacion_buscar_producto_comunidad, name='tienda_personalizacion_buscar_producto_comunidad'),
    path('personalizacion/<int:producto_id>/ir_a_comunidad_personalizacion/<int:comunidad_id>/', views.personalizacion_ir_a_comunidad, name='tienda_personalizacion_ir_a_comunidad_especifica'),
    path('cerrar_sesion_personalizacion_tienda/', views.cerrar_sesion_personalizacion_tienda, name='tienda_cerrar_sesion_personalizacion_tienda'),

    #Comunidad tienda
    path('comunidad/', views.comunidad, name='tienda_comunidad'),
    path('comunidad/<int:comunidad_id>/', views.comunidad_productos_publicados, name='tienda_comunidad_productos_publicados'),
    path('comunidad/<int:comunidad_id>/subir_producto/', views.comunidad_subir_producto, name='tienda_comunidad_agregar_producto'),
    path('comunidad/<int:comunidad_id>/buscar/<int:producto_id>/', views.comunidad_buscar, name='tienda_comunidad_buscar'),
    path('comunidad/<int:comunidad_id>/filtrar_buscar/<int:producto_id>/', views.comunidad_filtrar_buscar, name='tienda_comunidad_filtrar_buscar'),
    path('comunidad/<int:comunidad_id>/filtrar/<int:producto_id>/', views.comunidad_filtrar, name='tienda_comunidad_filtrar'),
    path('comunidad/<int:comunidad_id>/ordenar/<int:producto_id>/', views.comunidad_ordenar, name='tienda_comunidad_ordenar'),

    path('comunidad/<int:comunidad_id>/ver_productos_publicados/<int:producto_id>/', views.comunidad_ver_productos_publicados, name='tienda_comunidad_ver_productos_publicados'),
    path('comunidad/<int:comunidad_id>/perfil_usuario/<int:producto_id>/', views.comunidad_perfil_usuario, name='tienda_comunidad_perfil_usuario'),
    path('comunidad/<int:comunidad_id>/usuario_que_publica/<int:producto_id>/', views.comunidad_usuario_que_publica, name='tienda_comunidad_usuario_que_publica'),


    path('comunidad/<int:comunidad_id>/ordenar/<int:producto_id>/', views.comunidad_ordenar, name='tienda_comunidad_ordenar'),
    path('cerrar_sesion_comunidad_tienda/', views.cerrar_sesion_comunidad_tienda, name='tienda_cerrar_sesion_comunidad_tienda'),

    #Contacto tienda


    path('cerrar_sesion_contacto_tienda/', views.cerrar_sesion_contacto_tienda, name='tienda_cerrar_sesion_contacto_tienda'),

    #Acerca de (tienda)


    path('cerrar_sesion_acerca_de_tienda/', views.cerrar_sesion_acerca_de_tienda, name='tienda_cerrar_sesion_acerca_de_tienda'),

    #FAQ tienda


    path('cerrar_sesion_FAQ_mujer/', views.cerrar_sesion_FAQ_mujer, name='tienda_cerrar_sesion_FAQ_mujer'),

    #Novedades tienda


    path('cerrar_sesion_novedades/', views.cerrar_sesion_novedades, name='tienda_cerrar_sesion_novedades'),


    




    

]

