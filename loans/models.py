from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

EXCHANGE_RATE = Decimal("37")  # 1 USD = 37 NIO


class Loan(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PAID = "paid", "Pagado"

    class Currency(models.TextChoices):
        USD = "USD", "Dolar (USD)"
        NIO = "NIO", "Cordoba (NIO)"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loans",
    )
    borrower_name = models.CharField("nombre del prestatario", max_length=150)
    borrower_phone = models.CharField("telefono del prestatario", max_length=30, blank=True)
    borrower_email = models.EmailField("correo del prestatario", blank=True)
    amount = models.DecimalField(
        "monto",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(
        "moneda",
        max_length=3,
        choices=Currency.choices,
        default=Currency.NIO,
    )
    loan_date = models.DateField("fecha del prestamo")
    due_date = models.DateField("fecha de vencimiento")
    status = models.CharField(
        "estado",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-loan_date", "-created_at")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="loans_loan_amount_positive",
            )
        ]

    def __str__(self):
        sym = self.currency_symbol
        return f"{self.borrower_name} - {sym}{self.amount} ({self.get_status_display()})"

    def clean(self):
        super().clean()
        if self.loan_date and self.due_date and self.due_date < self.loan_date:
            raise ValidationError(
                {"due_date": "La fecha de vencimiento no puede ser anterior a la fecha del prestamo."}
            )

    @property
    def currency_symbol(self):
        return "$" if self.currency == self.Currency.USD else "C$"

    @property
    def total_paid(self):
        """Suma de abonos convertidos a la moneda del prestamo."""
        total = Decimal("0")
        for payment in self.payments.all():
            if payment.currency == self.currency:
                total += payment.amount
            elif self.currency == self.Currency.USD and payment.currency == "NIO":
                total += (payment.amount / EXCHANGE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:  # prestamo NIO, pago USD
                total += (payment.amount * EXCHANGE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return total

    @property
    def remaining_balance(self):
        return max(self.amount - self.total_paid, Decimal("0"))

    def sync_status(self):
        """Sincroniza el estado segun los abonos del modulo de pagos."""
        if self.remaining_balance <= 0 and self.status != self.Status.PAID:
            Loan.objects.filter(pk=self.pk).update(status=self.Status.PAID)
            self.status = self.Status.PAID
        elif self.remaining_balance > 0 and self.status == self.Status.PAID:
            Loan.objects.filter(pk=self.pk).update(status=self.Status.PENDING)
            self.status = self.Status.PENDING
