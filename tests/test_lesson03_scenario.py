import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l03_api_courier.scenario import (
    ACQUISITION_STRATEGY_FIELD,
    COMPLETENESS_INTERPRET_OPTIONS,
    KNOWN_GAP_FIELD,
    MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS,
    NOT_SAFE_TO_CLAIM_FIELD,
    RECOMMENDATION_FIELD,
    REQUEST_ATTEMPTS,
    SAFE_TO_CLAIM_FIELD,
    build_lesson_three_runner,
)
from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l03_api_courier.scoring import LessonThreeResult
from data_science_arcade.lessons.l03_api_courier.twist_data import BEST_ACHIEVABLE_TOTAL, TOTAL_COUNT
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene
from data_science_arcade.workbench.context import LessonContext

from lesson_test_helpers import click_through_mission_briefing

L03_STAGE_FINGERPRINT = "|".join(
    [
        "briefing",
        "framing",
        "acquisition",
        "gut_check",
        "completeness_reveal",
        "root_cause_confirmed",
        "revised_gut_check",
        "evidence_review",
        "final_decision",
        "mastery_challenge",
        "feedback",
        "debrief",
    ]
)

# KNOWN_GAP_FIELD's real option order - named here once since several tests
# below pick specific indices and the field now has 5 options, not 4.
_KNOWN_GAP_PAGE_SHORTFALL = 0
_KNOWN_GAP_BOTH_PAGES = 1
_KNOWN_GAP_RATE_LIMIT_ALONE = 2


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _play_dialogue_to_the_end(scene: DialogueScene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _play_out_the_console(scene: APIConsoleScene, choices: list) -> None:
    """`choices` is the full real sequence of continuation picks needed,
    starting with page 1's own pagination choice (typically
    "follow_cursor") and, if reached, page 5's rate-limit choice."""
    remaining = list(choices)
    while not scene._base_exhausted():
        if scene._pending is not None:
            key = remaining.pop(0)
            option = next(o for o in scene._pending.continuation_options if o.key == key)
            scene._make_choose_continuation(option)()
        else:
            scene._send_request()
    scene.buttons.buttons[0].on_activate()  # Finish


def _play_comparison_reveal(scene: ComparisonRevealScene, option_index: int = 0) -> None:
    scene.buttons.buttons[option_index].on_activate()
    scene.continue_button.on_activate()


def _fill_out(scene: BriefBuilderScene, field_count: int, option_index: int = 0) -> None:
    for _ in range(field_count):
        scene.buttons.buttons[option_index].on_activate()
        scene.next_button.on_activate()


def _play_decision_builder(scene: DecisionBuilderScene, option_index: int = 0) -> None:
    scene.buttons.buttons[option_index].on_activate()  # acquisition_strategy
    scene.next_button.on_activate()
    evidence_ids = list(scene._evidence_toggle_buttons.keys())
    scene._evidence_toggle_buttons[evidence_ids[0]].on_activate()
    scene._evidence_toggle_buttons[evidence_ids[1]].on_activate()
    scene.next_button.on_activate()
    for _ in range(4):  # known_gap, safe_to_claim, not_safe_to_claim, recommendation
        scene.buttons.buttons[option_index].on_activate()
        scene.next_button.on_activate()


def _play_decision_builder_with_indices(
    scene: DecisionBuilderScene,
    *,
    acquisition_strategy: int,
    known_gap: int,
    safe_to_claim: int,
    not_safe_to_claim: int,
    recommendation: int,
    evidence_count: int,
) -> None:
    scene.buttons.buttons[acquisition_strategy].on_activate()
    scene.next_button.on_activate()
    evidence_ids = list(scene._evidence_toggle_buttons.keys())
    for evidence_id in evidence_ids[:evidence_count]:
        scene._evidence_toggle_buttons[evidence_id].on_activate()
    scene.next_button.on_activate()
    for index in (known_gap, safe_to_claim, not_safe_to_claim, recommendation):
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def _play_lesson_to_completion(
    app, *, skip_mastery: bool = True, console_choices: list | None = None, option_index: int = 0
) -> None:
    runner_scene = app.scenes.current
    console_choices = ["follow_cursor", "wait_and_retry"] if console_choices is None else console_choices

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # briefing
    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # framing

    assert isinstance(app.scenes.current.inner, APIConsoleScene)
    _play_out_the_console(app.scenes.current.inner, console_choices)  # acquisition

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 1, option_index)  # gut check

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)
    _play_comparison_reveal(app.scenes.current.inner, option_index)  # completeness reveal

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed

    assert isinstance(app.scenes.current.inner, BriefBuilderScene)
    _fill_out(app.scenes.current.inner, 1, option_index)  # revised gut check

    assert isinstance(app.scenes.current.inner, WorkbenchScene)
    app.scenes.current.inner.continue_button.on_activate()  # evidence review

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)
    _play_decision_builder(app.scenes.current.inner, option_index)

    assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
    if skip_mastery:
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # Skip
    else:
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # Engage
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # pick a metric
        app.scenes.current.inner.buttons.buttons[0].on_activate()  # pick an interpretation
        app.scenes.current.inner.finish_button.on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)
    app.scenes.current.inner.buttons.buttons[0].on_activate()

    assert isinstance(app.scenes.current.inner, DialogueScene)
    _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

    assert app.scenes.current is not runner_scene


