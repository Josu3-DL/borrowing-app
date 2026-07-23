from borrowing_app import money


def money_settings(request):
    """Expose the single source of truth for the exchange rate to every
    template, so JavaScript never has to hardcode the value 37 again."""
    return {"EXCHANGE_RATE": money.EXCHANGE_RATE_USD_TO_NIO}
