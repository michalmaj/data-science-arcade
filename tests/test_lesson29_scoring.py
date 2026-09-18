from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l29_the_executive_brief.definition import LESSON_29
from data_science_arcade.lessons.l29_the_executive_brief.findings import CORRECT_FINDING_KEYS, ON_TOPIC_FINDING_KEYS
from data_science_arcade.lessons.l29_the_executive_brief.scoring import LessonTwentyNineResult, score_lesson_twenty_nine

GOOD_SHORTLIST = tuple(ON_TOPIC_FINDING_KEYS)
GOOD_CITED = frozenset(CORRECT_FINDING_KEYS)
GOOD_DECISION = {
    "lead_finding": "checkout_completion",
    "supporting_chart": "checkout_completion_over_time",
    "confidence_level": "high_sustained_with_consistent_evidence",
    "recommendation": "keep_and_monitor_returns",
    "caveats": "competitor_redesigned_too",
}


def _result(**overrides) -> LessonTwentyNineResult:
    defaults = dict(
        shortlist_choices=GOOD_SHORTLIST,
        cited_finding_keys=GOOD_CITED,
        decision=dict(GOOD_DECISION),
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyNineResult(**defaults)


def _scores(result: LessonTwentyNineResult) -> dict:
    return score_lesson_twenty_nine(result, LESSON_29, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.REASONING] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.COMMUNICATION] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_scoring_dimensions_are_exactly_four_no_method():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.COMMUNICATION, ScoreDimension.OVERCONFIDENCE}


def test_independence_case_a_calibration_only():
    """Everything correct except confidence_level overclaims -> only
    OVERCONFIDENCE drops."""
    result = _result(decision={**GOOD_DECISION, "confidence_level": "very_high_a_clear_triumph"})
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.COMMUNICATION] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0


def test_independence_case_b_communication_only_wrong_lead():
    """Evidence/reasoning/confidence correct, but the wrong lead is
    promoted (with a chart that still matches that wrong lead, so only
    the lead-correctness check fails, not the chart-consistency one) ->
    only COMMUNICATION drops."""
    result = _result(
        decision={
            **GOOD_DECISION,
            "lead_finding": "order_value_and_returns_steady",
            "supporting_chart": "order_value_and_returns_steady_over_time",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.COMMUNICATION] == 65.0  # 2 of 3 (lead wrong)


def test_independence_case_b_communication_only_mismatched_chart():
    """Correct lead, but a chart that doesn't match it -> only
    COMMUNICATION drops, proving the chart check is a real consistency
    check and not a restatement of the lead check."""
    result = _result(decision={**GOOD_DECISION, "supporting_chart": "social_mentions_over_time"})
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.COMMUNICATION] == 65.0  # 2 of 3 (chart mismatched)


def test_independence_case_c_evidence_only():
    """Shortlist/recommendation/lead/chart/caveat/confidence all correct,
    but the final citation swaps the true guardrail finding for the
    real-but-lower-priority support_tickets fact -> only EVIDENCE drops."""
    cited = frozenset({"checkout_completion", "payment_step_abandonment", "support_tickets_confusing_checkout"})
    result = _result(cited_finding_keys=cited)
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 92.0
    assert scores[ScoreDimension.COMMUNICATION] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 65.0  # 2 of 3


def test_independence_case_d_reasoning_only_wrong_recommendation():
    """Shortlist/citation/lead/chart/caveat/confidence all correct, but
    the recommendation doesn't follow from the evidence -> only REASONING
    drops."""
    result = _result(decision={**GOOD_DECISION, "recommendation": "revert_immediately"})
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.COMMUNICATION] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.REASONING] == 50.0  # 1 of 2


def test_independence_case_d_reasoning_only_bad_shortlist():
    """Citation/lead/chart/caveat/confidence/recommendation all correct,
    but the shortlist itself let a dramatic-unrelated finding through ->
    only REASONING drops (the other check, recommendation, still passes)."""
    bad_shortlist = tuple((ON_TOPIC_FINDING_KEYS - {"competitor_completion_rate"}) | {"stock_price"})
    result = _result(shortlist_choices=bad_shortlist)
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.COMMUNICATION] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.REASONING] == 50.0  # 1 of 2


def test_evidence_scored_from_final_citation_independent_of_shortlist_correctness():
    """A bad shortlist doesn't automatically fail EVIDENCE if the final
    citation still happens to be the true headline set - proves the two
    cuts are genuinely decoupled, not the same judgment scored twice."""
    bad_shortlist = tuple((ON_TOPIC_FINDING_KEYS - {"competitor_completion_rate"}) | {"stock_price"})
    result = _result(shortlist_choices=bad_shortlist, cited_finding_keys=GOOD_CITED)
    assert _scores(result)[ScoreDimension.EVIDENCE] == 95.0


def test_mastery_requires_both_the_metric_and_claim_checks():
    partial = _result(
        mastery_engaged=True,
        mastery_result={"mastery_which_metric_actually_mattered": "session_length_directly_relevant_to_engagement_question"},
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_which_metric_actually_mattered": "session_length_directly_relevant_to_engagement_question",
            "mastery_strongest_claim": "a_real_but_modest_engagement_gain",
        },
    )
    evaluation_partial = score_lesson_twenty_nine(partial, LESSON_29, hints_used=0)
    evaluation_complete = score_lesson_twenty_nine(complete, LESSON_29, hints_used=0)

    mastery_key = "lesson.l29.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]
