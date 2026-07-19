from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django import forms

from loans.models import EXCHANGE_RATE, Loan

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
        qs = Loan.objects.filter(owner=user).order_by("borrower_name")
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
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        loan = cleaned_data.get("loan")
        amount = cleaned_data.get("amount")
        currency = cleaned_data.get("currency")

        if not loan or not amount or not currency:
            return cleaned_data

        # Regla 1: no permitir abonar a un prestamo ya pagado
        if loan.status == Loan.Status.PAID:
            raise forms.ValidationError(
                f"El prestamo de {loan.borrower_name} ya esta completamente pagado. "
                "No se pueden registrar mas abonos."
            )

        # Regla 2: convertir abono a la moneda del prestamo y comparar con saldo
        if loan.currency == currency:
            amount_in_loan_cur = amount
        elif loan.currency == "USD" and currency == "NIO":
            amount_in_loan_cur = (amount / EXCHANGE_RATE).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:  # prestamo NIO, abono USD
            amount_in_loan_cur = (amount * EXCHANGE_RATE).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        balance = loan.remaining_balance
        if amount_in_loan_cur > balance:
            sym = loan.currency_symbol
            pay_sym = "$" if currency == "USD" else "C$"
            raise forms.ValidationError(
                f"El abono de {pay_sym}{amount} {currency} equivale a "
                f"{sym}{amount_in_loan_cur} {loan.currency}, "
                f"pero el saldo restante es solo {sym}{balance} {loan.currency}."
            )

        return cleaned_data
