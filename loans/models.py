from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from borrowing_app import money


class LoanQuerySet(models.QuerySet):
    def owned_by(self, user):
        """Central place for per-user isolation of loans."""
        return self.filter(owner=user)


class Loan(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PAID = "paid", "Pagado"

    # Single source of truth for supported currencies lives in borrowing_app.money.
    Currency = money.Currency

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
        help_text="Se calcula automaticamente a partir de los abonos registrados.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LoanQuerySet.as_manager()

    class Meta:
        ordering = ("-loan_date", "-created_at")
        verbose_name = "préstamo"
        verbose_name_plural = "préstamos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="loans_loan_amount_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(due_date__gte=models.F("loan_date")),
                name="loans_loan_due_date_not_before_loan_date",
            ),
            models.CheckConstraint(
                condition=models.Q(currency__in=tuple(Currency.values)),
                name="loans_loan_currency_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=tuple(Status.values)),
                name="loans_loan_status_valid",
            ),
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
        return money.symbol_for(self.currency)

    @property
    def has_payments(self):
        return self.payments.exists()

    @property
    def total_paid(self):
        """Suma de abonos convertidos a la moneda del prestamo."""
        total = Decimal("0")
        for payment in self.payments.all():
            total += money.convert(payment.amount, payment.currency, self.currency)
        return total

    @property
    def remaining_balance(self):
        return max(self.amount - self.total_paid, Decimal("0"))

    def compute_status(self):
        """Estado derivado del saldo restante. No escribe en la base de datos."""
        return self.Status.PAID if self.remaining_balance <= 0 else self.Status.PENDING

    def recompute_status(self):
        """Sincroniza el campo persistido `status` con el estado derivado.

        `status` se mantiene como columna persistida por razones de
        consulta (filtros, indices), pero su unica fuente de verdad es el
        saldo restante. Este metodo es la unica via soportada para
        actualizarlo y debe invocarse dentro de la misma transaccion que
        crea o elimina un abono (ver loans.services / payments.services).
        """
        derived = self.compute_status()
        if derived != self.status:
            Loan.objects.filter(pk=self.pk).update(status=derived)
            self.status = derived
        return self.status
