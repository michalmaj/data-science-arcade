from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l09_outlier_patrol.definition import LESSON_09
from data_science_arcade.lessons.l09_outlier_patrol.scoring import CRITICAL_EVIDENCE_KEYS, LessonNineResult, score_lesson_nine
from data_science_arcade.lessons.l09_outlier_patrol.twist_data import (
    ROUND1_ISSUE,
    ROUND2_ISSUES,
    apply_round1,
    apply_round2,
    fence_python_code,
    flagged_count,
    generate_orders,
    generate_support_tickets,
    global_fence,
    median_python_code,
    sum_python_code,
    total_exposure_state,
    typical_standard_order_state,
    zone_describe_python_code,
    zone_fence,
    zone_flag_rate,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask ---------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l09_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l09_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l09_briefing.line4"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_debrief.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l09_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l09_debrief.line3"),
    )
)

# --- Raw inspection ----------------------------------------------------

RAW_INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l09.inspection.prompt",
    options=(
        InspectionOption("obviously_fine", "lesson.l09.inspection.option.obviously_fine"),
        InspectionOption("needs_real_investigation", "lesson.l09.inspection.option.needs_real_investigation"),
        InspectionOption("everything_is_suspicious", "lesson.l09.inspection.option.everything_is_suspicious"),
    ),
    hint_key="lesson.l09.inspection.hint",
)

# --- Detection reveal ---------------------------------------------------

DETECTION_INTERPRET_OPTIONS = (
    InterpretOption("remove_them", "lesson.l09.detection.interpret.option.remove_them"),
    InterpretOption(
        "candidates_not_a_verdict",
        "lesson.l09.detection.interpret.option.candidates_not_a_verdict",
        evidence_key="lesson.l09.evidence.detection_flag_rate",
    ),
    InterpretOption("nothing_worth_checking", "lesson.l09.detection.interpret.option.nothing_worth_checking"),
)

# --- Round 1 consequence reveal ---------------------------------------------

CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption("ship_as_is", "lesson.l09.consequence.interpret.option.ship_as_is"),
    InterpretOption("worth_checking_what_left", "lesson.l09.consequence.interpret.option.worth_checking_what_left"),
    InterpretOption("recompute_blindly", "lesson.l09.consequence.interpret.option.recompute_blindly"),
)

# --- Pipeline Check reveal ---------------------------------------------

PIPELINE_CHECK_INTERPRET_OPTIONS = (
    InterpretOption("looks_ready", "lesson.l09.pipeline_check.interpret.option.looks_ready"),
    InterpretOption("worth_revising", "lesson.l09.pipeline_check.interpret.option.worth_revising"),
    InterpretOption("recompute_blindly", "lesson.l09.pipeline_check.interpret.option.recompute_blindly"),
)

# --- Diagnosis Builder ---------------------------------------------------

_DATA_ENTRY_ERROR_OPTION = BriefOption("data_entry_error", "lesson.l09.diagnosis.option.data_entry_error")
_RARE_BUT_LEGITIMATE_OPTION = BriefOption("rare_but_legitimate", "lesson.l09.diagnosis.option.rare_but_legitimate")
_DOCUMENTED_ANOMALY_OPTION = BriefOption("documented_anomaly", "lesson.l09.diagnosis.option.documented_anomaly")
_NO_REAL_BASIS_OPTION = BriefOption("no_real_basis_to_override", "lesson.l09.diagnosis.option.no_real_basis_to_override")

DECIMAL_DIAGNOSIS_FIELD = BriefField(
    key="decimal_row_diagnosis",
    prompt_key="lesson.l09.diagnosis.decimal_row.prompt",
    hint_key="lesson.l09.diagnosis.decimal_row.hint",
    options=(_RARE_BUT_LEGITIMATE_OPTION, _DATA_ENTRY_ERROR_OPTION, _DOCUMENTED_ANOMALY_OPTION, _NO_REAL_BASIS_OPTION),
)
BULK_DIAGNOSIS_FIELD = BriefField(
    key="bulk_row_diagnosis",
    prompt_key="lesson.l09.diagnosis.bulk_row.prompt",
    hint_key="lesson.l09.diagnosis.bulk_row.hint",
    options=(_DATA_ENTRY_ERROR_OPTION, _RARE_BUT_LEGITIMATE_OPTION, _DOCUMENTED_ANOMALY_OPTION, _NO_REAL_BASIS_OPTION),
)
ANOMALY_DIAGNOSIS_FIELD = BriefField(
    key="anomaly_row_diagnosis",
    prompt_key="lesson.l09.diagnosis.anomaly_row.prompt",
    hint_key="lesson.l09.diagnosis.anomaly_row.hint",
    options=(_DATA_ENTRY_ERROR_OPTION, _NO_REAL_BASIS_OPTION, _DOCUMENTED_ANOMALY_OPTION, _RARE_BUT_LEGITIMATE_OPTION),
)
# --- Final Decision ----------------------------------------------------

