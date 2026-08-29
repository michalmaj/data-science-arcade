from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l29_the_executive_brief.findings_data import generate_findings_data, percent_change, point_change


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
