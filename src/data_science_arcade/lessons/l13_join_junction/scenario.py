from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l13_join_junction.definition import LESSON_13
from data_science_arcade.lessons.l13_join_junction.orders import (
    ACTIVE_PROMOTIONS_DISTINCT_CUSTOMERS,
    ACTIVE_PROMOTIONS_ROWS,
    CONCRETE_EXAMPLE_CUSTOMER_ID,
    JOIN1_INNER_ROW_COUNT,
    JOIN1_LEFT_ROW_COUNT,
    JOIN1_OUTER_ROW_COUNT,
    ORDERS_DISTINCT_CUSTOMER_IDS,
    TOTAL_ORDERS,
    generate_active_promotions,
    generate_customers,
    generate_orders,
)
from data_science_arcade.lessons.l13_join_junction.scoring import CRITICAL_EVIDENCE_KEYS, LessonThirteenResult, score_lesson_thirteen
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.join_builder_scene import JoinBuilderScene, JoinTypeOption
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l13_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l13_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_briefing.line3"),
    )
)
FINANCE_PROMOTIONS_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l13_finance_promotions.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l13_finance_promotions.line2"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l13_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_debrief.line3"),
    )
)
MASTERY_DIALOGUE_KEYS = ("dialogue.l13_mastery.line1", "dialogue.l13_mastery.line2", "dialogue.l13_mastery.line3")

# --- Join 1 (orders <-> customers) -----------------------------------------
#
# A clean one-to-many join from customers' own unique key - nothing
# multiplies here, only rows get kept or dropped. No gratuitous right
# join: only inner/left/outer are ever offered as real options.

JOIN1_OPTIONS = (
    JoinTypeOption("inner", "lesson.l13.builder.join1.option.inner", "inner"),
    JoinTypeOption("left", "lesson.l13.builder.join1.option.left", "left"),
    JoinTypeOption("outer", "lesson.l13.builder.join1.option.outer", "outer"),
)
RAW_PROMO_OPTIONS = (JoinTypeOption("left_raw", "lesson.l13.builder.raw_promo.option.left", "left"),)
VALIDATE_PROMO_OPTIONS = (JoinTypeOption("left_validated", "lesson.l13.builder.validate_promo.option.left", "left"),)
REPAIR_OPTIONS = (JoinTypeOption("left_repaired", "lesson.l13.builder.repair.option.left", "left"),)

_JOIN1_ROW_COUNT_BY_HOW: dict[str, int] = {"inner": JOIN1_INNER_ROW_COUNT, "left": JOIN1_LEFT_ROW_COUNT, "outer": JOIN1_OUTER_ROW_COUNT}

# --- Reveal interpret options ------------------------------------------

ORDERS_KEY_INTERPRET_OPTIONS = (
    InterpretOption(
        "customer_id_repeats_in_orders",
        "lesson.l13.orders_key.interpret.option.repeats",
        evidence_key="lesson.l13.evidence.orders_key",
    ),
    InterpretOption(
        "data_is_broken", "lesson.l13.orders_key.interpret.option.broken", evidence_key="lesson.l13.evidence.orders_key"
    ),
    InterpretOption(
        "need_more_data_still", "lesson.l13.orders_key.interpret.option.need_more_data", evidence_key="lesson.l13.evidence.orders_key"
    ),
)

# join1_consequence has no evidence_key on its own options - its evidence
# is recorded manually (see _record_join1_consequence_evidence) so its
# own `detail` can carry the real, path-aware count the stage-5 revision
# may later update, exactly mirroring L12's own output_grain_role.
JOIN1_CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption("every_real_order_kept", "lesson.l13.join1_consequence.interpret.option.every_order_kept"),
    InterpretOption("some_real_orders_dropped", "lesson.l13.join1_consequence.interpret.option.orders_dropped"),
    InterpretOption("extra_non_order_rows_appeared", "lesson.l13.join1_consequence.interpret.option.extra_rows"),
)

PROMOTIONS_KEY_INTERPRET_OPTIONS = (
    InterpretOption(
        "promotions_key_is_one_to_many",
        "lesson.l13.promotions_key.interpret.option.one_to_many",
        evidence_key="lesson.l13.evidence.promotions_key",
    ),
    InterpretOption(
        "each_customer_has_one_promo",
        "lesson.l13.promotions_key.interpret.option.one_per_customer",
        evidence_key="lesson.l13.evidence.promotions_key",
    ),
    InterpretOption(
        "need_more_data_still", "lesson.l13.promotions_key.interpret.option.need_more_data", evidence_key="lesson.l13.evidence.promotions_key"
    ),
)

