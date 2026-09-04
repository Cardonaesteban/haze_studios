from decimal import Decimal
import re
import unicodedata
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from functools import wraps

from dashboard.models import (
    Cliente, Producto, Categoria, Disenador, Pedido, DetallePedido, MovimientoStock
)
from django.db.models import Count, Q
from .models import TokenRecuperacionCliente
from .forms import (
    LoginClienteForm, RegistroClienteForm, PerfilClienteForm,
    CambiarPasswordClienteForm, SolicitarRecuperacionClienteForm,
    ConfirmarPasswordClienteForm, CheckoutForm
)


# ──────────────────────────────────────────────
# DECORADORES Y UTILIDADES DE SESIÓN
# ──────────────────────────────────────────────

def cliente_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('cliente_id'):
            messages.info(request, 'Debes iniciar sesión para continuar.')
            return redirect(f'{reverse("tienda_login")}?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_cliente_actual(request):
    cliente_id = request.session.get('cliente_id')
    if cliente_id:
        try:
            return Cliente.objects.get(pk=cliente_id, estado='activo')
        except Cliente.DoesNotExist:
            request.session.flush()
    return None


def generar_item_key(producto_id, talla):
    """Genera una clave única y segura para URL/HTML combinando producto y talla."""
    n = unicodedata.normalize('NFKD', str(talla)).encode('ASCII', 'ignore').decode('utf-8')
    slug_talla = re.sub(r'[^a-zA-Z0-9]+', '-', n).strip('-').lower() or 'std'
    return f"{producto_id}_{slug_talla}"


def obtener_detalles_con_talla(pedido):
    """Obtiene los detalles del pedido asignando la talla registrada en los movimientos de stock si existe."""
    detalles = list(pedido.detalles.select_related('producto').all())
    movimientos = list(pedido.movimientos_stock.filter(tipo='salida').order_by('id'))
    movs_libres = list(movimientos)

    for det in detalles:
        det.talla = None
        for i, mov in enumerate(movs_libres):
            if mov.producto_id == det.producto_id and mov.cantidad == det.cantidad:
                match = re.search(r'\(Talla:\s*([^)]+)\)', mov.motivo)
                if match:
                    det.talla = match.group(1).strip()
                movs_libres.pop(i)
                break
    return detalles


def get_carrito_items(request):
    """Devuelve los items del carrito con los objetos Producto y totales, diferenciando por talla."""
    carrito = request.session.get('carrito', {})
    items = []
    total_general = Decimal('0')
    total_cantidad = 0

    if not carrito:
        return {'items': items, 'total_general': total_general, 'total_cantidad': total_cantidad}

    # Extraer los IDs únicos de producto compatibles con claves '1' y '1_s-oversize'
    productos_ids = set()
    for key, info in carrito.items():
        if isinstance(info, dict) and 'producto_id' in info:
            try:
                productos_ids.add(int(info['producto_id']))
            except (ValueError, TypeError):
                pass
        elif '_' in str(key):
            try:
                productos_ids.add(int(str(key).split('_')[0]))
            except ValueError:
                pass
        elif str(key).isdigit():
            productos_ids.add(int(key))

    productos = Producto.objects.filter(pk__in=productos_ids, estado='activo')
    productos_dict = {p.pk: p for p in productos}

    for item_key, info in list(carrito.items()):
        if not isinstance(info, dict):
            continue

        prod_id = info.get('producto_id')
        if not prod_id:
            if '_' in str(item_key):
                try:
                    prod_id = int(str(item_key).split('_')[0])
                except ValueError:
                    continue
            elif str(item_key).isdigit():
                prod_id = int(item_key)
            else:
                continue

        producto = productos_dict.get(prod_id)
        if not producto:
            continue

        cantidad = int(info.get('cantidad', 1))
        # Ajustar si el stock disponible es menor a la cantidad en carrito
        if cantidad > producto.stock:
            cantidad = max(0, producto.stock)

        talla = info.get('talla', 'L (Oversize)')
        subtotal = producto.precio * cantidad
        total_general += subtotal
        total_cantidad += cantidad

        items.append({
            'item_key': str(item_key),
            'producto': producto,
            'cantidad': cantidad,
            'talla': talla,
            'subtotal': subtotal,
            'stock_disponible': producto.stock,
            'sin_stock': producto.stock <= 0 or cantidad <= 0
        })

    return {
        'items': items,
        'total_general': total_general,
        'total_cantidad': total_cantidad
    }


# ──────────────────────────────────────────────
# PÁGINA PRINCIPAL Y CATÁLOGO
# ──────────────────────────────────────────────

def inicio(request):
    """Página principal / Portada de la tienda Streetwear & Oversize."""
    categorias = Categoria.objects.annotate(
        total_prods=Count('productos', filter=Q(productos__estado='activo'))
    ).filter(total_prods__gt=0)[:6]
    productos_destacados = Producto.objects.filter(estado='activo').order_by('-id')[:8]
    producto_nuevo = Producto.objects.filter(estado='activo').select_related('categoria').order_by('-id').first()
    total_prendas_global = Producto.objects.filter(estado='activo').count()
    cliente = get_cliente_actual(request)

    context = {
        'categorias': categorias,
        'productos_destacados': productos_destacados,
        'producto_nuevo': producto_nuevo,
        'total_prendas_global': total_prendas_global,
        'cliente': cliente,
    }
    return render(request, 'tienda/inicio.html', context)


def productos(request):
    """Catálogo completo de prendas oversize con filtros avanzados y búsqueda."""
    categoria_id = request.GET.get('categoria')
    query = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'recientes')
    rango_precio = request.GET.get('rango_precio', '')
    solo_disponibles = request.GET.get('disponibles') == '1'
    disenador_id = request.GET.get('disenador')

    productos_qs = Producto.objects.filter(estado='activo').select_related('categoria', 'disenador')

    if categoria_id and categoria_id.isdigit():
        productos_qs = productos_qs.filter(categoria_id=int(categoria_id))

    if disenador_id and disenador_id.isdigit():
        productos_qs = productos_qs.filter(disenador_id=int(disenador_id))

    if query:
        productos_qs = productos_qs.filter(nombre__icontains=query)

    if solo_disponibles:
        productos_qs = productos_qs.filter(stock__gt=0)

    # Rango de precios
    if rango_precio == 'menos_100':
        productos_qs = productos_qs.filter(precio__lt=100000)
    elif rango_precio == '100_180':
        productos_qs = productos_qs.filter(precio__gte=100000, precio__lte=180000)
    elif rango_precio == 'mas_180':
        productos_qs = productos_qs.filter(precio__gt=180000)

    if orden == 'precio_asc':
        productos_qs = productos_qs.order_by('precio')
    elif orden == 'precio_desc':
        productos_qs = productos_qs.order_by('-precio')
    elif orden == 'nombre':
        productos_qs = productos_qs.order_by('nombre')
    else:
        productos_qs = productos_qs.order_by('-id')

    # Categorías con conteo de prendas activas
    categorias = Categoria.objects.annotate(
        total_prods=Count('productos', filter=Q(productos__estado='activo'))
    )
    disenadores = Disenador.objects.annotate(
        total_prods=Count('productos', filter=Q(productos__estado='activo'))
    ).filter(total_prods__gt=0)

    total_prendas_global = Producto.objects.filter(estado='activo').count()
    cliente = get_cliente_actual(request)

    context = {
        'productos': productos_qs,
        'categorias': categorias,
        'disenadores': disenadores,
        'total_prendas_global': total_prendas_global,
        'categoria_seleccionada': int(categoria_id) if categoria_id and categoria_id.isdigit() else None,
        'disenador_seleccionado': int(disenador_id) if disenador_id and disenador_id.isdigit() else None,
        'rango_precio': rango_precio,
        'solo_disponibles': solo_disponibles,
        'query': query,
        'orden': orden,
        'cliente': cliente,
    }
    return render(request, 'tienda/productos.html', context)


