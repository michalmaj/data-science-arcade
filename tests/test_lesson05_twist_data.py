from data_science_arcade.lessons.l05_sampling_mission.twist_data import (
    RURAL_SYNCED_OK,
    RURAL_SYNCED_PROBLEM,
    TOTAL_POPULATION,
    TOTAL_PROBLEMS,
    TRUE_PROBLEM_RATE,
    _interleaved_outcomes,
    draw_sample,
    estimated_problem_rate,
    frame_for,
    generate_population,
    region_availability,
    round1_mechanism,
    rural_share,
    sample_dataset,
)


def _population():
    return generate_population().frame


def test_population_totals_match_the_hand_verified_table():
    population = _population()
    assert len(population) == TOTAL_POPULATION == 960
    assert int(population["had_problem"].sum()) == TOTAL_PROBLEMS == 131
    assert abs(TRUE_PROBLEM_RATE - 131 / 960) < 1e-9
    for region, expected in {"metro": 400, "suburban": 300, "coastal": 180, "rural": 80}.items():
        assert int((population["region"] == region).sum()) == expected


def test_region_partner_assignment_is_real_not_arbitrary():
    population = _population()
    assert set(population.loc[population["region"] == "rural", "partner"].unique()) == {"quickship"}
    for region in ("metro", "suburban", "coastal"):
        assert set(population.loc[population["region"] == region, "partner"].unique()) == {"carrierco"}


def test_tracking_export_frame_matches_the_hand_verified_table():
    frame = frame_for(_population(), "tracking_export")
    assert len(frame) == 895
    assert int(frame["had_problem"].sum()) == 108
    rural_rows = frame[frame["region"] == "rural"]
    assert len(rural_rows) == RURAL_SYNCED_PROBLEM + RURAL_SYNCED_OK == 15
    assert int(rural_rows["had_problem"].sum()) == RURAL_SYNCED_PROBLEM == 5


def test_support_tickets_frame_matches_the_hand_verified_table():
    frame = frame_for(_population(), "support_tickets")
    assert len(frame) == 172
    assert int(frame["had_problem"].sum()) == 119


def test_loyalty_app_frame_matches_the_hand_verified_table():
    frame = frame_for(_population(), "loyalty_app")
    assert len(frame) == 275
    assert int(frame["had_problem"].sum()) == 13


def test_the_three_frames_are_genuinely_different_bias_directions():
    population = _population()
    tracking_rate = estimated_problem_rate(frame_for(population, "tracking_export"))
    ticket_rate = estimated_problem_rate(frame_for(population, "support_tickets"))
    loyalty_rate = estimated_problem_rate(frame_for(population, "loyalty_app"))

    assert ticket_rate > TRUE_PROBLEM_RATE * 4  # dramatically overstates
    assert loyalty_rate < TRUE_PROBLEM_RATE / 2  # dramatically understates
    assert abs(tracking_rate - TRUE_PROBLEM_RATE) < 0.03  # close, not exact


def test_convenience_on_tracking_export_lands_entirely_in_metro():
    frame = frame_for(_population(), "tracking_export")
    sample = draw_sample(frame, "convenience", budget=80, costed=True)

    assert len(sample) == 80
    assert set(sample["region"].unique()) == {"metro"}


def test_convenience_on_a_self_reported_frame_uses_the_whole_free_list():
    population = _population()
    tickets = frame_for(population, "support_tickets")
    sample = draw_sample(tickets, "convenience", budget=80, costed=False)

    assert len(sample) == len(tickets) == 172  # bigger than the audit budget, and free


def test_simple_random_draw_is_deterministic_per_seed():
    frame = frame_for(_population(), "tracking_export")
    first = draw_sample(frame, "simple_random", budget=80, costed=True, seed=5)
    second = draw_sample(frame, "simple_random", budget=80, costed=True, seed=5)

    assert list(first["delivery_id"]) == list(second["delivery_id"])
    assert len(first) == 80


def test_two_different_seeds_give_two_different_rural_representations():
    # The exact pair scenario.py actually uses for Reveals 2/3 (SRS_SEED_A/
    # SRS_SEED_B) - hand-verified via a scratchpad script before being
    # locked into content: seed 2 draws 0 of the 15 real Rural-synced
    # rows, seed 29 draws 4 of them.
    frame = frame_for(_population(), "tracking_export")
    draw_a = draw_sample(frame, "simple_random", budget=80, costed=True, seed=2)
    draw_b = draw_sample(frame, "simple_random", budget=80, costed=True, seed=29)

    assert int((draw_a["region"] == "rural").sum()) == 0
    assert int((draw_b["region"] == "rural").sum()) == 4
    assert estimated_problem_rate(draw_a) != estimated_problem_rate(draw_b)


def test_stratified_draw_respects_the_given_allocation_exactly():
    frame = frame_for(_population(), "tracking_export")
    allocation = {"metro": 25, "suburban": 20, "coastal": 20, "rural": 15}
    sample = draw_sample(frame, "stratified", budget=80, costed=True, seed=1, allocation=allocation)

    assert len(sample) == 80
    assert sample["region"].value_counts().to_dict() == allocation


def test_stratified_draw_deliberately_over_covers_rural_relative_to_its_frame_share():
    frame = frame_for(_population(), "tracking_export")
    # Rural is only 15/895 (~1.7%) of the frame - a deliberate allocation
    # of 15/80 (~18.75%) is a real, large over-representation relative to
    # its own frame share, which is the entire point of stratifying.
    allocation = {"metro": 25, "suburban": 20, "coastal": 20, "rural": 15}
    sample = draw_sample(frame, "stratified", budget=80, costed=True, seed=1, allocation=allocation)

    assert rural_share(sample) > 15 / 895 * 5


