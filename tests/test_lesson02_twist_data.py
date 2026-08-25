from data_science_arcade.lessons.l02_source_scout.twist_data import (
    BRACKET_SIZE,
    generate_analytics_opt_in,
    opt_in_rate,
)


def test_total_customers_matches_three_brackets():
    dataset = generate_analytics_opt_in()
    assert len(dataset.frame) == 3 * BRACKET_SIZE


def test_overall_opt_in_rate_is_60_percent():
    dataset = generate_analytics_opt_in()
    assert opt_in_rate(dataset, age_bracket=None) == 0.60


def test_young_bracket_opt_in_rate_is_90_percent():
    dataset = generate_analytics_opt_in()
    assert opt_in_rate(dataset, age_bracket="18-34") == 0.90


def test_middle_bracket_opt_in_rate_is_60_percent():
    dataset = generate_analytics_opt_in()
    assert opt_in_rate(dataset, age_bracket="35-54") == 0.60


def test_old_bracket_opt_in_rate_is_30_percent():
    dataset = generate_analytics_opt_in()
    assert opt_in_rate(dataset, age_bracket="55+") == 0.30


def test_the_breakdown_reveals_a_real_skew_not_just_different_numbers():
    dataset = generate_analytics_opt_in()
    young = opt_in_rate(dataset, "18-34")
    old = opt_in_rate(dataset, "55+")
    assert young > old  # the whole pedagogical point: the aggregate hides this
