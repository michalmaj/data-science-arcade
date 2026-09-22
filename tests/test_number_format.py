from data_science_arcade.ui.number_format import format_number, format_percent


def test_english_uses_comma_thousands_and_dot_decimal():
    assert format_number(1234.5, "en") == "1,234.50"


def test_polish_uses_space_thousands_and_comma_decimal():
    assert format_number(1234.5, "pl") == "1 234,50"


def test_decimals_can_be_overridden():
    assert format_number(1236.5, "en", decimals=0) == "1,236"
    assert format_number(1236.5, "pl", decimals=0) == "1 236"


def test_small_numbers_have_no_separator_either_way():
    assert format_number(42.0, "en") == "42.00"
    assert format_number(42.0, "pl") == "42,00"


def test_english_percent_uses_a_dot():
    assert format_percent(0.245, "en") == "24.50%"


def test_polish_percent_uses_a_comma():
    assert format_percent(0.245, "pl") == "24,50%"


def test_signed_shows_a_leading_plus_for_positive_values():
    assert format_number(4.5, "en", decimals=1, signed=True) == "+4.5"
    assert format_number(-4.5, "en", decimals=1, signed=True) == "-4.5"
    assert format_percent(0.045, "pl", signed=True) == "+4,50%"
