from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l04_event_log_factory.definition import LESSON_04
from data_science_arcade.lessons.l04_event_log_factory.scoring import CRITICAL_EVIDENCE_KEYS, LessonFourResult, score_lesson_four
from data_science_arcade.lessons.l04_event_log_factory.twist_data import (
    APPROVED_ATTEMPTS,
    DECLINED_ATTEMPTS,
    ERROR_ATTEMPTS,
    MASTERY_DISTINCT_PYTHON_CODE,
    MASTERY_RAW_ACCOUNT_CREATED,
    MASTERY_RAW_PYTHON_CODE,
    MASTERY_REAL_SIGNUPS,
    ORDER_CONFIRMED_DISTINCT_ORDER_PYTHON_CODE,
    ORDER_CONFIRMED_DISTINCT_SESSION_PYTHON_CODE,
    ORDER_CONFIRMED_RAW_PYTHON_CODE,
    event_a_clean,
    event_a_state,
    generate_payment_attempts,
    order_confirmed_counts,
    outcome_breakdown_python_code,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene, MasteryOption, MetricValue
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask ---------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l04_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l04_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l04_briefing.line3"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l04_briefing.line4"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l04_briefing.line5"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_briefing.line6"),
    )
)

FRAMING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_framing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_framing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_framing.line3"),
    )
)

# --- The four real root-cause dialogue variants, chosen by Event A's real
# state (see event_a_state) rather than always the same content -----------

ROOT_CAUSE_CLEAN_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_clean.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_clean.line2"),
    )
)

ROOT_CAUSE_TRIGGER_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_trigger.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_trigger.line2"),
    )
)

ROOT_CAUSE_IDENTIFIERS_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_identifiers.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_identifiers.line2"),
    )
)

ROOT_CAUSE_BOTH_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_both.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_root_cause_both.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l04_debrief.line2"),
    )
)

# --- The spec builder --------------------------------------------------

ORDER_A_TRIGGER_FIELD = BriefField(
    key="order_a_trigger",
    prompt_key="lesson.l04.spec.order_a_trigger.prompt",
    hint_key="lesson.l04.spec.order_a_trigger.hint",
    options=(
        BriefOption("server_confirmed", "lesson.l04.spec.order_a_trigger.option.server_confirmed"),
        BriefOption("client_click", "lesson.l04.spec.order_a_trigger.option.client_click"),
        BriefOption("client_thank_you_page", "lesson.l04.spec.order_a_trigger.option.client_thank_you_page"),
    ),
)

ORDER_A_IDENTIFIERS_FIELD = BriefField(
    key="order_a_identifiers",
    prompt_key="lesson.l04.spec.order_a_identifiers.prompt",
    hint_key="lesson.l04.spec.order_a_identifiers.hint",
    options=(
        BriefOption("session_and_order", "lesson.l04.spec.order_a_identifiers.option.session_and_order"),
        BriefOption("session_only", "lesson.l04.spec.order_a_identifiers.option.session_only"),
        BriefOption("session_order_and_user", "lesson.l04.spec.order_a_identifiers.option.session_order_and_user"),
    ),
)

PAYMENT_B_TRIGGER_FIELD = BriefField(
    key="payment_b_trigger",
    prompt_key="lesson.l04.spec.payment_b_trigger.prompt",
    hint_key="lesson.l04.spec.payment_b_trigger.hint",
    options=(
        BriefOption("gateway_result", "lesson.l04.spec.payment_b_trigger.option.gateway_result"),
        BriefOption("every_click", "lesson.l04.spec.payment_b_trigger.option.every_click"),
        BriefOption("only_approved", "lesson.l04.spec.payment_b_trigger.option.only_approved"),
    ),
)

PAYMENT_B_IDENTIFIERS_FIELD = BriefField(
    key="payment_b_identifiers",
    prompt_key="lesson.l04.spec.payment_b_identifiers.prompt",
    hint_key="lesson.l04.spec.payment_b_identifiers.hint",
    options=(
        BriefOption("session_and_order", "lesson.l04.spec.payment_b_identifiers.option.session_and_order"),
        BriefOption("session_only", "lesson.l04.spec.payment_b_identifiers.option.session_only"),
        BriefOption("order_only", "lesson.l04.spec.payment_b_identifiers.option.order_only"),
    ),
)

