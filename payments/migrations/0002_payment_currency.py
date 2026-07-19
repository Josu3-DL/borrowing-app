from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="currency",
            field=models.CharField(
                choices=[("USD", "Dolar (USD)"), ("NIO", "Cordoba (NIO)")],
                default="NIO",
                max_length=3,
                verbose_name="moneda del abono",
            ),
        ),
    ]