def producto_detalle(request, pk):
    """Ficha de detalle de la prenda oversize, guía de medidas y botón de compra."""
    producto = get_object_or_404(Producto, pk=pk, estado='activo')
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria, estado='activo'
    ).exclude(pk=producto.pk)[:4]
    cliente = get_cliente_actual(request)

    context = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
        'cliente': cliente,
    }
    return render(request, 'tienda/producto_detalle.html', context)


# ──────────────────────────────────────────────
# CARRITO DE COMPRAS
# ──────────────────────────────────────────────

def carrito(request):
    """Vista de resumen del carrito."""
    carrito_data = get_carrito_items(request)
    cliente = get_cliente_actual(request)
    context = {
        'items': carrito_data['items'],
        'total_general': carrito_data['total_general'],
        'total_cantidad': carrito_data['total_cantidad'],
        'cliente': cliente,
    }
    return render(request, 'tienda/carrito.html', context)


def agregar_carrito(request, producto_id):
    """Añadir producto al carrito diferenciando por talla con validación de stock."""
    producto = get_object_or_404(Producto, pk=producto_id, estado='activo')

    if producto.stock <= 0:
        messages.error(request, f'Lo sentimos, "{producto.nombre}" está agotado temporalmente.')
        return redirect('tienda_producto_detalle', pk=producto_id)

    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (ValueError, TypeError):
        cantidad = 1

    if cantidad < 1:
        cantidad = 1

    talla = request.POST.get('talla', 'L (Oversize)').strip()
    item_key = generar_item_key(producto.pk, talla)

    carrito = request.session.get('carrito', {})

    # Unidades ya presentes de este producto en el carrito (otras tallas)
    cantidad_otras_tallas = sum(
        it.get('cantidad', 0) for k, it in carrito.items()
        if isinstance(it, dict) and k != item_key and (
            it.get('producto_id') == producto.pk
            or str(k).startswith(f"{producto.pk}_")
            or str(k) == str(producto.pk)
        )
    )

    stock_disponible = max(0, producto.stock - cantidad_otras_tallas)

    if stock_disponible <= 0:
        messages.warning(
            request,
            f'No puedes agregar más unidades de "{producto.nombre}". Ya tienes {cantidad_otras_tallas} unidad(es) de otras tallas en el carrito y el stock total es {producto.stock}.'
        )
        return redirect('tienda_carrito')

    cantidad_actual = carrito.get(item_key, {}).get('cantidad', 0) if isinstance(carrito.get(item_key), dict) else 0
    nueva_cantidad = cantidad_actual + cantidad

    if nueva_cantidad > stock_disponible:
        nueva_cantidad = stock_disponible
        messages.warning(
            request,
            f'Se ajustó a {nueva_cantidad} unidad(es) en talla {talla} para no superar el stock disponible ({producto.stock}).'
        )

    carrito[item_key] = {
        'producto_id': producto.pk,
        'cantidad': nueva_cantidad,
        'talla': talla,
    }
    request.session['carrito'] = carrito
    request.session.modified = True

    messages.success(request, f'¡"{producto.nombre}" (Talla: {talla}) se añadió al carrito!')
    return redirect('tienda_carrito')


