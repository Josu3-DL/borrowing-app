"""Read-only queries for payments: filtering, pagination and monthly totals."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.paginator import Paginator

from borrowing_app import money
from loans.models import Loan

from .models import Payment


def filtered_payments(user, *, filters=None):
    payments = Payment.objects.owned_by(user).select_related("loan").prefetch_related(
        "loan__payments"
    )
    if not filters:
        return payments

    borrower_name = filters.get("borrower_name")
    currency = filters.get("currency")
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")

    if borrower_name:
        payments = payments.filter(loan__borrower_name__icontains=borrower_name)
    if currency:
        payments = payments.filter(currency=currency)
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    return payments


def _payment_row(payment):
    names = payment.loan.borrower_name.split()
    initials = "".join(name[0] for name in names[:2]).upper()
    return {
        "payment": payment,
        "initials": initials,
        "amount": money.format_money(payment.amount, payment.currency),
        "amount_value": payment.amount,
        "amount_currency": payment.currency,
        "balance": money.format_money(payment.loan.remaining_balance, payment.loan.currency),
        "balance_value": payment.loan.remaining_balance,
        "balance_currency": payment.loan.currency,
        "completed": payment.loan.status == Loan.Status.PAID,
    }


def paginate_payment_rows(payments, *, page_number, per_page=8):
    """Paginate the queryset first, then build presentation rows only for
    the current page (instead of materializing every matching payment)."""
    paginator = Paginator(payments, per_page)
    page_obj = paginator.get_page(page_number)
    page_obj.object_list = [_payment_row(payment) for payment in page_obj.object_list]
    return paginator, page_obj


def monthly_collected_totals(user, *, today, currency=Payment.Currency.USD):
    """Total collected this month and last month, converted to `currency`.

    Only loads payments from the start of last month onward instead of
    the user's entire payment history.
    """
    current_month_start = date(today.year, today.month, 1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = date(previous_month_end.year, previous_month_end.month, 1)

    recent_payments = Payment.objects.owned_by(user).filter(
        payment_date__gte=previous_month_start
    )

    current_total = Decimal("0")
    previous_total = Decimal("0")
    for payment in recent_payments:
        converted = money.convert(payment.amount, payment.currency, currency)
        if payment.payment_date >= current_month_start:
            current_total += converted
        else:
            previous_total += converted
    return current_total, previous_total


def person_choices(user):
    return (
        Loan.objects.owned_by(user)
        .order_by("borrower_name")
        .values_list("borrower_name", flat=True)
        .distinct()
    )


def loan_status_counts(user, *, today):
    owner_loans = Loan.objects.owned_by(user)
    return {
        "pending_count": owner_loans.filter(status=Loan.Status.PENDING).count(),
        "overdue_count": owner_loans.filter(
            status=Loan.Status.PENDING, due_date__lt=today
        ).count(),
    }
