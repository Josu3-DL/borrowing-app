from django import forms

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
        qs = Loan.objects.filter(owner=user).order_by("borrower_name")
        self.fields["loan"].queryset = qs
        self.fields["loan"].label_from_instance = (
            lambda obj: (
                f"{obj.borrower_name}  |  "
                f"Prestamo: {obj.currency_symbol}{obj.amount} {obj.currency}  |  "
                f"Saldo: {obj.currency_symbol}{obj.remaining_balance} {obj.currency}"
            )
        )

    class Meta:
        model = Payment
        fields = ("loan", "amount", "currency", "payment_date", "notes")
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
