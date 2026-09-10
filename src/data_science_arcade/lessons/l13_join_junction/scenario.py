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

_PROMO_PER_CUSTOMER_SCHEMA = Schema(columns=(ColumnSchema("customer_id", "object"), ColumnSchema("active_promotion_count", "int64")))


def _promo_per_customer_dataset(active_promotions: Dataset) -> Dataset:
    frame = active_promotions.frame.groupby("customer_id", as_index=False).agg(active_promotion_count=("promotion_code", "size"))
    return Dataset(name="promo_per_customer", frame=frame, schema=_PROMO_PER_CUSTOMER_SCHEMA)


def _deduped_promotions_dataset(active_promotions: Dataset) -> Dataset:
    frame = active_promotions.frame.drop_duplicates(subset="customer_id", keep="first")
    return Dataset(name="deduped_promotions", frame=frame, schema=active_promotions.schema)


# --- Join 1 (orders <-> customers) -----------------------------------------
#
# A clean one-to-many join from customers' own unique key - nothing
# multiplies here, only rows get kept or dropped. No gratuitous right
# join: only inner/left/outer are ever offered as real options.
# validate="many_to_one" is real here too, not reserved as a special
# trick shown only at failure - customers' own customer_id IS unique
# regardless of which `how` is picked, so this always passes for real.

_JOIN1_ROW_COUNT_BY_HOW: dict[str, int] = {"inner": JOIN1_INNER_ROW_COUNT, "left": JOIN1_LEFT_ROW_COUNT, "outer": JOIN1_OUTER_ROW_COUNT}


def _join1_options(customers: Dataset) -> tuple[JoinTypeOption, ...]:
    return tuple(
        JoinTypeOption(
            key,
            f"lesson.l13.builder.join1.option.{key}",
            how,
            right_dataset=customers,
            validate="many_to_one",
            validate_explanation_key="lesson.l13.builder.join1.validate_explanation",
        )
        for key, how in (("inner", "inner"), ("left", "left"), ("outer", "outer"))
    )


def _raw_promo_options(active_promotions: Dataset) -> tuple[JoinTypeOption, ...]:
    # Same real contract as Join 1 (validate="many_to_one"), and this
    # time it genuinely fails - active_promotions' own customer_id
    # really isn't unique. The fan-out numbers this would have silently
    # produced are shown next, in concrete_fan_out_example - computed
    # independently (self-contained python_code) rather than depending
    # on this action's own output, since this merge never actually
    # succeeds here.
    return (
        JoinTypeOption(
            "left_raw",
            "lesson.l13.builder.raw_promo.option.left",
            "left",
            right_dataset=active_promotions,
            validate="many_to_one",
            validate_explanation_key="lesson.l13.builder.raw_promo.validate_explanation",
        ),
    )


# --- The promotions repair decision - a real choice, not a narrated
# canonical step. Three genuinely different real strategies against the
# same active_promotions table, each really executed:
#   - preaggregate_first: the correct repair (groupby to customer grain,
#     then a real many-to-one join that actually passes validate=).
#   - join_raw_directly: accept the raw table's own real cardinality,
#     no validate= - keeps the real 147-row fan-out.
#   - dedupe_keep_first: the tempting trap - drop_duplicates makes the
#     key pass validate="many_to_one" too, but silently discards every
#     promotion after the first for a multi-promo customer (real
#     information loss no row-count-based check below can catch; only
#     the concrete per-customer reveal does).


