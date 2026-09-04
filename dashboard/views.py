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
    Rol, Permiso, PerfilUsuario, Mensaje
)   
from .forms import (    
    ClienteForm, ProductoForm, ProductoEditarForm, CategoriaForm,
    ProveedorForm, DisenadorForm, PedidoForm, DetallePedidoFormSet,
    MovimientoStockForm, estructurar_notas_pedido,
    RolForm, PermisoForm, AsignarRolForm, UsuarioDashboardForm,
    MensajeForm
)
from .emails import enviar_notificacion_estado_pedido


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


def admin_required(view_func):
    decorated = user_passes_test(
        es_admin,
        login_url='login',  
        redirect_field_name=None
    )(view_func)
    return login_required(decorated)

# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

@admin_required
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

@admin_required
def usuarios_list(request):
    estado = request.GET.get('estado')
    clientes = Cliente.objects.prefetch_related('pedidos').all()
    if estado:
        clientes = clientes.filter(estado=estado)
    estados = Cliente.ESTADO_CHOICES
    return render(request, 'dashboard/usuarios/list.html', {
        'clientes': clientes,
        'estados': estados,
        'estado_seleccionado': estado,
        'total_clientes': clientes.count(),
    })

@admin_required
def usuarios_crear(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario registrado exitosamente.')
        return redirect('usuarios_list')
    return render(request, 'dashboard/usuarios/form.html', {'form': form, 'titulo': 'Registrar usuario'})

@admin_required
def usuarios_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario actualizado.')
        return redirect('usuarios_list')
    return render(request, 'dashboard/usuarios/form.html', {'form': form, 'titulo': 'Editar usuario', 'objeto': cliente})

@admin_required
def usuarios_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('usuarios_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': cliente, 'tipo': 'usuario'})

@admin_required
def usuarios_toggle_estado(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.toggle_estado()
    messages.success(request, f'Estado de {cliente} cambiado a {cliente.estado}.')
    return redirect('usuarios_list')


# ──────────────────────────────────────────────
# PRODUCTOS
# ──────────────────────────────────────────────

@admin_required
def productos_list(request):
    categoria_id = request.GET.get('categoria')
    productos = Producto.objects.select_related('categoria', 'proveedor', 'disenador').all()
    categoria_seleccionada = None
    if categoria_id and categoria_id.isdigit():
        categoria_seleccionada = int(categoria_id)
        productos = productos.filter(categoria_id=categoria_seleccionada)
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'dashboard/productos/list.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_seleccionada': categoria_seleccionada,
        'total_productos': productos.count(),
    })

@admin_required
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

@admin_required
def productos_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.estado == 'inactivo':
        messages.error(request, f'No se puede editar el producto "{producto.nombre}" porque está inactivo. Actívelo primero.')
        return redirect('productos_list')
    form = ProductoEditarForm(request.POST or None, instance=producto)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('productos_list')
    return render(request, 'dashboard/productos/form.html', {'form': form, 'titulo': 'Editar producto', 'objeto': producto})

@admin_required
def productos_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('productos_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': producto, 'tipo': 'producto'})

@admin_required
def productos_toggle_estado(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.toggle_estado()
    messages.success(request, f'Estado de {producto} cambiado a {producto.estado}.')
    return redirect('productos_list')


# ──────────────────────────────────────────────
# MOVIMIENTOS DE STOCK  (Stock reemplaza a Inventario)
# ──────────────────────────────────────────────

@admin_required
def stock_list(request):
    tipo = request.GET.get('tipo')
    movimientos = MovimientoStock.objects.select_related('producto', 'usuario', 'pedido').all()
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    productos = Producto.objects.filter(estado='activo').order_by('nombre')
    tipos = MovimientoStock.TIPO_CHOICES
    return render(request, 'dashboard/stock/list.html', {
        'movimientos': movimientos,
        'productos': productos,
        'tipos': tipos,
        'tipo_seleccionado': tipo,
        'total_movimientos': movimientos.count(),
    })

@admin_required
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

@admin_required
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

@admin_required
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

@admin_required
def categorias_list(request):
    categoria_id = request.GET.get('categoria')
    categorias = Categoria.objects.all().order_by('nombre')
    todas_categorias = list(categorias)
    categoria_seleccionada = None
    if categoria_id and categoria_id.isdigit():
        categoria_seleccionada = int(categoria_id)
        categorias = categorias.filter(pk=categoria_seleccionada)
    return render(request, 'dashboard/categorias/list.html', {
        'categorias': categorias,
        'todas_categorias': todas_categorias,
        'categoria_seleccionada': categoria_seleccionada,
        'total_categorias': categorias.count(),
    })

@admin_required
def categorias_crear(request):
    form = CategoriaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría registrada.')
        return redirect('categorias_list')
    return render(request, 'dashboard/categorias/form.html', {'form': form, 'titulo': 'Registrar categoría'})

@admin_required
def categorias_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)
    if form.is_valid():
        form.save()
        messages.success(request, 'Categoría actualizada.')
        return redirect('categorias_list')
    return render(request, 'dashboard/categorias/form.html', {'form': form, 'titulo': 'Editar categoría', 'objeto': categoria})

