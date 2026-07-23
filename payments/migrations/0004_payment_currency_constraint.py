from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0003_alter_payment_loan"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(currency__in=("USD", "NIO")),
                name="payments_payment_currency_valid",
            ),
        ),
    ]
