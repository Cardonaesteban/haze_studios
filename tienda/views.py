from decimal import Decimal
import base64
import json
import logging
import re
import unicodedata
import uuid
try:
    import requests
except ImportError:
    requests = None
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from functools import wraps

from dashboard.models import (
    Cliente, Producto, Categoria, Disenador, Pedido, DetallePedido, MovimientoStock
)
from dashboard.emails import enviar_factura_pedido
from .pagos_paypal import crear_orden_paypal, capturar_orden_paypal
from django.db.models import Count, Q
from .models import (
    TokenRecuperacionCliente, Favorito,
    Personalizacion, PrendaComunidad, ComentarioComunidad, ReaccionComunidad,
    TIPOS_PRENDA_CHOICES, TALLAS_COMUNIDAD_CHOICES, COLORES_COMUNIDAD_CHOICES,
    ESTAMPADOS_OFICIALES_CHOICES, TIPOGRAFIAS_OFICIALES_CHOICES,
)
from .forms import (
    LoginClienteForm, RegistroClienteForm, PerfilClienteForm,
    CambiarPasswordClienteForm, SolicitarRecuperacionClienteForm,
    ConfirmarPasswordClienteForm, CheckoutForm,
    PersonalizacionForm, PrendaComunidadPublicarForm,
    PrendaComunidadEditarForm, ComentarioComunidadForm,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# DECORADORES Y UTILIDADES DE SESIÓN
# ──────────────────────────────────────────────

def cliente_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        cliente = get_cliente_actual(request)
        if not cliente:
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


def _extraer_producto_id(key, info):
    """Extrae el ID numérico del producto desde la clave o diccionario del carrito."""
    if isinstance(info, dict) and 'producto_id' in info:
        try:
            return int(info['producto_id'])
        except (ValueError, TypeError):
            pass
    str_key = str(key)
    if '_' in str_key:
        try:
            return int(str_key.split('_')[0])
        except ValueError:
            pass
    elif str_key.isdigit():
        return int(str_key)
    return None


def get_carrito_items(request):
    """Devuelve los items del carrito con los objetos Producto y totales, diferenciando por talla."""
    carrito = request.session.get('carrito', {})
    items = []
    total_general = Decimal('0')
    total_cantidad = 0

    if not carrito:
        return {'items': items, 'total_general': total_general, 'total_cantidad': total_cantidad}

    # Extraer los IDs únicos de producto compatibles con claves '1' y '1_s-oversize'
    productos_ids = {
        pid for pid in (
            _extraer_producto_id(key, info)
            for key, info in carrito.items()
        ) if pid is not None
    }

    productos = Producto.objects.filter(pk__in=productos_ids, estado='activo')
    productos_dict = {p.pk: p for p in productos}

    for item_key, info in list(carrito.items()):
        if not isinstance(info, dict):
            continue

        prod_id = _extraer_producto_id(item_key, info)
        if not prod_id:
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


def obtener_tasa_usd_cop():
    """
    Devuelve cuántos COP equivalen a 1 USD, usando caché de 24 horas
    para no agotar la cuota gratuita de ExchangeRate-API (1500 req/mes).
    """
    tasa = cache.get('tasa_usd_cop')
    if tasa is not None:
        return tasa

    if not settings.EXCHANGE_RATE_API_KEY or not requests:
        return None

    try:
        url = f'https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/USD'
        respuesta = requests.get(url, timeout=5)
        data = respuesta.json()
        if data.get('result') == 'success':
            tasa = data['conversion_rates']['COP']
            cache.set('tasa_usd_cop', tasa, 60 * 60 * 24)  # 24 horas
            return tasa
    except requests.RequestException:
        pass
    return None


def producto_detalle(request, pk):
    """Ficha de detalle de la prenda oversize, guía de medidas y botón de compra."""
    producto = get_object_or_404(Producto, pk=pk, estado='activo')
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria, estado='activo'
    ).exclude(pk=producto.pk)[:4]
    cliente = get_cliente_actual(request)

    es_favorito = False
    if cliente:
        es_favorito = Favorito.objects.filter(cliente=cliente, producto=producto).exists()

    tasa_usd_cop = obtener_tasa_usd_cop()
    precio_usd = None
    if tasa_usd_cop:
        precio_usd = round(producto.precio / Decimal(str(tasa_usd_cop)), 2)

    context = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
        'cliente': cliente,
        'es_favorito': es_favorito,
        'precio_usd': precio_usd,
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
        if isinstance(it, dict) and k != item_key and _extraer_producto_id(k, it) == producto.pk
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
    if cliente is None:
        return redirect('tienda_login')
    
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

                    metodo_pago_post = request.POST.get('metodo_pago', 'paypal')
                    metodo_pago_val = 'contra_entrega' if metodo_pago_post == 'contraentrega' else 'paypal'

                    # Crear Pedido principal en Dashboard
                    pedido = Pedido.objects.create(
                        cliente=cliente,
                        fecha_pedido=timezone.now().date(),
                        estado='pendiente_pago',
                        total=carrito_data['total_general'],
                        notas=notas_finales.strip(),
                        metodo_pago=metodo_pago_val
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
                    return redirect('tienda_confirmar_pago', pedido_id=pedido.pk)

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
def confirmar_pago(request, pedido_id):
    """
    Pantalla de confirmación de pago con coexistencia de métodos:
    Opción A: PayPal / Tarjeta Internacional (Smart Buttons SDK)
    Opción B: Pago Contra Entrega (Efectivo al recibir)
    """
    cliente = get_cliente_actual(request)
    if cliente is None:
        return redirect('tienda_login')

    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)

    if pedido.verificar_expiracion():
        messages.error(request, f'El tiempo límite de 15 minutos para confirmar el pedido #{pedido.pk} expiró.')
        return redirect('tienda_carrito')

    if pedido.estado != 'pendiente_pago':
        return redirect('tienda_pedido_confirmado', pedido_id=pedido.pk)

    if request.method == 'POST':
        metodo = request.POST.get('metodo')
        resultado = request.POST.get('resultado')

        if metodo == 'contra_entrega' or resultado == 'aprobado':
            with transaction.atomic():
                pedido_lock = Pedido.objects.select_for_update().get(pk=pedido.pk, cliente=cliente)
                if pedido_lock.verificar_expiracion():
                    messages.error(request, f'El tiempo límite de espera para el pedido #{pedido.pk} expiró.')
                    return redirect('tienda_carrito')

                if pedido_lock.estado != 'pendiente_pago':
                    return redirect('tienda_pedido_confirmado', pedido_id=pedido.pk)

                pedido_lock.estado = 'pendiente'
                pedido_lock.metodo_pago = 'contra_entrega'
                pedido_lock.fecha_pago = timezone.now()
                pedido_lock.save(update_fields=['estado', 'metodo_pago', 'fecha_pago'])

                enviar_factura_pedido(pedido_lock)

            messages.success(request, f'¡Pedido #{pedido.pk} confirmado exitosamente con pago contra entrega!')
            return redirect('tienda_pedido_confirmado', pedido_id=pedido.pk)
        else:
            with transaction.atomic():
                pedido_lock = Pedido.objects.select_for_update().get(pk=pedido.pk, cliente=cliente)
                pedido_lock.cancelar(motivo=f'Cancelación del pedido #{pedido.pk} por el cliente en confirmación')
            messages.info(request, f'Pedido #{pedido.pk} cancelado. Los productos regresaron a tu disponibilidad.')
            return redirect('tienda_carrito')

    if request.GET.get('cancel'):
        messages.info(request, 'El pago en PayPal no se completó. Tus prendas siguen apartadas, puedes reintentar o elegir Pago Contra Entrega.')

    segundos_restantes = int((pedido.fecha_creacion + Pedido.TIEMPO_LIMITE_PAGO - timezone.now()).total_seconds())
    detalles = obtener_detalles_con_talla(pedido)

    tasa = obtener_tasa_usd_cop() or Decimal('4000.00')
    monto_usd = round(Decimal(str(pedido.total)) / Decimal(str(tasa)), 2)
    if monto_usd <= Decimal('0.01'):
        monto_usd = Decimal('1.00')

    context = {
        'pedido': pedido,
        'cliente': cliente,
        'detalles': detalles,
        'segundos_restantes': max(0, segundos_restantes),
        'paypal_client_id': getattr(settings, 'PAYPAL_CLIENT_ID', '').strip(),
        'monto_usd': monto_usd,
        'tasa_usd_cop': tasa,
    }
    return render(request, 'tienda/confirmar_pago.html', context)


