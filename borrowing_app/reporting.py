"""Dashboard reporting layer.

This is the one place allowed to query both `loans` and `payments`
together to compose the panel. Keeping it out of `loans/views.py` avoids a
loans -> payments dependency (payments already depends on loans, since a
payment belongs to a loan; this module sits above both so neither app has
to import the other's internals just to build a report).

Every value returned here is already presentation-ready (formatted money
strings, day/month labels, chart coordinates): templates should not need
to perform financial calculations of their own.
"""

from datetime import date
from decimal import Decimal

from django.utils import timezone

from borrowing_app import money
from loans.models import Loan
from payments.models import Payment

CHART_MONTH_OPTIONS = (3, 6, 12)
DEFAULT_CHART_MONTHS = 6
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


def chart_month_count(raw_value):
    try:
        month_count = int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_CHART_MONTHS
    return month_count if month_count in CHART_MONTH_OPTIONS else DEFAULT_CHART_MONTHS


def percent_change(current, previous):
    """Generic percentage change, shared by the loans dashboard and the
    payments list so both report growth the same way."""
    current = Decimal(current)
    previous = Decimal(previous)
    if previous == 0:
        return 100 if current > 0 else 0
    return int(((current - previous) / previous * 100).quantize(Decimal("1")))


# Backwards-compatible private alias for readability within this module.
_percent_change = percent_change


def _month_sequence(today, length):
    current_index = today.year * 12 + today.month - 1
    months = []
    for offset in range(length - 1, -1, -1):
        year, zero_based_month = divmod(current_index - offset, 12)
        months.append((year, zero_based_month + 1))
    return months


def _chart_coordinates(values, width=580, height=180, top=14):
    if not values:
        return []
    maximum = max(values) or Decimal("1")
    step = width / max(len(values) - 1, 1)
    coordinates = []
    for index, value in enumerate(values):
        x = index * step
        y = top + (height - (Decimal(value) / maximum * height))
        coordinates.append(
            {
                "x": f"{x:.1f}",
                "y": f"{float(y):.1f}",
                "tooltip_x": f"{min(max(x, 70), width - 70):.1f}",
                "tooltip_y": f"{max(float(y) - 10, 30):.1f}",
            }
        )
    return coordinates


def _chart_points(values):
    return " ".join(
        f'{coordinate["x"]},{coordinate["y"]}' for coordinate in _chart_coordinates(values)
    )


def _due_label(loan, today):
    days_until = (loan.due_date - today).days
    if days_until < 0:
        return f"{abs(days_until)} días vencido", "overdue"
    if days_until == 0:
        return "Vence hoy", "today"
    if days_until == 1:
        return "Vence mañana", "soon"
    return f"En {days_until} días", "upcoming"


