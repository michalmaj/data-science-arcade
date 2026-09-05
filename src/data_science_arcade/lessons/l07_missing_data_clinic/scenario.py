from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l07_missing_data_clinic.definition import LESSON_07
from data_science_arcade.lessons.l07_missing_data_clinic.scoring import CRITICAL_EVIDENCE_KEYS, LessonSevenResult, score_lesson_seven
from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import (
    ROUND1_ISSUES,
    ROUND2_ISSUES,
    STORES,
    apply_round1,
    apply_round2,
    complete_case_rate,
    complete_case_rate_python_code,
    generate_mastery_export,
    generate_orders,
    missing_rate_by,
    overall_missing_rate,
    sla_bounds,
    sla_lower_bound_python_code,
    sla_upper_bound_python_code,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext


def _format_rate(value: float) -> str:
    return f"{value:.0%}"


SLA_TARGET = 0.85

# --- The Ask ---------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l07_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l07_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_briefing.line3"),
    )
)

ROOT_CAUSE_PIVOT_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_root_cause_pivot.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_root_cause_pivot.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l07_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l07_debrief.line3"),
    )
)

# --- Raw inspection ----------------------------------------------------

RAW_INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l07.inspection.prompt",
    hint_key="lesson.l07.inspection.hint",
    options=(
        InspectionOption("every_missing_is_the_same", "lesson.l07.inspection.option.every_missing_is_the_same"),
        InspectionOption("missing_is_just_noise", "lesson.l07.inspection.option.missing_is_just_noise"),
        InspectionOption("missingness_needs_diagnosis", "lesson.l07.inspection.option.missingness_needs_diagnosis"),
    ),
)

# --- Contract Builder, round 1: declare cold_pack_temp_c's and
# promo_code's real missingness meaning before touching either - both
# discoverable immediately, no investigation needed first. ---

COLD_PACK_MEANING_FIELD = BriefField(
    key="cold_pack_meaning",
    prompt_key="lesson.l07.contract.cold_pack_temp_c.prompt",
    options=(
        BriefOption("structural_not_applicable", "lesson.l07.contract.cold_pack_temp_c.option.structural_not_applicable"),
        BriefOption("measurement_failure", "lesson.l07.contract.cold_pack_temp_c.option.measurement_failure"),
        BriefOption("explicit_category", "lesson.l07.contract.cold_pack_temp_c.option.explicit_category"),
    ),
)

PROMO_MEANING_FIELD = BriefField(
    key="promo_meaning",
    prompt_key="lesson.l07.contract.promo_code.prompt",
    options=(
        BriefOption("explicit_category", "lesson.l07.contract.promo_code.option.explicit_category"),
        BriefOption("measurement_failure", "lesson.l07.contract.promo_code.option.measurement_failure"),
        BriefOption("structural_not_applicable", "lesson.l07.contract.promo_code.option.structural_not_applicable"),
    ),
)

# --- Contract Builder, round 2: pick_minutes's real missingness meaning,
# only after the investigation. ---

PICK_MINUTES_MEANING_FIELD = BriefField(
    key="pick_minutes_meaning",
    prompt_key="lesson.l07.contract.pick_minutes.prompt",
    options=(
        BriefOption("measurement_failure_legacy_peak", "lesson.l07.contract.pick_minutes.option.measurement_failure_legacy_peak"),
        BriefOption("random_noise", "lesson.l07.contract.pick_minutes.option.random_noise"),
        BriefOption("structural_not_applicable", "lesson.l07.contract.pick_minutes.option.structural_not_applicable"),
    ),
)

PICK_MINUTES_TIERED_HINTS = {
    "pick_minutes_meaning": (
        "lesson.l07.hint.missingness_mechanism.tier1",
        "lesson.l07.hint.missingness_mechanism.tier2",
        "lesson.l07.hint.missingness_mechanism.tier3",
    ),
}

# --- First attempt: complete-case rate vs. the 85% target ---------------

FIRST_ATTEMPT_INTERPRET_OPTIONS = (
    InterpretOption("worth_checking", "lesson.l07.first_attempt.interpret.option.worth_checking"),
    InterpretOption("ship_as_is", "lesson.l07.first_attempt.interpret.option.ship_as_is"),
    InterpretOption("recompute", "lesson.l07.first_attempt.interpret.option.recompute"),
)