def actualizar_carrito(request):
    """Actualizar cantidades de artículos en el carrito diferenciando por variante/talla."""
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        for key, value in request.POST.items():
            if key.startswith('cantidad_'):
                item_key = key.replace('cantidad_', '', 1)
                try:
                    nueva_cant = int(value)
                    if item_key in carrito:
                        item_data = carrito[item_key]
                        prod_id = item_data.get('producto_id')
                        if not prod_id and '_' in item_key:
                            prod_id = int(item_key.split('_')[0])
                        elif not prod_id and item_key.isdigit():
                            prod_id = int(item_key)

                        producto = Producto.objects.filter(pk=prod_id, estado='activo').first()
                        if not producto or nueva_cant <= 0:
                            del carrito[item_key]
                        else:
                            # Calcular el stock disponible descontando otras tallas del mismo producto
                            otras_cant = sum(
                                it.get('cantidad', 0) for k, it in carrito.items()
                                if k != item_key and isinstance(it, dict) and (
                                    it.get('producto_id') == producto.pk
                                    or str(k).startswith(f"{producto.pk}_")
                                    or str(k) == str(producto.pk)
                                )
                            )
                            max_permitido = max(0, producto.stock - otras_cant)
                            if nueva_cant > max_permitido:
                                carrito[item_key]['cantidad'] = max_permitido
                                messages.warning(
                                    request,
                                    f'Cantidad para "{producto.nombre} ({item_data.get("talla", "")})" ajustada a {max_permitido} por stock disponible.'
                                )
                            else:
                                carrito[item_key]['cantidad'] = nueva_cant
                except (ValueError, TypeError):
                    pass

        request.session['carrito'] = carrito
        request.session.modified = True

    return redirect('tienda_carrito')


