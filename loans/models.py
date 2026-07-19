from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Loan(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PAID = "paid", "Pagado"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loans",
    )
    borrower_name = models.CharField("nombre del prestatario", max_length=150)
    borrower_phone = models.CharField(
        "teléfono del prestatario",
        max_length=30,
        blank=True,
    )
    borrower_email = models.EmailField("correo del prestatario", blank=True)
    amount = models.DecimalField(
        "monto",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    loan_date = models.DateField("fecha del préstamo")
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
        verbose_name = "préstamo"
        verbose_name_plural = "préstamos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="loans_loan_amount_positive",
            )
        ]

    def __str__(self):
        return f"{self.borrower_name} - {self.amount} ({self.get_status_display()})"

    def clean(self):
        super().clean()
        if self.loan_date and self.due_date and self.due_date < self.loan_date:
            raise ValidationError(
                {"due_date": "La fecha de vencimiento no puede ser anterior a la fecha del préstamo."}
            )