@cliente_required
def paypal_crear_orden(request, pedido_id):
    """Genera la orden en PayPal Orders v2 vía AJAX para los Smart Buttons."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    cliente = get_cliente_actual(request)
    if not cliente:
        return JsonResponse({'error': 'Debes iniciar sesión para continuar'}, status=401)

    try:
        with transaction.atomic():
            pedido = Pedido.objects.select_for_update().get(pk=pedido_id, cliente=cliente)

            if pedido.verificar_expiracion():
                return JsonResponse({'error': 'El tiempo para pagar este pedido ha expirado (15 min).'}, status=400)

            if pedido.estado != 'pendiente_pago':
                return JsonResponse({'error': 'El pedido no se encuentra en estado pendiente de pago.'}, status=400)

            tasa = obtener_tasa_usd_cop() or Decimal('4000.00')
            monto_usd = round(Decimal(str(pedido.total)) / Decimal(str(tasa)), 2)
            if monto_usd <= Decimal('0.01'):
                monto_usd = Decimal('1.00')

            return_url = request.build_absolute_uri(reverse('tienda_paypal_retorno', args=[pedido.pk]))
            cancel_url = request.build_absolute_uri(reverse('tienda_confirmar_pago', args=[pedido.pk])) + '?cancel=1'

            datos_orden = crear_orden_paypal(pedido, monto_usd, return_url=return_url, cancel_url=cancel_url)
            order_id = datos_orden['order_id']
            approve_url = datos_orden['approve_url']

            pedido.referencia_pago = order_id
            pedido.monto_usd = monto_usd
            pedido.save(update_fields=['referencia_pago', 'monto_usd'])

            return JsonResponse({'id': order_id, 'approve_url': approve_url})
    except Pedido.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error al crear orden en PayPal para pedido #{pedido_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@cliente_required
def paypal_capturar_orden(request, pedido_id):
    """Captura los fondos autorizados por el cliente en PayPal de forma atómica y confirma la compra."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    cliente = get_cliente_actual(request)
    if not cliente:
        return JsonResponse({'error': 'Debes iniciar sesión para continuar'}, status=401)

    try:
        data = {}
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                pass
        order_id = data.get('orderID') or request.POST.get('orderID')
        if not order_id:
            return JsonResponse({'error': 'Identificador de orden de PayPal no suministrado.'}, status=400)

        with transaction.atomic():
            pedido = Pedido.objects.select_for_update().get(pk=pedido_id, cliente=cliente)

            if pedido.verificar_expiracion():
                return JsonResponse({'error': 'El tiempo para pagar este pedido ha expirado.'}, status=400)

            if pedido.estado in ('procesando', 'enviado', 'entregado'):
                # Ya fue capturado previamente (idempotencia)
                return JsonResponse({
                    'status': 'COMPLETED',
                    'redirect_url': reverse('tienda_pedido_confirmado', args=[pedido.pk])
                })

            resultado = capturar_orden_paypal(order_id)

            if resultado.get('success'):
                pedido.estado = 'procesando'
                pedido.metodo_pago = 'paypal'
                pedido.transaccion_id = resultado.get('capture_id') or order_id
                pedido.fecha_pago = timezone.now()
                if resultado.get('monto_usd'):
                    try:
                        pedido.monto_usd = Decimal(str(resultado.get('monto_usd')))
                    except Exception:
                        pass
                pedido.save(update_fields=['estado', 'metodo_pago', 'transaccion_id', 'fecha_pago', 'monto_usd'])

                # Enviar factura por correo electrónico
                enviar_factura_pedido(pedido)

                messages.success(request, f'¡Pago aprobado con éxito! Tu pedido #{pedido.pk} está en proceso de despacho.')
                return JsonResponse({
                    'status': 'COMPLETED',
                    'redirect_url': reverse('tienda_pedido_confirmado', args=[pedido.pk])
                })
            else:
                error_msg = resultado.get('error', 'La transacción no pudo ser completada por PayPal.')
                return JsonResponse({'status': 'FAILED', 'error': error_msg}, status=400)

    except Pedido.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error al capturar orden PayPal para pedido #{pedido_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@cliente_required
