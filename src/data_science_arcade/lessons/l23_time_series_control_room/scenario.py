from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l23_time_series_control_room.definition import LESSON_23
from data_science_arcade.lessons.l23_time_series_control_room.kpi_data import (
    build_time_series,
    conversion_rate,
    day_rate_with_baseline_mirror_code,
    generate_kpi_data,
    timeseries_lens_mirror_code,
    weekday_baseline_mirror_code,
)
from data_science_arcade.lessons.l23_time_series_control_room.requests import TIME_SERIES_REQUESTS
from data_science_arcade.lessons.l23_time_series_control_room.scoring import (
    CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY,
    CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    LessonTwentyThreeResult,
    RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY,
    score_lesson_twenty_three,
)
from data_science_arcade.lessons.l23_time_series_control_room.twist_data import generate_delivery_alert_data, on_time_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.timeseries_scene import TimeSeriesScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l23_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l23_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_investigation.line2"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l23_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l23_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l23_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l23_mastery.line1",
    "dialogue.l23_mastery.line2",
    "dialogue.l23_mastery.line3",
)

# --- Two mandatory reveals - fixed, real reference values computed from
# the same NovaMart daily-conversion dataset. Zero InterpretOption.
# evidence_key anywhere: a student who picks the WRONG interpretation
# still saw the exact same real numbers and can cite them later. ---------

_KPI_DATASET = generate_kpi_data()


def _pct0(value: float) -> str:
    return f"{value:.0%}"


WEEKDAY_BASELINE_REVEAL_COMPARISONS = (
    ComparisonValue(
        CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "previous", 1),
        python_code=weekday_baseline_mirror_code(0, "baseline_reveal_mon_baseline"),
        value_format=_pct0,
    ),
    ComparisonValue(
        RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "previous", 13),
        python_code=weekday_baseline_mirror_code(5, "baseline_reveal_sat_baseline"),
        value_format=_pct0,
    ),
    ComparisonValue(
        RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "previous", 14),
        python_code=weekday_baseline_mirror_code(6, "baseline_reveal_sun_baseline"),
        value_format=_pct0,
    ),
    ComparisonValue(
        RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "current", 13),
        python_code=day_rate_with_baseline_mirror_code("current", 13, "baseline_reveal_sat_current"),
        value_format=_pct0,
    ),
    ComparisonValue(
        RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "current", 14),
        python_code=day_rate_with_baseline_mirror_code("current", 14, "baseline_reveal_sun_current"),
        value_format=_pct0,
    ),
)
WEEKDAY_BASELINE_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l23.weekday_baseline_reveal.interpret.option.{key}")
    for key in (
        "matches_recurring_baseline_no_extra_deviation",
        "proved_zero_effect_anywhere",
        "release_definitely_caused_the_dip",
    )
)

CAMPAIGN_DEVIATION_REVEAL_COMPARISONS = (
    ComparisonValue(
        CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "current", 8),
        python_code=day_rate_with_baseline_mirror_code("current", 8, "campaign_reveal_current"),
        value_format=_pct0,
    ),
    ComparisonValue(
        CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY,
        conversion_rate(_KPI_DATASET, "previous", 1),
        python_code=weekday_baseline_mirror_code(0, "campaign_reveal_baseline"),
        value_format=_pct0,
    ),
)
CAMPAIGN_DEVIATION_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l23.campaign_deviation_reveal.interpret.option.{key}")
    for key in (
        "real_deviation_not_causally_proven",
        "campaign_definitely_caused_exactly_plus_4pp",
        "just_normal_noise_nothing_unusual",
    )
)

# --- Final Time-Series Brief - 4 fields + Evidence ------------------------

