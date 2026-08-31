from data_science_arcade.lessons.framework.aggregation import AggregateOption, AggregationRequest, GroupByOption
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l01_question_first.definition import LESSON_01
from data_science_arcade.lessons.l01_question_first.scoring import LessonOneResult, score_lesson_one
from data_science_arcade.lessons.l01_question_first.twist_data import (
    RECENT_WINDOW_START,
    generate_twist_orders,
    is_returning_household,
    repeat_rate,
    total_value_by_household_group,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, InterpretOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene, MasteryOption
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- Act 1: The Ambiguous Ask -----------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l01_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l01_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_investigation.line2"),
    )
)

# --- Act 2: Meet the Data ----------------------------------------------------

INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l01.inspection.prompt",
    options=(
        InspectionOption("order", "lesson.l01.inspection.option.order"),
        InspectionOption("customer", "lesson.l01.inspection.option.customer"),
        InspectionOption("household", "lesson.l01.inspection.option.household"),
    ),
    hint_key="lesson.l01.inspection.hint",
)

# --- Act 3: Grain in Action ---------------------------------------------------

GRAIN_GROUP_BY_OPTIONS = (
    GroupByOption("by_customer", "lesson.l01.grain.group_by.customer", "customer_id"),
    GroupByOption("by_day", "lesson.l01.grain.group_by.day", "order_date"),
)

GRAIN_REQUESTS = (
    AggregationRequest(
        key="order_count",
        prompt_key="lesson.l01.grain.request.order_count.prompt",
        value_column="order_date",
        group_by_options=GRAIN_GROUP_BY_OPTIONS,
        aggregate_options=(AggregateOption("count", "lesson.l01.grain.aggregate.count", "count"),),
        hint_key="lesson.l01.grain.request.order_count.hint",
    ),
    AggregationRequest(
        key="total_spend",
        prompt_key="lesson.l01.grain.request.total_spend.prompt",
        value_column="order_value",
        group_by_options=GRAIN_GROUP_BY_OPTIONS,
        aggregate_options=(AggregateOption("sum", "lesson.l01.grain.aggregate.sum", "sum"),),
        hint_key="lesson.l01.grain.request.total_spend.hint",
    ),
)

# --- Act 4: Guided Brief ------------------------------------------------------

ENTITY_FIELD = BriefField(
    key="entity",
    prompt_key="lesson.l01.field.entity.prompt",
    options=(
        BriefOption("customer", "lesson.l01.option.entity.customer"),
        BriefOption("household", "lesson.l01.option.entity.household"),
        BriefOption("account", "lesson.l01.option.entity.account"),
    ),
)

TIME_HORIZON_FIELD = BriefField(
    key="time_horizon",
    prompt_key="lesson.l01.field.time_horizon.prompt",
    options=(
        BriefOption("last_30_days", "lesson.l01.option.time_horizon.last_30_days"),
        BriefOption("last_90_days", "lesson.l01.option.time_horizon.last_90_days"),
        BriefOption("last_12_months", "lesson.l01.option.time_horizon.last_12_months"),
        BriefOption("since_signup", "lesson.l01.option.time_horizon.since_signup"),
    ),
)

BEHAVIOR_FIELD = BriefField(
    key="behavior",
    prompt_key="lesson.l01.field.behavior.prompt",
    hint_key="lesson.l01.field.behavior.hint",
    options=(
        BriefOption("repeat_purchase", "lesson.l01.option.behavior.repeat_purchase"),
        BriefOption("any_purchase", "lesson.l01.option.behavior.any_purchase"),
        BriefOption("app_login", "lesson.l01.option.behavior.app_login"),
        BriefOption("subscription_renewal", "lesson.l01.option.behavior.subscription_renewal"),
    ),
)

POPULATION_FIELD = BriefField(
    key="population",
    prompt_key="lesson.l01.field.population.prompt",
    hint_key="lesson.l01.field.population.hint",
    options=(
        BriefOption("all_customers", "lesson.l01.option.population.all_customers"),
        BriefOption("active_last_year", "lesson.l01.option.population.active_last_year"),
        BriefOption("new_last_6_months", "lesson.l01.option.population.new_last_6_months"),
    ),
)

METRIC_FIELD = BriefField(
    key="metric",
    prompt_key="lesson.l01.field.metric.prompt",
    options=(
        BriefOption("retention_rate", "lesson.l01.option.metric.retention_rate"),
        BriefOption("purchase_frequency", "lesson.l01.option.metric.purchase_frequency"),
        BriefOption("churn_rate", "lesson.l01.option.metric.churn_rate"),
        BriefOption("days_since_last_order", "lesson.l01.option.metric.days_since_last_order"),
    ),
)