CONFIRMED_DATA_ERRORS_FIELD = BriefField(
    key="confirmed_data_errors",
    prompt_key="lesson.l09.decision.confirmed_data_errors.prompt",
    options=(
        BriefOption("bulk_row_too", "lesson.l09.decision.confirmed_data_errors.option.bulk_row_too"),
        BriefOption("decimal_row_only", "lesson.l09.decision.confirmed_data_errors.option.decimal_row_only"),
        BriefOption("anomaly_row_too", "lesson.l09.decision.confirmed_data_errors.option.anomaly_row_too"),
        BriefOption("none_of_them", "lesson.l09.decision.confirmed_data_errors.option.none_of_them"),
    ),
)

BULK_POPULATION_BASIS_FIELD = BriefField(
    key="bulk_order_population_basis",
    prompt_key="lesson.l09.decision.bulk_order_population_basis.prompt",
    options=(
        BriefOption("far_from_median", "lesson.l09.decision.bulk_order_population_basis.option.far_from_median"),
        BriefOption("likely_a_data_error", "lesson.l09.decision.bulk_order_population_basis.option.likely_a_data_error"),
        BriefOption("order_type_metadata", "lesson.l09.decision.bulk_order_population_basis.option.order_type_metadata"),
        BriefOption("no_real_reason", "lesson.l09.decision.bulk_order_population_basis.option.no_real_reason"),
    ),
)

INCIDENT_TREATMENT_FIELD = BriefField(
    key="incident_treatment",
    prompt_key="lesson.l09.decision.incident_treatment.prompt",
    options=(
        BriefOption("drop_it", "lesson.l09.decision.incident_treatment.option.drop_it"),
        BriefOption("correct_it_down", "lesson.l09.decision.incident_treatment.option.correct_it_down"),
        BriefOption("keep_and_flag", "lesson.l09.decision.incident_treatment.option.keep_and_flag"),
        BriefOption("keep_silently", "lesson.l09.decision.incident_treatment.option.keep_silently"),
    ),
)

SEGMENT_TREATMENT_FIELD = BriefField(
    key="segment_treatment",
    prompt_key="lesson.l09.decision.segment_treatment.prompt",
    options=(
        BriefOption("remote_proven_normal", "lesson.l09.decision.segment_treatment.option.remote_proven_normal"),
        BriefOption(
            "build_production_threshold_from_8_records",
            "lesson.l09.decision.segment_treatment.option.build_production_threshold_from_8_records",
        ),
        BriefOption(
            "interpret_in_context_no_auto_remove",
            "lesson.l09.decision.segment_treatment.option.interpret_in_context_no_auto_remove",
        ),
        BriefOption("one_global_threshold", "lesson.l09.decision.segment_treatment.option.one_global_threshold"),
    ),
)

# Shared option shape for both KPI-defensibility fields: given the real
# number the Pipeline Check just showed, is it ready to report? This is
# deliberately never a "guess the exact dollar figure" choice (which
# would need enumerating every reachable pipeline state) - it's a
# defensibility judgment, decoupled from whether the underlying pipeline
# happens to be objectively correct (DATA_QUALITY/METHOD's own job).
_REPORT_DEFENSIBLE_OPTION_KEY = "report_defensible"
_REPORT_PROVISIONAL_OPTION_KEY = "report_provisional"

TYPICAL_KPI_DEFENSIBILITY_FIELD = BriefField(
    key="typical_kpi_defensibility",
    prompt_key="lesson.l09.decision.typical_kpi_defensibility.prompt",
    options=(
        BriefOption("report_different_number", "lesson.l09.decision.kpi_defensibility.option.report_different_number"),
        BriefOption(_REPORT_DEFENSIBLE_OPTION_KEY, "lesson.l09.decision.kpi_defensibility.option.report_defensible"),
        BriefOption(_REPORT_PROVISIONAL_OPTION_KEY, "lesson.l09.decision.kpi_defensibility.option.report_provisional"),
        BriefOption("dont_report", "lesson.l09.decision.kpi_defensibility.option.dont_report"),
    ),
)

