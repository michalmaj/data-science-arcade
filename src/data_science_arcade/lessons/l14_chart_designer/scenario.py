from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l14_chart_designer.definition import LESSON_14
from data_science_arcade.lessons.l14_chart_designer.orders import (
    DATE_CYCLE,
    DAILY_ORDER_COUNTS,
    DELIVERY_BIN_COUNTS,
    DELIVERY_BIN_EDGES,
    STORE_IDS,
    STORE_RETURN_RATES,
    generate_orders,
)
from data_science_arcade.lessons.l14_chart_designer.scoring import CRITICAL_EVIDENCE_KEYS, LessonFourteenResult, score_lesson_fourteen
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_builder_scene import ChartBuilderScene, ChartFormOption
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l14_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l14_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l14_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_briefing.line4"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l14_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_debrief.line3"),
    )
)
MASTERY_DIALOGUE_KEYS = ("dialogue.l14_mastery.line1", "dialogue.l14_mastery.line2", "dialogue.l14_mastery.line3")

# --- Chart-form options - each fully self-contained (real labels/values
# or real raw_values, never a scale/window/denominator override - that
# capability simply doesn't exist on ChartBuilderScene/ChartFormOption at
# all, unlike the shared ChartDesignerScene reserved for L28). ----------
#
# Store comparison: bar is the real best fit (stores are discrete
# categories with no natural adjacency); line is real, legitimate data,
# just semantically risky here (implies a continuity between categories
# that doesn't exist) - never framed as "false."

_MODULE_ORDERS = generate_orders()

STORE_RATES_NATURAL = tuple(STORE_RETURN_RATES[store_id] for store_id in STORE_IDS)
STORE_IDS_SORTED_DESC = tuple(sorted(STORE_IDS, key=lambda store_id: -STORE_RETURN_RATES[store_id]))
STORE_RATES_SORTED_DESC = tuple(STORE_RETURN_RATES[store_id] for store_id in STORE_IDS_SORTED_DESC)


def _pct_format(value: float) -> str:
    return f"{value:.1f}%"


STORE_OPTIONS = (
    ChartFormOption(
        "bar_natural_order",
        "lesson.l14.builder.stores.option.bar_natural_order",
        "bar",
        "store_id vs return rate (%)",
        labels=STORE_IDS,
        values=STORE_RATES_NATURAL,
        value_format=_pct_format,
    ),
    ChartFormOption(
        "bar_sorted_desc",
        "lesson.l14.builder.stores.option.bar_sorted_desc",
        "bar",
        "store_id vs return rate (%), sorted highest first",
        labels=STORE_IDS_SORTED_DESC,
        values=STORE_RATES_SORTED_DESC,
        value_format=_pct_format,
    ),
    ChartFormOption(
        "line",
        "lesson.l14.builder.stores.option.line",
        "line",
        "store_id vs return rate (%)",
        labels=STORE_IDS,
        values=STORE_RATES_NATURAL,
        value_format=_pct_format,
    ),
)

# Time trend: both real options stay chronological - never a reordered
# x-axis, the one genuinely off-limits move for this ask. Line is the
# real best fit (a real time order makes connecting the points
# meaningful); a plain chronological bar is real, legitimate, just
# answers "how many, exactly, each day" rather than "how did it move."

_DATE_LABELS = tuple(date[5:] for date in DATE_CYCLE)  # "03-01".."03-14"
_DAILY_COUNTS_FLOAT = tuple(float(count) for count in DAILY_ORDER_COUNTS)

DATES_OPTIONS = (
    ChartFormOption(
        "line",
        "lesson.l14.builder.dates.option.line",
        "line",
        "order_date vs daily order count",
        labels=_DATE_LABELS,
        values=_DAILY_COUNTS_FLOAT,
    ),
    ChartFormOption(
        "bar_chronological",
        "lesson.l14.builder.dates.option.bar_chronological",
        "bar",
        "order_date vs daily order count",
        labels=_DATE_LABELS,
        values=_DAILY_COUNTS_FLOAT,
    ),
)

# Delivery-time distribution: histogram is the real best fit. The only
# real, safe alternative at this same 260-row scope is a bar of
# store-level averages - a genuinely different, real, small (4-category)
# chart that answers a comparison question, not the frequency/shape
# question actually asked. Never a raw-value bar/line: that would need
# one label per observation, which this scene structurally never offers
# (see ChartBuilderScene's own docstring).

