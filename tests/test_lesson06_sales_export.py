import pytest

from data_science_arcade.lessons.l06_schema_repair_shop.sales_export import (
    PRICE_FIXED_SCHEMA,
    RAW_SCHEMA,
    REPAIR_ISSUES,
    generate_sales_export,
)


def _issue(column: str):
    return next(issue for issue in REPAIR_ISSUES if issue.column == column)


def _option(column: str, key: str):
    return next(option for option in _issue(column).options if option.key == key)


def test_the_correct_price_fix_recovers_every_true_value():
    dataset = generate_sales_export()
    fixed = _option("price", "comma_as_decimal").apply(dataset.frame)
    assert list(fixed["price"]) == [19.99, 8.50, 142.00, 24.90, 6.75, 19.99, 45.00, 3.25]


def test_the_thousands_separator_decoy_inflates_comma_formatted_prices():
    dataset = generate_sales_export()
    fixed = _option("price", "comma_as_thousands").apply(dataset.frame)
    # DE/FR rows get badly inflated; US rows (no comma) are untouched
    assert fixed["price"].iloc[0] == 1999.0
    assert fixed["price"].iloc[5] == 19.99


def test_the_leading_digits_decoy_silently_drops_the_cents():
    dataset = generate_sales_export()
    fixed = _option("price", "leading_digits_only").apply(dataset.frame)
    assert fixed["price"].iloc[0] == 19.0  # "19,99" -> 19, not 19.99


def test_the_correct_currency_fix_produces_iso_codes():
    dataset = generate_sales_export()
    fixed = _option("currency", "uppercase").apply(dataset.frame)
    assert set(fixed["currency"]) == {"EUR", "USD"}


@pytest.mark.parametrize("column,decoy_key", [("price", "comma_as_thousands"), ("currency", "first_letter_only")])
def test_decoy_options_do_not_match_the_correct_result(column, decoy_key):
    dataset = generate_sales_export()
    correct_key = REPAIR_ISSUES[0].options[0].key if column == "price" else REPAIR_ISSUES[1].options[0].key
    correct = _option(column, correct_key).apply(dataset.frame)
    decoy = _option(column, decoy_key).apply(dataset.frame)
    assert list(correct[column]) != list(decoy[column])


@pytest.mark.parametrize("issue", list(REPAIR_ISSUES))
def test_every_issue_has_at_least_two_options(issue):
    assert len(issue.options) >= 2


def _column(schema, name: str):
    return next(column for column in schema.columns if column.name == name)


@pytest.mark.parametrize("column_name", ["price", "currency"])
def test_price_and_currency_descriptions_survive_the_post_repair_schema_swap(column_name):
    # Resolving the "price" issue swaps Dataset.schema to PRICE_FIXED_SCHEMA
    # wholesale (RepairIssue.schema_after) - if that schema doesn't carry
    # its own description_key for a column, the SCHEMA tab silently goes
    # blank for that column the instant price is resolved, even though
    # RAW_SCHEMA had real description text for it.
    assert _column(RAW_SCHEMA, column_name).description_key is not None
    assert _column(PRICE_FIXED_SCHEMA, column_name).description_key is not None
