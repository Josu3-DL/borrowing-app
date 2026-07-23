"""Shared monetary core.

Single source of truth for supported currencies, the fixed exchange rate,
rounding policy, and money formatting. No Django app should duplicate this
logic; import from here instead.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.db import models

# 1 USD = 37 NIO. Fixed rate, not stored per payment (see AGENTS.md / README
# for the product rationale: the app does not track historical rates).
EXCHANGE_RATE_USD_TO_NIO = Decimal("37")

# Precision used for every monetary value in the system.
TWO_PLACES = Decimal("0.01")


class Currency(models.TextChoices):
    USD = "USD", "Dolar (USD)"
    NIO = "NIO", "Cordoba (NIO)"


CURRENCY_SYMBOLS = {
    Currency.USD: "$",
    Currency.NIO: "C$",
}


def quantize(amount):
    """Round a Decimal-compatible amount to two decimal places (half up)."""
    return Decimal(amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def convert(amount, from_currency, to_currency):
    """Convert an amount between supported currencies, rounded to 2 places.

    Preserves the historical behaviour of the app: same currency is just
    quantized, USD -> NIO multiplies by the fixed rate, NIO -> USD divides.
    """
    amount = Decimal(amount)
    if from_currency == to_currency:
        return quantize(amount)
    if from_currency == Currency.USD and to_currency == Currency.NIO:
        return quantize(amount * EXCHANGE_RATE_USD_TO_NIO)
    if from_currency == Currency.NIO and to_currency == Currency.USD:
        return quantize(amount / EXCHANGE_RATE_USD_TO_NIO)
    raise ValueError(f"Moneda no admitida: {from_currency!r} -> {to_currency!r}")


def symbol_for(currency):
    try:
        return CURRENCY_SYMBOLS[currency]
    except KeyError as exc:
        raise ValueError(f"Moneda no admitida: {currency!r}") from exc


def format_money(amount, currency):
    """Format an amount with its currency symbol, e.g. 'C$1,234.56'."""
    return f"{symbol_for(currency)}{quantize(amount):,.2f}"