def _currency_report(*, currency, loans, payments, months, month_start, pending_loans):
    total_lent = sum(
        (money.convert(loan.amount, loan.currency, currency) for loan in loans),
        Decimal("0"),
    )
    total_recovered = sum(
        (money.convert(payment.amount, payment.currency, currency) for payment in payments),
        Decimal("0"),
    )
    total_pending = sum(
        (
            money.convert(loan.remaining_balance, loan.currency, currency)
            for loan in loans
            if loan.status == Loan.Status.PENDING
        ),
        Decimal("0"),
    )
    payments_this_month = sum(
        (
            money.convert(payment.amount, payment.currency, currency)
            for payment in payments
            if payment.payment_date >= month_start
        ),
        Decimal("0"),
    )

    loan_month_values, payment_month_values, month_series = [], [], []
    for year, month_number in months:
        monthly_loans = [
            loan for loan in loans if loan.loan_date.year == year and loan.loan_date.month == month_number
        ]
        lent = sum(
            (money.convert(loan.amount, loan.currency, currency) for loan in monthly_loans),
            Decimal("0"),
        )
        recovered = sum(
            (
                money.convert(payment.amount, payment.currency, currency)
                for payment in payments
                if payment.payment_date.year == year and payment.payment_date.month == month_number
            ),
            Decimal("0"),
        )
        loan_month_values.append(lent)
        payment_month_values.append(recovered)
        month_series.append(
            {
                "label": SPANISH_MONTHS[month_number],
                "lent_height": 8,
                "loan_count": len(monthly_loans),
                "recovered_amount": money.format_money(recovered, currency),
            }
        )

    max_monthly_lent = max(loan_month_values) if loan_month_values else Decimal("0")
    for item, lent in zip(month_series, loan_month_values):
        item["lent_height"] = max(8, int(lent / max_monthly_lent * 100)) if max_monthly_lent else 8

    for item, coordinate in zip(month_series, _chart_coordinates(payment_month_values)):
        item.update(
            recovery_x=coordinate["x"],
            recovery_y=coordinate["y"],
            recovery_tooltip_x=coordinate["tooltip_x"],
            recovery_tooltip_y=coordinate["tooltip_y"],
        )

    today = timezone.localdate()
    upcoming = []
    for loan in pending_loans:
        due_label, due_state = _due_label(loan, today)
        upcoming.append(
            {
                "id": loan.pk,
                "borrower_name": loan.borrower_name,
                "amount": money.format_money(loan.remaining_balance, loan.currency),
                "day": f"{loan.due_date.day:02d}",
                "month": SPANISH_MONTHS[loan.due_date.month].upper(),
                "due_label": due_label,
                "due_state": due_state,
            }
        )

    recent = [
        {
            "borrower_name": loan.borrower_name,
            "loan_date": loan.loan_date.strftime("%d %b %Y"),
            "amount": money.format_money(loan.amount, loan.currency),
            "status": loan.status,
            "status_display": loan.get_status_display(),
        }
        for loan in loans[:5]
    ]

    activity = [
        {
            "created_at": loan.created_at,
            "kind": "loan",
            "icon": "plus",
            "title": "Nuevo préstamo creado",
            "detail": f"{loan.borrower_name} · {money.format_money(loan.amount, loan.currency)}",
        }
        for loan in loans[:5]
    ]
    activity += [
        {
            "created_at": payment.created_at,
            "kind": "payment",
            "icon": "banknote",
            "title": "Pago recibido",
            "detail": f"{payment.loan.borrower_name} · {money.format_money(payment.amount, payment.currency)}",
        }
        for payment in payments[:5]
    ]
    activity.sort(key=lambda item: item["created_at"], reverse=True)

    return {
        "total_lent": money.format_money(total_lent, currency),
        "total_recovered": money.format_money(total_recovered, currency),
        "total_pending": money.format_money(total_pending, currency),
        "payments_this_month": money.format_money(payments_this_month, currency),
        "lent_change": _percent_change(loan_month_values[-1], loan_month_values[-2]),
        "recovered_change": _percent_change(payment_month_values[-1], payment_month_values[-2]),
        "month_series": month_series,
        "recovery_points": _chart_points(payment_month_values),
        "recovery_area_points": f"0,210 {_chart_points(payment_month_values)} 580,210",
        "recent_loans": recent,
        "upcoming_loans": upcoming,
        "recent_activity": activity[:5],
    }


def dashboard_context(user, *, chart_months_param):
    """Build the full context for the loans dashboard for `user`.

    Loads each user's loans and payments once (with `payments` prefetched
    on the loans queryset) and reuses that in-memory data to build the
    report for every supported display currency, avoiding N+1 queries and
    repeated round trips for a page that always needs the full picture.
    """
    today = timezone.localdate()
    months_to_show = chart_month_count(chart_months_param)

    loans = list(
        Loan.objects.owned_by(user).prefetch_related("payments").order_by("-created_at")
    )
    payments = list(
        Payment.objects.owned_by(user).select_related("loan").order_by("-created_at")
    )

    month_start = date(today.year, today.month, 1)
    months = _month_sequence(today, months_to_show)
    pending_loans = sorted(
        (loan for loan in loans if loan.status == Loan.Status.PENDING),
        key=lambda item: item.due_date,
    )[:4]

    currency_data = {
        currency: _currency_report(
            currency=currency,
            loans=loans,
            payments=payments,
            months=months,
            month_start=month_start,
            pending_loans=pending_loans,
        )
        for currency in Loan.Currency.values
    }
    selected = currency_data[Loan.Currency.NIO]

    return {
        "today": today,
        "total_lent": selected["total_lent"],
        "total_recovered": selected["total_recovered"],
        "total_pending": selected["total_pending"],
        "payments_this_month": selected["payments_this_month"],
        "active_count": sum(loan.status == Loan.Status.PENDING for loan in loans),
        "completed_count": sum(loan.status == Loan.Status.PAID for loan in loans),
        "lent_change": selected["lent_change"],
        "recovered_change": selected["recovered_change"],
        "pending_change": 0,
        "chart_month_count": months_to_show,
        "month_series": selected["month_series"],
        "recovery_points": selected["recovery_points"],
        "recovery_area_points": selected["recovery_area_points"],
        "recent_loans": selected["recent_loans"],
        "upcoming_loans": selected["upcoming_loans"],
        "recent_activity": selected["recent_activity"],
        "currency_data": currency_data,
    }