FAN_OUT_INTERPRET_OPTIONS = (
    InterpretOption(
        "key_matched_more_than_one_row",
        "lesson.l13.fan_out.interpret.option.key_matched_more_than_one_row",
        evidence_key="lesson.l13.evidence.fan_out",
    ),
    InterpretOption(
        "duplicate_row_should_be_removed", "lesson.l13.fan_out.interpret.option.duplicate", evidence_key="lesson.l13.evidence.fan_out"
    ),
    InterpretOption(
        "data_entry_error", "lesson.l13.fan_out.interpret.option.data_entry_error", evidence_key="lesson.l13.evidence.fan_out"
    ),
)

MULTI_CHECK_INTERPRET_OPTIONS = (
    InterpretOption(
        "row_count_alone_insufficient",
        "lesson.l13.multi_check.interpret.option.insufficient",
        evidence_key="lesson.l13.evidence.multi_check_validation",
    ),
    InterpretOption(
        "row_count_alone_sufficient",
        "lesson.l13.multi_check.interpret.option.sufficient",
        evidence_key="lesson.l13.evidence.multi_check_validation",
    ),
    InterpretOption(
        "need_more_data_still",
        "lesson.l13.multi_check.interpret.option.need_more_data",
        evidence_key="lesson.l13.evidence.multi_check_validation",
    ),
)

# --- Final Decision ("Join Brief") ----------------------------------------

