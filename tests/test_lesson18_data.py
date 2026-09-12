from data_science_arcade.lessons.l18_randomization_control_room import data as d


def _pct(value: float) -> float:
    return round(value * 100, 1)


def test_roster_has_no_outcome_shaped_column_anywhere():
    roster = d.generate_roster().frame
    outcome_like = {"outcome", "converted", "purchase", "repeat_purchase", "checkout_completed", "quick_pay_used"}
    assert not (set(roster.columns) & outcome_like)
    assert len(roster) == 1200


def test_roster_platform_totals_and_parity_construction_reconcile_exactly():
    roster = d.generate_roster().frame
    assert roster["platform"].value_counts().to_dict() == {"android": 720, "ios": 480}

    even = roster[roster["customer_id_num"] % 2 == 0]
    odd = roster[roster["customer_id_num"] % 2 == 1]
    assert len(even) == 600
    assert len(odd) == 600
    assert even["platform"].value_counts().to_dict() == {"ios": 360, "android": 240}
    assert odd["platform"].value_counts().to_dict() == {"android": 480, "ios": 120}


def test_roster_row_order_is_not_a_biased_block_within_a_parity_class():
    roster = d.generate_roster().frame
    even_first_eight = roster[roster["customer_id_num"] % 2 == 0]["platform"].head(8).tolist()
    assert len(set(even_first_eight)) == 2


def test_id_parity_gives_exact_600_600_and_severe_platform_imbalance():
    roster = d.generate_roster().frame
    group = d.execute_design(d.ID_PARITY, roster)
    audit = d.audit_values(roster, group)
    assert audit["n_treatment"] == 600
    assert audit["n_control"] == 600
    assert _pct(audit["ios_share_treatment"]) == 60.0
    assert _pct(audit["ios_share_control"]) == 20.0


def test_simple_random_gives_exact_600_600_with_a_small_realized_imbalance():
    roster = d.generate_roster().frame
    group = d.execute_design(d.SIMPLE_RANDOM, roster)
    audit = d.audit_values(roster, group)
    assert audit["n_treatment"] == 600
    assert audit["n_control"] == 600
    assert _pct(audit["ios_share_treatment"]) == 39.8
    assert _pct(audit["ios_share_control"]) == 40.2
    assert round(audit["avg_tenure_treatment"], 1) == 461.2
    assert round(audit["avg_tenure_control"], 1) == 483.5


def test_stratified_random_gives_exact_platform_balance_but_not_zero_tenure_gap():
    roster = d.generate_roster().frame
    group = d.execute_design(d.STRATIFIED_RANDOM, roster)
    audit = d.audit_values(roster, group)
    assert audit["n_treatment"] == 600
    assert audit["n_control"] == 600
    assert _pct(audit["ios_share_treatment"]) == 40.0
    assert _pct(audit["ios_share_control"]) == 40.0
    # Stratification protects platform specifically - it does not zero
    # every covariate's own realized gap.
    assert round(audit["avg_tenure_treatment"], 1) != round(audit["avg_tenure_control"], 1)


def test_tenure_is_not_a_hidden_alias_of_platform_or_parity():
    roster = d.generate_roster().frame
    ios_mean = roster[roster["platform"] == "ios"]["tenure_days"].mean()
    android_mean = roster[roster["platform"] == "android"]["tenure_days"].mean()
    # A real, independent covariate should land close for both platforms,
    # not be some deterministic function of platform/parity.
    assert abs(ios_mean - android_mean) < 30


def test_stratified_random_platform_pools_reconcile_to_240_360():
    roster = d.generate_roster().frame
    group = d.execute_design(d.STRATIFIED_RANDOM, roster)
    frame = roster.copy()
    frame["group"] = group
    ios_treatment = len(frame[(frame["platform"] == "ios") & (frame["group"] == "treatment")])
    ios_control = len(frame[(frame["platform"] == "ios") & (frame["group"] == "control")])
    android_treatment = len(frame[(frame["platform"] == "android") & (frame["group"] == "treatment")])
    android_control = len(frame[(frame["platform"] == "android") & (frame["group"] == "control")])
    assert ios_treatment == 240
    assert ios_control == 240
    assert android_treatment == 360
    assert android_control == 360


def test_packaging_mastery_dataset_reconciles_to_the_real_verified_numbers():
    frame = d.generate_packaging_experiment()
    assert len(frame) == 900
    audit = d.packaging_audit_values(frame)
    assert audit["n_treatment"] == 450
    assert audit["n_control"] == 450
    assert round(audit["avg_distance_treatment"], 1) == 47.3
    assert round(audit["avg_distance_control"], 1) == 49.5
