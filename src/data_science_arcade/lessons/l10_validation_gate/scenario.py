from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l10_validation_gate.definition import LESSON_10
from data_science_arcade.lessons.l10_validation_gate.scoring import CRITICAL_EVIDENCE_KEYS, LessonTenResult, score_lesson_ten
from data_science_arcade.lessons.l10_validation_gate.twist_data import (
    BATCH_ACTION_ISSUE,
    CORRECT_BATCH_ACTION_KEY,
    CheckOutcome,
    GateOutcome,
    ROUND1_ISSUE,
    apply_round1,
    baseline_checks_passed,
    baseline_checks_python_code,
    concentration_python_code,
    evaluate_gate,
    final_dataset,
    generate_inventory_feed,
    generate_orders,
    invariant_fail_rate_by_source,
    invariant_python_code,
    naive_total,
    referral_null_python_code,
    total_python_code,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -----------------------------------------------------------
#
# Deliberately no literal statement of the lesson's own central reflex
# here or in Round 1's hint - the false-green temptation has to be a real
# one, not a test of whether the student remembers a sentence spoken 30
# seconds earlier. The reflex itself is only ever spoken out loud AFTER
# the student has lived through a real consequence (coverage_investigation,
# debrief) - see the L10 corrective-pass notes in decisions/IMPLEMENTATION_STATE.md.

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l10_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l10_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_briefing.line4"),
    )
)

COVERAGE_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_coverage.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_coverage.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_coverage.line3"),
    )
)

REPLAY_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_replay.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_replay.line2"),
    )
)

NO_REPLAY_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_no_replay.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_no_replay.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_debrief.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l10_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = ("dialogue.l10_mastery.line1", "dialogue.l10_mastery.line2")

# --- Baseline gate reveal ------------------------------------------------

BASELINE_INTERPRET_OPTIONS = (
    InterpretOption(
        "six_conditions_held",
        "lesson.l10.baseline.interpret.option.six_conditions_held",
        evidence_key="lesson.l10.evidence.baseline_all_green",
    ),
    InterpretOption("data_fully_correct", "lesson.l10.baseline.interpret.option.data_fully_correct"),
    InterpretOption("nothing_worth_checking", "lesson.l10.baseline.interpret.option.nothing_worth_checking"),
)

# --- Round 1 consequence reveal ------------------------------------------

CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption("ship_as_is", "lesson.l10.consequence.interpret.option.ship_as_is"),
    InterpretOption(
        "worth_checking_further",
        "lesson.l10.consequence.interpret.option.worth_checking_further",
        evidence_key="lesson.l10.evidence.naive_total_published",
    ),
    InterpretOption("recompute_blindly", "lesson.l10.consequence.interpret.option.recompute_blindly"),
)

# --- Gate Builder ---------------------------------------------------------
#
# optional_field_threshold's own correct pick (flag_over_2pct) has a real
# principled anchor, not an arbitrary number: referral_source has a real
# historical baseline null rate (~1%, see the field's own hint text) - a
# rate meaningfully above that is worth a warning, without crying wolf on
# ordinary noise or waiting until drift is severe. invariant_tolerance
# accepts BOTH real, explicit tolerance configurations as defensible
# (exact-match with an explicit rtol=0.0, or a small explicit absolute
# tolerance) - on this specific dataset both behave identically since
# there's no legitimate rounding noise to distinguish them; what's wrong
# is never declaring a tolerance at all (no_invariant_check).

