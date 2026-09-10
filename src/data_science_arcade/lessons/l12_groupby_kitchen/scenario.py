from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l12_groupby_kitchen.definition import LESSON_12
from data_science_arcade.lessons.l12_groupby_kitchen.orders import (
    STORE_CUSTOMERS,
    cross_store_customers,
    distinct_dates,
    generate_orders,
    naive_mean_of_store_aovs,
    network_aov,
    network_distinct_customers,
    store_distinct_customers,
    store_order_count,
    sum_of_store_distinct_customers,
    weighted_aov,
)
from data_science_arcade.lessons.l12_groupby_kitchen.scoring import CRITICAL_EVIDENCE_KEYS, LessonTwelveResult, score_lesson_twelve
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.aggregation_builder_scene import AggregationBuilderScene, GroupByOption, MetricOption, MetricSlot
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l12_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l12_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_briefing.line3"),
    )
)
FINANCE_ROLLUP_ASK_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l12_finance_rollup.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l12_finance_rollup.line2"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l12_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_debrief.line3"),
    )
)
MASTERY_DIALOGUE_KEYS = ("dialogue.l12_mastery.line1", "dialogue.l12_mastery.line2")

# --- Store summary builder -------------------------------------------------
#
# Every group_by_options entry is a real, safe groupby key (any column can
# be a group key - no crash risk there). Every MetricOption is a real,
# hand-verified-safe (column, func) pair - never independently combined
# from two separate lists, which could reach a genuinely crashing pandas
# call (mean() on a string column, etc.). See AggregationBuilderScene's
# own docstring.

GROUP_BY_OPTIONS = (
    GroupByOption("by_customer", "lesson.l12.builder.group_by.option.customer", "customer_id"),
    GroupByOption("by_store", "lesson.l12.builder.group_by.option.store", "store_id"),
    GroupByOption("by_date", "lesson.l12.builder.group_by.option.date", "order_date"),
)

ORDERS_SLOT = MetricSlot(
    key="orders",
    label_key="lesson.l12.builder.slot.orders.prompt",
    options=(
        MetricOption("sum_revenue_as_orders", "lesson.l12.builder.slot.orders.option.sum_revenue", "revenue", "sum"),
        MetricOption("count_order_id", "lesson.l12.builder.slot.orders.option.count_order_id", "order_id", "size"),
        MetricOption("nunique_customer_id_as_orders", "lesson.l12.builder.slot.orders.option.nunique_customer_id", "customer_id", "nunique"),
    ),
)
REVENUE_SLOT = MetricSlot(
    key="revenue",
    label_key="lesson.l12.builder.slot.revenue.prompt",
    options=(
        MetricOption("mean_revenue_as_revenue", "lesson.l12.builder.slot.revenue.option.mean_revenue", "revenue", "mean"),
        MetricOption("sum_revenue", "lesson.l12.builder.slot.revenue.option.sum_revenue", "revenue", "sum"),
        MetricOption("count_order_id_as_revenue", "lesson.l12.builder.slot.revenue.option.count_order_id", "order_id", "size"),
    ),
)
UNIQUE_CUSTOMERS_SLOT = MetricSlot(
    key="unique_customers",
    label_key="lesson.l12.builder.slot.unique_customers.prompt",
    options=(
        MetricOption("count_order_id_as_customers", "lesson.l12.builder.slot.unique_customers.option.count_order_id", "order_id", "size"),
        MetricOption("nunique_customer_id", "lesson.l12.builder.slot.unique_customers.option.nunique_customer_id", "customer_id", "nunique"),
        MetricOption("nunique_order_id_as_customers", "lesson.l12.builder.slot.unique_customers.option.nunique_order_id", "order_id", "nunique"),
    ),
)
AOV_SLOT = MetricSlot(
    key="aov",
    label_key="lesson.l12.builder.slot.aov.prompt",
    options=(
        MetricOption("sum_revenue_as_aov", "lesson.l12.builder.slot.aov.option.sum_revenue", "revenue", "sum"),
        MetricOption("mean_revenue", "lesson.l12.builder.slot.aov.option.mean_revenue", "revenue", "mean"),
        MetricOption("count_order_id_as_aov", "lesson.l12.builder.slot.aov.option.count_order_id", "order_id", "size"),
    ),
)
METRIC_SLOTS = (ORDERS_SLOT, REVENUE_SLOT, UNIQUE_CUSTOMERS_SLOT, AOV_SLOT)