_STORE_AVG_DELIVERY_MINUTES = tuple(
    float(_MODULE_ORDERS.frame.groupby("store_id")["delivery_minutes"].mean()[store_id]) for store_id in STORE_IDS
)
_DELIVERY_MINUTES_RAW = tuple(float(value) for value in _MODULE_ORDERS.frame["delivery_minutes"])

DISTRIBUTION_OPTIONS = (
    ChartFormOption(
        "histogram",
        "lesson.l14.builder.distribution.option.histogram",
        "histogram",
        "delivery_minutes frequency",
        raw_values=_DELIVERY_MINUTES_RAW,
        bin_edges=DELIVERY_BIN_EDGES,
    ),
    ChartFormOption(
        "bar_store_averages",
        "lesson.l14.builder.distribution.option.bar_store_averages",
        "bar",
        "store_id vs avg delivery_minutes",
        labels=STORE_IDS,
        values=_STORE_AVG_DELIVERY_MINUTES,
        value_format=lambda v: f"{v:.0f} min",
    ),
)

# --- Reveal interpret options - same evidence_key on every option, none
# of these three facts are path-aware (they're true regardless of which
# chart form was actually picked), applying the L11-follow-up lesson. --

STORE_CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption(
        "implies_false_continuity",
        "lesson.l14.store_consequence.interpret.option.implies_false_continuity",
        evidence_key="lesson.l14.evidence.store_categories",
    ),
    InterpretOption(
        "shows_real_trend",
        "lesson.l14.store_consequence.interpret.option.shows_real_trend",
        evidence_key="lesson.l14.evidence.store_categories",
    ),
    InterpretOption(
        "doesnt_matter", "lesson.l14.store_consequence.interpret.option.doesnt_matter", evidence_key="lesson.l14.evidence.store_categories"
    ),
)

DATES_CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption(
        "real_chronological_meaning",
        "lesson.l14.dates_consequence.interpret.option.real_chronological_meaning",
        evidence_key="lesson.l14.evidence.date_order",
    ),
    InterpretOption(
        "order_doesnt_matter", "lesson.l14.dates_consequence.interpret.option.order_doesnt_matter", evidence_key="lesson.l14.evidence.date_order"
    ),
    InterpretOption(
        "only_bars_are_honest",
        "lesson.l14.dates_consequence.interpret.option.only_bars_are_honest",
        evidence_key="lesson.l14.evidence.date_order",
    ),
)

DISTRIBUTION_CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption(
        "bar_height_is_frequency",
        "lesson.l14.distribution_consequence.interpret.option.bar_height_is_frequency",
        evidence_key="lesson.l14.evidence.histogram_binning",
    ),
    InterpretOption(
        "bar_height_is_a_value",
        "lesson.l14.distribution_consequence.interpret.option.bar_height_is_a_value",
        evidence_key="lesson.l14.evidence.histogram_binning",
    ),
    InterpretOption(
        "bins_are_arbitrary",
        "lesson.l14.distribution_consequence.interpret.option.bins_are_arbitrary",
        evidence_key="lesson.l14.evidence.histogram_binning",
    ),
)

# --- Final Decision ("Chart Packet") ---------------------------------

