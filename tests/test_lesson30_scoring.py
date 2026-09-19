from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l30_the_data_incident.definition import LESSON_30
from data_science_arcade.lessons.l30_the_data_incident.scoring import LessonThirtyResult, score_lesson_thirty
from data_science_arcade.workbench.context import EvidenceItem

# "Strong" evidence: the 3 correct-variant slots (regional_cut left on
# by_region, baseline_check left on vs_own_baseline, promo_context/
# redesign_weak_correlation which have no wrong variant). Evidence keys
# are STABLE per lead slot (correction #26) - correctness is read from
# the matching `*_choice` field on the Result, not from the key itself,
# so every test that uses this fixture must also set those choice fields
# to the correct value, or the role won't count as gathered.
_STRONG_EVIDENCE = (
    EvidenceItem(id="e1", label_key="x", key="regional_cut"),
    EvidenceItem(id="e2", label_key="x", key="baseline_check"),
    EvidenceItem(id="e3", label_key="x", key="promo_context"),
    EvidenceItem(id="e4", label_key="x", key="redesign_weak_correlation"),
)


def _result(**overrides) -> LessonThirtyResult:
    defaults = dict(
        leads_investigated=frozenset(),
        gathered_evidence=(),
        regional_cut_choice=None,
        baseline_check_choice=None,
        checkout_health_choice=None,
        dedup_choice=None,
        promo_verdict_choice=None,
        redesign_verdict_choice=None,
        monitoring_choice=None,
        dashboard_choice=None,
        decision={},
    )
    defaults.update(overrides)
    return LessonThirtyResult(**defaults)


def _strong_result(**overrides) -> LessonThirtyResult:
    """A full strong-path result: correct regional_cut/baseline_check
    choices backing the `_STRONG_EVIDENCE` fixture's keys, plus a correct
    decision. Callers override only what they want to vary."""
    defaults = dict(
        gathered_evidence=_STRONG_EVIDENCE,
        regional_cut_choice="by_region",
        baseline_check_choice="vs_own_baseline",
        decision=dict(_STRONG_DECISION_BASE),
    )
    defaults.update(overrides)
    return _result(**defaults)


def _score(result: LessonThirtyResult):
    evaluation = score_lesson_thirty(result, LESSON_30, hints_used=0)
    return evaluation.dimension_scores, {obs.text_key for obs in evaluation.observations}


_STRONG_DECISION_BASE = {
    "what_happened": "east_promo_reverted",
    "supporting_evidence": ("e1", "e3", "e4"),
    "root_cause_confidence": "high_but_bounded",
    "remaining_uncertainties": ("promo_causal_lift_unknown",),
    "business_impact": "no_ongoing_loss_reversion",
    "recommended_action": "do_not_revert_measure_separately",
    "follow_up_measurement": "design_promo_incrementality_check",
}


def test_lucky_guess_with_no_evidence_is_not_rewarded():
    # P0 (correction #1): a strong claim with zero gathered evidence must
    # never score well just because it happens to match authorial truth.
    result = _result(decision={**_STRONG_DECISION_BASE, "supporting_evidence": ()})
    scores, observations = _score(result)
    assert scores[ScoreDimension.REASONING] <= 20.0
    assert scores[ScoreDimension.EVIDENCE] <= 15.0
    assert "lesson.l30.feedback.claim_outruns_evidence" in observations


def test_scenario_a_good_method_bad_interpretation():
    result = _strong_result(
        dedup_choice="dedupe_by_redemption_id",
        decision={
            **_STRONG_DECISION_BASE,
            "what_happened": "redesign_broke_checkout",
            "supporting_evidence": (),
            "recommended_action": "revert_redesign",
            "business_impact": "severe_ongoing_loss",
        },
    )
    scores, _ = _score(result)
    assert scores[ScoreDimension.METHOD] >= 90.0
    assert scores[ScoreDimension.REASONING] <= 20.0


def test_scenario_b_good_interpretation_weak_citation():
    result = _strong_result(decision={**_STRONG_DECISION_BASE, "supporting_evidence": ("e1",)})
    scores, _ = _score(result)
    assert scores[ScoreDimension.REASONING] >= 90.0
    assert scores[ScoreDimension.EVIDENCE] <= 35.0


def test_scenario_c_evidence_correct_overclaim_only_hurts_overconfidence():
    result = _strong_result(decision={**_STRONG_DECISION_BASE, "root_cause_confidence": "certain_promo_caused_exact_uplift"})
    scores, _ = _score(result)
    assert scores[ScoreDimension.REASONING] >= 90.0
    assert scores[ScoreDimension.EVIDENCE] >= 90.0
    assert scores[ScoreDimension.OVERCONFIDENCE] <= 25.0