def test_the_full_lesson_plays_through_all_twelve_stages_to_a_result():
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_three_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app)

        assert len(finished_results) == 1
        result = finished_results[0]
        assert isinstance(result, LessonThreeResult)
        assert result.completed_thoughtfully() is True
        assert result.mastery_engaged is False
        assert result.page5_recovered is True
        assert "analytical_context" in collected
        assert collected["running_total"] == BEST_ACHIEVABLE_TOTAL
    finally:
        pygame.quit()


def test_resending_a_page_before_following_its_cursor_does_not_change_the_final_total():
    # The real pagination micro-decision's own wrong choice (resend
    # instead of following next_cursor) must be a harmless, honest dead
    # end - not a way to silently inflate or corrupt the final total.
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_three_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app, console_choices=["resend", "follow_cursor", "wait_and_retry"])

        assert collected["running_total"] == BEST_ACHIEVABLE_TOTAL
        assert finished_results[0].page5_recovered is True
    finally:
        pygame.quit()


def test_skip_path_produces_a_lower_total_and_its_own_conditional_evidence():
    # The direct regression test for the real flaw a Plan-agent review
    # caught before any code was written: a student who skips the
    # rate-limited page instead of backing off ends up with a genuinely
    # different real total (103, not 128) and a real fourth evidence fact
    # (the skipped page) the backoff path never has - Known Gap/Safe/
    # Not-Safe all still have to resolve sensibly with that different
    # number behind them.
    app = _init_app()
    try:
        finished_results = []
        runner, collected = build_lesson_three_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)

        _play_lesson_to_completion(app, console_choices=["follow_cursor", "skip"])

        result = finished_results[0]
        assert result.page5_recovered is False
        assert collected["running_total"] == BEST_ACHIEVABLE_TOTAL - 25  # page 5's own 25 never recovered
    finally:
        pygame.quit()


def test_the_console_evidence_pool_includes_the_skipped_fact_only_on_that_path():
    app = _init_app()
    try:
        runner, collected = build_lesson_three_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        console = app.scenes.current.inner
        _play_out_the_console(console, ["follow_cursor", "skip"])

        assert {e.label_key for e in console.context.evidence} == {"lesson.l03.evidence.page_skipped_label"}
    finally:
        pygame.quit()


