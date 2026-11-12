from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

MENSAJES_ESTADO = {
    'pendiente': 'Tu pedido ha sido registrado y se encuentra pendiente de confirmación.',
    'procesando': 'Tu pedido está siendo preparado por nuestro equipo para su posterior despacho.',
    'enviado': 'Tu pedido ha sido enviado y se encuentra en camino hacia tu dirección de entrega.',
    'entregado': 'Tu pedido ha sido entregado exitosamente. Esperamos que disfrutes tus prendas de Haze Studios.',
    'cancelado': 'Tu pedido ha sido cancelado. Si tienes dudas o comentarios, contáctanos a soporte.',
}


def enviar_notificacion_estado_pedido(pedido, estado_anterior=None):
    """
    Envía un correo electrónico al cliente cuando el estado de su pedido cambia.
    """
    cliente = getattr(pedido, 'cliente', None)
    if not cliente or not getattr(cliente, 'correo', None):
        logger.warning(f"No se pudo enviar correo para pedido #{pedido.pk}: cliente sin correo.")
        return False

    estado_actual_display = pedido.get_estado_display()
    mensaje_personalizado = MENSAJES_ESTADO.get(
        pedido.estado,
        f'El estado de tu pedido ha sido actualizado a {estado_actual_display}.'
    )

    asunto = f'Actualización de tu pedido #{pedido.pk} — {estado_actual_display} — Haze Studios'

    detalles = pedido.detalles.select_related('producto').all()

    # Formatear lista en texto plano
    lineas_productos = []
    for d in detalles:
        nombre_prod = getattr(d.producto, 'nombre', 'Producto')
        lineas_productos.append(f"- {nombre_prod} x {d.cantidad}: ${d.subtotal():,.0f}")
    productos_texto = "\n".join(lineas_productos) if lineas_productos else "Detalles disponibles en tu cuenta."

    mensaje_plano = (
        f"Hola {cliente.nombre},\n\n"
        f"Queremos informarte sobre una actualización en tu pedido #{pedido.pk}.\n\n"
        f"Estado actual: {estado_actual_display}\n"
        f"{mensaje_personalizado}\n\n"
        f"Resumen de productos:\n"
        f"{productos_texto}\n\n"
        f"Total: ${pedido.total:,.0f}\n\n"
        f"Puedes revisar el seguimiento detallado ingresando a tu cuenta en Haze Studios.\n\n"
        f"Atentamente,\n"
        f"El equipo de Haze Studios"
    )

    # HTML - INICIALIZAR filas_html ANTES de usarla
    filas_html = ""
    for d in detalles:
        nombre_prod = getattr(d.producto, 'nombre', 'Producto')
        filas_html += f"""
        <tr>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #1e293b;">
                {nombre_prod}
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b; text-align: center;">
                {d.cantidad}
            </td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #0f172a; font-weight: 600; text-align: right;">
                ${d.subtotal():,.0f}
            </td>
        </tr>
        """

    # Si no hay detalles, mostrar un mensaje en la tabla
    if not filas_html:
        filas_html = """
        <tr>
            <td colspan="3" style="padding: 10px 12px; text-align: center; color: #64748b;">
                Sin productos en este pedido
            </td>
        </tr>
        """

    html_message = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #0f172a; }}
            .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .header {{ background: #0f172a; color: #ffffff; padding: 28px 32px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 20px; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; }}
            .content {{ padding: 32px; }}
            .status-box {{ background: #f1f5f9; border-left: 4px solid #0f172a; padding: 16px 20px; border-radius: 6px; margin: 20px 0; }}
            .status-title {{ font-size: 13px; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.5px; margin: 0 0 4px 0; }}
            .status-value {{ font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 6px 0; }}
            .status-desc {{ font-size: 14px; color: #334155; margin: 0; line-height: 1.5; }}
            .order-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .order-table th {{ background: #f8fafc; padding: 10px 12px; text-align: left; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #e2e8f0; }}
            .total-row {{ font-size: 16px; font-weight: 700; color: #0f172a; text-align: right; padding: 16px 12px 0 12px; }}
            .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; text-align: center; font-size: 13px; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>HAZE STUDIOS</h1>
            </div>
            <div class="content">
                <p style="font-size: 16px; margin-top: 0;">Hola <strong>{cliente.nombre}</strong>,</p>
                <p style="font-size: 15px; line-height: 1.5; color: #334155;">
                    Te informamos que tu pedido <strong>#{pedido.pk}</strong> ha tenido una actualización de estado:
                </p>
                <div class="status-box">
                    <p class="status-title">Estado del pedido</p>
                    <p class="status-value">{estado_actual_display}</p>
                    <p class="status-desc">{mensaje_personalizado}</p>
                </div>

                <h3 style="font-size: 15px; margin: 24px 0 10px 0; color: #0f172a;">Resumen de compra</h3>
                <table class="order-table">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th style="text-align: center;">Cantidad</th>
                            <th style="text-align: right;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_html}
                    </tbody>
                </table>
                <div class="total-row">
                    Total: ${pedido.total:,.0f}
                </div>
            </div>
            <div class="footer">
                Haze Studios — Moda urbana contemporánea.<br>
                Este es un mensaje automático de notificación de pedido.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        send_mail(
            subject=asunto,
            message=mensaje_plano,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[cliente.correo],
            html_message=html_message,
            fail_silently=True,
        )

        # Registrar en el historial de mensajes del sistema
        from .models import Mensaje
        resumen_prods = ", ".join([f"{getattr(d.producto, 'nombre', 'Producto')} (x{d.cantidad})" for d in detalles])
        if resumen_prods:
            contenido_registro = f"Actualización de pedido #{pedido.pk}: Estado {estado_actual_display}. {mensaje_personalizado} Productos: {resumen_prods}"
        else:
            contenido_registro = f"Actualización de pedido #{pedido.pk}: Estado {estado_actual_display}. {mensaje_personalizado}"
        contenido_registro = contenido_registro[:500]

        Mensaje.objects.create(
            destinatario=cliente,
            remitente='Haze Studios',
            tipo='notificacion_pedido',
            contenido=contenido_registro,
            estado='enviado',
            pedido=pedido
        )

        return True
    except Exception as e:
        logger.error(f"Error al enviar notificación de pedido #{pedido.pk}: {e}")
        return False


def enviar_factura_pedido(pedido):
    """
    Envía la factura y comprobante de compra oficial al correo del cliente
    con la identidad visual de Haze Studios (fondo oscuro, acentos en azul y violeta, cero emojis).
    """
    cliente = getattr(pedido, 'cliente', None)
    if not cliente or not getattr(cliente, 'correo', None):
        logger.warning(f"No se pudo enviar factura para pedido #{pedido.pk}: cliente sin correo.")
        return False

    asunto = f"Factura y Confirmación de Compra — Pedido #{pedido.pk} — Haze Studios"

    detalles = pedido.detalles.select_related('producto').all()

    # Formato de método de pago
    if pedido.metodo_pago == 'paypal':
        metodo_pago_texto = "PayPal / Tarjeta Internacional"
        info_adicional_pago = f"ID de Transacción: {pedido.transaccion_id or 'Confirmado'}"
        if pedido.monto_usd:
            info_adicional_pago += f" (${pedido.monto_usd:.2f} USD)"
    elif pedido.metodo_pago == 'contra_entrega':
        metodo_pago_texto = "Pago Contra Entrega"
        info_adicional_pago = "Cobro en efectivo al momento de recibir en dirección"
    else:
        metodo_pago_texto = "Confirmado"
        info_adicional_pago = "Pago registrado exitosamente"

    # Filas de productos en texto plano
    lineas_prods_texto = []
    for d in detalles:
        nombre_prod = getattr(d.producto, 'nombre', 'Prenda Haze')
        lineas_prods_texto.append(f"- {nombre_prod} (Cantidad: {d.cantidad}) | Subtotal: ${d.subtotal():,.0f} COP")
    prods_resumen_plano = "\n".join(lineas_prods_texto) if lineas_prods_texto else "Prendas de catálogo Haze Studios"

    mensaje_plano = (
        f"HAZE STUDIOS — FACTURA DE COMPRA\n"
        f"Pedido #{pedido.pk}\n\n"
        f"Cliente: {cliente.nombre} {cliente.apellido}\n"
        f"Correo: {cliente.correo}\n"
        f"Fecha: {pedido.fecha_pedido}\n"
        f"Metodo de pago: {metodo_pago_texto} ({info_adicional_pago})\n\n"
        f"RESUMEN DE PRODUCTOS:\n"
        f"{prods_resumen_plano}\n\n"
        f"TOTAL FACTURADO: ${pedido.total:,.0f} COP\n\n"
        f"Instrucciones de entrega: {pedido.notas or 'Entrega estandar a domicilio'}\n\n"
        f"Gracias por elegir Haze Studios. Moda urbana contemporanea.\n"
        f"Equipo de Atencion Haze Studios"
    )

    # Filas de la tabla HTML
    filas_html = ""
    for d in detalles:
        nombre_prod = getattr(d.producto, 'nombre', 'Prenda Haze')
        filas_html += f"""
        <tr>
            <td style="padding: 12px 14px; border-bottom: 1px solid #1f2937; color: #f3f4f6; font-size: 14px;">
                <strong>{nombre_prod}</strong>
            </td>
            <td style="padding: 12px 14px; border-bottom: 1px solid #1f2937; color: #9ca3af; font-size: 14px; text-align: center;">
                {d.cantidad}
            </td>
            <td style="padding: 12px 14px; border-bottom: 1px solid #1f2937; color: #9ca3af; font-size: 14px; text-align: right;">
                ${d.precio_unitario:,.0f}
            </td>
            <td style="padding: 12px 14px; border-bottom: 1px solid #1f2937; color: #60a5fa; font-weight: 700; font-size: 14px; text-align: right;">
                ${d.subtotal():,.0f}
            </td>
        </tr>
        """

    if not filas_html:
        filas_html = """
        <tr>
            <td colspan="4" style="padding: 14px; text-align: center; color: #9ca3af; font-size: 14px;">
                Prendas registradas en tu orden
            </td>
        </tr>
        """

    monto_usd_html = f"<div style='font-size: 13px; color: #9ca3af; margin-top: 4px;'>Equivalente cobrado en PayPal: <strong>${pedido.monto_usd:.2f} USD</strong></div>" if pedido.monto_usd else ""

    html_message = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Factura #{pedido.pk} - Haze Studios</title>
        <style>
            body {{
                margin: 0;
                padding: 24px;
                background-color: #0b0f19;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                color: #e5e7eb;
            }}
            .wrapper {{
                max-width: 620px;
                margin: 0 auto;
                background-color: #111827;
                border-radius: 14px;
                border: 1px solid #1f2937;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            }}
            .header {{
                background-color: #0f172a;
                padding: 30px 36px 24px 36px;
                border-bottom: 2px solid #3b82f6;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 900;
                letter-spacing: 3px;
                color: #ffffff;
                text-transform: uppercase;
            }}
            .header p {{
                margin: 6px 0 0 0;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: #93c5fd;
                font-weight: 600;
            }}
            .content {{
                padding: 32px 36px;
            }}
            .invoice-pill {{
                display: inline-block;
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #60a5fa;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 4px 12px;
                border-radius: 999px;
                margin-bottom: 16px;
            }}
            .meta-grid {{
                display: table;
                width: 100%;
                margin-bottom: 24px;
                background-color: #0f172a;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 16px;
                box-sizing: border-box;
            }}
            .meta-col {{
                display: table-cell;
                width: 50%;
                vertical-align: top;
                padding: 0 8px;
                font-size: 13px;
                line-height: 1.6;
            }}
            .meta-label {{
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #6b7280;
                margin-bottom: 2px;
            }}
            .meta-value {{
                color: #f3f4f6;
                font-weight: 600;
            }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .items-table th {{
                background-color: #0f172a;
                padding: 10px 14px;
                text-align: left;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #9ca3af;
                border-bottom: 2px solid #1f2937;
            }}
            .total-card {{
                background-color: #0f172a;
                border: 1px solid #1f2937;
                border-left: 4px solid #3b82f6;
                border-radius: 8px;
                padding: 18px 20px;
                text-align: right;
                margin-top: 16px;
            }}
            .total-title {{
                font-size: 12px;
                text-transform: uppercase;
                color: #9ca3af;
                font-weight: 700;
                letter-spacing: 0.5px;
                margin: 0 0 4px 0;
            }}
            .total-value {{
                font-size: 26px;
                font-weight: 900;
                color: #ffffff;
                margin: 0;
            }}
            .delivery-box {{
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 16px;
                margin-top: 24px;
                font-size: 13px;
                color: #9ca3af;
                line-height: 1.5;
            }}
            .footer {{
                background-color: #0b0f19;
                border-top: 1px solid #1f2937;
                padding: 24px 36px;
                text-align: center;
                font-size: 12px;
                color: #6b7280;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="header">
                <h1>HAZE STUDIOS</h1>
                <p>Comprobante Oficial de Compra</p>
            </div>
            <div class="content">
                <div class="invoice-pill">Factura #HAZE-{pedido.pk}</div>
                
                <div class="meta-grid">
                    <div class="meta-col">
                        <div class="meta-label">Cliente</div>
                        <div class="meta-value">{cliente.nombre} {cliente.apellido}</div>
                        <div style="color: #9ca3af;">{cliente.correo}</div>
                    </div>
                    <div class="meta-col" style="text-align: right;">
                        <div class="meta-label">Metodo de Pago</div>
                        <div class="meta-value" style="color: #60a5fa;">{metodo_pago_texto}</div>
                        <div style="font-size: 11px; color: #9ca3af; margin-top: 2px;">{info_adicional_pago}</div>
                    </div>
                </div>

                <table class="items-table">
                    <thead>
                        <tr>
                            <th>Prenda</th>
                            <th style="text-align: center;">Cant.</th>
                            <th style="text-align: right;">Precio Unit.</th>
                            <th style="text-align: right;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_html}
                    </tbody>
                </table>

                <div class="total-card">
                    <div class="total-title">Total Pagado / Liquidado</div>
                    <div class="total-value">${pedido.total:,.0f} COP</div>
                    {monto_usd_html}
                </div>

                <div class="delivery-box">
                    <div style="font-weight: 700; color: #e5e7eb; margin-bottom: 4px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">
                        Detalles de Entrega y Envio:
                    </div>
                    <div>{pedido.notas or 'Despacho estandar a direccion registrada.'}</div>
                </div>
            </div>

            <div class="footer">
                Haze Studios — Streetwear & Alta Moda Urbana.<br>
                Este correo confirma tu compra y registro formal en nuestro sistema.<br>
                Por favor conserva este comprobante para tu control.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        send_mail(
            subject=asunto,
            message=mensaje_plano,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[cliente.correo],
            html_message=html_message,
            fail_silently=False,
        )

        from .models import Mensaje
        contenido_historial = f"Factura de pedido #{pedido.pk} enviada a {cliente.correo}. Total: ${pedido.total:,.0f} COP ({metodo_pago_texto})"[:500]

        Mensaje.objects.create(
            destinatario=cliente,
            remitente='Haze Studios',
            tipo='notificacion_pedido',
            contenido=contenido_historial,
            estado='enviado',
            pedido=pedido
        )
        logger.info(f"Factura enviada correctamente para Pedido #{pedido.pk} a {cliente.correo}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar factura para pedido #{pedido.pk}: {e}")
        return False
