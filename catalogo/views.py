from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from gestion.models import Producto, Cliente, Pedido, DetallePedido, Notificacion

def catalogo(request):
    productos_list = Producto.objects.all().order_by('id')
    
    categoria_filter = request.GET.get('categoria')
    if categoria_filter:
        productos_list = productos_list.filter(categoria__icontains=categoria_filter)

    paginator = Paginator(productos_list, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'catalogo/catalogo.html', {'page_obj': page_obj})

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'catalogo/detalle.html', {'producto': producto})

@login_required
def reservar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Verificar que el usuario tenga perfil de cliente
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        messages.error(request, "Completa tu perfil antes de reservar.")
        return redirect('usuario:perfil')

    # Crear un Pedido especial de Reserva
    pedido_reserva = Pedido.objects.create(
        cliente=cliente,
        total=producto.precio, # Precio actual
        estado='Reserva Pendiente',
        tipo_entrega='Despacho' # Por defecto, luego se puede cambiar
    )

    # Crear el detalle
    DetallePedido.objects.create(
        pedido=pedido_reserva,
        producto=producto,
        cantidad=1,
        precio_unitario=producto.precio
    )

    # Notificar a Atención al Cliente
    try:
        grupo_atencion = Group.objects.get(name='Atencion al cliente')
        Notificacion.objects.create(
            destinatario_grupo=grupo_atencion,
            pedido=pedido_reserva,
            mensaje=f"SOLICITUD RESERVA: El cliente {cliente.nombre} solicita stock de {producto.nombre}.",
            estado='PENDIENTE'
        )
    except Group.DoesNotExist:
        pass

    messages.success(request, f"Solicitud de reserva enviada para {producto.nombre}. Te notificaremos cuando llegue.")
    return redirect('carrito:mis_pedidos')


