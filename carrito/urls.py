from django.urls import path
from . import views

app_name = 'carrito'

urlpatterns = [
    path('', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_producto, name='agregar'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar'),
    path('actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar'),
    path('limpiar/', views.limpiar_carrito, name='limpiar'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/envio/<int:pedido_id>/', views.seleccion_envio, name='seleccion_envio'),
    path('pago/<int:pedido_id>/', views.seleccion_pago, name='seleccion_pago'),
    path('mis-pedidos/detalle/<int:pedido_id>/', views.detalle_pedido_cliente, name='detalle_pedido_cliente'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
]   