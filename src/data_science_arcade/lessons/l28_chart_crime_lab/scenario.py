from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l28_chart_crime_lab.chart_data import (
    chart_pick_mirror_code,
    fair_rate_minimum_quarter_number,
    flawed_rate_minimum_quarter_number,
    generate_active_users_data,
    generate_returns_data,
    generate_satisfaction_data,
    rate_minimum_quarter_mirror_code,
    visual_amplification_mirror_code,
    visual_amplification_ratio,
    window_percent_change,
    window_percent_change_mirror_code,
)
from data_science_arcade.lessons.l28_chart_crime_lab.definition import LESSON_28
from data_science_arcade.lessons.l28_chart_crime_lab.requests import CHART_REQUESTS
from data_science_arcade.lessons.l28_chart_crime_lab.scoring import (
    ACTIVE_USERS_FIRST_TWO_MONTHS_CHANGE_EVIDENCE_KEY,
    ACTIVE_USERS_FULL_PERIOD_CHANGE_EVIDENCE_KEY,
    ACTIVE_USERS_LAST_TWO_MONTHS_CHANGE_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    LessonTwentyEightResult,
    MARKETING_SPEND_CHANGE_EVIDENCE_KEY,
    RETURNS_FAIR_RATE_MINIMUM_QUARTER_EVIDENCE_KEY,
    RETURNS_FLAWED_RATE_MINIMUM_QUARTER_EVIDENCE_KEY,
    SATISFACTION_DATA_GAP_EVIDENCE_KEY,
    SATISFACTION_VISUAL_AMPLIFICATION_EVIDENCE_KEY,
    SIGNUPS_CHANGE_EVIDENCE_KEY,
    score_lesson_twenty_eight,
)
from data_science_arcade.lessons.l28_chart_crime_lab.twist_data import generate_spend_signups_data, percent_change
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.dual_axis_reveal_scene import DualAxisRevealScene, DualAxisSeries
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui import colors
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l28_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l28_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_investigation.line3"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l28_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l28_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l28_mastery.line1",
    "dialogue.l28_mastery.line2",
    "dialogue.l28_mastery.line3",
)

# --- Four mandatory reveals - one per real mechanism, each showing a fact
# genuinely never visible side-by-side during the interactive picks. Zero
# InterpretOption.evidence_key anywhere: a student who picks the WRONG
# interpretation still saw the exact same real numbers and can cite them
# later. --------------------------------------------------------------


def _pct(value: float) -> str:
    return f"{value:+.1%}"


def _amplification(value: float) -> str:
    return f"{value:.1f}×"


def _gap_points(value: float) -> str:
    return f"{value:.1f} pts"


def _quarter(value: float) -> str:
    return f"Q{int(value)}"


# --- Reveal A: "Same Data, More Visual Space" - the satisfaction case's
# own real data gap (3.0 points, identical in both renderings) shown
# alongside the real visual-amplification ratio the truncated axis
# produces - a genuinely new synthesized fact, never printed anywhere
# during picking (the picker only ever prints the 4 raw point values). --

_SATISFACTION = generate_satisfaction_data()
_SATISFACTION_VALUES = tuple(float(v) for v in _SATISFACTION.frame["satisfaction_score"])
_SATISFACTION_GAP = max(_SATISFACTION_VALUES) - min(_SATISFACTION_VALUES)
_SATISFACTION_AMPLIFICATION = visual_amplification_ratio(_SATISFACTION_VALUES)

