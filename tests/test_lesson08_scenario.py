import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l08_duplicate_detective.definition import LESSON_08
from data_science_arcade.lessons.l08_duplicate_detective.scenario import (
    AUTOMATIC_REMOVAL_RULE_FIELD,
    CONFLICT_POLICY_FIELD,
    DECISION_FIELDS,
    IDENTITY_KEY_FIELD,
    KPI_RESULT_FIELD,
    LEGITIMATE_REPEATS_FIELD,
    MASTERY_KEY_FIELD,
    MASTERY_PRESERVE_FIELD,
    OBSERVATION_UNIT_FIELD,
    REQUIRED_PREVENTION_FIELD,
    SAFE_CLAIM_FIELD,
    build_lesson_eight_runner,
)
from data_science_arcade.lessons.l08_duplicate_detective.scoring import (
    LessonEightResult,
    _mastery_succeeded,
    score_lesson_eight,
)
from data_science_arcade.lessons.l08_duplicate_detective.twist_data import CORRECT_VERDICT_BY_GROUP, ROUND1_ISSUE, ROUND2_ISSUE
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.duplicate_group_scene import DuplicateGroupScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing

GOOD_ROUND1_RESOLUTION = {"event_id": "remove_exact_repeats_only"}
GOOD_ROUND2_RESOLUTION = {"amount": "quarantine_and_disclose"}
GOOD_GROUP_VERDICTS = dict(CORRECT_VERDICT_BY_GROUP)
GOOD_DECISION = {
    "observation_unit": "paid_orders_with_captured_payment",
    "identity_key": "shared_event_id",
    "automatic_removal_rule": "remove_exact_repeats_only",
    "legitimate_repeats": ("multiple_lifecycle_events", "multiple_payment_attempts", "repeat_purchases"),
    "conflict_policy": "quarantine_and_disclose",
    "kpi_result": "twenty_orders_range_995_to_1000",
    "safe_claim": "twenty_confirmed_range_disclosed",
    "prevention_recommendation": "idempotent_ingestion_and_uniqueness_validation",
}
DECISION_FIELDS_IN_ORDER = (
    OBSERVATION_UNIT_FIELD,
    IDENTITY_KEY_FIELD,
    AUTOMATIC_REMOVAL_RULE_FIELD,
    LEGITIMATE_REPEATS_FIELD,
    CONFLICT_POLICY_FIELD,
    KPI_RESULT_FIELD,
    SAFE_CLAIM_FIELD,
    REQUIRED_PREVENTION_FIELD,
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _leaf_scene(scene):
    """Unwraps nested SequenceScene/OfferThenTaskScene composites down to
    the real leaf scene currently on screen. Interaction itself doesn't
    need this - attribute access already proxies through __getattr__ on
    every wrapper - but isinstance checks do, and OfferThenTaskScene's
    own real `.buttons` attribute (kept alive even once engaged) shadows
    its nested task scene's own `.buttons` via plain attribute lookup, so
    any `.buttons`-touching helper (like _repair_issues) must be pointed
    at the unwrapped leaf, never the wrapper."""
    while isinstance(scene, (SequenceScene, OfferThenTaskScene)):
        active = getattr(scene, "_active", None)
        if active is None:
            break
        scene = active
    return scene


def _play_dialogue_to_the_end(scene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _option_index(field_or_options, option_key: str) -> int:
    options = field_or_options.options if hasattr(field_or_options, "options") else field_or_options
    return next(i for i, option in enumerate(options) if option.key == option_key)


def _answer_inspection(scene: WorkbenchScene, option_key: str) -> None:
    scene.inspection_buttons[option_key].on_activate()
    scene.continue_button.on_activate()


def _fill_single_select(scene: BriefBuilderScene, field, option_key: str) -> None:
    scene.buttons.buttons[_option_index(field, option_key)].on_activate()
    scene.next_button.on_activate()


def _fill_multi_select(scene, field, option_keys) -> None:
    for key in option_keys:
        scene.buttons.buttons[_option_index(field, key)].on_activate()
    scene.next_button.on_activate()


def _first_flagged_cell_button(scene: WorkbenchScene):
    chrome_labels = {scene.app.localization.t(key) for key in ("workbench.data.view_table", "workbench.data.view_schema", "workbench.continue")}
    tab_labels = {scene.app.localization.t(tab.value) for tab in type(scene.active_tab)}
    for button in scene.buttons.buttons:
        if button.label not in chrome_labels and button.label not in tab_labels:
            return button
    raise AssertionError("no flagged cell button found")


def _repair_issues(scene: WorkbenchScene, resolution: dict[str, str]) -> None:
    for _ in scene.issues:
        cell_button = _first_flagged_cell_button(scene)
        cell_button.on_activate()
        assert scene.active_issue is not None
        option_key = resolution[scene.active_issue.column]
        scene.picker_buttons[option_key].on_activate()


def _play_comparison_reveal(scene: ComparisonRevealScene, interpret_key: str) -> None:
    index = _option_index(scene.interpret_options, interpret_key)
    scene.buttons.buttons[index].on_activate()
    scene.continue_button.on_activate()


def _play_duplicate_group_scene(scene: DuplicateGroupScene, verdicts: dict[str, str]) -> None:
    for group in scene.groups:
        verdict_key = verdicts[group.key]
        index = next(i for i, option in enumerate(scene.verdict_options) if option.key == verdict_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, *, decision_keys: dict) -> None:
    for step in scene._steps:
        if step.key == "evidence":
            evidence_ids = list(scene._evidence_toggle_buttons.keys())[: scene.evidence_field.max_count]
            for item_id in evidence_ids:
                scene._evidence_toggle_buttons[item_id].on_activate()
        elif hasattr(step, "min_count"):  # MultiChoiceField
            for key in decision_keys[step.key]:
                index = _option_index(step, key)
                scene.buttons.buttons[index].on_activate()
        else:
            scene.buttons.buttons[_option_index(step, decision_keys[step.key])].on_activate()
        scene.next_button.on_activate()


def _play_lesson_to_feedback(
    app,
    *,
    inspection_option="duplicate_of_what",
    profiling_interpretation="each_number_is_a_different_question",
    round1_resolution=GOOD_ROUND1_RESOLUTION,
    consequence_interpretation="worth_checking_real_payments",
    group_verdicts=GOOD_GROUP_VERDICTS,
    revision_engage: bool = False,
    revised_round1_resolution=None,
    round2_resolution=GOOD_ROUND2_RESOLUTION,
    decision=GOOD_DECISION,
    mastery_engage: bool = False,
    mastery_key_choice="scan_event_id",
    mastery_preserve_selection=("checkpoint_scans", "qc_rescan"),
) -> LessonFeedbackScene:
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # raw inspection
    _answer_inspection(app.scenes.current.inner, inspection_option)

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # profiling reveal
    _play_comparison_reveal(app.scenes.current.inner, profiling_interpretation)

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 1
    _repair_issues(app.scenes.current.inner, round1_resolution)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # consequence reveal
    _play_comparison_reveal(app.scenes.current.inner, consequence_interpretation)

    assert isinstance(app.scenes.current.inner, DuplicateGroupScene)  # group investigation
    _play_duplicate_group_scene(
        app.scenes.current.inner, {key: group_verdicts[key] for key in ("replay_group", "lifecycle_group", "retry_group", "decoy_group")}
    )

    assert isinstance(app.scenes.current.inner, DialogueScene)  # root cause pivot
    _play_dialogue_to_the_end(app.scenes.current)

    assert isinstance(app.scenes.current.inner, DuplicateGroupScene)  # twist conflict
    _play_duplicate_group_scene(app.scenes.current.inner, {"conflict_group": group_verdicts["conflict_group"]})

    offer = _leaf_scene(app.scenes.current.inner)
    assert isinstance(offer, OfferThenTaskScene)  # revision offer
    if revision_engage:
        offer.buttons.buttons[0].on_activate()  # Engage
        leaf = _leaf_scene(offer)
        assert isinstance(leaf, WorkbenchScene)
        assert revised_round1_resolution is not None
        _repair_issues(leaf, revised_round1_resolution)
        leaf.continue_button.on_activate()
    else:
        offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # repair round 2
    _repair_issues(app.scenes.current.inner, round2_resolution)
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # evidence review
    app.scenes.current.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final decision
    _play_decision_builder(app.scenes.current.inner, decision_keys=decision)

    assert isinstance(app.scenes.current.inner, OfferThenTaskScene)  # optional mastery
    mastery_offer = app.scenes.current.inner
    if mastery_engage:
        mastery_offer.buttons.buttons[0].on_activate()  # Engage
        assert isinstance(mastery_offer._active, SequenceScene)
        mastery_offer._active.continue_button.on_activate()  # inspect the mastery export
        select_scene = mastery_offer._active._active
        _fill_single_select(select_scene, MASTERY_KEY_FIELD, mastery_key_choice)
        _fill_multi_select(select_scene, MASTERY_PRESERVE_FIELD, mastery_preserve_selection)
    else:
        mastery_offer.buttons.buttons[1].on_activate()  # Skip

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    return app.scenes.current.inner


def test_the_full_lesson_plays_through_all_fifteen_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_eight_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_feedback(app, mastery_engage=True)
        app.scenes.current.on_complete()  # feedback -> debrief

        assert isinstance(app.scenes.current.inner, DialogueScene)  # debrief
        _play_dialogue_to_the_end(app.scenes.current)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonEightResult)
        assert result.completed_thoughtfully() is True
        assert result.round1_resolution == GOOD_ROUND1_RESOLUTION
        assert result.round2_resolution == GOOD_ROUND2_RESOLUTION
        assert result.group_verdicts == GOOD_GROUP_VERDICTS
        assert set(result.decision) == {field.key for field in DECISION_FIELDS_IN_ORDER} | {"evidence"}
        assert result.mastery_engaged is True
        assert result.mastery_key_choice == "scan_event_id"
        assert result.mastery_preserve_selection == frozenset({"checkpoint_scans", "qc_rescan"})
        assert collected is not None
    finally:
        pygame.quit()


def test_a_playthrough_that_skips_mastery_still_completes():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eight_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_lesson_to_feedback(app, mastery_engage=False)
        app.scenes.current.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.mastery_engaged is False
        assert result.mastery_preserve_selection == frozenset()
    finally:
        pygame.quit()


def test_a_naive_round1_pick_can_be_revised_via_the_revision_offer():
    # The central productive-failure chain: pick a naive dedupe key,
    # see the conflict up close in the twist, revise via the real,
    # un-punished offer, then correctly quarantine it in Round 2.
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_eight_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            round1_resolution={"event_id": "dedupe_by_event_id_keep_first"},
            revision_engage=True,
            revised_round1_resolution=GOOD_ROUND1_RESOLUTION,
        )
        assert isinstance(feedback, LessonFeedbackScene)
        feedback.on_complete()
        _play_dialogue_to_the_end(app.scenes.current)

        result = finished_results[0]
        assert result.round1_revised is True
        assert result.initial_round1_resolution == {"event_id": "dedupe_by_event_id_keep_first"}
        assert result.round1_resolution == GOOD_ROUND1_RESOLUTION
        count, low, high = result.final_captured_state()
        assert (count, low, high) == (20, 995.0, 1000.0)

        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.METHOD] == 94.0
        assert scores[ScoreDimension.REASONING] == 92.0
        assert any(
            o.text_key == "lesson.l08.feedback.dedupe_key_recovered_via_revision" for o in feedback.evaluation.observations
        )
    finally:
        pygame.quit()


