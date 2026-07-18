from django import forms
from .models import Prestamo


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = ['cliente', 'monto', 'fecha_prestamo', 'fecha_vencimiento', 'estado']
        widgets = {
            'fecha_prestamo': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_prestamo = cleaned_data.get('fecha_prestamo')
        fecha_vencimiento = cleaned_data.get('fecha_vencimiento')
        if fecha_prestamo and fecha_vencimiento and fecha_vencimiento < fecha_prestamo:
            raise forms.ValidationError(
                'La fecha de vencimiento no puede ser anterior a la fecha del préstamo.'
            )
        return cleaned_data
