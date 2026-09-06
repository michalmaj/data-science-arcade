from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.duplicate_group import GroupVerdictOption
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l08_duplicate_detective.definition import LESSON_08
from data_science_arcade.lessons.l08_duplicate_detective.scoring import CRITICAL_EVIDENCE_KEYS, LessonEightResult, score_lesson_eight
from data_science_arcade.lessons.l08_duplicate_detective.twist_data import (
    CORRECT_VERDICT_BY_GROUP,
    GROUP_EVIDENCE_KEY,
    ROUND1_ISSUE,
    ROUND2_ISSUE,
    apply_round1,
    apply_round2,
    build_conflict_group,
    build_decoy_group,
    build_lifecycle_group,
    build_replay_group,
    build_retry_group,
    captured_count_python_code,
    captured_gmv_python_code,
    captured_summary,
    duplicate_count_by,
    duplicate_count_by_python_code,
    generate_events,
    generate_scan_log,
    unique_event_count,
    unique_event_count_python_code,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.duplicate_group_scene import DuplicateGroupScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask ---------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l08_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l08_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_briefing.line3"),
    )
)

ROOT_CAUSE_PIVOT_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_root_cause_pivot.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_root_cause_pivot.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l08_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l08_debrief.line3"),
    )
)

# --- Raw inspection ----------------------------------------------------

RAW_INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l08.inspection.prompt",
    options=(
        InspectionOption("i_now_know_the_count", "lesson.l08.inspection.option.i_now_know_the_count"),
        InspectionOption("duplicate_of_what", "lesson.l08.inspection.option.duplicate_of_what"),
        InspectionOption("number_is_useless", "lesson.l08.inspection.option.number_is_useless"),
    ),
    hint_key="lesson.l08.inspection.hint",
)

# --- Multi-level duplicate profiling ---------------------------------------

PROFILING_INTERPRET_OPTIONS = (
    InterpretOption("each_number_is_a_different_question", "lesson.l08.profiling.interpret.option.each_number_is_a_different_question"),
    InterpretOption("trust_the_strictest_number", "lesson.l08.profiling.interpret.option.trust_the_strictest_number"),
    InterpretOption("the_data_is_broken", "lesson.l08.profiling.interpret.option.the_data_is_broken"),
)

# --- Round 1 consequence reveal ---------------------------------------------

CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption("ship_as_is", "lesson.l08.consequence.interpret.option.ship_as_is"),
    InterpretOption("worth_checking_real_payments", "lesson.l08.consequence.interpret.option.worth_checking_real_payments"),
    InterpretOption("recompute_blindly", "lesson.l08.consequence.interpret.option.recompute_blindly"),
)

# --- Duplicate group investigation / twist verdict options ------------------

VERDICT_OPTIONS = (
    GroupVerdictOption("safe_to_remove_duplicate", "lesson.l08.verdict.option.safe_to_remove_duplicate"),
    GroupVerdictOption("keep_all_not_a_duplicate", "lesson.l08.verdict.option.keep_all_not_a_duplicate"),
    GroupVerdictOption("conflict_needs_reconciliation", "lesson.l08.verdict.option.conflict_needs_reconciliation"),
)

# --- Final Decision ----------------------------------------------------

OBSERVATION_UNIT_FIELD = BriefField(
    key="observation_unit",
    prompt_key="lesson.l08.decision.observation_unit.prompt",
    options=(
        BriefOption("every_lifecycle_event", "lesson.l08.decision.observation_unit.option.every_lifecycle_event"),
        BriefOption("paid_orders_with_captured_payment", "lesson.l08.decision.observation_unit.option.paid_orders_with_captured_payment"),
        BriefOption("every_payment_attempt_incl_declines", "lesson.l08.decision.observation_unit.option.every_payment_attempt_incl_declines"),
        BriefOption("unique_customers", "lesson.l08.decision.observation_unit.option.unique_customers"),
    ),
)

DUPLICATE_DEFINITION_FIELD = BriefField(
    key="duplicate_definition",
    prompt_key="lesson.l08.decision.duplicate_definition.prompt",
    options=(
        BriefOption("full_row_identical", "lesson.l08.decision.duplicate_definition.option.full_row_identical"),
        BriefOption("shared_event_id", "lesson.l08.decision.duplicate_definition.option.shared_event_id"),
        BriefOption("shared_order_id", "lesson.l08.decision.duplicate_definition.option.shared_order_id"),
        BriefOption("shared_customer_and_amount", "lesson.l08.decision.duplicate_definition.option.shared_customer_and_amount"),
    ),
)