def paypal_retorno(request, pedido_id):
    """
    Ruta a la que PayPal redirige al cliente tras autorizar el pago en la misma ventana (sin popups).
    Captura los fondos, actualiza el pedido a 'procesando', despacha la factura y redirige a confirmación.
    """
    cliente = get_cliente_actual(request)
    if not cliente:
        return redirect('tienda_login')

    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)
    order_id = request.GET.get('token') or pedido.referencia_pago

    if not order_id:
        messages.error(request, 'No se recibió la confirmación de la orden de PayPal.')
        return redirect('tienda_confirmar_pago', pedido_id=pedido.pk)

    try:
        with transaction.atomic():
            pedido_lock = Pedido.objects.select_for_update().get(pk=pedido.pk, cliente=cliente)

            if pedido_lock.verificar_expiracion():
                messages.error(request, 'El tiempo límite de 15 minutos para tu pedido expiró.')
                return redirect('tienda_carrito')

            if pedido_lock.estado in ('procesando', 'enviado', 'entregado'):
                return redirect('tienda_pedido_confirmado', pedido_id=pedido.pk)

            resultado = capturar_orden_paypal(order_id)

            if resultado.get('success'):
                pedido_lock.estado = 'procesando'
                pedido_lock.metodo_pago = 'paypal'
                pedido_lock.transaccion_id = resultado.get('capture_id') or order_id
                pedido_lock.fecha_pago = timezone.now()
                if resultado.get('monto_usd'):
                    try:
                        pedido_lock.monto_usd = Decimal(str(resultado.get('monto_usd')))
                    except Exception:
                        pass
                pedido_lock.save(update_fields=['estado', 'metodo_pago', 'transaccion_id', 'fecha_pago', 'monto_usd'])

                enviar_factura_pedido(pedido_lock)

                messages.success(request, f'¡Pago aprobado con éxito! Tu pedido #{pedido.pk} ha sido registrado.')
                return redirect('tienda_pedido_confirmado', pedido_id=pedido.pk)
            else:
                error_msg = resultado.get('error', 'No fue posible completar el cobro en PayPal.')
                messages.error(request, f'El pago no se completó: {error_msg}. Puedes intentar nuevamente o seleccionar Pago Contra Entrega.')
                return redirect('tienda_confirmar_pago', pedido_id=pedido.pk)

    except Exception as e:
        logger.error(f"Error en retorno de PayPal para pedido #{pedido.pk}: {e}")
        messages.error(request, 'Ocurrió un error al procesar el retorno de PayPal. Intenta de nuevo.')
        return redirect('tienda_confirmar_pago', pedido_id=pedido.pk)

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
    cliente = get_cliente_actual(request)
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-id').prefetch_related('detalles__producto')
    for p in pedidos:
        p.verificar_expiracion()
    context = {'pedidos': pedidos, 'cliente': cliente}
    return render(request, 'tienda/mis_pedidos.html', context)


@cliente_required
def pedido_detalle(request, pedido_id):
    cliente = get_cliente_actual(request)
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)
    pedido.verificar_expiracion()
    detalles = obtener_detalles_con_talla(pedido)
    context = {'pedido': pedido, 'detalles': detalles, 'cliente': cliente}
    return render(request, 'tienda/pedido_detalle.html', context)

