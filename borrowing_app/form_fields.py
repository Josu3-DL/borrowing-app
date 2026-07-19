import re

from django import forms
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.html import format_html_join


PHONE_COUNTRIES = (
    ("NI", "Nicaragua", "+505"),
    ("CR", "Costa Rica", "+506"),
    ("GT", "Guatemala", "+502"),
    ("HN", "Honduras", "+504"),
    ("SV", "El Salvador", "+503"),
    ("BZ", "Belice", "+501"),
    ("PA", "Panamá", "+507"),
    ("US", "Estados Unidos", "+1"),
    ("MX", "México", "+52"),
    ("CU", "Cuba", "+53"),
    ("AR", "Argentina", "+54"),
    ("BR", "Brasil", "+55"),
    ("CL", "Chile", "+56"),
    ("CO", "Colombia", "+57"),
    ("VE", "Venezuela", "+58"),
    ("BO", "Bolivia", "+591"),
    ("GY", "Guyana", "+592"),
    ("EC", "Ecuador", "+593"),
    ("GF", "Guayana Francesa", "+594"),
    ("SR", "Surinam", "+597"),
    ("UY", "Uruguay", "+598"),
    ("CW", "Curazao", "+599"),
    ("PE", "Perú", "+51"),
    ("HT", "Haití", "+509"),
    ("DO", "República Dominicana", "+1809"),
    ("PR", "Puerto Rico", "+1787"),
    ("ES", "España", "+34"),
    ("PT", "Portugal", "+351"),
    ("FR", "Francia", "+33"),
    ("GB", "Reino Unido", "+44"),
    ("DE", "Alemania", "+49"),
    ("IT", "Italia", "+39"),
    ("NL", "Países Bajos", "+31"),
    ("BE", "Bélgica", "+32"),
    ("CH", "Suiza", "+41"),
    ("AT", "Austria", "+43"),
    ("IE", "Irlanda", "+353"),
    ("DK", "Dinamarca", "+45"),
    ("SE", "Suecia", "+46"),
    ("NO", "Noruega", "+47"),
    ("PL", "Polonia", "+48"),
    ("UA", "Ucrania", "+380"),
    ("TR", "Turquía", "+90"),
    ("CN", "China", "+86"),
    ("JP", "Japón", "+81"),
    ("KR", "Corea del Sur", "+82"),
    ("IN", "India", "+91"),
    ("PK", "Pakistán", "+92"),
    ("PH", "Filipinas", "+63"),
    ("ID", "Indonesia", "+62"),
    ("AU", "Australia", "+61"),
    ("NZ", "Nueva Zelanda", "+64"),
    ("ZA", "Sudáfrica", "+27"),
    ("NG", "Nigeria", "+234"),
    ("EG", "Egipto", "+20"),
    ("MA", "Marruecos", "+212"),
    ("AE", "Emiratos Árabes Unidos", "+971"),
    ("IL", "Israel", "+972"),
)

PHONE_PREFIXES = tuple(
    (prefix, f"{country_name} ({country_code}) {prefix}")
    for country_code, country_name, prefix in PHONE_COUNTRIES
)
PHONE_COUNTRY_BY_PREFIX = {
    prefix: (country_code, country_name)
    for country_code, country_name, prefix in PHONE_COUNTRIES
}


class PhoneWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (
            forms.Select(
                choices=PHONE_PREFIXES,
                attrs={
                    "class": "phone-prefix-native",
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
        base_id = base_attrs.get("id", f"id_{name}")
        selected_prefix = values[0] if values and values[0] else "+505"
        selected_code, selected_name = PHONE_COUNTRY_BY_PREFIX.get(
            selected_prefix, ("NI", "Nicaragua")
        )

        select_attrs = base_attrs.copy()
        select_attrs.update(
            {
                "id": f"{base_id}_0_native",
                "class": "phone-prefix-native",
                "tabindex": "-1",
                "aria-hidden": "true",
            }
        )
        rendered_select = self.widgets[0].render(
            f"{name}_0",
            selected_prefix,
            select_attrs,
            renderer,
        )

        number_attrs = base_attrs.copy()
        number_attrs["id"] = f"{base_id}_1"
        rendered_number = self.widgets[1].render(
            f"{name}_1",
            values[1] if len(values) > 1 else None,
            number_attrs,
            renderer,
        )

        options = format_html_join(
            "",
            (
                '<li role="option" aria-selected="{}" data-phone-option '
                'data-value="{}" data-search="{} {} {}">'
                '<button type="button" tabindex="-1">'
                '<img src="{}" alt="" width="24" height="18">'
                '<span class="phone-country-name">{}</span>'
                '<span class="phone-country-code">{}</span>'
                '<span class="phone-dial-code">{}</span>'
                "</button></li>"
            ),
            (
                (
                    "true" if prefix == selected_prefix else "false",
                    prefix,
                    country_name,
                    country_code,
                    prefix,
                    static(f"vendor/flags/{country_code.lower()}.svg"),
                    country_name,
                    country_code,
                    prefix,
                )
                for country_code, country_name, prefix in PHONE_COUNTRIES
            ),
        )

        return format_html(
            '<div class="phone-control">'
            '<div class="phone-country-select" data-phone-country-select>'
            '<button id="{}_0" class="phone-prefix-trigger" type="button" '
            'aria-haspopup="listbox" aria-expanded="false" '
            'aria-label="Prefijo internacional: {}, {}">'
            '<img src="{}" alt="" width="24" height="18">'
            '<span class="phone-trigger-code">{}</span>'
            '<span class="phone-trigger-prefix">{}</span>'
            '<span class="phone-trigger-chevron" aria-hidden="true"></span>'
            "</button>"
            '<div class="phone-prefix-popover" hidden>'
            '<div class="phone-prefix-search-wrap">'
            '<span class="phone-search-icon" aria-hidden="true"></span>'
            '<input class="phone-prefix-search" type="search" '
            'placeholder="Buscar país o prefijo" aria-label="Buscar país o prefijo" '
            'autocomplete="off">'
            "</div>"
            '<ul class="phone-prefix-options" role="listbox" '
            'aria-label="Prefijos internacionales">{}</ul>'
            '<p class="phone-prefix-empty" hidden>No se encontraron países.</p>'
            "</div>{}</div>{}</div>",
            base_id,
            selected_name,
            selected_prefix,
            static(f"vendor/flags/{selected_code.lower()}.svg"),
            selected_code,
            selected_prefix,
            options,
            rendered_select,
            rendered_number,
        )

    def decompress(self, value):
        if not value:
            return ["+505", ""]

        normalized = str(value).strip()
        for prefix, _label in sorted(
            PHONE_PREFIXES, key=lambda choice: len(choice[0]), reverse=True
        ):
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
