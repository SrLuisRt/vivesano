from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import DatosEnvioForm
from gestion.models import Cliente, Pedido, DetallePedido
from django.contrib import messages
from gestion.models import Producto
from .carrito import Carrito

def agregar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)

    cantidad_solicitada = int(request.POST.get('cantidad', 1))
    
    # --- LÓGICA DE VALIDACIÓN DE STOCK CORREGIDA ---
    # 1. Obtenemos cuánto tiene ya este usuario en su carrito
    producto_id_str = str(producto.id)
    cantidad_en_carrito = 0
    
    if producto_id_str in carrito.carrito:
        cantidad_en_carrito = carrito.carrito[producto_id_str]['cantidad']
    
    # 2. Sumamos lo que tiene + lo que quiere agregar
    total_final = cantidad_en_carrito + cantidad_solicitada

    # 3. Validamos contra el stock real
    if total_final > producto.stock:
        messages.error(request, f"No hay suficiente stock. Ya tienes {cantidad_en_carrito} en el carrito y solo quedan {producto.stock} disponibles en total.")
        # Devolvemos al usuario a donde estaba
        return redirect(request.META.get('HTTP_REFERER', 'core:detalle'))
    
    # Si pasa la validación, agregamos
    carrito.agregar(producto=producto, cantidad=cantidad_solicitada)
    
    messages.success(request, f"¡{producto.nombre} agregado al carrito!")

    url_anterior = request.META.get('HTTP_REFERER')
    
    if url_anterior:
        return redirect(url_anterior)
    
    return redirect('catalogo:catalogo')

def actualizar_carrito(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except ValueError:
        cantidad = 1

    if cantidad == 0:
        carrito.eliminar(producto)
        return redirect('carrito:ver_carrito')

    if cantidad > producto.stock:
        messages.error(request, f"¡Ups! Solo quedan {producto.stock} unidades de {producto.nombre}.")
        return redirect('carrito:ver_carrito')

    carrito.actualizar(producto, cantidad)
    return redirect('carrito:ver_carrito')

def eliminar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    return redirect('carrito:ver_carrito')

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('carrito:ver_carrito')

def ver_carrito(request):
    carrito = Carrito(request)
    return render(request, 'carrito/carrito.html', {
        'carrito': carrito,
        'total': carrito.obtener_total_precio()
    })
@login_required
def checkout(request):
    carrito = Carrito(request)
    if len(carrito) == 0:
        return redirect('core:home')

    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        if request.user.email:
            cliente, created = Cliente.objects.get_or_create(email=request.user.email, defaults={'user': request.user})
            if not created:
                cliente.user = request.user
                cliente.save()
        else:
            cliente = Cliente.objects.create(user=request.user, email="")

    if request.method == 'POST':
        form = DatosEnvioForm(request.POST, instance=cliente, user=request.user)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()

            cliente = form.save(commit=False)
            cliente.nombre = form.cleaned_data['first_name']
            cliente.apellido = form.cleaned_data['last_name']
            cliente.rut = form.cleaned_data['rut']
            
            codigo = form.cleaned_data['codigo_pais']
            numero = form.cleaned_data['telefono']
            cliente.telefono = f"{codigo}{numero}"
            cliente.codigo_postal = form.cleaned_data['codigo_postal']
            cliente.save()

            # Validar Stock (Ultima verificacion antes de avanzar)
            for item in carrito.obtener_items():
                producto_bd = Producto.objects.get(id=item['producto_id'])
                if producto_bd.stock < item['cantidad']:
                    messages.error(request, f"Sin stock suficiente de {producto_bd.nombre}.")
                    return redirect('carrito:ver_carrito')

            # RECICLAJE DE PEDIDO (No saltar IDs)
            pedido = Pedido.objects.filter(cliente=cliente, estado='Pendiente').first()

            if pedido:
                pedido.fecha = timezone.now()
                pedido.total = carrito.obtener_total_precio()
                pedido.save()
                pedido.detalles.all().delete()
            else:
                pedido = Pedido.objects.create(
                    cliente=cliente,
                    total=carrito.obtener_total_precio(),
                    estado='Pendiente'
                )

            for item in carrito.obtener_items():
                producto = get_object_or_404(Producto, id=item['producto_id'])
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio']
                )
            
            return redirect('carrito:seleccion_envio', pedido_id=pedido.id)
            
    else:
        form = DatosEnvioForm(instance=cliente, user=request.user)

    return render(request, 'carrito/confirmar_compra.html', {
        'form': form,
        'carrito': carrito,
        'total': carrito.obtener_total_precio()
    })

@login_required
def seleccion_envio(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente__user=request.user)
    
    subtotal_productos = pedido.total
    COSTO_ENVIO_FIJO = 5990
    UMBRAL_GRATIS = 25000
    aplica_gratis = subtotal_productos > UMBRAL_GRATIS

    if request.method == 'POST':
        tipo_seleccionado = request.POST.get('opcion_envio') 

        if tipo_seleccionado == 'despacho':
            pedido.tipo_entrega = 'Despacho'
            if not aplica_gratis:
                pedido.total = subtotal_productos + COSTO_ENVIO_FIJO
            
        elif tipo_seleccionado == 'retiro':
            pedido.tipo_entrega = 'Retiro'
            pedido.total = subtotal_productos

        pedido.save()
        return redirect('carrito:seleccion_pago', pedido_id=pedido.id)

    context = {
        'pedido': pedido,
        'subtotal': subtotal_productos,
        'costo_envio': COSTO_ENVIO_FIJO,
        'aplica_gratis': aplica_gratis
    }
    return render(request, 'carrito/seleccion_envio.html', context)

def seleccion_pago(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    return render(request, 'carrito/seleccion_pago.html', {'pedido': pedido})

@login_required
def detalle_pedido_cliente(request, pedido_id):
    try:
        cliente = Cliente.objects.get(user=request.user)
        pedido = get_object_or_404(Pedido, id=pedido_id, cliente=cliente)
    except Cliente.DoesNotExist:
        return redirect('core:home')

    estado_actual = pedido.estado
    
    # Lógica de barra de progreso estándar
    progreso = {
        'recibido': True,
        'pagado': False,
        'preparacion': False,
        'despachado': False
    }
    if 'Pagado' in estado_actual or 'Preparacion' in estado_actual or 'Despachado' in estado_actual:
        progreso['pagado'] = True
    if 'Preparacion' in estado_actual or 'Despachado' in estado_actual:
        progreso['preparacion'] = True
    if 'Despachado' in estado_actual:
        progreso['despachado'] = True

    # Detectar si es una reserva habilitada para pagar
    es_reserva_pagable = (estado_actual == 'Reserva Disponible')

    return render(request, 'carrito/detalle_pedido_cliente.html', {
        'pedido': pedido,
        'progreso': progreso,
        'es_reserva_pagable': es_reserva_pagable # Variable nueva para el template
    })
@login_required
def mis_pedidos(request):
    try:
        cliente = Cliente.objects.get(user=request.user)
        pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha')
    except Cliente.DoesNotExist:
        pedidos = []
    return render(request, 'usuario/mis_pedidos.html', {'pedidos': pedidos})
