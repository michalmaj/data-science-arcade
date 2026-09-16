from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l25_kpi_emergency_room.definition import LESSON_25
from data_science_arcade.lessons.l25_kpi_emergency_room.incident_log import (
    false_alarm_count,
    false_alarm_count_mirror_code,
    generate_incident_log,
    monitoring_outcome_mirror_code,
    real_incidents_caught,
    real_incidents_caught_mirror_code,
    simulate_monitoring,
)
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import BALANCED_THRESHOLD, MONITORING_REQUESTS, TIGHT_THRESHOLD
from data_science_arcade.lessons.l25_kpi_emergency_room.scoring import (
    CHECKOUT_ERROR_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    ON_TIME_DELIVERY_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_BALANCED_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    LessonTwentyFiveResult,
    SOCIAL_MENTIONS_BALANCED_ALERT_COUNT_EVIDENCE_KEY,
    SOCIAL_MENTIONS_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    score_lesson_twenty_five,
)
from data_science_arcade.lessons.l25_kpi_emergency_room.twist_data import generate_alert_fatigue_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l25_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l25_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_investigation.line3"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l25_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l25_debrief.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l25_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_debrief.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_debrief.line4"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l25_mastery.line1",
    "dialogue.l25_mastery.line2",
    "dialogue.l25_mastery.line3",
)

# --- Two mandatory reveals - fixed, real reference values computed from
# the same 14-day incident log. Zero InterpretOption.evidence_key
# anywhere: a student who picks the WRONG interpretation still saw the
# exact same real numbers and can cite them later. ------------------------

_INCIDENT_LOG = generate_incident_log()


def _bare_int(value: float) -> str:
    return f"{value:.0f}"


# --- Reveal A: "The Cost of Watching Too Tightly" - page_load_time under
# both thresholds, isolating the threshold's own effect (2 false alarms
# tight vs. 0 balanced) from whether it ever catches anything real (0,
# under either threshold) - the tight/balanced comparison the student's
# own live preview never puts side by side. ------------------------------

_PAGE_LOAD_TIME_TIGHT_FALSE_ALARMS = false_alarm_count(_INCIDENT_LOG, "page_load_time", TIGHT_THRESHOLD.multiplier)
_PAGE_LOAD_TIME_BALANCED_FALSE_ALARMS = false_alarm_count(_INCIDENT_LOG, "page_load_time", BALANCED_THRESHOLD.multiplier)
_PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT = real_incidents_caught(_INCIDENT_LOG, "page_load_time", TIGHT_THRESHOLD.multiplier)

THRESHOLD_TRADEOFF_REVEAL_COMPARISONS = (
    ComparisonValue(
        PAGE_LOAD_TIME_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
        _PAGE_LOAD_TIME_TIGHT_FALSE_ALARMS,
        python_code=false_alarm_count_mirror_code("page_load_time", TIGHT_THRESHOLD.multiplier, "threshold_reveal_tight_false_alarms"),
        value_format=_bare_int,
    ),
    ComparisonValue(
        PAGE_LOAD_TIME_BALANCED_FALSE_ALARM_COUNT_EVIDENCE_KEY,
        _PAGE_LOAD_TIME_BALANCED_FALSE_ALARMS,
        python_code=false_alarm_count_mirror_code("page_load_time", BALANCED_THRESHOLD.multiplier, "threshold_reveal_balanced_false_alarms"),
        value_format=_bare_int,
    ),
    ComparisonValue(
        PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
        _PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT,
        python_code=real_incidents_caught_mirror_code("page_load_time", TIGHT_THRESHOLD.multiplier, "threshold_reveal_incidents_caught"),
        value_format=_bare_int,
    ),
)
THRESHOLD_TRADEOFF_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l25.threshold_tradeoff_reveal.interpret.option.{key}")
    for key in (
        "tighter_threshold_cost_more_false_alarms_without_catching_more",
        "any_tight_threshold_is_a_mistake_always_prefer_balanced",
        "two_false_alarms_in_fourteen_days_isnt_worth_worrying_about",
    )
)

# --- Reveal B: "Watching the Right Thing" - synthesizes the two real
# incidents' own correct metrics alongside social_mentions' own complete
# silence, so the compact two-metric set has real, reveal-backed positive
# support, not just "the other two are bad." -----------------------------

_CHECKOUT_ERROR_RATE_CAUGHT = real_incidents_caught(_INCIDENT_LOG, "checkout_error_rate", BALANCED_THRESHOLD.multiplier)
_ON_TIME_DELIVERY_RATE_CAUGHT = real_incidents_caught(_INCIDENT_LOG, "on_time_delivery_rate", BALANCED_THRESHOLD.multiplier)
_SOCIAL_MENTIONS_BALANCED_ALERTS = false_alarm_count(_INCIDENT_LOG, "social_mentions", BALANCED_THRESHOLD.multiplier)
_SOCIAL_MENTIONS_TIGHT_FALSE_ALARMS = false_alarm_count(_INCIDENT_LOG, "social_mentions", TIGHT_THRESHOLD.multiplier)