def test_analytical_context_survives_a_checkpoint_new_app_and_resume():
    # Real cross-process resume, not just a second LessonRunner against the
    # same in-memory App - a fresh App() picks up whatever DEFAULT_SAVE_PATH
    # holds on disk (tests/conftest.py's autouse fixture isolates it to one
    # tmp_path for this whole test), matching l01/l02's own precedent.
    app1 = _init_app()
    try:
        runner1, _ = build_lesson_three_runner(app1, on_finished=lambda result: None)
        runner1.start()
        click_through_mission_briefing(app1)
        _play_dialogue_to_the_end(app1.scenes.current)  # briefing
        _play_dialogue_to_the_end(app1.scenes.current)  # framing
        _play_out_the_console(app1.scenes.current.inner, ["follow_cursor", "wait_and_retry"])  # acquisition
        _fill_out(app1.scenes.current.inner, 1)  # gut check

        completeness_reveal = app1.scenes.current.inner
        assert isinstance(completeness_reveal, ComparisonRevealScene)
        completeness_reveal.buttons.buttons[0].on_activate()
        completeness_reveal.continue_button.on_activate()  # advances + checkpoints; quit right here
    finally:
        pygame.quit()

    app2 = _init_app()  # a brand new App(), same on-disk save - simulates relaunching
    try:
        runner2, _ = build_lesson_three_runner(app2, on_finished=lambda result: None)
        runner2.start()  # resumes straight into root_cause_confirmed, skipping everything before it

        root_cause = app2.scenes.current.inner
        assert isinstance(root_cause, DialogueScene)
        resumed_context = root_cause.context
        assert len(resumed_context.actions) >= 1  # the acquisition's own real action
        assert len(resumed_context.evidence) >= 2  # completeness reveal's own 2 real values
        assert "responses = []" in resumed_context.python_mirror()
    finally:
        pygame.quit()


@pytest.mark.parametrize("field", [ACQUISITION_STRATEGY_FIELD, KNOWN_GAP_FIELD, SAFE_TO_CLAIM_FIELD, NOT_SAFE_TO_CLAIM_FIELD, RECOMMENDATION_FIELD])
def test_every_single_select_decision_field_has_at_least_three_options(field):
    assert len(field.options) >= 3


def test_completeness_interpret_options_has_exactly_one_correct_answer_and_no_evidence_key_gating():
    # Deliberately different from l02_source_scout's Gap Discovery: the
    # correct fact here is recorded unconditionally by the follow-up
    # root_cause_confirmed dialogue, not gated behind this interpret pick
    # (see scenario.py's own docstring for why) - so no option here should
    # carry an evidence_key at all.
    assert len(COMPLETENESS_INTERPRET_OPTIONS) == 4
    assert all(option.evidence_key is None for option in COMPLETENESS_INTERPRET_OPTIONS)


def test_mastery_metric_and_interpret_options_are_both_real_choices():
    assert len(MASTERY_METRIC_OPTIONS) == 2
    assert len(MASTERY_INTERPRET_OPTIONS) == 2


def test_request_attempts_top_level_tuple_is_not_a_meaningful_total_on_its_own():
    # REQUEST_ATTEMPTS is only each *top-level* slot's first attempt -
    # page 2's own real data lives inside page 1's own continuation tree
    # (not a top-level slot at all, see scenario.py's own comment), and
    # page 5's first attempt is always the rate-limited one (0 records).
    # Naively summing this flat tuple's is_success entries (page 1 + 3 + 4
    # + 6, page 2 and 5 both absent/zeroed) isn't the real best case (128)
    # or the real skip case (103) - both only exist behind the real
    # continuation trees, reachable through actual choices, verified via
    # real gameplay in the full-playthrough tests above, not by summing
    # this tuple.
    first_pass_success_total = sum(a.records_returned for a in REQUEST_ATTEMPTS if a.is_success)
    assert first_pass_success_total == 25 + 16 + 25 + 12  # page 1, 3, 4, 6 - page 2/5 excluded


def test_best_achievable_total_still_falls_short_of_the_declared_total_count():
    assert BEST_ACHIEVABLE_TOTAL < TOTAL_COUNT  # page 3's shortfall is never recovered by anything the console does


