"""Transactional write operations for loans.

Views should not mutate `Loan` instances directly beyond calling these
services: this is where domain invariants are enforced as the final
authority (forms give friendly, early feedback, but these functions are
what actually gets to write to the database).
"""

from django.db import transaction

from .domain import validate_loan_amount_and_currency_change
from .models import Loan


def create_loan(*, owner, cleaned_data):
    loan = Loan(owner=owner, **cleaned_data)
    loan.save()
    return loan


@transaction.atomic
def update_loan(*, loan, cleaned_data):
    """Update a loan, re-checking invariants on a locked, fresh copy.

    Locking the row before validating means a currency change or amount
    reduction that raced against a just-registered payment is caught
    inside the same transaction, not just in the form's earlier read.
    """
    locked_loan = Loan.objects.select_for_update().get(pk=loan.pk)

    validate_loan_amount_and_currency_change(
        locked_loan,
        new_amount=cleaned_data["amount"],
        new_currency=cleaned_data["currency"],
    )

    for field, value in cleaned_data.items():
        setattr(locked_loan, field, value)
    locked_loan.save()
    locked_loan.recompute_status()
    return locked_loan
