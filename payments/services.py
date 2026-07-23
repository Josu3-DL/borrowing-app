"""Transactional write operations for payments.

Views should not create or delete `Payment` rows directly: this is where
the loan is locked and the overpay / already-paid rules are re-checked as
the final authority, so two concurrent submissions against the same loan
can't both slip through.
"""

from django.db import transaction

from loans.domain import validate_payment_amount
from loans.models import Loan

from .models import Payment


@transaction.atomic
def create_payment(*, user, cleaned_data):
    loan = Loan.objects.select_for_update().get(
        pk=cleaned_data["loan"].pk, owner=user
    )
    amount = cleaned_data["amount"]
    currency = cleaned_data["currency"]

    validate_payment_amount(loan, amount, currency)

    payment = Payment.objects.create(
        loan=loan,
        amount=amount,
        currency=currency,
        payment_date=cleaned_data["payment_date"],
        notes=cleaned_data.get("notes", ""),
    )
    loan.recompute_status()
    return payment


@transaction.atomic
def delete_payment(*, user, payment):
    loan = Loan.objects.select_for_update().get(pk=payment.loan_id, owner=user)
    payment.delete()
    loan.recompute_status()
    return loan
