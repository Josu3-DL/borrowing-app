from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0002_payment"),
    ]

    operations = [
        migrations.AddField(
            model_name="loan",
            name="currency",
            field=models.CharField(
                choices=[("USD", "Dolar (USD)"), ("NIO", "Cordoba (NIO)")],
                default="NIO",
                max_length=3,
                verbose_name="moneda",
            ),
        ),
    ]
