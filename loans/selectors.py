"""Read-only queries for loans: filtering, pagination and per-row flags.

Kept separate from views so `loans/views.py` only has to validate input,
call a selector or service, and render/redirect.
"""

from django.core.paginator import Paginator
from django.utils import timezone

from .models import Loan


def filtered_loans(user, *, filters=None):
    """`filters` is the cleaned_data of a valid LoanFilterForm, or None/empty
    to skip filtering entirely (e.g. the create/update/delete side panels,
    which reuse the loan list but don't apply the querystring filters)."""
    loans = Loan.objects.owned_by(user)
    if not filters:
        return loans

    status = filters.get("status")
    currency = filters.get("currency")
    borrower_name = filters.get("borrower_name")
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")

    if status == "overdue":
        loans = loans.filter(status=Loan.Status.PENDING, due_date__lt=timezone.localdate())
    elif status == Loan.Status.PENDING:
        loans = loans.filter(status=status, due_date__gte=timezone.localdate())
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
    return loans


def paginate_loans(loans, *, page_number, per_page=5):
    """Paginate first, then annotate only the current page's rows.

    `is_overdue` is a presentation flag computed in Python (it depends on
    "today", not something worth a DB round trip), but it's only ever
    computed for the loans actually shown on this page.
    """
    paginator = Paginator(loans, per_page)
    page_obj = paginator.get_page(page_number)
    today = timezone.localdate()
    for loan in page_obj.object_list:
        loan.is_overdue = loan.status == Loan.Status.PENDING and loan.due_date < today
    return paginator, page_obj
