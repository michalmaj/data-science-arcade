from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import (
    cell_retention_mirror_code,
    cohort_comparison_mirror_code,
    build_cohort_matrix,
    generate_cohort_data,
    latest_observed_month,
    latest_observed_month_mirror_code,
    retention_rate,
)
from data_science_arcade.lessons.l22_cohort_observatory.definition import LESSON_22
from data_science_arcade.lessons.l22_cohort_observatory.requests import COHORT_REQUESTS
from data_science_arcade.lessons.l22_cohort_observatory.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    JAN_MONTH1_EVIDENCE_KEY,
    JAN_MONTH5_EVIDENCE_KEY,
    LessonTwentyTwoResult,
    MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY,
    MAY_MONTH1_EVIDENCE_KEY,
    NOV_MONTH1_EVIDENCE_KEY,
    NOV_MONTH5_EVIDENCE_KEY,
    score_lesson_twenty_two,
)
from data_science_arcade.lessons.l22_cohort_observatory.twist_data import (
    generate_november_cohort_data,
    november_retention_mirror_code,
    november_retention_rate,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.cohort_matrix_scene import CohortMatrixScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l22_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l22_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_investigation.line2"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l22_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l22_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l22_mastery.line1",
    "dialogue.l22_mastery.line2",
    "dialogue.l22_mastery.line3",
)

# --- Two mandatory reveals - fixed, real reference values computed from
# the same NovaMart Plus / November datasets, never the student's own
# picks (canonical-substitution discipline, matching L18-L21). Zero
# InterpretOption.evidence_key anywhere: a student who picks the WRONG
# interpretation still saw the exact same real numbers and can cite them
# later - only the numbers themselves (via comparisons_are_evidence=True)
# are evidence, never which interpretation a student happened to pick. ---

_COHORT_DATASET = generate_cohort_data()
_NOVEMBER_DATASET = generate_november_cohort_data()


def _pct0(value: float) -> str:
    return f"{value:.0%}"


def _bare_int(value: float) -> str:
    return f"{value:.0f}"


HORIZON_REVEAL_COMPARISONS = (
    ComparisonValue(
        MAY_MONTH1_EVIDENCE_KEY,
        retention_rate(_COHORT_DATASET, "may", 1),
        python_code=cell_retention_mirror_code("may", 1, "horizon_reveal_may_month1"),
        value_format=_pct0,
    ),
    ComparisonValue(
        JAN_MONTH1_EVIDENCE_KEY,
        retention_rate(_COHORT_DATASET, "jan", 1),
        python_code=cell_retention_mirror_code("jan", 1, "horizon_reveal_jan_month1"),
        value_format=_pct0,
    ),
    ComparisonValue(
        MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY,
        float(latest_observed_month(_COHORT_DATASET, "may")),
        python_code=latest_observed_month_mirror_code("may", "horizon_reveal_may_latest_month"),
        value_format=_bare_int,
    ),
)
HORIZON_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l22.horizon_reveal.interpret.option.{key}")
    for key in (
        "same_age_leads_but_only_month1_observed",
        "too_immature_to_tell_anything",
        "missing_months_count_as_zero",
    )
)

REVERSAL_REVEAL_COMPARISONS = (
    ComparisonValue(
        NOV_MONTH1_EVIDENCE_KEY,
        november_retention_rate(_NOVEMBER_DATASET, 1),
        python_code=november_retention_mirror_code(1, "reversal_reveal_nov_month1"),
        value_format=_pct0,
    ),
    ComparisonValue(
        JAN_MONTH1_EVIDENCE_KEY,
        retention_rate(_COHORT_DATASET, "jan", 1),
        python_code=cell_retention_mirror_code("jan", 1, "reversal_reveal_jan_month1"),
        value_format=_pct0,
    ),
    ComparisonValue(
        NOV_MONTH5_EVIDENCE_KEY,
        november_retention_rate(_NOVEMBER_DATASET, 5),
        python_code=november_retention_mirror_code(5, "reversal_reveal_nov_month5"),
        value_format=_pct0,
    ),
    ComparisonValue(
        JAN_MONTH5_EVIDENCE_KEY,
        retention_rate(_COHORT_DATASET, "jan", 5),
        python_code=cell_retention_mirror_code("jan", 5, "reversal_reveal_jan_month5"),
        value_format=_pct0,
    ),
)
REVERSAL_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l22.reversal_reveal.interpret.option.{key}")
    for key in (
        "month1_lead_was_real_but_didnt_guarantee_month5",
        "early_number_wasnt_real",
        "later_result_proves_early_was_wrong",
    )
)