@admin_required
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


@admin_required
def pedidos_list(request):
    estado = request.GET.get('estado')
    pedidos = Pedido.objects.select_related('cliente').prefetch_related('detalles__producto', 'movimientos_stock').all()
    if estado:
        pedidos = pedidos.filter(estado=estado)
    for p in pedidos:
        movs = list(p.movimientos_stock.filter(tipo='salida'))
        movs_libres = list(movs)
        for d in p.detalles.all():
            d.talla = None
            for i, m in enumerate(movs_libres):
                if m.producto_id == d.producto_id and m.cantidad == d.cantidad:
                    import re
                    match = re.search(r'\(Talla:\s*([^)]+)\)', m.motivo)
                    if match:
                        d.talla = match.group(1).strip()
                    movs_libres.pop(i)
                    break
    estados = Pedido.ESTADO_CHOICES
    return render(request, 'dashboard/pedidos/list.html', {
        'pedidos': pedidos,
        'estados': estados,
        'estado_seleccionado': estado,
        'total_pedidos': pedidos.count(),
    })

@admin_required
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

@admin_required
def pedidos_editar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    estado_anterior = pedido.estado
    form = PedidoForm(request.POST or None, instance=pedido)
    formset = DetallePedidoFormSet(request.POST or None, instance=pedido)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            pedido = form.save()
            formset.save()
            pedido.calcular_total()
        if pedido.estado != estado_anterior:
            enviar_notificacion_estado_pedido(pedido, estado_anterior)
            messages.success(request, f'Pedido actualizado. Se envió notificación por correo al cliente ({pedido.cliente.correo}) con el estado {pedido.get_estado_display()}.')
        else:
            messages.success(request, 'Pedido actualizado.')
        return redirect('pedidos_list')
    return render(request, 'dashboard/pedidos/form.html', {
        'form': form, 'formset': formset, 'titulo': 'Editar pedido', 'objeto': pedido
    })

@admin_required
def pedidos_eliminar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido eliminado.')
        return redirect('pedidos_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': pedido, 'tipo': 'pedido'})

@admin_required
def pedidos_toggle_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    nuevo_estado = request.POST.get('nuevo_estado') or request.GET.get('nuevo_estado')
    estado_anterior = pedido.estado
    estados_validos = dict(Pedido.ESTADO_CHOICES)

    if nuevo_estado and nuevo_estado in estados_validos:
        if pedido.estado != nuevo_estado:
            pedido.estado = nuevo_estado
            pedido.save(update_fields=['estado'])
            enviar_notificacion_estado_pedido(pedido, estado_anterior)
            messages.success(request, f'Estado del pedido #{pedido.pk} cambiado a {pedido.get_estado_display()}. Se notificó al cliente por correo.')
        else:
            messages.info(request, f'El pedido #{pedido.pk} ya se encuentra en estado {pedido.get_estado_display()}.')
    else:
        # Fallback legacy si no se especificó nuevo estado
        pedido.toggle_estado()
        enviar_notificacion_estado_pedido(pedido, estado_anterior)
        messages.success(request, f'Estado del pedido #{pedido.pk} cambiado a {pedido.get_estado_display()}.')
    return redirect('pedidos_list')

