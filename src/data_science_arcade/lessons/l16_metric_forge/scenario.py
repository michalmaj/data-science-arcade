from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l16_metric_forge import data as d
from data_science_arcade.lessons.l16_metric_forge.definition import LESSON_16
from data_science_arcade.lessons.l16_metric_forge.scoring import (
    AGED_BACKLOG_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    DEFINITION_STRESS_RESULT_EVIDENCE_KEY,
    GUARDRAIL_DETERIORATED_EVIDENCE_KEY,
    HEADLINE_IMPROVED_EVIDENCE_KEY,
    REVISED_CONTRACT_RESISTS_EVIDENCE_KEY,
    LessonSixteenResult,
    score_lesson_sixteen,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.metric_contract_scene import MetricContractScene, MetricDefinitionOption
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l16_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l16_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_briefing.line3"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l16_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l16_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_debrief.line3"),
    )
)
MASTERY_DIALOGUE_KEYS = ("dialogue.l16_mastery.line1", "dialogue.l16_mastery.line2")


def _pct(value: float) -> str:
    return f"{value:.1f}%"


# --- Ground truth, precomputed once (real, hand-verified via a real
# pandas script - see data.py's own module docstring) --------------------

HONEST = d.honest_tickets()
EARLY = d.early_snapshot(HONEST)
MATURE = d.mature_snapshot(HONEST)
STRESS_A = d.apply_stress_test_a(HONEST)
STRESS_B = d.apply_stress_test_b(HONEST)

EARLY_AS_OF_EXPR = "tickets['opened_at'].max() + pd.Timedelta(hours=24)"
MATURE_AS_OF_EXPR = "tickets['opened_at'].max() + pd.Timedelta(days=30)"

REOPEN_STRESS_A_PCT = d.reopen_rate(STRESS_A, MATURE) * 100
BACKLOG_STRESS_B_PCT = d.aged_backlog_rate(STRESS_B, MATURE) * 100
DEF_A_STRESS_B_PCT = d.definition_a_rate(STRESS_B, MATURE) * 100
DEF_B_STRESS_B_PCT = d.definition_b_rate(STRESS_B, MATURE) * 100

_VALUE_FUNCS = {
    "eligible_population": d.definition_a_rate,
    "closed_only": d.definition_b_rate,
    "durable": d.durable_resolution_rate,
}


def _value_for(definition_key: str, frame, as_of) -> float:
    return _VALUE_FUNCS[definition_key](frame, as_of)


# --- Raw ticket inspection - grain, before anything else ------------------

INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l16.inspection.prompt",
    hint_key="lesson.l16.inspection.hint",
    options=(
        InspectionOption("one_row_per_ticket", "lesson.l16.inspection.option.one_row_per_ticket"),
        InspectionOption("one_row_per_status_change", "lesson.l16.inspection.option.one_row_per_status_change"),
        InspectionOption("one_row_per_agent_day", "lesson.l16.inspection.option.one_row_per_agent_day"),
    ),
)

# --- Metric contract candidates - real, self-contained, live-computed ----


def _mirror_eligible(as_of_expr: str, frame_var: str = "tickets") -> str:
    return (
        f"as_of = {as_of_expr}\n"
        f"opened_by_asof = {frame_var}['opened_at'] <= as_of\n"
        f"closed_by_asof = {frame_var}['closed_at'].notna() & ({frame_var}['closed_at'] <= as_of)\n"
        f"resolved_24h = closed_by_asof & (({frame_var}['closed_at'] - {frame_var}['opened_at']) <= pd.Timedelta(hours=24))\n"
        "definition_a_rate = resolved_24h[opened_by_asof].mean()"
    )


def _mirror_closed_only(as_of_expr: str, frame_var: str = "tickets") -> str:
    return (
        f"as_of = {as_of_expr}\n"
        f"closed_by_asof = {frame_var}['closed_at'].notna() & ({frame_var}['closed_at'] <= as_of)\n"
        f"resolved_24h = closed_by_asof & (({frame_var}['closed_at'] - {frame_var}['opened_at']) <= pd.Timedelta(hours=24))\n"
        "definition_b_rate = resolved_24h[closed_by_asof].mean()"
    )


