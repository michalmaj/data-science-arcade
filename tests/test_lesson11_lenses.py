import pytest

from data_science_arcade.lessons.l11_distribution_observatory.lenses import CORRECT_OPTION_BY_LENS, build_distribution_lenses
from data_science_arcade.lessons.l11_distribution_observatory.order_values import generate_order_values

LENSES = build_distribution_lenses(generate_order_values())


def test_every_lens_has_a_correct_option_recorded():
    assert {lens.key for lens in LENSES} == set(CORRECT_OPTION_BY_LENS)


def test_all_three_lenses_are_present():
    assert {lens.key for lens in LENSES} == {"single_number_pick", "spread_pick", "shape_pick"}


@pytest.mark.parametrize("lens", list(LENSES))
def test_the_correct_option_is_among_the_offered_options(lens):
    correct = CORRECT_OPTION_BY_LENS[lens.key]
    assert correct in {option.key for option in lens.options}


@pytest.mark.parametrize("lens", list(LENSES))
def test_every_lens_has_at_least_two_options(lens):
    assert len(lens.options) >= 2


def test_correct_option_position_varies_across_lenses():
    # Regression guard for the Lesson 04 bug: ButtonGroup defaults keyboard
    # focus to option index 0, so an answer key always sitting at the same
    # index would be visibly pre-highlighted before the player chooses.
    indexes = []
    for lens in LENSES:
        correct = CORRECT_OPTION_BY_LENS[lens.key]
        indexes.append(next(i for i, option in enumerate(lens.options) if option.key == correct))
    assert len(set(indexes)) > 1


def test_marker_values_are_real_numbers_computed_from_the_dataset_not_hand_picked():
    dataset = generate_order_values()
    values = dataset.frame["order_value"]
    single_number_lens = next(lens for lens in LENSES if lens.key == "single_number_pick")
    mean_option = next(option for option in single_number_lens.options if option.key == "mean")
    median_option = next(option for option in single_number_lens.options if option.key == "median")

    assert mean_option.marker_value == pytest.approx(float(values.mean()))
    assert median_option.marker_value == pytest.approx(float(values.median()))


def test_options_that_deny_variation_or_shape_draw_no_marker():
    spread_lens = next(lens for lens in LENSES if lens.key == "spread_pick")
    assume_consistent = next(option for option in spread_lens.options if option.key == "assume_consistent")
    assert assume_consistent.marker_value is None
