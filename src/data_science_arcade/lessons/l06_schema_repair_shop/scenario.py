from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l06_schema_repair_shop.definition import LESSON_06
from data_science_arcade.lessons.l06_schema_repair_shop.scoring import CRITICAL_EVIDENCE_KEYS, LessonSixResult, score_lesson_six
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import (
    CORRECT_REPAIR,
    ROUND1_ISSUES,
    ROUND2_ISSUES,
    apply_round1,
    apply_round2,
    breach_rate,
    breach_rate_python_code,
    generate_mastery_export,
    generate_shipments,
    last_month_breach_rate,
    last_month_breach_rate_python_code,
    malformed_count,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.workbench_scene import DataView, WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext


def _format_rate(value: float) -> str:
    # value != value is a real, deliberate NaN test (IEEE floats: NaN is
    # the only value that never equals itself) - a badly chosen
    # delivered_at repair can leave zero "this month" rows with any
    # parseable timestamp at all, and breach_rate() returns NaN rather
    # than crashing; this is what keeps that a real, readable "can't
    # compute this yet" consequence on screen instead of a literal "nan%".
    if value != value:
        return "n/a"
    return f"{value:.0%}"


# --- The Ask ---------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l06_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l06_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_briefing.line3"),
    )
)

FIRST_ATTEMPT_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_first_attempt.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_first_attempt.line2"),
    )
)

ROOT_CAUSE_PIVOT_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_root_cause_pivot.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_root_cause_pivot.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l06_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l06_debrief.line3"),
    )
)

# --- Raw inspection ---------------------------------------------------------

RAW_INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l06.inspection.prompt",
    hint_key="lesson.l06.inspection.hint",
    options=(
        InspectionOption("every_dtype_is_valid", "lesson.l06.inspection.option.every_dtype_is_valid"),
        InspectionOption("dtypes_tell_the_full_story", "lesson.l06.inspection.option.dtypes_tell_the_full_story"),
        InspectionOption("dtypes_are_a_starting_point", "lesson.l06.inspection.option.dtypes_are_a_starting_point"),
    ),
)

# --- Safe-columns prediction: duration_minutes is deliberately not offered
# here - nothing discoverable yet contradicts it, and grading "safe" as
# wrong before the twist is even reachable would be an un-earnable trap. ---

SAFE_COLUMNS_FIELD = MultiChoiceField(
    key="safe_columns",
    prompt_key="lesson.l06.prediction.safe_columns.prompt",
    min_count=1,
    max_count=3,
    options=(
        BriefOption("shipment_id", "lesson.l06.prediction.safe_columns.option.shipment_id"),
        BriefOption("delivered_at", "lesson.l06.prediction.safe_columns.option.delivered_at"),
        BriefOption("item_count", "lesson.l06.prediction.safe_columns.option.item_count"),
    ),
)

# --- Contract Builder, round 1: declare shipment_id's and delivered_at's
# real semantic type before touching either. ---

SHIPMENT_ID_CONTRACT_FIELD = BriefField(
    key="shipment_id_contract",
    prompt_key="lesson.l06.contract.shipment_id.prompt",
    options=(
        BriefOption("identifier", "lesson.l06.contract.shipment_id.option.identifier"),
        BriefOption("numeric_measure", "lesson.l06.contract.shipment_id.option.numeric_measure"),
        BriefOption("categorical_code", "lesson.l06.contract.shipment_id.option.categorical_code"),
    ),
)

DELIVERED_AT_CONTRACT_FIELD = BriefField(
    key="delivered_at_contract",
    prompt_key="lesson.l06.contract.delivered_at.prompt",
    options=(
        BriefOption("timestamp", "lesson.l06.contract.delivered_at.option.timestamp"),
        BriefOption("free_text", "lesson.l06.contract.delivered_at.option.free_text"),
        BriefOption("categorical_label", "lesson.l06.contract.delivered_at.option.categorical_label"),
    ),
)

ROUND1_CONTRACT_TIERED_HINTS = {
    "shipment_id_contract": (
        "lesson.l06.hint.dtype_vs_semantic_type.tier1",
        "lesson.l06.hint.dtype_vs_semantic_type.tier2",
        "lesson.l06.hint.dtype_vs_semantic_type.tier3",
    ),
}

# --- Contract Builder, round 2: duration_minutes's real unit, informed by
# its own schema description (the migration note) - guaranteed visible via
# duration_schema_check, not just reachable if the player happens to look. ---

