"""Shared email rules for registration and profile editing.

Both RegistrationForm and ProfileForm need the exact same normalization
and the exact same "this email is taken" friendly message; keeping that
logic here means there's one place to change it.
"""

from django import forms

from .models import User


def normalize_email(email):
    return email.strip().lower()


def validate_email_is_available(email, *, exclude_pk=None):
    """Normalize `email` and raise a friendly ValidationError if another
    user already has it. Returns the normalized email otherwise."""
    normalized = normalize_email(email)
    existing = User.objects.filter(email__iexact=normalized)
    if exclude_pk is not None:
        existing = existing.exclude(pk=exclude_pk)
    if existing.exists():
        raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
    return normalized
