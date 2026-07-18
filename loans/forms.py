from django import forms

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
            "loan_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
