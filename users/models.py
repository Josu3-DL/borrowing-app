from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from .managers import UserManager


class User(AbstractUser):
    email = models.EmailField("correo electrónico", unique=True)
    phone = models.CharField("teléfono", max_length=20, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        ordering = ("username",)
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="users_user_email_ci_unique",
            )
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        super().save(*args, **kwargs)
