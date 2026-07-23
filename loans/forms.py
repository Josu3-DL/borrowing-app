from django import forms
from django.core.exceptions import ValidationError

from borrowing_app.form_fields import PhoneField

from .domain import validate_loan_amount_and_currency_change
from .models import Loan


class LoanFilterForm(forms.Form):
    status = forms.ChoiceField(
        label="Estado",
        choices=(
            ("", "Todos"),
            (Loan.Status.PENDING, "Pendientes"),
            (Loan.Status.PAID, "Pagados"),
            ("overdue", "Atrasados"),
        ),
        required=False,
    )
    currency = forms.ChoiceField(
        label="Moneda",
        choices=(("", "Todas"), *Loan.Currency.choices),
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
        # `status` is intentionally excluded: it is a derived value, kept
        # in sync exclusively by loans.services / payments.services from
        # the recorded payments. See Loan.recompute_status.
        fields = (
            "borrower_name",
            "borrower_phone",
            "borrower_email",
            "amount",
            "currency",
            "loan_date",
            "due_date",
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
            "loan_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "due_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        currency = cleaned_data.get("currency")
        if amount is not None and currency:
            try:
                validate_loan_amount_and_currency_change(
                    self.instance, new_amount=amount, new_currency=currency
                )
            except ValidationError as exc:
                self.add_error(None, exc)
        return cleaned_data