def _mirror_durable(as_of_expr: str, frame_var: str = "tickets") -> str:
    return (
        f"as_of = {as_of_expr}\n"
        f"opened_by_asof = {frame_var}['opened_at'] <= as_of\n"
        f"closed_by_asof = {frame_var}['closed_at'].notna() & ({frame_var}['closed_at'] <= as_of)\n"
        f"resolved_24h = closed_by_asof & (({frame_var}['closed_at'] - {frame_var}['opened_at']) <= pd.Timedelta(hours=24))\n"
        f"mature = opened_by_asof & ({frame_var}['opened_at'] <= as_of - pd.Timedelta(days=8))  # 24h resolution + 7d reopen window\n"
        f"reopened = {frame_var}['reopened_at'].notna() & ({frame_var}['reopened_at'] <= as_of) & "
        f"(({frame_var}['reopened_at'] - {frame_var}['closed_at']) <= pd.Timedelta(days=7))\n"
        "durable = resolved_24h & ~reopened\n"
        "durable_resolution_rate = durable[mature].mean()"
    )


_MIRROR_BUILDERS = {
    "eligible_population": _mirror_eligible,
    "closed_only": _mirror_closed_only,
    "durable": _mirror_durable,
}
_MIRROR_FINAL_VAR = {
    "eligible_population": "definition_a_rate",
    "closed_only": "definition_b_rate",
    "durable": "durable_resolution_rate",
}


def _mirror_for_chosen(chosen: str, as_of_expr: str, frame_var: str, result_name: str) -> str:
    """The chosen candidate's own real formula, applied to `frame_var`,
    with its own final value renamed to `result_name` - so a later reveal
    (or a test) can reference a stable, chosen-independent name rather
    than needing to know which of the 3 real variable names this
    particular student's own choice happens to produce."""
    body = _MIRROR_BUILDERS[chosen](as_of_expr, frame_var=frame_var)
    return f"{body}\n{result_name} = {_MIRROR_FINAL_VAR[chosen]}"


def _stress_frames_preamble() -> str:
    """Real, self-contained pandas deriving `stress_a_tickets` and
    `stress_b_tickets` from `tickets` alone - recorded once, as the first
    real action of the stress-test stage, so neither frame ever appears
    "magically" later in the Mirror (the same failure class L11's own
    hidden segment column had to be fixed for).

    The real 70-ticket subset both stress tests independently
    re-simulate is identified via a genuinely player-visible rule -
    tickets that honestly took longer than 24h to resolve - never the
    hidden `difficulty` column `tickets` itself never exposes."""
    return (
        "hard_tickets = tickets[(tickets['closed_at'] - tickets['opened_at']) > pd.Timedelta(hours=24)]\n"
        "stress_subset_ids = hard_tickets.sort_values('ticket_id')['ticket_id'].head(70)\n"
        "\n"
        "# Stress Test A - Close Fast: rush-close the subset; 56 of the 70\n"
        "# (80%) genuinely reopen 3 days after their own rushed close.\n"
        "stress_a_tickets = tickets.copy()\n"
        "rushed = stress_a_tickets['ticket_id'].isin(stress_subset_ids)\n"
        "stress_a_tickets.loc[rushed, 'closed_at'] = stress_a_tickets.loc[rushed, 'opened_at'] + pd.Timedelta(hours=20)\n"
        "reopened_ids = stress_subset_ids.head(56)\n"
        "reopened_mask = stress_a_tickets['ticket_id'].isin(reopened_ids)\n"
        "stress_a_tickets.loc[reopened_mask, 'reopened_at'] = stress_a_tickets.loc[reopened_mask, 'closed_at'] + pd.Timedelta(days=3)\n"
        "\n"
        "# Stress Test B - Leave Hard Tickets Open: an INDEPENDENT re-simulation\n"
        "# from the same honest baseline and the same real subset - not a\n"
        "# continuation of Stress Test A.\n"
        "stress_b_tickets = tickets.copy()\n"
        "left_open = stress_b_tickets['ticket_id'].isin(stress_subset_ids)\n"
        "stress_b_tickets.loc[left_open, 'closed_at'] = pd.NaT"
    )