def eliminar_carrito(request, item_key):
    """Eliminar un producto y talla específico del carrito."""
    carrito = request.session.get('carrito', {})
    item_key_str = str(item_key)
    if item_key_str in carrito:
        del carrito[item_key_str]
        request.session['carrito'] = carrito
        request.session.modified = True
        messages.success(request, 'Prenda eliminada del carrito.')
    elif item_key_str.isdigit():
        # Soporte para IDs numéricos anteriores
        a_borrar = [k for k in carrito if k == item_key_str or str(k).startswith(f"{item_key_str}_")]
        for k in a_borrar:
            del carrito[k]
        request.session['carrito'] = carrito
        request.session.modified = True
        messages.success(request, 'Prenda eliminada del carrito.')
    return redirect('tienda_carrito')


def vaciar_carrito(request):
    """Vaciar todo el contenido del carrito."""
    request.session['carrito'] = {}
    request.session.modified = True
    messages.info(request, 'El carrito ha sido vaciado.')
    return redirect('tienda_carrito')


# ──────────────────────────────────────────────
# REALIZAR PEDIDO (CHECKOUT)
# ──────────────────────────────────────────────

@cliente_required
def checkout(request):
    """Pasarela de confirmación de pedido y datos de entrega."""
    cliente = get_cliente_actual(request)
    carrito_data = get_carrito_items(request)

    if not carrito_data['items']:
        messages.warning(request, 'Tu carrito de compras está vacío.')
        return redirect('tienda_productos')

    # Validar si algún producto no tiene stock
    hay_sin_stock = any(item['sin_stock'] for item in carrito_data['items'])
    if hay_sin_stock:
        messages.error(request, 'Uno o más productos en tu carrito no tienen stock suficiente. Por favor revísalos.')
        return redirect('tienda_carrito')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            direccion_envio = form.cleaned_data['direccion_envio']
            telefono = form.cleaned_data['telefono_contacto']
            notas = form.cleaned_data['notas']

            # Transacción atómica para crear pedido y descontar stock
            try:
                with transaction.atomic():
                    # Sumar cantidad total requerida por producto para verificar stock conjunto
                    totales_por_producto = {}
                    for item in carrito_data['items']:
                        pid = item['producto'].pk
                        totales_por_producto[pid] = totales_por_producto.get(pid, 0) + item['cantidad']

                    # Re-verificar y bloquear stock
                    for pid, cant_requerida in totales_por_producto.items():
                        prod = Producto.objects.select_for_update().get(pk=pid)
                        if prod.stock < cant_requerida:
                            raise ValueError(
                                f'Stock insuficiente para "{prod.nombre}". Solicitado en total: {cant_requerida}, Disponible: {prod.stock}'
                            )

                    # Formato limpio y estructurado para notas de entrega y contacto
                    partes_notas = [
                        f"Contacto: {telefono}",
                        f"Entrega: {direccion_envio}"
                    ]
                    if notas and notas.strip():
                        partes_notas.append(f"Instrucciones del cliente: {notas.strip()}")

                    notas_finales = "\n".join(partes_notas)

                    # Crear Pedido principal en Dashboard
                    pedido = Pedido.objects.create(
                        cliente=cliente,
                        fecha_pedido=timezone.now().date(),
                        estado='pendiente',
                        total=carrito_data['total_general'],
                        notas=notas_finales.strip()
                    )

                    # Crear Detalles y descontar stock con movimiento
                    for item in carrito_data['items']:
                        prod = Producto.objects.get(pk=item['producto'].pk)
                        cant = item['cantidad']
                        stock_ant = prod.stock
                        stock_post = max(0, stock_ant - cant)

                        # Crear detalle
                        DetallePedido.objects.create(
                            pedido=pedido,
                            producto=prod,
                            cantidad=cant,
                            precio_unitario=prod.precio
                        )

                        # Actualizar producto
                        prod.stock = stock_post
                        prod.save(update_fields=['stock'])

                        # Registrar movimiento de stock de salida
                        MovimientoStock.objects.create(
                            producto=prod,
                            tipo='salida',
                            cantidad=cant,
                            stock_anterior=stock_ant,
                            stock_posterior=stock_post,
                            motivo=f'Compra Tienda Web - Pedido #{pedido.pk} (Talla: {item["talla"]})',
                            pedido=pedido
                        )

                    # Vaciar carrito de la sesión
                    request.session['carrito'] = {}
                    request.session.modified = True

                    messages.success(request, f'¡Pedido #{pedido.pk} realizado con éxito!')
                    return redirect('tienda_pedido_confirmado', pedido_id=pedido.pk)

            except ValueError as e:
                messages.error(request, str(e))
                return redirect('tienda_carrito')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al procesar el pedido: {str(e)}')
        else:
            messages.warning(request, 'Revisa los campos marcados y corrige los errores.')
    else:
        # Pre-llenar con los datos guardados del cliente
        initial_data = {
            'direccion_envio': cliente.direccion,
            'telefono_contacto': cliente.telefono,
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'items': carrito_data['items'],
        'total_general': carrito_data['total_general'],
        'total_cantidad': carrito_data['total_cantidad'],
        'cliente': cliente,
    }
    return render(request, 'tienda/checkout.html', context)


