"""Domain rules for loans and the payments applied to them.

These functions are the single source of truth for the invariants of the
lending domain. Forms call them for friendly, early feedback; the
transactional services in `loans.services` and `payments.services` call
them again as the final authority right before writing, inside a locked
transaction, so the rule always holds regardless of the entry point
(view, admin, shell, concurrent request).
"""

from django.core.exceptions import ValidationError

from borrowing_app import money


def ensure_currency_unchanged_after_payments(loan, new_currency):
    """A loan with at least one recorded payment cannot change currency."""
    if loan.pk and loan.has_payments and new_currency != loan.currency:
        raise ValidationError(
            {
                "currency": (
                    "No se puede cambiar la moneda de un prestamo que ya "
                    "tiene abonos registrados."
                )
            }
        )


def ensure_amount_not_below_paid(loan, new_amount):
    """A loan's amount cannot be reduced below what has already been paid."""
    if loan.pk:
        total_paid = loan.total_paid
        if new_amount < total_paid:
            raise ValidationError(
                {
                    "amount": (
                        "El monto no puede ser menor a lo ya abonado "
                        f"({loan.currency_symbol}{total_paid})."
                    )
                }
            )


def validate_loan_amount_and_currency_change(loan, *, new_amount, new_currency):
    """Run every invariant that applies to editing an existing loan."""
    ensure_currency_unchanged_after_payments(loan, new_currency)
    ensure_amount_not_below_paid(loan, new_amount)


def validate_payment_amount(loan, amount, currency):
    """Ensure a payment can be applied to `loan`.

    Returns the payment amount converted to the loan's currency so callers
    can reuse it without recomputing the conversion.
    """
    if loan.status == loan.Status.PAID:
        raise ValidationError(
            f"El prestamo de {loan.borrower_name} ya esta completamente "
            "pagado. No se pueden registrar mas abonos."
        )

    amount_in_loan_currency = money.convert(amount, currency, loan.currency)
    balance = loan.remaining_balance
    if amount_in_loan_currency > balance:
        sym = loan.currency_symbol
        pay_sym = money.symbol_for(currency)
        raise ValidationError(
            f"El abono de {pay_sym}{amount} {currency} equivale a "
            f"{sym}{amount_in_loan_currency} {loan.currency}, "
            f"pero el saldo restante es solo {sym}{balance} {loan.currency}."
        )
    return amount_in_loan_currency
