from typing import Callable, Any
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import (
    Cliente, Producto, Categoria, Proveedor, Disenador,
    Pedido, DetallePedido, Inventario, MovimientoStock,
    Rol, Permiso, PerfilUsuario
)   
from .forms import (    
    ClienteForm, ProductoForm, CategoriaForm,
    ProveedorForm, DisenadorForm, PedidoForm, DetallePedidoFormSet,
    MovimientoStockForm,
    RolForm, PermisoForm, AsignarRolForm, UsuarioDashboardForm
)


# ──────────────────────────────────────────────
# HELPERS DE PERMISOS
# ──────────────────────────────────────────────

def es_admin(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    try:
        return user.perfil.es_admin()
    except PerfilUsuario.DoesNotExist:
        return False


def admin_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
    decorated = user_passes_test(
        es_admin,
        login_url='dashboard',
        redirect_field_name=None # type: ignore
    )(view_func)
    return login_required(decorated)

# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

@login_required
def dashboard(request):
    context = {
        'total_clientes':    Cliente.objects.count(),
        'total_productos':   Producto.objects.count(),
        'total_categorias':  Categoria.objects.count(),
        'total_pedidos':     Pedido.objects.count(),
        'total_proveedores': Proveedor.objects.count(),
        'total_disenadores': Disenador.objects.count(),
        'total_roles':       Rol.objects.count(),
        'total_permisos':    Permiso.objects.count(),
        'ultimos_movimientos': MovimientoStock.objects.select_related('producto', 'usuario').order_by('-fecha')[:5],
        'productos_bajo_stock': Producto.objects.filter(estado='activo').extra(where=['stock <= stock_minimo'])[:5],
        'pedidos_pendientes': Pedido.objects.filter(estado='pendiente').count(),
    }
    return render(request, 'dashboard/index.html', context)


# ──────────────────────────────────────────────
# USUARIOS / CLIENTES
# ──────────────────────────────────────────────

@login_required
def usuarios_list(request):
    clientes = Cliente.objects.prefetch_related('pedidos').all()
    return render(request, 'dashboard/usuarios/list.html', {'clientes': clientes})

@login_required
def usuarios_crear(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario registrado exitosamente.')
        return redirect('usuarios_list')
    return render(request, 'dashboard/usuarios/form.html', {'form': form, 'titulo': 'Registrar usuario'})

@login_required
def usuarios_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('usuarios_list')
    return render(request, 'dashboard/usuarios/form.html', {'form': form, 'titulo': 'Editar usuario', 'objeto': cliente})

@login_required
def usuarios_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('usuarios_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': cliente, 'tipo': 'usuario'})

@login_required
def usuarios_toggle_estado(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.toggle_estado()
    messages.success(request, f'Estado de {cliente} cambiado a {cliente.estado}.')
    return redirect('usuarios_list')


# ──────────────────────────────────────────────
# PRODUCTOS
# ──────────────────────────────────────────────

@login_required
def productos_list(request):
    productos = Producto.objects.select_related('categoria', 'proveedor', 'disenador').all()
    return render(request, 'dashboard/productos/list.html', {'productos': productos})

@login_required
def productos_crear(request):
    form = ProductoForm(request.POST or None)
    if form.is_valid():
        producto = form.save()
        if producto.stock > 0:
            MovimientoStock.objects.create(
                producto=producto, tipo='entrada',
                cantidad=producto.stock, stock_anterior=0,
                stock_posterior=producto.stock,
                motivo='Stock inicial', usuario=request.user
            )
        messages.success(request, 'Producto registrado exitosamente.')
        return redirect('productos_list')
    return render(request, 'dashboard/productos/form.html', {'form': form, 'titulo': 'Registrar producto'})

@login_required
def productos_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    stock_anterior = producto.stock
    form = ProductoForm(request.POST or None, instance=producto)
    if form.is_valid():
        producto = form.save()
        nuevo_stock = producto.stock
        if nuevo_stock != stock_anterior:
            diferencia = nuevo_stock - stock_anterior
            MovimientoStock.objects.create(
                producto=producto, tipo='ajuste',
                cantidad=abs(diferencia),
                stock_anterior=stock_anterior,
                stock_posterior=nuevo_stock,
                motivo='Ajuste manual desde formulario de producto',
                usuario=request.user
            )
        messages.success(request, 'Producto actualizado.')
        return redirect('productos_list')
    return render(request, 'dashboard/productos/form.html', {'form': form, 'titulo': 'Editar producto', 'objeto': producto})

@login_required
def productos_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('productos_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': producto, 'tipo': 'producto'})

@login_required
def productos_toggle_estado(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.toggle_estado()
    messages.success(request, f'Estado de {producto} cambiado a {producto.estado}.')
    return redirect('productos_list')


# ──────────────────────────────────────────────
# MOVIMIENTOS DE STOCK  (Stock reemplaza a Inventario)
# ──────────────────────────────────────────────

@login_required
def stock_list(request):
    movimientos = MovimientoStock.objects.select_related('producto', 'usuario', 'pedido').all()
    productos = Producto.objects.filter(estado='activo').order_by('nombre')
    return render(request, 'dashboard/stock/list.html', {
        'movimientos': movimientos,
        'productos': productos,
    })

@login_required
def stock_entrada(request):
    form = MovimientoStockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            mov = form.save(commit=False)
            mov.tipo = 'entrada'
            producto = mov.producto
            mov.stock_anterior = producto.stock
            producto.stock += mov.cantidad
            producto.save(update_fields=['stock'])
            mov.stock_posterior = producto.stock
            mov.usuario = request.user
            mov.fecha = timezone.now()
            mov.save()
        messages.success(request, f'Entrada de {mov.cantidad} unidades registrada para "{mov.producto.nombre}".')
        return redirect('stock_list')
    return render(request, 'dashboard/stock/form.html', {
        'form': form, 'titulo': 'Registrar Entrada de Stock', 'tipo': 'entrada'
    })

@login_required
def stock_salida(request):
    form = MovimientoStockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            mov = form.save(commit=False)
            mov.tipo = 'salida'
            producto = mov.producto
            if mov.cantidad > producto.stock:
                messages.error(request, f'Stock insuficiente. Disponible: {producto.stock}')
                return render(request, 'dashboard/stock/form.html', {
                    'form': form, 'titulo': 'Registrar Salida de Stock', 'tipo': 'salida'
                })
            mov.stock_anterior = producto.stock
            producto.stock -= mov.cantidad
            producto.save(update_fields=['stock'])
            mov.stock_posterior = producto.stock
            mov.usuario = request.user
            mov.fecha = timezone.now()
            mov.save()
        messages.success(request, f'Salida de {mov.cantidad} unidades registrada para "{mov.producto.nombre}".')
        return redirect('stock_list')
    return render(request, 'dashboard/stock/form.html', {
        'form': form, 'titulo': 'Registrar Salida de Stock', 'tipo': 'salida'
    })

@login_required
def stock_ajuste(request):
    form = MovimientoStockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            mov = form.save(commit=False)
            mov.tipo = 'ajuste'
            producto = mov.producto
            mov.stock_anterior = producto.stock
            producto.stock = mov.cantidad
            producto.save(update_fields=['stock'])
            mov.stock_posterior = producto.stock
            mov.usuario = request.user
            mov.fecha = timezone.now()
            mov.save()
        messages.success(request, f'Stock ajustado a {mov.cantidad} unidades para "{mov.producto.nombre}".')
        return redirect('stock_list')
    return render(request, 'dashboard/stock/form.html', {
        'form': form, 'titulo': 'Ajuste de Stock', 'tipo': 'ajuste',
        'help_text': 'El stock del producto se establecerá exactamente al valor ingresado.'
    })


# ──────────────────────────────────────────────
# CATEGORÍAS
# ──────────────────────────────────────────────

@login_required
def categorias_list(request):
    categorias = Categoria.objects.all()
    return render(request, 'dashboard/categorias/list.html', {'categorias': categorias})

@login_required
def categorias_crear(request):
    form = CategoriaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría registrada.')
        return redirect('categorias_list')
    return render(request, 'dashboard/categorias/form.html', {'form': form, 'titulo': 'Registrar categoría'})

@login_required
def categorias_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría actualizada.')
        return redirect('categorias_list')
    return render(request, 'dashboard/categorias/form.html', {'form': form, 'titulo': 'Editar categoría', 'objeto': categoria})

@login_required
def categorias_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada.')
        return redirect('categorias_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': categoria, 'tipo': 'categoría'})


# ──────────────────────────────────────────────
# PEDIDOS
# ──────────────────────────────────────────────

@login_required
def pedidos_list(request):
    pedidos = Pedido.objects.select_related('cliente').prefetch_related('detalles__producto').all()
    return render(request, 'dashboard/pedidos/list.html', {'pedidos': pedidos})

@login_required
def pedidos_crear(request):
    form = PedidoForm(request.POST or None)
    formset = DetallePedidoFormSet(request.POST or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            pedido = form.save()
            detalles = formset.save(commit=False)
            for detalle in detalles:
                detalle.pedido = pedido
                producto = detalle.producto
                if detalle.cantidad > producto.stock:
                    messages.error(request, f'Stock insuficiente para "{producto.nombre}". Disponible: {producto.stock}')
                    return render(request, 'dashboard/pedidos/form.html', {
                        'form': form, 'formset': formset, 'titulo': 'Registrar pedido'
                    })
                stock_antes = producto.stock
                producto.stock -= detalle.cantidad
                producto.save(update_fields=['stock'])
                MovimientoStock.objects.create(
                    producto=producto, tipo='salida',
                    cantidad=detalle.cantidad,
                    stock_anterior=stock_antes,
                    stock_posterior=producto.stock,
                    motivo=f'Pedido #{pedido.pk}',
                    usuario=request.user, pedido=pedido
                )
                detalle.save()
            for detalle in formset.deleted_objects:
                detalle.delete()
            pedido.calcular_total()
        messages.success(request, 'Pedido registrado exitosamente.')
        return redirect('pedidos_list')
    return render(request, 'dashboard/pedidos/form.html', {
        'form': form, 'formset': formset, 'titulo': 'Registrar pedido'
    })

@login_required
def pedidos_editar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    form = PedidoForm(request.POST or None, instance=pedido)
    formset = DetallePedidoFormSet(request.POST or None, instance=pedido)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            pedido = form.save()
            formset.save()
            pedido.calcular_total()
        messages.success(request, 'Pedido actualizado.')
        return redirect('pedidos_list')
    return render(request, 'dashboard/pedidos/form.html', {
        'form': form, 'formset': formset, 'titulo': 'Editar pedido', 'objeto': pedido
    })

@login_required
def pedidos_eliminar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido eliminado.')
        return redirect('pedidos_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': pedido, 'tipo': 'pedido'})

@login_required
def pedidos_toggle_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    pedido.toggle_estado()
    messages.success(request, f'Estado del pedido #{pedido.pk} cambiado a {pedido.estado}.')
    return redirect('pedidos_list')

@login_required
def pedidos_detalle(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    detalles = pedido.detalles.select_related('producto').all()
    return render(request, 'dashboard/pedidos/detalle.html', {
        'pedido': pedido, 'detalles': detalles
    })


# ──────────────────────────────────────────────
# PROVEEDORES
# ──────────────────────────────────────────────

@login_required
def proveedores_list(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'dashboard/proveedores/list.html', {'proveedores': proveedores})

@login_required
def proveedores_crear(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proveedor registrado.')
        return redirect('proveedores_list')
    return render(request, 'dashboard/proveedores/form.html', {'form': form, 'titulo': 'Registrar proveedor'})

@login_required
def proveedores_editar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proveedor actualizado.')
        return redirect('proveedores_list')
    return render(request, 'dashboard/proveedores/form.html', {'form': form, 'titulo': 'Editar proveedor', 'objeto': proveedor})

@login_required
def proveedores_eliminar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado.')
        return redirect('proveedores_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': proveedor, 'tipo': 'proveedor'})


# ──────────────────────────────────────────────
# DISEÑADORES
# ──────────────────────────────────────────────

@login_required
def disenadores_list(request):
    disenadores = Disenador.objects.all()
    return render(request, 'dashboard/disenadores/list.html', {'disenadores': disenadores})

@login_required
def disenadores_crear(request):
    form = DisenadorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Diseñador registrado.')
        return redirect('disenadores_list')
    return render(request, 'dashboard/disenadores/form.html', {'form': form, 'titulo': 'Registrar diseñador'})

@login_required
def disenadores_editar(request, pk):
    disenador = get_object_or_404(Disenador, pk=pk)
    form = DisenadorForm(request.POST or None, instance=disenador)
    if form.is_valid():
        form.save()
        messages.success(request, 'Diseñador actualizado.')
        return redirect('disenadores_list')
    return render(request, 'dashboard/disenadores/form.html', {'form': form, 'titulo': 'Editar diseñador', 'objeto': disenador})

@login_required
def disenadores_eliminar(request, pk):
    disenador = get_object_or_404(Disenador, pk=pk)
    if request.method == 'POST':
        disenador.delete()
        messages.success(request, 'Diseñador eliminado.')
        return redirect('disenadores_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': disenador, 'tipo': 'diseñador'})


# ──────────────────────────────────────────────
# ROLES
# ──────────────────────────────────────────────

@login_required
def roles_list(request):
    roles = Rol.objects.prefetch_related('permisos', 'usuarios').all()
    return render(request, 'dashboard/roles/list.html', {'roles': roles})

@login_required
def roles_crear(request):
    form = RolForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Rol creado.')
        return redirect('roles_list')
    return render(request, 'dashboard/roles/form.html', {'form': form, 'titulo': 'Crear rol'})

@login_required
def roles_editar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    form = RolForm(request.POST or None, instance=rol)
    if form.is_valid():
        form.save()
        messages.success(request, 'Rol actualizado.')
        return redirect('roles_list')
    return render(request, 'dashboard/roles/form.html', {'form': form, 'titulo': 'Editar rol', 'objeto': rol})

@login_required
def roles_eliminar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.delete()
        messages.success(request, 'Rol eliminado.')
        return redirect('roles_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': rol, 'tipo': 'rol'})

