import pandas as pd
import pytest

from data_science_arcade.lessons.l21_funnel_factory.checkout_events import funnel_mirror_code, generate_checkout_events
from data_science_arcade.lessons.l21_funnel_factory.requests import (
    COMPLETE_CART_TRACKING,
    LEGACY_CART_TRACKING,
    PERCENT_OF_PREVIOUS_STEP,
    PERCENT_OF_TOTAL_VISITS,
    RAW_CART_EVENTS,
)


def _pct(value: float) -> float:
    return round(value * 100, 1)


def _exec_mirror(definition, var_name: str) -> pd.DataFrame:
    checkout_events = generate_checkout_events().frame
    namespace: dict = {"checkout_events": checkout_events, "pd": pd}
    exec(funnel_mirror_code(definition, var_name), namespace)
    return namespace[var_name]


@pytest.mark.parametrize(
    "definition,expected_pct",
    [
        (LEGACY_CART_TRACKING, 25.6),
        (COMPLETE_CART_TRACKING, 59.8),
        (RAW_CART_EVENTS, 89.0),
    ],
)
def test_add_to_cart_previous_basis_reconciles_to_the_real_verified_numbers(definition, expected_pct):
    frame = _exec_mirror(definition, "definition_check")
    row = frame[frame["step_key"] == "add_to_cart"].iloc[0]
    assert _pct(row["conversion"]) == expected_pct


def test_checkout_started_top_basis_reconciles_to_the_real_verified_number():
    frame = _exec_mirror(PERCENT_OF_TOTAL_VISITS, "basis_check_top")
    row = frame[frame["step_key"] == "checkout_started"].iloc[0]
    assert _pct(row["conversion"]) == 19.0


def test_checkout_started_previous_basis_reconciles_to_the_real_verified_number():
    frame = _exec_mirror(PERCENT_OF_PREVIOUS_STEP, "basis_check_previous")
    row = frame[frame["step_key"] == "checkout_started"].iloc[0]
    assert _pct(row["conversion"]) == 38.8


def test_neighboring_local_rates_on_the_defended_baseline_reconcile():
    frame = _exec_mirror(PERCENT_OF_PREVIOUS_STEP, "basis_check_previous")
    add_to_cart = frame[frame["step_key"] == "add_to_cart"].iloc[0]
    order_confirmed = frame[frame["step_key"] == "order_confirmed"].iloc[0]
    product_view = frame[frame["step_key"] == "product_view"].iloc[0]
    assert _pct(add_to_cart["conversion"]) == 59.8
    assert _pct(order_confirmed["conversion"]) == 78.9
    assert _pct(product_view["conversion"]) == 82.0
    # checkout_started (38.8%) is the real, uniquely bad local transition
    # only WITHIN this one defended reading - never a cross-definition
    # invariant (see checkout_started's own wildly different reading
    # under legacy=90.5%/raw=26.0% in test_checkout_started_moves_with_definition).
    checkout_started = frame[frame["step_key"] == "checkout_started"].iloc[0]
    assert checkout_started["conversion"] < add_to_cart["conversion"]
    assert checkout_started["conversion"] < order_confirmed["conversion"]
    assert checkout_started["conversion"] < product_view["conversion"]


@pytest.mark.parametrize(
    "definition,expected_pct",
    [
        (LEGACY_CART_TRACKING, 90.5),
        (COMPLETE_CART_TRACKING, 38.8),
        (RAW_CART_EVENTS, 26.0),
    ],
)
def test_checkout_started_moves_with_definition_never_a_stable_cross_definition_number(definition, expected_pct):
    """The corrected central claim: checkout_started's own %-of-previous
    is NOT a definition-independent anomaly - it moves with whatever
    add_to_cart count feeds it, exactly like every other step."""
    frame = _exec_mirror(definition, "moves_check")
    row = frame[frame["step_key"] == "checkout_started"].iloc[0]
    assert _pct(row["conversion"]) == expected_pct


def test_mirror_code_uses_a_real_distinct_variable_name_never_a_bare_expression():
    code = funnel_mirror_code(COMPLETE_CART_TRACKING, "mobile_dropout_funnel")
    assert code.startswith("mobile_dropout_funnel = (")
    assert 'mobile_dropout_funnel["conversion"]' in code


def test_top_basis_and_previous_basis_produce_genuinely_different_code():
    top_code = funnel_mirror_code(PERCENT_OF_TOTAL_VISITS, "x")
    previous_code = funnel_mirror_code(PERCENT_OF_PREVIOUS_STEP, "x")
    assert "iloc[0]" in top_code
    assert "shift(1)" in previous_code
    assert top_code != previous_code
