from dashboard.models import Cliente


def tienda_context(request):
    """Context processor global para la tienda: cliente logueado y conteo de carrito."""
    cliente_id = request.session.get('cliente_id')
    cliente = None
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id, estado='activo')
        except Cliente.DoesNotExist:
            pass

    carrito = request.session.get('carrito', {})
    carrito_conteo = sum(item.get('cantidad', 1) for item in carrito.values() if isinstance(item, dict))

    return {
        'cliente_autenticado': cliente,
        'carrito_conteo': carrito_conteo,
    }
