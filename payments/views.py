import json
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from loans.models import EXCHANGE_RATE, Loan

from .forms import PaymentFilterForm, PaymentForm
from .models import Payment


MONEY_PLACES = Decimal("0.01")


def _to_usd(amount, currency):
    amount = Decimal(amount)
    if currency == Payment.Currency.NIO:
        amount /= EXCHANGE_RATE
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _format_money(amount, currency=Payment.Currency.USD):
    symbol = "$" if currency == Payment.Currency.USD else "C$"
    return f"{symbol}{Decimal(amount):,.2f}"


def _percent_change(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return int(((current - previous) / previous * 100).quantize(Decimal("1")))


def _payment_list_context(request):
    today = timezone.localdate()
    all_payments = list(
        Payment.objects.filter(loan__owner=request.user)
        .select_related("loan")
        .prefetch_related("loan__payments")
        .order_by("-payment_date", "-created_at")
    )
    filtered_payments = Payment.objects.filter(
        loan__owner=request.user
    ).select_related("loan").prefetch_related("loan__payments")
    filter_form = PaymentFilterForm(request.GET or None)

    if filter_form.is_valid():
        borrower_name = filter_form.cleaned_data["borrower_name"]
        currency = filter_form.cleaned_data["currency"]
        date_from = filter_form.cleaned_data["date_from"]
        date_to = filter_form.cleaned_data["date_to"]

        if borrower_name:
            filtered_payments = filtered_payments.filter(
                loan__borrower_name__icontains=borrower_name
            )
        if currency:
            filtered_payments = filtered_payments.filter(currency=currency)
        if date_from:
            filtered_payments = filtered_payments.filter(
                payment_date__gte=date_from
            )
        if date_to:
            filtered_payments = filtered_payments.filter(
                payment_date__lte=date_to
            )

    payment_rows = []
    for payment in filtered_payments:
        names = payment.loan.borrower_name.split()
        initials = "".join(name[0] for name in names[:2]).upper()
        payment_rows.append(
            {
                "payment": payment,
                "initials": initials,
                "amount": _format_money(payment.amount, payment.currency),
                "balance": _format_money(
                    payment.loan.remaining_balance,
                    payment.loan.currency,
                ),
                "completed": payment.loan.status == Loan.Status.PAID,
            }
        )

    paginator = Paginator(payment_rows, 8)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)

    current_month_start = date(today.year, today.month, 1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = date(
        previous_month_end.year,
        previous_month_end.month,
        1,
    )
    current_total = sum(
        (
            _to_usd(payment.amount, payment.currency)
            for payment in all_payments
            if payment.payment_date >= current_month_start
        ),
        Decimal("0"),
    )
    previous_total = sum(
        (
            _to_usd(payment.amount, payment.currency)
            for payment in all_payments
            if previous_month_start
            <= payment.payment_date
            <= previous_month_end
        ),
        Decimal("0"),
    )
    owner_loans = Loan.objects.filter(owner=request.user)
    person_choices = (
        owner_loans.order_by("borrower_name")
        .values_list("borrower_name", flat=True)
        .distinct()
    )

    return {
        "filter_form": filter_form,
        "page_obj": page_obj,
        "payment_rows": page_obj.object_list,
        "total_collected_month": _format_money(current_total),
        "collected_change": _percent_change(current_total, previous_total),
        "pending_count": owner_loans.filter(
            status=Loan.Status.PENDING
        ).count(),
        "overdue_count": owner_loans.filter(
            status=Loan.Status.PENDING,
            due_date__lt=today,
        ).count(),
        "person_choices": person_choices,
        "selected_person": request.GET.get("borrower_name", ""),
        "filter_query": query_params.urlencode(),
    }


@login_required
@require_http_methods(["GET"])
def payment_list(request):
    return render(
        request,
        "payments/payment_list.html",
        _payment_list_context(request),
    )


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

    context = _payment_list_context(request)
    context.update({
        "form": form,
        "title": "Registrar abono",
        "loan_data_json": json.dumps(loan_data),
        "exchange_rate": 37,
    })
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
