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
    MensajeForm, PrendaComunidadAdminForm
)
from tienda.models import PrendaComunidad
from .emails import enviar_notificacion_estado_pedido
from django.db.models import ProtectedError, F
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# HELPERS DE PERMISOS
# ──────────────────────────────────────────────

def es_admin(user):
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    try:
        return user.perfil.es_admin()
    except PerfilUsuario.DoesNotExist:
        return False


def admin_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
    decorated = user_passes_test(
        es_admin,
        login_url='login',
        redirect_field_name=None  # type: ignore[arg-type]
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
        'total_comunidad':   PrendaComunidad.objects.count(),
        'ultimos_movimientos': MovimientoStock.objects.select_related('producto', 'usuario').order_by('-fecha')[:5],
        'productos_bajo_stock': Producto.objects.filter(estado='activo', stock__lte=F('stock_minimo'))[:5],
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
        # Validar si tiene pedidos o publicaciones asociadas antes de eliminar
        tiene_pedidos = cliente.pedidos.exists()
        tiene_prendas = hasattr(cliente, 'prendas_comunidad') and cliente.prendas_comunidad.exists()
        if tiene_pedidos or tiene_prendas:
            motivo = 'pedidos registrados' if tiene_pedidos else 'prendas publicadas en comunidad'
            messages.error(
                request,
                f'No se puede eliminar al usuario {cliente.nombre} {cliente.apellido} porque tiene {motivo}. En su lugar, puedes cambiar su estado a Inactivo.'
            )
            return redirect('usuarios_list')

        cliente.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
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

def _obtener_imagenes_productos():
    """Obtiene la lista de nombres de imágenes ya disponibles en media/productos/."""
    ruta_dir = settings.MEDIA_ROOT / 'productos'
    if not ruta_dir.exists():
        return []
    extensiones_validas = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    archivos = []
    for item in ruta_dir.iterdir():
        if item.is_file() and item.suffix.lower() in extensiones_validas:
            archivos.append(item.name)
    archivos.sort()
    return archivos


@admin_required
def productos_crear(request):
    form = ProductoForm(request.POST or None, request.FILES or None)
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
    imagenes_existentes = _obtener_imagenes_productos()
    return render(request, 'dashboard/productos/form.html', {
        'form': form,
        'titulo': 'Registrar producto',
        'imagenes_existentes': imagenes_existentes,
    })

@admin_required
def productos_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.estado == 'inactivo':
        messages.error(request, f'No se puede editar el producto "{producto.nombre}" porque está inactivo. Actívelo primero.')
        return redirect('productos_list')
    form = ProductoEditarForm(request.POST or None, request.FILES or None, instance=producto)
    if form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('productos_list')
    imagenes_existentes = _obtener_imagenes_productos()
    return render(request, 'dashboard/productos/form.html', {
        'form': form,
        'titulo': 'Editar producto',
        'objeto': producto,
        'imagenes_existentes': imagenes_existentes,
    })

@admin_required
def productos_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            producto.delete()
            messages.success(request, 'Producto eliminado.')
        except ProtectedError:
            messages.error(request, f'No se puede eliminar el producto "{producto.nombre}" porque tiene pedidos asociados')
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

def _registrar_movimiento_stock(request, tipo, titulo, help_text=None):
    """Procesa y registra un movimiento de stock (entrada, salida o ajuste) de forma segura y atómica."""
    form = MovimientoStockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            mov = form.save(commit=False)
            mov.tipo = tipo
            producto = mov.producto

            if tipo == 'salida' and mov.cantidad > producto.stock:
                messages.error(request, f'Stock insuficiente. Disponible: {producto.stock}')
                return render(request, 'dashboard/stock/form.html', {
                    'form': form, 'titulo': titulo, 'tipo': tipo
                })

            mov.stock_anterior = producto.stock
            if tipo == 'entrada':
                producto.stock += mov.cantidad
            elif tipo == 'salida':
                producto.stock -= mov.cantidad
            elif tipo == 'ajuste':
                producto.stock = mov.cantidad

            producto.save(update_fields=['stock'])
            mov.stock_posterior = producto.stock
            mov.usuario = request.user
            mov.fecha = timezone.now()
            mov.save()

        if tipo == 'ajuste':
            messages.success(request, f'Stock ajustado a {mov.cantidad} unidades para "{mov.producto.nombre}".')
        else:
            tipo_label = 'Entrada' if tipo == 'entrada' else 'Salida'
            messages.success(request, f'{tipo_label} de {mov.cantidad} unidades registrada para "{mov.producto.nombre}".')
        return redirect('stock_list')

    context = {'form': form, 'titulo': titulo, 'tipo': tipo}
    if help_text:
        context['help_text'] = help_text
    return render(request, 'dashboard/stock/form.html', context)


@admin_required
def stock_entrada(request):
    return _registrar_movimiento_stock(request, 'entrada', 'Registrar Entrada de Stock')


@admin_required
def stock_salida(request):
    return _registrar_movimiento_stock(request, 'salida', 'Registrar Salida de Stock')


@admin_required
def stock_ajuste(request):
    return _registrar_movimiento_stock(
        request, 'ajuste', 'Ajuste de Stock',
        help_text='El stock del producto se establecerá exactamente al valor ingresado.'
    )


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

    if categoria.productos.exists():
        messages.error(request, f'No se puede eliminar la categoría "{categoria.nombre}" porque tiene productos asociados.')
        return redirect('categorias_list')
    
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
    from django.db.models import Count
    proveedor_id = request.GET.get('proveedor')
    proveedores = Proveedor.objects.annotate(total_productos=Count('productos')).order_by('nombre')
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

@admin_required
def proveedores_toggle_estado(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.toggle_estado()
    messages.success(request, f'Estado de {proveedor} cambiado a {proveedor.estado}.')
    return redirect('proveedores_list')

# ──────────────────────────────────────────────
# DISEÑADORES
# ──────────────────────────────────────────────

@admin_required
def disenadores_list(request):
    from django.db.models import Count
    disenador_id = request.GET.get('disenador')
    disenadores = Disenador.objects.annotate(total_productos=Count('productos')).order_by('nombre')
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

@admin_required
def disenadores_toggle_estado(request, pk):
    disenador = get_object_or_404(Disenador, pk=pk)
    disenador.toggle_estado()
    messages.success(request, f'Estado de {disenador} cambiado a {disenador.estado}.')
    return redirect('disenadores_list')
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
    rol.toggle_estado()
    messages.success(request, f'Estado de {rol} cambiado a {rol.estado}.')
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
def permisos_detalle(request, pk):
    permiso = get_object_or_404(Permiso.objects.prefetch_related('roles'), pk=pk)
    return render(request, 'dashboard/permisos/detalle.html', {
        'permiso': permiso,
    })

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
    if permiso.codigo in ['administrador', 'cliente']:
        messages.error(request, f'No se puede eliminar el permiso esencial "{permiso.nombre}".')
        return redirect('permisos_list')
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
        destinatario = form.cleaned_data['destinatario']
        correo_destino = destinatario.correo  # campo `correo` verificado en modelo Cliente
        tipo_display = dict(Mensaje.TIPO_CHOICES).get(
            form.cleaned_data['tipo'], form.cleaned_data['tipo']  # .get() evita KeyError
        )
        contenido = form.cleaned_data['contenido']
        remitente = form.cleaned_data.get('remitente') or 'Haze Studios'

        html_message = render_to_string('dashboard/emails/mensaje_cliente.html', {
            'tipo_display': tipo_display,
            'destinatario': destinatario,
            'contenido': contenido,
            'remitente': remitente,
        })

        try:
            send_mail(
                subject=f'[Haze Studios] {tipo_display}',
                message=contenido,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[correo_destino],
                html_message=html_message,
                fail_silently=False,
            )
            # Solo se guarda en BD si el correo se envió correctamente
            mensaje = form.save()
            messages.success(request, f'Mensaje #{mensaje.pk} enviado exitosamente a {mensaje.destinatario}.')
        except Exception as e:
            logger.error(f'Error al enviar mensaje a {correo_destino}: {e}')
            messages.error(request, f'No se pudo enviar el correo a {correo_destino}. Verifica la configuración SMTP y vuelve a intentarlo.')
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


# ──────────────────────────────────────────────
# COMUNIDAD (MODERACIÓN Y CRUD ADMINISTRATIVO)
# ──────────────────────────────────────────────

@admin_required
def comunidad_admin_list(request):
    """
    Permite exclusivamente al administrador consultar y moderar las prendas publicadas en la comunidad.
    Solo muestra las prendas publicadas (no aparecen personalizaciones en proceso sin publicar).
    """
    estado = request.GET.get('estado', '').strip()
    q = request.GET.get('q', '').strip()

    prendas = PrendaComunidad.objects.select_related(
        'autor', 'personalizacion', 'personalizacion__producto', 'producto_base'
    ).all().order_by('-fecha_publicacion')

    if estado in ('activo', 'inactivo'):
        prendas = prendas.filter(estado=estado)
    if q:
        prendas = prendas.filter(nombre__icontains=q)

    return render(request, 'dashboard/comunidad/list.html', {
        'prendas': prendas,
        'estado_seleccionado': estado,
        'q': q,
        'total_prendas': prendas.count(),
    })


@admin_required
def comunidad_admin_detalle(request, pk):
    """
    Muestra al administrador toda la información de la publicación y toda la personalización asociada.
    """
    prenda = get_object_or_404(
        PrendaComunidad.objects.select_related(
            'autor', 'personalizacion', 'personalizacion__producto', 'producto_base'
        ),
        pk=pk
    )
    comentarios = prenda.comentarios.select_related('autor').order_by('-fecha_publicacion')
    return render(request, 'dashboard/comunidad/detalle.html', {
        'prenda': prenda,
        'comentarios': comentarios,
        'total_reacciones': prenda.reacciones.count(),
    })


@admin_required
def comunidad_admin_editar(request, pk):
    """Permite al administrador editar una prenda publicada en la comunidad."""
    prenda = get_object_or_404(PrendaComunidad, pk=pk)
    form = PrendaComunidadAdminForm(request.POST or None, request.FILES or None, instance=prenda)
    if request.method == 'POST' and form.is_valid():
        prenda_actualizada = form.save()
        if prenda_actualizada.personalizacion:
            pers = prenda_actualizada.personalizacion
            pers.nombre_personalizacion = prenda_actualizada.nombre
            pers.color = prenda_actualizada.color
            pers.talla = prenda_actualizada.talla
            pers.estampado = prenda_actualizada.estampado
            pers.tipografia = prenda_actualizada.tipografia
            pers.detalle = prenda_actualizada.descripcion
            # Sincronizar estado de la personalización si se inactiva
            if prenda_actualizada.estado == 'inactivo':
                pers.estado = 'en_proceso'
            else:
                pers.estado = 'publicada'
            pers.save()
        messages.success(request, f'Publicación "{prenda.nombre}" actualizada correctamente.')
        return redirect('comunidad_admin_list')
    return render(request, 'dashboard/comunidad/form.html', {
        'form': form,
        'prenda': prenda,
        'titulo': f'Editar publicación: {prenda.nombre}',
    })


@admin_required
def comunidad_admin_toggle_estado(request, pk):
    """Permite al administrador cambiar el estado (Activo / Inactivo) de una publicación en comunidad."""
    prenda = get_object_or_404(PrendaComunidad, pk=pk)
    motivo = (request.POST.get('motivo_inactivacion') or request.GET.get('motivo_inactivacion') or '').strip()
    prenda.toggle_estado()
    if prenda.estado == 'inactivo' and motivo:
        prenda.motivo_inactivacion = motivo
        prenda.save(update_fields=['motivo_inactivacion'])
    elif prenda.estado == 'activo':
        prenda.motivo_inactivacion = ''
        prenda.save(update_fields=['motivo_inactivacion'])

    # Sincronizar estado en personalización
    if prenda.personalizacion:
        prenda.personalizacion.estado = 'publicada' if prenda.estado == 'activo' else 'en_proceso'
        prenda.personalizacion.save(update_fields=['estado'])

    messages.info(request, f'Estado de "{prenda.nombre}" cambiado a {prenda.get_estado_display()}.')
    return redirect('comunidad_admin_list')


@admin_required
def comunidad_admin_eliminar(request, pk):
    """Permite al administrador eliminar una prenda publicada en la comunidad previa confirmación."""
    prenda = get_object_or_404(PrendaComunidad, pk=pk)
    if request.method == 'POST':
        nombre = prenda.nombre
        if prenda.personalizacion:
            pers = prenda.personalizacion
            pers.estado = 'en_proceso'
            pers.save(update_fields=['estado'])
        prenda.delete()
        messages.success(request, f'La publicación "{nombre}" fue eliminada de la comunidad.')
        return redirect('comunidad_admin_list')
    return render(request, 'dashboard/confirmar_eliminar.html', {
        'objeto': prenda,
        'tipo': 'publicación de comunidad',
    })