AXIS_REVEAL_COMPARISONS = (
    ComparisonValue(
        SATISFACTION_DATA_GAP_EVIDENCE_KEY,
        _SATISFACTION_GAP,
        python_code='satisfaction = pd.read_csv("novamart_quarterly_satisfaction.csv")\n'
        'axis_reveal_gap = satisfaction["satisfaction_score"].max() - satisfaction["satisfaction_score"].min()',
        value_format=_gap_points,
    ),
    ComparisonValue(
        SATISFACTION_VISUAL_AMPLIFICATION_EVIDENCE_KEY,
        _SATISFACTION_AMPLIFICATION,
        python_code=visual_amplification_mirror_code("satisfaction", "satisfaction_score", "axis_reveal_amplification"),
        value_format=_amplification,
    ),
)
AXIS_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l28.axis_reveal.interpret.option.{key}")
    for key in (
        "the_data_is_the_same_the_truncated_baseline_just_gives_it_more_space",
        "any_non_zero_baseline_chart_is_automatically_dishonest",
        "the_underlying_numbers_must_have_been_altered",
    )
)

# --- Reveal B: "Which Window Do You Believe?" - the active_users case's
# three real, competing window-dependent stories shown together, never
# rendered side by side during picking (only one option's own slice ever
# renders at a time). --------------------------------------------------

_ACTIVE_USERS = generate_active_users_data()
_ACTIVE_USERS_SORTED = tuple(float(v) for v in _ACTIVE_USERS.frame.sort_values("month_index")["active_users"])
_FULL_PERIOD_CHANGE = window_percent_change(_ACTIVE_USERS_SORTED)
_LAST_TWO_MONTHS_CHANGE = window_percent_change(_ACTIVE_USERS_SORTED[-2:])
_FIRST_TWO_MONTHS_CHANGE = window_percent_change(_ACTIVE_USERS_SORTED[:2])

WINDOW_REVEAL_COMPARISONS = (
    ComparisonValue(
        ACTIVE_USERS_FULL_PERIOD_CHANGE_EVIDENCE_KEY,
        _FULL_PERIOD_CHANGE,
        python_code='active_users = pd.read_csv("novamart_monthly_active_users.csv")\n'
        + window_percent_change_mirror_code("active_users", "active_users", "[:]", "window_reveal_full_period"),
        value_format=_pct,
    ),
    ComparisonValue(
        ACTIVE_USERS_LAST_TWO_MONTHS_CHANGE_EVIDENCE_KEY,
        _LAST_TWO_MONTHS_CHANGE,
        python_code=window_percent_change_mirror_code("active_users", "active_users", "[-2:]", "window_reveal_last_two"),
        value_format=_pct,
    ),
    ComparisonValue(
        ACTIVE_USERS_FIRST_TWO_MONTHS_CHANGE_EVIDENCE_KEY,
        _FIRST_TWO_MONTHS_CHANGE,
        python_code=window_percent_change_mirror_code("active_users", "active_users", "[:2]", "window_reveal_first_two"),
        value_format=_pct,
    ),
)
WINDOW_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l28.window_reveal.interpret.option.{key}")
    for key in (
        "the_same_dataset_supports_very_different_stories_depending_on_the_window",
        "any_partial_window_is_invalid_only_full_history_is_honest",
        "averaging_over_more_time_always_gives_the_one_true_number",
    )
)

# --- Reveal C: "The Wrong Population" - the returns case's real fair-vs-
# flawed rate minimum, showing the denominator doesn't just rescale the
# numbers, it changes which quarter looks best. --------------------------

_RETURNS = generate_returns_data()
_FAIR_MIN_QUARTER = fair_rate_minimum_quarter_number(_RETURNS)
_FLAWED_MIN_QUARTER = flawed_rate_minimum_quarter_number(_RETURNS)

DENOMINATOR_REVEAL_COMPARISONS = (
    ComparisonValue(
        RETURNS_FAIR_RATE_MINIMUM_QUARTER_EVIDENCE_KEY,
        _FAIR_MIN_QUARTER,
        python_code='returns = pd.read_csv("novamart_quarterly_returns.csv")\n'
        + rate_minimum_quarter_mirror_code("units_sold", "denominator_reveal_fair_min"),
        value_format=_quarter,
    ),
    ComparisonValue(
        RETURNS_FLAWED_RATE_MINIMUM_QUARTER_EVIDENCE_KEY,
        _FLAWED_MIN_QUARTER,
        python_code=rate_minimum_quarter_mirror_code("total_customers", "denominator_reveal_flawed_min"),
        value_format=_quarter,
    ),
)
DENOMINATOR_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l28.denominator_reveal.interpret.option.{key}")
    for key in (
        "the_denominator_changed_which_quarter_looks_best_not_just_the_size_of_the_numbers",
        "any_rate_built_on_a_large_denominator_is_automatically_suspect",
        "percentages_are_inherently_less_trustworthy_than_raw_counts",
    )
)

