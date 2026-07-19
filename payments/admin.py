from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("loan", "amount", "payment_date", "created_at")
    list_filter = ("payment_date",)
    search_fields = ("loan__borrower_name",)
    list_select_related = ("loan",)
