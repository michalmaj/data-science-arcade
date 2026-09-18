from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l29_the_executive_brief.findings_data import (
    generate_findings_data,
    percent_change,
    percent_change_mirror_code,
    point_change,
    point_change_mirror_code,
)


def test_generated_data_matches_its_schema():
    dataset = generate_findings_data()
    dtesting.assert_matches_schema(dataset)


def test_checkout_completion_rose_a_real_four_points():
    dataset = generate_findings_data()
    assert point_change(dataset, "checkout_completion") == 4.0


def test_payment_step_abandonment_dropped_a_real_five_points():
    dataset = generate_findings_data()
    assert point_change(dataset, "payment_step_abandonment") == -5.0


def test_average_order_value_and_return_rate_barely_moved():
    dataset = generate_findings_data()
    assert abs(point_change(dataset, "average_order_value")) < 1.0
    assert abs(point_change(dataset, "return_rate")) < 0.5


def test_the_dramatic_looking_findings_are_real_but_large_swings():
    dataset = generate_findings_data()
    assert round(percent_change(dataset, "social_mentions"), 2) == 3.0  # +300%
    assert round(percent_change(dataset, "stock_price"), 2) == 0.09
    assert round(percent_change(dataset, "support_tickets_confusing_checkout"), 2) == -0.6


def test_the_competitor_finding_shows_a_much_smaller_lift():
    dataset = generate_findings_data()
    competitor_lift = point_change(dataset, "competitor_completion_rate")
    novamart_lift = point_change(dataset, "checkout_completion")
    assert competitor_lift < novamart_lift


def test_point_change_mirror_code_ends_on_a_named_variable_matching_the_real_value():
    dataset = generate_findings_data()
    namespace = {"findings": dataset.frame}
    exec(point_change_mirror_code("checkout_completion", "checkout_completion_change"), namespace)
    assert namespace["checkout_completion_change"] == point_change(dataset, "checkout_completion")


def test_percent_change_mirror_code_ends_on_a_named_variable_matching_the_real_value():
    dataset = generate_findings_data()
    namespace = {"findings": dataset.frame}
    exec(percent_change_mirror_code("support_tickets_confusing_checkout", "support_tickets_change"), namespace)
    assert namespace["support_tickets_change"] == percent_change(dataset, "support_tickets_confusing_checkout")


def test_mirror_code_matches_every_real_finding_in_the_pool_exactly():
    dataset = generate_findings_data()
    namespace_base = {"findings": dataset.frame}
    point_keys = ("checkout_completion", "payment_step_abandonment", "average_order_value", "return_rate", "employee_satisfaction", "competitor_completion_rate")
    percent_keys = ("social_mentions", "stock_price", "support_tickets_confusing_checkout")
    for key in point_keys:
        namespace = dict(namespace_base)
        exec(point_change_mirror_code(key, "x"), namespace)
        assert namespace["x"] == point_change(dataset, key)
    for key in percent_keys:
        namespace = dict(namespace_base)
        exec(percent_change_mirror_code(key, "x"), namespace)
        assert namespace["x"] == percent_change(dataset, key)
