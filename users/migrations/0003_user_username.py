import django.contrib.auth.validators
from django.db import migrations, models


def populate_usernames(apps, schema_editor):
    User = apps.get_model("users", "User")
    used = set()

    for user in User.objects.order_by("pk"):
        base = (user.email.split("@", 1)[0] or f"usuario-{user.pk}")[:140]
        candidate = base
        suffix = 1

        while candidate in used or User.objects.filter(username=candidate).exists():
            candidate = f"{base[:140]}-{suffix}"
            suffix += 1

        user.username = candidate
        user.save(update_fields=["username"])
        used.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_users_user_email_ci_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="username",
            field=models.CharField(
                blank=True,
                max_length=150,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_usernames,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                error_messages={
                    "unique": "A user with that username already exists."
                },
                help_text=(
                    "Required. 150 characters or fewer. "
                    "Letters, digits and @/./+/-/_ only."
                ),
                max_length=150,
                unique=True,
                validators=[
                    django.contrib.auth.validators.UnicodeUsernameValidator()
                ],
                verbose_name="username",
            ),
        ),
        migrations.AlterModelOptions(
            name="user",
            options={
                "ordering": ("username",),
                "verbose_name": "usuario",
                "verbose_name_plural": "usuarios",
            },
        ),
    ]
