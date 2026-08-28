import pytest

from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l21_funnel_factory.checkout_events import build_funnel_definition, generate_checkout_events
from data_science_arcade.ui.funnel_chart import step_percent


def test_generated_data_matches_its_schema():
    dataset = generate_checkout_events()
    dtesting.assert_matches_schema(dataset)


def test_the_flawed_legacy_tracking_makes_cart_look_like_the_worst_step():
    dataset = generate_checkout_events()
    definition = build_funnel_definition(dataset, "legacy_cart_tracking", "k", "l")
    # product_view -> add_to_cart
    assert round(step_percent(definition.steps, 2, "previous"), 3) == 0.256
    # this definition's own add_to_cart -> checkout_started then looks
    # implausibly efficient - the tell that something's wrong with it
    assert step_percent(definition.steps, 3, "previous") > 0.85


def test_the_complete_tracking_shows_checkout_as_the_real_worst_step():
    dataset = generate_checkout_events()
    definition = build_funnel_definition(dataset, "complete_cart_tracking", "k", "l")
    drops = [1 - step_percent(definition.steps, i, "previous") for i in range(1, len(definition.steps))]
    worst_step_index = 1 + drops.index(max(drops))
    assert definition.steps[worst_step_index].key == "checkout_started"


def test_raw_event_counting_makes_the_real_bottleneck_look_even_worse():
    dataset = generate_checkout_events()
    complete = build_funnel_definition(dataset, "complete_cart_tracking", "k", "l")
    raw = build_funnel_definition(dataset, "raw_cart_events", "k", "l")
    complete_conversion = step_percent(complete.steps, 3, "previous")
    raw_conversion = step_percent(raw.steps, 3, "previous")
    assert raw_conversion < complete_conversion


def test_percent_basis_top_makes_every_later_step_look_worse_in_isolation():
    dataset = generate_checkout_events()
    previous_basis = build_funnel_definition(dataset, "complete_cart_tracking", "k", "l", percent_basis="previous")
    top_basis = build_funnel_definition(dataset, "complete_cart_tracking", "k", "l", percent_basis="top")
    # Same underlying counts either way - only the displayed % changes.
    assert previous_basis.steps == top_basis.steps
    checkout_index = 3
    assert step_percent(top_basis.steps, checkout_index, "top") < step_percent(previous_basis.steps, checkout_index, "previous")


@pytest.mark.parametrize("definition_key", ["legacy_cart_tracking", "complete_cart_tracking", "raw_cart_events"])
def test_every_definition_has_all_five_steps_in_order(definition_key):
    dataset = generate_checkout_events()
    definition = build_funnel_definition(dataset, definition_key, "k", "l")
    assert [step.key for step in definition.steps] == [
        "site_visit",
        "product_view",
        "add_to_cart",
        "checkout_started",
        "order_confirmed",
    ]