DECISION_SUPPORT_FIELD = BriefField(
    key="decision_support",
    prompt_key="lesson.l01.field.decision_support.prompt",
    hint_key="lesson.l01.field.decision_support.hint",
    options=(
        BriefOption("loyalty_program", "lesson.l01.option.decision_support.loyalty_program"),
        BriefOption("escalate", "lesson.l01.option.decision_support.escalate"),
        BriefOption("segment_investigation", "lesson.l01.option.decision_support.segment_investigation"),
    ),
)

BRIEF_FIELDS: tuple[BriefField, ...] = (
    ENTITY_FIELD,
    TIME_HORIZON_FIELD,
    BEHAVIOR_FIELD,
    POPULATION_FIELD,
    METRIC_FIELD,
    DECISION_SUPPORT_FIELD,
)

TIERED_HINT_KEYS = {
    "entity": (
        "lesson.l01.field.entity.hint_tier1",
        "lesson.l01.field.entity.hint_tier2",
        "lesson.l01.field.entity.hint_tier3",
    ),
    "time_horizon": (
        "lesson.l01.field.time_horizon.hint_tier1",
        "lesson.l01.field.time_horizon.hint_tier2",
        "lesson.l01.field.time_horizon.hint_tier3",
    ),
    "metric": (
        "lesson.l01.field.metric.hint_tier1",
        "lesson.l01.field.metric.hint_tier2",
        "lesson.l01.field.metric.hint_tier3",
    ),
}

# --- Act 5: Time-Window Sensitivity ------------------------------------------

WINDOW_PREDICTION_FIELD = BriefField(
    key="window_prediction",
    prompt_key="lesson.l01.window_predict.prompt",
    options=(
        BriefOption("recent_lower", "lesson.l01.window_predict.option.recent_lower"),
        BriefOption("recent_higher", "lesson.l01.window_predict.option.recent_higher"),
        BriefOption("about_same", "lesson.l01.window_predict.option.about_same"),
    ),
)

WINDOW_CONFIDENCE_BEFORE_FIELD = BriefField(
    key="window_confidence_before",
    prompt_key="lesson.l01.window_confidence_before.prompt",
    hint_key="lesson.l01.window_confidence_before.hint",
    options=(
        BriefOption("low", "lesson.l01.decision.confidence.option.low"),
        BriefOption("medium", "lesson.l01.decision.confidence.option.medium"),
        BriefOption("high", "lesson.l01.decision.confidence.option.high"),
    ),
)

WINDOW_INTERPRET_OPTIONS = (
    InterpretOption("real_shift", "lesson.l01.window_interpret.option.real_shift"),
    InterpretOption("needs_more_data", "lesson.l01.window_interpret.option.needs_more_data"),
)

# --- Act 6: Entity Sensitivity ------------------------------------------------

HOUSEHOLD_REVEAL_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l01_household_reveal.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l01_household_reveal.line2"),
    )
)

ENTITY_REVISION_FIELD = BriefField(
    key="entity_revision",
    prompt_key="lesson.l01.entity_revision.prompt",
    hint_key="lesson.l01.entity_revision.hint",
    options=(
        BriefOption("customer", "lesson.l01.option.entity.customer"),
        BriefOption("household", "lesson.l01.option.entity.household"),
    ),
)

ENTITY_INTERPRET_OPTIONS = (
    InterpretOption("entity_changes_the_count", "lesson.l01.entity_interpret.option.entity_changes_the_count"),
    InterpretOption("entity_does_not_matter", "lesson.l01.entity_interpret.option.entity_does_not_matter"),
)

# --- Act 7: Coverage Discovery ------------------------------------------------

COVERAGE_REVEAL_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l01_coverage_reveal.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l01_coverage_reveal.line2"),
    )
)

COVERAGE_INTERPRET_FIELD = BriefField(
    key="coverage_interpretation",
    prompt_key="lesson.l01.coverage_interpret.prompt",
    options=(
        BriefOption("narrow_the_claim", "lesson.l01.coverage_interpret.option.narrow_the_claim"),
        BriefOption("numbers_still_wrong", "lesson.l01.coverage_interpret.option.numbers_still_wrong"),
        BriefOption("does_not_matter", "lesson.l01.coverage_interpret.option.does_not_matter"),
    ),
)

# --- Act 9: Evidence Review is pure WorkbenchScene, no new content ----------

# --- Act 10: Final Decision Builder ------------------------------------------

