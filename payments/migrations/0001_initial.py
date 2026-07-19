import decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(
                                decimal.Decimal("0.01")
                            )
                        ],
                        verbose_name="monto del abono",
                    ),
                ),
                ("payment_date", models.DateField(verbose_name="fecha de pago")),
                ("notes", models.TextField(blank=True, verbose_name="notas")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="loans.loan",
                        verbose_name="préstamo",
                    ),
                ),
            ],
            options={
                "ordering": ("-payment_date", "-created_at"),
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount__gt", 0)),
                        name="payments_payment_amount_positive",
                    )
                ],
            },
        ),
    ]
