from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from gestion.models import Cliente, Pedido
from .forms import RegistroClienteForm, PerfilUsuarioForm


def registro(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('core:home')
    else:
        form = RegistroClienteForm()
    return render(request, 'usuario/registro.html', {'form': form})

def login_usuario(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        data = request.POST.copy()
        username = data.get('username')
        try:
            user_candidate = User.objects.get(username__iexact=username)
            data['username'] = user_candidate.username
        except User.DoesNotExist:
            pass 

        form = AuthenticationForm(request, data=data)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('core:home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()
    return render(request, 'usuario/login.html', {'form': form})

def logout_usuario(request):
    logout(request)
    return redirect('core:home')

@login_required
def perfil_usuario(request):
    cliente, created = Cliente.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=cliente, user=request.user)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()

            cliente = form.save(commit=False)
            cliente.nombre = form.cleaned_data['first_name']
            cliente.apellido = form.cleaned_data['last_name']
            cliente.email = form.cleaned_data['email']
            
            cliente.rut = form.cleaned_data['rut']
            
            codigo = form.cleaned_data['codigo_pais']
            numero = form.cleaned_data['telefono']
            cliente.telefono = f"{codigo}{numero}"
            
            cliente.codigo_postal = form.cleaned_data['codigo_postal']
            cliente.save()
            
            messages.success(request, "Tus datos han sido actualizados correctamente.")
            return redirect('usuario:perfil')
    else:
        form = PerfilUsuarioForm(instance=cliente, user=request.user)
    return render(request, 'usuario/perfil.html', {'form': form})

@login_required
def mis_pedidos(request):
    try:
        cliente = Cliente.objects.get(user=request.user)
        pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha')
    except Cliente.DoesNotExist:
        pedidos = []
    return render(request, 'usuario/mis_pedidos.html', {'pedidos': pedidos})

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
