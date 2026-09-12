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
    assert (immature["opened_at"] > as_of - d.FULL_OBSERVATION_WINDOW).all()


def test_maturity_requires_the_full_resolution_plus_reopen_window_not_just_7_days():
    # Regression: a ticket opened 7 days 12 hours ago that closed at hour
    # 23 has only had ~6.5 real days of its own reopen window observed -
    # counting it mature off "opened >= 7 days ago" alone was a real bug
    # (it could call a ticket durable almost a full day before its own
    # real reopen window had actually elapsed).
    frame = d.honest_tickets()
    as_of = frame["opened_at"].max()
    boundary_open = as_of - pd.Timedelta(days=7, hours=12)
    boundary_row = pd.DataFrame(
        [
            {
                "ticket_id": "T-BOUNDARY",
                "opened_at": boundary_open,
                "closed_at": boundary_open + pd.Timedelta(hours=23),
                "reopened_at": pd.NaT,
            }
        ]
    )
    test_frame = pd.concat([frame, boundary_row], ignore_index=True)
    mask = d.mature_mask(test_frame, as_of)
    assert mask.iloc[-1] == False  # noqa: E712 - opened >7d but <8d ago, not yet eligible

    long_enough_open = as_of - pd.Timedelta(days=8, hours=1)
    mature_row = pd.DataFrame(
        [
            {
                "ticket_id": "T-MATURE",
                "opened_at": long_enough_open,
                "closed_at": long_enough_open + pd.Timedelta(hours=23),
                "reopened_at": pd.NaT,
            }
        ]
    )
    test_frame_2 = pd.concat([frame, mature_row], ignore_index=True)
    mask_2 = d.mature_mask(test_frame_2, as_of)
    assert mask_2.iloc[-1] == True  # noqa: E712 - genuinely opened >= 8 days ago


def test_an_immature_ticket_never_counts_as_a_durable_success_before_its_window_ends():
    # "Not reopened yet" must never silently mean success while a
    # ticket's own real reopen window is still running.
    frame = d.honest_tickets()
    as_of = frame["opened_at"].max()
    boundary_open = as_of - pd.Timedelta(days=7, hours=12)
    boundary_row = pd.DataFrame(
        [{"ticket_id": "T-BOUNDARY", "opened_at": boundary_open, "closed_at": boundary_open + pd.Timedelta(hours=23), "reopened_at": pd.NaT}]
    )
    test_frame = pd.concat([frame, boundary_row], ignore_index=True)

    rate_including_boundary = d.durable_resolution_rate(test_frame, as_of)
    rate_excluding_boundary = d.durable_resolution_rate(frame, as_of)
    assert rate_including_boundary == rate_excluding_boundary  # the immature row contributes to neither side


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
