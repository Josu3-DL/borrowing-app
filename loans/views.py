from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from payments.models import Payment

from .forms import LoanFilterForm, LoanForm
from .models import EXCHANGE_RATE, Loan


MONEY_PLACES = Decimal("0.01")
SPANISH_MONTHS = (
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
)


def _to_usd(amount, currency):
    amount = Decimal(amount)
    if currency == Loan.Currency.NIO:
        amount /= EXCHANGE_RATE
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _format_usd(amount):
    return f"${Decimal(amount):,.2f}"


def _percent_change(current, previous):
    current = Decimal(current)
    previous = Decimal(previous)
    if previous == 0:
        return 100 if current > 0 else 0
    return int(((current - previous) / previous * 100).quantize(Decimal("1")))


def _month_sequence(today, length=6):
    current_index = today.year * 12 + today.month - 1
    months = []
    for offset in range(length - 1, -1, -1):
        year, zero_based_month = divmod(current_index - offset, 12)
        months.append((year, zero_based_month + 1))
    return months


def _chart_points(values, width=580, height=180, top=14):
    if not values:
        return ""
    maximum = max(values) or Decimal("1")
    step = width / max(len(values) - 1, 1)
    points = []
    for index, value in enumerate(values):
        x = index * step
        y = top + (height - (Decimal(value) / maximum * height))
        points.append(f"{x:.1f},{float(y):.1f}")
    return " ".join(points)


@login_required
@require_http_methods(["GET"])
def dashboard(request):
    today = timezone.localdate()
    loans = list(
        Loan.objects.filter(owner=request.user)
        .prefetch_related("payments")
        .order_by("-created_at")
    )
    payments = list(
        Payment.objects.filter(loan__owner=request.user)
        .select_related("loan")
        .order_by("-created_at")
    )

    total_lent = sum(
        (_to_usd(loan.amount, loan.currency) for loan in loans),
        Decimal("0"),
    )
    total_recovered = sum(
        (_to_usd(payment.amount, payment.currency) for payment in payments),
        Decimal("0"),
    )
    total_pending = sum(
        (
            _to_usd(loan.remaining_balance, loan.currency)
            for loan in loans
            if loan.status == Loan.Status.PENDING
        ),
        Decimal("0"),
    )
    month_start = date(today.year, today.month, 1)
    payments_this_month = sum(
        (
            _to_usd(payment.amount, payment.currency)
            for payment in payments
            if payment.payment_date >= month_start
        ),
        Decimal("0"),
    )

    months = _month_sequence(today)
    loan_month_values = []
    payment_month_values = []
    month_series = []
    for year, month in months:
        lent = sum(
            (
                _to_usd(loan.amount, loan.currency)
                for loan in loans
                if loan.loan_date.year == year and loan.loan_date.month == month
            ),
            Decimal("0"),
        )
        recovered = sum(
            (
                _to_usd(payment.amount, payment.currency)
                for payment in payments
                if payment.payment_date.year == year
                and payment.payment_date.month == month
            ),
            Decimal("0"),
        )
        loan_month_values.append(lent)
        payment_month_values.append(recovered)
        month_series.append(
            {
                "label": SPANISH_MONTHS[month],
                "lent": lent,
                "recovered": recovered,
            }
        )

    max_monthly_lent = max(loan_month_values) if loan_month_values else Decimal("0")
    for item in month_series:
        item["lent_height"] = (
            max(8, int(item["lent"] / max_monthly_lent * 100))
            if max_monthly_lent
            else 8
        )

    upcoming_loans = []
    for loan in sorted(
        (
            loan
            for loan in loans
            if loan.status == Loan.Status.PENDING
        ),
        key=lambda item: item.due_date,
    )[:4]:
        days_until = (loan.due_date - today).days
        if days_until < 0:
            due_label = f"{abs(days_until)} días vencido"
            due_state = "overdue"
        elif days_until == 0:
            due_label = "Vence hoy"
            due_state = "today"
        elif days_until == 1:
            due_label = "Vence mañana"
            due_state = "soon"
        else:
            due_label = f"En {days_until} días"
            due_state = "upcoming"
        upcoming_loans.append(
            {
                "loan": loan,
                "amount": _format_usd(
                    _to_usd(loan.remaining_balance, loan.currency)
                ),
                "day": f"{loan.due_date.day:02d}",
                "month": SPANISH_MONTHS[loan.due_date.month].upper(),
                "due_label": due_label,
                "due_state": due_state,
            }
        )

    recent_activity = []
    for loan in loans[:5]:
        recent_activity.append(
            {
                "created_at": loan.created_at,
                "kind": "loan",
                "icon": "plus",
                "title": "Nuevo préstamo creado",
                "detail": (
                    f"{loan.borrower_name} · "
                    f"{_format_usd(_to_usd(loan.amount, loan.currency))}"
                ),
            }
        )
    for payment in payments[:5]:
        recent_activity.append(
            {
                "created_at": payment.created_at,
                "kind": "payment",
                "icon": "banknote",
                "title": "Pago recibido",
                "detail": (
                    f"{payment.loan.borrower_name} · "
                    f"{_format_usd(_to_usd(payment.amount, payment.currency))}"
                ),
            }
        )
    recent_activity.sort(key=lambda item: item["created_at"], reverse=True)

    context = {
        "today": today,
        "total_lent": _format_usd(total_lent),
        "total_recovered": _format_usd(total_recovered),
        "total_pending": _format_usd(total_pending),
        "payments_this_month": _format_usd(payments_this_month),
        "active_count": sum(
            loan.status == Loan.Status.PENDING for loan in loans
        ),
        "completed_count": sum(
            loan.status == Loan.Status.PAID for loan in loans
        ),
        "lent_change": _percent_change(
            loan_month_values[-1], loan_month_values[-2]
        ),
        "recovered_change": _percent_change(
            payment_month_values[-1], payment_month_values[-2]
        ),
        "pending_change": 0,
        "month_series": month_series,
        "recovery_points": _chart_points(payment_month_values),
        "recovery_area_points": (
            f"0,210 {_chart_points(payment_month_values)} 580,210"
        ),
        "recent_loans": loans[:5],
        "upcoming_loans": upcoming_loans,
        "recent_activity": recent_activity[:5],
    }
    return render(request, "loans/dashboard.html", context)


