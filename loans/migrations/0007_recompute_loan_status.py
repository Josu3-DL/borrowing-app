"""Data migration: recompute Loan.status from recorded payments.

`status` has always been meant to reflect the remaining balance, but it
used to also be directly editable through LoanForm, so some rows may be
out of sync with their actual payments. This is a one-time backfill; from
here on `status` is only ever written by Loan.recompute_status (see
loans.services / payments.services).

Kept deliberately self-contained (no import of application code) since
migrations must keep working even if the app's conversion logic changes
later.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations

EXCHANGE_RATE_USD_TO_NIO = Decimal("37")
TWO_PLACES = Decimal("0.01")


def _convert(amount, from_currency, to_currency):
    amount = Decimal(amount)
    if from_currency == to_currency:
        return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    if from_currency == "USD" and to_currency == "NIO":
        return (amount * EXCHANGE_RATE_USD_TO_NIO).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return (amount / EXCHANGE_RATE_USD_TO_NIO).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def recompute_status(apps, schema_editor):
    Loan = apps.get_model("loans", "Loan")
    Payment = apps.get_model("payments", "Payment")

    for loan in Loan.objects.all():
        total_paid = Decimal("0")
        for payment in Payment.objects.filter(loan_id=loan.pk):
            total_paid += _convert(payment.amount, payment.currency, loan.currency)
        remaining = max(loan.amount - total_paid, Decimal("0"))
        correct_status = "paid" if remaining <= 0 else "pending"
        if loan.status != correct_status:
            loan.status = correct_status
            loan.save(update_fields=["status"])


def noop_reverse(apps, schema_editor):
    """Not reversible: we don't know the pre-migration status values."""


class Migration(migrations.Migration):

    dependencies = [
        ("loans", "0006_loan_domain_constraints"),
        ("payments", "0004_payment_currency_constraint"),
    ]

    operations = [
        migrations.RunPython(recompute_status, noop_reverse),
    ]