PAYMENT_B_PROPERTIES_FIELD = MultiChoiceField(
    key="payment_b_properties",
    prompt_key="lesson.l04.spec.payment_b_properties.prompt",
    hint_key="lesson.l04.spec.payment_b_properties.hint",
    min_count=1,
    max_count=4,
    options=(
        BriefOption("outcome", "lesson.l04.spec.payment_b_properties.option.outcome"),
        BriefOption("payment_method", "lesson.l04.spec.payment_b_properties.option.payment_method"),
        BriefOption("amount", "lesson.l04.spec.payment_b_properties.option.amount"),
        BriefOption("decline_reason_detail", "lesson.l04.spec.payment_b_properties.option.decline_reason_detail"),
        BriefOption("raw_card_number", "lesson.l04.spec.payment_b_properties.option.raw_card_number"),
    ),
)

DATA_MINIMIZATION_FIELD = BriefField(
    key="data_minimization",
    prompt_key="lesson.l04.spec.data_minimization.prompt",
    hint_key="lesson.l04.spec.data_minimization.hint",
    options=(
        BriefOption("only_what_is_needed", "lesson.l04.spec.data_minimization.option.only_what_is_needed"),
        BriefOption("always_collect_more", "lesson.l04.spec.data_minimization.option.always_collect_more"),
        BriefOption("legal_minimum_only", "lesson.l04.spec.data_minimization.option.legal_minimum_only"),
    ),
)

SPEC_FIELDS = (
    ORDER_A_TRIGGER_FIELD,
    ORDER_A_IDENTIFIERS_FIELD,
    PAYMENT_B_TRIGGER_FIELD,
    PAYMENT_B_IDENTIFIERS_FIELD,
    PAYMENT_B_PROPERTIES_FIELD,
    DATA_MINIMIZATION_FIELD,
)

# --- Gut-check -----------------------------------------------------------

INITIAL_GUT_CHECK_FIELD = BriefField(
    key="initial_gut_check",
    prompt_key="lesson.l04.gut_check.prompt",
    options=(
        BriefOption("yes_all_three", "lesson.l04.gut_check.option.yes_all_three"),
        BriefOption("no_gaps_likely", "lesson.l04.gut_check.option.no_gaps_likely"),
        BriefOption("not_sure", "lesson.l04.gut_check.option.not_sure"),
    ),
)

# --- Event A reveal --------------------------------------------------------

EVENT_A_INTERPRET_OPTIONS = (
    InterpretOption("no_real_gap", "lesson.l04.reveal.interpret.option.no_real_gap"),
    InterpretOption("duplicate_trigger", "lesson.l04.reveal.interpret.option.duplicate_trigger"),
    InterpretOption("cannot_verify_orders", "lesson.l04.reveal.interpret.option.cannot_verify_orders"),
    InterpretOption("out_of_order_arrival", "lesson.l04.reveal.interpret.option.out_of_order_arrival"),
)

# --- Final Decision --------------------------------------------------------

