from django.urls import path
from . import views

app_name = 'pago'

urlpatterns = [
            path('pago/transferencia/<int:pedido_id>/', views.iniciar_pago_transferencia, name='iniciar_transferencia'),
]