# --- Output-grain check - path-aware, never a substituted canonical answer
#
# No evidence_key on these options on purpose - output_grain_role's
# evidence is recorded manually (see _record_output_grain_evidence) so
# its own `detail` can carry the real, path-aware numbers
# ComparisonRevealScene's own automatic per-option evidence recording has
# no hook for. The 3 labels themselves are static regardless of which
# group key was actually picked (only which one is the honest answer
# varies, at grading time - not this tuple's own content), so this is a
# plain module-level constant like the other 3 reveals' own interpret-
# option lists, not a function.

GRAIN_CHECK_INTERPRET_OPTIONS = (
    InterpretOption("one_customer", "lesson.l12.grain_check.option.one_customer"),
    InterpretOption("one_store", "lesson.l12.grain_check.option.one_store"),
    InterpretOption("one_date", "lesson.l12.grain_check.option.one_date"),
)


def _grouped_row_count(group_by_column: str) -> int:
    if group_by_column == "store_id":
        return len(STORE_CUSTOMERS)
    if group_by_column == "customer_id":
        return network_distinct_customers()
    if group_by_column == "order_date":
        return distinct_dates()
    raise ValueError(group_by_column)


# --- Business roll-up methods (shared by the prior pass, the revision, and
# Final Decision - see LessonTwelveResult's own docstring for why the prior
# and revision stay genuinely separate from Final Decision's own fields) --

NETWORK_CUSTOMER_METHOD_FIELD = BriefField(
    key="network_customer_method",
    prompt_key="lesson.l12.rollup.network_customer_method.prompt",
    options=(
        BriefOption("sum_per_store", "lesson.l12.rollup.network_customer_method.option.sum_per_store"),
        BriefOption("distinct_network_wide", "lesson.l12.rollup.network_customer_method.option.distinct_network_wide"),
    ),
)
NETWORK_AOV_METHOD_FIELD = BriefField(
    key="network_aov_method",
    prompt_key="lesson.l12.rollup.network_aov_method.prompt",
    options=(
        BriefOption("mean_of_store_aovs", "lesson.l12.rollup.network_aov_method.option.mean_of_store_aovs"),
        BriefOption("order_level_or_weighted", "lesson.l12.rollup.network_aov_method.option.order_level_or_weighted"),
    ),
)
NETWORK_ROLLUP_FIELDS: tuple[BriefField, ...] = (NETWORK_CUSTOMER_METHOD_FIELD, NETWORK_AOV_METHOD_FIELD)

# --- Roll-up reveals -------------------------------------------------------

CUSTOMER_ROLLUP_INTERPRET_OPTIONS = (
    InterpretOption(
        "sum_is_still_fine",
        "lesson.l12.customer_rollup.interpret.option.sum_is_still_fine",
        evidence_key="lesson.l12.evidence.customer_rollup",
    ),
    InterpretOption(
        "overlap_breaks_the_sum",
        "lesson.l12.customer_rollup.interpret.option.overlap_breaks_the_sum",
        evidence_key="lesson.l12.evidence.customer_rollup",
    ),
    InterpretOption(
        "need_more_data_still",
        "lesson.l12.customer_rollup.interpret.option.need_more_data_still",
        evidence_key="lesson.l12.evidence.customer_rollup",
    ),
)
AOV_ROLLUP_INTERPRET_OPTIONS = (
    InterpretOption(
        "unweighted_mean_is_fine",
        "lesson.l12.aov_rollup.interpret.option.unweighted_mean_is_fine",
        evidence_key="lesson.l12.evidence.aov_rollup",
    ),
    InterpretOption(
        "unweighted_mean_weights_stores_not_orders",
        "lesson.l12.aov_rollup.interpret.option.unweighted_mean_weights_stores_not_orders",
        evidence_key="lesson.l12.evidence.aov_rollup",
    ),
    InterpretOption(
        "need_more_data_still",
        "lesson.l12.aov_rollup.interpret.option.need_more_data_still",
        evidence_key="lesson.l12.evidence.aov_rollup",
    ),
)
CUSTOMER_COUNT_INTERPRET_OPTIONS = (
    InterpretOption(
        "row_count_is_fine",
        "lesson.l12.customer_count.interpret.option.row_count_is_fine",
        evidence_key="lesson.l12.evidence.repeat_customer",
    ),
    InterpretOption(
        "repeats_mean_fewer_real_customers",
        "lesson.l12.customer_count.interpret.option.repeats_mean_fewer_real_customers",
        evidence_key="lesson.l12.evidence.repeat_customer",
    ),
    InterpretOption(
        "need_more_data_still",
        "lesson.l12.customer_count.interpret.option.need_more_data_still",
        evidence_key="lesson.l12.evidence.repeat_customer",
    ),
)

