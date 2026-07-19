import re

from django import forms
from django.utils.html import format_html


PHONE_PREFIXES = (
    ("+505", "🇳🇮 +505"),
    ("+506", "🇨🇷 +506"),
    ("+502", "🇬🇹 +502"),
    ("+504", "🇭🇳 +504"),
    ("+503", "🇸🇻 +503"),
    ("+1", "🇺🇸 +1"),
    ("+52", "🇲🇽 +52"),
    ("+34", "🇪🇸 +34"),
    ("+57", "🇨🇴 +57"),
)


class PhoneWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (
            forms.Select(
                choices=PHONE_PREFIXES,
                attrs={
                    "class": "phone-prefix",
                    "aria-label": "Prefijo internacional",
                    "autocomplete": "tel-country-code",
                },
            ),
            forms.TextInput(
                attrs={
                    "class": "phone-number",
                    "placeholder": "88888888",
                    "inputmode": "numeric",
                    "pattern": "[0-9]*",
                    "maxlength": "15",
                    "autocomplete": "tel-national",
                    "data-numeric-phone": "true",
                }
            ),
        )
        super().__init__(widgets, attrs)

    def render(self, name, value, attrs=None, renderer=None):
        values = (
            list(value)
            if isinstance(value, (list, tuple))
            else self.decompress(value)
        )
        base_attrs = self.build_attrs(self.attrs, attrs)
        rendered_widgets = []

        for index, widget in enumerate(self.widgets):
            widget_attrs = base_attrs.copy()
            if widget_attrs.get("id"):
                widget_attrs["id"] = f"{widget_attrs['id']}_{index}"
            widget_value = values[index] if index < len(values) else None
            rendered_widgets.append(
                widget.render(
                    f"{name}_{index}",
                    widget_value,
                    widget_attrs,
                    renderer,
                )
            )

        return format_html(
            '<div class="phone-control">{}{}</div>',
            *rendered_widgets,
        )

    def decompress(self, value):
        if not value:
            return ["+505", ""]

        normalized = str(value).strip()
        for prefix, _label in PHONE_PREFIXES:
            if normalized.startswith(prefix):
                number = re.sub(r"\D", "", normalized[len(prefix) :])
                return [prefix, number]

        return ["+505", re.sub(r"\D", "", normalized)]


class PhoneField(forms.MultiValueField):
    default_error_messages = {
        "invalid": "Ingresa solo números.",
    }

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", False)
        fields = (
            forms.ChoiceField(choices=PHONE_PREFIXES, required=False),
            forms.RegexField(
                regex=r"^\d+$",
                required=False,
                max_length=15,
                error_messages={"invalid": "Ingresa solo números."},
            ),
        )
        super().__init__(
            fields=fields,
            require_all_fields=False,
            required=required,
            widget=PhoneWidget(),
            *args,
            **kwargs,
        )

    def compress(self, data_list):
        if not data_list or not data_list[1]:
            return ""

        prefix = data_list[0] or "+505"
        return f"{prefix} {data_list[1]}"