ORDERS_JOIN_TYPE_FIELD = BriefField(
    key="orders_join_type",
    prompt_key="lesson.l13.decision.orders_join_type.prompt",
    options=(
        BriefOption("left", "lesson.l13.decision.orders_join_type.option.left"),
        BriefOption("inner", "lesson.l13.decision.orders_join_type.option.inner"),
        BriefOption("outer", "lesson.l13.decision.orders_join_type.option.outer"),
    ),
)
ORDERS_JOIN_ROW_COUNT_FIELD = BriefField(
    key="orders_join_row_count",
    prompt_key="lesson.l13.decision.orders_join_row_count.prompt",
    options=(
        BriefOption("120", "lesson.l13.decision.row_count.option.120"),
        BriefOption("108", "lesson.l13.decision.row_count.option.108"),
        BriefOption("140", "lesson.l13.decision.row_count.option.140"),
    ),
)
PROMOTIONS_KEY_CARDINALITY_FIELD = BriefField(
    key="promotions_key_cardinality",
    prompt_key="lesson.l13.decision.promotions_key_cardinality.prompt",
    options=(
        BriefOption("many_to_one_from_promotions", "lesson.l13.decision.promotions_key_cardinality.option.many_to_one"),
        BriefOption("one_to_one", "lesson.l13.decision.promotions_key_cardinality.option.one_to_one"),
        BriefOption("cant_tell", "lesson.l13.decision.promotions_key_cardinality.option.cant_tell"),
    ),
)
PROMOTIONS_NEEDS_PREAGGREGATION_FIELD = BriefField(
    key="promotions_join_needs_preaggregation",
    prompt_key="lesson.l13.decision.needs_preaggregation.prompt",
    options=(
        BriefOption("preaggregate_first", "lesson.l13.decision.needs_preaggregation.option.preaggregate_first"),
        BriefOption("join_raw_directly", "lesson.l13.decision.needs_preaggregation.option.join_raw_directly"),
    ),
)
PROMOTIONS_REPAIRED_ROW_COUNT_FIELD = BriefField(
    key="promotions_row_count_after_repair",
    prompt_key="lesson.l13.decision.repaired_row_count.prompt",
    options=(
        BriefOption("120", "lesson.l13.decision.row_count.option.120"),
        BriefOption("147", "lesson.l13.decision.row_count.option.147"),
        BriefOption("100", "lesson.l13.decision.row_count.option.100"),
    ),
)
VALIDATION_SUFFICIENCY_FIELD = BriefField(
    key="validation_sufficiency",
    prompt_key="lesson.l13.decision.validation_sufficiency.prompt",
    options=(
        BriefOption("no_needs_multiple_checks", "lesson.l13.decision.validation_sufficiency.option.no"),
        BriefOption("yes_row_count_enough", "lesson.l13.decision.validation_sufficiency.option.yes"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l13.decision.evidence.prompt", min_count=3, max_count=5)
DECISION_FIELDS: tuple[BriefField, ...] = (
    ORDERS_JOIN_TYPE_FIELD,
    ORDERS_JOIN_ROW_COUNT_FIELD,
    PROMOTIONS_KEY_CARDINALITY_FIELD,
    PROMOTIONS_NEEDS_PREAGGREGATION_FIELD,
    PROMOTIONS_REPAIRED_ROW_COUNT_FIELD,
    VALIDATION_SUFFICIENCY_FIELD,
)

# --- Optional mastery: the inverted case (shipments/checkpoint_scans) -----

MASTERY_SUPPORTING_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l13.mastery.field.supporting_evidence.prompt",
    options=(
        BriefOption(
            "shipment_has_multiple_real_checkpoints", "lesson.l13.mastery.option.supporting_evidence.multiple_real_checkpoints"
        ),
        BriefOption("row_count_grew", "lesson.l13.mastery.option.supporting_evidence.row_count_grew"),
        BriefOption("shipment_ids_are_unique", "lesson.l13.mastery.option.supporting_evidence.shipment_ids_are_unique"),
        BriefOption("checkpoint_names_repeat", "lesson.l13.mastery.option.supporting_evidence.checkpoint_names_repeat"),
    ),
    min_count=1,
    max_count=2,
)
MASTERY_ROW_GROWTH_JUDGMENT_FIELD = BriefField(
    key="mastery_row_growth_judgment",
    prompt_key="lesson.l13.mastery.field.row_growth_judgment.prompt",
    options=(
        BriefOption("expected_real_grain", "lesson.l13.mastery.option.row_growth_judgment.expected_real_grain"),
        BriefOption("needs_repair_like_promotions", "lesson.l13.mastery.option.row_growth_judgment.needs_repair"),
        BriefOption("cant_tell", "lesson.l13.mastery.option.row_growth_judgment.cant_tell"),
    ),
)


def build_lesson_thirteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 13's real investigation: a 120-row NovaMart order
    feed joined first to customers (a clean one-to-many join, testing
    only the keep/drop question) and then to active_promotions (a real
    one-to-many key from the promotions side, testing only the multiply
    question) - two genuinely separate join-arithmetic mechanisms, never
    entangled in the same stage. LessonContext is threaded through every
    analytical stage exactly like L06-L12.

    Join 1's own final state (after the stage-5 revision opportunity) is
    tracked for trajectory feedback, but only the Final Decision's own
    `orders_join_type` field is the real scored METHOD fact - see
    LessonThirteenResult's own docstring for why."""
    collected: dict = {}
    context = LessonContext()

    customers = generate_customers()
    orders = generate_orders()
    active_promotions = generate_active_promotions()

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    def _record_join1_consequence_evidence(how: str) -> None:
        count = _JOIN1_ROW_COUNT_BY_HOW[how]
        detail = f"{count} rows ({how})"
        action = context.record_action(label_key="lesson.l13.evidence.join1_consequence", key="join1_consequence_role")
        context.record_evidence(
            label_key="lesson.l13.evidence.join1_consequence", source_action=action, key="join1_consequence_role", detail=detail
        )

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    # --- Orders-side key-cardinality inspection ---

    def orders_key_inspection(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.orders_key.title",
            narrative_keys=("dialogue.l13_orders_key.line1", "dialogue.l13_orders_key.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l13.orders_key.rows_label",
                    float(TOTAL_ORDERS),
                    python_code="orders['customer_id'].value_counts()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l13.orders_key.distinct_label",
                    float(ORDERS_DISTINCT_CUSTOMER_IDS),
                    python_code="orders['customer_id'].nunique()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
            ),
            interpret_prompt_key="lesson.l13.orders_key.interpret_prompt",
            interpret_options=ORDERS_KEY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Join 1 attempt ---

    def join1_attempt(advance):
        def on_complete(choice, _succeeded):
            collected["join1_first_choice"] = choice
            collected["join1_choice"] = choice
            _sync_context_into_collected()
            advance()

        return JoinBuilderScene(
            app,
            "lesson.l13.builder.join1.title",
            orders,
            customers,
            "customer_id",
            JOIN1_OPTIONS,
            on_complete,
            context,
            output_variable_name="join1_result",
            mirror_action_key="join1_pipeline",
            hint_key="lesson.l13.builder.join1.hint",
            guided=True,
        )

    # --- Join 1 consequence reveal (path-aware) ---

    def join1_consequence_reveal(advance):
        how = collected["join1_choice"]
        count = _JOIN1_ROW_COUNT_BY_HOW[how]

        def on_complete(_interpretation):
            _record_join1_consequence_evidence(how)
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.join1_consequence.title",
            narrative_keys=("dialogue.l13_join1_consequence.line1",),
            comparisons=(
                ComparisonValue("lesson.l13.join1_consequence.your_pick_label", float(count), value_format=lambda v: f"{v:,.0f}"),
                ComparisonValue(
                    "lesson.l13.join1_consequence.total_real_orders_label", float(TOTAL_ORDERS), value_format=lambda v: f"{v:,.0f}"
                ),
            ),
            interpret_prompt_key="lesson.l13.join1_consequence.interpret_prompt",
            interpret_options=JOIN1_CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Join 1 revision offer ---

    def join1_revision_offer(advance):
        prior_choice = collected["join1_choice"]

        def build_revision_task(on_task_complete):
            def on_revise_complete(choice, _succeeded):
                collected["join1_choice"] = choice
                if choice != prior_choice:
                    _record_join1_consequence_evidence(choice)
                on_task_complete(None)

            return JoinBuilderScene(
                app,
                "lesson.l13.builder.join1.title",
                orders,
                customers,
                "customer_id",
                JOIN1_OPTIONS,
                on_revise_complete,
                context,
                initial_choice=collected["join1_choice"],
                output_variable_name="join1_result",
                mirror_action_key="join1_pipeline",
                hint_key="lesson.l13.builder.join1.hint",
                guided=True,
            )

        def on_offer_complete(_engaged, _result):
            _sync_context_into_collected()
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l13.revision_offer.title",
            line_keys=("lesson.l13.revision_offer.line1",),
            engage_label_key="lesson.l13.revision_offer.engage",
            skip_label_key="lesson.l13.revision_offer.skip",
        )

    # --- Finance's promotions ask ---

    def finance_promotions_ask(advance):
        return DialogueScene(app, FINANCE_PROMOTIONS_DIALOGUE, on_complete=advance)

    # --- Promotions-side key-cardinality inspection (mandatory, computed) ---

    def promotions_key_inspection(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.promotions_key.title",
            narrative_keys=("dialogue.l13_promotions_key.line1", "dialogue.l13_promotions_key.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l13.promotions_key.rows_label",
                    float(ACTIVE_PROMOTIONS_ROWS),
                    python_code="active_promotions['customer_id'].value_counts()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l13.promotions_key.distinct_label",
                    float(ACTIVE_PROMOTIONS_DISTINCT_CUSTOMERS),
                    python_code="active_promotions['customer_id'].nunique()",
                    value_format=lambda v: f"{v:,.0f}",
                ),
            ),
            interpret_prompt_key="lesson.l13.promotions_key.interpret_prompt",
            interpret_options=PROMOTIONS_KEY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Raw promotions join attempt ---

    def raw_promotions_attempt(advance):
        def on_complete(_choice, _succeeded):
            _sync_context_into_collected()
            advance()

        return JoinBuilderScene(
            app,
            "lesson.l13.builder.raw_promo.title",
            orders,
            active_promotions,
            "customer_id",
            RAW_PROMO_OPTIONS,
            on_complete,
            context,
            output_variable_name="raw_promo_join",
            mirror_action_key="raw_promo_pipeline",
            guided=True,
        )

    # --- Concrete fan-out example ---

    def concrete_fan_out_example(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.fan_out.title",
            narrative_keys=("dialogue.l13_fan_out.line1", "dialogue.l13_fan_out.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l13.fan_out.before_label",
                    1.0,
                    python_code=f"orders.loc[orders['customer_id'] == '{CONCRETE_EXAMPLE_CUSTOMER_ID}']",
                    value_format=lambda v: f"{v:,.0f} row",
                ),
                ComparisonValue(
                    "lesson.l13.fan_out.after_label",
                    3.0,
                    python_code=f"raw_promo_join.loc[raw_promo_join['customer_id'] == '{CONCRETE_EXAMPLE_CUSTOMER_ID}']",
                    value_format=lambda v: f"{v:,.0f} rows",
                ),
            ),
            interpret_prompt_key="lesson.l13.fan_out.interpret_prompt",
            interpret_options=FAN_OUT_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- validate= reveal ---

    def validate_reveal(advance):
        def on_complete(_choice, _succeeded):
            _sync_context_into_collected()
            advance()

        return JoinBuilderScene(
            app,
            "lesson.l13.builder.validate_promo.title",
            orders,
            active_promotions,
            "customer_id",
            VALIDATE_PROMO_OPTIONS,
            on_complete,
            context,
            validate="many_to_one",
            output_variable_name="_probe",
            mirror_action_key="validate_probe_pipeline",
            guided=True,
        )

    # --- Repair: pre-aggregate then join ---

    def repair_attempt(advance):
        promo_per_customer_frame = active_promotions.frame.groupby("customer_id", as_index=False).agg(
            active_promotion_count=("promotion_code", "size")
        )
        promo_per_customer_schema = Schema(
            columns=(ColumnSchema("customer_id", "object"), ColumnSchema("active_promotion_count", "int64"))
        )
        promo_per_customer = Dataset(name="promo_per_customer", frame=promo_per_customer_frame, schema=promo_per_customer_schema)
        context.record_action(
            label_key="lesson.l13.repair.preaggregate_title",
            python_code=(
                "promo_per_customer = active_promotions.groupby('customer_id', as_index=False).agg(\n"
                "    active_promotion_count=('promotion_code', 'size'),\n"
                ")"
            ),
            key="preaggregate_pipeline",
        )

        def on_complete(_choice, _succeeded):
            _sync_context_into_collected()
            advance()

        return JoinBuilderScene(
            app,
            "lesson.l13.builder.repair.title",
            orders,
            promo_per_customer,
            "customer_id",
            REPAIR_OPTIONS,
            on_complete,
            context,
            validate="many_to_one",
            output_variable_name="final",
            mirror_action_key="repair_pipeline",
            guided=True,
        )

    # --- Multi-check validation reveal ---

    def multi_check_validation_reveal(advance):
        promo_per_customer_frame = active_promotions.frame.groupby("customer_id", as_index=False).agg(
            active_promotion_count=("promotion_code", "size")
        )
        corrected = orders.frame.merge(promo_per_customer_frame, on="customer_id", how="left", indicator=True)
        revenue_before = float(orders.frame["revenue"].sum())
        revenue_after = float(corrected["revenue"].sum())
        unmatched_orders = int((corrected["_merge"] == "left_only").sum())

        def on_complete(_interpretation):
            action = context.record_action(label_key="lesson.l13.evidence.multi_check_validation", key="multi_check_validation_role")
            context.record_evidence(
                label_key="lesson.l13.evidence.multi_check_validation",
                source_action=action,
                key="multi_check_validation_role",
                detail=f"key unique: True, revenue ${revenue_before:,.2f} -> ${revenue_after:,.2f}, unmatched: {unmatched_orders}",
            )
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.multi_check.title",
            narrative_keys=("dialogue.l13_multi_check.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l13.multi_check.key_unique_label",
                    1.0,
                    python_code="promo_per_customer['customer_id'].is_unique",
                    value_format=lambda v: "Yes" if v == 1.0 else "No",
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.revenue_before_label", revenue_before, value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.revenue_after_label", revenue_after, value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.unmatched_label", float(unmatched_orders), value_format=lambda v: f"{v:,.0f}"
                ),
            ),
            interpret_prompt_key="lesson.l13.multi_check.interpret_prompt",
            interpret_options=MULTI_CHECK_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
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
            "lesson.l13.decision_title",
            steps=(
                ORDERS_JOIN_TYPE_FIELD,
                ORDERS_JOIN_ROW_COUNT_FIELD,
                PROMOTIONS_KEY_CARDINALITY_FIELD,
                PROMOTIONS_NEEDS_PREAGGREGATION_FIELD,
                PROMOTIONS_REPAIRED_ROW_COUNT_FIELD,
                VALIDATION_SUFFICIENCY_FIELD,
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
                "lesson.l13.mastery.title",
                (MASTERY_SUPPORTING_EVIDENCE_FIELD, MASTERY_ROW_GROWTH_JUDGMENT_FIELD),
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
            title_key="lesson.l13.mastery.title",
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

    def _build_result() -> LessonThirteenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonThirteenResult(
            join1_first_choice=collected.get("join1_first_choice"),
            join1_choice=collected.get("join1_choice"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_13.number, 0)
        evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        orders_key_inspection,
        join1_attempt,
        join1_consequence_reveal,
        join1_revision_offer,
        finance_promotions_ask,
        promotions_key_inspection,
        raw_promotions_attempt,
        concrete_fan_out_example,
        validate_reveal,
        repair_attempt,
        multi_check_validation_reveal,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=13,
        collected=collected,
        definition=LESSON_13,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