@cliente_required
def pedido_confirmado(request, pedido_id):
    """Pantalla de confirmación de pedido."""
    cliente = get_cliente_actual(request)
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)
    detalles = obtener_detalles_con_talla(pedido)

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'cliente': cliente,
    }
    return render(request, 'tienda/pedido_confirmado.html', context)


@cliente_required
def mis_pedidos(request):
    """Historial de pedidos realizados por el cliente."""
    cliente = get_cliente_actual(request)
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-id').prefetch_related('detalles__producto')

    context = {
        'pedidos': pedidos,
        'cliente': cliente,
    }
    return render(request, 'tienda/mis_pedidos.html', context)


@cliente_required
def pedido_detalle(request, pedido_id):
    """Vista detallada de un pedido específico."""
    cliente = get_cliente_actual(request)
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)
    detalles = obtener_detalles_con_talla(pedido)

    context = {
        'pedido': pedido,
        'detalles': detalles,
        'cliente': cliente,
    }
    return render(request, 'tienda/pedido_detalle.html', context)


# ──────────────────────────────────────────────
# AUTENTICACIÓN Y REGISTRO DE CLIENTES
# ──────────────────────────────────────────────

def login_cliente(request):
    """Inicio de sesión para clientes de la tienda."""
    if request.session.get('cliente_id'):
        return redirect('tienda_inicio')

    next_url = request.GET.get('next', 'tienda_inicio')
    error = None

    if request.method == 'POST':
        form = LoginClienteForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            contraseña = form.cleaned_data['contraseña']

            try:
                cliente = Cliente.objects.get(correo=correo)
            except Cliente.DoesNotExist:
                error = 'Correo electrónico o contraseña incorrectos.'
            else:
                if cliente.estado == 'inactivo':
                    error = 'Tu cuenta se encuentra inactiva. Contacta con soporte.'
                elif check_password(contraseña, cliente.contraseña):
                    request.session['cliente_id'] = cliente.pk
                    request.session['cliente_nombre'] = cliente.nombre
                    request.session['cliente_correo'] = cliente.correo
                    messages.success(request, f'¡Bienvenido de nuevo, {cliente.nombre}!')
                    if next_url and next_url != 'tienda_inicio' and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect('tienda_inicio')
                else:
                    error = 'Correo electrónico o contraseña incorrectos.'
    else:
        form = LoginClienteForm()

    return render(request, 'tienda/login.html', {'form': form, 'error': error, 'next': next_url})


def registro_cliente(request):
    """Registro de nuevos clientes."""
    if request.session.get('cliente_id'):
        return redirect('tienda_inicio')

    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.contraseña = make_password(form.cleaned_data['contraseña'])
            cliente.estado = 'activo'
            cliente.save()

            # Iniciar sesión automáticamente
            request.session['cliente_id'] = cliente.pk
            request.session['cliente_nombre'] = cliente.nombre
            request.session['cliente_correo'] = cliente.correo

            messages.success(request, f'¡Cuenta creada exitosamente! Bienvenido a Haze Studios, {cliente.nombre}.')
            return redirect('tienda_inicio')
    else:
        form = RegistroClienteForm()

    return render(request, 'tienda/registro.html', {'form': form})


def logout_cliente(request):
    """Cerrar sesión del cliente."""
    # Guardar carrito temporalmente si se desea, o limpiar sesión
    carrito = request.session.get('carrito', {})
    request.session.flush()
    # Mantener carrito anónimo
    if carrito:
        request.session['carrito'] = carrito
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('tienda_login')