def roles_toggle_estado(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    rol.activo = not rol.activo
    rol.save()
    return redirect('roles_list')

# ──────────────────────────────────────────────
# PERMISOS
# ──────────────────────────────────────────────

@login_required
def permisos_list(request):
    permisos = Permiso.objects.prefetch_related('roles').all()
    return render(request, 'dashboard/permisos/list.html', {'permisos': permisos})

@login_required
def permisos_crear(request):
    form = PermisoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Permiso creado.')
        return redirect('permisos_list')
    return render(request, 'dashboard/permisos/form.html', {'form': form, 'titulo': 'Crear permiso'})

@login_required
def permisos_editar(request, pk):
    permiso = get_object_or_404(Permiso, pk=pk)
    form = PermisoForm(request.POST or None, instance=permiso)
    if form.is_valid():
        form.save()
        messages.success(request, 'Permiso actualizado.')
        return redirect('permisos_list')
    return render(request, 'dashboard/permisos/form.html', {'form': form, 'titulo': 'Editar permiso', 'objeto': permiso})

@login_required
def permisos_eliminar(request, pk):
    permiso = get_object_or_404(Permiso, pk=pk)
    if request.method == 'POST':
        permiso.delete()
        messages.success(request, 'Permiso eliminado.')
        return redirect('permisos_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': permiso, 'tipo': 'permiso'})


