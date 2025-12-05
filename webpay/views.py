from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from gestion.models import Producto, Pedido
from carrito.carrito import Carrito
import time

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType

# Create your views here.

def iniciar_pago_webpay(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    tx = Transaction(WebpayOptions(
        IntegrationCommerceCodes.WEBPAY_PLUS, 
        IntegrationApiKeys.WEBPAY, 
        IntegrationType.TEST
    ))
    buy_order = f"P-{pedido.id}-{int(time.time())}"
    session_id = f"S-{request.user.id}-{int(time.time())}"
    amount = int(pedido.total)
    return_url = request.build_absolute_uri('/webpay/retorno/') 
    response = tx.create(buy_order, session_id, amount, return_url)
    return redirect(response['url'] + '?token_ws=' + response['token'])

def confirmar_pago_webpay(request):
    token = request.GET.get('token_ws') or request.POST.get('token_ws')
    if not token:
        messages.error(request, "Error: No se recibió token de WebPay")
        return redirect('core:home')

    try:
        tx = Transaction(WebpayOptions(
            IntegrationCommerceCodes.WEBPAY_PLUS, 
            IntegrationApiKeys.WEBPAY, 
            IntegrationType.TEST
        ))
        response = tx.commit(token)
        if response['response_code'] == 0:
            buy_order = response['buy_order']
            pedido_id = buy_order.split('-')[1]
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.estado = 'Pagado (WebPay)'
            pedido.save()
            
            carrito = Carrito(request)
            for item in carrito.obtener_items():
                prod = get_object_or_404(Producto, id=item['producto_id'])
                prod.stock -= item['cantidad']
                prod.save()
            
            carrito.limpiar()
            messages.success(request, "¡Pago exitoso con WebPay!")
            return render(request, 'carrito/exito.html', {'pedido_id': pedido.id})
        else:
            messages.error(request, "El pago fue anulado o rechazado por WebPay.")
            return redirect('core:home')
    except Exception as e:
        print(f"Error Webpay: {e}")
        messages.error(request, "Ocurrió un error técnico al confirmar el pago.")
        return redirect('core:home')
    