CHART_FORM_FOR_STORES_FIELD = BriefField(
    key="chart_form_for_stores",
    prompt_key="lesson.l14.decision.chart_form_for_stores.prompt",
    options=(
        BriefOption("bar_sorted_desc", "lesson.l14.decision.chart_form_for_stores.option.bar_sorted_desc"),
        BriefOption("bar_natural_order", "lesson.l14.decision.chart_form_for_stores.option.bar_natural_order"),
        BriefOption("line", "lesson.l14.decision.chart_form_for_stores.option.line"),
    ),
)
RATIONALE_FOR_STORES_FORM_FIELD = BriefField(
    key="rationale_for_stores_form",
    prompt_key="lesson.l14.decision.rationale_for_stores_form.prompt",
    options=(
        BriefOption("bars_compare_magnitude", "lesson.l14.decision.rationale_for_stores_form.option.bars_compare_magnitude"),
        BriefOption("line_looks_smoother", "lesson.l14.decision.rationale_for_stores_form.option.line_looks_smoother"),
        BriefOption("either_works_equally", "lesson.l14.decision.rationale_for_stores_form.option.either_works_equally"),
    ),
)
CHART_FORM_FOR_DATES_FIELD = BriefField(
    key="chart_form_for_dates",
    prompt_key="lesson.l14.decision.chart_form_for_dates.prompt",
    options=(
        BriefOption("line", "lesson.l14.decision.chart_form_for_dates.option.line"),
        BriefOption("bar_chronological", "lesson.l14.decision.chart_form_for_dates.option.bar_chronological"),
    ),
)
RATIONALE_FOR_DATES_FORM_FIELD = BriefField(
    key="rationale_for_dates_form",
    prompt_key="lesson.l14.decision.rationale_for_dates_form.prompt",
    options=(
        BriefOption("real_time_order_shows_change", "lesson.l14.decision.rationale_for_dates_form.option.real_time_order_shows_change"),
        BriefOption("bars_always_more_precise", "lesson.l14.decision.rationale_for_dates_form.option.bars_always_more_precise"),
        BriefOption("form_doesnt_matter", "lesson.l14.decision.rationale_for_dates_form.option.form_doesnt_matter"),
    ),
)
CHART_FORM_FOR_DISTRIBUTION_FIELD = BriefField(
    key="chart_form_for_distribution",
    prompt_key="lesson.l14.decision.chart_form_for_distribution.prompt",
    options=(
        BriefOption("histogram", "lesson.l14.decision.chart_form_for_distribution.option.histogram"),
        BriefOption("bar_store_averages", "lesson.l14.decision.chart_form_for_distribution.option.bar_store_averages"),
    ),
)
COMMUNICATION_PRINCIPLE_FIELD = BriefField(
    key="communication_principle",
    prompt_key="lesson.l14.decision.communication_principle.prompt",
    options=(
        BriefOption("honest_complete_caption", "lesson.l14.decision.communication_principle.option.honest_complete_caption"),
        BriefOption("overclaiming_caption", "lesson.l14.decision.communication_principle.option.overclaiming_caption"),
        BriefOption("vague_caption", "lesson.l14.decision.communication_principle.option.vague_caption"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l14.decision.evidence.prompt", min_count=2, max_count=3)
DECISION_FIELDS: tuple[BriefField, ...] = (
    CHART_FORM_FOR_STORES_FIELD,
    RATIONALE_FOR_STORES_FORM_FIELD,
    CHART_FORM_FOR_DATES_FIELD,
    RATIONALE_FOR_DATES_FORM_FIELD,
    CHART_FORM_FOR_DISTRIBUTION_FIELD,
    COMMUNICATION_PRINCIPLE_FIELD,
)

# --- Optional mastery: SLA-vs-target, inverting "time series = line" -----

MASTERY_SUPPORTING_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l14.mastery.field.supporting_evidence.prompt",
    options=(
        BriefOption("ask_names_a_fixed_threshold", "lesson.l14.mastery.option.supporting_evidence.ask_names_a_fixed_threshold"),
        BriefOption("its_a_time_series", "lesson.l14.mastery.option.supporting_evidence.its_a_time_series"),
        BriefOption("twelve_months_of_data", "lesson.l14.mastery.option.supporting_evidence.twelve_months_of_data"),
        BriefOption("values_moved_up_and_down", "lesson.l14.mastery.option.supporting_evidence.values_moved_up_and_down"),
    ),
    min_count=1,
    max_count=2,
)
MASTERY_CHART_JUDGMENT_FIELD = BriefField(
    key="mastery_chart_judgment",
    prompt_key="lesson.l14.mastery.field.chart_judgment.prompt",
    options=(
        BriefOption("needs_target_reference_line", "lesson.l14.mastery.option.chart_judgment.needs_target_reference_line"),
        BriefOption("plain_line_is_enough", "lesson.l14.mastery.option.chart_judgment.plain_line_is_enough"),
        BriefOption("cant_tell", "lesson.l14.mastery.option.chart_judgment.cant_tell"),
    ),
)


def build_lesson_fourteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 14's real investigation: one 260-order NovaMart
    feed, three real business asks (store comparison, 14-day trend,
    delivery-time distribution), each answered by picking a real chart
    form for a real stated ask - never a bare "which chart is always
    best" lookup. LessonContext is threaded through every analytical
    stage exactly like L06-L13.

    Each ask is a real cold-pick -> real rendered consequence -> one
    consolidated revision (all three re-editable together) sequence.
    METHOD is scored purely off the three FINAL EXECUTED chart forms
    (after the revision) - the Final Decision's own claims are checked
    separately under REASONING, applying the L13 follow-up's own lesson
    proactively (see LessonFourteenResult's own docstring)."""
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

    # --- Store comparison ---

    def store_attempt(advance):
        context.record_action(
            label_key="lesson.l14.data_prep.stores_title",
            python_code="returns_by_store = (\n    orders.groupby('store_id')['returned']\n    .mean()\n    .mul(100)\n)",
            key="stores_data_prep",
        )

        def on_complete(choice):
            collected["chart_choice_stores_first"] = choice
            collected["chart_choice_stores"] = choice
            _sync_context_into_collected()
            advance()

        return ChartBuilderScene(
            app,
            "lesson.l14.builder.stores.title",
            "lesson.l14.builder.stores.ask",
            STORE_OPTIONS,
            on_complete,
            context,
            mirror_action_key="stores_chart_pipeline",
            hint_key="lesson.l14.builder.stores.hint",
            guided=True,
        )

    def store_consequence_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l14.store_consequence.title",
            narrative_keys=("dialogue.l14_store_consequence.line1", "dialogue.l14_store_consequence.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l14.store_consequence.highest_label",
                    max(STORE_RATES_NATURAL),
                    python_code="returns_by_store.idxmax(), returns_by_store.max()",
                    value_format=_pct_format,
                ),
                ComparisonValue(
                    "lesson.l14.store_consequence.lowest_label",
                    min(STORE_RATES_NATURAL),
                    python_code="returns_by_store.idxmin(), returns_by_store.min()",
                    value_format=_pct_format,
                ),
            ),
            interpret_prompt_key="lesson.l14.store_consequence.interpret_prompt",
            interpret_options=STORE_CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Time trend ---

    def dates_attempt(advance):
        context.record_action(
            label_key="lesson.l14.data_prep.dates_title",
            python_code="daily_orders = (\n    orders.groupby('order_date')\n    .size()\n    .sort_index()\n)",
            key="dates_data_prep",
        )

        def on_complete(choice):
            collected["chart_choice_dates_first"] = choice
            collected["chart_choice_dates"] = choice
            _sync_context_into_collected()
            advance()

        return ChartBuilderScene(
            app,
            "lesson.l14.builder.dates.title",
            "lesson.l14.builder.dates.ask",
            DATES_OPTIONS,
            on_complete,
            context,
            mirror_action_key="dates_chart_pipeline",
            hint_key="lesson.l14.builder.dates.hint",
            guided=True,
        )

    def dates_consequence_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l14.dates_consequence.title",
            narrative_keys=("dialogue.l14_dates_consequence.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l14.dates_consequence.first_day_label",
                    float(DAILY_ORDER_COUNTS[0]),
                    python_code="daily_orders.iloc[0]",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l14.dates_consequence.last_day_label",
                    float(DAILY_ORDER_COUNTS[-1]),
                    python_code="daily_orders.iloc[-1]",
                    value_format=lambda v: f"{v:,.0f}",
                ),
            ),
            interpret_prompt_key="lesson.l14.dates_consequence.interpret_prompt",
            interpret_options=DATES_CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Delivery-time distribution ---

    def distribution_attempt(advance):
        context.record_action(
            label_key="lesson.l14.data_prep.distribution_title",
            python_code=(
                "import numpy as np\n"
                "delivery_minutes = orders['delivery_minutes']\n"
                "hist_counts, hist_edges = np.histogram(\n"
                f"    delivery_minutes,\n    bins={list(DELIVERY_BIN_EDGES)},\n"
                ")"
            ),
            key="distribution_data_prep",
        )

        def on_complete(choice):
            collected["chart_choice_distribution_first"] = choice
            collected["chart_choice_distribution"] = choice
            _sync_context_into_collected()
            advance()

        return ChartBuilderScene(
            app,
            "lesson.l14.builder.distribution.title",
            "lesson.l14.builder.distribution.ask",
            DISTRIBUTION_OPTIONS,
            on_complete,
            context,
            mirror_action_key="distribution_chart_pipeline",
            hint_key="lesson.l14.builder.distribution.hint",
            guided=True,
        )

    def distribution_consequence_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l14.distribution_consequence.title",
            narrative_keys=("dialogue.l14_distribution_consequence.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l14.distribution_consequence.busiest_bin_label",
                    float(max(DELIVERY_BIN_COUNTS)),
                    python_code="hist_counts.max()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l14.distribution_consequence.quietest_bin_label",
                    float(min(DELIVERY_BIN_COUNTS)),
                    python_code="hist_counts.min()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
            ),
            interpret_prompt_key="lesson.l14.distribution_consequence.interpret_prompt",
            interpret_options=DISTRIBUTION_CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Consolidated revision offer (all three, together) -----------

    def consolidated_revision_offer(advance):
        def build_revision_task(on_task_complete):
            def on_stores_revised(choice):
                collected["chart_choice_stores"] = choice
                middle_sequence.advance_to_second()

            def on_dates_revised(choice):
                collected["chart_choice_dates"] = choice
                inner_sequence.advance_to_second()

            def on_distribution_revised(choice):
                collected["chart_choice_distribution"] = choice
                on_task_complete(None)

            def build_dates_revision():
                return ChartBuilderScene(
                    app,
                    "lesson.l14.builder.dates.title",
                    "lesson.l14.builder.dates.ask",
                    DATES_OPTIONS,
                    on_dates_revised,
                    context,
                    initial_choice=collected["chart_choice_dates"],
                    mirror_action_key="dates_chart_pipeline",
                    hint_key="lesson.l14.builder.dates.hint",
                    guided=True,
                )

            def build_distribution_revision():
                return ChartBuilderScene(
                    app,
                    "lesson.l14.builder.distribution.title",
                    "lesson.l14.builder.distribution.ask",
                    DISTRIBUTION_OPTIONS,
                    on_distribution_revised,
                    context,
                    initial_choice=collected["chart_choice_distribution"],
                    mirror_action_key="distribution_chart_pipeline",
                    hint_key="lesson.l14.builder.distribution.hint",
                    guided=True,
                )

            inner_sequence = SequenceScene(app, first=build_dates_revision(), build_second=build_distribution_revision)
            middle_sequence = SequenceScene(
                app,
                first=ChartBuilderScene(
                    app,
                    "lesson.l14.builder.stores.title",
                    "lesson.l14.builder.stores.ask",
                    STORE_OPTIONS,
                    on_stores_revised,
                    context,
                    initial_choice=collected["chart_choice_stores"],
                    mirror_action_key="stores_chart_pipeline",
                    hint_key="lesson.l14.builder.stores.hint",
                    guided=True,
                ),
                build_second=lambda: inner_sequence,
            )
            return middle_sequence

        def on_offer_complete(_engaged, _result):
            _sync_context_into_collected()
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l14.revision_offer.title",
            line_keys=("lesson.l14.revision_offer.line1",),
            engage_label_key="lesson.l14.revision_offer.engage",
            skip_label_key="lesson.l14.revision_offer.skip",
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
            "lesson.l14.decision_title",
            steps=(
                CHART_FORM_FOR_STORES_FIELD,
                RATIONALE_FOR_STORES_FORM_FIELD,
                CHART_FORM_FOR_DATES_FIELD,
                RATIONALE_FOR_DATES_FORM_FIELD,
                CHART_FORM_FOR_DISTRIBUTION_FIELD,
                COMMUNICATION_PRINCIPLE_FIELD,
                DECISION_EVIDENCE_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l14.mastery.title",
                (MASTERY_SUPPORTING_EVIDENCE_FIELD, MASTERY_CHART_JUDGMENT_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l14.mastery.title",
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

    def _build_result() -> LessonFourteenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonFourteenResult(
            chart_choice_stores_first=collected.get("chart_choice_stores_first"),
            chart_choice_stores=collected.get("chart_choice_stores"),
            chart_choice_dates_first=collected.get("chart_choice_dates_first"),
            chart_choice_dates=collected.get("chart_choice_dates"),
            chart_choice_distribution_first=collected.get("chart_choice_distribution_first"),
            chart_choice_distribution=collected.get("chart_choice_distribution"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_14.number, 0)
        evaluation = score_lesson_fourteen(result, LESSON_14, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        store_attempt,
        store_consequence_reveal,
        dates_attempt,
        dates_consequence_reveal,
        distribution_attempt,
        distribution_consequence_reveal,
        consolidated_revision_offer,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=14,
        collected=collected,
        definition=LESSON_14,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
