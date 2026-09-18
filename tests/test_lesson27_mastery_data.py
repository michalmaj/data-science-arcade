from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l27_causality_courtroom.mastery_data import (
    generate_express_shipping_data,
    group_gap_mirror_code,
    repeat_purchase_rate,
)


def test_dataset_matches_its_own_schema():
    dtesting.assert_matches_schema(generate_express_shipping_data())


def test_naive_gap_is_37_points():
    dataset = generate_express_shipping_data()
    gap = repeat_purchase_rate(dataset, "opt_in") - repeat_purchase_rate(dataset, "non_opt_in")
    assert round(gap, 2) == 0.37


def test_randomized_gap_is_5_points():
    dataset = generate_express_shipping_data()
    gap = repeat_purchase_rate(dataset, "randomized_treatment") - repeat_purchase_rate(dataset, "randomized_control")
    assert round(gap, 2) == 0.05


def test_mirror_code_matches_the_naive_gap_exactly():
    dataset = generate_express_shipping_data()
    expected = repeat_purchase_rate(dataset, "opt_in") - repeat_purchase_rate(dataset, "non_opt_in")
    namespace = {"express_shipping": dataset.frame}
    exec(group_gap_mirror_code("express_shipping", "opt_in", "non_opt_in", "gap"), namespace)
    assert namespace["gap"] == expected


def test_mirror_code_matches_the_randomized_gap_exactly():
    dataset = generate_express_shipping_data()
    expected = repeat_purchase_rate(dataset, "randomized_treatment") - repeat_purchase_rate(dataset, "randomized_control")
    namespace = {"express_shipping": dataset.frame}
    exec(group_gap_mirror_code("express_shipping", "randomized_treatment", "randomized_control", "gap"), namespace)
    assert namespace["gap"] == expected