# --- Final Decision ("Aggregation Brief") ---------------------------------

RAW_OBSERVATION_UNIT_FIELD = BriefField(
    key="raw_observation_unit",
    prompt_key="lesson.l12.decision.raw_observation_unit.prompt",
    options=(
        BriefOption("customer", "lesson.l12.decision.observation_unit.option.customer"),
        BriefOption("order", "lesson.l12.decision.observation_unit.option.order"),
        BriefOption("store", "lesson.l12.decision.observation_unit.option.store"),
    ),
)
GROUPED_OUTPUT_GRAIN_FIELD = BriefField(
    key="grouped_output_grain",
    prompt_key="lesson.l12.decision.grouped_output_grain.prompt",
    options=(
        BriefOption("order", "lesson.l12.decision.observation_unit.option.order"),
        BriefOption("store", "lesson.l12.decision.observation_unit.option.store"),
        BriefOption("customer", "lesson.l12.decision.observation_unit.option.customer"),
    ),
)
SAFE_ROLLUP_METRICS_FIELD = MultiChoiceField(
    key="safe_rollup_metrics",
    prompt_key="lesson.l12.decision.safe_rollup_metrics.prompt",
    options=(
        BriefOption("unique_customers", "lesson.l12.decision.safe_rollup_metrics.option.unique_customers"),
        BriefOption("orders", "lesson.l12.decision.safe_rollup_metrics.option.orders"),
        BriefOption("revenue", "lesson.l12.decision.safe_rollup_metrics.option.revenue"),
        BriefOption("aov", "lesson.l12.decision.safe_rollup_metrics.option.aov"),
    ),
    min_count=2,
    max_count=2,
)
DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l12.decision.evidence.prompt",
    min_count=2,
    max_count=4,
)
DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    RAW_OBSERVATION_UNIT_FIELD,
    GROUPED_OUTPUT_GRAIN_FIELD,
    SAFE_ROLLUP_METRICS_FIELD,
    NETWORK_CUSTOMER_METHOD_FIELD,
    NETWORK_AOV_METHOD_FIELD,
)

# --- Optional mastery -------------------------------------------------

MASTERY_SUPPORTING_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l12.mastery.field.supporting_evidence.prompt",
    options=(
        BriefOption("same_style_averages", "lesson.l12.mastery.option.supporting_evidence.same_style_averages"),
        BriefOption("channel_volumes_differ", "lesson.l12.mastery.option.supporting_evidence.channel_volumes_differ"),
        BriefOption("channel_names_differ", "lesson.l12.mastery.option.supporting_evidence.channel_names_differ"),
        BriefOption("customers_overlap_channels", "lesson.l12.mastery.option.supporting_evidence.customers_overlap_channels"),
    ),
    min_count=1,
    max_count=2,
)
MASTERY_PURCHASER_SUM_FIELD = BriefField(
    key="mastery_purchaser_sum",
    prompt_key="lesson.l12.mastery.field.purchaser_sum.prompt",
    options=(
        BriefOption("sum_is_fine", "lesson.l12.mastery.option.purchaser_sum.sum_is_fine"),
        BriefOption("cant_sum_overlap", "lesson.l12.mastery.option.purchaser_sum.cant_sum_overlap"),
        BriefOption("cant_tell", "lesson.l12.mastery.option.purchaser_sum.cant_tell"),
    ),
)
MASTERY_AVG_VALUE_METHOD_FIELD = BriefField(
    key="mastery_avg_value_method",
    prompt_key="lesson.l12.mastery.field.avg_value_method.prompt",
    options=(
        BriefOption("mean_of_channel_averages", "lesson.l12.mastery.option.avg_value_method.mean_of_channel_averages"),
        BriefOption("raw_or_weighted", "lesson.l12.mastery.option.avg_value_method.raw_or_weighted"),
        BriefOption("cant_tell", "lesson.l12.mastery.option.avg_value_method.cant_tell"),
    ),
)