# --- Reveal D: "A Truthful Chart Can Still Argue" - the dual-axis Twist,
# promoted to a mandatory reveal that actually RENDERS the deceptive
# chart (two real series, independently scaled to their own start/end on
# one shared rect - the exact mechanism a rigged dual-axis chart uses),
# so the student sees the visual trick, not just a description of one. --

_SPEND_SIGNUPS = generate_spend_signups_data()
_SPEND_CHANGE = percent_change(_SPEND_SIGNUPS, "marketing_spend")
_SIGNUPS_CHANGE = percent_change(_SPEND_SIGNUPS, "signups")


def _dual_axis_series() -> tuple[DualAxisSeries, DualAxisSeries]:
    spend_row = _SPEND_SIGNUPS.frame[_SPEND_SIGNUPS.frame["metric"] == "marketing_spend"].iloc[0]
    signups_row = _SPEND_SIGNUPS.frame[_SPEND_SIGNUPS.frame["metric"] == "signups"].iloc[0]
    spend_series = DualAxisSeries(
        "lesson.l28.dual_axis_reveal.series.marketing_spend",
        (float(spend_row["start_value"]), float(spend_row["end_value"])),
        colors.BUTTON_FOCUS_BORDER,
    )
    signups_series = DualAxisSeries(
        "lesson.l28.dual_axis_reveal.series.signups",
        (float(signups_row["start_value"]), float(signups_row["end_value"])),
        colors.SEGMENT_SECONDARY,
    )
    return spend_series, signups_series


DUAL_AXIS_REVEAL_COMPARISONS = (
    ComparisonValue(
        MARKETING_SPEND_CHANGE_EVIDENCE_KEY,
        _SPEND_CHANGE,
        python_code='spend_signups = pd.read_csv("novamart_dual_axis_spend_signups.csv")\n'
        'spend_row = spend_signups[spend_signups["metric"] == "marketing_spend"].iloc[0]\n'
        'dual_axis_reveal_spend_change = float((spend_row["end_value"] - spend_row["start_value"]) / spend_row["start_value"])',
        value_format=_pct,
    ),
    ComparisonValue(
        SIGNUPS_CHANGE_EVIDENCE_KEY,
        _SIGNUPS_CHANGE,
        python_code='signups_row = spend_signups[spend_signups["metric"] == "signups"].iloc[0]\n'
        'dual_axis_reveal_signups_change = float((signups_row["end_value"] - signups_row["start_value"]) / signups_row["start_value"])',
        value_format=_pct,
    ),
)
DUAL_AXIS_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l28.dual_axis_reveal.interpret.option.{key}")
    for key in (
        "independent_axis_scaling_made_very_different_relative_changes_look_the_same",
        "dual_axis_charts_are_never_a_legitimate_choice",
        "as_long_as_both_lines_are_correctly_plotted_the_chart_is_honest",
    )
)

# --- Final Decision Brief - 4 REASONING fields + 1 OVERCONFIDENCE field + Evidence --