def _loan_page_context(request, apply_filters=False):
    loans = Loan.objects.filter(owner=request.user)
    filter_form = LoanFilterForm(
        request.GET if apply_filters else None,
        auto_id="filter_%s",
    )

    if apply_filters and filter_form.is_valid():
        status = filter_form.cleaned_data["status"]
        currency = filter_form.cleaned_data["currency"]
        borrower_name = filter_form.cleaned_data["borrower_name"]
        date_from = filter_form.cleaned_data["date_from"]
        date_to = filter_form.cleaned_data["date_to"]

        if status == "overdue":
            loans = loans.filter(
                status=Loan.Status.PENDING,
                due_date__lt=timezone.localdate(),
            )
        elif status == Loan.Status.PENDING:
            loans = loans.filter(
                status=status,
                due_date__gte=timezone.localdate(),
            )
        elif status:
            loans = loans.filter(status=status)
        if currency:
            loans = loans.filter(currency=currency)
        if borrower_name:
            loans = loans.filter(borrower_name__icontains=borrower_name)
        if date_from:
            loans = loans.filter(loan_date__gte=date_from)
        if date_to:
            loans = loans.filter(loan_date__lte=date_to)

    paginator = Paginator(loans, 5)
    page_obj = paginator.get_page(request.GET.get("page"))
    today = timezone.localdate()
    for loan in page_obj.object_list:
        loan.is_overdue = (
            loan.status == Loan.Status.PENDING and loan.due_date < today
        )

    query_params = request.GET.copy()
    query_params.pop("page", None)
    return {
        "loans": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": query_params.urlencode(),
        "filter_form": filter_form,
    }


@login_required
@require_http_methods(["GET"])
def loan_list(request):
    context = _loan_page_context(request, apply_filters=True)
    return render(request, "loans/loan_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_create(request):
    form = LoanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        loan = form.save(commit=False)
        loan.owner = request.user
        loan.save()
        messages.success(request, "Prestamo creado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context.update({"form": form, "title": "Nuevo préstamo"})
    return render(request, "loans/loan_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_update(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    form = LoanForm(request.POST or None, instance=loan)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Prestamo actualizado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context.update({"form": form, "title": "Editar préstamo"})
    return render(request, "loans/loan_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    if request.method == "POST":
        loan.delete()
        messages.success(request, "Prestamo eliminado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context["loan"] = loan
    return render(request, "loans/loan_confirm_delete.html", context)
