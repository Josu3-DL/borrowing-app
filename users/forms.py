from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from borrowing_app.form_fields import PhoneField

from .domain import validate_email_is_available
from .models import User


class RegistrationForm(UserCreationForm):
    phone = PhoneField(label="Teléfono", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Ej. juanperez",
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "nombre@ejemplo.com",
            "phone": "Ej. 8888-8888",
            "password1": "••••••••",
            "password2": "••••••••",
        }
        autocomplete = {
            "username": "username",
            "first_name": "given-name",
            "last_name": "family-name",
            "email": "email",
            "phone": "tel",
            "password1": "new-password",
            "password2": "new-password",
        }
        for field_name, field in self.fields.items():
            if field_name == "phone":
                continue
            field.widget.attrs.update(
                {
                    "placeholder": placeholders.get(field_name, ""),
                    "autocomplete": autocomplete.get(field_name, ""),
                }
            )
        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
            "phone": "Teléfono",
        }

    def clean_email(self):
        return validate_email_is_available(self.cleaned_data["email"])


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "placeholder": "Tu nombre de usuario",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "••••••••",
            }
        ),
    )


class ProfileForm(forms.ModelForm):
    phone = PhoneField(label="Teléfono", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        autocomplete = {
            "username": "username",
            "first_name": "given-name",
            "last_name": "family-name",
            "email": "email",
            "phone": "tel",
        }
        for field_name, field in self.fields.items():
            if field_name == "phone":
                continue
            field.widget.attrs["autocomplete"] = autocomplete[field_name]
        self.fields["username"].help_text = ""

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
            "phone": "Teléfono",
        }

    def clean_email(self):
        return validate_email_is_available(
            self.cleaned_data["email"], exclude_pk=self.instance.pk
        )