CLAIM_FIELD = BriefField(
    key="claim",
    prompt_key="lesson.l01.decision.claim.prompt",
    options=(
        BriefOption("overreaching", "lesson.l01.decision.claim.option.overreaching"),
        BriefOption("well_scoped", "lesson.l01.decision.claim.option.well_scoped"),
        BriefOption("either_view", "lesson.l01.decision.claim.option.either_view"),
        BriefOption("cannot_say", "lesson.l01.decision.claim.option.cannot_say"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l01.decision.evidence.prompt",
    min_count=2,
    max_count=3,
)

DECISION_LIMITATION_FIELD = BriefField(
    key="limitation",
    prompt_key="lesson.l01.decision.limitation.prompt",
    options=(
        BriefOption("definition_sensitive", "lesson.l01.decision.limitation.option.definition_sensitive"),
        BriefOption("coverage_gap", "lesson.l01.decision.limitation.option.coverage_gap"),
        BriefOption("no_seasonality", "lesson.l01.decision.limitation.option.no_seasonality"),
        BriefOption("no_real_limitation", "lesson.l01.decision.limitation.option.no_real_limitation"),
    ),
)

DECISION_CONFIDENCE_FIELD = BriefField(
    key="confidence",
    prompt_key="lesson.l01.decision.confidence.prompt",
    options=(
        BriefOption("low", "lesson.l01.decision.confidence.option.low"),
        BriefOption("medium", "lesson.l01.decision.confidence.option.medium"),
        BriefOption("high", "lesson.l01.decision.confidence.option.high"),
    ),
)

DECISION_RECOMMENDATION_FIELD = BriefField(
    key="recommendation",
    prompt_key="lesson.l01.decision.recommendation.prompt",
    options=(
        BriefOption("loyalty_program", "lesson.l01.option.decision_support.loyalty_program"),
        BriefOption("escalate", "lesson.l01.option.decision_support.escalate"),
        BriefOption("segment_investigation", "lesson.l01.option.decision_support.segment_investigation"),
    ),
)

DECISION_FOLLOW_UP_FIELD = BriefField(
    key="follow_up",
    prompt_key="lesson.l01.decision.follow_up.prompt",
    options=(
        BriefOption("get_identity_data", "lesson.l01.decision.follow_up.option.get_identity_data"),
        BriefOption("rerun_next_month", "lesson.l01.decision.follow_up.option.rerun_next_month"),
        BriefOption("nothing_further", "lesson.l01.decision.follow_up.option.nothing_further"),
    ),
)

# --- Act 11: Optional Mastery Challenge --------------------------------------

MASTERY_METRIC_OPTIONS = (
    MasteryOption("total", "lesson.l01.mastery.metric_total"),
    MasteryOption("average", "lesson.l01.mastery.metric_average"),
)

MASTERY_INTERPRET_OPTIONS = (
    MasteryOption("returning_higher", "lesson.l01.mastery.interpret_returning_higher"),
    MasteryOption("about_same", "lesson.l01.mastery.interpret_about_same"),
)

# --- Act 12: Debrief ----------------------------------------------------------

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_debrief.line2"),
    )
)


def _evidence_family(label_key: str) -> str:
    """Groups an EvidenceItem by which part of the investigation it came
    from (lesson.l01.evidence.window_30d_label -> "window", etc.) - used
    only to check the Decision Builder's picked evidence spans more than
    one real source, not just repeats of the same finding."""
    for family in ("window", "entity", "coverage"):
        if family in label_key:
            return family
    return "other"


