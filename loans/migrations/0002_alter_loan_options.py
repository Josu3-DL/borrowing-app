from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="loan",
            options={
                "ordering": ("-loan_date", "-created_at"),
                "verbose_name": "préstamo",
                "verbose_name_plural": "préstamos",
            },
        ),
    ]