def test_region_availability_reflects_the_real_frame_specific_counts():
    population = _population()
    assert region_availability(frame_for(population, "tracking_export")) == {
        "metro": 400,
        "suburban": 300,
        "coastal": 180,
        "rural": 15,
    }
    assert region_availability(frame_for(population, "loyalty_app")) == {
        "metro": 200,
        "suburban": 50,
        "coastal": 20,
        "rural": 5,
    }


def test_round1_mechanism_covers_all_nine_real_frame_strategy_combinations():
    for frame_key in ("support_tickets", "loyalty_app"):
        for strategy_key in ("convenience", "simple_random", "stratified"):
            assert round1_mechanism(frame_key, strategy_key) == "self_selection"
    assert round1_mechanism("tracking_export", "convenience") == "draw_order_bias"
    assert round1_mechanism("tracking_export", "simple_random") == "frame_coverage_gap"
    assert round1_mechanism("tracking_export", "stratified") == "frame_coverage_gap"


def test_express_deliveries_have_a_real_rate_bump_over_their_own_region():
    population = _population()
    for region in ("metro", "suburban", "coastal", "rural"):
        region_frame = population[population["region"] == region]
        express = region_frame[region_frame["is_express"]]
        assert len(express) > 0
        assert express["had_problem"].mean() > region_frame["had_problem"].mean()


def test_sample_dataset_wraps_a_drawn_sample_without_a_schema_mismatch():
    frame = frame_for(_population(), "tracking_export")
    sample = draw_sample(frame, "simple_random", budget=80, costed=True, seed=1)

    dataset = sample_dataset(sample, "audit_sample", "sample = frame.sample(n=80, random_state=1)")

    assert len(dataset.frame) == 80
    assert dataset.python_mirror() == "sample = frame.sample(n=80, random_state=1)"


# --- Follow-up: the weighted, CarrierCo-scoped estimator (P0) -------------


def test_interleaved_outcomes_produces_exactly_the_requested_counts():
    for problem_count, ok_count in ((40, 360), (28, 52), (0, 10), (10, 0), (1, 1), (3, 7)):
        outcomes = _interleaved_outcomes(problem_count, ok_count)
        assert len(outcomes) == problem_count + ok_count
        assert sum(outcomes) == problem_count


def test_interleaved_outcomes_spreads_problems_instead_of_grouping_them():
    # Metro's own real shape (40 problem / 360 ok, an exact 1-in-10 ratio) -
    # every contiguous run of 10 should contain exactly 1 problem, not all
    # 40 problems bunched at the front.
    outcomes = _interleaved_outcomes(40, 360)
    for start in range(0, 400, 10):
        assert sum(outcomes[start : start + 10]) == 1


def test_convenience_on_tracking_export_reflects_metros_true_rate_not_an_artifact():
    # Regression: before the row-interleaving fix, "first 80 rows" grabbed
    # every one of Metro's 40 real problem rows plus only 40 of its 360 ok
    # rows (rows were generated problem-block-then-ok-block), giving a
    # wildly wrong 50% instead of Metro's real 10%.
    frame = frame_for(_population(), "tracking_export")
    sample = draw_sample(frame, "convenience", budget=80, costed=True)

    assert set(sample["region"].unique()) == {"metro"}
    assert estimated_problem_rate(sample) == 0.10


def test_estimated_problem_rate_excludes_rural_from_the_headline_number():
    population = _population()
    frame = frame_for(population, "tracking_export")
    sample = draw_sample(frame, "simple_random", budget=80, costed=True, seed=29)  # has 4 real rural rows
    assert int((sample["region"] == "rural").sum()) == 4

    carrierco_only = sample[sample["region"] != "rural"]
    assert estimated_problem_rate(sample) == carrierco_only["had_problem"].mean()


def test_stratified_estimate_is_weighted_by_frame_share_not_by_how_much_was_drawn():
    # The P0: a plain sample.mean() lets whichever CarrierCo region the
    # student chose to over-allocate dominate the headline number by
    # however much of it they drew, not by its real frame share. Coastal
    # is deliberately over-allocated here (55 of 65 CarrierCo slots, vs a
    # real ~20% frame share) - the weighted estimate must correct back
    # toward the true CarrierCo rate, not follow Coastal's own higher rate.
    population = _population()
    frame = frame_for(population, "tracking_export")
    true_carrierco_rate = population[population["region"] != "rural"]["had_problem"].mean()
    allocation = {"metro": 5, "suburban": 5, "coastal": 55, "rural": 15}
    sample = draw_sample(frame, "stratified", budget=80, costed=True, seed=1, allocation=allocation)

    carrierco_sample = sample[sample["region"] != "rural"]
    plain_mean = carrierco_sample["had_problem"].mean()
    weighted = estimated_problem_rate(sample, frame=frame)

    assert abs(weighted - true_carrierco_rate) < abs(plain_mean - true_carrierco_rate)


def test_stratified_estimate_without_a_frame_argument_falls_back_to_plain_mean():
    # A caller that forgets to pass `frame` for a stratified draw gets the
    # old (wrong-for-uneven-allocations) behavior, not a crash - documented
    # here so the fallback is a deliberate, tested choice.
    frame = frame_for(_population(), "tracking_export")
    allocation = {"metro": 5, "suburban": 5, "coastal": 55, "rural": 15}
    sample = draw_sample(frame, "stratified", budget=80, costed=True, seed=1, allocation=allocation)

    carrierco_sample = sample[sample["region"] != "rural"]
    assert estimated_problem_rate(sample) == carrierco_sample["had_problem"].mean()
