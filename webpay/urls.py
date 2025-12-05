# webpay/urls.py (CORRECTO)
from django.urls import path
from . import views

app_name = 'webpay'

urlpatterns = [
    
    path('iniciar/<int:pedido_id>/', views.iniciar_pago_webpay, name='iniciar_webpay'),
    path('retorno/', views.confirmar_pago_webpay, name='webpay_retorno'),
]