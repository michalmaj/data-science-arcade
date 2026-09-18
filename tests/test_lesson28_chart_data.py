from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.framework.chart import chart_render_range
from data_science_arcade.lessons.l28_chart_crime_lab.chart_data import (
    chart_pick_mirror_code,
    fair_rate_minimum_quarter_number,
    fair_return_rate,
    flawed_rate_minimum_quarter_number,
    flawed_return_rate,
    generate_active_users_data,
    generate_returns_data,
    generate_satisfaction_data,
    rate_minimum_quarter_mirror_code,
    visual_amplification_mirror_code,
    visual_amplification_ratio,
    window_percent_change,
    window_percent_change_mirror_code,
)


def test_all_three_datasets_match_their_schema():
    for dataset in (generate_satisfaction_data(), generate_active_users_data(), generate_returns_data()):
        dtesting.assert_matches_schema(dataset)


def test_satisfaction_shows_a_real_modest_improvement():
    dataset = generate_satisfaction_data()
    scores = list(dataset.frame["satisfaction_score"])
    assert scores == [72.0, 73.0, 74.0, 75.0]


def test_active_users_decline_through_most_of_the_year_then_recover():
    dataset = generate_active_users_data()
    frame = dataset.frame.sort_values("month_index")
    values = list(frame["active_users"])
    assert values[9] < values[0]  # October is well below January - a real decline
    assert values[-1] > values[-2]  # December is above November - a real late recovery


def test_fair_return_rate_is_meaningfully_larger_than_the_flawed_one():
    dataset = generate_returns_data()
    for quarter in ("Q1", "Q2", "Q3", "Q4"):
        fair = fair_return_rate(dataset, quarter)
        flawed = flawed_return_rate(dataset, quarter)
        assert fair > 0.10
        assert flawed < 0.01
        assert fair > flawed * 10


def test_chart_render_range_matches_the_documented_zoomed_and_zero_based_formulas():
    values = (72.0, 73.0, 74.0, 75.0)
    assert chart_render_range("bar", "zoomed", values) == (72.0 * 0.9, 75.0 * 1.05)
    assert chart_render_range("bar", "zero_based", values) == (0.0, 75.0 * 1.15)
    assert chart_render_range("line", "zoomed", values) == (0.0, 75.0 * 1.15)  # scale ignored for line


def test_visual_amplification_ratio_is_about_six_times():
    values = (72.0, 73.0, 74.0, 75.0)
    ratio = visual_amplification_ratio(values)
    assert round(ratio, 2) == 6.18


def test_visual_amplification_mirror_code_matches_the_real_ratio_exactly():
    dataset = generate_satisfaction_data()
    values = tuple(float(v) for v in dataset.frame["satisfaction_score"])
    expected = visual_amplification_ratio(values)
    namespace = {"satisfaction": dataset.frame}
    exec(visual_amplification_mirror_code("satisfaction", "satisfaction_score", "amp"), namespace)
    assert namespace["amp"] == expected


def test_window_percent_change_matches_each_real_window():
    dataset = generate_active_users_data()
    sorted_values = tuple(float(v) for v in dataset.frame.sort_values("month_index")["active_users"])
    assert round(window_percent_change(sorted_values), 4) == 0.02
    assert round(window_percent_change(sorted_values[-2:]), 4) == 0.0851
    assert round(window_percent_change(sorted_values[:2]), 4) == -0.02


def test_window_percent_change_mirror_code_matches_each_real_window_exactly():
    dataset = generate_active_users_data()
    sorted_values = tuple(float(v) for v in dataset.frame.sort_values("month_index")["active_users"])
    for window_expr, values in (("[:]", sorted_values), ("[-2:]", sorted_values[-2:]), ("[:2]", sorted_values[:2])):
        expected = window_percent_change(values)
        namespace = {"active_users": dataset.frame}
        exec(window_percent_change_mirror_code("active_users", "active_users", window_expr, "w"), namespace)
        assert namespace["w"] == expected


def test_fair_rate_minimum_is_q3_flawed_rate_minimum_is_q1():
    dataset = generate_returns_data()
    assert fair_rate_minimum_quarter_number(dataset) == 3.0
    assert flawed_rate_minimum_quarter_number(dataset) == 1.0


def test_rate_minimum_quarter_mirror_code_matches_both_real_minimums_exactly():
    dataset = generate_returns_data()
    namespace_fair = {"returns": dataset.frame}
    exec(rate_minimum_quarter_mirror_code("units_sold", "fm"), namespace_fair)
    assert namespace_fair["fm"] == fair_rate_minimum_quarter_number(dataset)

    namespace_flawed = {"returns": dataset.frame}
    exec(rate_minimum_quarter_mirror_code("total_customers", "flm"), namespace_flawed)
    assert namespace_flawed["flm"] == flawed_rate_minimum_quarter_number(dataset)


def test_chart_pick_mirror_code_matches_the_exact_rendered_series_for_every_option():
    satisfaction = generate_satisfaction_data()
    active_users = generate_active_users_data()
    returns = generate_returns_data()

    for option_key in ("zoomed", "zero_based"):
        namespace = {"satisfaction": satisfaction.frame}
        exec(chart_pick_mirror_code("satisfaction_score_claim", option_key, "x"), namespace)
        assert list(namespace["x"]) == [72.0, 73.0, 74.0, 75.0]

    sorted_values = list(active_users.frame.sort_values("month_index")["active_users"])
    expected_by_option = {"full_year": sorted_values, "last_two_months": sorted_values[-2:], "first_two_months": sorted_values[:2]}
    for option_key, expected in expected_by_option.items():
        namespace = {"active_users": active_users.frame}
        exec(chart_pick_mirror_code("active_users_claim", option_key, "x"), namespace)
        assert list(namespace["x"]) == expected

    namespace = {"returns": returns.frame}
    exec(chart_pick_mirror_code("returns_rate_claim", "per_units_sold", "x"), namespace)
    assert [round(v, 4) for v in namespace["x"]] == [0.15, 0.16, 0.13, 0.17]

    namespace = {"returns": returns.frame}
    exec(chart_pick_mirror_code("returns_rate_claim", "per_customers", "x"), namespace)
    assert [round(v, 4) for v in namespace["x"]] == [0.0054, 0.0064, 0.0057, 0.0082]