SHIP_READINESS_FIELD = BriefField(
    key="ship_readiness",
    prompt_key="lesson.l04.decision.ship_readiness.prompt",
    options=(
        BriefOption("ship_clean", "lesson.l04.decision.ship_readiness.option.ship_clean"),
        BriefOption("ship_with_fix", "lesson.l04.decision.ship_readiness.option.ship_with_fix"),
        BriefOption("monitor_after_launch", "lesson.l04.decision.ship_readiness.option.monitor_after_launch"),
        BriefOption("block_for_properties_too", "lesson.l04.decision.ship_readiness.option.block_for_properties_too"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l04.decision.evidence.prompt",
    min_count=2,
    max_count=4,
)

QUESTIONS_ANSWERABLE_FIELD = BriefField(
    key="questions_answerable",
    prompt_key="lesson.l04.decision.questions_answerable.prompt",
    options=(
        BriefOption("all_three_clean", "lesson.l04.decision.questions_answerable.option.all_three_clean"),
        BriefOption("pm_support_once_fixed", "lesson.l04.decision.questions_answerable.option.pm_support_once_fixed"),
        BriefOption("pm_support_clean_growth_no", "lesson.l04.decision.questions_answerable.option.pm_support_clean_growth_no"),
        BriefOption("all_three_once_fixed", "lesson.l04.decision.questions_answerable.option.all_three_once_fixed"),
    ),
)

KNOWN_GAP_FIELD = BriefField(
    key="known_gap",
    prompt_key="lesson.l04.decision.known_gap.prompt",
    options=(
        BriefOption("cannot_distinguish_outcomes", "lesson.l04.decision.known_gap.option.cannot_distinguish_outcomes"),
        BriefOption("decline_reason_unknown", "lesson.l04.decision.known_gap.option.decline_reason_unknown"),
        BriefOption("never_know_failures", "lesson.l04.decision.known_gap.option.never_know_failures"),
        BriefOption("duplication_means_untrustworthy", "lesson.l04.decision.known_gap.option.duplication_means_untrustworthy"),
        BriefOption("no_remaining_gap", "lesson.l04.decision.known_gap.option.no_remaining_gap"),
    ),
)

REQUIRED_CHANGE_FIELD = BriefField(
    key="required_change",
    prompt_key="lesson.l04.decision.required_change.prompt",
    options=(
        BriefOption("nothing_needed", "lesson.l04.decision.required_change.option.nothing_needed"),
        BriefOption("fix_trigger", "lesson.l04.decision.required_change.option.fix_trigger"),
        BriefOption("fix_identifiers", "lesson.l04.decision.required_change.option.fix_identifiers"),
        BriefOption("fix_both", "lesson.l04.decision.required_change.option.fix_both"),
        BriefOption("fix_properties", "lesson.l04.decision.required_change.option.fix_properties"),
    ),
)

NOT_COLLECTED_FIELD = BriefField(
    key="not_collected",
    prompt_key="lesson.l04.decision.not_collected.prompt",
    options=(
        BriefOption("raw_card_numbers", "lesson.l04.decision.not_collected.option.raw_card_numbers"),
        BriefOption("raw_card_number_needs_removal", "lesson.l04.decision.not_collected.option.raw_card_number_needs_removal"),
        BriefOption("capture_everything", "lesson.l04.decision.not_collected.option.capture_everything"),
        BriefOption("excluded_order_id", "lesson.l04.decision.not_collected.option.excluded_order_id"),
        BriefOption("excluded_outcome_on_purpose", "lesson.l04.decision.not_collected.option.excluded_outcome_on_purpose"),
    ),
)

# --- Optional Mastery: a different flow, a real transfer --------------------

MASTERY_METRIC_OPTIONS = (
    MasteryOption("raw_account_created_count", "lesson.l04.mastery.metric_raw_account_created_count"),
    MasteryOption("distinct_user_id_count", "lesson.l04.mastery.metric_distinct_user_id_count"),
)

MASTERY_INTERPRET_OPTIONS = (
    MasteryOption("flow_is_fine", "lesson.l04.mastery.interpret_flow_is_fine"),
    MasteryOption("some_signups_double_counted", "lesson.l04.mastery.interpret_some_signups_double_counted"),
)


def _properties_quality(properties: tuple[str, ...]) -> float:
    """0.0-1.0: none of the three stated business questions actually need
    anything beyond `outcome` (Growth's question - approved vs. declined
    vs. error - is the only one payment_b_properties serves at all), so
    picking outcome alone is the real minimal-and-sufficient answer, not
    an artifact of a widget that happens to require a second pick.
    Picking outcome plus real extras (payment_method/amount/
    decline_reason_detail) isn't wrong, but it's real over-collection
    relative to what's actually justified - "select everything except
    the card number" isn't pedagogically the same as a deliberately
    minimal, well-justified selection, so it scores a real if modest
    step below it, not identically."""
    if "raw_card_number" in properties or "outcome" not in properties:
        return 0.0
    extra = len(properties) - 1
    return 1.0 if extra == 0 else max(0.4, 1.0 - 0.2 * extra)


def _critical_evidence_present(context: LessonContext, selected_evidence_ids: set[str]) -> tuple[str, ...]:
    """Which of CRITICAL_EVIDENCE_KEYS the student's picked evidence
    actually covers - checked by substring on the picked items' own
    label_key, the same technique l03_api_courier/scenario.py's own
    _critical_evidence_present uses."""
    present: set[str] = set()
    for item in context.evidence:
        if item.id not in selected_evidence_ids:
            continue
        for critical_key in CRITICAL_EVIDENCE_KEYS:
            if critical_key in item.label_key:
                present.add(critical_key)
    return tuple(sorted(present))


def build_lesson_four_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 04's real 11-stage investigation: one continuous
    LessonContext threaded via closures through every analytical stage.
    Unlike L03's own single acquisition axis, L04 has two real,
    independent Event A design choices (trigger, identifiers) - the
    reveal, root-cause dialogue, and Required Change/Ship-readiness
    scoring all branch on the real 4-way twist_data.event_a_state
    (clean/trigger/identifiers/both), not a single collapsed flag, since
    a student who broke both needs both mechanisms named and both fixes
    required - only EVIDENCE's own expected-category-count still uses the
    coarser twist_data.event_a_clean (2 categories clean, 3 otherwise,
    regardless of which specific problem)."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        saved = collected.get("analytical_context")
        if saved is not None:
            context.restore_from_dict(saved)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def framing(advance):
        return DialogueScene(app, FRAMING_DIALOGUE, on_complete=advance)

    # --- The Spec Builder ---

    def spec_builder(advance):
        def on_complete(brief):
            collected["spec"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l04.spec_title", SPEC_FIELDS, on_complete, guided=True)

    def gut_check(advance):
        def on_complete(brief):
            collected["initial_gut_check"] = brief["initial_gut_check"]
            advance()

        return BriefBuilderScene(app, "lesson.l04.gut_check.title", (INITIAL_GUT_CHECK_FIELD,), on_complete, guided=False)

    # --- Event A reveal ---

    def event_a_reveal(advance):
        spec = collected.get("spec", {})
        trigger_is_client_side = spec.get("order_a_trigger") != "server_confirmed"
        identifiers_include_order_id = spec.get("order_a_identifiers") in ("session_and_order", "session_order_and_user")
        raw, distinct, distinct_label_key = order_confirmed_counts(trigger_is_client_side, identifiers_include_order_id)
        distinct_python_code = (
            ORDER_CONFIRMED_DISTINCT_ORDER_PYTHON_CODE
            if identifiers_include_order_id
            else ORDER_CONFIRMED_DISTINCT_SESSION_PYTHON_CODE
        )

        def on_complete(interpretation):
            collected["event_a_interpret_choice"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l04.event_a_reveal.title",
            narrative_keys=("dialogue.l04_event_a_reveal.line1", "dialogue.l04_event_a_reveal.line2"),
            comparisons=(
                ComparisonValue("lesson.l04.reveal.raw_count_label", float(raw), python_code=ORDER_CONFIRMED_RAW_PYTHON_CODE),
                ComparisonValue(distinct_label_key, float(distinct), python_code=distinct_python_code),
            ),
            interpret_prompt_key="lesson.l04.event_a_interpret.prompt",
            interpret_options=EVENT_A_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    # --- Root cause confirmed (content and evidence both state-dependent) ---

    def root_cause_confirmed(advance):
        spec = collected.get("spec", {})
        trigger_is_client_side = spec.get("order_a_trigger") != "server_confirmed"
        identifiers_include_order_id = spec.get("order_a_identifiers") in ("session_and_order", "session_order_and_user")
        state = event_a_state(trigger_is_client_side, identifiers_include_order_id)

        def on_complete():
            _sync_context_into_collected()
            advance()

        if state == "trigger":
            return DialogueScene(
                app,
                ROOT_CAUSE_TRIGGER_DIALOGUE,
                on_complete=on_complete,
                context=context,
                record_label_key="lesson.l04.feedback.evidence.event_a_gap_duplicate",
                record_evidence_key="lesson.l04.feedback.evidence.event_a_gap_duplicate",
                record_key="event_a_gap_duplicate",
            )
        if state == "identifiers":
            return DialogueScene(
                app,
                ROOT_CAUSE_IDENTIFIERS_DIALOGUE,
                on_complete=on_complete,
                context=context,
                record_label_key="lesson.l04.feedback.evidence.event_a_gap_identifiers",
                record_evidence_key="lesson.l04.feedback.evidence.event_a_gap_identifiers",
                record_key="event_a_gap_identifiers",
            )
        if state == "both":
            # Two real, distinct mechanisms, not one - DialogueScene's own
            # record_label_key/record_evidence_key only handles a single
            # fact, so both get recorded directly here instead, the same
            # way the Combined Workbench visit's own on_complete already
            # records real facts outside of any scene's built-in hook.
            def on_complete_both():
                duplicate_action = context.record_action(
                    label_key="lesson.l04.feedback.evidence.event_a_gap_duplicate", key="event_a_gap_duplicate"
                )
                context.record_evidence(
                    label_key="lesson.l04.feedback.evidence.event_a_gap_duplicate",
                    source_action=duplicate_action,
                    key="event_a_gap_duplicate",
                )
                identifiers_action = context.record_action(
                    label_key="lesson.l04.feedback.evidence.event_a_gap_identifiers", key="event_a_gap_identifiers"
                )
                context.record_evidence(
                    label_key="lesson.l04.feedback.evidence.event_a_gap_identifiers",
                    source_action=identifiers_action,
                    key="event_a_gap_identifiers",
                )
                on_complete()

            return DialogueScene(app, ROOT_CAUSE_BOTH_DIALOGUE, on_complete=on_complete_both, context=context)
        return DialogueScene(app, ROOT_CAUSE_CLEAN_DIALOGUE, on_complete=on_complete, context=context)

    # --- Combined Workbench visit: Event B discovery + evidence review ---

    def evidence_review(advance):
        spec = collected.get("spec", {})
        outcome_captured = "outcome" in spec.get("payment_b_properties", ())
        dataset = generate_payment_attempts(outcome_captured)

        def on_complete(_resolution):
            if outcome_captured:
                action = context.record_action(
                    label_key="lesson.l04.feedback.evidence.event_b_outcome_available",
                    python_code=outcome_breakdown_python_code(),
                    key="event_b_outcome",
                )
                context.record_evidence(
                    label_key="lesson.l04.feedback.evidence.event_b_outcome_available",
                    source_action=action,
                    key="event_b_outcome",
                    detail=f"{APPROVED_ATTEMPTS}/{DECLINED_ATTEMPTS}/{ERROR_ATTEMPTS}",
                )
            else:
                action = context.record_action(
                    label_key="lesson.l04.feedback.evidence.event_b_outcome_missing", key="event_b_outcome"
                )
                context.record_evidence(
                    label_key="lesson.l04.feedback.evidence.event_b_outcome_missing",
                    source_action=action,
                    key="event_b_outcome",
                )
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
            "lesson.l04.decision_title",
            steps=(
                SHIP_READINESS_FIELD,
                DECISION_EVIDENCE_FIELD,
                QUESTIONS_ANSWERABLE_FIELD,
                KNOWN_GAP_FIELD,
                REQUIRED_CHANGE_FIELD,
                NOT_COLLECTED_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery Challenge ---

    def mastery_challenge(advance):
        def on_complete(engaged, metric_key, interpretation_key):
            collected["mastery_engaged"] = engaged
            collected["mastery_metric"] = metric_key
            collected["mastery_interpretation"] = interpretation_key
            _sync_context_into_collected()
            advance()

        def compute(_metric_key: str) -> tuple[MetricValue, MetricValue]:
            return (
                MetricValue(
                    "lesson.l04.mastery.raw_label", float(MASTERY_RAW_ACCOUNT_CREATED), python_code=MASTERY_RAW_PYTHON_CODE
                ),
                MetricValue(
                    "lesson.l04.mastery.distinct_label", float(MASTERY_REAL_SIGNUPS), python_code=MASTERY_DISTINCT_PYTHON_CODE
                ),
            )

        return MasteryChallengeScene(
            app,
            title_key="lesson.l04.mastery.title",
            narrative_keys=("dialogue.l04_mastery.line1", "dialogue.l04_mastery.line2"),
            metric_prompt_key="lesson.l04.mastery.metric_prompt",
            metric_options=MASTERY_METRIC_OPTIONS,
            compute=compute,
            interpret_prompt_key="lesson.l04.mastery.interpret_prompt",
            interpret_options=MASTERY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    # --- Feedback / Debrief ---

    def _build_result() -> LessonFourResult:
        # A plain function, not something stashed in `collected` - see
        # l01_question_first/scenario.py's own _build_result for why
        # (LessonRunner checkpoints `collected` via json.dumps, and
        # neither LessonFourResult nor LessonEvaluation is serializable).
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))
        spec = collected.get("spec", {})
        trigger_is_client_side = spec.get("order_a_trigger") != "server_confirmed"
        identifiers_include_order_id = spec.get("order_a_identifiers") in ("session_and_order", "session_order_and_user")
        properties = spec.get("payment_b_properties", ())
        outcome_captured = "outcome" in properties
        decline_reason_captured = "decline_reason_detail" in properties
        privacy_violation = "raw_card_number" in properties

        quality_hits = 0.0
        quality_hits += spec.get("order_a_trigger") == "server_confirmed"
        quality_hits += spec.get("order_a_identifiers") == "session_and_order"
        quality_hits += spec.get("payment_b_trigger") == "gateway_result"
        quality_hits += spec.get("payment_b_identifiers") == "session_and_order"
        quality_hits += _properties_quality(properties)
        quality_hits += spec.get("data_minimization") == "only_what_is_needed"

        return LessonFourResult(
            initial_gut_check=collected.get("initial_gut_check", ""),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(context, selected_evidence_ids),
            event_a_state=event_a_state(trigger_is_client_side, identifiers_include_order_id),
            event_a_clean=event_a_clean(trigger_is_client_side, identifiers_include_order_id),
            outcome_captured=outcome_captured,
            decline_reason_captured=decline_reason_captured,
            privacy_violation=privacy_violation,
            spec_quality_hits=quality_hits,
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_metric=collected.get("mastery_metric") or "",
            mastery_interpretation=collected.get("mastery_interpretation") or "",
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_04.number, 0)
        evaluation = score_lesson_four(result, LESSON_04, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        framing,
        spec_builder,
        gut_check,
        event_a_reveal,
        root_cause_confirmed,
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
        lesson_number=4,
        collected=collected,
        definition=LESSON_04,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