def build_lesson_twelve_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 12's real investigation: a 90-row NovaMart order-
    level feed, a real store-summary pipeline the student composes
    themselves (AggregationBuilderScene), and a real network roll-up
    trap. LessonContext is threaded through every analytical stage
    exactly like L06-L11.

    The store-summary pipeline (group key + 4 metric slots) is scored on
    its own FINAL state - after the stage-5 revision opportunity, never
    the cold first pass. The two network roll-up methods get their own,
    separate prior-pass/revision/Final-Decision chain (rollup_prior ->
    rollup_revised_picks -> decision), mirroring L11's own corrected
    business_asks_revised_picks pattern: the stage-10 revision's own real
    picks are stored, never discarded, and Final Decision is never a
    substitute for it."""
    collected: dict = {}
    context = LessonContext()

    dataset = generate_orders()

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    def _group_by_column(group_by_key: str) -> str:
        return next(o.column for o in GROUP_BY_OPTIONS if o.key == group_by_key)

    def _record_output_grain_evidence(group_by_key: str) -> None:
        column = _group_by_column(group_by_key)
        grouped_count = _grouped_row_count(column)
        detail = f"90 -> {grouped_count} ({column})"
        action = context.record_action(
            label_key="lesson.l12.evidence.output_grain",
            python_code=f"orders.groupby('{column}').ngroups",
            key="output_grain_role",
        )
        context.record_evidence(label_key="lesson.l12.evidence.output_grain", source_action=action, key="output_grain_role", detail=detail)

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    # --- Store summary build ---

    def store_summary_build(advance):
        def on_complete(group_by_key, metric_choices):
            collected["group_by"] = group_by_key
            collected["metric_choices"] = metric_choices
            _sync_context_into_collected()
            advance()

        return AggregationBuilderScene(
            app,
            "lesson.l12.builder.title",
            dataset,
            GROUP_BY_OPTIONS,
            METRIC_SLOTS,
            on_complete,
            context,
            guided=True,
            output_variable_name="store_summary",
        )

    # --- Output-grain check (path-aware) ---

    def output_grain_check(advance):
        group_by_key = collected["group_by"]
        column = _group_by_column(group_by_key)
        grouped_count = _grouped_row_count(column)

        def on_complete(_interpretation):
            _record_output_grain_evidence(group_by_key)
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l12.grain_check.title",
            narrative_keys=("dialogue.l12_grain_check.line1",),
            comparisons=(
                ComparisonValue("lesson.l12.grain_check.raw_label", float(len(dataset.frame)), value_format=lambda v: f"{v:,.0f}"),
                ComparisonValue("lesson.l12.grain_check.grouped_label", float(grouped_count), value_format=lambda v: f"{v:,.0f}"),
            ),
            interpret_prompt_key="lesson.l12.grain_check.interpret_prompt",
            interpret_options=GRAIN_CHECK_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Customer-count reveal (S02) ---

    def customer_count_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l12.customer_count.title",
            narrative_keys=("dialogue.l12_customer_count.line1", "dialogue.l12_customer_count.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l12.customer_count.rows_label",
                    float(store_order_count("S02")),
                    python_code="orders.loc[orders['store_id'] == 'S02', 'customer_id'].size",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l12.customer_count.distinct_label",
                    float(store_distinct_customers("S02")),
                    python_code="orders.loc[orders['store_id'] == 'S02', 'customer_id'].nunique()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
            ),
            interpret_prompt_key="lesson.l12.customer_count.interpret_prompt",
            interpret_options=CUSTOMER_COUNT_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Store-summary revision offer (full pipeline, every fact changeable)

    def store_summary_revision_offer(advance):
        prior_group_by = collected["group_by"]

        def build_revision_task(on_task_complete):
            def on_revise_complete(group_by_key, metric_choices):
                collected["group_by"] = group_by_key
                collected["metric_choices"] = metric_choices
                if group_by_key != prior_group_by:
                    _record_output_grain_evidence(group_by_key)
                on_task_complete(None)

            return AggregationBuilderScene(
                app,
                "lesson.l12.builder.title",
                dataset,
                GROUP_BY_OPTIONS,
                METRIC_SLOTS,
                on_revise_complete,
                context,
                initial_group_by=collected["group_by"],
                initial_choices=dict(collected["metric_choices"]),
                guided=True,
                output_variable_name="store_summary",
            )

        def on_offer_complete(_engaged, _result):
            _sync_context_into_collected()
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l12.revision_offer.title",
            line_keys=("lesson.l12.revision_offer.line1",),
            engage_label_key="lesson.l12.revision_offer.engage",
            skip_label_key="lesson.l12.revision_offer.skip",
        )

    # --- Finance's roll-up ask ---

    def finance_rollup_ask(advance):
        return DialogueScene(app, FINANCE_ROLLUP_ASK_DIALOGUE, on_complete=advance)

    # --- Network roll-up attempt (prior, unscored) ---

    def network_rollup_attempt(advance):
        def on_complete(brief):
            collected["rollup_prior"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l12.rollup.title", NETWORK_ROLLUP_FIELDS, on_complete, guided=True)

    # --- Customer roll-up reveal ---

    def customer_rollup_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l12.customer_rollup.title",
            narrative_keys=("dialogue.l12_customer_rollup.line1", "dialogue.l12_customer_rollup.line2"),
            comparisons=(
                ComparisonValue("lesson.l12.customer_rollup.cross_store_label", float(len(cross_store_customers())), value_format=lambda v: f"{v:,.0f}"),
                ComparisonValue(
                    "lesson.l12.customer_rollup.sum_label",
                    float(sum_of_store_distinct_customers()),
                    python_code="store_summary['unique_customers'].sum()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l12.customer_rollup.network_label",
                    float(network_distinct_customers()),
                    python_code="orders['customer_id'].nunique()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
            ),
            interpret_prompt_key="lesson.l12.customer_rollup.interpret_prompt",
            interpret_options=CUSTOMER_ROLLUP_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- AOV roll-up reveal ---

    def aov_rollup_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l12.aov_rollup.title",
            narrative_keys=("dialogue.l12_aov_rollup.line1", "dialogue.l12_aov_rollup.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l12.aov_rollup.naive_label",
                    naive_mean_of_store_aovs(),
                    python_code="store_summary['aov'].mean()",
                    value_format=lambda v: f"${v:,.2f}",
                ),
                ComparisonValue(
                    "lesson.l12.aov_rollup.network_label",
                    network_aov(),
                    python_code="orders['revenue'].mean()",
                    value_format=lambda v: f"${v:,.2f}",
                ),
                ComparisonValue(
                    "lesson.l12.aov_rollup.weighted_label",
                    weighted_aov(),
                    python_code="import numpy as np\nnp.average(store_summary['aov'], weights=store_summary['orders'])",
                    value_format=lambda v: f"${v:,.2f}",
                ),
            ),
            interpret_prompt_key="lesson.l12.aov_rollup.interpret_prompt",
            interpret_options=AOV_ROLLUP_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Roll-up revision offer (practice, but the real picks are kept) ---

    def rollup_revision_offer(advance):
        def build_revision_task(on_task_complete):
            def on_brief_complete(brief):
                collected["rollup_revised_picks"] = dict(brief)
                on_task_complete(None)

            return BriefBuilderScene(app, "lesson.l12.rollup.title", NETWORK_ROLLUP_FIELDS, on_brief_complete, guided=True)

        def on_offer_complete(_engaged, _result):
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l12.rollup_revision_offer.title",
            line_keys=("lesson.l12.rollup_revision_offer.line1",),
            engage_label_key="lesson.l12.rollup_revision_offer.engage",
            skip_label_key="lesson.l12.rollup_revision_offer.skip",
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
            "lesson.l12.decision_title",
            steps=(
                RAW_OBSERVATION_UNIT_FIELD,
                GROUPED_OUTPUT_GRAIN_FIELD,
                SAFE_ROLLUP_METRICS_FIELD,
                NETWORK_CUSTOMER_METHOD_FIELD,
                NETWORK_AOV_METHOD_FIELD,
                DECISION_EVIDENCE_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            def build_select():
                return BriefBuilderScene(
                    app,
                    "lesson.l12.mastery.title",
                    (MASTERY_SUPPORTING_EVIDENCE_FIELD, MASTERY_PURCHASER_SUM_FIELD, MASTERY_AVG_VALUE_METHOD_FIELD),
                    on_task_complete,
                    guided=False,
                )

            return build_select()

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l12.mastery.title",
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

    def _build_result() -> LessonTwelveResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwelveResult(
            group_by=collected.get("group_by"),
            metric_choices=collected.get("metric_choices", {}),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            rollup_prior=collected.get("rollup_prior", {}),
            rollup_revised_picks=collected.get("rollup_revised_picks"),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_12.number, 0)
        evaluation = score_lesson_twelve(result, LESSON_12, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        store_summary_build,
        output_grain_check,
        customer_count_reveal,
        store_summary_revision_offer,
        finance_rollup_ask,
        network_rollup_attempt,
        customer_rollup_reveal,
        aov_rollup_reveal,
        rollup_revision_offer,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=12,
        collected=collected,
        definition=LESSON_12,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