OPTIONAL_FIELD_SEVERITY_FIELD = BriefField(
    key="optional_field_severity",
    prompt_key="lesson.l10.gate.field.optional_field_severity.prompt",
    hint_key="lesson.l10.gate.field.optional_field_severity.hint",
    options=(
        BriefOption("no_check", "lesson.l10.gate.option.optional_field_severity.no_check"),
        BriefOption("info_only", "lesson.l10.gate.option.optional_field_severity.info_only"),
        BriefOption("warn_at_threshold", "lesson.l10.gate.option.optional_field_severity.warn_at_threshold"),
        BriefOption("block", "lesson.l10.gate.option.optional_field_severity.block"),
    ),
)
OPTIONAL_FIELD_THRESHOLD_FIELD = BriefField(
    key="optional_field_threshold",
    prompt_key="lesson.l10.gate.field.optional_field_threshold.prompt",
    hint_key="lesson.l10.gate.field.optional_field_threshold.hint",
    options=(
        BriefOption("zero_tolerance", "lesson.l10.gate.option.optional_field_threshold.zero_tolerance"),
        BriefOption("flag_over_2pct", "lesson.l10.gate.option.optional_field_threshold.flag_over_2pct"),
        BriefOption("flag_over_10pct", "lesson.l10.gate.option.optional_field_threshold.flag_over_10pct"),
    ),
)
INVARIANT_TOLERANCE_FIELD = BriefField(
    key="invariant_tolerance",
    prompt_key="lesson.l10.gate.field.invariant_tolerance.prompt",
    hint_key="lesson.l10.gate.field.invariant_tolerance.hint",
    options=(
        BriefOption("no_invariant_check", "lesson.l10.gate.option.invariant_tolerance.no_invariant_check"),
        BriefOption("exact_match_atol_0", "lesson.l10.gate.option.invariant_tolerance.exact_match_atol_0"),
        BriefOption("small_tolerance_atol_1", "lesson.l10.gate.option.invariant_tolerance.small_tolerance_atol_1"),
    ),
)
INVARIANT_SEVERITY_FIELD = BriefField(
    key="invariant_severity",
    prompt_key="lesson.l10.gate.field.invariant_severity.prompt",
    hint_key="lesson.l10.gate.field.invariant_severity.hint",
    options=(
        BriefOption("no_action", "lesson.l10.gate.option.invariant_severity.no_action"),
        BriefOption("info_only", "lesson.l10.gate.option.invariant_severity.info_only"),
        BriefOption("warn_only", "lesson.l10.gate.option.invariant_severity.warn_only"),
        BriefOption("block", "lesson.l10.gate.option.invariant_severity.block"),
    ),
)
GATE_FIELDS: tuple[BriefField, ...] = (
    OPTIONAL_FIELD_SEVERITY_FIELD,
    OPTIONAL_FIELD_THRESHOLD_FIELD,
    INVARIANT_TOLERANCE_FIELD,
    INVARIANT_SEVERITY_FIELD,
)

# --- Gate rerun / concentration reveals -----------------------------------

GATE_RERUN_INTERPRET_OPTIONS = (
    InterpretOption(
        "reflects_only_written_checks",
        "lesson.l10.gate_rerun.interpret.option.reflects_only_written_checks",
        evidence_key="lesson.l10.evidence.gate_reflects_only_written_checks",
    ),
    InterpretOption("guarantees_data_is_fine", "lesson.l10.gate_rerun.interpret.option.guarantees_data_is_fine"),
    InterpretOption("result_is_meaningless", "lesson.l10.gate_rerun.interpret.option.result_is_meaningless"),
)

CONCENTRATION_INTERPRET_OPTIONS = (
    InterpretOption(
        "shared_process_failure",
        "lesson.l10.concentration.interpret.option.shared_process_failure",
        evidence_key="lesson.l10.evidence.concentration_by_source",
    ),
    InterpretOption("random_scattered_typos", "lesson.l10.concentration.interpret.option.random_scattered_typos"),
    InterpretOption("just_a_coincidence", "lesson.l10.concentration.interpret.option.just_a_coincidence"),
)

GATE_RERUN_CLEAN_INTERPRET_OPTIONS = (
    InterpretOption(
        "safe_to_publish",
        "lesson.l10.gate_rerun_clean.interpret.option.safe_to_publish",
        evidence_key="lesson.l10.evidence.corrected_total",
    ),
    InterpretOption("still_not_sure", "lesson.l10.gate_rerun_clean.interpret.option.still_not_sure"),
    InterpretOption(
        "could_have_published_earlier_number", "lesson.l10.gate_rerun_clean.interpret.option.could_have_published_earlier_number"
    ),
)

GATE_RERUN_UNRESOLVED_INTERPRET_OPTIONS = (
    InterpretOption(
        "still_unresolved",
        "lesson.l10.gate_rerun_unresolved.interpret.option.still_unresolved",
        evidence_key="lesson.l10.evidence.final_state_unresolved",
    ),
    InterpretOption(
        "safe_because_gate_didnt_block", "lesson.l10.gate_rerun_unresolved.interpret.option.safe_because_gate_didnt_block"
    ),
    InterpretOption("irrelevant_now", "lesson.l10.gate_rerun_unresolved.interpret.option.irrelevant_now"),
)

