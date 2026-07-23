from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .domain import validate_loan_amount_and_currency_change
from .models import Loan


class LoanAdminForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = "__all__"

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


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    form = LoanAdminForm
    list_display = ("borrower_name", "amount", "loan_date", "due_date", "status", "owner")
    list_filter = ("status",)
    search_fields = ("borrower_name", "borrower_email", "owner__username")
    list_select_related = ("owner",)
    # `status` is derived from the recorded payments; admins can read it
    # here but writes only happen through Loan.recompute_status (see
    # save_model below and loans/payments services).
    readonly_fields = ("status",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.recompute_status()
