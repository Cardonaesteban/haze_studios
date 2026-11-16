from django.contrib import admin
from .models import (
    Permiso,
    Rol,
    PerfilUsuario,
    Categoria,
    Proveedor,
    Disenador,
    Producto,
    MovimientoStock,
    Cliente,
    Pedido,
    DetallePedido,
    Inventario,
    TokenRecuperacion,
    Mensaje,
)


# ──────────────────────────────────────────────
# ROLES Y PERMISOS
# ──────────────────────────────────────────────

@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre')


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre',)
    filter_horizontal = ('permisos',)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol')
    list_filter = ('rol',)
    search_fields = ('user__username', 'user__email')


# ──────────────────────────────────────────────
# CATÁLOGO
# ──────────────────────────────────────────────

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre', 'correo')


@admin.register(Disenador)
class DisenadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'estado')
    list_filter = ('estado', 'categoria', 'proveedor', 'disenador')
    search_fields = ('nombre', 'descripcion')


# ──────────────────────────────────────────────
# MOVIMIENTOS DE STOCK E INVENTARIO
# ──────────────────────────────────────────────

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo', 'cantidad', 'stock_anterior', 'stock_posterior', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'motivo')
    readonly_fields = (
        'producto', 'tipo', 'cantidad', 'stock_anterior',
        'stock_posterior', 'motivo', 'fecha', 'usuario', 'pedido',
    )

    # Historial de auditoría: solo lectura para evitar alterar movimientos registrados
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'stock', 'fecha_actualizacion')
    list_filter = ('fecha_actualizacion',)
    search_fields = ('producto__nombre',)


# ──────────────────────────────────────────────
# CLIENTES Y PEDIDOS
# ──────────────────────────────────────────────

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'correo', 'telefono', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'correo')
    readonly_fields = ('fecha_registro',)
    exclude = ('contraseña',)


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha_pedido', 'estado', 'metodo_pago', 'total', 'fecha_pago')
    list_filter = ('estado', 'metodo_pago', 'fecha_pedido')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'cliente__correo', 'referencia_pago', 'transaccion_id')
    readonly_fields = ('fecha_creacion',)
    inlines = [DetallePedidoInline]


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario')
    search_fields = ('producto__nombre', 'pedido__id')


# ──────────────────────────────────────────────
# TOKENS Y MENSAJES
# ──────────────────────────────────────────────

@admin.register(TokenRecuperacion)
class TokenRecuperacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'token', 'creado', 'usado')
    list_filter = ('usado', 'creado')
    search_fields = ('usuario__username', 'token')
    readonly_fields = ('token', 'creado')


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'destinatario', 'tipo', 'estado', 'remitente', 'fecha_envio')
    list_filter = ('tipo', 'estado', 'fecha_envio')
    search_fields = ('destinatario__nombre', 'destinatario__correo', 'contenido')
    readonly_fields = ('fecha_envio',)