INCIDENT_COVERAGE_REVEAL_COMPARISONS = (
    ComparisonValue(
        CHECKOUT_ERROR_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
        _CHECKOUT_ERROR_RATE_CAUGHT,
        python_code=real_incidents_caught_mirror_code("checkout_error_rate", BALANCED_THRESHOLD.multiplier, "coverage_reveal_checkout_caught"),
        value_format=_bare_int,
    ),
    ComparisonValue(
        ON_TIME_DELIVERY_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
        _ON_TIME_DELIVERY_RATE_CAUGHT,
        python_code=real_incidents_caught_mirror_code("on_time_delivery_rate", BALANCED_THRESHOLD.multiplier, "coverage_reveal_delivery_caught"),
        value_format=_bare_int,
    ),
    ComparisonValue(
        SOCIAL_MENTIONS_BALANCED_ALERT_COUNT_EVIDENCE_KEY,
        _SOCIAL_MENTIONS_BALANCED_ALERTS,
        python_code=false_alarm_count_mirror_code("social_mentions", BALANCED_THRESHOLD.multiplier, "coverage_reveal_social_balanced_alerts"),
        value_format=_bare_int,
    ),
    ComparisonValue(
        SOCIAL_MENTIONS_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
        _SOCIAL_MENTIONS_TIGHT_FALSE_ALARMS,
        python_code=false_alarm_count_mirror_code("social_mentions", TIGHT_THRESHOLD.multiplier, "coverage_reveal_social_tight_false_alarms"),
        value_format=_bare_int,
    ),
)
INCIDENT_COVERAGE_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l25.incident_coverage_reveal.interpret.option.{key}")
    for key in (
        "checkout_and_delivery_metrics_caught_their_incidents_social_mentions_caught_neither",
        "since_social_mentions_never_alerted_the_business_was_healthy_the_whole_period",
        "social_mentions_is_worthless_and_should_be_deleted_from_every_dashboard",
    )
)

# --- Final Decision Brief - 1 MultiChoice + 3 REASONING + 1 CALIBRATION --

