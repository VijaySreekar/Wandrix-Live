def format_currency_amount(amount: float, currency: str | None) -> str:
    code = (currency or "GBP").upper()
    return f"{code} {amount:,.0f}"