# ──────────────────────────────────────────────
# USUARIOS DASHBOARD (Django User)
# ──────────────────────────────────────────────

@login_required
def dashboard_users_list(request):
    users = User.objects.prefetch_related('perfil__rol').all()
    return render(request, 'dashboard/dashboard_users/list.html', {'users': users})

@login_required
def dashboard_users_crear(request):
    form = UsuarioDashboardForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario del dashboard creado.')
        return redirect('dashboard_users_list')
    return render(request, 'dashboard/dashboard_users/form.html', {'form': form, 'titulo': 'Crear usuario dashboard'})

@login_required
def dashboard_users_editar(request, pk):
    user = get_object_or_404(User, pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
    form = UsuarioDashboardForm(request.POST or None, instance=user, initial={'rol': perfil.rol})
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('dashboard_users_list')
    return render(request, 'dashboard/dashboard_users/form.html', {
        'form': form, 'titulo': 'Editar usuario dashboard', 'objeto': user
    })

@login_required
def dashboard_users_eliminar(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'No puedes eliminar tu propio usuario.')
        return redirect('dashboard_users_list')
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('dashboard_users_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': user, 'tipo': 'usuario dashboard'})

@login_required
def dashboard_users_asignar_rol(request, pk):
    user = get_object_or_404(User, pk=pk)
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
    form = AsignarRolForm(request.POST or None, instance=perfil)
    if form.is_valid():
        form.save()
        messages.success(request, f'Rol asignado a {user.username}.')
        return redirect('dashboard_users_list')
    return render(request, 'dashboard/dashboard_users/asignar_rol.html', {
        'form': form, 'titulo': f'Asignar rol a {user.username}', 'objeto': user
    })


