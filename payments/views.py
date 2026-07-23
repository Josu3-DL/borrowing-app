from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from borrowing_app import money
from borrowing_app.reporting import percent_change
from loans.models import Loan

from . import selectors, services
from .forms import PaymentFilterForm, PaymentForm
from .models import Payment


def _payment_list_context(request):
    today = timezone.localdate()
    filter_form = PaymentFilterForm(request.GET or None)

    filters = filter_form.cleaned_data if filter_form.is_valid() else None
    payments = selectors.filtered_payments(request.user, filters=filters)
    paginator, page_obj = selectors.paginate_payment_rows(
        payments, page_number=request.GET.get("page")
    )

    current_total, previous_total = selectors.monthly_collected_totals(
        request.user, today=today
    )
    status_counts = selectors.loan_status_counts(request.user, today=today)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return {
        "filter_form": filter_form,
        "page_obj": page_obj,
        "payment_rows": page_obj.object_list,
        "total_collected_month": money.format_money(current_total, Payment.Currency.USD),
        "total_collected_month_value": current_total,
        "collected_change": percent_change(current_total, previous_total),
        "pending_count": status_counts["pending_count"],
        "overdue_count": status_counts["overdue_count"],
        "person_choices": selectors.person_choices(request.user),
        "selected_person": request.GET.get("borrower_name", ""),
        "filter_query": query_params.urlencode(),
    }


@login_required
@require_http_methods(["GET"])
def payment_list(request):
    return render(request, "payments/payment_list.html", _payment_list_context(request))


def _safe_next_url(candidate):
    """Restringe el redirect posterior al registro de un abono a rutas conocidas."""
    allowed = {reverse("payments:list"), reverse("loans:list")}
    return candidate if candidate in allowed else reverse("payments:list")


@login_required
@require_http_methods(["GET", "POST"])
def payment_create(request):
    next_url = _safe_next_url(request.POST.get("next") or request.GET.get("next"))

    initial = {}
    preselected_loan = request.GET.get("loan")
    if request.method == "GET" and preselected_loan:
        initial["loan"] = preselected_loan

    form = PaymentForm(request.user, request.POST or None, initial=initial)

    # Datos de prestamos para conversion JS en tiempo real.
    loans_qs = Loan.objects.owned_by(request.user).prefetch_related("payments")
    loan_data = {
        str(loan.pk): {
            "currency": loan.currency,
            "symbol": loan.currency_symbol,
            "amount": str(loan.amount),
            "balance": str(loan.remaining_balance),
            "borrower": loan.borrower_name,
            "status": loan.status,
        }
        for loan in loans_qs
    }

    if request.method == "POST" and form.is_valid():
        try:
            payment = services.create_payment(
                user=request.user, cleaned_data=form.cleaned_data
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            loan = payment.loan
            sym = payment.currency_symbol
            messages.success(
                request,
                f"Abono de {sym}{payment.amount} {payment.currency} registrado correctamente.",
            )
            if loan.status == Loan.Status.PAID:
                messages.success(
                    request,
                    f"El prestamo de {loan.borrower_name} ha quedado completamente pagado!",
                )
            return redirect(next_url)

    context = _payment_list_context(request)
    context.update(
        {
            "form": form,
            "title": "Registrar abono",
            "loan_data": loan_data,
            "next_url": next_url,
        }
    )
    return render(request, "payments/payment_form.html", context)


@login_required
@require_http_methods(["GET"])
def loan_payments_json(request, loan_pk):
    """Devuelve el historial de abonos de un préstamo como JSON."""
    loan = get_object_or_404(Loan.objects.owned_by(request.user), pk=loan_pk)
    payments = list(loan.payments.all().order_by("-payment_date", "-created_at"))
    return JsonResponse(
        {
            "loan_code": f"LN-{loan.pk:04d}",
            "borrower_name": loan.borrower_name,
            "amount": f"{loan.currency_symbol}{loan.amount:,.2f}",
            "total_paid": f"{loan.currency_symbol}{loan.total_paid:,.2f}",
            "remaining_balance": f"{loan.currency_symbol}{loan.remaining_balance:,.2f}",
            "status": loan.get_status_display(),
            "payments": [
                {
                    "amount": f"{p.currency_symbol}{p.amount:,.2f}",
                    "payment_date": p.payment_date.strftime("%d %b %Y"),
                    "notes": p.notes if p.notes else "—",
                }
                for p in payments
            ],
        }
    )


@login_required
@require_http_methods(["POST"])
def payment_delete(request, pk):
    payment = get_object_or_404(Payment.objects.owned_by(request.user), pk=pk)
    services.delete_payment(user=request.user, payment=payment)
    messages.success(request, "Abono eliminado correctamente.")
    return redirect("payments:list")
