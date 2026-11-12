import base64
import json
import logging
import urllib.request
import urllib.parse
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


def get_paypal_base_url():
    mode = getattr(settings, 'PAYPAL_MODE', 'sandbox').lower()
    if mode == 'live' or mode == 'production':
        return 'https://api-m.paypal.com'
    return 'https://api-m.sandbox.paypal.com'


def _realizar_peticion_http(url, metodo='GET', datos=None, headers=None):
    """
    Realiza una petición HTTP usando urllib nativo de Python para garantizar
    máxima compatibilidad sin depender de librerías externas.
    """
    if headers is None:
        headers = {}

    req_data = None
    if datos is not None:
        if isinstance(datos, (dict, list)):
            req_data = json.dumps(datos).encode('utf-8')
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
        elif isinstance(datos, str):
            req_data = datos.encode('utf-8')
        elif isinstance(datos, bytes):
            req_data = datos

    request = urllib.request.Request(url, data=req_data, headers=headers, method=metodo)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status_code = response.status
            body_bytes = response.read()
            body_str = body_bytes.decode('utf-8')
            try:
                body_json = json.loads(body_str) if body_str else {}
            except json.JSONDecodeError:
                body_json = {'raw': body_str}
            return status_code, body_json
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f'Error HTTP en PayPal ({url}) [{e.code}]: {error_body}')
        try:
            error_json = json.loads(error_body)
        except Exception:
            error_json = {'message': error_body}
        return e.code, error_json
    except Exception as e:
        logger.error(f'Excepción de conexión al comunicarse con PayPal ({url}): {e}')
        return 500, {'message': str(e)}


def obtener_access_token():
    """
    Obtiene un Bearer Token OAuth2 de PayPal usando Client ID y Secret.
    """
    client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '').strip()
    secret = getattr(settings, 'PAYPAL_SECRET', '').strip()

    if not client_id or not secret:
        raise ValueError('Las credenciales de PayPal (PAYPAL_CLIENT_ID o PAYPAL_SECRET) no están configuradas.')

    credenciales = f'{client_id}:{secret}'.encode('utf-8')
    auth_header = 'Basic ' + base64.b64encode(credenciales).decode('utf-8')

    url = f'{get_paypal_base_url()}/v1/oauth2/token'
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }
    payload = urllib.parse.urlencode({'grant_type': 'client_credentials'})

    status, response = _realizar_peticion_http(url, metodo='POST', datos=payload, headers=headers)

    if status == 200 and 'access_token' in response:
        return response['access_token']

    error_desc = response.get('error_description') or response.get('message') or 'No se pudo obtener el token de PayPal'
    raise ValueError(f'Error de autenticación con PayPal: {error_desc}')


def crear_orden_paypal(pedido, monto_usd, return_url=None, cancel_url=None):
    """
    Crea una orden en la API v2 de PayPal Checkout.
    Retorna diccionario con 'order_id' y 'approve_url' para redirección directa sin ventanas emergentes.
    """
    token = obtener_access_token()
    url = f'{get_paypal_base_url()}/v2/checkout/orders'

    monto_formateado = f'{Decimal(str(monto_usd)):.2f}'

    app_context = {
        'brand_name': 'HAZE STUDIOS',
        'landing_page': 'NO_PREFERENCE',
        'user_action': 'PAY_NOW',
        'shipping_preference': 'NO_SHIPPING',
    }
    if return_url:
        app_context['return_url'] = return_url
    if cancel_url:
        app_context['cancel_url'] = cancel_url

    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [
            {
                'reference_id': f'HAZE-{pedido.pk}',
                'description': f'Haze Studios - Pedido #{pedido.pk}',
                'custom_id': str(pedido.pk),
                'amount': {
                    'currency_code': 'USD',
                    'value': monto_formateado,
                }
            }
        ],
        'application_context': app_context,
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }

    status, response = _realizar_peticion_http(url, metodo='POST', datos=payload, headers=headers)

    if status in (200, 201) and 'id' in response:
        order_id = response['id']
        approve_url = None
        for link in response.get('links', []):
            if link.get('rel') == 'approve':
                approve_url = link.get('href')
                break

        logger.info(f'Orden #{pedido.pk} creada en PayPal con ID {order_id}')
        return {
            'order_id': order_id,
            'approve_url': approve_url or f'https://www.sandbox.paypal.com/checkoutnow?token={order_id}',
            'raw': response,
        }

    error_msg = response.get('message') or response.get('details') or 'Error al crear orden en PayPal'
    logger.error(f'Fallo al crear orden en PayPal para Pedido #{pedido.pk}: {error_msg}')
    raise ValueError(f'No se pudo inicializar la orden en PayPal: {error_msg}')


def capturar_orden_paypal(order_id):
    """
    Captura los fondos de una orden autorizada por el cliente en PayPal.
    Retorna diccionario con el estado y los datos de la captura.
    """
    token = obtener_access_token()
    url = f'{get_paypal_base_url()}/v2/checkout/orders/{order_id}/capture'

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }

    status, response = _realizar_peticion_http(url, metodo='POST', datos={}, headers=headers)

    if status in (200, 201):
        order_status = response.get('status')
        if order_status == 'COMPLETED':
            purchase_units = response.get('purchase_units', [])
            capture_id = None
            amount_captured = None

            if purchase_units:
                payments = purchase_units[0].get('payments', {})
                captures = payments.get('captures', [])
                if captures:
                    capture_id = captures[0].get('id')
                    amount_captured = captures[0].get('amount', {}).get('value')

            payer = response.get('payer', {})
            payer_email = payer.get('email_address')

            return {
                'success': True,
                'status': 'COMPLETED',
                'order_id': order_id,
                'capture_id': capture_id or order_id,
                'monto_usd': amount_captured,
                'payer_email': payer_email,
                'raw': response,
            }

    error_msg = response.get('message') or response.get('details') or f'Estado recibido: {response.get("status")}'
    logger.error(f'Fallo al capturar orden de PayPal {order_id}: {error_msg}')
    return {
        'success': False,
        'status': response.get('status', 'FAILED'),
        'error': error_msg,
        'raw': response,
    }
