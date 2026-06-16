from django.urls import path
from . import views

urlpatterns = [
    #Login cliente
    path('login/', views.login_cliente, name='tienda_login'),
    path('logout/', views.logout_cliente, name='tienda_logout'),
    
    #Inicio tienda
    path('inicio/', views.inicio, name='tienda_inicio'),
    path('', views.inicio, name='tienda_inicio'),  # Redirige la raíz de la tienda al inicio

#     #Productos tienda (vistas hechas) 
#     path('productos/', views.productos, name='tienda_productos'),
#     path('productos/<int:pk>/', views.producto_detalle, name='tienda_producto_detalle'),

#     #Acciones productos tienda
#     path('reportar_producto/<int:pk>/', views.reportar_producto, name='tienda_reportar_producto'),
#     path('compartir_producto/<int:pk>/', views.compartir_producto, name='tienda_compartir_producto'),
#     path('favoritos_producto/<int:pk>/', views.favoritos_producto, name='tienda_favoritos_producto'),
#     path('lista_deseados_producto/<int:pk>/', views.lista_deseados_producto, name='tienda_lista_deseados_producto'),
#     path('comparar_producto/<int:pk>/', views.comparar_producto, name='tienda_comparar_producto'),

#     #Ver producto en la seccion comunidad
#     path('comunidad_producto/<int:pk>/', views.comunidad_producto, name='tienda_comunidad_producto'), 

    
#     #Filtrar ordenar y buscar productos tienda
#     path('buscar_productos/', views.buscar_productos, name='tienda_buscar_productos'),
#     path('filtrar_productos/', views.filtrar_productos, name='tienda_filtrar_productos'),
#     path('ordenar_productos/', views.ordenar_productos, name='tienda_ordenar_productos'),

#     #Ventas tienda
#     path('ventas/', views.ventas, name='tienda_ventas'),
       
#     #Carrito tienda
#     path('carrito/', views.carrito, name='tienda_carrito'),
#     path('cupon/<str:codigo>/', views.cupon, name='cupon'),
    
#     #CRUD carrito tienda
#     path('agregar_carrito/<int:producto_id>/', views.añadir_carrito, name='agregar_carrito'),
#     path('eliminar_carrito/<int:producto_id>/', views.eliminar_carrito, name='eliminar_carrito'),
#     path('vaciar_carrito/', views.vaciar_carrito, name='vaciar_carrito'),

#     #Compras tienda
#     path('checkout/', views.checkout, name='tienda_checkout'),
#     path('confirmar_compra/', views.confirmar_compra, name='tienda_confirmar_compra'),

#     path('compras/', views.compras_realizadas, name='tienda_compras_realizadas'),
#     path('compras/<int:pedido_id>/', views.detalle_compra, name='tienda_detalle_compra'),

#     path('cancelar_compra/<int:pedido_id>/', views.cancelar_compra, name='tienda_cancelar_compra'),
#     path('repetir_compra/<int:pedido_id>/', views.repetir_compra, name='tienda_repetir_compra'),

#     #Categorias tienda
#     path('categorias/', views.categorias, name='tienda_categorias'),
#     path('categorias/<int:categoria_id>/', views.categoria_detalle, name='tienda_categoria_detalle'),

#     #Ropa hombre tienda
#     path('ropa_hombre/', views.ropa_hombre, name='tienda_ropa_hombre'),
#     path('camisas_hombre/', views.camisas_hombre, name='tienda_camisas_hombre'),

#     #Ropa mujer
#     path('ropa_mujer/', views.ropa_mujer, name='tienda_ropa_mujer'),
#     path('camisas_mujer/', views.camisas_mujer, name='tienda_camisas_mujer'),


#     #Personalizacion tienda
#     path('personalizacion/', views.personalizacion, name='tienda_personalizacion'),
#     path('personalizacion/<int:producto_id>/', views.personalizacion_producto, name='tienda_personalizacion_producto'),

#     #Ver personalizacion en la seccion comunidad
#     path('comunidad_personalizacion/<int:producto_id>/', views.comunidad_personalizacion, name='tienda_comunidad_personalizacion'),

#     #Comunidad tienda
#     path('comunidad/', views.comunidad, name='tienda_comunidad'),
#     path('productos_publicados_usuario/', views.productos_publicados_usuario, name='productos_publicados'),
#     path('comunidad/<int:comunidad_id>/subir_producto/', views.comunidad_subir_producto, name='tienda_comunidad_subir_producto'),

#     #Acciones comunidad
#     path('comunidad/buscar/', views.comunidad_buscar, name='comunidad_buscar'),
#     path('comunidad/filtrar/', views.comunidad_filtrar, name='comunidad_filtrar'),
#     path('comunidad/ordenar/', views.comunidad_ordenar, name='comunidad_ordenar'),
#     path('comunidad/<int:perfil_id>/perfil_usuario/', views.comunidad_perfil_usuario, name='tienda_comunidad_perfil_usuario'),

#     #FAQ tienda
#     path('faq/', views.faq, name='tienda_faq'),


 

 ]