DURATION_CONTRACT_FIELD = BriefField(
    key="duration_contract",
    prompt_key="lesson.l06.contract.duration_minutes.prompt",
    options=(
        BriefOption("uniform_minutes", "lesson.l06.contract.duration_minutes.option.uniform_minutes"),
        BriefOption("per_store_unit_drift", "lesson.l06.contract.duration_minutes.option.per_store_unit_drift"),
        BriefOption("already_normalized", "lesson.l06.contract.duration_minutes.option.already_normalized"),
    ),
)

# --- KPI reveals -------------------------------------------------------

REVEAL1_INTERPRET_OPTIONS = (
    InterpretOption("worth_checking", "lesson.l06.reveal1.interpret.option.worth_checking"),
    InterpretOption("ship_as_is", "lesson.l06.reveal1.interpret.option.ship_as_is"),
    InterpretOption("assume_crash", "lesson.l06.reveal1.interpret.option.assume_crash"),
)

REVEAL2_INTERPRET_OPTIONS = (
    InterpretOption("sample_size_changed", "lesson.l06.reveal2.interpret.option.sample_size_changed"),
    InterpretOption("unit_drift", "lesson.l06.reveal2.interpret.option.unit_drift"),
    InterpretOption("fewer_deliveries", "lesson.l06.reveal2.interpret.option.fewer_deliveries"),
    InterpretOption("threshold_changed", "lesson.l06.reveal2.interpret.option.threshold_changed"),
)

# --- Final Decision ------------------------------------------------------

READINESS_FIELD = BriefField(
    key="readiness",
    prompt_key="lesson.l06.decision.readiness.prompt",
    options=(
        BriefOption("ready", "lesson.l06.decision.readiness.option.ready"),
        BriefOption("conditionally_ready", "lesson.l06.decision.readiness.option.conditionally_ready"),
        BriefOption("not_ready", "lesson.l06.decision.readiness.option.not_ready"),
    ),
)

