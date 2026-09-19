from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l30_the_data_incident.device_dashboard_data import device_revenue_at, generate_device_dashboard


def test_generated_dashboard_matches_its_schema():
    dataset = generate_device_dashboard()
    dtesting.assert_matches_schema(dataset)


def test_weeks_7_and_8_device_split_matches_finance_company_totals():
    # These are the two weeks the incident actually turns on - they must
    # reconcile exactly with Finance's own company-wide totals used
    # elsewhere (420,000.0 week 7, 344,100.0 week 8), or this "second
    # source" would silently disagree with the first.
    dataset = generate_device_dashboard()
    week_7_total = device_revenue_at(dataset, "mobile", 7) + device_revenue_at(dataset, "desktop", 7)
    week_8_total = device_revenue_at(dataset, "mobile", 8) + device_revenue_at(dataset, "desktop", 8)
    assert week_7_total == 420000.0
    assert week_8_total == 344100.0


def test_weeks_1_through_6_are_computed_not_hand_typed_and_reconcile_too():
    dataset = generate_device_dashboard()
    company_weekly_1_to_6 = (344400.0, 345600.0, 344400.0, 345600.0, 345600.0, 344200.0)
    for week, total in zip(range(1, 7), company_weekly_1_to_6):
        combined = device_revenue_at(dataset, "mobile", week) + device_revenue_at(dataset, "desktop", week)
        assert abs(combined - total) < 0.01


def test_device_split_shows_a_similar_sized_move_both_weeks_unlike_the_regional_cut():
    # The decoy's whole point: by device, both weeks 7-8 look like a
    # roughly proportional, broad move - very different from the regional
    # cut, where the move is concentrated entirely in East.
    dataset = generate_device_dashboard()
    for device in ("mobile", "desktop"):
        week_7 = device_revenue_at(dataset, device, 7)
        week_8 = device_revenue_at(dataset, device, 8)
        change = (week_8 - week_7) / week_7
        assert -0.25 < change < -0.1