TOTAL_KPI_DEFENSIBILITY_FIELD = BriefField(
    key="total_kpi_defensibility",
    prompt_key="lesson.l09.decision.total_kpi_defensibility.prompt",
    options=(
        BriefOption("dont_report", "lesson.l09.decision.kpi_defensibility.option.dont_report"),
        BriefOption(_REPORT_PROVISIONAL_OPTION_KEY, "lesson.l09.decision.kpi_defensibility.option.report_provisional"),
        BriefOption("report_different_number", "lesson.l09.decision.kpi_defensibility.option.report_different_number"),
        BriefOption(_REPORT_DEFENSIBLE_OPTION_KEY, "lesson.l09.decision.kpi_defensibility.option.report_defensible"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l09.decision.evidence.prompt",
    min_count=2,
    max_count=4,
)

PREVENTION_ACTION_FIELD = BriefField(
    key="prevention_action",
    prompt_key="lesson.l09.decision.prevention_action.prompt",
    options=(
        BriefOption("nothing_needed", "lesson.l09.decision.prevention_action.option.nothing_needed"),
        BriefOption("entry_time_sanity_check", "lesson.l09.decision.prevention_action.option.entry_time_sanity_check"),
        BriefOption("manual_review_every_order", "lesson.l09.decision.prevention_action.option.manual_review_every_order"),
        BriefOption("round_every_cost", "lesson.l09.decision.prevention_action.option.round_every_cost"),
    ),
)

SAFE_CLAIM_FIELD = BriefField(
    key="safe_claim",
    prompt_key="lesson.l09.decision.safe_claim.prompt",
    options=(
        BriefOption("exact_everywhere_no_scope_needed", "lesson.l09.decision.safe_claim.option.exact_everywhere_no_scope_needed"),
        BriefOption("both_numbers_scoped_honestly", "lesson.l09.decision.safe_claim.option.both_numbers_scoped_honestly"),
        BriefOption("all_outliers_removed_data_clean", "lesson.l09.decision.safe_claim.option.all_outliers_removed_data_clean"),
        BriefOption("both_numbers_are_the_same", "lesson.l09.decision.safe_claim.option.both_numbers_are_the_same"),
    ),
)

DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    CONFIRMED_DATA_ERRORS_FIELD,
    BULK_POPULATION_BASIS_FIELD,
    INCIDENT_TREATMENT_FIELD,
    SEGMENT_TREATMENT_FIELD,
    TYPICAL_KPI_DEFENSIBILITY_FIELD,
    TOTAL_KPI_DEFENSIBILITY_FIELD,
    PREVENTION_ACTION_FIELD,
    SAFE_CLAIM_FIELD,
)

# --- Optional mastery --------------------------------------------------

MASTERY_MUST_NOT_REMOVE_FIELD = MultiChoiceField(
    key="mastery_must_not_remove",
    prompt_key="lesson.l09.mastery.must_not_remove.prompt",
    options=(
        BriefOption("error_ticket", "lesson.l09.mastery.option.error_ticket"),
        BriefOption("escalation_ticket", "lesson.l09.mastery.option.escalation_ticket"),
    ),
    min_count=1,
    max_count=1,
)

MASTERY_NEEDS_CORRECTION_FIELD = MultiChoiceField(
    key="mastery_needs_correction",
    prompt_key="lesson.l09.mastery.needs_correction.prompt",
    options=(
        BriefOption("escalation_ticket", "lesson.l09.mastery.option.escalation_ticket"),
        BriefOption("error_ticket", "lesson.l09.mastery.option.error_ticket"),
    ),
    min_count=1,
    max_count=1,
)


def build_lesson_nine_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 09's real investigation: an 89-row NovaMart
    Logistics fulfillment-cost feed with 4 genuinely different reasons a
    row can sit far from the rest of the distribution, only one of which
    is an actual data error. LessonContext is threaded through every
    analytical stage exactly like L06-L08.

    Detection (the IQR reveal) is never a student-executed pick - it only
    ever generates candidates. The graded methodology choices are the
    Round 1 blanket-policy pick, the segment scope, and the three real
    per-row treatments, all replayed via twist_data.apply_round1/
    apply_round2 against the raw feed, never a ground-truth substitute."""
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

    def detection_reveal(advance):
        dataset = generate_orders()
        lower, upper = global_fence(dataset)
        count = flagged_count(dataset, lower, upper)

        def on_complete(interpretation):
            collected["detection_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l09.detection.title",
            narrative_keys=("dialogue.l09_detection.line1", "dialogue.l09_detection.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l09.evidence.lower_fence", lower, python_code=fence_python_code(), value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue("lesson.l09.evidence.upper_fence", upper, value_format=lambda v: f"${v:,.2f}"),
                ComparisonValue(
                    "lesson.l09.evidence.detection_flag_rate",
                    float(count),
                    python_code="((orders['fulfillment_cost'] < lower) | (orders['fulfillment_cost'] > upper)).sum()",
                    value_format=lambda v: f"{int(v)} of 89",
                ),
            ),
            interpret_prompt_key="lesson.l09.detection.interpret_prompt",
            interpret_options=DETECTION_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    def repair_round1(advance):
        def on_complete(resolution):
            collected["round1_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, generate_orders(), (ROUND1_ISSUE,), on_complete, guided=True, context=context)

    def consequence_reveal(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))
        n, median = typical_standard_order_state(dataset)
        _, total = total_exposure_state(dataset)

        def on_complete(interpretation):
            collected["consequence_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l09.consequence.title",
            narrative_keys=("dialogue.l09_consequence.line1", "dialogue.l09_consequence.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l09.consequence.orders_remaining_label", float(n), value_format=lambda v: f"{int(v)}"
                ),
                ComparisonValue(
                    "lesson.l09.consequence.median_label",
                    median,
                    python_code=median_python_code(),
                    value_format=lambda v: f"${v:,.2f}",
                ),
                ComparisonValue(
                    "lesson.l09.consequence.total_label", total, python_code=sum_python_code(), value_format=lambda v: f"${v:,.2f}"
                ),
            ),
            interpret_prompt_key="lesson.l09.consequence.interpret_prompt",
            interpret_options=CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Round 1 revision offer ---

    def revision_offer(advance):
        """A real, un-punished chance to revise the Round 1 blanket-policy
        pick after seeing its own real consequence - matching L07/L08's
        own revision-offer precedent (always offered, regardless of
        whether the current pick was already correct)."""
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
            title_key="lesson.l09.revision_offer.title",
            line_keys=("lesson.l09.revision_offer.line1",),
            engage_label_key="lesson.l09.revision_offer.engage",
            skip_label_key="lesson.l09.revision_offer.skip",
        )

    # --- Segment investigation ---

    def segment_investigation(advance):
        dataset = generate_orders()
        lower, upper = global_fence(dataset)
        urban_low, urban_up = zone_fence(dataset, "urban")
        remote_low, remote_up = zone_fence(dataset, "remote")

        request = SegmentRequest(
            key="detection_scope",
            prompt_key="lesson.l09.segment.prompt",
            hint_key="lesson.l09.segment.hint",
            options=(
                SliceOption(
                    "by_zone",
                    "lesson.l09.segment.option.by_zone",
                    segments=(
                        Segment(
                            "urban",
                            "lesson.l09.segment.row.urban",
                            before_rate=zone_flag_rate(dataset, "urban", lower, upper),
                            after_rate=zone_flag_rate(dataset, "urban", urban_low, urban_up),
                        ),
                        Segment(
                            "remote",
                            "lesson.l09.segment.row.remote",
                            before_rate=zone_flag_rate(dataset, "remote", lower, upper),
                            after_rate=zone_flag_rate(dataset, "remote", remote_low, remote_up),
                        ),
                    ),
                ),
            ),
        )

        def on_complete(choices):
            collected["segment_choices"] = choices
            action = context.record_action(
                label_key="lesson.l09.segment.option.by_zone",
                python_code=zone_describe_python_code(),
                key="detection_scope",
            )
            context.record_evidence(
                label_key="lesson.l09.evidence.segment_threshold_contrast", source_action=action, key="detection_scope"
            )
            _sync_context_into_collected()
            advance()

        return SegmentSlicerScene(
            app,
            "lesson.l09.segment.title",
            (request,),
            on_complete,
            guided=True,
            row_column_label_key="lesson.l09.segment.row_column_label",
            before_column_label_key="lesson.l09.segment.before_column_label",
            after_column_label_key="lesson.l09.segment.after_column_label",
            pick_hint_key="lesson.l09.segment.pick_hint",
        )

    # --- Diagnosis Builder ---

    def diagnosis_builder(advance):
        def on_complete(brief):
            collected["diagnosis"] = brief
            advance()

        return BriefBuilderScene(
            app,
            "lesson.l09.diagnosis.title",
            (DECIMAL_DIAGNOSIS_FIELD, BULK_DIAGNOSIS_FIELD, ANOMALY_DIAGNOSIS_FIELD),
            on_complete,
            guided=True,
        )

    # --- Case-by-case treatment ---

    def case_treatment(advance):
        dataset = apply_round1(collected.get("round1_resolution", {}))

        def on_complete(resolution):
            collected["round2_resolution"] = resolution
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(app, dataset, ROUND2_ISSUES, on_complete, guided=True, context=context)

    # --- Pipeline Check reveal ---

    def pipeline_check_reveal(advance):
        """The real, live typical/total numbers this specific pipeline
        actually produces - shown before any Final Decision claim about
        them, and regardless of whether Round 1/Round 2 were picked
        correctly. This is what lets the Final Decision's own KPI fields
        stay a defensibility judgment instead of needing to enumerate
        every reachable dollar figure as a separate pre-authored
        option."""
        dataset = apply_round2(collected.get("round1_resolution", {}), collected.get("round2_resolution", {}))
        n, median = typical_standard_order_state(dataset)
        total_n, total = total_exposure_state(dataset)

        def on_complete(interpretation):
            collected["pipeline_check_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l09.pipeline_check.title",
            narrative_keys=("dialogue.l09_pipeline_check.line1", "dialogue.l09_pipeline_check.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l09.pipeline_check.typical_label", median, python_code=median_python_code(), value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue(
                    "lesson.l09.pipeline_check.total_label", total, python_code=sum_python_code(), value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue("lesson.l09.pipeline_check.orders_label", float(total_n), value_format=lambda v: f"{int(v)}"),
            ),
            interpret_prompt_key="lesson.l09.pipeline_check.interpret_prompt",
            interpret_options=PIPELINE_CHECK_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Round 2 revision offer ---

    def round2_revision_offer(advance):
        """A real, un-punished chance to revise the case-by-case
        treatment after seeing the pipeline's own real result - always
        offered, matching the Round 1 revision offer's own precedent
        (never gated on whether the current picks were already
        correct)."""
        collected["initial_round2_resolution"] = dict(collected.get("round2_resolution", {}))

        def build_revision_task(on_task_complete):
            def on_repair_complete(resolution):
                collected["round2_resolution"] = resolution
                collected["round2_revised"] = True
                _sync_context_into_collected()
                on_task_complete(None)

            dataset = apply_round1(collected.get("round1_resolution", {}))
            return WorkbenchScene(app, dataset, ROUND2_ISSUES, on_repair_complete, guided=True, context=context)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l09.round2_revision_offer.title",
            line_keys=("lesson.l09.round2_revision_offer.line1",),
            engage_label_key="lesson.l09.round2_revision_offer.engage",
            skip_label_key="lesson.l09.round2_revision_offer.skip",
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
            "lesson.l09.decision_title",
            steps=(
                CONFIRMED_DATA_ERRORS_FIELD,
                BULK_POPULATION_BASIS_FIELD,
                INCIDENT_TREATMENT_FIELD,
                SEGMENT_TREATMENT_FIELD,
                TYPICAL_KPI_DEFENSIBILITY_FIELD,
                TOTAL_KPI_DEFENSIBILITY_FIELD,
                DECISION_EVIDENCE_FIELD,
                PREVENTION_ACTION_FIELD,
                SAFE_CLAIM_FIELD,
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
                    "lesson.l09.mastery.title",
                    (MASTERY_MUST_NOT_REMOVE_FIELD, MASTERY_NEEDS_CORRECTION_FIELD),
                    on_task_complete,
                    guided=False,
                )

            sequence = SequenceScene(
                app,
                first=WorkbenchScene(
                    app,
                    generate_support_tickets(),
                    issues=(),
                    on_complete=on_inspect_complete,
                    visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
                ),
                build_second=build_select,
            )
            return sequence

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_must_not_remove"] = result.get("mastery_must_not_remove", ()) if result else ()
            collected["mastery_needs_correction"] = result.get("mastery_needs_correction", ()) if result else ()
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l09.mastery.title",
            line_keys=("dialogue.l09_mastery.line1", "dialogue.l09_mastery.line2"),
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

    def _build_result() -> LessonNineResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonNineResult(
            round1_resolution=collected.get("round1_resolution", {}),
            round2_resolution=collected.get("round2_resolution", {}),
            diagnosis=collected.get("diagnosis", {}),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_must_not_remove=frozenset(collected.get("mastery_must_not_remove", ())),
            mastery_needs_correction=frozenset(collected.get("mastery_needs_correction", ())),
            initial_round1_resolution=collected.get("initial_round1_resolution", {}),
            round1_revised=collected.get("round1_revised", False),
            initial_round2_resolution=collected.get("initial_round2_resolution", {}),
            round2_revised=collected.get("round2_revised", False),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_09.number, 0)
        evaluation = score_lesson_nine(result, LESSON_09, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        raw_inspection,
        detection_reveal,
        repair_round1,
        consequence_reveal,
        revision_offer,
        segment_investigation,
        diagnosis_builder,
        case_treatment,
        pipeline_check_reveal,
        round2_revision_offer,
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
        lesson_number=9,
        collected=collected,
        definition=LESSON_09,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
