from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from dashboard.models import Cliente
from .forms import LoginClienteForm
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.db import transaction
# from django.utils import timezone
# from .models import( 
#    Cliente, Producto, Categoria, Pedido, DetallePedido, Disenadore,
#     Comunidad, ReporteProducto, Favoritos, ListaDeseados,
#     Cupon, PerfilUsuario, Comentarios,
#     ComparacionProducto, Carrito, ItemCarrito, Venta,
#     DetalleVenta, FAQ
# )

# ──────────────────────────────────────────────
# LOGIN USUARIOS
# ──────────────────────────────────────────────

def login_cliente(request):
    form = LoginClienteForm(request.POST or None)
    error = None

    if request.method == 'POST' and form.is_valid():
        correo = form.cleaned_data['correo']
        contraseña = form.cleaned_data['contraseña']

        try:
            cliente = Cliente.objects.get(correo=correo)
        except Cliente.DoesNotExist:
            error = 'Correo o contraseña incorrectos.'
        else:
            if cliente.estado == 'inactivo':
                error = 'Tu cuenta está inactiva.'
            elif check_password(contraseña, cliente.contraseña):
                request.session['cliente_id'] = cliente.pk
                request.session['cliente_nombre'] = cliente.nombre
                return redirect('tienda_inicio')
            else:
                error = 'Correo o contraseña incorrectos.'

    return render(request, 'tienda/login.html', {'form': form, 'error': error})


def logout_cliente(request):
    request.session.flush()
    return redirect('tienda_login')


def inicio(request):
    # Si no hay sesión, manda al login
    if not request.session.get('cliente_id'):
        return redirect('tienda_login')

    nombre = request.session.get('cliente_nombre')
    return render(request, 'tienda/inicio.html', {'nombre': nombre})


# # ──────────────────────────────────────────────
# # PRODUCTOS
# # ──────────────────────────────────────────────

# def productos(request):
#     productos_lista = producto.objects.filter(estado='activo')
#     return render(request, 'tienda/productos.html', {'productos': productos_lista})

# def producto_detalle(request, pk):
#     detalle_producto = get_object_or_404(producto, pk=pk)
#     return render(request, 'tienda/producto_detalle.html', {'producto': detalle_producto})


# # ──────────────────────────────────────────────
# # ACCIONES
# # ──────────────────────────────────────────────

# @login_required
# def reportar_producto(request, pk):
#     producto_reportar = get_object_or_404(producto, pk=pk)
#     return render(request, 'tienda/reportar_producto.html', {'producto': producto_reportar})

# @login_required
# def compartir_producto(request, pk):
#     producto_compartir = get_object_or_404(producto, pk=pk)
#     return render(request, 'tienda/compartir_producto.html', {'producto': producto_compartir})

# @login_required
# def favoritos_producto(request, pk):
#     producto_favoritos = get_object_or_404(producto, pk=pk)
#     return render(request, 'tienda/favoritos_producto.html', {'producto': producto_favoritos})

# @login_required
# def lista_deseados_producto(request, pk):
#     producto_lista_deseados = get_object_or_404(producto, pk=pk)
#     return render(request, 'lista_deseados_producto.html', {'producto': producto_lista_deseados})

# @login_required
# def comparar_producto(request, pk):
#     producto_comparar = get_object_or_404 (producto, pk=pk)
#     return render(request, 'comparar_producto.html', {'producto': producto_comparar})


# # ──────────────────────────────────────────────
# # VER PRODUCTOS EN SECCION COMUNIDAD
# # ──────────────────────────────────────────────

# def comunidad_producto(request, pk):
#     publicacion = get_object_or_404 (producto, pk=pk)
#     return render(request, 'comunidad_producto.html', {'publicacion': publicacion})


# # ──────────────────────────────────────────────
# # FILTRAR, ORDENAR Y BUSCAR PRODUCTOS 
# # ──────────────────────────────────────────────

# def buscar_productos(request, pk):
#     productos_buscar = productos.objects.filter (nombre)
#     return render(request, )