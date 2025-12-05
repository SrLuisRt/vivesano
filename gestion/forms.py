from django import forms
from .models import Pedido

class CodigoSeguimientoForm(forms.ModelForm):
    codigo_seguimiento = forms.CharField(
        label="Código de Seguimiento (Courier)",
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', 
            'placeholder': 'Ej: 123456789012',
            'autofocus': 'autofocus'
        }),
        help_text="Ingresa el código proporcionado por el courier (Máx 12 caracteres)."
    )

    class Meta:
        model = Pedido
        fields = ['codigo_seguimiento']

class CorreoSoporteForm(forms.Form):
    asunto = forms.CharField(
        label="Asunto", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    mensaje = forms.CharField(
        label="Mensaje para el Cliente", 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'style': 'resize: none;'})
    )