# ──────────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA (Admin)
# ──────────────────────────────────────────────

from .models import TokenRecuperacion
from .forms import SolicitarRecuperacionForm, CambiarContrasenaForm


def recuperar_password(request):
    """Paso 1: El admin ingresa su username y se genera un link de recuperación."""
    if request.method == 'POST':
        form = SolicitarRecuperacionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = User.objects.get(username=username, is_staff=True)
            # Invalida tokens anteriores
            TokenRecuperacion.objects.filter(usuario=user, usado=False).update(usado=True)
            # Crea nuevo token
            token_obj = TokenRecuperacion.objects.create(usuario=user)
            # Construye el link
            reset_url = request.build_absolute_uri(
                f'/recuperar-password/confirmar/{token_obj.token}/'
            )
            return render(request, 'registration/recuperar_password_link.html', {
                'user': user,
                'reset_url': reset_url,
                'token': token_obj,
            })
    else:
        form = SolicitarRecuperacionForm()
    return render(request, 'registration/recuperar_password.html', {'form': form})


def recuperar_password_confirmar(request, token):
    """Paso 2: El admin usa el link y establece su nueva contraseña."""
    try:
        token_obj = TokenRecuperacion.objects.select_related('usuario').get(token=token)
    except TokenRecuperacion.DoesNotExist:
        messages.error(request, 'El enlace de recuperación no es válido.')
        return redirect('recuperar_password')

    if not token_obj.es_valido():
        messages.error(request, 'El enlace ha expirado o ya fue utilizado. Solicita uno nuevo.')
        return redirect('recuperar_password')

    if request.method == 'POST':
        form = CambiarContrasenaForm(request.POST)
        if form.is_valid():
            user = token_obj.usuario
            user.set_password(form.cleaned_data['password1'])
            user.save()
            token_obj.usado = True
            token_obj.save()
            messages.success(request, '¡Contraseña actualizada correctamente! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = CambiarContrasenaForm()

    return render(request, 'registration/recuperar_password_confirmar.html', {
        'form': form,
        'token_obj': token_obj,
    })