_STATUS_KEY_BY_SEVERITY: dict[str, str] = {
    "block": "lesson.l10.gate_rerun.status.blocked",
    "warn": "lesson.l10.gate_rerun.status.warn_triggered",
}
_OUTCOME_KEY_BY_VALUE: dict[str, str] = {
    "blocked": "lesson.l10.gate_rerun.outcome.blocked",
    "pass_with_warning": "lesson.l10.gate_rerun.outcome.pass_with_warning",
    "pass": "lesson.l10.gate_rerun.outcome.pass",
}


def _check_status_text(loc, outcome: CheckOutcome, affected_noun_key: str) -> str:
    if not outcome.exists:
        return loc.t("lesson.l10.gate_rerun.status.not_authored")
    base = f"{outcome.affected_count} / {outcome.affected_total} {loc.t(affected_noun_key)}"
    if outcome.assertion_passed:
        return f"{base} - {loc.t('lesson.l10.gate_rerun.status.clear')}"
    status_key = _STATUS_KEY_BY_SEVERITY.get(outcome.severity, "lesson.l10.gate_rerun.status.flagged_info_only")
    return f"{base} - {loc.t(status_key)}"


def _gate_outcome_text(loc, outcome: GateOutcome) -> str:
    return loc.t(_OUTCOME_KEY_BY_VALUE[outcome.outcome()])


# --- Final Decision --------------------------------------------------------

BASELINE_GATE_MEANING_FIELD = BriefField(
    key="baseline_gate_meaning",
    prompt_key="lesson.l10.decision.baseline_gate_meaning.prompt",
    options=(
        BriefOption("six_conditions_only", "lesson.l10.decision.baseline_gate_meaning.option.six_conditions_only"),
        BriefOption("data_fully_correct", "lesson.l10.decision.baseline_gate_meaning.option.data_fully_correct"),
        BriefOption("nothing_worth_checking", "lesson.l10.decision.baseline_gate_meaning.option.nothing_worth_checking"),
    ),
)

MISSING_COVERAGE_FIELD = BriefField(
    key="missing_coverage",
    prompt_key="lesson.l10.decision.missing_coverage.prompt",
    options=(
        BriefOption("cross_field_invariant_check", "lesson.l10.decision.missing_coverage.option.cross_field_invariant_check"),
        BriefOption("null_rate_check", "lesson.l10.decision.missing_coverage.option.null_rate_check"),
        BriefOption("stricter_range_check", "lesson.l10.decision.missing_coverage.option.stricter_range_check"),
    ),
)

INVARIANT_ACTION_FIELD = BriefField(
    key="invariant_action",
    prompt_key="lesson.l10.decision.invariant_action.prompt",
    options=(
        BriefOption("block", "lesson.l10.decision.invariant_action.option.block"),
        BriefOption("info_only", "lesson.l10.decision.invariant_action.option.info_only"),
        BriefOption("warn_only", "lesson.l10.decision.invariant_action.option.warn_only"),
        BriefOption("just_log_it", "lesson.l10.decision.invariant_action.option.just_log_it"),
    ),
)

BATCH_SCOPE_DECISION_FIELD = BriefField(
    key="batch_scope_decision",
    prompt_key="lesson.l10.decision.batch_scope_decision.prompt",
    options=(
        BriefOption("block_whole_batch_replay", "lesson.l10.decision.batch_scope_decision.option.block_whole_batch_replay"),
        BriefOption("quarantine_and_report_rest", "lesson.l10.decision.batch_scope_decision.option.quarantine_and_report_rest"),
        BriefOption("publish_anyway", "lesson.l10.decision.batch_scope_decision.option.publish_anyway"),
        BriefOption("investigate_only", "lesson.l10.decision.batch_scope_decision.option.investigate_only"),
    ),
)

PASS_MEANING_FIELD = BriefField(
    key="pass_meaning",
    prompt_key="lesson.l10.decision.pass_meaning.prompt",
    options=(
        BriefOption("satisfies_written_checks_only", "lesson.l10.decision.pass_meaning.option.satisfies_written_checks_only"),
        BriefOption("guaranteed_correct", "lesson.l10.decision.pass_meaning.option.guaranteed_correct"),
        BriefOption("no_further_review_needed", "lesson.l10.decision.pass_meaning.option.no_further_review_needed"),
    ),
)

