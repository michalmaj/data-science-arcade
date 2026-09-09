from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l11_distribution_observatory.definition import LESSON_11
from data_science_arcade.lessons.l11_distribution_observatory.order_values import (
    generate_order_values,
    mastery_process_series,
    order_value_segments,
    segment_mean,
)
from data_science_arcade.lessons.l11_distribution_observatory.scoring import CRITICAL_EVIDENCE_KEYS, LessonElevenResult, score_lesson_eleven
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.distribution_explorer_scene import DistributionExplorerScene, DistributionMarker
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -----------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l11_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l11_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l11_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_briefing.line4"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l11_debrief.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l11_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = ("dialogue.l11_mastery.line1", "dialogue.l11_mastery.line2")

# --- Distribution explore --------------------------------------------------

EXPLORE_INTERPRET_OPTIONS = (
    InterpretOption("mean_looks_representative", "lesson.l11.explore.interpret.option.mean_looks_representative"),
    InterpretOption(
        "mean_falls_in_gap",
        "lesson.l11.explore.interpret.option.mean_falls_in_gap",
        evidence_key="lesson.l11.evidence.center_location",
    ),
    InterpretOption("need_more_data", "lesson.l11.explore.interpret.option.need_more_data"),
)

# --- Capacity check (p90) ---------------------------------------------

CAPACITY_CHECK_INTERPRET_OPTIONS = (
    InterpretOption("use_the_maximum_instead", "lesson.l11.capacity_check.interpret.option.use_the_maximum_instead"),
    InterpretOption(
        "p90_is_the_boundary",
        "lesson.l11.capacity_check.interpret.option.p90_is_the_boundary",
        evidence_key="lesson.l11.evidence.upper_tail_p90",
    ),
    InterpretOption("cant_know_without_more_data", "lesson.l11.capacity_check.interpret.option.cant_know_without_more_data"),
)

# --- Business asks (prior, unscored) ---------------------------------------

FINANCE_PRIOR_FIELD = BriefField(
    key="finance_prior_pick",
    prompt_key="lesson.l11.business_ask.finance.prompt",
    options=(
        BriefOption("median", "lesson.l11.business_ask.option.median"),
        BriefOption("mean", "lesson.l11.business_ask.option.mean"),
        BriefOption("p90", "lesson.l11.business_ask.option.p90"),
    ),
)
PRODUCT_PRIOR_FIELD = BriefField(
    key="product_prior_pick",
    prompt_key="lesson.l11.business_ask.product.prompt",
    options=(
        BriefOption("mean", "lesson.l11.business_ask.option.mean"),
        BriefOption("p90", "lesson.l11.business_ask.option.p90"),
        BriefOption("median", "lesson.l11.business_ask.option.median"),
    ),
)
OPS_PRIOR_FIELD = BriefField(
    key="ops_prior_pick",
    prompt_key="lesson.l11.business_ask.ops.prompt",
    options=(
        BriefOption("median", "lesson.l11.business_ask.option.median"),
        BriefOption("mean", "lesson.l11.business_ask.option.mean"),
        BriefOption("p90", "lesson.l11.business_ask.option.p90"),
    ),
)
BUSINESS_ASKS_FIELDS: tuple[BriefField, ...] = (FINANCE_PRIOR_FIELD, PRODUCT_PRIOR_FIELD, OPS_PRIOR_FIELD)

# --- Shape investigation -----------------------------------------------

SHAPE_INTERPRET_OPTIONS = (
    InterpretOption("one_population_with_outliers", "lesson.l11.shape.interpret.option.one_population_with_outliers"),
    InterpretOption(
        "looks_like_two_populations",
        "lesson.l11.shape.interpret.option.looks_like_two_populations",
        evidence_key="lesson.l11.evidence.shape_mixture",
    ),
    InterpretOption("roughly_symmetric", "lesson.l11.shape.interpret.option.roughly_symmetric"),
)

# --- Segment reveal ------------------------------------------------------

SEGMENT_REVEAL_INTERPRET_OPTIONS = (
    InterpretOption("segments_dont_matter", "lesson.l11.segment_reveal.interpret.option.segments_dont_matter"),
    InterpretOption(
        "segments_explain_mixture",
        "lesson.l11.segment_reveal.interpret.option.segments_explain_mixture",
        evidence_key="lesson.l11.evidence.segment_explains_mixture",
    ),
    InterpretOption("need_more_data_still", "lesson.l11.segment_reveal.interpret.option.need_more_data_still"),
)

# --- Final Decision --------------------------------------------------------