DEDUPE_KEY_FIELD = BriefField(
    key="dedupe_key",
    prompt_key="lesson.l08.decision.dedupe_key.prompt",
    options=(
        BriefOption("dedupe_by_order_id", "lesson.l08.option.event_id.dedupe_by_order_id"),
        BriefOption("dedupe_by_event_id_keep_first", "lesson.l08.option.event_id.dedupe_by_event_id_keep_first"),
        BriefOption("remove_exact_repeats_only", "lesson.l08.option.event_id.remove_exact_repeats_only"),
    ),
)

LEGITIMATE_REPEATS_FIELD = MultiChoiceField(
    key="legitimate_repeats",
    prompt_key="lesson.l08.decision.legitimate_repeats.prompt",
    options=(
        BriefOption("multiple_lifecycle_events", "lesson.l08.decision.legitimate_repeats.option.multiple_lifecycle_events"),
        BriefOption("multiple_payment_attempts", "lesson.l08.decision.legitimate_repeats.option.multiple_payment_attempts"),
        BriefOption("repeat_purchases", "lesson.l08.decision.legitimate_repeats.option.repeat_purchases"),
        BriefOption("transport_replay", "lesson.l08.decision.legitimate_repeats.option.transport_replay"),
    ),
    min_count=3,
    max_count=4,
)

CONFLICT_POLICY_FIELD = BriefField(
    key="conflict_policy",
    prompt_key="lesson.l08.decision.conflict_policy.prompt",
    options=(
        BriefOption("keep_first_by_event_id", "lesson.l08.option.amount.keep_first_by_event_id"),
        BriefOption("quarantine_and_disclose", "lesson.l08.option.amount.quarantine_and_disclose"),
        BriefOption("keep_last_by_event_id", "lesson.l08.option.amount.keep_last_by_event_id"),
        BriefOption("keep_higher_amount", "lesson.l08.option.amount.keep_higher_amount"),
    ),
)