def _build_candidates(frame, as_of, as_of_expr: str) -> tuple[MetricDefinitionOption, ...]:
    """3 real, fully self-contained candidates - each own mirror_code
    redefines everything it needs (never depends on another candidate's
    own action, since only whichever ONE gets picked is ever recorded)."""
    return (
        MetricDefinitionOption(
            key="eligible_population",
            label_key="lesson.l16.metric.eligible_population",
            numerator_key="lesson.l16.metric.numerator.resolved_24h",
            denominator_key="lesson.l16.metric.denominator.eligible_population",
            window_key="lesson.l16.metric.window.no_wait",
            mirror_code=_mirror_eligible(as_of_expr),
            value=d.definition_a_rate(frame, as_of),
        ),
        MetricDefinitionOption(
            key="closed_only",
            label_key="lesson.l16.metric.closed_only",
            numerator_key="lesson.l16.metric.numerator.resolved_24h",
            denominator_key="lesson.l16.metric.denominator.closed_only",
            window_key="lesson.l16.metric.window.no_wait",
            mirror_code=_mirror_closed_only(as_of_expr),
            value=d.definition_b_rate(frame, as_of),
        ),
        MetricDefinitionOption(
            key="durable",
            label_key="lesson.l16.metric.durable",
            numerator_key="lesson.l16.metric.numerator.durable",
            denominator_key="lesson.l16.metric.denominator.durable",
            window_key="lesson.l16.metric.window.durable",
            mirror_code=_mirror_durable(as_of_expr),
            value=d.durable_resolution_rate(frame, as_of),
        ),
    )


# --- Guardrail selection (re-asked, fresh, at revision too) ---------------

GUARDRAIL_FIELD = MultiChoiceField(
    key="guardrails",
    prompt_key="lesson.l16.guardrails.prompt",
    hint_key="lesson.l16.guardrails.hint",
    options=(
        BriefOption("reopen_rate", "lesson.l16.guardrails.option.reopen_rate"),
        BriefOption("aged_backlog_rate", "lesson.l16.guardrails.option.aged_backlog_rate"),
        BriefOption("avg_time_to_close", "lesson.l16.guardrails.option.avg_time_to_close"),
    ),
    min_count=1,
    max_count=2,
)

# --- Prior success verdict - a real, unscored trajectory-only capture,
# taken right after Stress Test A's own primary-metric reveal but BEFORE
# its guardrail reveal - the real before-signal for OVERCONFIDENCE. -------

PRIOR_VERDICT_FIELD = BriefField(
    key="prior_success_verdict",
    prompt_key="lesson.l16.prior_verdict.prompt",
    hint_key="lesson.l16.prior_verdict.hint",
    options=(
        BriefOption("ship_it_success", "lesson.l16.prior_verdict.option.ship_it_success"),
        BriefOption("not_yet_needs_guardrails", "lesson.l16.prior_verdict.option.not_yet_needs_guardrails"),
        BriefOption("depends_on_more_data", "lesson.l16.prior_verdict.option.depends_on_more_data"),
    ),
)

# --- Stress test reveal interpret options - every option within one
# reveal shares the SAME evidence_key ("fact seen != correct
# interpretation," the discipline every ComparisonRevealScene reveal in
# this codebase already follows). -----------------------------------------

STRESS_A_PRIMARY_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l16.stress_a_primary.interpret.option.{key}", evidence_key=HEADLINE_IMPROVED_EVIDENCE_KEY)
    for key in ("looks_solved_already", "impressive_but_need_more_signals", "probably_a_measurement_artifact")
)
STRESS_A_GUARDRAIL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l16.stress_a_guardrail.interpret.option.{key}", evidence_key=GUARDRAIL_DETERIORATED_EVIDENCE_KEY)
    for key in ("reopens_show_work_wasnt_durable", "reopens_are_unrelated_noise", "guardrail_itself_is_the_real_problem")
)
STRESS_B_DEFINITION_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l16.stress_b_definition.interpret.option.{key}", evidence_key=DEFINITION_STRESS_RESULT_EVIDENCE_KEY)
    for key in ("population_denominator_held", "closed_only_denominator_was_fooled", "both_denominators_behave_the_same")
)
STRESS_B_BACKLOG_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l16.stress_b_backlog.interpret.option.{key}", evidence_key=AGED_BACKLOG_EVIDENCE_KEY)
    for key in ("hidden_cost_the_ratio_cant_see", "backlog_growth_is_expected_here", "backlog_doesnt_matter_if_ratio_is_high")
)
RERUN_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l16.rerun.interpret.option.{key}", evidence_key=REVISED_CONTRACT_RESISTS_EVIDENCE_KEY)
    for key in ("fully_resists_both", "resists_one_not_the_other", "resists_neither")
)