def _repair_decision_options(
    active_promotions: Dataset, promo_per_customer: Dataset, deduped_promotions: Dataset
) -> tuple[JoinTypeOption, ...]:
    return (
        JoinTypeOption(
            "preaggregate_first",
            "lesson.l13.builder.repair_decision.option.preaggregate_first",
            "left",
            right_dataset=promo_per_customer,
            validate="many_to_one",
            validate_explanation_key="lesson.l13.builder.repair_decision.preaggregate_first.validate_explanation",
            preamble_python_code=(
                "promo_per_customer = active_promotions.groupby('customer_id', as_index=False).agg(\n"
                "    active_promotion_count=('promotion_code', 'size'),\n"
                ")"
            ),
        ),
        JoinTypeOption(
            "join_raw_directly",
            "lesson.l13.builder.repair_decision.option.join_raw_directly",
            "left",
            right_dataset=active_promotions,
            validate=None,
            validate_explanation_key="lesson.l13.builder.repair_decision.join_raw_directly.validate_explanation",
        ),
        JoinTypeOption(
            "dedupe_keep_first",
            "lesson.l13.builder.repair_decision.option.dedupe_keep_first",
            "left",
            right_dataset=deduped_promotions,
            validate="many_to_one",
            validate_explanation_key="lesson.l13.builder.repair_decision.dedupe_keep_first.validate_explanation",
            preamble_python_code="deduped_promotions = active_promotions.drop_duplicates(subset='customer_id', keep='first')",
        ),
    )


def _repair_right_dataset(choice: str, active_promotions: Dataset, promo_per_customer: Dataset, deduped_promotions: Dataset) -> Dataset:
    return {"preaggregate_first": promo_per_customer, "join_raw_directly": active_promotions, "dedupe_keep_first": deduped_promotions}[
        choice
    ]


def _represented_promo_count(right: Dataset, customer_id: str) -> float:
    """How many of this customer's real active promotions the CHOSEN
    repair's own right-side table actually represents - read from the
    real `active_promotion_count` feature when the repair produced one
    (preaggregate_first), or counted directly from however many rows
    that table still carries for this customer otherwise (join_raw_
    directly's own 3 raw rows; dedupe_keep_first's own single surviving
    row - silently undercounting, the real trap no row-count-based check
    elsewhere catches)."""
    if "active_promotion_count" in right.frame.columns:
        row = right.frame.loc[right.frame["customer_id"] == customer_id]
        return float(row["active_promotion_count"].iloc[0])
    return float((right.frame["customer_id"] == customer_id).sum())


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

