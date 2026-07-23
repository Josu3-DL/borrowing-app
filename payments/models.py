from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from borrowing_app import money


class PaymentQuerySet(models.QuerySet):
    def owned_by(self, user):
        """Central place for per-user isolation of payments (via their loan)."""
        return self.filter(loan__owner=user)


class Payment(models.Model):
    # Single source of truth for supported currencies lives in borrowing_app.money.
    Currency = money.Currency

    loan = models.ForeignKey(
        "loans.Loan",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="prestamo",
    )
    amount = models.DecimalField(
        "monto del abono",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(
        "moneda del abono",
        max_length=3,
        choices=Currency.choices,
        default=Currency.NIO,
    )
    payment_date = models.DateField("fecha de pago")
    notes = models.TextField("notas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PaymentQuerySet.as_manager()

    class Meta:
        ordering = ("-payment_date", "-created_at")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payments_payment_amount_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(currency__in=tuple(Currency.values)),
                name="payments_payment_currency_valid",
            ),
        ]

    def __str__(self):
        sym = self.currency_symbol
        return f"Abono {sym}{self.amount} ({self.currency}) -> {self.loan.borrower_name} ({self.payment_date})"

    @property
    def currency_symbol(self):
        return money.symbol_for(self.currency)