# --- Final Metric Brief ----------------------------------------------------

BUSINESS_OUTCOME_FIELD = BriefField(
    key="business_outcome",
    prompt_key="lesson.l16.decision.business_outcome.prompt",
    options=(
        BriefOption("durable_not_a_single_number", "lesson.l16.decision.business_outcome.option.durable_not_a_single_number"),
        BriefOption("primary_metric_alone", "lesson.l16.decision.business_outcome.option.primary_metric_alone"),
        BriefOption("fastest_possible_closure", "lesson.l16.decision.business_outcome.option.fastest_possible_closure"),
    ),
)
DENOMINATOR_CHOICE_RATIONALE_FIELD = BriefField(
    key="denominator_choice_rationale",
    prompt_key="lesson.l16.decision.denominator_choice_rationale.prompt",
    options=(
        BriefOption("cant_shrink_by_leaving_open", "lesson.l16.decision.denominator_choice_rationale.option.cant_shrink_by_leaving_open"),
        BriefOption("its_simpler_to_compute", "lesson.l16.decision.denominator_choice_rationale.option.its_simpler_to_compute"),
        BriefOption("it_always_gives_a_higher_number", "lesson.l16.decision.denominator_choice_rationale.option.it_always_gives_a_higher_number"),
    ),
)
MATURITY_WINDOW_REASONING_FIELD = BriefField(
    key="maturity_window_reasoning",
    prompt_key="lesson.l16.decision.maturity_window_reasoning.prompt",
    options=(
        BriefOption("immature_hasnt_had_its_window", "lesson.l16.decision.maturity_window_reasoning.option.immature_hasnt_had_its_window"),
        BriefOption("makes_the_number_look_better", "lesson.l16.decision.maturity_window_reasoning.option.makes_the_number_look_better"),
        BriefOption("not_actually_necessary", "lesson.l16.decision.maturity_window_reasoning.option.not_actually_necessary"),
    ),
)
NUMERATOR_LOOPHOLE_FIELD = BriefField(
    key="numerator_loophole",
    prompt_key="lesson.l16.decision.numerator_loophole.prompt",
    options=(
        BriefOption("closing_without_finishing", "lesson.l16.decision.numerator_loophole.option.closing_without_finishing"),
        BriefOption("definition_a_denominator_is_broken", "lesson.l16.decision.numerator_loophole.option.definition_a_denominator_is_broken"),
        BriefOption("we_need_a_csat_guardrail_instead", "lesson.l16.decision.numerator_loophole.option.we_need_a_csat_guardrail_instead"),
    ),
)
DENOMINATOR_LOOPHOLE_FIELD = BriefField(
    key="denominator_loophole",
    prompt_key="lesson.l16.decision.denominator_loophole.prompt",
    options=(
        BriefOption(
            "closed_only_denominator_hides_backlog", "lesson.l16.decision.denominator_loophole.option.closed_only_denominator_hides_backlog"
        ),
        BriefOption("definition_a_is_just_as_vulnerable", "lesson.l16.decision.denominator_loophole.option.definition_a_is_just_as_vulnerable"),
        BriefOption("reopen_rate_catches_this_too", "lesson.l16.decision.denominator_loophole.option.reopen_rate_catches_this_too"),
    ),
)
GUARDRAIL_BREACH_ACTION_FIELD = BriefField(
    key="guardrail_breach_action",
    prompt_key="lesson.l16.decision.guardrail_breach_action.prompt",
    options=(
        BriefOption("gate_on_guardrails", "lesson.l16.decision.guardrail_breach_action.option.gate_on_guardrails"),
        BriefOption("ship_anyway", "lesson.l16.decision.guardrail_breach_action.option.ship_anyway"),
        BriefOption("redefine_the_guardrail", "lesson.l16.decision.guardrail_breach_action.option.redefine_the_guardrail"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l16.decision.evidence.prompt", min_count=3, max_count=5)
DECISION_FIELDS: tuple[BriefField, ...] = (
    BUSINESS_OUTCOME_FIELD,
    DENOMINATOR_CHOICE_RATIONALE_FIELD,
    MATURITY_WINDOW_REASONING_FIELD,
    NUMERATOR_LOOPHOLE_FIELD,
    DENOMINATOR_LOOPHOLE_FIELD,
    GUARDRAIL_BREACH_ACTION_FIELD,
)

# --- Optional mastery: NovaMart Logistics picker productivity, a
# different domain - same evidence/claim pairing discipline from day one.

MASTERY_JUDGMENT_FIELD = BriefField(
    key="mastery_metric_system_judgment",
    prompt_key="lesson.l16.mastery.field.judgment.prompt",
    options=(
        BriefOption(
            "productivity_needs_completeness_guardrail", "lesson.l16.mastery.option.judgment.productivity_needs_completeness_guardrail"
        ),
        BriefOption("items_per_hour_alone", "lesson.l16.mastery.option.judgment.items_per_hour_alone"),
        BriefOption("switch_to_bulky_only", "lesson.l16.mastery.option.judgment.switch_to_bulky_only"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l16.mastery.field.evidence.prompt",
    options=(
        BriefOption("narrow_optimization_hits_forty", "lesson.l16.mastery.option.evidence.narrow_optimization_hits_forty"),
        BriefOption("completeness_collapsed", "lesson.l16.mastery.option.evidence.completeness_collapsed"),
        BriefOption("labor_hours_stayed_fixed", "lesson.l16.mastery.option.evidence.labor_hours_stayed_fixed"),
        BriefOption("bulky_items_take_longer", "lesson.l16.mastery.option.evidence.bulky_items_take_longer"),
    ),
    min_count=1,
    max_count=2,
)


def build_lesson_sixteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 16's real investigation: one real 500-ticket
    NovaMart Support population (data.py), the same population re-used
    for every beat - never three independent mini-simulators. LessonContext
    is threaded through every analytical stage exactly like L06-L15.

    METHOD scores only the FINAL EXECUTED contract (primary_definition +
    guardrails, after the one revision); REASONING scores the Final Metric
    Brief's own comprehension checks - deliberately independent signals
    (see test_lesson16_scenario.py's own method/reasoning independence
    regressions)."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        data_ = collected.get("analytical_context")
        if data_ is not None:
            context.restore_from_dict(data_)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def raw_ticket_inspection(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            d.generate_tickets(),
            issues=(),
            on_complete=on_complete,
            inspection_prompt=INSPECTION_PROMPT,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    # --- Initial metric contract (definition + guardrails) ---

    def initial_contract(advance):
        def on_contract_complete(choice):
            collected["primary_definition"] = choice
            _sync_context_into_collected()
            composite.advance_to_second()

        def on_guardrail_complete(choices):
            collected["guardrails"] = choices["guardrails"]
            _sync_context_into_collected()
            advance()

        def build_guardrail():
            return BriefBuilderScene(app, "lesson.l16.guardrails.title", (GUARDRAIL_FIELD,), on_guardrail_complete, guided=True)

        contract_scene = MetricContractScene(
            app,
            "lesson.l16.contract.title",
            "lesson.l16.contract.ask",
            _build_candidates(HONEST, EARLY, EARLY_AS_OF_EXPR),
            on_contract_complete,
            context,
            hint_key="lesson.l16.contract.hint",
            guided=True,
        )
        composite = SequenceScene(app, first=contract_scene, build_second=build_guardrail)
        return composite

    # --- Stress Test A - Close Fast (numerator/event gaming) ---

    def _stress_a_primary_reveal(on_complete):
        chosen = collected["primary_definition"]
        before = _value_for(chosen, HONEST, MATURE) * 100
        after = _value_for(chosen, STRESS_A, MATURE) * 100
        return ComparisonRevealScene(
            app,
            title_key="lesson.l16.stress_a_primary.title",
            narrative_keys=("dialogue.l16_stress_a.line1", "dialogue.l16_stress_a.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l16.stress_a_primary.before_label",
                    before,
                    python_code=(
                        _stress_frames_preamble()
                        + "\n\n"
                        + _mirror_for_chosen(chosen, MATURE_AS_OF_EXPR, "tickets", "honest_baseline_rate")
                    ),
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l16.stress_a_primary.after_label",
                    after,
                    python_code=_mirror_for_chosen(chosen, MATURE_AS_OF_EXPR, "stress_a_tickets", "stress_a_primary_rate"),
                    value_format=_pct,
                ),
            ),
            interpret_prompt_key="lesson.l16.stress_a_primary.interpret_prompt",
            interpret_options=STRESS_A_PRIMARY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def _stress_a_guardrail_reveal(on_complete):
        return ComparisonRevealScene(
            app,
            title_key="lesson.l16.stress_a_guardrail.title",
            narrative_keys=("dialogue.l16_stress_a_guardrail.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l16.stress_a_guardrail.before_label",
                    0.0,
                    python_code="reopen_rate_before = 0.0  # honest baseline",
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l16.stress_a_guardrail.after_label",
                    REOPEN_STRESS_A_PCT,
                    python_code=(
                        "reopened = stress_a_tickets['reopened_at'].notna() & (stress_a_tickets['reopened_at'] <= as_of) & "
                        "((stress_a_tickets['reopened_at'] - stress_a_tickets['closed_at']) <= pd.Timedelta(days=7))\n"
                        "reopen_rate_after = reopened[closed_by_asof].mean()"
                    ),
                    value_format=_pct,
                ),
            ),
            interpret_prompt_key="lesson.l16.stress_a_guardrail.interpret_prompt",
            interpret_options=STRESS_A_GUARDRAIL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def stress_test_a(advance):
        def on_primary_complete(_interpretation):
            _sync_context_into_collected()
            composite.advance_to_second()

        def on_verdict_complete(choices):
            collected["prior_success_verdict"] = choices["prior_success_verdict"]
            _sync_context_into_collected()
            inner.advance_to_second()

        def on_guardrail_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        def build_verdict():
            return BriefBuilderScene(app, "lesson.l16.prior_verdict.title", (PRIOR_VERDICT_FIELD,), on_verdict_complete, guided=True)

        inner = SequenceScene(app, first=build_verdict(), build_second=lambda: _stress_a_guardrail_reveal(on_guardrail_complete))
        composite = SequenceScene(app, first=_stress_a_primary_reveal(on_primary_complete), build_second=lambda: inner)
        return composite

    # --- Stress Test B - Leave Hard Tickets Open (denominator gaming) ---

    def _stress_b_definition_reveal(on_complete):
        return ComparisonRevealScene(
            app,
            title_key="lesson.l16.stress_b_definition.title",
            narrative_keys=("dialogue.l16_stress_b.line1", "dialogue.l16_stress_b.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l16.stress_b_definition.population_denominator_label",
                    DEF_A_STRESS_B_PCT,
                    python_code=(
                        f"as_of = {MATURE_AS_OF_EXPR}\n"
                        "closed_by_asof = stress_b_tickets['closed_at'].notna() & (stress_b_tickets['closed_at'] <= as_of)\n"
                        "resolved_24h = closed_by_asof & ((stress_b_tickets['closed_at'] - stress_b_tickets['opened_at']) <= pd.Timedelta(hours=24))\n"
                        "opened_by_asof = stress_b_tickets['opened_at'] <= as_of\n"
                        "population_denominator_rate = resolved_24h[opened_by_asof].mean()"
                    ),
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l16.stress_b_definition.closed_only_label",
                    DEF_B_STRESS_B_PCT,
                    python_code="closed_only_rate = resolved_24h[closed_by_asof].mean()",
                    value_format=_pct,
                ),
            ),
            interpret_prompt_key="lesson.l16.stress_b_definition.interpret_prompt",
            interpret_options=STRESS_B_DEFINITION_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def _stress_b_backlog_reveal(on_complete):
        return ComparisonRevealScene(
            app,
            title_key="lesson.l16.stress_b_backlog.title",
            narrative_keys=("dialogue.l16_stress_b_backlog.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l16.stress_b_backlog.before_label", 0.0, python_code="aged_backlog_before = 0.0  # honest baseline", value_format=_pct
                ),
                ComparisonValue(
                    "lesson.l16.stress_b_backlog.after_label",
                    BACKLOG_STRESS_B_PCT,
                    python_code="aged_backlog_after = (~closed_by_asof)[opened_by_asof].mean()",
                    value_format=_pct,
                ),
            ),
            interpret_prompt_key="lesson.l16.stress_b_backlog.interpret_prompt",
            interpret_options=STRESS_B_BACKLOG_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def stress_test_b(advance):
        def on_definition_complete(_interpretation):
            _sync_context_into_collected()
            composite.advance_to_second()

        def on_backlog_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        composite = SequenceScene(app, first=_stress_b_definition_reveal(on_definition_complete), build_second=lambda: _stress_b_backlog_reveal(on_backlog_complete))
        return composite

    # --- Revise the metric contract - a real, un-punished second chance ---

    def revise_contract(advance):
        def on_contract_complete(choice):
            collected["primary_definition"] = choice
            _sync_context_into_collected()
            composite.advance_to_second()

        def on_guardrail_complete(choices):
            collected["guardrails"] = choices["guardrails"]
            _sync_context_into_collected()
            advance()

        def build_guardrail():
            return BriefBuilderScene(app, "lesson.l16.guardrails_revision.title", (GUARDRAIL_FIELD,), on_guardrail_complete, guided=False)

        contract_scene = MetricContractScene(
            app,
            "lesson.l16.contract_revision.title",
            "lesson.l16.contract_revision.ask",
            _build_candidates(HONEST, MATURE, MATURE_AS_OF_EXPR),
            on_contract_complete,
            context,
            initial_choice=collected.get("primary_definition"),
            guided=False,
        )
        composite = SequenceScene(app, first=contract_scene, build_second=build_guardrail)
        return composite

    # --- Rerun the stress tests against the FINAL executed contract ---

    def rerun_stress_test(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        chosen = collected["primary_definition"]
        a_after = _value_for(chosen, STRESS_A, MATURE) * 100
        b_after = _value_for(chosen, STRESS_B, MATURE) * 100
        return ComparisonRevealScene(
            app,
            title_key="lesson.l16.rerun.title",
            narrative_keys=("dialogue.l16_rerun.line1", "dialogue.l16_rerun.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l16.rerun.stress_a_label",
                    a_after,
                    python_code=_mirror_for_chosen(chosen, MATURE_AS_OF_EXPR, "stress_a_tickets", "revised_stress_a_rate"),
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l16.rerun.stress_b_label",
                    b_after,
                    python_code=_mirror_for_chosen(chosen, MATURE_AS_OF_EXPR, "stress_b_tickets", "revised_stress_b_rate"),
                    value_format=_pct,
                ),
            ),
            interpret_prompt_key="lesson.l16.rerun.interpret_prompt",
            interpret_options=RERUN_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Final Metric Brief ---

    def final_metric_brief(advance):
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
            "lesson.l16.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(app, "lesson.l16.mastery.title", (MASTERY_JUDGMENT_FIELD, MASTERY_EVIDENCE_FIELD), on_task_complete, guided=False)

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l16.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonSixteenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonSixteenResult(
            primary_definition=collected.get("primary_definition"),
            guardrails=collected.get("guardrails", ()),
            prior_success_verdict=collected.get("prior_success_verdict"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_16.number, 0)
        evaluation = score_lesson_sixteen(result, LESSON_16, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        raw_ticket_inspection,
        initial_contract,
        stress_test_a,
        stress_test_b,
        revise_contract,
        rerun_stress_test,
        final_metric_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=16,
        collected=collected,
        definition=LESSON_16,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
