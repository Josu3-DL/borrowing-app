from django import forms

from borrowing_app.form_fields import PhoneField

from .models import Loan


class LoanFilterForm(forms.Form):
    status = forms.ChoiceField(
        label="Estado",
        choices=(("", "Todos"), *Loan.Status.choices),
        required=False,
    )
    borrower_name = forms.CharField(
        label="Nombre del prestatario",
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Buscar por nombre...", "type": "search"}
        ),
    )
    date_from = forms.DateField(
        label="Fecha inicial",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        label="Fecha final",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                "La fecha inicial no puede ser posterior a la fecha final."
            )

        return cleaned_data


class LoanForm(forms.ModelForm):
    borrower_phone = PhoneField(
        label="Teléfono del prestatario",
        required=False,
    )

    class Meta:
        model = Loan
        fields = (
            "borrower_name",
            "borrower_phone",
            "borrower_email",
            "amount",
            "loan_date",
            "due_date",
            "status",
        )
        widgets = {
            "borrower_name": forms.TextInput(
                attrs={"placeholder": "Ej. Juan Pérez", "autocomplete": "name"}
            ),
            "borrower_email": forms.EmailInput(
                attrs={"placeholder": "correo@ejemplo.com", "autocomplete": "email"}
            ),
            "amount": forms.NumberInput(
                attrs={"placeholder": "0.00", "min": "0.01", "step": "0.01"}
            ),
            "loan_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