COMPACT_MONITORING_SET_FIELD = MultiChoiceField(
    key="compact_monitoring_set",
    prompt_key="lesson.l25.field.compact_monitoring_set.prompt",
    options=(
        BriefOption("checkout_error_rate", "lesson.l25.option.compact_monitoring_set.checkout_error_rate"),
        BriefOption("on_time_delivery_rate", "lesson.l25.option.compact_monitoring_set.on_time_delivery_rate"),
        BriefOption("social_mentions", "lesson.l25.option.compact_monitoring_set.social_mentions"),
        BriefOption("page_load_time", "lesson.l25.option.compact_monitoring_set.page_load_time"),
    ),
    min_count=2,
    max_count=2,
)
WHY_TIGHT_THRESHOLD_CREATES_EXTRA_FALSE_ALARMS_FIELD = BriefField(
    key="why_tight_threshold_creates_extra_false_alarms",
    prompt_key="lesson.l25.field.why_tight_threshold_creates_extra_false_alarms.prompt",
    options=(
        BriefOption(
            "flags_ordinary_variation_without_improving_detection_of_the_real_incidents",
            "lesson.l25.option.why_tight_threshold_creates_extra_false_alarms.flags_ordinary_variation_without_improving_detection_of_the_real_incidents",
        ),
        BriefOption(
            "tight_thresholds_are_always_the_wrong_choice",
            "lesson.l25.option.why_tight_threshold_creates_extra_false_alarms.tight_thresholds_are_always_the_wrong_choice",
        ),
        BriefOption("the_metric_itself_is_broken", "lesson.l25.option.why_tight_threshold_creates_extra_false_alarms.the_metric_itself_is_broken"),
    ),
)
WHY_SOCIAL_MENTIONS_MISSED_BOTH_OBSERVED_INCIDENTS_FIELD = BriefField(
    key="why_social_mentions_missed_both_observed_incidents",
    prompt_key="lesson.l25.field.why_social_mentions_missed_both_observed_incidents.prompt",
    options=(
        BriefOption(
            "did_not_align_with_either_incident_and_threshold_changes_only_shifted_which_days_alarmed",
            "lesson.l25.option.why_social_mentions_missed_both_observed_incidents.did_not_align_with_either_incident_and_threshold_changes_only_shifted_which_days_alarmed",
        ),
        BriefOption("not_enough_data_was_collected", "lesson.l25.option.why_social_mentions_missed_both_observed_incidents.not_enough_data_was_collected"),
        BriefOption("the_threshold_was_set_wrong", "lesson.l25.option.why_social_mentions_missed_both_observed_incidents.the_threshold_was_set_wrong"),
    ),
)
WHAT_AN_ALERT_CAN_AND_CANT_TELL_YOU_FIELD = BriefField(
    key="what_an_alert_can_and_cant_tell_you",
    prompt_key="lesson.l25.field.what_an_alert_can_and_cant_tell_you.prompt",
    options=(
        BriefOption(
            "something_crossed_a_real_line_worth_investigating_not_why_it_happened",
            "lesson.l25.option.what_an_alert_can_and_cant_tell_you.something_crossed_a_real_line_worth_investigating_not_why_it_happened",
        ),
        BriefOption("it_proves_the_specific_cause", "lesson.l25.option.what_an_alert_can_and_cant_tell_you.it_proves_the_specific_cause"),
        BriefOption(
            "it_can_be_safely_ignored_until_confirmed", "lesson.l25.option.what_an_alert_can_and_cant_tell_you.it_can_be_safely_ignored_until_confirmed"
        ),
    ),
)
STRONGEST_DEFENSIBLE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_claim",
    prompt_key="lesson.l25.field.strongest_defensible_claim.prompt",
    options=(
        BriefOption(
            "checkout_and_delivery_alerts_flag_real_incidents_but_dont_explain_them_and_silence_elsewhere_isnt_proof_of_health",
            "lesson.l25.option.strongest_defensible_claim.checkout_and_delivery_alerts_flag_real_incidents_but_dont_explain_them_and_silence_elsewhere_isnt_proof_of_health",
        ),
        BriefOption("the_dashboard_now_proves_nothing_else_is_wrong", "lesson.l25.option.strongest_defensible_claim.the_dashboard_now_proves_nothing_else_is_wrong"),
        BriefOption(
            "alerts_dont_tell_us_anything_useful_without_a_root_cause",
            "lesson.l25.option.strongest_defensible_claim.alerts_dont_tell_us_anything_useful_without_a_root_cause",
        ),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l25.decision.evidence.prompt", min_count=4, max_count=7)
DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    COMPACT_MONITORING_SET_FIELD,
    WHY_TIGHT_THRESHOLD_CREATES_EXTRA_FALSE_ALARMS_FIELD,
    WHY_SOCIAL_MENTIONS_MISSED_BOTH_OBSERVED_INCIDENTS_FIELD,
    WHAT_AN_ALERT_CAN_AND_CANT_TELL_YOU_FIELD,
    STRONGEST_DEFENSIBLE_CLAIM_FIELD,
)

# --- Optional mastery: NovaMart Warehouse Ops alert-fatigue dataset,
# promoted unchanged from this lesson's own old flat twist. -------------

