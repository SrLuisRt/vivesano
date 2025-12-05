from django.shortcuts import render
from gestion.models import Producto

def home(request):
    productos_destacados = Producto.objects.all().order_by('-id')[:4]
    return render(request, 'core/home.html', {'productos': productos_destacados})

