from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle'),
    path('reservar/<int:producto_id>/', views.reservar_producto, name='reservar_producto'),
]