MASTERY_WHAT_46_FALSE_ALARMS_COST_FIELD = BriefField(
    key="mastery_what_the_46_false_alarms_cost",
    prompt_key="lesson.l25.mastery.field.what_the_46_false_alarms_cost.prompt",
    options=(
        BriefOption(
            "real_incident_response_was_90x_slower_consistent_with_alert_fatigue",
            "lesson.l25.mastery.option.what_the_46_false_alarms_cost.real_incident_response_was_90x_slower_consistent_with_alert_fatigue",
        ),
        BriefOption(
            "the_false_alarms_directly_caused_the_slow_response",
            "lesson.l25.mastery.option.what_the_46_false_alarms_cost.the_false_alarms_directly_caused_the_slow_response",
        ),
        BriefOption("46_is_too_small_a_number_to_matter", "lesson.l25.mastery.option.what_the_46_false_alarms_cost.46_is_too_small_a_number_to_matter"),
    ),
)
MASTERY_STRONGEST_CLAIM_FIELD = BriefField(
    key="mastery_strongest_claim",
    prompt_key="lesson.l25.mastery.field.strongest_claim.prompt",
    options=(
        BriefOption(
            "high_false_alarm_volume_has_a_real_cost_even_when_the_real_incident_is_eventually_caught",
            "lesson.l25.mastery.option.strongest_claim.high_false_alarm_volume_has_a_real_cost_even_when_the_real_incident_is_eventually_caught",
        ),
        BriefOption(
            "false_alarms_should_be_reduced_to_zero_regardless_of_cost",
            "lesson.l25.mastery.option.strongest_claim.false_alarms_should_be_reduced_to_zero_regardless_of_cost",
        ),
        BriefOption(
            "since_the_real_incident_was_caught_the_false_alarm_rate_doesnt_matter",
            "lesson.l25.mastery.option.strongest_claim.since_the_real_incident_was_caught_the_false_alarm_rate_doesnt_matter",
        ),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l25.mastery.field.evidence.prompt",
    options=(
        BriefOption("false_alarm_avg_response_4_minutes", "lesson.l25.mastery.option.evidence.false_alarm_avg_response_4_minutes"),
        BriefOption("real_incident_avg_response_360_minutes", "lesson.l25.mastery.option.evidence.real_incident_avg_response_360_minutes"),
        BriefOption("false_alarm_count_46", "lesson.l25.mastery.option.evidence.false_alarm_count_46"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_five_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 25's real investigation: one continuous NovaMart
    KPI incident log, two real distinct decisions (which metric actually
    reflects each of the quarter's two real incidents), tested twice - an
    initial AlertConfigScene pass (guided=False - a motivated-reasoning
    trap, not a hidden-information one, since the live result preview is
    already real and inspectable before commit), two mandatory synthesis
    reveals (threshold tradeoff, incident coverage - two genuinely
    distinct mechanisms), then a real revision pass seeded with the first
    pass's own pick."""
    collected: dict = {}
    context = LessonContext()
    incident_log = _INCIDENT_LOG
    alert_fatigue = generate_alert_fatigue_data()

    def _restore_context_if_present() -> None:
        data_ = collected.get("analytical_context")
        if data_ is not None:
            context.restore_from_dict(data_)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    # --- Initial monitoring pass - a motivated-reasoning trap, not a
    # hidden-information one: the live result preview is already real and
    # inspectable before commit. -----------------------------------------

    def initial_monitoring_pass(advance):
        def on_complete(choices):
            collected["initial_monitoring_choices"] = choices
            _sync_context_into_collected()
            advance()

        return AlertConfigScene(
            app,
            "lesson.l25.builder_title",
            incident_log,
            MONITORING_REQUESTS,
            simulate_monitoring,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=monitoring_outcome_mirror_code,
        )

    # --- Two mandatory reveals - shown to every student regardless of
    # path. Each names a genuinely distinct mechanism. --------------------

    def threshold_tradeoff_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_threshold_tradeoff_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l25.threshold_tradeoff_reveal.title",
            narrative_keys=("dialogue.l25_threshold_tradeoff_reveal.line1", "dialogue.l25_threshold_tradeoff_reveal.line2"),
            comparisons=THRESHOLD_TRADEOFF_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l25.threshold_tradeoff_reveal.interpret_prompt",
            interpret_options=THRESHOLD_TRADEOFF_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def incident_coverage_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_incident_coverage_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l25.incident_coverage_reveal.title",
            narrative_keys=("dialogue.l25_incident_coverage_reveal.line1", "dialogue.l25_incident_coverage_reveal.line2"),
            comparisons=INCIDENT_COVERAGE_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l25.incident_coverage_reveal.interpret_prompt",
            interpret_options=INCIDENT_COVERAGE_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_monitoring_pass(advance):
        def on_complete(choices):
            collected["monitoring_choices"] = choices
            _sync_context_into_collected()
            advance()

        return AlertConfigScene(
            app,
            "lesson.l25.builder_title",
            incident_log,
            MONITORING_REQUESTS,
            simulate_monitoring,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_monitoring_choices"),
            mirror_python_code_for=monitoring_outcome_mirror_code,
        )

    # --- Final Decision Brief ---

    def final_decision_brief(advance):
        def on_complete(choices):
            collected["decision"] = choices
            context.set_decision(
                DecisionState(
                    choices={k: v for k, v in choices.items() if isinstance(v, str)},
                    supporting_evidence_ids=tuple(choices["evidence"]),
                )
            )
            _sync_context_into_collected()
            advance()

        return DecisionBuilderScene(
            app,
            "lesson.l25.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l25.mastery.title",
                (MASTERY_WHAT_46_FALSE_ALARMS_COST_FIELD, MASTERY_STRONGEST_CLAIM_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l25.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

    # --- Feedback / Debrief ---

    def _critical_evidence_present(selected_evidence_ids: set[str]) -> tuple[str, ...]:
        present: set[str] = set()
        for item in context.evidence:
            if item.id not in selected_evidence_ids:
                continue
            for critical_key in CRITICAL_EVIDENCE_KEYS:
                if critical_key in item.label_key:
                    present.add(critical_key)
        return tuple(sorted(present))

    def _build_result() -> LessonTwentyFiveResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyFiveResult(
            initial_monitoring_choices=collected.get("initial_monitoring_choices", {}),
            monitoring_choices=collected.get("monitoring_choices", {}),
            reveal_threshold_tradeoff_interpretation=collected.get("reveal_threshold_tradeoff_interpretation"),
            reveal_incident_coverage_interpretation=collected.get("reveal_incident_coverage_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_25.number, 0)
        evaluation = score_lesson_twenty_five(result, LESSON_25, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_monitoring_pass,
        threshold_tradeoff_reveal,
        incident_coverage_reveal,
        revision_intro,
        revision_monitoring_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=25,
        collected=collected,
        definition=LESSON_25,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
