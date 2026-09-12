from data_science_arcade.lessons.l17_hypothesis_detective import data as d


def _pct(value: float) -> float:
    return round(value * 100, 1)


def test_pilot_primary_rates_reconcile_to_the_real_verified_numbers():
    pilot = d.generate_pilot().frame
    assert len(pilot) == 1200
    assert _pct(d.primary_rate(pilot, "control")) == 25.0
    assert _pct(d.primary_rate(pilot, "one_click")) == 26.0


def test_pilot_device_composition_is_identical_across_both_variants():
    pilot = d.generate_pilot().frame
    counts = pilot.groupby(["variant", "device"]).size().unstack()
    assert counts.loc["control", "app"] == counts.loc["one_click", "app"] == 360
    assert counts.loc["control", "web"] == counts.loc["one_click", "web"] == 240


def test_pilot_device_split_rates_reconcile_and_sum_to_the_real_primary_totals():
    pilot = d.generate_pilot().frame
    assert _pct(d.device_rate(pilot, "app", "control")) == 33.3
    assert _pct(d.device_rate(pilot, "app", "one_click")) == 40.0
    assert _pct(d.device_rate(pilot, "web", "control")) == 12.5
    assert _pct(d.device_rate(pilot, "web", "one_click")) == 5.0

    control_repeats = pilot.loc[pilot["variant"] == "control", "repeat_purchase_14d"].sum()
    one_click_repeats = pilot.loc[pilot["variant"] == "one_click", "repeat_purchase_14d"].sum()
    assert control_repeats == 150  # 120 app + 30 web
    assert one_click_repeats == 156  # 144 app + 12 web


def test_deliveries_overall_late_rate_reconciles_to_the_real_verified_numbers():
    deliveries = d.generate_deliveries()
    assert len(deliveries) == 2000
    assert _pct(d.late_rate(deliveries, "before")) == 10.0
    assert _pct(d.late_rate(deliveries, "after")) == 10.5  # a real, small increase - the hypothesis is not borne out


def test_deliveries_route_composition_is_identical_across_both_periods():
    deliveries = d.generate_deliveries()
    counts = deliveries.groupby(["period", "route_type"]).size().unstack()
    assert counts.loc["before", "urban"] == counts.loc["after", "urban"] == 600
    assert counts.loc["before", "rural"] == counts.loc["after", "rural"] == 400


def test_blinded_roster_has_no_outcome_column_and_matches_the_real_roster_rows():
    roster = d.generate_blinded_roster().frame
    assert list(roster.columns) == ["customer_id", "variant", "device"]
    assert "repeat_purchase_14d" not in roster.columns
    assert len(roster) == 1200
    pilot = d.generate_pilot().frame
    assert list(roster["customer_id"]) == list(pilot["customer_id"])


def test_pilot_row_order_is_not_a_biased_block_of_successes_then_failures():
    # The first several rows of any one device/variant slice must not all
    # share the same outcome - a naive "first k rows are True" generator
    # would make even a raw head() preview an unrepresentative sample.
    pilot = d.generate_pilot().frame
    control_app = pilot[(pilot["variant"] == "control") & (pilot["device"] == "app")]
    first_eight = control_app["repeat_purchase_14d"].head(8).tolist()
    assert len(set(first_eight)) == 2


def test_deliveries_route_split_reconciles_to_the_real_verified_numbers():
    deliveries = d.generate_deliveries()
    assert _pct(d.route_late_rate(deliveries, "urban", "before")) == 15.0
    assert _pct(d.route_late_rate(deliveries, "urban", "after")) == 10.0
    assert _pct(d.route_late_rate(deliveries, "rural", "before")) == 2.5
    assert _pct(d.route_late_rate(deliveries, "rural", "after")) == 11.2

    before_late = deliveries.loc[deliveries["period"] == "before", "late"].sum()
    after_late = deliveries.loc[deliveries["period"] == "after", "late"].sum()
    assert before_late == 100  # 90 urban + 10 rural
    assert after_late == 105  # 60 urban + 45 rural