@admin_required
def pedidos_detalle(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    detalles = list(pedido.detalles.select_related('producto').all())
    movs = list(pedido.movimientos_stock.filter(tipo='salida').order_by('id'))
    movs_libres = list(movs)
    for det in detalles:
        det.talla = None
        for i, mov in enumerate(movs_libres):
            if mov.producto_id == det.producto_id and mov.cantidad == det.cantidad:
                import re
                match = re.search(r'\(Talla:\s*([^)]+)\)', mov.motivo)
                if match:
                    det.talla = match.group(1).strip()
                movs_libres.pop(i)
                break

    notas_info = estructurar_notas_pedido(pedido.notas)

    return render(request, 'dashboard/pedidos/detalle.html', {
        'pedido': pedido,
        'detalles': detalles,
        'notas_info': notas_info,
    })


# ──────────────────────────────────────────────
# PROVEEDORES
# ──────────────────────────────────────────────

@admin_required
def proveedores_list(request):
    proveedor_id = request.GET.get('proveedor')
    proveedores = Proveedor.objects.all().order_by('nombre')
    todos_proveedores = list(proveedores)
    proveedor_seleccionado = None
    if proveedor_id and proveedor_id.isdigit():
        proveedor_seleccionado = int(proveedor_id)
        proveedores = proveedores.filter(pk=proveedor_seleccionado)
    return render(request, 'dashboard/proveedores/list.html', {
        'proveedores': proveedores,
        'todos_proveedores': todos_proveedores,
        'proveedor_seleccionado': proveedor_seleccionado,
        'total_proveedores': proveedores.count(),
    })

@admin_required
def proveedores_crear(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proveedor registrado.')
        return redirect('proveedores_list')
    return render(request, 'dashboard/proveedores/form.html', {'form': form, 'titulo': 'Registrar proveedor'})

@admin_required
def proveedores_editar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proveedor actualizado.')
        return redirect('proveedores_list')
    return render(request, 'dashboard/proveedores/form.html', {'form': form, 'titulo': 'Editar proveedor', 'objeto': proveedor})

@admin_required
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

@admin_required
def disenadores_list(request):
    disenador_id = request.GET.get('disenador')
    disenadores = Disenador.objects.all().order_by('nombre')
    todos_disenadores = list(disenadores)
    disenador_seleccionado = None
    if disenador_id and disenador_id.isdigit():
        disenador_seleccionado = int(disenador_id)
        disenadores = disenadores.filter(pk=disenador_seleccionado)
    return render(request, 'dashboard/disenadores/list.html', {
        'disenadores': disenadores,
        'todos_disenadores': todos_disenadores,
        'disenador_seleccionado': disenador_seleccionado,
        'total_disenadores': disenadores.count(),
    })

@admin_required
def disenadores_crear(request):
    form = DisenadorForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Diseñador registrado.')
        return redirect('disenadores_list')
    return render(request, 'dashboard/disenadores/form.html', {'form': form, 'titulo': 'Registrar diseñador'})

@admin_required
def disenadores_editar(request, pk):
    disenador = get_object_or_404(Disenador, pk=pk)
    form = DisenadorForm(request.POST or None, instance=disenador)
    if form.is_valid():
        form.save()
        messages.success(request, 'Diseñador actualizado.')
        return redirect('disenadores_list')
    return render(request, 'dashboard/disenadores/form.html', {'form': form, 'titulo': 'Editar diseñador', 'objeto': disenador})

@admin_required
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

@admin_required
def roles_list(request):
    estado = request.GET.get('estado')
    roles = Rol.objects.prefetch_related('permisos', 'usuarios').all()
    if estado:
        roles = roles.filter(estado=estado)
    estados = Rol.ESTADO_CHOICES
    return render(request, 'dashboard/roles/list.html', {
        'roles': roles,
        'estados': estados,
        'estado_seleccionado': estado,
        'total_roles': roles.count(),
    })

@admin_required
def roles_crear(request):
    form = RolForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Rol creado.')
        return redirect('roles_list')
    return render(request, 'dashboard/roles/form.html', {'form': form, 'titulo': 'Crear rol'})

@admin_required
def roles_editar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    form = RolForm(request.POST or None, instance=rol)
    if form.is_valid():
        form.save()
        messages.success(request, 'Rol actualizado.')
        return redirect('roles_list')
    return render(request, 'dashboard/roles/form.html', {'form': form, 'titulo': 'Editar rol', 'objeto': rol})

@admin_required
def roles_eliminar(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.delete()
        messages.success(request, 'Rol eliminado.')
        return redirect('roles_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': rol, 'tipo': 'rol'})

@admin_required
def roles_toggle_estado(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    rol.activo = not rol.activo
    rol.save()
    return redirect('roles_list')

# ──────────────────────────────────────────────
# PERMISOS
# ──────────────────────────────────────────────

@admin_required
def permisos_list(request):
    rol_id = request.GET.get('rol')
    permisos = Permiso.objects.prefetch_related('roles').all()
    rol_seleccionado = None
    if rol_id and rol_id.isdigit():
        rol_seleccionado = int(rol_id)
        permisos = permisos.filter(roles__id=rol_seleccionado)
    roles = Rol.objects.all().order_by('nombre')
    return render(request, 'dashboard/permisos/list.html', {
        'permisos': permisos,
        'roles': roles,
        'rol_seleccionado': rol_seleccionado,
        'total_permisos': permisos.count(),
    })

@admin_required
def permisos_crear(request):
    form = PermisoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Permiso creado.')
        return redirect('permisos_list')
    return render(request, 'dashboard/permisos/form.html', {'form': form, 'titulo': 'Crear permiso'})

@admin_required
def permisos_editar(request, pk):
    permiso = get_object_or_404(Permiso, pk=pk)
    form = PermisoForm(request.POST or None, instance=permiso)
    if form.is_valid():
        form.save()
        messages.success(request, 'Permiso actualizado.')
        return redirect('permisos_list')
    return render(request, 'dashboard/permisos/form.html', {'form': form, 'titulo': 'Editar permiso', 'objeto': permiso})

@admin_required
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

@admin_required
def dashboard_users_list(request):
    rol_id = request.GET.get('rol')
    users = User.objects.prefetch_related('perfil__rol').all().order_by('username')
    rol_seleccionado = None
    if rol_id:
        if rol_id == 'sin_rol':
            users = users.filter(perfil__rol__isnull=True)
            rol_seleccionado = 'sin_rol'
        elif rol_id.isdigit():
            rol_seleccionado = int(rol_id)
            users = users.filter(perfil__rol_id=rol_seleccionado)
    roles = Rol.objects.all().order_by('nombre')
    return render(request, 'dashboard/dashboard_users/list.html', {
        'users': users,
        'roles': roles,
        'rol_seleccionado': rol_seleccionado,
        'total_users': users.count(),
    })

@admin_required
def dashboard_users_crear(request):
    form = UsuarioDashboardForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario del dashboard creado.')
        return redirect('dashboard_users_list')
    return render(request, 'dashboard/dashboard_users/form.html', {'form': form, 'titulo': 'Crear usuario dashboard'})

@admin_required
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

@admin_required
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

@admin_required
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
    try:
        token_obj = TokenRecuperacion.objects.select_related('usuario').get(token=token)
    except TokenRecuperacion.DoesNotExist:
        messages.error(request, 'El enlace de recuperación no es válido.')
        return redirect('recuperar_password')

    if not token_obj.es_valido():
        messages.error(request, 'El enlace ha expirado o ya fue utilizado. Solicita uno nuevo.')
        return redirect('recuperar_password')

    exito = False

    if request.method == 'POST':
        form = CambiarContrasenaForm(request.POST)
        if form.is_valid():
            user = token_obj.usuario
            user.set_password(form.cleaned_data['password1'])
            user.save()
            token_obj.usado = True
            token_obj.save()
            exito = True
    else:
        form = CambiarContrasenaForm()

    return render(request, 'registration/recuperar_password_confirmar.html', {
        'form': form,
        'token_obj': token_obj,
        'exito': exito,
    })


# ──────────────────────────────────────────────
# MENSAJES ENVIADOS A USUARIOS
# ──────────────────────────────────────────────

@admin_required
def mensajes_list(request):
    cliente_id = request.GET.get('cliente')
    mensajes = Mensaje.objects.select_related('destinatario', 'pedido').all().order_by('-fecha_envio')

    cliente_seleccionado = None
    if cliente_id and cliente_id.isdigit():
        cliente_id_int = int(cliente_id)
        mensajes = mensajes.filter(destinatario_id=cliente_id_int)
        cliente_seleccionado = cliente_id_int

    clientes = Cliente.objects.all().order_by('nombre', 'apellido')

    return render(request, 'dashboard/mensajes/list.html', {
        'mensajes': mensajes,
        'clientes': clientes,
        'cliente_seleccionado': cliente_seleccionado,
        'total_mensajes': mensajes.count(),
    })

@admin_required
def mensajes_crear(request):
    form = MensajeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        mensaje = form.save()
        messages.success(request, f'Mensaje #{mensaje.pk} registrado y enviado exitosamente a {mensaje.destinatario}.')
        return redirect('mensajes_list')
    return render(request, 'dashboard/mensajes/form.html', {'form': form, 'titulo': 'Registrar mensaje'})

@admin_required
def mensajes_detalle(request, pk):
    mensaje = get_object_or_404(Mensaje.objects.select_related('destinatario', 'pedido'), pk=pk)
    return render(request, 'dashboard/mensajes/detalle.html', {'mensaje': mensaje})

@admin_required
def mensajes_eliminar(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado.')
        return redirect('mensajes_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {'objeto': mensaje, 'tipo': 'mensaje'})