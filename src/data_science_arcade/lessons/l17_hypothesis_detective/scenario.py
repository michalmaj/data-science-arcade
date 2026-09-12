from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l17_hypothesis_detective import data as d
from data_science_arcade.lessons.l17_hypothesis_detective.definition import LESSON_17
from data_science_arcade.lessons.l17_hypothesis_detective.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    DEVICE_PATTERN_EVIDENCE_KEY,
    DEVICE_PROVENANCE_EVIDENCE_KEY,
    PLAN_LOCKED_EVIDENCE_KEY,
    PRIMARY_RESULT_EVIDENCE_KEY,
    LessonSeventeenResult,
    score_lesson_seventeen,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask ---------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_briefing.line3"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_debrief.line3"),
    )
)
LOCK_CONFIRMATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_lock.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_lock.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_lock.line3"),
    )
)
PROVENANCE_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_provenance.line1"),))
MASTERY_DIALOGUE_KEYS = ("dialogue.l17_mastery.line1", "dialogue.l17_mastery.line2")


def _pct(value: float) -> str:
    return f"{value:.1f}%"


# --- Ground truth, precomputed once (real, hand-verified via a real
# pandas script - see data.py's own module docstring) ----------------------

PILOT = d.generate_pilot().frame
CONTROL_PCT = d.primary_rate(PILOT, "control") * 100
ONE_CLICK_PCT = d.primary_rate(PILOT, "one_click") * 100
APP_CONTROL_PCT = d.device_rate(PILOT, "app", "control") * 100
APP_ONE_CLICK_PCT = d.device_rate(PILOT, "app", "one_click") * 100
WEB_CONTROL_PCT = d.device_rate(PILOT, "web", "control") * 100
WEB_ONE_CLICK_PCT = d.device_rate(PILOT, "web", "one_click") * 100

# --- Blinded roster inspection - grain, before anything else. The
# hypothesis plan must be locked before any real outcome value is visible
# anywhere, so this is a real, deliberately blinded view: customer_id,
# variant, device - no repeat_purchase_14d column at all (see
# data.generate_blinded_roster). The full pilot, outcome included, is
# only shown once via full_pilot_reveal, after the lock. -------------------

INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l17.inspection.prompt",
    hint_key="lesson.l17.inspection.hint",
    options=(
        InspectionOption("one_row_per_customer", "lesson.l17.inspection.option.one_row_per_customer"),
        InspectionOption("one_row_per_purchase_event", "lesson.l17.inspection.option.one_row_per_purchase_event"),
        InspectionOption("one_row_per_week", "lesson.l17.inspection.option.one_row_per_week"),
    ),
)

# --- Hypothesis plan - 4 real fields, reused unmodified for the one real
# pre-data revision via BriefBuilderScene's own new initial_choices seeding.

HYPOTHESIS_PLAN_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="target_population",
        prompt_key="lesson.l17.plan.target_population.prompt",
        hint_key="lesson.l17.plan.target_population.hint",
        options=(
            BriefOption("all_eligible_returning_customers", "lesson.l17.plan.target_population.option.all_eligible_returning_customers"),
            BriefOption("app_users_only", "lesson.l17.plan.target_population.option.app_users_only"),
            BriefOption("one_click_group_only", "lesson.l17.plan.target_population.option.one_click_group_only"),
        ),
    ),
    BriefField(
        key="primary_outcome",
        prompt_key="lesson.l17.plan.primary_outcome.prompt",
        hint_key="lesson.l17.plan.primary_outcome.hint",
        options=(
            BriefOption("repeat_purchase_14d", "lesson.l17.plan.primary_outcome.option.repeat_purchase_14d"),
            BriefOption("average_order_value", "lesson.l17.plan.primary_outcome.option.average_order_value"),
            BriefOption("support_contact_rate", "lesson.l17.plan.primary_outcome.option.support_contact_rate"),
        ),
    ),
    BriefField(
        key="observation_window",
        prompt_key="lesson.l17.plan.observation_window.prompt",
        hint_key="lesson.l17.plan.observation_window.hint",
        options=(
            BriefOption("fourteen_days", "lesson.l17.plan.observation_window.option.fourteen_days"),
            BriefOption("thirty_days", "lesson.l17.plan.observation_window.option.thirty_days"),
            BriefOption("seven_days", "lesson.l17.plan.observation_window.option.seven_days"),
        ),
    ),
    BriefField(
        key="predicted_direction",
        prompt_key="lesson.l17.plan.predicted_direction.prompt",
        hint_key="lesson.l17.plan.predicted_direction.hint",
        options=(
            BriefOption("increase", "lesson.l17.plan.predicted_direction.option.increase"),
            BriefOption("decrease", "lesson.l17.plan.predicted_direction.option.decrease"),
            BriefOption("no_real_change", "lesson.l17.plan.predicted_direction.option.no_real_change"),
        ),
    ),
)