def test_declining_the_revision_offer_keeps_the_naive_round1_pick():
    app = _init_app()
    try:
        runner, _ = build_lesson_eight_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        feedback = _play_lesson_to_feedback(
            app,
            round1_resolution={"event_id": "dedupe_by_order_id"},
            revision_engage=False,
            round2_resolution={"amount": "quarantine_and_disclose"},
            decision=dict(GOOD_DECISION, automatic_removal_rule="dedupe_by_order_id", kpi_result="zero_orders_0"),
        )
        assert isinstance(feedback, LessonFeedbackScene)
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [*DECISION_FIELDS_IN_ORDER, MASTERY_KEY_FIELD, MASTERY_PRESERVE_FIELD])
def test_every_field_has_at_least_two_options(field):
    assert len(field.options) >= 2


# --- Scoring, exercised directly against hand-built results ---------------


def _result(**overrides) -> LessonEightResult:
    base = dict(
        round1_resolution=GOOD_ROUND1_RESOLUTION,
        round2_resolution=GOOD_ROUND2_RESOLUTION,
        group_verdicts=GOOD_GROUP_VERDICTS,
        decision=dict(GOOD_DECISION, evidence=("e1", "e2")),
        critical_evidence_present=(
            "lesson.l08.evidence.event_id_duplicate_count",
            "lesson.l08.group.retry.evidence",
            "lesson.l08.group.decoy.evidence",
            "lesson.l08.group.conflict.evidence",
        ),
    )
    base.update(overrides)
    return LessonEightResult(**base)