PUBLISHED_TOTAL_DEFENSIBILITY_FIELD = BriefField(
    key="published_total_defensibility",
    prompt_key="lesson.l10.decision.published_total_defensibility.prompt",
    options=(
        BriefOption("report_different_number", "lesson.l10.decision.published_total_defensibility.option.report_different_number"),
        BriefOption("report_defensible", "lesson.l10.decision.published_total_defensibility.option.report_defensible"),
        BriefOption("report_provisional", "lesson.l10.decision.published_total_defensibility.option.report_provisional"),
        BriefOption("dont_report", "lesson.l10.decision.published_total_defensibility.option.dont_report"),
    ),
)

PREVENTION_OWNERSHIP_FIELD = BriefField(
    key="prevention_ownership",
    prompt_key="lesson.l10.decision.prevention_ownership.prompt",
    options=(
        BriefOption("cross_field_validation_required", "lesson.l10.decision.prevention_ownership.option.cross_field_validation_required"),
        BriefOption("manual_review_every_order", "lesson.l10.decision.prevention_ownership.option.manual_review_every_order"),
        BriefOption("widen_range_check", "lesson.l10.decision.prevention_ownership.option.widen_range_check"),
        BriefOption("nothing_needed", "lesson.l10.decision.prevention_ownership.option.nothing_needed"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l10.decision.evidence.prompt",
    min_count=3,
    max_count=5,
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BASELINE_GATE_MEANING_FIELD,
    MISSING_COVERAGE_FIELD,
    INVARIANT_ACTION_FIELD,
    BATCH_SCOPE_DECISION_FIELD,
    PASS_MEANING_FIELD,
    PUBLISHED_TOTAL_DEFENSIBILITY_FIELD,
    PREVENTION_OWNERSHIP_FIELD,
)

# --- Optional mastery -------------------------------------------------

MASTERY_MISSING_RULE_FIELD = BriefField(
    key="mastery_missing_rule",
    prompt_key="lesson.l10.mastery.field.missing_rule.prompt",
    options=(
        BriefOption("cross_field_invariant_check", "lesson.l10.mastery.option.missing_rule.cross_field_invariant_check"),
        BriefOption("null_rate_check", "lesson.l10.mastery.option.missing_rule.null_rate_check"),
        BriefOption("range_check", "lesson.l10.mastery.option.missing_rule.range_check"),
        BriefOption("uniqueness_check", "lesson.l10.mastery.option.missing_rule.uniqueness_check"),
    ),
)
MASTERY_SEVERITY_FIELD = BriefField(
    key="mastery_severity",
    prompt_key="lesson.l10.mastery.field.severity.prompt",
    options=(
        BriefOption("info_only", "lesson.l10.mastery.option.severity.info_only"),
        BriefOption("warn_only", "lesson.l10.mastery.option.severity.warn_only"),
        BriefOption("block", "lesson.l10.mastery.option.severity.block"),
        BriefOption("no_action", "lesson.l10.mastery.option.severity.no_action"),
    ),
)
MASTERY_PASS_MEANING_FIELD = BriefField(
    key="mastery_pass_meaning",
    prompt_key="lesson.l10.mastery.field.pass_meaning.prompt",
    options=(
        BriefOption("satisfies_written_checks_only", "lesson.l10.mastery.option.pass_meaning.satisfies_written_checks_only"),
        BriefOption("guaranteed_correct", "lesson.l10.mastery.option.pass_meaning.guaranteed_correct"),
        BriefOption("no_further_review_needed", "lesson.l10.mastery.option.pass_meaning.no_further_review_needed"),
    ),
)


def build_lesson_ten_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 10's real investigation: a 200-row NovaMart daily
    orders feed that passes 6 real, given baseline checks clean, while 50
    rows from one source system carry a real x100 unit-convention bug
    that only a cross-field invariant check can catch. LessonContext is
    threaded through every analytical stage exactly like L06-L09.

    Contract (corrective pass): authored rule -> real execution -> real
    PASS/WARN/BLOCK result -> revision opportunity. Unlike L09's IQR
    detector (deliberately GIVEN, never a student pick, since L09's own
    objective was never "design a check"), L10's own objective IS "design
    a cross-field check" - so gate_rerun_reveal and gate_rerun_clean both
    run evaluate_gate() against the student's own real gate_resolution,
    never a canonical reference calibration. A check the student never
    authored (an "opt out" pick) can never flag anything, however real
    the underlying problem is - the real business risk exists whether or
    not the student's own gate was built to catch it, but the gate
    itself only ever reports what it was actually told to check.
    concentration_reveal stays deliberately decoupled from the student's
    own gate_resolution (a manual, mentor-led "let's look at where this
    really concentrates, independent of what your gate found" beat) -
    otherwise a student who never authors the invariant check could never
    reach this real, load-bearing fact at all."""
    collected: dict = {}
    context = LessonContext()
    loc = app.localization

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    # --- Baseline gate reveal ---

    def baseline_gate_reveal(advance):
        dataset = generate_orders()
        passed = baseline_checks_passed(dataset)

        def on_complete(interpretation):
            collected["baseline_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l10.baseline.title",
            narrative_keys=("dialogue.l10_baseline.line1", "dialogue.l10_baseline.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l10.baseline.checks_passed_label",
                    float(passed),
                    python_code=baseline_checks_python_code(),
                    value_format=lambda v: f"{int(v)} / 6",
                ),
                ComparisonValue(
                    "lesson.l10.baseline.rows_in_batch_label", float(len(dataset.frame)), value_format=lambda v: f"{int(v)}"
                ),
            ),
            interpret_prompt_key="lesson.l10.baseline.interpret_prompt",
            interpret_options=BASELINE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Round 1 ---

    def round1(advance):
        def on_complete(resolution):
            collected["round1_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, generate_orders(), (ROUND1_ISSUE,), on_complete, guided=True, context=context)

    def consequence_reveal(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        total = naive_total(dataset)

        def on_complete(interpretation):
            collected["consequence_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l10.consequence.title",
            narrative_keys=("dialogue.l10_consequence.line1", "dialogue.l10_consequence.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l10.consequence.published_total_label", total, python_code=total_python_code(), value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue(
                    "lesson.l10.consequence.rows_included_label", float(len(dataset.frame)), value_format=lambda v: f"{int(v)}"
                ),
            ),
            interpret_prompt_key="lesson.l10.consequence.interpret_prompt",
            interpret_options=CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def round1_revision_offer(advance):
        collected["initial_round1_resolution"] = dict(collected.get("round1_resolution", {}))

        def build_revision_task(on_task_complete):
            def on_repair_complete(resolution):
                collected["round1_resolution"] = resolution
                collected["round1_revised"] = True
                _sync_context_into_collected()
                on_task_complete(None)

            return WorkbenchScene(app, generate_orders(), (ROUND1_ISSUE,), on_repair_complete, guided=True, context=context)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l10.round1_revision_offer.title",
            line_keys=("lesson.l10.round1_revision_offer.line1",),
            engage_label_key="lesson.l10.round1_revision_offer.engage",
            skip_label_key="lesson.l10.round1_revision_offer.skip",
        )

    # --- Coverage investigation ---

    def coverage_investigation(advance):
        return DialogueScene(app, COVERAGE_DIALOGUE, on_complete=advance)

    # --- Gate Builder ---

    def gate_builder(advance):
        def on_complete(brief):
            collected["gate_resolution"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l10.gate_builder.title", GATE_FIELDS, on_complete, guided=True)

    # --- Gate rerun reveal - runs the student's own real config ---

    def gate_rerun_reveal(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        gate_resolution = collected.get("gate_resolution", {})
        outcome = evaluate_gate(dataset, gate_resolution)

        def on_complete(interpretation):
            collected["gate_rerun_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        optional_code = referral_null_python_code() if outcome.optional_check.exists else None
        invariant_code = (
            invariant_python_code(atol=0.0 if gate_resolution.get("invariant_tolerance") == "exact_match_atol_0" else 1.0, rtol=0.0)
            if outcome.invariant_check.exists
            else None
        )

        return ComparisonRevealScene(
            app,
            title_key="lesson.l10.gate_rerun.title",
            narrative_keys=("dialogue.l10_gate_rerun.line1", "dialogue.l10_gate_rerun.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l10.gate_rerun.optional_check_label",
                    0.0,
                    python_code=optional_code,
                    value_format=lambda v, text=_check_status_text(loc, outcome.optional_check, "lesson.l10.gate_rerun.noun.missing"): text,
                ),
                ComparisonValue(
                    "lesson.l10.gate_rerun.invariant_check_label",
                    0.0,
                    python_code=invariant_code,
                    value_format=lambda v, text=_check_status_text(loc, outcome.invariant_check, "lesson.l10.gate_rerun.noun.mismatched"): text,
                ),
                ComparisonValue(
                    "lesson.l10.gate_rerun.outcome_label", 0.0, value_format=lambda v, text=_gate_outcome_text(loc, outcome): text
                ),
            ),
            interpret_prompt_key="lesson.l10.gate_rerun.interpret_prompt",
            interpret_options=GATE_RERUN_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def gate_revision_offer(advance):
        collected["initial_gate_resolution"] = dict(collected.get("gate_resolution", {}))

        def build_revision_task(on_task_complete):
            def on_gate_complete(brief):
                collected["gate_resolution"] = brief
                collected["gate_revised"] = True
                on_task_complete(None)

            return BriefBuilderScene(app, "lesson.l10.gate_builder.title", GATE_FIELDS, on_gate_complete, guided=True)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l10.gate_revision_offer.title",
            line_keys=("lesson.l10.gate_revision_offer.line1",),
            engage_label_key="lesson.l10.gate_revision_offer.engage",
            skip_label_key="lesson.l10.gate_revision_offer.skip",
        )

    # --- Concentration reveal - a manual investigation, independent of
    # --- whatever the student's own gate did or didn't catch ---

    def concentration_reveal(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        rates = invariant_fail_rate_by_source(dataset)

        def on_complete(interpretation):
            collected["concentration_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l10.concentration.title",
            narrative_keys=("dialogue.l10_concentration.line1", "dialogue.l10_concentration.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l10.concentration.checkout_v2_label",
                    rates.get("checkout_v2", 0.0),
                    python_code=concentration_python_code(),
                    value_format=lambda v: f"{v:.0%}",
                ),
                ComparisonValue(
                    "lesson.l10.concentration.legacy_pos_v1_label", rates.get("legacy_pos_v1", 0.0), value_format=lambda v: f"{v:.0%}"
                ),
            ),
            interpret_prompt_key="lesson.l10.concentration.interpret_prompt",
            interpret_options=CONCENTRATION_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Batch-action decision ---

    def batch_action(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))

        def on_complete(resolution):
            collected["batch_action_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, dataset, (BATCH_ACTION_ISSUE,), on_complete, guided=True, context=context)

    def batch_action_revision_offer(advance):
        collected["initial_batch_action_resolution"] = dict(collected.get("batch_action_resolution", {}))

        def build_revision_task(on_task_complete):
            def on_repair_complete(resolution):
                collected["batch_action_resolution"] = resolution
                collected["batch_action_revised"] = True
                _sync_context_into_collected()
                on_task_complete(None)

            dataset = apply_round1(collected.get("round1_resolution", {}))
            return WorkbenchScene(app, dataset, (BATCH_ACTION_ISSUE,), on_repair_complete, guided=True, context=context)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l10.batch_action_revision_offer.title",
            line_keys=("lesson.l10.batch_action_revision_offer.line1",),
            engage_label_key="lesson.l10.batch_action_revision_offer.engage",
            skip_label_key="lesson.l10.batch_action_revision_offer.skip",
        )

    # --- Simulated replay + path-aware final rerun ---

    def replay(advance):
        batch_action_resolution = collected.get("batch_action_resolution", {})
        dialogue = (
            REPLAY_DIALOGUE if batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY else NO_REPLAY_DIALOGUE
        )
        return DialogueScene(app, dialogue, on_complete=advance)

    def gate_rerun_clean(advance):
        round1_resolution = collected.get("round1_resolution", {})
        batch_action_resolution = collected.get("batch_action_resolution", {})
        gate_resolution = collected.get("gate_resolution", {})
        dataset = final_dataset(round1_resolution, batch_action_resolution)
        replay_happened = batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY
        outcome = evaluate_gate(dataset, gate_resolution)
        total = naive_total(dataset)

        def on_complete(interpretation):
            collected["gate_rerun_clean_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        checks_passed_value = ComparisonValue(
            "lesson.l10.gate_rerun_clean.checks_passed_label",
            float(outcome.assertions_passed()),
            value_format=lambda v, run=outcome.assertions_run(): f"{int(v)} / {run}",
        )
        outcome_value = ComparisonValue(
            "lesson.l10.gate_rerun.outcome_label", 0.0, value_format=lambda v, text=_gate_outcome_text(loc, outcome): text
        )

        if replay_happened:
            return ComparisonRevealScene(
                app,
                title_key="lesson.l10.gate_rerun_clean.title",
                narrative_keys=("dialogue.l10_gate_rerun_clean.line1", "dialogue.l10_gate_rerun_clean.line2"),
                comparisons=(
                    checks_passed_value,
                    outcome_value,
                    ComparisonValue(
                        "lesson.l10.gate_rerun_clean.corrected_total_label",
                        total,
                        python_code=total_python_code(),
                        value_format=lambda v: f"${v:,.2f}",
                    ),
                ),
                interpret_prompt_key="lesson.l10.gate_rerun_clean.interpret_prompt",
                interpret_options=GATE_RERUN_CLEAN_INTERPRET_OPTIONS,
                on_complete=on_complete,
                context=context,
                comparisons_are_evidence=False,
            )

        return ComparisonRevealScene(
            app,
            title_key="lesson.l10.gate_rerun_unresolved.title",
            narrative_keys=("dialogue.l10_gate_rerun_unresolved.line1", "dialogue.l10_gate_rerun_unresolved.line2"),
            comparisons=(
                checks_passed_value,
                outcome_value,
                ComparisonValue(
                    "lesson.l10.gate_rerun_unresolved.reported_total_label",
                    total,
                    python_code=total_python_code(),
                    value_format=lambda v: f"${v:,.2f}",
                ),
            ),
            interpret_prompt_key="lesson.l10.gate_rerun_unresolved.interpret_prompt",
            interpret_options=GATE_RERUN_UNRESOLVED_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Evidence review ---

    def evidence_review(advance):
        dataset = final_dataset(collected.get("round1_resolution", {}), collected.get("batch_action_resolution", {}))

        def on_complete(_resolution):
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(
            app,
            dataset,
            issues=(),
            on_complete=on_complete,
            context=context,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.EVIDENCE, WorkbenchTab.PYTHON),
        )

    # --- Final Decision ---

    def final_decision(advance):
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
            "lesson.l10.decision_title",
            steps=(
                BASELINE_GATE_MEANING_FIELD,
                MISSING_COVERAGE_FIELD,
                INVARIANT_ACTION_FIELD,
                BATCH_SCOPE_DECISION_FIELD,
                PASS_MEANING_FIELD,
                PUBLISHED_TOTAL_DEFENSIBILITY_FIELD,
                DECISION_EVIDENCE_FIELD,
                PREVENTION_OWNERSHIP_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            def on_inspect_complete(_resolution):
                sequence.advance_to_second()

            def build_select():
                return BriefBuilderScene(
                    app,
                    "lesson.l10.mastery.title",
                    (MASTERY_MISSING_RULE_FIELD, MASTERY_SEVERITY_FIELD, MASTERY_PASS_MEANING_FIELD),
                    on_task_complete,
                    guided=False,
                )

            sequence = SequenceScene(
                app,
                first=WorkbenchScene(
                    app,
                    generate_inventory_feed(),
                    issues=(),
                    on_complete=on_inspect_complete,
                    visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
                ),
                build_second=build_select,
            )
            return sequence

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l10.mastery.title",
            line_keys=MASTERY_DIALOGUE_KEYS,
        )

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

    def _build_result() -> LessonTenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTenResult(
            round1_resolution=collected.get("round1_resolution", {}),
            batch_action_resolution=collected.get("batch_action_resolution", {}),
            gate_resolution=collected.get("gate_resolution", {}),
            decision=decision,
            baseline_interpretation=collected.get("baseline_interpretation"),
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
            initial_round1_resolution=collected.get("initial_round1_resolution", {}),
            round1_revised=collected.get("round1_revised", False),
            initial_batch_action_resolution=collected.get("initial_batch_action_resolution", {}),
            batch_action_revised=collected.get("batch_action_revised", False),
            initial_gate_resolution=collected.get("initial_gate_resolution", {}),
            gate_revised=collected.get("gate_revised", False),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_10.number, 0)
        evaluation = score_lesson_ten(result, LESSON_10, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        baseline_gate_reveal,
        round1,
        consequence_reveal,
        round1_revision_offer,
        coverage_investigation,
        gate_builder,
        gate_rerun_reveal,
        gate_revision_offer,
        concentration_reveal,
        batch_action,
        batch_action_revision_offer,
        replay,
        gate_rerun_clean,
        evidence_review,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=10,
        collected=collected,
        definition=LESSON_10,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
