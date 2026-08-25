from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import (
    correctly_dated_rate,
    generate_date_parse_results,
)


def test_every_us_order_parses_correctly_under_the_global_rule():
    dataset = generate_date_parse_results()
    assert correctly_dated_rate(dataset, "US") == 1.0


def test_every_de_order_is_silently_misdated():
    dataset = generate_date_parse_results()
    assert correctly_dated_rate(dataset, "DE") == 0.0


def test_overall_rate_is_dragged_down_by_the_misdated_market():
    dataset = generate_date_parse_results()
    assert correctly_dated_rate(dataset) == 0.8


def test_total_order_count_is_one_hundred_fifty():
    dataset = generate_date_parse_results()
    assert len(dataset.frame) == 150