def test_a_well_scoped_playthrough_scores_high_on_every_dimension():
    # The direct regression test for real score discrimination, matching
    # l02_source_scout's own "verified end-to-end both directions" manual
    # playthrough discipline, but committed as a real test rather than a
    # one-off script.
    app = _init_app()
    try:
        runner, _ = build_lesson_three_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        _play_out_the_console(app.scenes.current.inner, ["follow_cursor", "wait_and_retry"])  # sound method: real backoff
        _fill_out(app.scenes.current.inner, 1, option_index=0)  # gut check: yes_complete
        _play_comparison_reveal(app.scenes.current.inner, option_index=0)  # correct interpret: page_shortfall
        _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed
        _fill_out(app.scenes.current.inner, 1, option_index=1)  # revised gut check: no_would_flag_it
        app.scenes.current.inner.continue_button.on_activate()  # evidence review

        _play_decision_builder_with_indices(
            app.scenes.current.inner,
            acquisition_strategy=1,  # floor_and_range
            known_gap=_KNOWN_GAP_PAGE_SHORTFALL,  # correct on the recovered path
            safe_to_claim=0,  # floor_and_threshold_flag
            not_safe_to_claim=0,  # single_exact_total
            recommendation=0,  # report_range_and_flag
            evidence_count=3,  # all 3 real, critical facts available on this path
        )

        assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # Skip

        feedback = app.scenes.current.inner
        assert isinstance(feedback, LessonFeedbackScene)
        scores = feedback.evaluation.dimension_scores
        assert all(score >= 80 for score in scores.values()), scores
    finally:
        pygame.quit()


def test_a_weak_playthrough_scores_low_on_every_dimension():
    app = _init_app()
    try:
        runner, _ = build_lesson_three_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        _play_out_the_console(app.scenes.current.inner, ["follow_cursor", "skip"])  # weak method: gave up instead of backing off
        _fill_out(app.scenes.current.inner, 1, option_index=0)  # gut check
        _play_comparison_reveal(app.scenes.current.inner, option_index=1)  # wrong interpret: rate_limit_alone
        _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed
        _fill_out(app.scenes.current.inner, 1, option_index=0)  # revised gut check: yes_still_fine (no revision)
        app.scenes.current.inner.continue_button.on_activate()  # evidence review

        _play_decision_builder_with_indices(
            app.scenes.current.inner,
            acquisition_strategy=0,  # raw_no_caveat
            known_gap=_KNOWN_GAP_RATE_LIMIT_ALONE,  # wrong on either path
            safe_to_claim=1,  # exact_precision
            not_safe_to_claim=1,  # api_unreliable
            recommendation=1,  # report_raw_and_move_on
            evidence_count=2,  # weak citation regardless of path
        )

        assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # Skip

        feedback = app.scenes.current.inner
        assert isinstance(feedback, LessonFeedbackScene)
        scores = feedback.evaluation.dimension_scores
        assert all(score <= 45 for score in scores.values()), scores
    finally:
        pygame.quit()


def test_skip_path_naming_both_real_gaps_scores_evidence_and_uncertainty_high():
    # The direct regression test for the P0 this follow-up exists to fix:
    # a skip-path student who correctly cites all 4 real facts and names
    # both real mechanisms must be able to reach a full argument, not be
    # capped by critical-evidence/known-gap logic that only ever expected
    # the 3-fact/1-mechanism recovered-path shape.
    app = _init_app()
    try:
        runner, _ = build_lesson_three_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        _play_out_the_console(app.scenes.current.inner, ["follow_cursor", "skip"])
        _fill_out(app.scenes.current.inner, 1, option_index=0)  # gut check
        _play_comparison_reveal(app.scenes.current.inner, option_index=0)  # correct interpret: page_shortfall
        _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed
        _fill_out(app.scenes.current.inner, 1, option_index=1)  # revised gut check
        app.scenes.current.inner.continue_button.on_activate()  # evidence review

        decision = app.scenes.current.inner
        _play_decision_builder_with_indices(
            decision,
            acquisition_strategy=1,  # floor_and_range
            known_gap=_KNOWN_GAP_BOTH_PAGES,  # names page 3 AND page 5 - correct on the skip path
            safe_to_claim=0,
            not_safe_to_claim=0,
            recommendation=0,
            evidence_count=4,  # all 4 real facts, including the skip-only page_skipped one
        )

        assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # Skip

        feedback = app.scenes.current.inner
        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.EVIDENCE] >= 80, scores
        assert scores[ScoreDimension.UNCERTAINTY] >= 80, scores
    finally:
        pygame.quit()