@cliente_required
def pedido_cancelar(request, pedido_id):
    """Permite al cliente cancelar su pedido si el estado lo permite"""
    cliente = get_cliente_actual(request)
    if cliente is None:
        return redirect('tienda_login')

    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=cliente)

    if pedido.cancelar():
        messages.success(request, f'Pedido #{pedido.pk} cancelado correctamente.')
    else:
        messages.error(request, f'No se puede cancelar el pedido #{pedido.pk}. Estado actual: {pedido.estado}.')

    return redirect('tienda_pedido_detalle', pedido_id=pedido.pk)
    


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
                    request.session.cycle_key()
                    request.session['cliente_id'] = cliente.pk
                    request.session['cliente_nombre'] = cliente.nombre
                    request.session['cliente_correo'] = cliente.correo
                    messages.success(request, f'¡Bienvenido de nuevo, {cliente.nombre}!')
                    if next_url and next_url != 'tienda_inicio' and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
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

            # Iniciar sesión automáticamente de forma segura
            request.session.cycle_key()
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
    if cliente is None:
        return redirect('tienda_login')

    if request.method == 'POST':
        form = PerfilClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            request.session['cliente_nombre'] = cliente.nombre
            messages.success(request, 'Tus datos de perfil han sido actualizados con éxito.')
            return redirect('tienda_perfil')
    else:
        form = PerfilClienteForm(instance=cliente)

    mis_personalizaciones = Personalizacion.objects.filter(
        cliente=cliente
    ).select_related('producto__categoria', 'publicacion_comunidad').order_by('-fecha_creacion')[:6]
    mis_publicaciones = PrendaComunidad.objects.filter(
        autor=cliente
    ).select_related('personalizacion', 'producto_base').annotate(
        total_reacciones=Count('reacciones', distinct=True),
        total_comentarios=Count('comentarios', distinct=True),
    ).order_by('-fecha_publicacion')[:6]

    context = {
        'form': form,
        'cliente': cliente,
        'mis_personalizaciones': mis_personalizaciones,
        'mis_publicaciones': mis_publicaciones,
        'total_personalizaciones': Personalizacion.objects.filter(cliente=cliente).count(),
        'total_publicaciones': PrendaComunidad.objects.filter(autor=cliente).count(),
    }
    return render(request, 'tienda/perfil.html', context)


@cliente_required
def cambiar_password_cliente(request):
    """Cambiar contraseña desde el perfil de usuario."""
    cliente = get_cliente_actual(request)
    if cliente is None:
        return redirect('tienda_login')

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

# ──────────────────────────────────────────────
# FAVORITOS API (SIN RECARGAR PÁGINA) Y LISTA DE FAVORITOS
# ──────────────────────────────────────────────