def build_lesson_one_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 01's real 70-90 minute act structure: one
    continuous investigation on one dataset (twist_data.py), not a string
    of disconnected exercises - a persistent `context` (LessonContext) is
    threaded via closures through every analytical stage, so evidence
    gathered early (Acts 2-3) is still visible when the student builds
    their final argument (Act 10). See decisions/IMPLEMENTATION_STATE.md
    for the full act-by-act rationale and time budget this stage list is
    built from."""
    collected: dict = {}
    context = LessonContext()
    dataset = generate_twist_orders()

    def _restore_context_if_present() -> None:
        saved = collected.get("analytical_context")
        if saved is not None:
            context.restore_from_dict(saved)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- Act 1 ---

    def briefing(advance):
        _restore_context_if_present()
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    # --- Act 2 ---

    def meet_the_data(advance):
        def on_complete(_resolution):
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(
            app,
            dataset,
            issues=(),
            on_complete=on_complete,
            context=context,
            visible_tabs=(WorkbenchTab.MISSION, WorkbenchTab.DATA),
            inspection_prompt=INSPECTION_PROMPT,
        )

    # --- Act 3 ---

    def grain_in_action(advance):
        # Deliberately NOT passed the shared `context`: this act's real
        # payoff is the live preview inside the scene itself (order rows
        # becoming customer rows, in front of the student), not a lasting
        # evidence trail. Group-by choice alone ("By customer") carries no
        # number and no request-specific meaning once recorded as a bare
        # AnalyticalAction/EvidenceItem - threading it into the shared
        # context produced two visually-identical, content-free "By
        # customer" entries in the Decision Builder's evidence pool
        # (order_count's and total_spend's group-by choices collide on
        # label text with nothing to tell them apart), for a claim
        # (repeat-purchase rate) this act's own numbers don't actually
        # speak to anyway. A fresh throwaway LessonContext (this scene's
        # own default) keeps that live preview without polluting the real
        # investigation's evidence trail.
        def on_complete(_choices):
            advance()

        return PipelineBuilderScene(app, "lesson.l01.grain.title", dataset, GRAIN_REQUESTS, on_complete)

    # --- Act 4 ---

    def guided_brief(advance):
        def on_complete(brief):
            collected["guided_brief"] = brief
            advance()

        return BriefBuilderScene(
            app, "lesson.l01.brief_title", BRIEF_FIELDS, on_complete, guided=True, tiered_hint_keys=TIERED_HINT_KEYS
        )

    # --- Act 5 ---

    def predict_window(advance):
        def on_complete(brief):
            collected["window_prediction"] = brief["window_prediction"]
            collected["window_confidence_before"] = brief["window_confidence_before"]
            advance()

        return BriefBuilderScene(
            app,
            "lesson.l01.window_predict.title",
            (WINDOW_PREDICTION_FIELD, WINDOW_CONFIDENCE_BEFORE_FIELD),
            on_complete,
            guided=False,
        )

    def compute_window(advance):
        def on_complete(interpretation):
            collected["window_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        recent_rate = repeat_rate(dataset, "customer_id", RECENT_WINDOW_START)
        full_period_rate = repeat_rate(dataset, "customer_id", None)
        return ComparisonRevealScene(
            app,
            title_key="lesson.l01.window_compute.title",
            narrative_keys=("dialogue.l01_window_compute.line1", "dialogue.l01_window_compute.line2"),
            comparisons=(
                ("lesson.l01.evidence.window_30d_label", recent_rate),
                ("lesson.l01.evidence.window_12m_label", full_period_rate),
            ),
            interpret_prompt_key="lesson.l01.window_interpret.prompt",
            interpret_options=WINDOW_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Act 6 ---

    def household_reveal(advance):
        return DialogueScene(app, HOUSEHOLD_REVEAL_DIALOGUE, on_complete=advance)

    def revise_entity(advance):
        def on_complete(brief):
            collected["entity_revision"] = brief["entity_revision"]
            advance()

        return BriefBuilderScene(app, "lesson.l01.entity_revision.title", (ENTITY_REVISION_FIELD,), on_complete, guided=False)

    def compute_entity(advance):
        def on_complete(interpretation):
            collected["entity_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        customer_rate = repeat_rate(dataset, "customer_id", RECENT_WINDOW_START)
        household_rate = repeat_rate(dataset, "household_id", RECENT_WINDOW_START)
        return ComparisonRevealScene(
            app,
            title_key="lesson.l01.entity_compute.title",
            narrative_keys=("dialogue.l01_entity_compute.line1",),
            comparisons=(
                ("lesson.l01.evidence.entity_customer_label", customer_rate),
                ("lesson.l01.evidence.entity_household_label", household_rate),
            ),
            interpret_prompt_key="lesson.l01.entity_interpret.prompt",
            interpret_options=ENTITY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Act 7 ---

    def coverage_reveal(advance):
        return DialogueScene(app, COVERAGE_REVEAL_DIALOGUE, on_complete=advance)

    def coverage_interpret(advance):
        def on_complete(brief):
            choice_key = brief["coverage_interpretation"]
            collected["coverage_interpretation"] = choice_key
            option = next(o for o in COVERAGE_INTERPRET_FIELD.options if o.key == choice_key)
            action = context.record_action(label_key=option.label_key, key="coverage_interpretation")
            context.record_evidence(label_key="lesson.l01.evidence.coverage_gap_label", source_action=action, key="coverage_gap")
            _sync_context_into_collected()
            advance()

        return BriefBuilderScene(
            app, "lesson.l01.coverage_interpret.title", (COVERAGE_INTERPRET_FIELD,), on_complete, guided=False
        )

    # --- Act 8 ---

    def the_twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l01.twist_title",
            narrative_keys=(
                "dialogue.l01_twist.line1",
                "dialogue.l01_twist.line2",
                "dialogue.l01_twist.line3",
            ),
            dataset=dataset,
            comparisons=(
                ("lesson.l01.evidence.window_30d_label", repeat_rate(dataset, "customer_id", RECENT_WINDOW_START)),
                ("lesson.l01.evidence.window_12m_label", repeat_rate(dataset, "customer_id", None)),
                ("lesson.l01.evidence.entity_household_label", repeat_rate(dataset, "household_id", RECENT_WINDOW_START)),
            ),
            on_complete=advance,
        )

    # --- Act 9 ---

    def evidence_review(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            dataset,
            issues=(),
            on_complete=on_complete,
            context=context,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.EVIDENCE, WorkbenchTab.PYTHON),
        )

    # --- Act 10 ---

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
            "lesson.l01.decision_title",
            steps=(
                CLAIM_FIELD,
                DECISION_EVIDENCE_FIELD,
                DECISION_LIMITATION_FIELD,
                DECISION_CONFIDENCE_FIELD,
                DECISION_RECOMMENDATION_FIELD,
                DECISION_FOLLOW_UP_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Act 11 (optional) ---

    def mastery_challenge(advance):
        def on_complete(engaged, metric_key, interpretation_key):
            collected["mastery_engaged"] = engaged
            collected["mastery_metric"] = metric_key
            collected["mastery_interpretation"] = interpretation_key
            _sync_context_into_collected()
            advance()

        def compute(metric_key: str) -> tuple[tuple[str, float], tuple[str, float]]:
            if metric_key == "total":
                returning = total_value_by_household_group(dataset, returning=True)
                one_time = total_value_by_household_group(dataset, returning=False)
            else:
                returning_households = {
                    hid for hid in dataset.frame["household_id"].unique() if is_returning_household(dataset, hid)
                }
                one_time_households = set(dataset.frame["household_id"].unique()) - returning_households
                returning = total_value_by_household_group(dataset, returning=True) / max(len(returning_households), 1)
                one_time = total_value_by_household_group(dataset, returning=False) / max(len(one_time_households), 1)
            return (
                ("lesson.l01.mastery.returning_label", returning),
                ("lesson.l01.mastery.one_time_label", one_time),
            )

        return MasteryChallengeScene(
            app,
            title_key="lesson.l01.mastery.title",
            narrative_keys=("dialogue.l01_mastery.line1", "dialogue.l01_mastery.line2"),
            metric_prompt_key="lesson.l01.mastery.metric_prompt",
            metric_options=MASTERY_METRIC_OPTIONS,
            compute=compute,
            interpret_prompt_key="lesson.l01.mastery.interpret_prompt",
            interpret_options=MASTERY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Act 12 ---

    def _build_result() -> LessonOneResult:
        # A plain function, not something stashed in `collected`:
        # LessonRunner checkpoints `collected` via json.dumps on every
        # stage transition, and a LessonOneResult/LessonEvaluation object
        # isn't JSON-serializable - storing one there broke the very next
        # checkpoint save. Recomputed from collected's own plain,
        # already-serializable values instead, wherever it's needed.
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))
        evidence_families = tuple(
            sorted({_evidence_family(item.label_key) for item in context.evidence if item.id in selected_evidence_ids})
        )
        return LessonOneResult(
            guided_brief=collected.get("guided_brief", {}),
            entity_revision=collected.get("entity_revision", ""),
            window_prediction=collected.get("window_prediction", ""),
            window_confidence_before=collected.get("window_confidence_before", ""),
            window_interpretation=collected.get("window_interpretation", ""),
            entity_interpretation=collected.get("entity_interpretation", ""),
            coverage_interpretation=collected.get("coverage_interpretation", ""),
            decision=decision,
            evidence_families=evidence_families,
            mastery_engaged=collected.get("mastery_engaged", False),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        # Reads the same (pre-existing, not-yet-updated-by-this-attempt)
        # value course_map_scene.py's own on_finished will read moments
        # later for the exact same lesson_number - score_lesson_one is a
        # pure function, so computing it here (for immediate display) and
        # again in finished() below (for on_finished) is safe: same
        # inputs, same result, and neither ever touches `collected`.
        hints_used = app.progress.hints_used.get(LESSON_01.number, 0)
        evaluation = score_lesson_one(result, LESSON_01, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        meet_the_data,
        grain_in_action,
        guided_brief,
        predict_window,
        compute_window,
        household_reveal,
        revise_entity,
        compute_entity,
        coverage_reveal,
        coverage_interpret,
        the_twist,
        evidence_review,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=1, collected=collected, definition=LESSON_01
    )
    return runner, collected