KPI_RESULT_FIELD = BriefField(
    key="kpi_result",
    prompt_key="lesson.l08.decision.kpi_result.prompt",
    options=(
        BriefOption("twenty_orders_1000_no_caveats", "lesson.l08.decision.kpi_result.option.twenty_orders_1000_no_caveats"),
        BriefOption("nineteen_orders_950_one_excluded", "lesson.l08.decision.kpi_result.option.nineteen_orders_950_one_excluded"),
        BriefOption("twentyone_rows_1045", "lesson.l08.decision.kpi_result.option.twentyone_rows_1045"),
        BriefOption("zero_orders_0", "lesson.l08.decision.kpi_result.option.zero_orders_0"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l08.decision.evidence.prompt",
    min_count=2,
    max_count=3,
)

SAFE_CLAIM_FIELD = BriefField(
    key="safe_claim",
    prompt_key="lesson.l08.decision.safe_claim.prompt",
    options=(
        BriefOption("exact_no_limitations", "lesson.l08.decision.safe_claim.option.exact_no_limitations"),
        BriefOption(
            "one_conflicting_payment_excluded_pending_reconciliation",
            "lesson.l08.decision.safe_claim.option.one_conflicting_payment_excluded_pending_reconciliation",
        ),
        BriefOption("all_duplicates_removed_data_perfect", "lesson.l08.decision.safe_claim.option.all_duplicates_removed_data_perfect"),
        BriefOption("whole_feed_unreliable", "lesson.l08.decision.safe_claim.option.whole_feed_unreliable"),
    ),
)

REQUIRED_PREVENTION_FIELD = BriefField(
    key="prevention_recommendation",
    prompt_key="lesson.l08.decision.prevention_recommendation.prompt",
    options=(
        BriefOption("limit_one_attempt_per_order", "lesson.l08.decision.prevention_recommendation.option.limit_one_attempt_per_order"),
        BriefOption("idempotent_ingestion_and_uniqueness_validation", "lesson.l08.decision.prevention_recommendation.option.idempotent_ingestion_and_uniqueness_validation"),
        BriefOption("manual_review_every_report", "lesson.l08.decision.prevention_recommendation.option.manual_review_every_report"),
        BriefOption("nothing_needed", "lesson.l08.decision.prevention_recommendation.option.nothing_needed"),
    ),
)

# Every real option-bearing field in this lesson, regardless of which
# scene ends up rendering it - matching every lesson from L05 onward's
# own convention, so test_option_label_widths.py can check them all the
# same way without a separate import per field.
DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    OBSERVATION_UNIT_FIELD,
    DUPLICATE_DEFINITION_FIELD,
    DEDUPE_KEY_FIELD,
    LEGITIMATE_REPEATS_FIELD,
    CONFLICT_POLICY_FIELD,
    KPI_RESULT_FIELD,
    SAFE_CLAIM_FIELD,
    REQUIRED_PREVENTION_FIELD,
)

# --- Optional mastery --------------------------------------------------

MASTERY_KEY_FIELD = BriefField(
    key="mastery_key_choice",
    prompt_key="lesson.l08.mastery.key_field.prompt",
    options=(
        BriefOption("package_id", "lesson.l08.mastery.key_field.option.package_id"),
        BriefOption("scan_event_id", "lesson.l08.mastery.key_field.option.scan_event_id"),
        BriefOption("no_dedupe_needed", "lesson.l08.mastery.key_field.option.no_dedupe_needed"),
    ),
)

MASTERY_PRESERVE_FIELD = MultiChoiceField(
    key="mastery_preserve_selection",
    prompt_key="lesson.l08.mastery.preserve_field.prompt",
    options=(
        BriefOption("checkpoint_scans", "lesson.l08.mastery.preserve_field.option.checkpoint_scans"),
        BriefOption("qc_rescan", "lesson.l08.mastery.preserve_field.option.qc_rescan"),
        BriefOption("scanner_retry_replay", "lesson.l08.mastery.preserve_field.option.scanner_retry_replay"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_eight_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 08's real investigation: a 77-row NovaMart Pay
    payment-event feed with 5 genuinely different things that look like
    duplicates at first glance, only one of which actually is one at the
    event_id grain. LessonContext is threaded through every analytical
    stage exactly like L01-L07.

    Every downstream stage reconstructs the real dataset via
    twist_data.apply_round1/apply_round2, replaying the student's own
    actual RepairResolution against the raw feed, the same real-replay
    discipline established by the L06 follow-up and adopted unchanged by
    L07."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def raw_inspection(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            generate_events(),
            issues=(),
            on_complete=on_complete,
            inspection_prompt=RAW_INSPECTION_PROMPT,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    def profiling_reveal(advance):
        dataset = generate_events()

        def on_complete(interpretation):
            collected["profiling_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l08.profiling.title",
            narrative_keys=("dialogue.l08_profiling.line1", "dialogue.l08_profiling.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l08.evidence.raw_row_count", float(len(dataset.frame)), value_format=lambda v: f"{int(v)}"
                ),
                ComparisonValue(
                    "lesson.l08.evidence.unique_event_count",
                    float(unique_event_count(dataset)),
                    python_code=unique_event_count_python_code(),
                    value_format=lambda v: f"{int(v)}",
                ),
                ComparisonValue(
                    "lesson.l08.evidence.event_id_duplicate_count",
                    float(duplicate_count_by(dataset, "event_id")),
                    python_code=duplicate_count_by_python_code("event_id"),
                    value_format=lambda v: f"{int(v)}",
                ),
                ComparisonValue(
                    "lesson.l08.evidence.order_id_duplicate_count",
                    float(duplicate_count_by(dataset, "order_id")),
                    python_code=duplicate_count_by_python_code("order_id"),
                    value_format=lambda v: f"{int(v)}",
                ),
            ),
            interpret_prompt_key="lesson.l08.profiling.interpret_prompt",
            interpret_options=PROFILING_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    def repair_round1(advance):
        def on_complete(resolution):
            collected["round1_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, generate_events(), (ROUND1_ISSUE,), on_complete, guided=True, context=context)

    def consequence_reveal(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        count, gmv = captured_summary(dataset)

        def on_complete(interpretation):
            collected["consequence_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l08.consequence.title",
            narrative_keys=("dialogue.l08_consequence.line1", "dialogue.l08_consequence.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l08.consequence.captured_count_label",
                    float(count),
                    python_code=captured_count_python_code(),
                    value_format=lambda v: f"{int(v)}",
                ),
                ComparisonValue(
                    "lesson.l08.consequence.captured_gmv_label",
                    gmv,
                    python_code=captured_gmv_python_code(),
                    value_format=lambda v: f"${v:,.2f}",
                ),
            ),
            interpret_prompt_key="lesson.l08.consequence.interpret_prompt",
            interpret_options=CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Duplicate group investigation ---

    def group_investigation(advance):
        dataset = generate_events()
        groups = (
            build_replay_group(dataset),
            build_lifecycle_group(dataset),
            build_retry_group(dataset),
            build_decoy_group(dataset),
        )

        def on_complete(verdicts):
            collected["group_verdicts"] = {**collected.get("group_verdicts", {}), **verdicts}
            _record_group_evidence(verdicts)
            _sync_context_into_collected()
            advance()

        return DuplicateGroupScene(app, "lesson.l08.group_title", groups, VERDICT_OPTIONS, on_complete, guided=True)

    def _record_group_evidence(verdicts: dict[str, str]) -> None:
        for group_key, verdict in verdicts.items():
            correct = CORRECT_VERDICT_BY_GROUP.get(group_key)
            evidence_key = GROUP_EVIDENCE_KEY.get(group_key)
            if verdict == correct and evidence_key is not None:
                action = context.record_action(label_key=f"lesson.l08.verdict.option.{verdict}", key=group_key)
                context.record_evidence(label_key=evidence_key, source_action=action, key=group_key)

    def root_cause_pivot(advance):
        return DialogueScene(app, ROOT_CAUSE_PIVOT_DIALOGUE, on_complete=advance)

    def twist_conflict(advance):
        dataset = generate_events()
        group = build_conflict_group(dataset)

        def on_complete(verdicts):
            collected["group_verdicts"] = {**collected.get("group_verdicts", {}), **verdicts}
            _record_group_evidence(verdicts)
            _sync_context_into_collected()
            advance()

        return DuplicateGroupScene(app, "lesson.l08.group_title", (group,), VERDICT_OPTIONS, on_complete, guided=True)

    # --- Round 1 revision offer ---

    def revision_offer(advance):
        """A real, un-punished chance to revise the Round 1 dedupe-key
        pick after seeing the conflict up close - matching L07's own
        sensitivity-revision offer precedent (always offered, regardless
        of whether the current pick was already correct)."""
        collected["initial_round1_resolution"] = dict(collected.get("round1_resolution", {}))

        def build_revision_task(on_task_complete):
            def on_repair_complete(resolution):
                collected["round1_resolution"] = resolution
                collected["round1_revised"] = True
                _sync_context_into_collected()
                on_task_complete(None)

            return WorkbenchScene(app, generate_events(), (ROUND1_ISSUE,), on_repair_complete, guided=True, context=context)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l08.revision_offer.title",
            line_keys=("lesson.l08.revision_offer.line1",),
            engage_label_key="lesson.l08.revision_offer.engage",
            skip_label_key="lesson.l08.revision_offer.skip",
        )

    def repair_round2(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))

        def on_complete(resolution):
            collected["round2_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, dataset, (ROUND2_ISSUE,), on_complete, guided=True, context=context)

    # --- Evidence review ---

    def evidence_review(advance):
        dataset = apply_round2(collected.get("round1_resolution", {}), collected.get("round2_resolution", {}))

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
            "lesson.l08.decision_title",
            steps=(
                OBSERVATION_UNIT_FIELD,
                DUPLICATE_DEFINITION_FIELD,
                DEDUPE_KEY_FIELD,
                LEGITIMATE_REPEATS_FIELD,
                CONFLICT_POLICY_FIELD,
                KPI_RESULT_FIELD,
                DECISION_EVIDENCE_FIELD,
                SAFE_CLAIM_FIELD,
                REQUIRED_PREVENTION_FIELD,
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
                    app, "lesson.l08.mastery.title", (MASTERY_KEY_FIELD, MASTERY_PRESERVE_FIELD), on_task_complete, guided=False
                )

            sequence = SequenceScene(
                app,
                first=WorkbenchScene(
                    app,
                    generate_scan_log(),
                    issues=(),
                    on_complete=on_inspect_complete,
                    visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
                ),
                build_second=build_select,
            )
            return sequence

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_key_choice"] = result.get("mastery_key_choice", "") if result else ""
            collected["mastery_preserve_selection"] = result.get("mastery_preserve_selection", ()) if result else ()
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l08.mastery.title",
            line_keys=("dialogue.l08_mastery.line1", "dialogue.l08_mastery.line2"),
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

    def _build_result() -> LessonEightResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonEightResult(
            round1_resolution=collected.get("round1_resolution", {}),
            round2_resolution=collected.get("round2_resolution", {}),
            group_verdicts=collected.get("group_verdicts", {}),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_key_choice=collected.get("mastery_key_choice", ""),
            mastery_preserve_selection=frozenset(collected.get("mastery_preserve_selection", ())),
            initial_round1_resolution=collected.get("initial_round1_resolution", {}),
            round1_revised=collected.get("round1_revised", False),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_08.number, 0)
        evaluation = score_lesson_eight(result, LESSON_08, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        raw_inspection,
        profiling_reveal,
        repair_round1,
        consequence_reveal,
        group_investigation,
        root_cause_pivot,
        twist_conflict,
        revision_offer,
        repair_round2,
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
        lesson_number=8,
        collected=collected,
        definition=LESSON_08,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