def test_recovered_path_falsely_claiming_page5_unrecovered_scores_uncertainty_low():
    # The mirror image of the above: on the recovered path, page 5's data
    # genuinely came back - claiming it was never recovered is a real,
    # false statement, not a generous superset of the correct answer, and
    # must not score anywhere near what the true, precise answer scores.
    app = _init_app()
    try:
        runner, _ = build_lesson_three_runner(app, on_finished=lambda result: None)
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        _play_out_the_console(app.scenes.current.inner, ["follow_cursor", "wait_and_retry"])
        _fill_out(app.scenes.current.inner, 1, option_index=0)  # gut check
        _play_comparison_reveal(app.scenes.current.inner, option_index=0)
        _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed
        _fill_out(app.scenes.current.inner, 1, option_index=1)  # revised gut check
        app.scenes.current.inner.continue_button.on_activate()  # evidence review

        _play_decision_builder_with_indices(
            app.scenes.current.inner,
            acquisition_strategy=1,
            known_gap=_KNOWN_GAP_BOTH_PAGES,  # false on this path - page 5 really was recovered
            safe_to_claim=0,
            not_safe_to_claim=0,
            recommendation=0,
            evidence_count=3,
        )

        assert isinstance(app.scenes.current.inner, MasteryChallengeScene)
        app.scenes.current.inner.buttons.buttons[1].on_activate()  # Skip

        feedback = app.scenes.current.inner
        scores = feedback.evaluation.dimension_scores
        assert scores[ScoreDimension.UNCERTAINTY] <= 30, scores
    finally:
        pygame.quit()


def test_mastery_solved_vs_attempted_depends_on_the_real_interpretation_not_just_engaging():
    app = _init_app()
    try:
        finished_results = []
        runner, _ = build_lesson_three_runner(app, on_finished=lambda result: finished_results.append(result))
        runner.start()
        click_through_mission_briefing(app)
        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        _play_out_the_console(app.scenes.current.inner, ["follow_cursor", "wait_and_retry"])
        _fill_out(app.scenes.current.inner, 1)  # gut check
        _play_comparison_reveal(app.scenes.current.inner)  # completeness reveal
        _play_dialogue_to_the_end(app.scenes.current)  # root cause confirmed
        _fill_out(app.scenes.current.inner, 1)  # revised gut check
        app.scenes.current.inner.continue_button.on_activate()  # evidence review
        _play_decision_builder(app.scenes.current.inner)

        mastery = app.scenes.current.inner
        assert isinstance(mastery, MasteryChallengeScene)
        mastery.buttons.buttons[0].on_activate()  # Engage
        mastery.buttons.buttons[0].on_activate()  # pick a metric
        wrong_interpret_index = next(i for i, o in enumerate(MASTERY_INTERPRET_OPTIONS) if o.key == "looks_complete")
        mastery.buttons.buttons[wrong_interpret_index].on_activate()
        mastery.finish_button.on_activate()

        app.scenes.current.inner.buttons.buttons[0].on_activate()  # feedback
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        result = finished_results[0]
        assert result.mastery_engaged is True
        assert result.mastery_interpretation == "looks_complete"
    finally:
        pygame.quit()