FINANCE_FINAL_FIELD = BriefField(
    key="finance_summary_choice",
    prompt_key="lesson.l11.decision.finance_summary_choice.prompt",
    options=(
        BriefOption("median", "lesson.l11.business_ask.option.median"),
        BriefOption("mean", "lesson.l11.business_ask.option.mean"),
        BriefOption("p90", "lesson.l11.business_ask.option.p90"),
    ),
)
PRODUCT_FINAL_FIELD = BriefField(
    key="product_typical_order_claim",
    prompt_key="lesson.l11.decision.product_typical_order_claim.prompt",
    options=(
        BriefOption("median_denies_mixture", "lesson.l11.decision.product_typical_order_claim.option.median_denies_mixture"),
        BriefOption("median_with_limitation", "lesson.l11.decision.product_typical_order_claim.option.median_with_limitation"),
        BriefOption("mean_as_typical", "lesson.l11.decision.product_typical_order_claim.option.mean_as_typical"),
    ),
)
OPS_FINAL_FIELD = BriefField(
    key="ops_capacity_summary",
    prompt_key="lesson.l11.decision.ops_capacity_summary.prompt",
    options=(
        BriefOption("mean", "lesson.l11.business_ask.option.mean"),
        BriefOption("p90", "lesson.l11.business_ask.option.p90"),
        BriefOption("median", "lesson.l11.business_ask.option.median"),
    ),
)
SHAPE_FIELD = BriefField(
    key="shape_interpretation",
    prompt_key="lesson.l11.decision.shape_interpretation.prompt",
    options=(
        BriefOption("one_population_with_outliers", "lesson.l11.shape.interpret.option.one_population_with_outliers"),
        BriefOption("two_separate_populations", "lesson.l11.decision.shape_interpretation.option.two_separate_populations"),
        BriefOption("roughly_symmetric", "lesson.l11.shape.interpret.option.roughly_symmetric"),
    ),
)
COMMUNICATION_FIELD = BriefField(
    key="communication_recommendation",
    prompt_key="lesson.l11.decision.communication_recommendation.prompt",
    options=(
        BriefOption("one_global_number_for_everyone", "lesson.l11.decision.communication_recommendation.option.one_global_number_for_everyone"),
        BriefOption("always_report_full_histogram_never_a_number", "lesson.l11.decision.communication_recommendation.option.always_report_full_histogram_never_a_number"),
        BriefOption("differentiated_summaries_per_audience", "lesson.l11.decision.communication_recommendation.option.differentiated_summaries_per_audience"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l11.decision.evidence.prompt",
    min_count=2,
    max_count=4,
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    FINANCE_FINAL_FIELD,
    PRODUCT_FINAL_FIELD,
    OPS_FINAL_FIELD,
    SHAPE_FIELD,
    COMMUNICATION_FIELD,
)

# --- Optional mastery -------------------------------------------------

MASTERY_SUPPORTING_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l11.mastery.field.supporting_evidence.prompt",
    options=(
        BriefOption("same_mean", "lesson.l11.mastery.option.supporting_evidence.same_mean"),
        BriefOption("different_spread_or_std", "lesson.l11.mastery.option.supporting_evidence.different_spread_or_std"),
        BriefOption("different_sample_size", "lesson.l11.mastery.option.supporting_evidence.different_sample_size"),
        BriefOption("different_shape_right_skew", "lesson.l11.mastery.option.supporting_evidence.different_shape_right_skew"),
    ),
    min_count=1,
    max_count=2,
)
MASTERY_INTERPRETATION_FIELD = BriefField(
    key="mastery_interpretation",
    prompt_key="lesson.l11.mastery.field.interpretation.prompt",
    options=(
        BriefOption("yes_same_process", "lesson.l11.mastery.option.interpretation.yes_same_process"),
        BriefOption("no_practically_different", "lesson.l11.mastery.option.interpretation.no_practically_different"),
        BriefOption("cant_tell", "lesson.l11.mastery.option.interpretation.cant_tell"),
    ),
)


def build_lesson_eleven_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 11's real investigation: a 100-row NovaMart order-
    value feed mixing two real customer populations, with no `segment`
    column anywhere in the player-facing frame or its schema (see
    order_values.py's own module docstring). LessonContext is threaded
    through every analytical stage exactly like L06-L10.

    DistributionExplorerScene's own toggle markers are never themselves
    scored or recorded as Evidence - only a real interpret choice ever
    is (mirroring ComparisonRevealScene's own established discipline).
    Core METHOD/REASONING/COMMUNICATION all score the FINAL Decision
    Brief's own fields only, never the earlier business_asks prior pass -
    a wrong first guess is a real, un-punished trajectory signal, never
    a permanent cap, exactly like every prior lesson's own productive-
    failure discipline."""
    collected: dict = {}
    context = LessonContext()

    dataset = generate_order_values()
    series = dataset.frame["order_value"]
    values = series.tolist()
    mean = float(series.mean())
    median = float(series.median())
    p25 = float(series.quantile(0.25))
    p75 = float(series.quantile(0.75))
    p90 = float(series.quantile(0.90))
    iqr = p75 - p25

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    # --- Distribution explore ---

    def distribution_explore(advance):
        markers = (
            DistributionMarker("mean", "lesson.l11.marker.mean_label", mean, python_code="orders['order_value'].mean()"),
            DistributionMarker("median", "lesson.l11.marker.median_label", median, python_code="orders['order_value'].median()"),
        )

        def on_complete(interpretation):
            collected["explore_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return DistributionExplorerScene(
            app,
            "lesson.l11.explore.title",
            values,
            markers,
            on_complete,
            context,
            interpret_prompt_key="lesson.l11.explore.interpret_prompt",
            interpret_options=EXPLORE_INTERPRET_OPTIONS,
            interpret_hint_key="lesson.l11.explore.interpret_hint",
        )

    # --- Capacity check (p90) ---

    def capacity_check(advance):
        def on_complete(interpretation):
            collected["capacity_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l11.capacity_check.title",
            narrative_keys=("dialogue.l11_capacity_check.line1", "dialogue.l11_capacity_check.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l11.capacity_check.p90_label", p90, python_code="orders['order_value'].quantile(0.90)", value_format=lambda v: f"${v:,.2f}"
                ),
            ),
            interpret_prompt_key="lesson.l11.capacity_check.interpret_prompt",
            interpret_options=CAPACITY_CHECK_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Business asks (prior) ---

    def business_asks(advance):
        def on_complete(brief):
            collected["business_asks_prior"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l11.business_asks.title", BUSINESS_ASKS_FIELDS, on_complete, guided=True)

    # --- Shape investigation ---

    def shape_investigation(advance):
        def on_complete(interpretation):
            collected["shape_investigation_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l11.shape.title",
            narrative_keys=("dialogue.l11_shape.line1", "dialogue.l11_shape.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l11.shape.p25_label", p25, python_code="orders['order_value'].quantile([0.25, 0.5, 0.75, 0.9])", value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue("lesson.l11.shape.p75_label", p75, value_format=lambda v: f"${v:,.2f}"),
                ComparisonValue("lesson.l11.shape.iqr_label", iqr, value_format=lambda v: f"${v:,.2f}"),
            ),
            interpret_prompt_key="lesson.l11.shape.interpret_prompt",
            interpret_options=SHAPE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Segment reveal ---
    #
    # order_value_segments() is called for the first time only here - the
    # real segment mapping never reaches any earlier stage, and every
    # earlier stage's own AnalyticalAction/python_code never mentions the
    # word "segment" (see test_lesson11_data.py's own construction tests).

    def segment_reveal(advance):
        segments = order_value_segments()
        consumer_mean = segment_mean("consumer")
        business_mean_value = segment_mean("business")
        markers = (
            DistributionMarker(
                "consumer_mean",
                "lesson.l11.segment.consumer_mean_label",
                consumer_mean,
                python_code="orders.loc[orders['segment'] == 'consumer', 'order_value'].mean()",
            ),
            DistributionMarker(
                "business_mean",
                "lesson.l11.segment.business_mean_label",
                business_mean_value,
                python_code="orders.loc[orders['segment'] == 'business', 'order_value'].mean()",
            ),
        )

        def on_complete(interpretation):
            collected["segment_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return DistributionExplorerScene(
            app,
            "lesson.l11.segment_reveal.title",
            values,
            markers,
            on_complete,
            context,
            interpret_prompt_key="lesson.l11.segment_reveal.interpret_prompt",
            interpret_options=SEGMENT_REVEAL_INTERPRET_OPTIONS,
            segment_series=segments,
        )

    # --- Revision offer ---

    def revision_offer(advance):
        def build_revision_task(on_task_complete):
            def on_brief_complete(_brief):
                collected["business_asks_revised"] = True
                on_task_complete(None)

            return BriefBuilderScene(app, "lesson.l11.business_asks.title", BUSINESS_ASKS_FIELDS, on_brief_complete, guided=True)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l11.revision_offer.title",
            line_keys=("lesson.l11.revision_offer.line1",),
            engage_label_key="lesson.l11.revision_offer.engage",
            skip_label_key="lesson.l11.revision_offer.skip",
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
            "lesson.l11.decision_title",
            steps=(
                FINANCE_FINAL_FIELD,
                PRODUCT_FINAL_FIELD,
                OPS_FINAL_FIELD,
                SHAPE_FIELD,
                DECISION_EVIDENCE_FIELD,
                COMMUNICATION_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            process_series = mastery_process_series()
            combined_values = list(process_series[0][2]) + list(process_series[1][2])

            def on_explore_complete(_interpretation):
                sequence.advance_to_second()

            def build_select():
                return BriefBuilderScene(
                    app,
                    "lesson.l11.mastery.title",
                    (MASTERY_SUPPORTING_EVIDENCE_FIELD, MASTERY_INTERPRETATION_FIELD),
                    on_task_complete,
                    guided=False,
                )

            sequence = SequenceScene(
                app,
                first=DistributionExplorerScene(
                    app,
                    "lesson.l11.mastery.title",
                    combined_values,
                    (),
                    on_explore_complete,
                    context,
                    segment_series=process_series,
                    guided=False,
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
            title_key="lesson.l11.mastery.title",
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

    def _build_result() -> LessonElevenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonElevenResult(
            business_asks_prior=collected.get("business_asks_prior", {}),
            decision=decision,
            segment_interpretation_seen=collected.get("segment_interpretation"),
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
            business_asks_revised=collected.get("business_asks_revised", False),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_11.number, 0)
        evaluation = score_lesson_eleven(result, LESSON_11, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        distribution_explore,
        capacity_check,
        business_asks,
        shape_investigation,
        segment_reveal,
        revision_offer,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=11,
        collected=collected,
        definition=LESSON_11,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
