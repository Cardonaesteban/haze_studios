from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Usuarios / Clientes
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/crear/', views.usuarios_crear, name='usuarios_crear'),
    path('usuarios/<int:pk>/editar/', views.usuarios_editar, name='usuarios_editar'),
    path('usuarios/<int:pk>/eliminar/', views.usuarios_eliminar, name='usuarios_eliminar'),
    path('usuarios/<int:pk>/estado/', views.usuarios_toggle_estado, name='usuarios_estado'),

    # Productos
    path('productos/', views.productos_list, name='productos_list'),
    path('productos/crear/', views.productos_crear, name='productos_crear'),
    path('productos/<int:pk>/editar/', views.productos_editar, name='productos_editar'),
    path('productos/<int:pk>/eliminar/', views.productos_eliminar, name='productos_eliminar'),
    path('productos/<int:pk>/estado/', views.productos_toggle_estado, name='productos_estado'),

    # Movimientos de Stock
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/entrada/', views.stock_entrada, name='stock_entrada'),
    path('stock/salida/', views.stock_salida, name='stock_salida'),
    path('stock/ajuste/', views.stock_ajuste, name='stock_ajuste'),

    # Categorías
    path('categorias/', views.categorias_list, name='categorias_list'),
    path('categorias/crear/', views.categorias_crear, name='categorias_crear'),
    path('categorias/<int:pk>/editar/', views.categorias_editar, name='categorias_editar'),
    path('categorias/<int:pk>/eliminar/', views.categorias_eliminar, name='categorias_eliminar'),

    # Pedidos
    path('pedidos/', views.pedidos_list, name='pedidos_list'),
    path('pedidos/crear/', views.pedidos_crear, name='pedidos_crear'),
    path('pedidos/<int:pk>/editar/', views.pedidos_editar, name='pedidos_editar'),
    path('pedidos/<int:pk>/eliminar/', views.pedidos_eliminar, name='pedidos_eliminar'),
    path('pedidos/<int:pk>/estado/', views.pedidos_toggle_estado, name='pedidos_estado'),
    path('pedidos/<int:pk>/detalle/', views.pedidos_detalle, name='pedidos_detalle'),

    # Proveedores
    path('proveedores/', views.proveedores_list, name='proveedores_list'),
    path('proveedores/crear/', views.proveedores_crear, name='proveedores_crear'),
    path('proveedores/<int:pk>/editar/', views.proveedores_editar, name='proveedores_editar'),
    path('proveedores/<int:pk>/eliminar/', views.proveedores_eliminar, name='proveedores_eliminar'),

    # Diseñadores
    path('disenadores/', views.disenadores_list, name='disenadores_list'),
    path('disenadores/crear/', views.disenadores_crear, name='disenadores_crear'),
    path('disenadores/<int:pk>/editar/', views.disenadores_editar, name='disenadores_editar'),
    path('disenadores/<int:pk>/eliminar/', views.disenadores_eliminar, name='disenadores_eliminar'),

    # Roles (solo admin)
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/crear/', views.roles_crear, name='roles_crear'),
    path('roles/<int:pk>/editar/', views.roles_editar, name='roles_editar'),
    # path('roles/<int:pk>/estado/', views.roles_toggle_estado, name='roles_estado'),  # En desarrollo
    path('roles/<int:pk>/eliminar/', views.roles_eliminar, name='roles_eliminar'),

    # Permisos (solo admin)
    path('permisos/', views.permisos_list, name='permisos_list'),
    path('permisos/crear/', views.permisos_crear, name='permisos_crear'),
    path('permisos/<int:pk>/editar/', views.permisos_editar, name='permisos_editar'),
    path('permisos/<int:pk>/eliminar/', views.permisos_eliminar, name='permisos_eliminar'),

    # Usuarios Dashboard (solo admin)
    path('dashboard-users/', views.dashboard_users_list, name='dashboard_users_list'),
    path('dashboard-users/crear/', views.dashboard_users_crear, name='dashboard_users_crear'),
    path('dashboard-users/<int:pk>/editar/', views.dashboard_users_editar, name='dashboard_users_editar'),
    path('dashboard-users/<int:pk>/eliminar/', views.dashboard_users_eliminar, name='dashboard_users_eliminar'),
    path('dashboard-users/<int:pk>/rol/', views.dashboard_users_asignar_rol, name='dashboard_users_rol'),
]