WHY_A_TRUNCATED_AXIS_MISLEADS_FIELD = BriefField(
    key="why_a_truncated_axis_misleads",
    prompt_key="lesson.l28.field.why_a_truncated_axis_misleads.prompt",
    options=(
        BriefOption(
            "same_data_difference_occupies_more_visual_space_when_the_baseline_is_truncated",
            "lesson.l28.option.why_a_truncated_axis_misleads.same_data_difference_occupies_more_visual_space_when_the_baseline_is_truncated",
        ),
        BriefOption(
            "any_non_zero_baseline_chart_is_automatically_dishonest",
            "lesson.l28.option.why_a_truncated_axis_misleads.any_non_zero_baseline_chart_is_automatically_dishonest",
        ),
        BriefOption(
            "the_underlying_numbers_must_have_been_altered",
            "lesson.l28.option.why_a_truncated_axis_misleads.the_underlying_numbers_must_have_been_altered",
        ),
    ),
)
WHY_CHERRY_PICKING_MISLEADS_FIELD = BriefField(
    key="why_cherry_picking_misleads",
    prompt_key="lesson.l28.field.why_cherry_picking_misleads.prompt",
    options=(
        BriefOption(
            "a_short_window_can_omit_material_context_the_full_period_would_show",
            "lesson.l28.option.why_cherry_picking_misleads.a_short_window_can_omit_material_context_the_full_period_would_show",
        ),
        BriefOption(
            "any_partial_window_is_invalid_only_full_history_is_honest",
            "lesson.l28.option.why_cherry_picking_misleads.any_partial_window_is_invalid_only_full_history_is_honest",
        ),
        BriefOption(
            "averaging_over_more_time_always_gives_the_one_true_number",
            "lesson.l28.option.why_cherry_picking_misleads.averaging_over_more_time_always_gives_the_one_true_number",
        ),
    ),
)
WHY_THE_WRONG_DENOMINATOR_MISLEADS_FIELD = BriefField(
    key="why_the_wrong_denominator_misleads",
    prompt_key="lesson.l28.field.why_the_wrong_denominator_misleads.prompt",
    options=(
        BriefOption(
            "the_denominator_must_match_the_population_the_question_implies",
            "lesson.l28.option.why_the_wrong_denominator_misleads.the_denominator_must_match_the_population_the_question_implies",
        ),
        BriefOption(
            "any_rate_built_on_a_large_denominator_is_automatically_suspect",
            "lesson.l28.option.why_the_wrong_denominator_misleads.any_rate_built_on_a_large_denominator_is_automatically_suspect",
        ),
        BriefOption(
            "percentages_are_inherently_less_trustworthy_than_raw_counts",
            "lesson.l28.option.why_the_wrong_denominator_misleads.percentages_are_inherently_less_trustworthy_than_raw_counts",
        ),
    ),
)
WHY_A_TRUTHFUL_CHART_CAN_STILL_MISLEAD_FIELD = BriefField(
    key="why_a_truthful_chart_can_still_mislead",
    prompt_key="lesson.l28.field.why_a_truthful_chart_can_still_mislead.prompt",
    options=(
        BriefOption(
            "independent_axis_scaling_can_make_different_relative_changes_look_comparable",
            "lesson.l28.option.why_a_truthful_chart_can_still_mislead.independent_axis_scaling_can_make_different_relative_changes_look_comparable",
        ),
        BriefOption(
            "dual_axis_charts_are_never_a_legitimate_choice",
            "lesson.l28.option.why_a_truthful_chart_can_still_mislead.dual_axis_charts_are_never_a_legitimate_choice",
        ),
        BriefOption(
            "as_long_as_both_lines_are_correctly_plotted_the_chart_is_honest",
            "lesson.l28.option.why_a_truthful_chart_can_still_mislead.as_long_as_both_lines_are_correctly_plotted_the_chart_is_honest",
        ),
    ),
)
CHART_REVIEW_STANDARD_FIELD = BriefField(
    key="chart_review_standard",
    prompt_key="lesson.l28.field.chart_review_standard.prompt",
    options=(
        BriefOption(
            "check_both_the_real_numbers_and_the_real_presentation",
            "lesson.l28.option.chart_review_standard.check_both_the_real_numbers_and_the_real_presentation",
        ),
        BriefOption(
            "any_chart_using_a_design_choice_like_axis_window_or_dual_axis_is_automatically_suspect",
            "lesson.l28.option.chart_review_standard.any_chart_using_a_design_choice_like_axis_window_or_dual_axis_is_automatically_suspect",
        ),
        BriefOption(
            "if_the_underlying_numbers_are_accurate_the_chart_cannot_mislead",
            "lesson.l28.option.chart_review_standard.if_the_underlying_numbers_are_accurate_the_chart_cannot_mislead",
        ),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l28.decision.evidence.prompt", min_count=5, max_count=9)
DECISION_FIELDS: tuple[BriefField, ...] = (
    WHY_A_TRUNCATED_AXIS_MISLEADS_FIELD,
    WHY_CHERRY_PICKING_MISLEADS_FIELD,
    WHY_THE_WRONG_DENOMINATOR_MISLEADS_FIELD,
    WHY_A_TRUTHFUL_CHART_CAN_STILL_MISLEAD_FIELD,
    CHART_REVIEW_STANDARD_FIELD,
)

# --- Optional mastery: a new, small NovaMart complaints dataset - no
# existing L28 dataset is free to promote (the dual-axis spend/signups
# dataset is this lesson's own mandatory Twist). Mirrors the returns
# case's own shape deliberately: the wrong denominator doesn't just
# rescale the numbers, it changes which quarter looks best/worst - same
# reflex, new domain. Copy stays in "real rate, wrong population" terms
# throughout, never "meaningless". -----------------------------------

MASTERY_WHAT_THE_FLAWED_RATE_SHOWS_FIELD = BriefField(
    key="mastery_what_the_flawed_rate_shows",
    prompt_key="lesson.l28.mastery.field.what_the_flawed_rate_shows.prompt",
    options=(
        BriefOption(
            "a_mathematically_real_rate_but_not_the_right_denominator_for_the_question",
            "lesson.l28.mastery.option.what_the_flawed_rate_shows.a_mathematically_real_rate_but_not_the_right_denominator_for_the_question",
        ),
        BriefOption(
            "proof_complaints_are_spiraling_out_of_control",
            "lesson.l28.mastery.option.what_the_flawed_rate_shows.proof_complaints_are_spiraling_out_of_control",
        ),
        BriefOption(
            "the_number_is_meaningless_and_should_be_ignored_entirely",
            "lesson.l28.mastery.option.what_the_flawed_rate_shows.the_number_is_meaningless_and_should_be_ignored_entirely",
        ),
    ),
)
MASTERY_STRONGEST_CLAIM_FIELD = BriefField(
    key="mastery_strongest_claim",
    prompt_key="lesson.l28.mastery.field.strongest_claim.prompt",
    options=(
        BriefOption(
            "the_correctly_denominated_rate_is_the_relevant_rate_for_this_question",
            "lesson.l28.mastery.option.strongest_claim.the_correctly_denominated_rate_is_the_relevant_rate_for_this_question",
        ),
        BriefOption(
            "the_flawed_rate_is_the_real_complaint_rate",
            "lesson.l28.mastery.option.strongest_claim.the_flawed_rate_is_the_real_complaint_rate",
        ),
        BriefOption(
            "since_one_rate_was_wrong_no_complaint_data_here_can_be_trusted",
            "lesson.l28.mastery.option.strongest_claim.since_one_rate_was_wrong_no_complaint_data_here_can_be_trusted",
        ),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l28.mastery.field.evidence.prompt",
    options=(
        BriefOption("fair_rate_q3_low_point", "lesson.l28.mastery.option.evidence.fair_rate_q3_low_point"),
        BriefOption("flawed_rate_q4_low_point", "lesson.l28.mastery.option.evidence.flawed_rate_q4_low_point"),
        BriefOption("lifetime_customers_90000", "lesson.l28.mastery.option.evidence.lifetime_customers_90000"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_eight_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 28's real investigation: three genuinely
    independent chart-review picks (a truncated axis, a cherry-picked
    window, a wrong denominator), tested twice - an initial
    ChartDesignerScene pass (guided=False - a motivated-reasoning trap,
    not a hidden-information one, since every rendered option already
    prints its own real numbers), four mandatory reveals (one per real
    mechanism, the fourth actually rendering the deceptive dual-axis
    chart), then a real revision pass seeded with the first pass's own
    pick."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        data_ = collected.get("analytical_context")
        if data_ is not None:
            context.restore_from_dict(data_)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    def _mirror_python_code_for(request, option, var_name: str) -> str:
        return chart_pick_mirror_code(request.key, option.key, var_name)

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    # --- Initial chart-review pass - a motivated-reasoning trap, not a
    # hidden-information one: every rendered option already prints its
    # own real numbers. -----------------------------------------------

    def initial_pass(advance):
        def on_complete(choices):
            collected["initial_verdict_choices"] = choices
            _sync_context_into_collected()
            advance()

        return ChartDesignerScene(
            app,
            "lesson.l28.chart_title",
            CHART_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=_mirror_python_code_for,
        )

    # --- Four mandatory reveals, one per real mechanism. ------------------

    def reveal_axis(advance):
        def on_complete(interpretation):
            collected["reveal_axis_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l28.axis_reveal.title",
            narrative_keys=("dialogue.l28_axis_reveal.line1", "dialogue.l28_axis_reveal.line2"),
            comparisons=AXIS_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l28.axis_reveal.interpret_prompt",
            interpret_options=AXIS_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def reveal_window(advance):
        def on_complete(interpretation):
            collected["reveal_window_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l28.window_reveal.title",
            narrative_keys=("dialogue.l28_window_reveal.line1", "dialogue.l28_window_reveal.line2"),
            comparisons=WINDOW_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l28.window_reveal.interpret_prompt",
            interpret_options=WINDOW_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def reveal_denominator(advance):
        def on_complete(interpretation):
            collected["reveal_denominator_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l28.denominator_reveal.title",
            narrative_keys=("dialogue.l28_denominator_reveal.line1", "dialogue.l28_denominator_reveal.line2"),
            comparisons=DENOMINATOR_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l28.denominator_reveal.interpret_prompt",
            interpret_options=DENOMINATOR_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def reveal_dual_axis(advance):
        def on_complete(interpretation):
            collected["reveal_dual_axis_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        series_a, series_b = _dual_axis_series()
        return DualAxisRevealScene(
            app,
            title_key="lesson.l28.dual_axis_reveal.title",
            narrative_keys=("dialogue.l28_dual_axis_reveal.line1", "dialogue.l28_dual_axis_reveal.line2"),
            series_a=series_a,
            series_b=series_b,
            comparisons=DUAL_AXIS_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l28.dual_axis_reveal.interpret_prompt",
            interpret_options=DUAL_AXIS_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_pass(advance):
        def on_complete(choices):
            collected["verdict_choices"] = choices
            _sync_context_into_collected()
            advance()

        return ChartDesignerScene(
            app,
            "lesson.l28.chart_title",
            CHART_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_verdict_choices"),
            mirror_python_code_for=_mirror_python_code_for,
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
            "lesson.l28.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l28.mastery.title",
                (MASTERY_WHAT_THE_FLAWED_RATE_SHOWS_FIELD, MASTERY_STRONGEST_CLAIM_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l28.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentyEightResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyEightResult(
            initial_verdict_choices=collected.get("initial_verdict_choices", {}),
            verdict_choices=collected.get("verdict_choices", {}),
            reveal_axis_interpretation=collected.get("reveal_axis_interpretation"),
            reveal_window_interpretation=collected.get("reveal_window_interpretation"),
            reveal_denominator_interpretation=collected.get("reveal_denominator_interpretation"),
            reveal_dual_axis_interpretation=collected.get("reveal_dual_axis_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_28.number, 0)
        evaluation = score_lesson_twenty_eight(result, LESSON_28, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_pass,
        reveal_axis,
        reveal_window,
        reveal_denominator,
        reveal_dual_axis,
        revision_intro,
        revision_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=28,
        collected=collected,
        definition=LESSON_28,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
