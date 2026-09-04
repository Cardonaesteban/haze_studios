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

    # HTML elegante corporativo (sin emojis)
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