# --- Missingness investigation: 2 real cuts, each a real signal vs. a
# real, non-contrived absence of one. ---

_INVESTIGATION_COLUMN_BY_OPTION: dict[str, str] = {
    "scanner_type": "scanner_type",
    "store": "store",
    "hour_bucket": "hour_bucket",
    "basket_size": "basket_size",
}
_INVESTIGATION_EVIDENCE_KEY_BY_OPTION: dict[str, str] = {
    "scanner_type": "lesson.l07.evidence.scanner_type_gap",
    "store": "lesson.l07.evidence.store_flat",
    "hour_bucket": "lesson.l07.evidence.hour_bucket_gap",
    "basket_size": "lesson.l07.evidence.basket_size_flat",
}


def _build_investigation_requests(dataset) -> tuple[SegmentRequest, SegmentRequest]:
    baseline = overall_missing_rate(dataset)
    by_scanner = missing_rate_by(dataset, "scanner_type")
    by_store = missing_rate_by(dataset, "store")
    by_hour = missing_rate_by(dataset, "hour_bucket")
    by_basket = missing_rate_by(dataset, "basket_size")

    primary_cut = SegmentRequest(
        key="primary_cut",
        prompt_key="lesson.l07.investigation.primary_cut.prompt",
        hint_key="lesson.l07.investigation.hint",
        options=(
            SliceOption(
                "scanner_type",
                "lesson.l07.investigation.option.scanner_type",
                segments=(
                    Segment("legacy", "lesson.l07.investigation.segment.scanner_legacy", baseline, by_scanner["legacy"]),
                    Segment("current", "lesson.l07.investigation.segment.scanner_current", baseline, by_scanner["current"]),
                ),
            ),
            SliceOption(
                "store",
                "lesson.l07.investigation.option.store",
                segments=tuple(
                    Segment(f"store_{s.lower()}", f"lesson.l07.investigation.segment.store_{s.lower()}", baseline, by_store[s])
                    for s in STORES
                ),
            ),
        ),
    )

    secondary_cut = SegmentRequest(
        key="secondary_cut",
        prompt_key="lesson.l07.investigation.secondary_cut.prompt",
        hint_key="lesson.l07.investigation.hint",
        options=(
            SliceOption(
                "hour_bucket",
                "lesson.l07.investigation.option.hour_bucket",
                segments=(
                    Segment("peak", "lesson.l07.investigation.segment.hour_peak", baseline, by_hour["peak"]),
                    Segment("offpeak", "lesson.l07.investigation.segment.hour_offpeak", baseline, by_hour["offpeak"]),
                ),
            ),
            SliceOption(
                "basket_size",
                "lesson.l07.investigation.option.basket_size",
                segments=(
                    Segment("small", "lesson.l07.investigation.segment.basket_small", baseline, by_basket["small"]),
                    Segment("large", "lesson.l07.investigation.segment.basket_large", baseline, by_basket["large"]),
                ),
            ),
        ),
    )

    return primary_cut, secondary_cut


def _record_investigation_evidence(context: LessonContext, dataset, choices: dict[str, str]) -> None:
    """SegmentSlicerScene has no LessonContext integration of its own
    (none of its other 4 real uses touch evidence/scoring) - so this
    lesson records real evidence directly from the stage's own
    on_complete handler, using the Segment/SliceOption data it already
    has. Which evidence lands depends on which option was actually
    picked: the real-signal pick records the real gap; the decoy pick
    records a real "checked, found flat" fact instead - either way, a
    real, citable finding, never a placeholder for a wasted click."""
    for request_key, option_key in choices.items():
        column = _INVESTIGATION_COLUMN_BY_OPTION[option_key]
        evidence_key = _INVESTIGATION_EVIDENCE_KEY_BY_OPTION[option_key]
        rates = missing_rate_by(dataset, column)
        detail = ", ".join(f"{name}: {rate:.0%}" for name, rate in sorted(rates.items()))
        action = context.record_action(
            label_key=f"lesson.l07.investigation.option.{option_key}", key=f"investigation_{request_key}"
        )
        context.record_evidence(label_key=evidence_key, source_action=action, key=f"investigation_{request_key}", detail=detail)