# ──────────────────────────────────────────────
# PERFIL DE USUARIO Y RECUPERACIÓN DE CONTRASEÑA
# ──────────────────────────────────────────────

@cliente_required
def perfil_cliente(request):
    """Ver y editar datos del perfil de usuario."""
    cliente = get_cliente_actual(request)

    if request.method == 'POST':
        form = PerfilClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            request.session['cliente_nombre'] = cliente.nombre
            messages.success(request, 'Tus datos de perfil han sido actualizados con éxito.')
            return redirect('tienda_perfil')
    else:
        form = PerfilClienteForm(instance=cliente)

    context = {
        'form': form,
        'cliente': cliente,
    }
    return render(request, 'tienda/perfil.html', context)


@cliente_required
def cambiar_password_cliente(request):
    """Cambiar contraseña desde el perfil de usuario."""
    cliente = get_cliente_actual(request)

    if request.method == 'POST':
        form = CambiarPasswordClienteForm(request.POST, cliente=cliente)
        if form.is_valid():
            nuevo_pass = form.cleaned_data['nuevo_password']
            cliente.contraseña = make_password(nuevo_pass)
            cliente.save(update_fields=['contraseña'])
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
            return redirect('tienda_perfil')
    else:
        form = CambiarPasswordClienteForm(cliente=cliente)

    context = {
        'form': form,
        'cliente': cliente,
    }
    return render(request, 'tienda/cambiar_password.html', context)


def recuperar_password_cliente(request):
    """Paso 1: solicitar recuperación; se envía enlace seguro por correo."""
    if request.session.get('cliente_id'):
        return redirect('tienda_inicio')

    if request.method == 'POST':
        form = SolicitarRecuperacionClienteForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            cliente = Cliente.objects.filter(correo=correo, estado='activo').first()

            if cliente:
                TokenRecuperacionCliente.objects.filter(
                    cliente=cliente, usado=False
                ).update(usado=True)
                token_obj = TokenRecuperacionCliente.objects.create(cliente=cliente)
                reset_url = request.build_absolute_uri(
                    reverse('tienda_recuperar_password_confirmar', kwargs={'token': token_obj.token})
                )
                send_mail(
                    subject='Restablecer contraseña — Haze Studios',
                    message=(
                        f'Hola {cliente.nombre},\n\n'
                        f'Recibimos una solicitud para restablecer la contraseña de tu cuenta.\n'
                        f'Usa este enlace (válido 2 horas, un solo uso):\n\n'
                        f'{reset_url}\n\n'
                        f'Si no solicitaste este cambio, ignora este correo.\n\n'
                        f'— Haze Studios'
                    ),
                    from_email=None,
                    recipient_list=[cliente.correo],
                    fail_silently=False,
                )

            return redirect('tienda_recuperar_password_enviado')
    else:
        form = SolicitarRecuperacionClienteForm()

    return render(request, 'tienda/recuperar_password.html', {'form': form})


def recuperar_password_enviado(request):
    """Confirmación de solicitud enviada (sin revelar si el correo existe)."""
    return render(request, 'tienda/recuperar_password_enviado.html')


def recuperar_password_confirmar_cliente(request, token):
    """Paso 2: restablecer contraseña solo con token válido."""
    try:
        token_obj = TokenRecuperacionCliente.objects.select_related('cliente').get(token=token)
    except TokenRecuperacionCliente.DoesNotExist:
        messages.error(request, 'El enlace de recuperación no es válido.')
        return redirect('tienda_recuperar_password')

    if not token_obj.es_valido():
        messages.error(request, 'El enlace ha expirado o ya fue utilizado. Solicita uno nuevo.')
        return redirect('tienda_recuperar_password')

    if request.method == 'POST':
        form = ConfirmarPasswordClienteForm(request.POST)
        if form.is_valid():
            cliente = token_obj.cliente
            cliente.contraseña = make_password(form.cleaned_data['password1'])
            cliente.save(update_fields=['contraseña'])
            token_obj.usado = True
            token_obj.save()
            messages.success(request, '¡Contraseña actualizada correctamente! Ya puedes iniciar sesión.')
            return redirect('tienda_login')
    else:
        form = ConfirmarPasswordClienteForm()

    return render(request, 'tienda/recuperar_password_confirmar.html', {
        'form': form,
        'token_obj': token_obj,
    })