# --- Protocol check - real, non-outcome consequences of the CURRENT plan,
# selected (never generated) from a small fixed map keyed to whichever
# field is wrong. Never reveals anything about the eventual result. --------

_POPULATION_ISSUE_KEYS = {
    "app_users_only": "lesson.l17.protocol_check.issue.population_app_only",
    "one_click_group_only": "lesson.l17.protocol_check.issue.population_one_click_only",
}
_OUTCOME_ISSUE_KEYS = {
    "average_order_value": "lesson.l17.protocol_check.issue.outcome_aov",
    "support_contact_rate": "lesson.l17.protocol_check.issue.outcome_support",
}
_WINDOW_ISSUE_KEYS = {
    "thirty_days": "lesson.l17.protocol_check.issue.window_thirty",
    "seven_days": "lesson.l17.protocol_check.issue.window_seven",
}
_DIRECTION_ISSUE_KEY = "lesson.l17.protocol_check.issue.direction_mismatch"
_NO_ISSUE_KEY = "lesson.l17.protocol_check.issue.none_plan_looks_sound"


def _protocol_check_line_keys(plan: dict) -> tuple[str, ...]:
    keys: list[str] = []
    population_issue = _POPULATION_ISSUE_KEYS.get(plan.get("target_population"))
    if population_issue:
        keys.append(population_issue)
    outcome_issue = _OUTCOME_ISSUE_KEYS.get(plan.get("primary_outcome"))
    if outcome_issue:
        keys.append(outcome_issue)
    window_issue = _WINDOW_ISSUE_KEYS.get(plan.get("observation_window"))
    if window_issue:
        keys.append(window_issue)
    if plan.get("predicted_direction") != "increase":
        keys.append(_DIRECTION_ISSUE_KEY)
    if not keys:
        keys.append(_NO_ISSUE_KEY)
    return tuple(keys)


def _plan_mirror_code(plan: dict) -> str:
    """Provenance only - no outcome computation. The lock action's whole
    job is to prove WHEN the plan existed, never to compute anything from
    the outcome column (which isn't even visible yet at lock time - see
    generate_blinded_roster). primary_reveal's own ComparisonValue.
    python_code is what first computes `primary`, after the lock."""
    return (
        "# PRE-SPECIFIED BEFORE RESULTS\n"
        f"# Population: {plan.get('target_population')}\n"
        f"# Outcome: {plan.get('primary_outcome')}\n"
        f"# Window: {plan.get('observation_window')}\n"
        f"# Direction: one_click vs control -> {plan.get('predicted_direction')}\n"
        "# Planned subgroup analyses: none"
    )


# --- Reveal interpret options - every option within one reveal shares the
# SAME evidence_key ("fact seen != correct interpretation"). ---------------

PRIMARY_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l17.primary_reveal.interpret.option.{key}", evidence_key=PRIMARY_RESULT_EVIDENCE_KEY)
    for key in ("observed_in_predicted_direction", "proves_one_click_increases_repeat_purchase", "too_small_to_count_as_evidence")
)
DEVICE_PATTERN_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l17.device_pattern_reveal.interpret.option.{key}", evidence_key=DEVICE_PATTERN_EVIDENCE_KEY)
    for key in ("a_real_pattern_worth_a_closer_look", "proves_the_feature_works_better_on_app", "means_nothing_probably_noise")
)

