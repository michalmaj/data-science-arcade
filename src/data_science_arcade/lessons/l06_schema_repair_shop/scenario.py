from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l06_schema_repair_shop.definition import LESSON_06
from data_science_arcade.lessons.l06_schema_repair_shop.scoring import CRITICAL_EVIDENCE_KEYS, LessonSixResult, score_lesson_six
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import (
    ROUND1_ISSUES,
    ROUND2_ISSUES,
    breach_rate,
    breach_rate_python_code,
    generate_mastery_export,
    generate_shipments,
    generate_shipments_after_round1,
    last_month_breach_rate,
    last_month_breach_rate_python_code,
    malformed_count,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui import colors
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2

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
# its own schema description (the migration note). ---

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


class _SequenceScene(Scene):
    """Shows `first`, then swaps to `build_second()` once `advance_to_second`
    is called - a single LessonRunner-stage-shaped composition of two
    already-existing scenes shown back to back, matching the same
    "runtime-conditional sub-scene can't be a second, sometimes-included
    stage" reasoning _DesignThenAllocateScene already established in L05,
    generalized here to an unconditional two-step sequence (inspect the
    mastery export, then decide) rather than a conditional one."""

    def __init__(self, app, first: Scene, build_second: Callable[[], Scene]) -> None:
        super().__init__(app)
        self._build_second = build_second
        self._active = first

    def advance_to_second(self) -> None:
        self._active = self._build_second()

    def __getattr__(self, name: str):
        return getattr(self._active, name)

    def on_enter(self) -> None:
        self._active.on_enter()

    def on_exit(self) -> None:
        self._active.on_exit()

    def handle_event(self, event) -> None:
        self._active.handle_event(event)

    def draw(self, surface) -> None:
        self._active.draw(surface)


class _OfferThenTaskScene(Scene):
    """Engage-or-skip gate for the optional mastery act, mirroring
    MasteryChallengeScene's own OFFER phase - needed because this lesson's
    mastery task (a MultiChoiceField: "which of these genuinely need a
    fix") doesn't fit that scene's own pick-a-metric-then-compare-two-
    values shape, but skipping still needs to stay a real, zero-
    consequence choice like every other lesson's optional act. A single
    LessonRunner stage either way, matching _DesignThenAllocateScene's own
    reasoning in L05 for why a runtime-conditional sub-scene can't be a
    second, sometimes-included item in LessonRunner's own fixed stage
    list."""

    def __init__(self, app, build_task: Callable[[Callable[[dict], None]], Scene], on_complete: Callable[[bool, dict | None], None]) -> None:
        super().__init__(app)
        self._build_task = build_task
        self._on_complete = on_complete
        self._active: Scene | None = None
        self._rebuild_offer_buttons()

    def __getattr__(self, name: str):
        if self._active is not None:
            return getattr(self._active, name)
        raise AttributeError(name)

    def _rebuild_offer_buttons(self) -> None:
        loc = self.app.localization
        engage_rect = pygame.Rect(0, 0, 420, 46)
        engage_rect.center = (CENTER_X, 260)
        skip_rect = pygame.Rect(0, 0, 420, 46)
        skip_rect.center = (CENTER_X, 320)
        self.buttons = ButtonGroup(
            [
                Button(engage_rect, loc.t("mastery.engage"), self._engage),
                Button(skip_rect, loc.t("mastery.skip"), self._skip),
            ]
        )

    def _engage(self) -> None:
        self._active = self._build_task(lambda result: self._on_complete(True, result))

    def _skip(self) -> None:
        self._on_complete(False, None)

    def on_enter(self) -> None:
        if self._active is not None:
            self._active.on_enter()

    def on_exit(self) -> None:
        if self._active is not None:
            self._active.on_exit()

    def handle_event(self, event) -> None:
        if self._active is not None:
            self._active.handle_event(event)
        else:
            self.buttons.handle_event(event)

    def draw(self, surface) -> None:
        if self._active is not None:
            self._active.draw(surface)
            return
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, loc.t("lesson.l06.mastery.title"), (CENTER_X, 90), 28, colors.TEXT)
        draw_wrapped_text(surface, loc.t("dialogue.l06_mastery.line1"), (CENTER_X - 400, 150), 800, 16, colors.TEXT)
        draw_wrapped_text(surface, loc.t("dialogue.l06_mastery.line2"), (CENTER_X - 400, 190), 800, 16, colors.TEXT)
        self.buttons.draw(surface)


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

    Round 2's WorkbenchScene and both KPI reveals all regenerate a fresh
    Dataset via twist_data's own generator functions rather than carrying
    forward WorkbenchScene's own resulting Dataset, since on_complete only
    ever returns the RepairResolution dict, not the dataset itself - the
    same pattern the original L06 and L04's own evidence_review already
    use."""
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
        dataset = generate_shipments_after_round1()
        naive = breach_rate(dataset, corrected=False)
        baseline = last_month_breach_rate(dataset)

        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l06.reveal1.title",
            narrative_keys=("dialogue.l06_reveal1.line1", "dialogue.l06_reveal1.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l06.reveal1.naive_label", naive, python_code=breach_rate_python_code(corrected=False)
                ),
                ComparisonValue(
                    "lesson.l06.reveal1.last_month_label", baseline, python_code=last_month_breach_rate_python_code()
                ),
            ),
            interpret_prompt_key="lesson.l06.reveal1.interpret_prompt",
            interpret_options=REVEAL1_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    def root_cause_pivot(advance):
        return DialogueScene(app, ROOT_CAUSE_PIVOT_DIALOGUE, on_complete=advance)

    # --- Round 2: declare, then execute ---

    def contract_builder_round2(advance):
        def on_complete(brief):
            collected["round2_contract"] = brief
            advance()

        return BriefBuilderScene(
            app, "lesson.l06.contract_title", (DURATION_CONTRACT_FIELD,), on_complete, guided=True
        )

    def repair_round2(advance):
        def on_complete(resolution):
            collected["round2_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        dataset = generate_shipments_after_round1()
        return WorkbenchScene(app, dataset, ROUND2_ISSUES, on_complete, guided=True, context=context)

    def kpi_reveal2(advance):
        dataset = generate_shipments_after_round1()
        naive = breach_rate(dataset, corrected=False)
        corrected = breach_rate(dataset, corrected=True)

        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l06.reveal2.title",
            narrative_keys=("dialogue.l06_reveal2.line1", "dialogue.l06_reveal2.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l06.reveal2.naive_label", naive, python_code=breach_rate_python_code(corrected=False)
                ),
                ComparisonValue(
                    "lesson.l06.reveal2.corrected_label",
                    corrected,
                    python_code=breach_rate_python_code(corrected=True),
                ),
            ),
            interpret_prompt_key="lesson.l06.reveal2.interpret_prompt",
            interpret_options=REVEAL2_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Evidence review ---

    def evidence_review(advance):
        dataset = generate_shipments_after_round1()

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

            sequence = _SequenceScene(
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

        return _OfferThenTaskScene(app, build_task, on_complete)

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

        return LessonSixResult(
            safe_columns=frozenset(collected.get("safe_columns", ())),
            shipment_id_contract=round1_contract.get("shipment_id_contract", ""),
            delivered_at_contract=round1_contract.get("delivered_at_contract", ""),
            duration_contract=round2_contract.get("duration_contract", ""),
            round1_resolution=collected.get("round1_resolution", {}),
            round2_resolution=collected.get("round2_resolution", {}),
            malformed_count_reported=malformed_count(generate_shipments_after_round1()),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_selection=frozenset(collected.get("mastery_selection", ())),
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