def test_data_quality_rewards_every_correct_group_verdict():
    good = score_lesson_eight(_result(), LESSON_08, hints_used=0)
    bad = score_lesson_eight(
        _result(group_verdicts={**GOOD_GROUP_VERDICTS, "replay_group": "keep_all_not_a_duplicate"}), LESSON_08, hints_used=0
    )
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] > bad.dimension_scores[ScoreDimension.DATA_QUALITY]


def test_data_quality_flags_the_conflict_group_misjudged():
    result = score_lesson_eight(
        _result(group_verdicts={**GOOD_GROUP_VERDICTS, "conflict_group": "safe_to_remove_duplicate"}), LESSON_08, hints_used=0
    )
    assert any(o.text_key == "lesson.l08.feedback.conflict_group_misjudged" for o in result.observations)


def test_data_quality_requires_the_exact_legitimate_repeats_set():
    # Two decorative-looking fields (identity_key, legitimate_repeats)
    # must actually be wired into scoring - a student who over-includes
    # the transport replay as "legitimate" must score worse, not the
    # same, as one who names the exact correct set.
    good = score_lesson_eight(_result(), LESSON_08, hints_used=0)
    over_included = score_lesson_eight(
        _result(
            decision=dict(
                GOOD_DECISION,
                legitimate_repeats=(
                    "multiple_lifecycle_events",
                    "multiple_payment_attempts",
                    "repeat_purchases",
                    "transport_replay",
                ),
                evidence=("e1", "e2"),
            )
        ),
        LESSON_08,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0
    assert over_included.dimension_scores[ScoreDimension.DATA_QUALITY] < 100.0
    assert any(o.text_key == "lesson.l08.feedback.legitimate_repeats_incorrect" for o in over_included.observations)


def test_method_rewards_the_correct_dedupe_key_conflict_policy_and_prevention():
    good = score_lesson_eight(_result(), LESSON_08, hints_used=0)
    weak = score_lesson_eight(
        _result(decision=dict(GOOD_DECISION, prevention_recommendation="nothing_needed", evidence=("e1", "e2"))),
        LESSON_08,
        hints_used=0,
    )
    assert good.dimension_scores[ScoreDimension.METHOD] == 94.0
    assert good.dimension_scores[ScoreDimension.METHOD] > weak.dimension_scores[ScoreDimension.METHOD]
    assert any(o.text_key == "lesson.l08.feedback.no_prevention_recommended" for o in weak.observations)


def test_method_does_not_score_event_id_correct_just_because_it_solved_replay():
    # Picking the right transport-replay key (event_id/remove_exact_repeats_only)
    # must not by itself satisfy conflict_policy's own separate hit.
    result = score_lesson_eight(
        _result(round2_resolution={"amount": "keep_first_by_event_id"}), LESSON_08, hints_used=0
    )
    assert result.dimension_scores[ScoreDimension.METHOD] < 94.0


def test_reasoning_catches_a_dedupe_key_claim_that_doesnt_match_execution():
    result = score_lesson_eight(
        _result(decision=dict(GOOD_DECISION, automatic_removal_rule="dedupe_by_order_id", evidence=("e1", "e2"))),
        LESSON_08,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l08.feedback.dedupe_key_claim_doesnt_match_execution" for o in result.observations)


def test_reasoning_identity_key_requires_grounded_group_verdicts():
    # Naming "shared event ID" only counts as a real, grounded claim if
    # the replay and conflict groups actually got the correct verdict -
    # getting the definition right while misjudging either isn't
    # evidenced, just a lucky guess.
    result = score_lesson_eight(
        _result(group_verdicts={**GOOD_GROUP_VERDICTS, "replay_group": "keep_all_not_a_duplicate"}),
        LESSON_08,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l08.feedback.identity_key_not_grounded" for o in result.observations)


def test_reasoning_catches_a_kpi_claim_that_contradicts_the_real_pipeline():
    result = score_lesson_eight(
        _result(
            round2_resolution={"amount": "keep_first_by_event_id"},
            decision=dict(GOOD_DECISION, conflict_policy="keep_first_by_event_id", evidence=("e1", "e2")),
        ),
        LESSON_08,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l08.feedback.kpi_claim_contradicts_own_pipeline" for o in result.observations)


def test_reasoning_safe_claim_is_only_coherent_after_a_real_quarantine():
    result = score_lesson_eight(
        _result(
            round2_resolution={"amount": "keep_higher_amount"},
            decision=dict(
                GOOD_DECISION,
                conflict_policy="keep_higher_amount",
                kpi_result="twenty_orders_1000_no_caveats",
                evidence=("e1", "e2"),
            ),
        ),
        LESSON_08,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l08.feedback.safe_claim_incoherent" for o in result.observations)


def test_evidence_rewards_citing_the_critical_facts():
    good = score_lesson_eight(_result(), LESSON_08, hints_used=0)
    empty = score_lesson_eight(_result(critical_evidence_present=()), LESSON_08, hints_used=0)
    assert good.dimension_scores[ScoreDimension.EVIDENCE] > empty.dimension_scores[ScoreDimension.EVIDENCE]


def test_evidence_requires_the_conflict_fact_specifically_not_any_three():
    # Any 3-of-N used to be enough; now full credit requires the
    # conflict fact plus at least one identity/legitimate-repeat fact -
    # never an arbitrary combination that happens to skip the one fact
    # the final argument (an unresolved amount) actually rests on.
    no_conflict_fact = score_lesson_eight(
        _result(
            critical_evidence_present=(
                "lesson.l08.evidence.event_id_duplicate_count",
                "lesson.l08.group.retry.evidence",
                "lesson.l08.group.decoy.evidence",
            )
        ),
        LESSON_08,
        hints_used=0,
    )
    assert any(o.text_key == "lesson.l08.feedback.evidence_missing_conflict_fact" for o in no_conflict_fact.observations)
    assert no_conflict_fact.dimension_scores[ScoreDimension.EVIDENCE] < 95.0


def test_evidence_late_correct_evidence_via_round2_still_counts():
    # Productive failure: a student who misjudged the twist conflict
    # group (no group.conflict.evidence recorded) but genuinely saw the
    # conflict via Round 2's own unconditional issue.amount.evidence and
    # picked the correct reconciliation policy has real, citable proof
    # of the same fact - full Evidence credit, not a dead end.
    result = score_lesson_eight(
        _result(
            group_verdicts={**GOOD_GROUP_VERDICTS, "conflict_group": "safe_to_remove_duplicate"},
            critical_evidence_present=(
                "lesson.l08.evidence.event_id_duplicate_count",
                "lesson.l08.issue.amount.evidence",
            ),
        ),
        LESSON_08,
        hints_used=0,
    )
    assert result.dimension_scores[ScoreDimension.EVIDENCE] == 95.0


def test_reproducibility_gives_equal_credit_to_any_real_stated_rule():
    # keep_higher_amount is a real, stated rule (unlike keep-first/keep-last's
    # bare tie-break), so it earns the SAME REPRODUCIBILITY credit as the
    # disclosed quarantine policy - the two dimensions diverge on METHOD
    # instead, which strictly requires the disclosed quarantine policy.
    quarantine_result = score_lesson_eight(_result(), LESSON_08, hints_used=0)
    higher_amount_result = score_lesson_eight(
        _result(round2_resolution={"amount": "keep_higher_amount"}), LESSON_08, hints_used=0
    )
    keep_first_result = score_lesson_eight(
        _result(round2_resolution={"amount": "keep_first_by_event_id"}), LESSON_08, hints_used=0
    )
    assert (
        higher_amount_result.dimension_scores[ScoreDimension.REPRODUCIBILITY]
        > keep_first_result.dimension_scores[ScoreDimension.REPRODUCIBILITY]
    )
    assert (
        higher_amount_result.dimension_scores[ScoreDimension.REPRODUCIBILITY]
        == quarantine_result.dimension_scores[ScoreDimension.REPRODUCIBILITY]
    )
    assert (
        higher_amount_result.dimension_scores[ScoreDimension.METHOD] < quarantine_result.dimension_scores[ScoreDimension.METHOD]
    )


def test_round1_reproducibility_and_method_are_not_identical():
    # dedupe_by_order_id is methodologically wrong (destroys legitimate
    # retries) but still a real, fully deterministic rule - it should
    # score low on METHOD while still scoring real, nonzero credit on
    # REPRODUCIBILITY, never a flat zero just for being the wrong policy.
    correct_result = score_lesson_eight(_result(), LESSON_08, hints_used=0)
    order_id_result = score_lesson_eight(
        _result(round1_resolution={"event_id": "dedupe_by_order_id"}), LESSON_08, hints_used=0
    )
    assert order_id_result.dimension_scores[ScoreDimension.METHOD] < correct_result.dimension_scores[ScoreDimension.METHOD]
    assert order_id_result.dimension_scores[ScoreDimension.REPRODUCIBILITY] > 15.0
    assert (
        order_id_result.dimension_scores[ScoreDimension.REPRODUCIBILITY]
        < correct_result.dimension_scores[ScoreDimension.REPRODUCIBILITY]
    )


def test_mastery_requires_the_exact_correct_key_and_preserve_set():
    assert _mastery_succeeded(
        _result(mastery_key_choice="scan_event_id", mastery_preserve_selection=frozenset({"checkpoint_scans", "qc_rescan"}))
    )
    assert not _mastery_succeeded(
        _result(mastery_key_choice="package_id", mastery_preserve_selection=frozenset({"checkpoint_scans", "qc_rescan"}))
    )
    assert not _mastery_succeeded(
        _result(
            mastery_key_choice="scan_event_id",
            mastery_preserve_selection=frozenset({"checkpoint_scans", "qc_rescan", "scanner_retry_replay"}),
        )
    )