KPI_RESULT_FIELD = BriefField(
    key="kpi_result",
    prompt_key="lesson.l06.decision.kpi_result.prompt",
    options=(
        BriefOption("naive_29", "lesson.l06.decision.kpi_result.option.naive_29"),
        BriefOption("corrected_12", "lesson.l06.decision.kpi_result.option.corrected_12"),
        BriefOption("corrected_12_all_month", "lesson.l06.decision.kpi_result.option.corrected_12_all_month"),
        BriefOption("cannot_determine", "lesson.l06.decision.kpi_result.option.cannot_determine"),
        BriefOption("average_based", "lesson.l06.decision.kpi_result.option.average_based"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l06.decision.evidence.prompt",
    min_count=2,
    max_count=3,
)

REMAINING_AMBIGUITY_FIELD = BriefField(
    key="remaining_ambiguity",
    prompt_key="lesson.l06.decision.remaining_ambiguity.prompt",
    options=(
        BriefOption("malformed_rows_pattern", "lesson.l06.decision.remaining_ambiguity.option.malformed_rows_pattern"),
        BriefOption("nothing_remains", "lesson.l06.decision.remaining_ambiguity.option.nothing_remains"),
        BriefOption(
            "other_stores_unit_drift", "lesson.l06.decision.remaining_ambiguity.option.other_stores_unit_drift"
        ),
        BriefOption("threshold_wrong", "lesson.l06.decision.remaining_ambiguity.option.threshold_wrong"),
    ),
)

SAFE_USE_FIELD = BriefField(
    key="safe_use",
    prompt_key="lesson.l06.decision.safe_use.prompt",
    options=(
        BriefOption("this_month_sla", "lesson.l06.decision.safe_use.option.this_month_sla"),
        BriefOption("cross_month_trend", "lesson.l06.decision.safe_use.option.cross_month_trend"),
        BriefOption("financial_reconciliation", "lesson.l06.decision.safe_use.option.financial_reconciliation"),
        BriefOption("not_safe_yet", "lesson.l06.decision.safe_use.option.not_safe_yet"),
    ),
)

REQUIRED_CHANGE_FIELD = BriefField(
    key="required_change",
    prompt_key="lesson.l06.decision.required_change.prompt",
    options=(
        BriefOption("update_contract_and_validate", "lesson.l06.decision.required_change.option.update_contract_and_validate"),
        BriefOption("nothing_needed", "lesson.l06.decision.required_change.option.nothing_needed"),
        BriefOption("rename_column", "lesson.l06.decision.required_change.option.rename_column"),
        BriefOption("block_store_d", "lesson.l06.decision.required_change.option.block_store_d"),
    ),
)

# --- Optional Mastery: a different export, transfer not repetition ------

MASTERY_FIELD = MultiChoiceField(
    key="needs_fix",
    prompt_key="lesson.l06.mastery.prompt",
    min_count=1,
    max_count=4,
    options=(
        BriefOption("store_id", "lesson.l06.mastery.option.store_id"),
        BriefOption("revenue", "lesson.l06.mastery.option.revenue"),
        BriefOption("promo_code", "lesson.l06.mastery.option.promo_code"),
        BriefOption("quantity", "lesson.l06.mastery.option.quantity"),
    ),
)

# Every real option-bearing BriefField/MultiChoiceField in this lesson,
# regardless of which scene ends up rendering it - matching every lesson
# from L05 onward's own convention, so test_option_label_widths.py can
# check them all the same way without a separate import per field.
DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    SAFE_COLUMNS_FIELD,
    SHIPMENT_ID_CONTRACT_FIELD,
    DELIVERED_AT_CONTRACT_FIELD,
    DURATION_CONTRACT_FIELD,
    READINESS_FIELD,
    KPI_RESULT_FIELD,
    REMAINING_AMBIGUITY_FIELD,
    SAFE_USE_FIELD,
    REQUIRED_CHANGE_FIELD,
    MASTERY_FIELD,
)


def build_lesson_six_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 06's real investigation: one hidden 220-row
    shipment export, three real schema problems (an identifier that looks
    numeric, a timestamp stored as text, and a unit-drift bug hiding
    behind an already-correct dtype), all feeding one KPI (this month's
    SLA breach rate). Every fix is declared (Contract Builder) before it's
    executed (WorkbenchScene repair), and each round ends in a real
    analytical consequence - a KPI reveal that only becomes computable, or
    changes - never a bare "correct/incorrect" click. LessonContext is
    threaded through every analytical stage exactly like L01-L05.

    Every downstream stage reconstructs the real dataset via
    twist_data.apply_round1/apply_round2, replaying the student's own
    actual RepairResolution against the raw export - never a ground-truth
    substitute for what they actually picked. Round 2's own WorkbenchScene
    also re-offers any Round 1 issue that wasn't resolved correctly the
    first time, alongside duration_minutes - a real second chance, taken
    right after Reveal 1 showed that issue's own real consequence, not a
    silent correction happening underneath the student."""
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
            generate_shipments(),
            issues=(),
            on_complete=on_complete,
            inspection_prompt=RAW_INSPECTION_PROMPT,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    def safe_columns_prediction(advance):
        def on_complete(brief):
            collected["safe_columns"] = brief["safe_columns"]
            advance()

        return BriefBuilderScene(
            app, "lesson.l06.prediction_title", (SAFE_COLUMNS_FIELD,), on_complete, guided=True
        )

    def first_kpi_attempt(advance):
        return DialogueScene(app, FIRST_ATTEMPT_DIALOGUE, on_complete=advance)

    # --- Round 1: declare, then execute ---

    def contract_builder_round1(advance):
        def on_complete(brief):
            collected["round1_contract"] = brief
            advance()

        return BriefBuilderScene(
            app,
            "lesson.l06.contract_title",
            (SHIPMENT_ID_CONTRACT_FIELD, DELIVERED_AT_CONTRACT_FIELD),
            on_complete,
            guided=True,
            tiered_hint_keys=ROUND1_CONTRACT_TIERED_HINTS,
        )

    def repair_round1(advance):
        def on_complete(resolution):
            collected["round1_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, generate_shipments(), ROUND1_ISSUES, on_complete, guided=True, context=context)

    def kpi_reveal1(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        naive = breach_rate(dataset)
        baseline = last_month_breach_rate(dataset)

        def on_complete(interpretation):
            collected["reveal1_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l06.reveal1.title",
            narrative_keys=("dialogue.l06_reveal1.line1", "dialogue.l06_reveal1.line2"),
            comparisons=(
                ComparisonValue("lesson.l06.reveal1.naive_label", naive, python_code=breach_rate_python_code()),
                ComparisonValue(
                    "lesson.l06.reveal1.last_month_label", baseline, python_code=last_month_breach_rate_python_code()
                ),
            ),
            interpret_prompt_key="lesson.l06.reveal1.interpret_prompt",
            interpret_options=REVEAL1_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=_format_rate,
        )

    def root_cause_pivot(advance):
        return DialogueScene(app, ROOT_CAUSE_PIVOT_DIALOGUE, on_complete=advance)

    # --- Round 2: a guaranteed real look at the migration note, declare,
    # then execute (with a real second chance at any Round 1 miss) ---

    def duration_schema_check(advance):
        def on_complete(_resolution):
            advance()

        dataset = apply_round1(collected.get("round1_resolution", {}))
        return WorkbenchScene(
            app,
            dataset,
            issues=(),
            on_complete=on_complete,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
            initial_data_view=DataView.SCHEMA,
        )

    def contract_builder_round2(advance):
        def on_complete(brief):
            collected["round2_contract"] = brief
            advance()

        return BriefBuilderScene(
            app, "lesson.l06.contract_title", (DURATION_CONTRACT_FIELD,), on_complete, guided=True
        )

    def repair_round2(advance):
        round1_resolution = collected.get("round1_resolution", {})
        revision_issues = tuple(
            issue for issue in ROUND1_ISSUES if round1_resolution.get(issue.column) not in CORRECT_REPAIR[issue.column]
        )

        def on_complete(resolution):
            # Anything from a re-offered Round 1 issue (its column is
            # already a key in round1_resolution, right or wrong) updates
            # that column's own slot in place - a real, final correction,
            # not a separate parallel record; duration_minutes (never a
            # Round 1 key) always lands in round2_resolution.
            updated_round1 = dict(round1_resolution)
            round2_resolution = {}
            for column, option_key in resolution.items():
                if column in updated_round1:
                    updated_round1[column] = option_key
                else:
                    round2_resolution[column] = option_key
            collected["round1_resolution"] = updated_round1
            collected["round2_resolution"] = round2_resolution
            _sync_context_into_collected()
            advance()

        dataset = apply_round1(round1_resolution)
        return WorkbenchScene(
            app, dataset, (*revision_issues, *ROUND2_ISSUES), on_complete, guided=True, context=context
        )

    def kpi_reveal2(advance):
        round1_resolution = collected.get("round1_resolution", {})
        round2_resolution = collected.get("round2_resolution", {})
        before = apply_round1(round1_resolution)
        after = apply_round2(round1_resolution, round2_resolution)
        naive = breach_rate(before)
        actual = breach_rate(after)

        def on_complete(interpretation):
            collected["reveal2_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l06.reveal2.title",
            narrative_keys=("dialogue.l06_reveal2.line1", "dialogue.l06_reveal2.line2"),
            comparisons=(
                ComparisonValue("lesson.l06.reveal2.naive_label", naive, python_code=breach_rate_python_code()),
                ComparisonValue(
                    "lesson.l06.reveal2.corrected_label",
                    actual,
                    python_code=breach_rate_python_code(),
                ),
            ),
            interpret_prompt_key="lesson.l06.reveal2.interpret_prompt",
            interpret_options=REVEAL2_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=_format_rate,
        )

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
            "lesson.l06.decision_title",
            steps=(
                READINESS_FIELD,
                KPI_RESULT_FIELD,
                DECISION_EVIDENCE_FIELD,
                REMAINING_AMBIGUITY_FIELD,
                SAFE_USE_FIELD,
                REQUIRED_CHANGE_FIELD,
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
                    app, "lesson.l06.mastery.title", (MASTERY_FIELD,), on_task_complete, guided=False
                )

            sequence = SequenceScene(
                app,
                first=WorkbenchScene(
                    app,
                    generate_mastery_export(),
                    issues=(),
                    on_complete=on_inspect_complete,
                    visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
                ),
                build_second=build_select,
            )
            return sequence

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_selection"] = result["needs_fix"] if result else ()
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l06.mastery.title",
            line_keys=("dialogue.l06_mastery.line1", "dialogue.l06_mastery.line2"),
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

    def _build_result() -> LessonSixResult:
        round1_contract = collected.get("round1_contract", {})
        round2_contract = collected.get("round2_contract", {})
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))
        round1_resolution = collected.get("round1_resolution", {})

        return LessonSixResult(
            safe_columns=frozenset(collected.get("safe_columns", ())),
            shipment_id_contract=round1_contract.get("shipment_id_contract", ""),
            delivered_at_contract=round1_contract.get("delivered_at_contract", ""),
            duration_contract=round2_contract.get("duration_contract", ""),
            round1_resolution=round1_resolution,
            round2_resolution=collected.get("round2_resolution", {}),
            malformed_count_reported=malformed_count(apply_round1(round1_resolution)),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_selection=frozenset(collected.get("mastery_selection", ())),
            reveal1_interpretation=collected.get("reveal1_interpretation", ""),
            reveal2_interpretation=collected.get("reveal2_interpretation", ""),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_06.number, 0)
        evaluation = score_lesson_six(result, LESSON_06, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        raw_inspection,
        safe_columns_prediction,
        first_kpi_attempt,
        contract_builder_round1,
        repair_round1,
        kpi_reveal1,
        root_cause_pivot,
        duration_schema_check,
        contract_builder_round2,
        repair_round2,
        kpi_reveal2,
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
        lesson_number=6,
        collected=collected,
        definition=LESSON_06,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