# --- Final Decision Brief - 6 fields + Evidence --------------------------

BUSINESS_QUESTION_HORIZON_FIELD = BriefField(
    key="business_question_horizon",
    prompt_key="lesson.l22.field.business_question_horizon.prompt",
    options=(
        BriefOption(
            "two_separate_questions_early_and_long_term", "lesson.l22.option.business_question_horizon.two_separate_questions_early_and_long_term"
        ),
        BriefOption("only_asking_about_month_1", "lesson.l22.option.business_question_horizon.only_asking_about_month_1"),
        BriefOption("only_asking_about_long_term_loyalty", "lesson.l22.option.business_question_horizon.only_asking_about_long_term_loyalty"),
    ),
)
CORRECT_COMPARISON_BASIS_FIELD = BriefField(
    key="correct_comparison_basis",
    prompt_key="lesson.l22.field.correct_comparison_basis.prompt",
    options=(
        BriefOption("same_month_across_cohorts", "lesson.l22.option.correct_comparison_basis.same_month_across_cohorts"),
        BriefOption("mature_cohorts_own_best_month", "lesson.l22.option.correct_comparison_basis.mature_cohorts_own_best_month"),
        BriefOption("mays_own_month_0_against_others_month_1", "lesson.l22.option.correct_comparison_basis.mays_own_month_0_against_others_month_1"),
    ),
)
WHAT_MAY_MONTH1_SUPPORTS_FIELD = BriefField(
    key="what_may_month1_supports",
    prompt_key="lesson.l22.field.what_may_month1_supports.prompt",
    options=(
        BriefOption(
            "real_evidence_of_leading_early_retention_so_far", "lesson.l22.option.what_may_month1_supports.real_evidence_of_leading_early_retention_so_far"
        ),
        BriefOption("proves_permanent_improvement", "lesson.l22.option.what_may_month1_supports.proves_permanent_improvement"),
        BriefOption("doesnt_support_anything_yet", "lesson.l22.option.what_may_month1_supports.doesnt_support_anything_yet"),
    ),
)
CAN_MONTH5_BE_EVALUATED_FIELD = BriefField(
    key="can_month5_be_evaluated",
    prompt_key="lesson.l22.field.can_month5_be_evaluated.prompt",
    options=(
        BriefOption("no_data_doesnt_exist_yet", "lesson.l22.option.can_month5_be_evaluated.no_data_doesnt_exist_yet"),
        BriefOption("yes_assume_same_trend_as_month1", "lesson.l22.option.can_month5_be_evaluated.yes_assume_same_trend_as_month1"),
        BriefOption("yes_blank_cells_count_as_failing", "lesson.l22.option.can_month5_be_evaluated.yes_blank_cells_count_as_failing"),
    ),
)
BLANK_CELL_MEANING_FIELD = BriefField(
    key="blank_cell_meaning",
    prompt_key="lesson.l22.field.blank_cell_meaning.prompt",
    options=(
        BriefOption("cohort_hasnt_reached_that_month_yet", "lesson.l22.option.blank_cell_meaning.cohort_hasnt_reached_that_month_yet"),
        BriefOption("zero_percent_everyone_churned", "lesson.l22.option.blank_cell_meaning.zero_percent_everyone_churned"),
        BriefOption("a_tracking_data_quality_error", "lesson.l22.option.blank_cell_meaning.a_tracking_data_quality_error"),
    ),
)
STRONGEST_DEFENSIBLE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_claim",
    prompt_key="lesson.l22.field.strongest_defensible_claim.prompt",
    options=(
        BriefOption(
            "strong_observed_month1_long_term_not_yet_observed",
            "lesson.l22.option.strongest_defensible_claim.strong_observed_month1_long_term_not_yet_observed",
        ),
        BriefOption("may_clearly_improved_retention_overall", "lesson.l22.option.strongest_defensible_claim.may_clearly_improved_retention_overall"),
        BriefOption("cant_say_anything_about_may_yet", "lesson.l22.option.strongest_defensible_claim.cant_say_anything_about_may_yet"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l22.decision.evidence.prompt", min_count=4, max_count=6)
DECISION_FIELDS: tuple[BriefField, ...] = (
    BUSINESS_QUESTION_HORIZON_FIELD,
    CORRECT_COMPARISON_BASIS_FIELD,
    WHAT_MAY_MONTH1_SUPPORTS_FIELD,
    CAN_MONTH5_BE_EVALUATED_FIELD,
    BLANK_CELL_MEANING_FIELD,
    STRONGEST_DEFENSIBLE_CLAIM_FIELD,
)

# --- Optional mastery: NovaMart Logistics courier week-1 activation, a
# different domain reproducing the same ranking-reversal shape. ----------

MASTERY_FAIR_COMPARISON_FIELD = BriefField(
    key="mastery_fair_comparison",
    prompt_key="lesson.l22.mastery.field.fair_comparison.prompt",
    options=(
        BriefOption("compare_n_to_others_own_week1", "lesson.l22.mastery.option.fair_comparison.compare_n_to_others_own_week1"),
        BriefOption("compare_n_to_others_own_week8", "lesson.l22.mastery.option.fair_comparison.compare_n_to_others_own_week8"),
        BriefOption("compare_n_week1_to_o_week8", "lesson.l22.mastery.option.fair_comparison.compare_n_week1_to_o_week8"),
    ),
)
MASTERY_CLAIM_STRENGTH_FIELD = BriefField(
    key="mastery_claim_strength",
    prompt_key="lesson.l22.mastery.field.claim_strength.prompt",
    options=(
        BriefOption(
            "n_strongest_observed_week1_week8_unknown", "lesson.l22.mastery.option.claim_strength.n_strongest_observed_week1_week8_unknown"
        ),
        BriefOption("n_clearly_best_cohort_overall", "lesson.l22.mastery.option.claim_strength.n_clearly_best_cohort_overall"),
        BriefOption("cant_say_anything_about_n_yet", "lesson.l22.mastery.option.claim_strength.cant_say_anything_about_n_yet"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l22.mastery.field.evidence.prompt",
    options=(
        BriefOption("n_week1_82_percent", "lesson.l22.mastery.option.evidence.n_week1_82_percent"),
        BriefOption("h_reversal_week1_78_vs_week8_44", "lesson.l22.mastery.option.evidence.h_reversal_week1_78_vs_week8_44"),
        BriefOption("o_week8_52_percent", "lesson.l22.mastery.option.evidence.o_week8_52_percent"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_two_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 22's real investigation: one continuous NovaMart
    Plus cohort matrix, one real decision (which comparison basis
    defends May's own retention claim), tested twice - an initial
    CohortMatrixScene pass (guided=False - a motivated-reasoning trap, not
    a hidden-information one), two mandatory synthesis reveals, then a
    real revision pass seeded with the first pass's own pick."""
    collected: dict = {}
    context = LessonContext()
    cohort_data = _COHORT_DATASET
    matrix = build_cohort_matrix(cohort_data)

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

    # --- Initial matrix pass - a motivated-reasoning trap, not a hidden-
    # information one: the full matrix is already real and inspectable
    # before commit. -----------------------------------------------------

    def initial_matrix_pass(advance):
        def on_complete(choices):
            collected["initial_cohort_choices"] = choices
            _sync_context_into_collected()
            advance()

        return CohortMatrixScene(
            app,
            "lesson.l22.matrix_title",
            matrix,
            COHORT_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=cohort_comparison_mirror_code,
        )

    # --- Two mandatory reveals - shown to every student regardless of path

    def horizon_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_horizon_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l22.horizon_reveal.title",
            narrative_keys=("dialogue.l22_horizon_reveal.line1", "dialogue.l22_horizon_reveal.line2"),
            comparisons=HORIZON_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l22.horizon_reveal.interpret_prompt",
            interpret_options=HORIZON_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def reversal_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_reversal_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l22.reversal_reveal.title",
            narrative_keys=("dialogue.l22_reversal_reveal.line1",),
            comparisons=REVERSAL_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l22.reversal_reveal.interpret_prompt",
            interpret_options=REVERSAL_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_matrix_pass(advance):
        def on_complete(choices):
            collected["cohort_choices"] = choices
            _sync_context_into_collected()
            advance()

        return CohortMatrixScene(
            app,
            "lesson.l22.matrix_title",
            matrix,
            COHORT_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_cohort_choices"),
            mirror_python_code_for=cohort_comparison_mirror_code,
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
            "lesson.l22.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l22.mastery.title",
                (MASTERY_FAIR_COMPARISON_FIELD, MASTERY_CLAIM_STRENGTH_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l22.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentyTwoResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyTwoResult(
            initial_cohort_choices=collected.get("initial_cohort_choices", {}),
            cohort_choices=collected.get("cohort_choices", {}),
            reveal_horizon_interpretation=collected.get("reveal_horizon_interpretation"),
            reveal_reversal_interpretation=collected.get("reveal_reversal_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_22.number, 0)
        evaluation = score_lesson_twenty_two(result, LESSON_22, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_matrix_pass,
        horizon_reveal,
        reversal_reveal,
        revision_intro,
        revision_matrix_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=22,
        collected=collected,
        definition=LESSON_22,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
