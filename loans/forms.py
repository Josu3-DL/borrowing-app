from django import forms

from .models import Loan


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
