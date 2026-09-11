import pandas as pd

from data_science_arcade.lessons.l16_metric_forge import data as d


def _pct(value: float) -> float:
    return round(value * 100, 1)


def test_honest_baseline_at_full_maturity_agrees_across_every_definition():
    frame = d.honest_tickets()
    as_of = d.mature_snapshot(frame)
    assert _pct(d.definition_a_rate(frame, as_of)) == 82.0
    assert _pct(d.definition_b_rate(frame, as_of)) == 82.0
    assert _pct(d.durable_resolution_rate(frame, as_of)) == 82.0
    assert _pct(d.reopen_rate(frame, as_of)) == 0.0
    assert _pct(d.aged_backlog_rate(frame, as_of)) == 0.0


def test_early_snapshot_shows_the_same_metric_name_giving_two_real_numbers():
    # Zero gaming involved - the exact same honest population, two
    # structurally different but both-legitimate denominator choices.
    frame = d.honest_tickets()
    as_of = d.early_snapshot(frame)
    assert _pct(d.definition_a_rate(frame, as_of)) == 82.0
    assert _pct(d.definition_b_rate(frame, as_of)) == 86.7
    assert d.definition_a_rate(frame, as_of) != d.definition_b_rate(frame, as_of)


def test_stress_test_a_close_fast_inflates_both_definitions_identically():
    frame = d.honest_tickets()
    stressed = d.apply_stress_test_a(frame)
    as_of = d.mature_snapshot(frame)
    assert _pct(d.definition_a_rate(stressed, as_of)) == 96.0
    assert _pct(d.definition_b_rate(stressed, as_of)) == 96.0
    # The real signal: durable resolution barely moves, reopen rate spikes.
    assert _pct(d.durable_resolution_rate(stressed, as_of)) == 84.8
    assert _pct(d.reopen_rate(stressed, as_of)) == 11.2


def test_stress_test_b_leave_open_only_fools_the_closed_only_definition():
    frame = d.honest_tickets()
    stressed = d.apply_stress_test_b(frame)
    as_of = d.mature_snapshot(frame)
    # Definition A's own population denominator is structurally immune.
    assert _pct(d.definition_a_rate(stressed, as_of)) == 82.0
    assert _pct(d.definition_b_rate(stressed, as_of)) == 95.3
    assert _pct(d.durable_resolution_rate(stressed, as_of)) == 82.0
    assert _pct(d.aged_backlog_rate(stressed, as_of)) == 14.0


def test_durable_resolution_rate_resists_both_real_stress_tests():
    frame = d.honest_tickets()
    as_of = d.mature_snapshot(frame)
    a_after = _pct(d.durable_resolution_rate(d.apply_stress_test_a(frame), as_of))
    b_after = _pct(d.durable_resolution_rate(d.apply_stress_test_b(frame), as_of))
    honest = _pct(d.durable_resolution_rate(frame, as_of))
    assert abs(a_after - honest) < 3.0  # a real, small move - not the headline's fake +14pp
    assert b_after == honest  # exactly flat


def test_both_stress_tests_manipulate_the_same_real_70_ticket_subset():
    # Independent re-simulations from the same honest baseline, not a
    # shared timeline - confirmed by checking the actual affected rows.
    frame = d.honest_tickets()
    stressed_a = d.apply_stress_test_a(frame)
    stressed_b = d.apply_stress_test_b(frame)
    changed_a = frame.loc[frame["closed_at"] != stressed_a["closed_at"], "ticket_id"]
    changed_b = frame.loc[frame["closed_at"] != stressed_b["closed_at"], "ticket_id"]
    assert len(changed_a) == d.STRESS_SUBSET_SIZE
    assert len(changed_b) == d.STRESS_SUBSET_SIZE
    assert set(changed_a) == set(changed_b)


def test_mature_mask_excludes_tickets_that_havent_had_their_full_reopen_window():
    frame = d.honest_tickets()
    as_of = d.early_snapshot(frame)
    mask = d.mature_mask(frame, as_of)
    assert mask.sum() < len(frame)
    immature = frame.loc[~mask & (frame["opened_at"] <= as_of)]
    assert (immature["opened_at"] > as_of - pd.Timedelta(days=7)).all()


def test_honest_picker_productivity_is_real_and_row_level_verified():
    honest = d.generate_honest_picks()
    assert round(d.picks_per_hour(honest), 1) == 28.2
    assert d.tracked_order_completeness_pct(honest) == 100.0


def test_narrow_optimization_inflates_rate_and_collapses_completeness():
    narrow = d.generate_narrow_picks()
    assert d.picks_per_hour(narrow) == 40.0
    assert d.tracked_order_completeness_pct(narrow) == 0.0
    # Same real labor budget in both scenarios.
    honest = d.generate_honest_picks()
    honest_hours = honest.loc[honest["picked"], "seconds"].sum() / 3600
    narrow_hours = narrow.loc[narrow["picked"], "seconds"].sum() / 3600
    assert round(honest_hours, 1) == round(narrow_hours, 1) == 42.5
