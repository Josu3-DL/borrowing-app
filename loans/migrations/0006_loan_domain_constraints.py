from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("loans", "0005_merge_20260718_dashboard"),
    ]

    operations = [
        migrations.AlterField(
            model_name="loan",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pendiente"), ("paid", "Pagado")],
                default="pending",
                help_text="Se calcula automaticamente a partir de los abonos registrados.",
                max_length=10,
                verbose_name="estado",
            ),
        ),
        migrations.AddConstraint(
            model_name="loan",
            constraint=models.CheckConstraint(
                condition=models.Q(("due_date__gte", models.F("loan_date"))),
                name="loans_loan_due_date_not_before_loan_date",
            ),
        ),
        migrations.AddConstraint(
            model_name="loan",
            constraint=models.CheckConstraint(
                condition=models.Q(currency__in=("USD", "NIO")),
                name="loans_loan_currency_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="loan",
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=("pending", "paid")),
                name="loans_loan_status_valid",
            ),
        ),
    ]