def test_scenario_d_calibrated_strength_wrong_unknown():
    result = _strong_result(decision={**_STRONG_DECISION_BASE, "remaining_uncertainties": ("nothing_left_uncertain",)})
    scores, _ = _score(result)
    assert scores[ScoreDimension.UNCERTAINTY] <= 20.0
    assert scores[ScoreDimension.OVERCONFIDENCE] >= 90.0


def test_scenario_e_coherent_analysis_incoherent_report():
    result = _strong_result(decision={**_STRONG_DECISION_BASE, "recommended_action": "revert_redesign"})
    scores, _ = _score(result)
    assert scores[ScoreDimension.REASONING] >= 90.0
    assert scores[ScoreDimension.COMMUNICATION] <= 65.0


def test_scenario_f_weak_investigation_calibrated_restraint_scores_well_on_reasoning():
    # The single most important regression: skipping the critical leads
    # must not force a low REASONING/OVERCONFIDENCE score if the student
    # honestly admits insufficiency instead of guessing.
    weak_evidence = (EvidenceItem(id="e1", label_key="x", key="regional_cut"),)
    result = _result(
        gathered_evidence=weak_evidence,
        regional_cut_choice="by_device",  # visited, but left on the wrong (decoy) variant
        decision={
            "what_happened": "insufficient_evidence_investigate_further",
            "supporting_evidence": ("e1",),
            "root_cause_confidence": "low_too_early",
            "remaining_uncertainties": ("promo_causal_lift_unknown", "redesign_not_fully_checked"),
            "business_impact": "unclear_insufficient_investigation",
            "recommended_action": "investigate_before_deciding",
            "follow_up_measurement": "design_promo_incrementality_check",
        },
    )
    scores, _ = _score(result)
    assert scores[ScoreDimension.METHOD] <= 60.0
    assert scores[ScoreDimension.EVIDENCE] <= 80.0
    assert scores[ScoreDimension.REASONING] >= 90.0
    assert scores[ScoreDimension.OVERCONFIDENCE] >= 90.0


def test_scenario_g_raw_count_instead_of_dedup_only_hurts_method():
    result = _strong_result(dedup_choice="count_every_log_row", decision=dict(_STRONG_DECISION_BASE))
    scores, _ = _score(result)
    assert scores[ScoreDimension.METHOD] < 90.0
    assert scores[ScoreDimension.REASONING] >= 90.0


def test_method_never_rewards_opening_more_leads_on_its_own():
    # Correction #14: METHOD must grade quality of choices, never lead
    # count - a student who investigated fewer leads but chose well on
    # every one of them should score at least as well as one who
    # investigated more but chose no better proportionally.
    fewer_but_correct = _result(regional_cut_choice="by_region", baseline_check_choice="vs_own_baseline")
    more_but_same_ratio = _result(
        regional_cut_choice="by_region",
        baseline_check_choice="vs_own_baseline",
        dedup_choice="dedupe_by_redemption_id",
        dashboard_choice="zero_based_bar",
    )
    scores_fewer, _ = _score(fewer_but_correct)
    scores_more, _ = _score(more_but_same_ratio)
    assert scores_fewer[ScoreDimension.METHOD] == scores_more[ScoreDimension.METHOD]


def test_reopening_a_slot_and_leaving_it_on_the_wrong_variant_does_not_count_the_role():
    # The evidence key ("regional_cut") is still present after reopening,
    # but the FINAL choice is the decoy - licensing must reflect the real
    # current state, not the mere existence of a same-named evidence item.
    evidence = (EvidenceItem(id="e1", label_key="x", key="regional_cut"),)
    result = _result(
        gathered_evidence=evidence,
        regional_cut_choice="by_device",  # left on the decoy after reopening
        decision={**_STRONG_DECISION_BASE, "supporting_evidence": ("e1",)},
    )
    scores, _ = _score(result)
    assert scores[ScoreDimension.REASONING] <= 20.0  # claim_outruns_evidence - baseline role isn't actually satisfied


def test_redesign_ruled_out_only_via_correlation_still_licenses_the_strong_claim_conditionally():
    evidence = (
        EvidenceItem(id="e1", label_key="x", key="regional_cut"),
        EvidenceItem(id="e2", label_key="x", key="promo_context"),
    )
    result = _result(
        gathered_evidence=evidence,
        regional_cut_choice="by_region",
        decision={**_STRONG_DECISION_BASE, "supporting_evidence": ("e1", "e2")},
    )
    scores, observations = _score(result)
    assert scores[ScoreDimension.REASONING] >= 90.0
    # redesign was never checked - the honest uncertainty list must say so
    assert result.decision["remaining_uncertainties"] == ("promo_causal_lift_unknown",)
    assert "lesson.l30.feedback.uncertainty_missed_expected" in observations
