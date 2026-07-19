from django.contrib import admin

from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("borrower_name", "amount", "loan_date", "due_date", "status", "owner")
    list_filter = ("status",)
    search_fields = ("borrower_name", "borrower_email", "owner__username")
    list_select_related = ("owner",)
