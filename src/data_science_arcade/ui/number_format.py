def format_number(value: float, locale: str, decimals: int = 2, signed: bool = False) -> str:
    """Locale-aware thousands/decimal separator for a dynamically-displayed
    number - EN "1,234.56", PL "1 234,56" (matching the plain-space
    thousands separator already used in this project's own PL locale
    strings, e.g. "10 000"). `signed` always shows a leading +/- (for a
    diff/delta value), matching Python's own `+` format spec. Never use
    this for column names, code identifiers, or a Python Mirror value -
    those must stay exactly as pandas itself would print them, in every
    locale."""
    sign = "+" if signed else ""
    text = f"{value:{sign},.{decimals}f}"
    if locale != "pl":
        return text
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", " ")


def format_percent(fraction: float, locale: str, decimals: int = 2, signed: bool = False) -> str:
    """Same locale-aware formatting as format_number, for a 0-1 fraction
    displayed as a percentage - EN "24.50%", PL "24,50%"."""
    return f"{format_number(fraction * 100, locale, decimals, signed=signed)}%"