# repair_consequence has no evidence_key on its own options either - same
# manual, update-by-key recording as join1_consequence, since the
# stage-12 revision can change which repair is actually in effect.
REPAIR_CONSEQUENCE_INTERPRET_OPTIONS = (
    InterpretOption("represented_correctly_and_safely", "lesson.l13.repair_consequence.interpret.option.correct"),
    InterpretOption("represented_but_order_row_multiplied", "lesson.l13.repair_consequence.interpret.option.multiplied"),
    InterpretOption("silently_lost_real_information", "lesson.l13.repair_consequence.interpret.option.lost_information"),
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
        BriefOption("dedupe_keep_first", "lesson.l13.decision.needs_preaggregation.option.dedupe_keep_first"),
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
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l13.decision.evidence.prompt", min_count=3, max_count=6)
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

    Both Join 1 and the promotions repair are real cold-pick -> real
    executed consequence -> revision-offer sequences. METHOD is scored
    purely off each one's own FINAL EXECUTED state
    (`join1_choice`/`promotions_repair_choice`) - the Final Decision's own
    claims about them are separately checked for normative understanding
    and internal coherence under REASONING (see scoring.py's own
    docstring for why Final Decision can never "rewrite" what the
    pipeline actually did)."""
    collected: dict = {}
    context = LessonContext()

    customers = generate_customers()
    orders = generate_orders()
    active_promotions = generate_active_promotions()
    promo_per_customer = _promo_per_customer_dataset(active_promotions)
    deduped_promotions = _deduped_promotions_dataset(active_promotions)

    join1_options = _join1_options(customers)
    raw_promo_options = _raw_promo_options(active_promotions)
    repair_decision_options = _repair_decision_options(active_promotions, promo_per_customer, deduped_promotions)

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

    def _record_repair_consequence_evidence(choice: str) -> None:
        right = _repair_right_dataset(choice, active_promotions, promo_per_customer, deduped_promotions)
        represented_count = _represented_promo_count(right, CONCRETE_EXAMPLE_CUSTOMER_ID)
        detail = f"{CONCRETE_EXAMPLE_CUSTOMER_ID}: represents {represented_count:.0f} of 3 real promotions after {choice}"
        action = context.record_action(label_key="lesson.l13.evidence.repair_consequence", key="repair_consequence_role")
        context.record_evidence(
            label_key="lesson.l13.evidence.repair_consequence", source_action=action, key="repair_consequence_role", detail=detail
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
            "customer_id",
            join1_options,
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
                "customer_id",
                join1_options,
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
            "customer_id",
            raw_promo_options,
            on_complete,
            context,
            output_variable_name="raw_promo_join",
            mirror_action_key="raw_promo_pipeline",
            guided=True,
        )

    # --- Concrete fan-out example (rows AND the real revenue consequence) ---

    def concrete_fan_out_example(advance):
        raw_promo_join = orders.frame.merge(active_promotions.frame, on="customer_id", how="left")
        real_revenue = float(orders.frame["revenue"].sum())
        naive_revenue = float(raw_promo_join["revenue"].sum())

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
                    # Self-contained (not "raw_promo_join.loc[...]"): the
                    # earlier raw_promotions_attempt action now really
                    # fails validate="many_to_one" (item 3's own point),
                    # so it never actually assigns raw_promo_join -
                    # nothing upstream in the Mirror can be assumed to
                    # have defined it.
                    python_code=(
                        "raw_promo_join = orders.merge(active_promotions, on='customer_id', how='left')\n"
                        f"raw_promo_join.loc[raw_promo_join['customer_id'] == '{CONCRETE_EXAMPLE_CUSTOMER_ID}']"
                    ),
                    value_format=lambda v: f"{v:,.0f} rows",
                ),
                ComparisonValue(
                    "lesson.l13.fan_out.naive_revenue_label",
                    naive_revenue,
                    python_code=(
                        "raw_promo_join = orders.merge(active_promotions, on='customer_id', how='left')\n"
                        "raw_promo_join['revenue'].sum()"
                    ),
                    value_format=lambda v: f"${v:,.2f}",
                ),
                ComparisonValue(
                    "lesson.l13.fan_out.real_revenue_label",
                    real_revenue,
                    python_code="orders['revenue'].sum()",
                    value_format=lambda v: f"${v:,.2f}",
                ),
            ),
            interpret_prompt_key="lesson.l13.fan_out.interpret_prompt",
            interpret_options=FAN_OUT_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- The promotions repair decision (a real choice, not narrated) ---

    def promotions_repair_decision(advance):
        def on_complete(choice, _succeeded):
            collected["promotions_repair_first_choice"] = choice
            collected["promotions_repair_choice"] = choice
            _sync_context_into_collected()
            advance()

        return JoinBuilderScene(
            app,
            "lesson.l13.builder.repair_decision.title",
            orders,
            "customer_id",
            repair_decision_options,
            on_complete,
            context,
            output_variable_name="final",
            mirror_action_key="repair_pipeline",
            hint_key="lesson.l13.builder.repair_decision.hint",
            guided=True,
        )

    # --- Promotions repair consequence reveal (path-aware, concrete) ---

    def promotions_repair_consequence_reveal(advance):
        choice = collected["promotions_repair_choice"]
        right = _repair_right_dataset(choice, active_promotions, promo_per_customer, deduped_promotions)
        option = next(o for o in repair_decision_options if o.key == choice)
        final = orders.frame.merge(right.frame, on="customer_id", how=option.how, indicator=True, validate=option.validate)
        order_rows_for_customer = float((final["customer_id"] == CONCRETE_EXAMPLE_CUSTOMER_ID).sum())
        represented_count = _represented_promo_count(right, CONCRETE_EXAMPLE_CUSTOMER_ID)

        def on_complete(_interpretation):
            _record_repair_consequence_evidence(choice)
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.repair_consequence.title",
            narrative_keys=("dialogue.l13_repair_consequence.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l13.repair_consequence.real_promo_count_label",
                    3.0,
                    python_code=f"active_promotions.loc[active_promotions['customer_id'] == '{CONCRETE_EXAMPLE_CUSTOMER_ID}']",
                    value_format=lambda v: f"{v:,.0f}",
                ),
                ComparisonValue(
                    "lesson.l13.repair_consequence.order_rows_label", order_rows_for_customer, value_format=lambda v: f"{v:,.0f}"
                ),
                ComparisonValue(
                    "lesson.l13.repair_consequence.represented_count_label", represented_count, value_format=lambda v: f"{v:,.0f}"
                ),
            ),
            interpret_prompt_key="lesson.l13.repair_consequence.interpret_prompt",
            interpret_options=REPAIR_CONSEQUENCE_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Promotions repair revision offer ---

    def promotions_repair_revision_offer(advance):
        prior_choice = collected["promotions_repair_choice"]

        def build_revision_task(on_task_complete):
            def on_revise_complete(choice, _succeeded):
                collected["promotions_repair_choice"] = choice
                if choice != prior_choice:
                    _record_repair_consequence_evidence(choice)
                on_task_complete(None)

            return JoinBuilderScene(
                app,
                "lesson.l13.builder.repair_decision.title",
                orders,
                "customer_id",
                repair_decision_options,
                on_revise_complete,
                context,
                initial_choice=collected["promotions_repair_choice"],
                output_variable_name="final",
                mirror_action_key="repair_pipeline",
                hint_key="lesson.l13.builder.repair_decision.hint",
                guided=True,
            )

        def on_offer_complete(_engaged, _result):
            _sync_context_into_collected()
            advance()

        return OfferThenTaskScene(
            app,
            build_revision_task,
            on_offer_complete,
            title_key="lesson.l13.repair_revision_offer.title",
            line_keys=("lesson.l13.repair_revision_offer.line1",),
            engage_label_key="lesson.l13.repair_revision_offer.engage",
            skip_label_key="lesson.l13.repair_revision_offer.skip",
        )

    # --- Multi-check validation reveal (path-aware - never a canonical-
    # green proof independent of what the student actually did) ---

    def multi_check_validation_reveal(advance):
        choice = collected["promotions_repair_choice"]
        right = _repair_right_dataset(choice, active_promotions, promo_per_customer, deduped_promotions)
        final = orders.frame.merge(right.frame, on="customer_id", how="left", indicator=True)

        row_count_matches = float(len(final))
        order_id_unique = 1.0 if final["order_id"].is_unique else 0.0
        right_key_unique = 1.0 if right.frame["customer_id"].is_unique else 0.0
        revenue_before = float(orders.frame["revenue"].sum())
        revenue_after = float(final["revenue"].sum())
        unmatched = float((final["_merge"] == "left_only").sum())

        def on_complete(_interpretation):
            action = context.record_action(label_key="lesson.l13.evidence.multi_check_validation", key="multi_check_validation_role")
            context.record_evidence(
                label_key="lesson.l13.evidence.multi_check_validation",
                source_action=action,
                key="multi_check_validation_role",
                detail=(
                    f"rows={int(row_count_matches)}, order_id_unique={bool(order_id_unique)}, "
                    f"right_key_unique={bool(right_key_unique)}, revenue ${revenue_before:,.2f} -> ${revenue_after:,.2f}, "
                    f"unmatched={int(unmatched)}"
                ),
            )
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l13.multi_check.title",
            narrative_keys=("dialogue.l13_multi_check.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l13.multi_check.row_count_label", row_count_matches, value_format=lambda v: f"{v:,.0f}"
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.order_id_unique_label", order_id_unique, value_format=lambda v: "Yes" if v == 1.0 else "No"
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.right_key_unique_label",
                    right_key_unique,
                    value_format=lambda v: "Yes" if v == 1.0 else "No",
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.revenue_before_label", revenue_before, value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue(
                    "lesson.l13.multi_check.revenue_after_label", revenue_after, value_format=lambda v: f"${v:,.2f}"
                ),
                ComparisonValue("lesson.l13.multi_check.unmatched_label", unmatched, value_format=lambda v: f"{v:,.0f}"),
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
            promotions_repair_first_choice=collected.get("promotions_repair_first_choice"),
            promotions_repair_choice=collected.get("promotions_repair_choice"),
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
        promotions_repair_decision,
        promotions_repair_consequence_reveal,
        promotions_repair_revision_offer,
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