@cliente_required
def favoritos_toggle_api(request, producto_id):
    """
    Vista API que recibe peticiones POST desde Alpine.js para agregar/quitar favoritos
    SIN recargar la página. Devuelve JSON con el resultado.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        import json
        cliente = get_cliente_actual(request)
        if cliente is None:
            return JsonResponse({'success': False, 'error': 'Cliente no autenticado'}, status=401)
        
        producto = get_object_or_404(Producto, pk=producto_id, estado='activo')
        
        data = json.loads(request.body)
        accion = data.get('accion')
        
        if accion == 'agregar':
            favorito, creado = Favorito.objects.get_or_create(cliente=cliente, producto=producto)
            es_favorito = True
            mensaje = f'"{producto.nombre}" agregado a favoritos'
        elif accion == 'quitar':
            Favorito.objects.filter(cliente=cliente, producto=producto).delete()
            es_favorito = False
            mensaje = f'"{producto.nombre}" quitado de favoritos'
        else:
            return JsonResponse({'success': False, 'error': 'Acción inválida'}, status=400)
        
        return JsonResponse({
            'success': True,
            'es_favorito': es_favorito,
            'message': mensaje
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cliente_required
def favoritos_comunidad_toggle_api(request, prenda_id):
    """
    Vista API que recibe peticiones POST desde Alpine.js para agregar/quitar
    prendas personalizadas de la comunidad en favoritos SIN recargar la página.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        import json
        cliente = get_cliente_actual(request)
        if cliente is None:
            return JsonResponse({'success': False, 'error': 'Cliente no autenticado'}, status=401)

        prenda = get_object_or_404(PrendaComunidad, pk=prenda_id, estado='activo')

        data = json.loads(request.body) if request.body else {}
        accion = data.get('accion')

        if accion == 'agregar':
            favorito, creado = Favorito.objects.get_or_create(cliente=cliente, prenda_comunidad=prenda)
            es_favorito = True
            mensaje = f'"{prenda.nombre}" agregada a favoritos'
        elif accion == 'quitar':
            Favorito.objects.filter(cliente=cliente, prenda_comunidad=prenda).delete()
            es_favorito = False
            mensaje = f'"{prenda.nombre}" quitada de favoritos'
        else:
            fav = Favorito.objects.filter(cliente=cliente, prenda_comunidad=prenda).first()
            if fav:
                fav.delete()
                es_favorito = False
                mensaje = f'"{prenda.nombre}" quitada de favoritos'
            else:
                Favorito.objects.create(cliente=cliente, prenda_comunidad=prenda)
                es_favorito = True
                mensaje = f'"{prenda.nombre}" agregada a favoritos'

        return JsonResponse({
            'success': True,
            'es_favorito': es_favorito,
            'message': mensaje
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except PrendaComunidad.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prenda no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@cliente_required
def mis_favoritos(request):
    """
    Muestra los favoritos del cliente divididos claramente en dos categorías:
    1. Prendas normales del catálogo.
    2. Prendas personalizadas creadas por la comunidad.
    """
    cliente = get_cliente_actual(request)

    favoritos_normales = Favorito.objects.filter(
        cliente=cliente, producto__isnull=False
    ).select_related('producto', 'producto__categoria')

    favoritos_comunidad = Favorito.objects.filter(
        cliente=cliente, prenda_comunidad__isnull=False
    ).select_related('prenda_comunidad', 'prenda_comunidad__autor', 'prenda_comunidad__personalizacion')

    favoritos_ids = list(favoritos_normales.values_list('producto_id', flat=True))
    favoritos_comunidad_ids = list(favoritos_comunidad.values_list('prenda_comunidad_id', flat=True))

    tab = request.GET.get('tab', 'todas')

    context = {
        'cliente': cliente,
        'favoritos_normales': favoritos_normales,
        'favoritos_comunidad': favoritos_comunidad,
        'total_normales': favoritos_normales.count(),
        'total_comunidad': favoritos_comunidad.count(),
        'total_favoritos': favoritos_normales.count() + favoritos_comunidad.count(),
        'favoritos_ids': favoritos_ids,
        'favoritos_comunidad_ids': favoritos_comunidad_ids,
        'tab_activa': tab,
    }
    return render(request, 'tienda/mis_favoritos.html', context)


# ──────────────────────────────────────────────
# PERSONALIZACIÓN DE PRODUCTOS
# ──────────────────────────────────────────────

@cliente_required
def personalizar_producto(request):
    """
    Permite al usuario realizar personalizaciones sobre productos disponibles del catálogo.
    No permite solicitar personalizaciones para productos inactivos o agotados.
    """
    cliente = get_cliente_actual(request)
    if cliente is None:
        return redirect('tienda_login')

    producto_preseleccionado = None
    prod_id_param = request.GET.get('producto')
    if prod_id_param and prod_id_param.isdigit():
        prod_obj = Producto.objects.filter(pk=int(prod_id_param)).first()
        if not prod_obj or prod_obj.estado != 'activo' or prod_obj.stock <= 0:
            messages.error(
                request,
                'No se permite solicitar personalizaciones para productos no disponibles o agotados.'
            )
            return redirect('tienda_productos')
        producto_preseleccionado = prod_obj

    productos_catalogo = Producto.objects.all().select_related('categoria').order_by(
        '-estado', '-stock', 'nombre'
    )

    if not producto_preseleccionado:
        producto_preseleccionado = Producto.objects.filter(
            estado='activo', stock__gt=0
        ).order_by('nombre').first()

    productos_info = {}
    for p in productos_catalogo:
        disponible = (p.estado == 'activo' and p.stock > 0)
        productos_info[str(p.pk)] = {
            'id': p.pk,
            'nombre': p.nombre,
            'categoria': p.categoria.nombre if p.categoria else 'Oversize',
            'imagen_url': p.get_imagen_url(),
            'stock': p.stock,
            'estado': p.estado,
            'disponible': disponible,
        }

    if request.method == 'POST':
        form = PersonalizacionForm(request.POST)
        if form.is_valid():
            personalizacion = form.save(commit=False)
            personalizacion.cliente = cliente
            personalizacion.estado = 'en_proceso'

            # Guardar la imagen generada desde la vista previa en fondo blanco si fue enviada
            img_b64 = (request.POST.get('imagen_preview_b64') or '').strip()
            if img_b64.startswith('data:image/png;base64,'):
                try:
                    raw_b64 = img_b64.split(',', 1)[1]
                    img_bytes = base64.b64decode(raw_b64)
                    filename = f"custom_{cliente.pk}_{uuid.uuid4().hex[:8]}.png"
                    personalizacion.imagen_preview.save(filename, ContentFile(img_bytes), save=False)
                except Exception as e:
                    logger.warning(f"No se pudo guardar imagen_preview_b64: {e}")

            personalizacion.save()

            accion = request.POST.get('accion', 'guardar')
            if accion == 'guardar_y_publicar':
                messages.success(
                    request,
                    f'Personalización "{personalizacion.nombre_personalizacion}" creada y aplicada. Completa la publicación en la comunidad.'
                )
                return redirect(f"{reverse('tienda_comunidad_publicar')}?personalizacion={personalizacion.pk}")

            messages.success(
                request,
                f'Tu personalización "{personalizacion.nombre_personalizacion}" ha sido aplicada y guardada en proceso.'
            )
            return redirect('tienda_mis_personalizaciones')
        else:
            messages.warning(request, 'Por favor revisa los campos del estudio de personalización.')
    else:
        initial = {}
        if producto_preseleccionado:
            initial['producto'] = producto_preseleccionado.pk
            initial['nombre_personalizacion'] = f"{producto_preseleccionado.nombre} Custom"
        form = PersonalizacionForm(initial=initial)

    context = {
        'form': form,
        'cliente': cliente,
        'producto_preseleccionado': producto_preseleccionado,
        'productos_disponibles': productos_catalogo,
        'productos_json': productos_info,
        'estampados_choices': ESTAMPADOS_OFICIALES_CHOICES,
        'tipografias_choices': TIPOGRAFIAS_OFICIALES_CHOICES,
    }
    return render(request, 'tienda/personalizar/form.html', context)


@cliente_required
def mis_personalizaciones(request):
    """
    Lista las personalizaciones del usuario (estados 'en_proceso' y 'publicada')
    y sus publicaciones en la comunidad.
    """
    cliente = get_cliente_actual(request)
    if cliente is None:
        return redirect('tienda_login')

    personalizaciones = Personalizacion.objects.filter(
        cliente=cliente
    ).select_related('producto', 'publicacion_comunidad').order_by('-fecha_creacion')

    publicaciones = PrendaComunidad.objects.filter(
        autor=cliente
    ).select_related('personalizacion', 'producto_base').annotate(
        total_reacciones=Count('reacciones', distinct=True),
        total_comentarios=Count('comentarios', distinct=True),
    ).order_by('-fecha_publicacion')

    context = {
        'cliente': cliente,
        'personalizaciones': personalizaciones,
        'publicaciones': publicaciones,
    }
    return render(request, 'tienda/personalizar/mis_personalizaciones.html', context)


@cliente_required
def personalizacion_eliminar(request, pk):
    """Elimina una personalización perteneciente al usuario actual."""
    if request.method != 'POST':
        return redirect('tienda_mis_personalizaciones')

    cliente = get_cliente_actual(request)
    personalizacion = get_object_or_404(Personalizacion, pk=pk, cliente=cliente)
    nombre = personalizacion.nombre_personalizacion
    personalizacion.delete()
    messages.success(request, f'La personalización "{nombre}" fue eliminada correctamente.')
    return redirect('tienda_mis_personalizaciones')


# ──────────────────────────────────────────────
# COMUNIDAD DE PRENDAS PERSONALIZADAS
# ──────────────────────────────────────────────

def comunidad_lista(request):
    """
    Consulta y búsqueda de prendas publicadas en la comunidad.
    Muestra únicamente las prendas activas y permite combinar filtros por
    nombre, color, talla, autor, estampado y tipografía.
    """
    cliente = get_cliente_actual(request)

    nombre_q = request.GET.get('nombre', '').strip()
    color_q = request.GET.get('color', '').strip()
    talla_q = request.GET.get('talla', '').strip()
    autor_q = request.GET.get('autor', '').strip()
    estampado_q = request.GET.get('estampado', '').strip()
    tipografia_q = request.GET.get('tipografia', '').strip()
    orden = request.GET.get('orden', 'recientes').strip()

    prendas_qs = PrendaComunidad.objects.filter(
        estado='activo'
    ).select_related(
        'autor', 'producto_base', 'personalizacion', 'personalizacion__producto'
    ).annotate(
        total_reacciones=Count('reacciones', distinct=True),
        total_comentarios=Count('comentarios', distinct=True),
    )

    if nombre_q:
        prendas_qs = prendas_qs.filter(nombre__icontains=nombre_q)
    if color_q:
        prendas_qs = prendas_qs.filter(color__iexact=color_q)
    if talla_q:
        prendas_qs = prendas_qs.filter(talla__iexact=talla_q)
    if autor_q:
        prendas_qs = prendas_qs.filter(
            Q(autor__nombre__icontains=autor_q) | Q(autor__apellido__icontains=autor_q)
        )
    if estampado_q:
        prendas_qs = prendas_qs.filter(estampado__iexact=estampado_q)
    if tipografia_q:
        prendas_qs = prendas_qs.filter(tipografia__iexact=tipografia_q)

    if orden == 'populares':
        prendas_qs = prendas_qs.order_by('-total_reacciones', '-fecha_publicacion')
    else:
        prendas_qs = prendas_qs.order_by('-fecha_publicacion')

    reacciones_cliente_ids = set()
    favoritos_comunidad_ids = set()
    if cliente:
        reacciones_cliente_ids = set(
            ReaccionComunidad.objects.filter(cliente=cliente).values_list('prenda_id', flat=True)
        )
        favoritos_comunidad_ids = set(
            Favorito.objects.filter(cliente=cliente, prenda_comunidad__isnull=False).values_list('prenda_comunidad_id', flat=True)
        )

    hay_filtros = any([nombre_q, color_q, talla_q, autor_q, estampado_q, tipografia_q])

    context = {
        'cliente': cliente,
        'prendas': prendas_qs,
        'reacciones_cliente_ids': reacciones_cliente_ids,
        'favoritos_comunidad_ids': favoritos_comunidad_ids,
        'nombre_q': nombre_q,
        'color_q': color_q,
        'talla_q': talla_q,
        'autor_q': autor_q,
        'estampado_q': estampado_q,
        'tipografia_q': tipografia_q,
        'orden': orden,
        'hay_filtros': hay_filtros,
        'colores_choices': COLORES_COMUNIDAD_CHOICES,
        'tallas_choices': TALLAS_COMUNIDAD_CHOICES,
        'estampados_choices': ESTAMPADOS_OFICIALES_CHOICES,
        'tipografias_choices': TIPOGRAFIAS_OFICIALES_CHOICES,
        'total_activas_comunidad': PrendaComunidad.objects.filter(estado='activo').count(),
    }
    return render(request, 'tienda/comunidad/lista.html', context)


@cliente_required
def comunidad_publicar(request):
    """
    Permite al usuario publicar una prenda personalizada en la comunidad.
    Al seleccionar una personalización se autocompletan sus especificaciones.
    No permite duplicados activos con las mismas especificaciones para el mismo usuario.
    """
    cliente = get_cliente_actual(request)
    if cliente is None:
        return redirect('tienda_login')

    personalizaciones_usuario = Personalizacion.objects.filter(
        cliente=cliente
    ).select_related('producto', 'publicacion_comunidad').order_by('-fecha_creacion')

    if not personalizaciones_usuario.exists():
        messages.info(
            request,
            'Para publicar en la comunidad primero debes crear una personalización en el Estudio Haze.'
        )
        return redirect('tienda_personalizar')

    # Diccionario JSON para autocompletado instantáneo en el formulario
    pers_data = {}
    for p in personalizaciones_usuario:
        ya_publicada = hasattr(p, 'publicacion_comunidad') and p.publicacion_comunidad is not None
        pers_data[str(p.pk)] = {
            'id': p.pk,
            'nombre': p.nombre_personalizacion,
            'descripcion': p.detalle,
            'tipo': p.tipo,
            'color': p.color,
            'talla': p.talla,
            'estampado': p.estampado,
            'tipografia': p.tipografia,
            'producto_nombre': p.producto.nombre if p.producto else 'Prenda Haze',
            'imagen_url': p.get_imagen_url(),
            'estado': p.get_estado_display(),
            'ya_publicada': ya_publicada,
        }

    pers_preseleccionada = None
    pers_id_param = request.GET.get('personalizacion')
    if pers_id_param and pers_id_param.isdigit():
        pers_preseleccionada = personalizaciones_usuario.filter(pk=int(pers_id_param)).first()

    if not pers_preseleccionada:
        # Seleccionar por defecto la más reciente en proceso
        pers_preseleccionada = personalizaciones_usuario.filter(estado='en_proceso').first() or personalizaciones_usuario.first()

    if request.method == 'POST':
        form = PrendaComunidadPublicarForm(request.POST, cliente=cliente)
        if form.is_valid():
            pers = form.cleaned_data['personalizacion']
            prenda = form.save(commit=False)
            prenda.autor = cliente
            prenda.personalizacion = pers
            prenda.producto_base = pers.producto
            if pers.imagen_preview:
                prenda.imagen = pers.imagen_preview
            prenda.estado = 'activo'
            prenda.save()

            pers.estado = 'publicada'
            pers.save(update_fields=['estado'])

            messages.success(
                request,
                f'¡Tu prenda "{prenda.nombre}" ha sido publicada en la Comunidad Haze Studios!'
            )
            return redirect('tienda_comunidad_detalle', pk=prenda.pk)
        else:
            messages.error(request, 'No se pudo publicar la prenda. Revisa las indicaciones del formulario.')
    else:
        initial = {}
        if pers_preseleccionada:
            initial = {
                'personalizacion': pers_preseleccionada.pk,
                'nombre': pers_preseleccionada.nombre_personalizacion,
                'descripcion': pers_preseleccionada.detalle,
                'color': pers_preseleccionada.color,
                'talla': pers_preseleccionada.talla,
                'estampado': pers_preseleccionada.estampado,
                'tipografia': pers_preseleccionada.tipografia,
            }
        form = PrendaComunidadPublicarForm(initial=initial, cliente=cliente)

    context = {
        'form': form,
        'cliente': cliente,
        'personalizaciones_usuario': personalizaciones_usuario,
        'personalizaciones_json': pers_data,
        'pers_inicial_id': str(pers_preseleccionada.pk) if pers_preseleccionada else '',
    }
    return render(request, 'tienda/comunidad/publicar.html', context)


def comunidad_detalle(request, pk):
    """
    Vista de detalle de una prenda publicada en la comunidad.
    Muestra especificaciones completas, reacciones y comentarios.
    """
    cliente = get_cliente_actual(request)
    prenda = get_object_or_404(
        PrendaComunidad.objects.select_related(
            'autor', 'producto_base', 'personalizacion', 'personalizacion__producto'
        ),
        pk=pk
    )

    es_autor = bool(cliente and prenda.autor_id == cliente.pk)

    if prenda.estado != 'activo' and not es_autor:
        messages.warning(
            request,
            f'Esta publicación no se encuentra disponible porque está inactiva.{(" Motivo: " + prenda.motivo_inactivacion) if prenda.motivo_inactivacion else ""}'
        )
        return redirect('tienda_comunidad_lista')

    comentarios = prenda.comentarios.select_related('autor').order_by('fecha_publicacion')
    total_reacciones = prenda.reacciones.count()
    usuario_reacciono = False
    es_favorito = False
    if cliente:
        usuario_reacciono = ReaccionComunidad.objects.filter(prenda=prenda, cliente=cliente).exists()
        es_favorito = Favorito.objects.filter(prenda_comunidad=prenda, cliente=cliente).exists()

    comentario_form = ComentarioComunidadForm()

    context = {
        'cliente': cliente,
        'prenda': prenda,
        'es_autor': es_autor,
        'comentarios': comentarios,
        'total_reacciones': total_reacciones,
        'usuario_reacciono': usuario_reacciono,
        'es_favorito': es_favorito,
        'comentario_form': comentario_form,
    }
    return render(request, 'tienda/comunidad/detalle.html', context)


@cliente_required
def comunidad_editar(request, pk):
    """
    Permite únicamente al autor de la prenda publicada modificar su información y estado (activo / inactivo).
    """
    cliente = get_cliente_actual(request)
    prenda = get_object_or_404(PrendaComunidad, pk=pk)

    if prenda.autor_id != cliente.pk:
        messages.error(request, 'Solo el autor de la prenda puede editar esta publicación.')
        return redirect('tienda_comunidad_detalle', pk=prenda.pk)

    if request.method == 'POST':
        form = PrendaComunidadEditarForm(request.POST, instance=prenda)
        if form.is_valid():
            prenda_editada = form.save()
            # Si tiene personalización vinculada, sincronizar campos básicos
            if prenda_editada.personalizacion:
                pers = prenda_editada.personalizacion
                pers.nombre_personalizacion = prenda_editada.nombre
                pers.color = prenda_editada.color
                pers.talla = prenda_editada.talla
                pers.estampado = prenda_editada.estampado
                pers.tipografia = prenda_editada.tipografia
                pers.detalle = prenda_editada.descripcion
                pers.estado = prenda_editada.estado
                pers.save()
            messages.success(request, f'La publicación "{prenda_editada.nombre}" fue actualizada correctamente.')
            return redirect('tienda_comunidad_detalle', pk=prenda.pk)
        else:
            messages.warning(request, 'Por favor revisa los errores en el formulario.')
    else:
        form = PrendaComunidadEditarForm(instance=prenda)

    context = {
        'form': form,
        'prenda': prenda,
        'cliente': cliente,
    }
    return render(request, 'tienda/comunidad/editar.html', context)


@cliente_required
def comunidad_eliminar(request, pk):
    """
    Permite únicamente al autor eliminar su prenda publicada previa confirmación.
    La acción no se puede deshacer.
    """
    if request.method != 'POST':
        return redirect('tienda_comunidad_detalle', pk=pk)

    cliente = get_cliente_actual(request)
    prenda = get_object_or_404(PrendaComunidad, pk=pk)

    if prenda.autor_id != cliente.pk:
        messages.error(request, 'Solo el autor de la prenda puede eliminar esta publicación.')
        return redirect('tienda_comunidad_detalle', pk=prenda.pk)

    nombre = prenda.nombre
    if prenda.personalizacion:
        pers = prenda.personalizacion
        pers.estado = 'en_proceso'
        pers.save(update_fields=['estado'])

    prenda.delete()
    messages.success(request, f'La publicación "{nombre}" fue eliminada permanentemente de la comunidad.')
    return redirect('tienda_comunidad_lista')


@cliente_required
def comunidad_reaccionar_api(request, pk):
    """
    Registra o retira la reacción del usuario en una prenda publicada.
    Cada usuario solo puede reaccionar una vez por prenda y puede retirarla si lo desea.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    cliente = get_cliente_actual(request)
    if cliente is None:
        return JsonResponse({'success': False, 'error': 'Debes iniciar sesión'}, status=401)

    prenda = get_object_or_404(PrendaComunidad, pk=pk, estado='activo')
    reaccion, creada = ReaccionComunidad.objects.get_or_create(prenda=prenda, cliente=cliente)

    if not creada:
        reaccion.delete()
        reaccionado = False
    else:
        reaccionado = True

    total = prenda.reacciones.count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'reaccionado': reaccionado,
            'total': total,
        })

    return redirect(request.META.get('HTTP_REFERER') or reverse('tienda_comunidad_detalle', args=[prenda.pk]))


@cliente_required
def comunidad_comentar(request, pk):
    """
    Permite a un usuario con sesión iniciada comentar una prenda publicada en la comunidad.
    """
    if request.method != 'POST':
        return redirect('tienda_comunidad_detalle', pk=pk)

    cliente = get_cliente_actual(request)
    prenda = get_object_or_404(PrendaComunidad, pk=pk, estado='activo')

    form = ComentarioComunidadForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.prenda = prenda
        comentario.autor = cliente
        comentario.save()
        messages.success(request, 'Tu comentario ha sido publicado.')
    else:
        messages.error(request, 'No se pudo publicar el comentario. Verifica que no esté vacío.')

    return redirect(f"{reverse('tienda_comunidad_detalle', args=[prenda.pk])}#comentarios")


@cliente_required
def comunidad_comentario_editar(request, comentario_id):
    """
    Permite al usuario editar únicamente su propio comentario.
    """
    if request.method != 'POST':
        return redirect('tienda_comunidad_lista')

    cliente = get_cliente_actual(request)
    comentario = get_object_or_404(ComentarioComunidad, pk=comentario_id)

    if comentario.autor_id != cliente.pk:
        messages.error(request, 'Solo puedes editar tus propios comentarios.')
        return redirect('tienda_comunidad_detalle', pk=comentario.prenda_id)

    nuevo_contenido = (request.POST.get('contenido') or '').strip()
    if not nuevo_contenido:
        messages.error(request, 'El comentario no puede quedar vacío.')
    elif len(nuevo_contenido) > 400:
        messages.error(request, 'El comentario no puede superar los 400 caracteres.')
    else:
        comentario.contenido = nuevo_contenido
        comentario.editado = True
        comentario.save(update_fields=['contenido', 'editado', 'fecha_edicion'])
        messages.success(request, 'Tu comentario fue actualizado.')

    return redirect(f"{reverse('tienda_comunidad_detalle', args=[comentario.prenda_id])}#comentario-{comentario.pk}")


@cliente_required
def comunidad_comentario_eliminar(request, comentario_id):
    """
    Permite al usuario eliminar únicamente su propio comentario.
    """
    if request.method != 'POST':
        return redirect('tienda_comunidad_lista')

    cliente = get_cliente_actual(request)
    comentario = get_object_or_404(ComentarioComunidad, pk=comentario_id)
    prenda_id = comentario.prenda_id

    if comentario.autor_id != cliente.pk:
        messages.error(request, 'Solo puedes eliminar tus propios comentarios.')
        return redirect('tienda_comunidad_detalle', pk=prenda_id)

    comentario.delete()
    messages.info(request, 'Tu comentario fue eliminado.')
    return redirect(f"{reverse('tienda_comunidad_detalle', args=[prenda_id])}#comentarios")