# --- Sensitivity reveal ---------------------------------------------------

SENSITIVITY_INTERPRET_OPTIONS = (
    InterpretOption("range_real_undecided", "lesson.l07.sensitivity.interpret.option.range_real_undecided"),
    InterpretOption("range_collapsed_erased", "lesson.l07.sensitivity.interpret.option.range_collapsed_erased"),
    InterpretOption("clearly_meets", "lesson.l07.sensitivity.interpret.option.clearly_meets"),
    InterpretOption("data_useless", "lesson.l07.sensitivity.interpret.option.data_useless"),
)

# --- Final Decision ------------------------------------------------------

TARGET_SCOPE_FIELD = BriefField(
    key="target_scope",
    prompt_key="lesson.l07.decision.target_scope.prompt",
    options=(
        BriefOption("this_period_go_orders", "lesson.l07.decision.target_scope.option.this_period_go_orders"),
        BriefOption("captured_only", "lesson.l07.decision.target_scope.option.captured_only"),
        BriefOption("all_novamart_orders", "lesson.l07.decision.target_scope.option.all_novamart_orders"),
    ),
)

MISSINGNESS_DIAGNOSIS_FIELD = BriefField(
    key="missingness_diagnosis",
    prompt_key="lesson.l07.decision.missingness_diagnosis.prompt",
    options=(
        BriefOption("legacy_peak_workflow", "lesson.l07.decision.missingness_diagnosis.option.legacy_peak_workflow"),
        BriefOption("random_noise", "lesson.l07.decision.missingness_diagnosis.option.random_noise"),
        BriefOption("unrelated_factor", "lesson.l07.decision.missingness_diagnosis.option.unrelated_factor"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l07.decision.evidence.prompt",
    min_count=2,
    max_count=3,
)

TREATMENT_FIELD = BriefField(
    key="treatment",
    prompt_key="lesson.l07.decision.treatment.prompt",
    options=(
        BriefOption("preserve_and_report", "lesson.l07.decision.treatment.option.preserve_and_report"),
        BriefOption("fill_global_median", "lesson.l07.decision.treatment.option.fill_global_median"),
        BriefOption("fill_group_median", "lesson.l07.decision.treatment.option.fill_group_median"),
        BriefOption("fill_zero", "lesson.l07.decision.treatment.option.fill_zero"),
    ),
)

KPI_RESULT_FIELD = BriefField(
    key="kpi_result",
    prompt_key="lesson.l07.decision.kpi_result.prompt",
    options=(
        BriefOption("complete_case_ship_it", "lesson.l07.decision.kpi_result.option.complete_case_ship_it"),
        BriefOption("range_straddles", "lesson.l07.decision.kpi_result.option.range_straddles"),
        BriefOption("group_median_close_enough", "lesson.l07.decision.kpi_result.option.group_median_close_enough"),
        BriefOption("cannot_report", "lesson.l07.decision.kpi_result.option.cannot_report"),
    ),
)

SENSITIVITY_FIELD = BriefField(
    key="sensitivity",
    prompt_key="lesson.l07.decision.sensitivity.prompt",
    options=(
        BriefOption("bounds_are_real_assumptions", "lesson.l07.decision.sensitivity.option.bounds_are_real_assumptions"),
        BriefOption("bounds_are_decorative", "lesson.l07.decision.sensitivity.option.bounds_are_decorative"),
        BriefOption("exact_truth_knowable", "lesson.l07.decision.sensitivity.option.exact_truth_knowable"),
    ),
)

STRUCTURAL_TREATMENT_FIELD = BriefField(
    key="structural_treatment",
    prompt_key="lesson.l07.decision.structural_treatment.prompt",
    options=(
        BriefOption("leave_as_missing", "lesson.l07.decision.structural_treatment.option.leave_as_missing"),
        BriefOption("impute_segment_average", "lesson.l07.decision.structural_treatment.option.impute_segment_average"),
        BriefOption("drop_missing_cold_pack", "lesson.l07.decision.structural_treatment.option.drop_missing_cold_pack"),
    ),
)

REQUIRED_ACTION_FIELD = BriefField(
    key="required_action",
    prompt_key="lesson.l07.decision.required_action.prompt",
    options=(
        BriefOption("fix_capture_path", "lesson.l07.decision.required_action.option.fix_capture_path"),
        BriefOption("nothing_needed", "lesson.l07.decision.required_action.option.nothing_needed"),
        BriefOption("impute_better", "lesson.l07.decision.required_action.option.impute_better"),
        BriefOption("block_legacy_scanners", "lesson.l07.decision.required_action.option.block_legacy_scanners"),
    ),
)

# --- Optional Mastery: a different export, transfer not repetition ------

MASTERY_FIELD = MultiChoiceField(
    key="needs_investigation",
    prompt_key="lesson.l07.mastery.prompt",
    min_count=1,
    max_count=4,
    options=(
        BriefOption("restock_date", "lesson.l07.mastery.option.restock_date"),
        BriefOption("supplier_lead_days", "lesson.l07.mastery.option.supplier_lead_days"),
        BriefOption("warehouse_zone", "lesson.l07.mastery.option.warehouse_zone"),
        BriefOption("unit_cost", "lesson.l07.mastery.option.unit_cost"),
    ),
)

# Every real option-bearing BriefField/MultiChoiceField in this lesson,
# regardless of which scene ends up rendering it - matching every lesson
# from L05 onward's own convention, so test_option_label_widths.py can
# check them all the same way without a separate import per field.
DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    COLD_PACK_MEANING_FIELD,
    PROMO_MEANING_FIELD,
    PICK_MINUTES_MEANING_FIELD,
    TARGET_SCOPE_FIELD,
    MISSINGNESS_DIAGNOSIS_FIELD,
    TREATMENT_FIELD,
    KPI_RESULT_FIELD,
    SENSITIVITY_FIELD,
    STRUCTURAL_TREATMENT_FIELD,
    REQUIRED_ACTION_FIELD,
    MASTERY_FIELD,
)


def build_lesson_seven_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 07's real investigation: 400 hidden Go orders,
    three real missingness cases (a real measurement failure concentrated
    in a legacy-scanner/peak-hour workflow, a structural not-applicable
    gap, and a null with real business meaning), all feeding one launch-
    readiness KPI (this period's picking-SLA rate). Every treatment is
    declared (Contract Builder) before it's executed (WorkbenchScene
    repair), and the central pick_minutes problem is declared only after
    a real investigation, not before. LessonContext is threaded through
    every analytical stage exactly like L01-L06.

    Every downstream stage reconstructs the real dataset via
    twist_data.apply_round1/apply_round2, replaying the student's own
    actual RepairResolution against the raw export - the same generic
    real-replay discipline the L06 follow-up built, adopted here with no
    further framework changes needed."""
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
            generate_orders(),
            issues=(),
            on_complete=on_complete,
            inspection_prompt=RAW_INSPECTION_PROMPT,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    # --- Round 1: declare, then execute (up front - both discoverable
    # immediately, no investigation needed) ---

    def contract_builder_round1(advance):
        def on_complete(brief):
            collected["round1_contract"] = brief
            advance()

        return BriefBuilderScene(
            app,
            "lesson.l07.contract_title",
            (COLD_PACK_MEANING_FIELD, PROMO_MEANING_FIELD),
            on_complete,
            guided=True,
        )

    def repair_round1(advance):
        def on_complete(resolution):
            collected["round1_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, generate_orders(), ROUND1_ISSUES, on_complete, guided=True, context=context)

    def first_attempt(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        rate = complete_case_rate(dataset)

        def on_complete(interpretation):
            collected["first_attempt_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l07.first_attempt.title",
            narrative_keys=("dialogue.l07_first_attempt.line1", "dialogue.l07_first_attempt.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l07.first_attempt.complete_case_label", rate, python_code=complete_case_rate_python_code()
                ),
                ComparisonValue("lesson.l07.first_attempt.target_label", SLA_TARGET),
            ),
            interpret_prompt_key="lesson.l07.first_attempt.interpret_prompt",
            interpret_options=FIRST_ATTEMPT_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=_format_rate,
        )

    # --- Missingness investigation ---

    def missingness_investigation(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        requests = _build_investigation_requests(dataset)

        def on_complete(choices):
            _record_investigation_evidence(context, dataset, choices)
            _sync_context_into_collected()
            advance()

        return SegmentSlicerScene(
            app,
            "lesson.l07.investigation_title",
            requests,
            on_complete,
            guided=True,
            row_column_label_key="lesson.l07.investigation.row_column_label",
            before_column_label_key="lesson.l07.investigation.before_column_label",
            after_column_label_key="lesson.l07.investigation.after_column_label",
            pick_hint_key="lesson.l07.investigation.pick_hint",
            value_format=lambda segment, value: f"{value:.0%}",
            flag_check=lambda before, after: after > before,
        )

    def root_cause_pivot(advance):
        return DialogueScene(app, ROOT_CAUSE_PIVOT_DIALOGUE, on_complete=advance)

    # --- Round 2: declare (now informed), then execute ---

    def contract_builder_round2(advance):
        def on_complete(brief):
            collected["round2_contract"] = brief
            advance()

        return BriefBuilderScene(
            app,
            "lesson.l07.contract_title",
            (PICK_MINUTES_MEANING_FIELD,),
            on_complete,
            guided=True,
            tiered_hint_keys=PICK_MINUTES_TIERED_HINTS,
        )

    def repair_round2(advance):
        def on_complete(resolution):
            collected["round2_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        dataset = apply_round1(collected.get("round1_resolution", {}))
        return WorkbenchScene(app, dataset, ROUND2_ISSUES, on_complete, guided=True, context=context)

    def sensitivity_reveal(advance):
        dataset = apply_round2(collected.get("round1_resolution", {}), collected.get("round2_resolution", {}))
        lower, upper = sla_bounds(dataset)

        def on_complete(interpretation):
            collected["sensitivity_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l07.sensitivity.title",
            narrative_keys=("dialogue.l07_sensitivity.line1", "dialogue.l07_sensitivity.line2"),
            comparisons=(
                ComparisonValue("lesson.l07.sensitivity.lower_label", lower, python_code=sla_lower_bound_python_code()),
                ComparisonValue("lesson.l07.sensitivity.upper_label", upper, python_code=sla_upper_bound_python_code()),
                ComparisonValue("lesson.l07.sensitivity.target_label", SLA_TARGET),
            ),
            interpret_prompt_key="lesson.l07.sensitivity.interpret_prompt",
            interpret_options=SENSITIVITY_INTERPRET_OPTIONS,
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
            "lesson.l07.decision_title",
            steps=(
                TARGET_SCOPE_FIELD,
                MISSINGNESS_DIAGNOSIS_FIELD,
                DECISION_EVIDENCE_FIELD,
                TREATMENT_FIELD,
                KPI_RESULT_FIELD,
                SENSITIVITY_FIELD,
                STRUCTURAL_TREATMENT_FIELD,
                REQUIRED_ACTION_FIELD,
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
                    app, "lesson.l07.mastery.title", (MASTERY_FIELD,), on_task_complete, guided=False
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
            collected["mastery_selection"] = result["needs_investigation"] if result else ()
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l07.mastery.title",
            line_keys=("dialogue.l07_mastery.line1", "dialogue.l07_mastery.line2"),
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

    def _build_result() -> LessonSevenResult:
        round1_contract = collected.get("round1_contract", {})
        round2_contract = collected.get("round2_contract", {})
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonSevenResult(
            cold_pack_meaning=round1_contract.get("cold_pack_meaning", ""),
            promo_meaning=round1_contract.get("promo_meaning", ""),
            pick_minutes_meaning=round2_contract.get("pick_minutes_meaning", ""),
            round1_resolution=collected.get("round1_resolution", {}),
            round2_resolution=collected.get("round2_resolution", {}),
            sensitivity_interpretation=collected.get("sensitivity_interpretation", ""),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_selection=frozenset(collected.get("mastery_selection", ())),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_07.number, 0)
        evaluation = score_lesson_seven(result, LESSON_07, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        raw_inspection,
        contract_builder_round1,
        repair_round1,
        first_attempt,
        missingness_investigation,
        root_cause_pivot,
        contract_builder_round2,
        repair_round2,
        sensitivity_reveal,
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
        lesson_number=7,
        collected=collected,
        definition=LESSON_07,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
