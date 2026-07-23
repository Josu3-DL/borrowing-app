from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from loans.domain import validate_payment_amount

from .models import Payment


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        loan = cleaned_data.get("loan")
        amount = cleaned_data.get("amount")
        currency = cleaned_data.get("currency")
        if loan and amount is not None and currency:
            try:
                validate_payment_amount(loan, amount, currency)
            except ValidationError as exc:
                self.add_error(None, exc)
        return cleaned_data


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm
    list_display = ("loan", "amount", "payment_date", "created_at")
    list_filter = ("payment_date",)
    search_fields = ("loan__borrower_name",)
    list_select_related = ("loan",)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.loan.recompute_status()

    def delete_model(self, request, obj):
        loan = obj.loan
        super().delete_model(request, obj)
        loan.recompute_status()

    def delete_queryset(self, request, queryset):
        loans = {payment.loan_id: payment.loan for payment in queryset}
        super().delete_queryset(request, queryset)
        for loan in loans.values():
            loan.recompute_status()
