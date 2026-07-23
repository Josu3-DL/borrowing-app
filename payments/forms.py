from datetime import date

from django import forms

from loans.domain import validate_payment_amount
from loans.models import Loan

from .models import Payment


class PaymentFilterForm(forms.Form):
    borrower_name = forms.CharField(
        label="Prestatario",
        max_length=150,
        required=False,
    )
    currency = forms.ChoiceField(
        label="Moneda del abono",
        choices=(("", "Todas"), *Payment.Currency.choices),
        required=False,
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


class PaymentForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Loan.objects.owned_by(user).filter(
            status=Loan.Status.PENDING
        ).order_by("borrower_name")
        self.fields["loan"].queryset = qs
        self.fields["loan"].label = "Seleccionar préstamo"
        self.fields["amount"].label = "Monto del pago"
        self.fields["currency"].label = "Moneda del pago"
        self.fields["payment_date"].label = "Fecha del pago"
        self.fields["notes"].label = "Referencia / Nota"
        self.fields["loan"].widget.attrs["autocomplete"] = "off"
        self.fields["amount"].widget.attrs.update(
            {
                "placeholder": "0.00",
                "inputmode": "decimal",
            }
        )
        self.fields["notes"].widget.attrs["placeholder"] = (
            "Ej. Pago cuota mensual, referencia bancaria..."
        )
        if not self.is_bound:
            self.fields["payment_date"].initial = date.today()
        self.fields["loan"].label_from_instance = (
            lambda obj: (
                f"{obj.borrower_name}  |  "
                f"Prestamo: {obj.currency_symbol}{obj.amount} {obj.currency}  |  "
                f"Saldo: {obj.currency_symbol}{obj.remaining_balance} {obj.currency}"
                + ("  [PAGADO]" if obj.status == obj.Status.PAID else "")
            )
        )

    class Meta:
        model = Payment
        fields = ("loan", "amount", "currency", "payment_date", "notes")
        widgets = {
            "payment_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        loan = cleaned_data.get("loan")
        amount = cleaned_data.get("amount")
        currency = cleaned_data.get("currency")

        if not loan or not amount or not currency:
            return cleaned_data

        # Validacion amigable y temprana. La autoridad final sobre estas
        # mismas reglas vive en payments.services.create_payment, que las
        # vuelve a aplicar dentro de una transaccion con el prestamo
        # bloqueado.
        try:
            validate_payment_amount(loan, amount, currency)
        except forms.ValidationError as exc:
            self.add_error(None, exc)

        return cleaned_data