BASELINE_FOR_RELEASE_CLAIM_FIELD = BriefField(
    key="baseline_for_release_claim",
    prompt_key="lesson.l23.field.baseline_for_release_claim.prompt",
    options=(
        BriefOption("weekday_aligned_reference_period", "lesson.l23.option.baseline_for_release_claim.weekday_aligned_reference_period"),
        BriefOption("nearby_days_only", "lesson.l23.option.baseline_for_release_claim.nearby_days_only"),
        BriefOption("single_previous_day_only", "lesson.l23.option.baseline_for_release_claim.single_previous_day_only"),
    ),
)
WHAT_POST_RELEASE_WEEKEND_SUPPORTS_FIELD = BriefField(
    key="what_post_release_weekend_supports",
    prompt_key="lesson.l23.field.what_post_release_weekend_supports.prompt",
    options=(
        BriefOption(
            "matches_ordinary_recurring_pattern_no_extra_deviation",
            "lesson.l23.option.what_post_release_weekend_supports.matches_ordinary_recurring_pattern_no_extra_deviation",
        ),
        BriefOption("proves_zero_effect_anywhere", "lesson.l23.option.what_post_release_weekend_supports.proves_zero_effect_anywhere"),
        BriefOption(
            "proves_release_definitely_caused_it", "lesson.l23.option.what_post_release_weekend_supports.proves_release_definitely_caused_it"
        ),
    ),
)
WHAT_CAMPAIGN_MONDAY_SUPPORTS_FIELD = BriefField(
    key="what_campaign_monday_supports",
    prompt_key="lesson.l23.field.what_campaign_monday_supports.prompt",
    options=(
        BriefOption(
            "real_observed_deviation_from_own_baseline", "lesson.l23.option.what_campaign_monday_supports.real_observed_deviation_from_own_baseline"
        ),
        BriefOption("proves_campaign_caused_the_rise", "lesson.l23.option.what_campaign_monday_supports.proves_campaign_caused_the_rise"),
        BriefOption("just_normal_noise", "lesson.l23.option.what_campaign_monday_supports.just_normal_noise"),
    ),
)
WHY_NEARBY_DAY_COMPARISON_MISLEADING_FIELD = BriefField(
    key="why_nearby_day_comparison_misleading",
    prompt_key="lesson.l23.field.why_nearby_day_comparison_misleading.prompt",
    options=(
        BriefOption(
            "conflates_different_weekdays_own_different_baselines",
            "lesson.l23.option.why_nearby_day_comparison_misleading.conflates_different_weekdays_own_different_baselines",
        ),
        BriefOption("nearby_days_are_always_best", "lesson.l23.option.why_nearby_day_comparison_misleading.nearby_days_are_always_best"),
        BriefOption("no_difference_between_methods", "lesson.l23.option.why_nearby_day_comparison_misleading.no_difference_between_methods"),
    ),
)
STRONGEST_DEFENSIBLE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_claim",
    prompt_key="lesson.l23.field.strongest_defensible_claim.prompt",
    options=(
        BriefOption(
            "no_extra_release_deviation_campaign_real_not_causally_proven",
            "lesson.l23.option.strongest_defensible_claim.no_extra_release_deviation_campaign_real_not_causally_proven",
        ),
        BriefOption(
            "release_and_campaign_both_definitely_caused_it", "lesson.l23.option.strongest_defensible_claim.release_and_campaign_both_definitely_caused_it"
        ),
        BriefOption("everything_here_is_just_calendar_noise", "lesson.l23.option.strongest_defensible_claim.everything_here_is_just_calendar_noise"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l23.decision.evidence.prompt", min_count=3, max_count=6)
DECISION_FIELDS: tuple[BriefField, ...] = (
    BASELINE_FOR_RELEASE_CLAIM_FIELD,
    WHAT_POST_RELEASE_WEEKEND_SUPPORTS_FIELD,
    WHAT_CAMPAIGN_MONDAY_SUPPORTS_FIELD,
    WHY_NEARBY_DAY_COMPARISON_MISLEADING_FIELD,
    STRONGEST_DEFENSIBLE_CLAIM_FIELD,
)

# --- Optional mastery: NovaMart Logistics delivery-holiday alert, a
# different domain reproducing the same recurring-vs-one-off shape. ------

MASTERY_FAIR_REFERENCE_FIELD = BriefField(
    key="mastery_fair_reference",
    prompt_key="lesson.l23.mastery.field.fair_reference.prompt",
    options=(
        BriefOption("compare_to_another_post_holiday_day", "lesson.l23.mastery.option.fair_reference.compare_to_another_post_holiday_day"),
        BriefOption("compare_to_a_random_normal_weekday", "lesson.l23.mastery.option.fair_reference.compare_to_a_random_normal_weekday"),
        BriefOption(
            "no_comparison_needed_the_number_speaks_for_itself",
            "lesson.l23.mastery.option.fair_reference.no_comparison_needed_the_number_speaks_for_itself",
        ),
    ),
)
MASTERY_INCIDENT_INTERPRETATION_FIELD = BriefField(
    key="mastery_incident_interpretation",
    prompt_key="lesson.l23.mastery.field.incident_interpretation.prompt",
    options=(
        BriefOption(
            "recurring_post_holiday_pattern_not_a_one_off",
            "lesson.l23.mastery.option.incident_interpretation.recurring_post_holiday_pattern_not_a_one_off",
        ),
        BriefOption(
            "unique_one_off_incident_needs_root_cause_investigation",
            "lesson.l23.mastery.option.incident_interpretation.unique_one_off_incident_needs_root_cause_investigation",
        ),
        BriefOption(
            "the_dip_is_unrelated_to_the_holiday_pure_coincidence",
            "lesson.l23.mastery.option.incident_interpretation.the_dip_is_unrelated_to_the_holiday_pure_coincidence",
        ),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l23.mastery.field.evidence.prompt",
    options=(
        BriefOption("spring_alert_71_percent", "lesson.l23.mastery.option.evidence.spring_alert_71_percent"),
        BriefOption("autumn_repeat_70_percent", "lesson.l23.mastery.option.evidence.autumn_repeat_70_percent"),
        BriefOption("recovered_within_two_days_88_percent", "lesson.l23.mastery.option.evidence.recovered_within_two_days_88_percent"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_three_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 23's real investigation: one continuous NovaMart
    daily-conversion case, one real decision (which comparison basis
    defends the post-release dip claim), tested twice - an initial
    TimeSeriesScene pass (guided=False - a motivated-reasoning trap, not
    a hidden-information one), two mandatory synthesis reveals, then a
    real revision pass seeded with the first pass's own pick."""
    collected: dict = {}
    context = LessonContext()
    kpi_data = _KPI_DATASET
    current_period = build_time_series(kpi_data, "current", "timeseries.current_period_label")
    previous_period = build_time_series(kpi_data, "previous", "timeseries.previous_period_label")
    delivery_data = generate_delivery_alert_data()

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

    # --- Initial lens pass - a motivated-reasoning trap, not a hidden-
    # information one: the full chart is already real and inspectable
    # before commit. -------------------------------------------------------

    def initial_lens_pass(advance):
        def on_complete(choices):
            collected["initial_lens_choices"] = choices
            _sync_context_into_collected()
            advance()

        return TimeSeriesScene(
            app,
            "lesson.l23.chart_title",
            current_period,
            previous_period,
            TIME_SERIES_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=timeseries_lens_mirror_code,
        )

    # --- Two mandatory reveals - shown to every student regardless of path

    def weekday_baseline_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_weekday_baseline_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l23.weekday_baseline_reveal.title",
            narrative_keys=("dialogue.l23_weekday_baseline_reveal.line1", "dialogue.l23_weekday_baseline_reveal.line2"),
            comparisons=WEEKDAY_BASELINE_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l23.weekday_baseline_reveal.interpret_prompt",
            interpret_options=WEEKDAY_BASELINE_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def campaign_deviation_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_campaign_deviation_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l23.campaign_deviation_reveal.title",
            narrative_keys=("dialogue.l23_campaign_deviation_reveal.line1",),
            comparisons=CAMPAIGN_DEVIATION_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l23.campaign_deviation_reveal.interpret_prompt",
            interpret_options=CAMPAIGN_DEVIATION_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_lens_pass(advance):
        def on_complete(choices):
            collected["lens_choices"] = choices
            _sync_context_into_collected()
            advance()

        return TimeSeriesScene(
            app,
            "lesson.l23.chart_title",
            current_period,
            previous_period,
            TIME_SERIES_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_lens_choices"),
            mirror_python_code_for=timeseries_lens_mirror_code,
        )

    # --- Final Time-Series Brief ---

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
            "lesson.l23.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l23.mastery.title",
                (MASTERY_FAIR_REFERENCE_FIELD, MASTERY_INCIDENT_INTERPRETATION_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l23.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentyThreeResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyThreeResult(
            initial_lens_choices=collected.get("initial_lens_choices", {}),
            lens_choices=collected.get("lens_choices", {}),
            reveal_weekday_baseline_interpretation=collected.get("reveal_weekday_baseline_interpretation"),
            reveal_campaign_deviation_interpretation=collected.get("reveal_campaign_deviation_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_23.number, 0)
        evaluation = score_lesson_twenty_three(result, LESSON_23, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_lens_pass,
        weekday_baseline_reveal,
        campaign_deviation_reveal,
        revision_intro,
        revision_lens_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=23,
        collected=collected,
        definition=LESSON_23,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
