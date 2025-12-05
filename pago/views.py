from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import Group
from gestion.models import  Pedido, Notificacion
from carrito.carrito import Carrito


def iniciar_pago_transferencia(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pedido.estado = 'Pendiente Pago (Transferencia)'
    pedido.save()
    
    try:
        grupo_atencion = Group.objects.get(name__iexact='Atencion al cliente')
        existe = Notificacion.objects.filter(pedido=pedido, mensaje__contains="TRANSFERENCIA").exists()
        if not existe:
            Notificacion.objects.create(
                destinatario_grupo=grupo_atencion,
                pedido=pedido,
                mensaje=f"TRANSFERENCIA: El cliente {pedido.cliente.nombre} seleccionó transferencia. Esperando comprobante.",
                estado='PENDIENTE'
            )
    except Group.DoesNotExist:
        pass
    
    carrito = Carrito(request)
    carrito.limpiar()
    
    return render(request, 'pago/transferencia_instrucciones.html', {'pedido': pedido})