# --- Final Hypothesis Brief -------------------------------------------------

DEVICE_FINDING_STATUS_FIELD = BriefField(
    key="device_finding_status",
    prompt_key="lesson.l17.decision.device_finding_status.prompt",
    options=(
        BriefOption("exploratory_discovered_after_reveal", "lesson.l17.decision.device_finding_status.option.exploratory_discovered_after_reveal"),
        BriefOption("confirmatory_it_was_the_real_plan", "lesson.l17.decision.device_finding_status.option.confirmatory_it_was_the_real_plan"),
        BriefOption("irrelevant_should_be_discarded", "lesson.l17.decision.device_finding_status.option.irrelevant_should_be_discarded"),
    ),
)
WHY_DEVICE_STATUS_DIFFERS_FIELD = BriefField(
    key="why_device_status_differs",
    prompt_key="lesson.l17.decision.why_device_status_differs.prompt",
    options=(
        BriefOption(
            "introduced_only_after_primary_result_visible",
            "lesson.l17.decision.why_device_status_differs.option.introduced_only_after_primary_result_visible",
        ),
        BriefOption("device_was_always_part_of_the_plan", "lesson.l17.decision.why_device_status_differs.option.device_was_always_part_of_the_plan"),
        BriefOption("device_is_a_data_quality_issue", "lesson.l17.decision.why_device_status_differs.option.device_is_a_data_quality_issue"),
    ),
)
PRIMARY_RESULT_CLAIM_FIELD = BriefField(
    key="primary_result_claim",
    prompt_key="lesson.l17.decision.primary_result_claim.prompt",
    options=(
        BriefOption(
            "observed_plus_one_pp_in_predicted_direction", "lesson.l17.decision.primary_result_claim.option.observed_plus_one_pp_in_predicted_direction"
        ),
        BriefOption("proved_one_click_increases_repeat_purchase", "lesson.l17.decision.primary_result_claim.option.proved_one_click_increases_repeat_purchase"),
        BriefOption("too_small_to_count_as_evidence", "lesson.l17.decision.primary_result_claim.option.too_small_to_count_as_evidence"),
    ),
)
STRONGEST_DEFENSIBLE_DEVICE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_device_claim",
    prompt_key="lesson.l17.decision.strongest_defensible_device_claim.prompt",
    options=(
        BriefOption(
            "real_pattern_worth_a_new_pre_specified_test", "lesson.l17.decision.strongest_defensible_device_claim.option.real_pattern_worth_a_new_pre_specified_test"
        ),
        BriefOption("confirmed_device_specific_effect", "lesson.l17.decision.strongest_defensible_device_claim.option.confirmed_device_specific_effect"),
        BriefOption("coincidence_not_worth_reexamining", "lesson.l17.decision.strongest_defensible_device_claim.option.coincidence_not_worth_reexamining"),
    ),
)
NEXT_STEP_FIELD = BriefField(
    key="next_step",
    prompt_key="lesson.l17.decision.next_step.prompt",
    options=(
        BriefOption(
            "form_new_hypothesis_prespecify_test_on_new_data", "lesson.l17.decision.next_step.option.form_new_hypothesis_prespecify_test_on_new_data"
        ),
        BriefOption("ship_the_app_only_version", "lesson.l17.decision.next_step.option.ship_the_app_only_version"),
        BriefOption("nothing_further_needed", "lesson.l17.decision.next_step.option.nothing_further_needed"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l17.decision.evidence.prompt", min_count=3, max_count=4)
DECISION_FIELDS: tuple[BriefField, ...] = (
    DEVICE_FINDING_STATUS_FIELD,
    WHY_DEVICE_STATUS_DIFFERS_FIELD,
    PRIMARY_RESULT_CLAIM_FIELD,
    STRONGEST_DEFENSIBLE_DEVICE_CLAIM_FIELD,
    NEXT_STEP_FIELD,
)

# --- Optional mastery: NovaMart Logistics route planner, a different
# domain - same evidence/claim pairing discipline from day one. -----------

MASTERY_JUDGMENT_FIELD = BriefField(
    key="mastery_route_judgment",
    prompt_key="lesson.l17.mastery.field.judgment.prompt",
    options=(
        BriefOption("not_borne_out_overall_late_rate_increased", "lesson.l17.mastery.option.judgment.not_borne_out_overall_late_rate_increased"),
        BriefOption("yes_urban_pattern_proves_it", "lesson.l17.mastery.option.judgment.yes_urban_pattern_proves_it"),
        BriefOption("cant_tell_without_a_significance_test", "lesson.l17.mastery.option.judgment.cant_tell_without_a_significance_test"),
    ),
)
MASTERY_URBAN_STATUS_FIELD = BriefField(
    key="mastery_urban_status",
    prompt_key="lesson.l17.mastery.field.urban_status.prompt",
    options=(
        BriefOption("post_hoc_exploratory_worth_new_test", "lesson.l17.mastery.option.urban_status.post_hoc_exploratory_worth_new_test"),
        BriefOption("confirmed_planner_works_in_urban", "lesson.l17.mastery.option.urban_status.confirmed_planner_works_in_urban"),
        BriefOption("irrelevant_ignore_it", "lesson.l17.mastery.option.urban_status.irrelevant_ignore_it"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l17.mastery.field.evidence.prompt",
    options=(
        BriefOption("overall_late_rate_increased", "lesson.l17.mastery.option.evidence.overall_late_rate_increased"),
        BriefOption("urban_late_rate_improved", "lesson.l17.mastery.option.evidence.urban_late_rate_improved"),
        BriefOption("rural_late_rate_worsened", "lesson.l17.mastery.option.evidence.rural_late_rate_worsened"),
        BriefOption("urban_routes_have_more_deliveries", "lesson.l17.mastery.option.evidence.urban_routes_have_more_deliveries"),
    ),
    min_count=1,
    max_count=2,
)


def build_lesson_seventeen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 17's real investigation: one real 1200-customer
    NovaMart one-click reorder pilot (data.py). LessonContext is threaded
    through every analytical stage exactly like L06-L16.

    The hypothesis plan is drafted, protocol-checked, and optionally
    revised entirely in `collected` - no AnalyticalAction is ever recorded
    for it until the real lock moment, since the timestamp/provenance IS
    the lesson's own subject: recording a draft under the same key
    `record_action` would later update means the "locked" action's own
    real creation time would misrepresent when the plan actually became
    final. Exactly one `record_action(key="hypothesis_plan_locked")` call
    exists in this whole file, at the lock step, never touched again."""
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

    def blinded_roster_inspection(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            d.generate_blinded_roster(),
            issues=(),
            on_complete=on_complete,
            inspection_prompt=INSPECTION_PROMPT,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    # --- Hypothesis plan: draft -> protocol check -> optional single
    # revision -> lock (the only place the locked action is ever written) ---

    def hypothesis_plan_and_check(advance):
        def _lock_plan() -> None:
            plan = collected["hypothesis_plan"]
            action = context.record_action(label_key="lesson.l17.plan.locked_action_label", python_code=_plan_mirror_code(plan), key="hypothesis_plan_locked")
            context.record_evidence(label_key=PLAN_LOCKED_EVIDENCE_KEY, source_action=action, key="plan_locked_before_results")
            _sync_context_into_collected()

        def on_initial_plan_complete(choices):
            collected["hypothesis_plan"] = dict(choices)
            composite.advance_to_second()

        def build_protocol_check():
            plan = collected["hypothesis_plan"]
            line_keys = _protocol_check_line_keys(plan)

            def build_revision_task(on_task_complete):
                def on_revised(choices):
                    collected["hypothesis_plan"] = dict(choices)
                    on_task_complete(None)

                return BriefBuilderScene(
                    app, "lesson.l17.plan.revision_title", HYPOTHESIS_PLAN_FIELDS, on_revised, guided=False, initial_choices=plan
                )

            def on_offer_complete(_engaged, _result):
                _lock_plan()
                advance()

            return OfferThenTaskScene(
                app,
                build_revision_task,
                on_offer_complete,
                title_key="lesson.l17.protocol_check.title",
                line_keys=line_keys,
                engage_label_key="lesson.l17.protocol_check.revise",
                skip_label_key="lesson.l17.protocol_check.lock",
            )

        initial_scene = BriefBuilderScene(app, "lesson.l17.plan.title", HYPOTHESIS_PLAN_FIELDS, on_initial_plan_complete, guided=True)
        composite = SequenceScene(app, first=initial_scene, build_second=build_protocol_check)
        return composite

    def plan_locked_confirmation(advance):
        return DialogueScene(app, LOCK_CONFIRMATION_DIALOGUE, on_complete=advance)

    def full_pilot_reveal(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            d.generate_pilot(),
            issues=(),
            on_complete=on_complete,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    # --- Reveals ---

    def primary_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l17.primary_reveal.title",
            narrative_keys=("dialogue.l17_primary_reveal.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l17.primary_reveal.control_label",
                    CONTROL_PCT,
                    python_code="primary = pilot.groupby('variant')['repeat_purchase_14d'].mean()\nprimary.loc['control']",
                    value_format=_pct,
                ),
                ComparisonValue("lesson.l17.primary_reveal.one_click_label", ONE_CLICK_PCT, python_code="primary.loc['one_click']", value_format=_pct),
            ),
            interpret_prompt_key="lesson.l17.primary_reveal.interpret_prompt",
            interpret_options=PRIMARY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def device_pattern_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l17.device_pattern_reveal.title",
            narrative_keys=("dialogue.l17_device_pattern_reveal.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l17.device_pattern_reveal.app_label",
                    APP_ONE_CLICK_PCT - APP_CONTROL_PCT,
                    python_code=(
                        "device_rates = pilot.groupby(['device', 'variant'])['repeat_purchase_14d'].mean().unstack()\n"
                        "device_rates.loc['app', 'one_click'] - device_rates.loc['app', 'control']"
                    ),
                    value_format=lambda v: f"{v:+.1f}pp",
                ),
                ComparisonValue(
                    "lesson.l17.device_pattern_reveal.web_label",
                    WEB_ONE_CLICK_PCT - WEB_CONTROL_PCT,
                    python_code="device_rates.loc['web', 'one_click'] - device_rates.loc['web', 'control']",
                    value_format=lambda v: f"{v:+.1f}pp",
                ),
            ),
            interpret_prompt_key="lesson.l17.device_pattern_reveal.interpret_prompt",
            interpret_options=DEVICE_PATTERN_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def device_provenance_reveal(advance):
        def on_complete():
            _sync_context_into_collected()
            advance()

        return DialogueScene(
            app,
            PROVENANCE_DIALOGUE,
            on_complete=on_complete,
            context=context,
            record_label_key="lesson.l17.provenance.record_label",
            record_evidence_key=DEVICE_PROVENANCE_EVIDENCE_KEY,
            record_key="device_split_added_after_reveal",
        )

    # --- Final Hypothesis Brief ---

    def final_hypothesis_brief(advance):
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
            "lesson.l17.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l17.mastery.title",
                (MASTERY_JUDGMENT_FIELD, MASTERY_URBAN_STATUS_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l17.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonSeventeenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonSeventeenResult(
            hypothesis_plan=collected.get("hypothesis_plan", {}),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_17.number, 0)
        evaluation = score_lesson_seventeen(result, LESSON_17, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        blinded_roster_inspection,
        hypothesis_plan_and_check,
        plan_locked_confirmation,
        full_pilot_reveal,
        primary_reveal,
        device_pattern_reveal,
        device_provenance_reveal,
        final_hypothesis_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=17,
        collected=collected,
        definition=LESSON_17,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
