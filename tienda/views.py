from decimal import Decimal
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


def get_carrito_items(request):
    """Devuelve los items del carrito con los objetos Producto y totales."""
    carrito = request.session.get('carrito', {})
    items = []
    total_general = Decimal('0')
    total_cantidad = 0

    if not carrito:
        return {'items': items, 'total_general': total_general, 'total_cantidad': total_cantidad}

    productos_ids = [int(pk) for pk in carrito.keys() if pk.isdigit()]
    productos = Producto.objects.filter(pk__in=productos_ids, estado='activo')
    productos_dict = {p.pk: p for p in productos}

    for prod_id_str, info in list(carrito.items()):
        prod_id = int(prod_id_str)
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
    """Añadir producto al carrito con validación de stock."""
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

    talla = request.POST.get('talla', 'L (Oversize)')

    carrito = request.session.get('carrito', {})
    prod_id_str = str(producto.pk)

    cantidad_actual = carrito.get(prod_id_str, {}).get('cantidad', 0)
    nueva_cantidad = cantidad_actual + cantidad

    if nueva_cantidad > producto.stock:
        messages.warning(
            request,
            f'No puedes agregar {nueva_cantidad} unidades. Stock disponible: {producto.stock}.'
        )
        nueva_cantidad = producto.stock

    carrito[prod_id_str] = {
        'cantidad': nueva_cantidad,
        'talla': talla,
    }
    request.session['carrito'] = carrito
    request.session.modified = True

    messages.success(request, f'¡"{producto.nombre}" ({talla}) se añadió al carrito!')
    return redirect('tienda_carrito')


def actualizar_carrito(request):
    """Actualizar cantidades de artículos en el carrito."""
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        for key, value in request.POST.items():
            if key.startswith('cantidad_'):
                prod_id_str = key.replace('cantidad_', '')
                try:
                    nueva_cant = int(value)
                    if prod_id_str in carrito:
                        producto = Producto.objects.filter(pk=prod_id_str, estado='activo').first()
                        if not producto or nueva_cant <= 0:
                            del carrito[prod_id_str]
                        elif nueva_cant > producto.stock:
                            carrito[prod_id_str]['cantidad'] = producto.stock
                            messages.warning(
                                request,
                                f'Cantidad ajustada al máximo disponible ({producto.stock}) para {producto.nombre}.'
                            )
                        else:
                            carrito[prod_id_str]['cantidad'] = nueva_cant
                except ValueError:
                    pass

        request.session['carrito'] = carrito
        request.session.modified = True
        messages.success(request, 'Carrito actualizado con éxito.')

    return redirect('tienda_carrito')


def eliminar_carrito(request, producto_id):
    """Eliminar un producto específico del carrito."""
    carrito = request.session.get('carrito', {})
    prod_id_str = str(producto_id)
    if prod_id_str in carrito:
        del carrito[prod_id_str]
        request.session['carrito'] = carrito
        request.session.modified = True
        messages.success(request, 'Producto eliminado del carrito.')
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
                    # Re-verificar y bloquear stock
                    for item in carrito_data['items']:
                        prod = Producto.objects.select_for_update().get(pk=item['producto'].pk)
                        if prod.stock < item['cantidad']:
                            raise ValueError(
                                f'Stock insuficiente para "{prod.nombre}". Disponible: {prod.stock}'
                            )

                    # Crear Pedido principal en Dashboard
                    pedido = Pedido.objects.create(
                        cliente=cliente,
                        fecha_pedido=timezone.now().date(),
                        estado='pendiente',
                        total=carrito_data['total_general'],
                        notas=f'Contacto: {telefono}\nEntrega: {direccion_envio}\nNotas: {notas}'.strip()
                    )

                    # Crear Detalles y descontar stock con movimiento
                    for item in carrito_data['items']:
                        prod = Producto.objects.get(pk=item['producto'].pk)
                        cant = item['cantidad']
                        stock_ant = prod.stock
                        stock_post = stock_ant - cant

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
    detalles = pedido.detalles.select_related('producto').all()

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
    detalles = pedido.detalles.select_related('producto').all()

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