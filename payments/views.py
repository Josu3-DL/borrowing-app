import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from loans.models import Loan

from .forms import PaymentFilterForm, PaymentForm
from .models import Payment


@login_required
@require_http_methods(["GET"])
def payment_list(request):
    payments = Payment.objects.filter(loan__owner=request.user).select_related("loan")
    filter_form = PaymentFilterForm(request.GET)

    if filter_form.is_valid():
        borrower_name = filter_form.cleaned_data["borrower_name"]
        currency = filter_form.cleaned_data["currency"]
        date_from = filter_form.cleaned_data["date_from"]
        date_to = filter_form.cleaned_data["date_to"]

        if borrower_name:
            payments = payments.filter(loan__borrower_name__icontains=borrower_name)
        if currency:
            payments = payments.filter(currency=currency)
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)

    context = {"payments": payments, "filter_form": filter_form}
    return render(request, "payments/payment_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def payment_create(request):
    form = PaymentForm(request.user, request.POST or None)

    # Datos de prestamos para conversion JS en tiempo real
    loans_qs = Loan.objects.filter(owner=request.user).prefetch_related("payments")
    loan_data = {
        str(l.pk): {
            "currency": l.currency,
            "symbol": l.currency_symbol,
            "amount": str(l.amount),
            "balance": str(l.remaining_balance),
            "borrower": l.borrower_name,
            "status": l.status,
        }
        for l in loans_qs
    }

    if request.method == "POST" and form.is_valid():
        payment = form.save()
        loan = payment.loan
        loan.sync_status()
        sym = payment.currency_symbol
        messages.success(request, f"Abono de {sym}{payment.amount} {payment.currency} registrado correctamente.")
        if loan.status == Loan.Status.PAID:
            messages.success(request, f"El prestamo de {loan.borrower_name} ha quedado completamente pagado!")
        return redirect("payments:list")

    context = {
        "form": form,
        "title": "Registrar abono",
        "loan_data_json": json.dumps(loan_data),
        "exchange_rate": 37,
    }
    return render(request, "payments/payment_form.html", context)


@login_required
@require_http_methods(["POST"])
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk, loan__owner=request.user)
    loan = payment.loan
    payment.delete()
    loan.sync_status()
    messages.success(request, "Abono eliminado correctamente.")
    return redirect("payments:list")
