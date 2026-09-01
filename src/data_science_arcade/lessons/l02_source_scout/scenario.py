from data_science_arcade.lessons.framework.aggregation import AggregateOption, AggregationRequest, GroupByOption
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.source import DataSource, SourceAttribute
from data_science_arcade.lessons.l02_source_scout.definition import LESSON_02
from data_science_arcade.lessons.l02_source_scout.scoring import CRITICAL_EVIDENCE_KEYS, LessonTwoResult, score_lesson_two
from data_science_arcade.lessons.l02_source_scout.twist_data import (
    LEGACYPAY,
    app_log_active_count,
    billing_active_count,
    generate_app_log,
    generate_billing,
    generate_marketing,
    generate_support,
    marketing_enrolled_count,
    missing_from_billing_counts,
    population_legacypay_share,
    support_legacypay_counts,
    support_legacypay_share,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene, MasteryOption
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.source_board_scene import SourceBoardScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask ------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l02_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l02_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l02_briefing.line3"),
    )
)

FRAMING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_framing.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_framing.line2"),
    )
)

# --- Source Map -----------------------------------------------------------

SOURCES: tuple[DataSource, ...] = (
    # Deliberately 4 neutral facts per source - owner, format, documented
    # purpose, freshness - none of them High/Medium/Low rated and none of
    # them the thing this lesson's real comparisons exist to make the
    # student discover firsthand: which customers a source actually
    # covers, and what it counts as "active." A dossier that already
    # states "Currently billed subscribers" or "Active means payment
    # status not cancelled" up front would hand the student comparison_1's
    # and comparison_2's own conclusions before they ever open the data.
    DataSource(
        key="billing",
        name_key="lesson.l02.source.billing.name",
        attributes=(
            SourceAttribute("lesson.l02.attr.owner", "lesson.l02.fact.billing.owner"),
            SourceAttribute("lesson.l02.attr.format", "lesson.l02.fact.billing.format"),
            SourceAttribute("lesson.l02.attr.documented_purpose", "lesson.l02.fact.billing.documented_purpose"),
            SourceAttribute("lesson.l02.attr.freshness", "lesson.l02.fact.billing.freshness"),
        ),
    ),
    DataSource(
        key="app_log",
        name_key="lesson.l02.source.app_log.name",
        attributes=(
            SourceAttribute("lesson.l02.attr.owner", "lesson.l02.fact.app_log.owner"),
            SourceAttribute("lesson.l02.attr.format", "lesson.l02.fact.app_log.format"),
            SourceAttribute("lesson.l02.attr.documented_purpose", "lesson.l02.fact.app_log.documented_purpose"),
            SourceAttribute("lesson.l02.attr.freshness", "lesson.l02.fact.app_log.freshness"),
        ),
    ),
    DataSource(
        key="marketing",
        name_key="lesson.l02.source.marketing.name",
        attributes=(
            SourceAttribute("lesson.l02.attr.owner", "lesson.l02.fact.marketing.owner"),
            SourceAttribute("lesson.l02.attr.format", "lesson.l02.fact.marketing.format"),
            SourceAttribute("lesson.l02.attr.documented_purpose", "lesson.l02.fact.marketing.documented_purpose"),
            SourceAttribute("lesson.l02.attr.freshness", "lesson.l02.fact.marketing.freshness"),
        ),
    ),
    DataSource(
        key="support",
        name_key="lesson.l02.source.support.name",
        attributes=(
            SourceAttribute("lesson.l02.attr.owner", "lesson.l02.fact.support.owner"),
            SourceAttribute("lesson.l02.attr.format", "lesson.l02.fact.support.format"),
            SourceAttribute("lesson.l02.attr.documented_purpose", "lesson.l02.fact.support.documented_purpose"),
            SourceAttribute("lesson.l02.attr.freshness", "lesson.l02.fact.support.freshness"),
        ),
    ),
)

# --- Meet Billing -----------------------------------------------------------

BILLING_INSPECTION = InspectionPrompt(
    prompt_key="lesson.l02.billing_inspect.prompt",
    options=(
        InspectionOption("who_pays", "lesson.l02.billing_inspect.option.who_pays"),
        InspectionOption("everyone_enrolled", "lesson.l02.billing_inspect.option.everyone_enrolled"),
        InspectionOption("no_idea", "lesson.l02.billing_inspect.option.no_idea"),
    ),
    hint_key="lesson.l02.billing_inspect.hint",
)

BILLING_GROUP_BY_OPTIONS = (
    GroupByOption("by_status", "lesson.l02.billing_compute.group_by.status", "status"),
    GroupByOption("by_customer", "lesson.l02.billing_compute.group_by.customer", "customer_id"),
)

BILLING_REQUESTS = (
    AggregationRequest(
        key="billing_active",
        prompt_key="lesson.l02.billing_compute.prompt",
        value_column="customer_id",
        group_by_options=BILLING_GROUP_BY_OPTIONS,
        aggregate_options=(AggregateOption("count", "lesson.l02.billing_compute.aggregate.count", "count"),),
        hint_key="lesson.l02.billing_compute.hint",
    ),
)

# --- Meet the App Log --------------------------------------------------------

APP_LOG_INSPECTION = InspectionPrompt(
    prompt_key="lesson.l02.app_log_inspect.prompt",
    options=(
        InspectionOption("app_users_only", "lesson.l02.app_log_inspect.option.app_users_only"),
        InspectionOption("every_plus_member", "lesson.l02.app_log_inspect.option.every_plus_member"),
        InspectionOption("payers_only", "lesson.l02.app_log_inspect.option.payers_only"),
    ),
    hint_key="lesson.l02.app_log_inspect.hint",
)

# --- Conflict #1: Billing vs. App Log ----------------------------------------

COMPARISON_1_INTERPRET_OPTIONS = (
    InterpretOption("different_population_and_definition", "lesson.l02.comparison1_interpret.option.different_population_and_definition"),
    InterpretOption("one_is_wrong", "lesson.l02.comparison1_interpret.option.one_is_wrong"),
    InterpretOption("just_average_them", "lesson.l02.comparison1_interpret.option.just_average_them"),
)

# --- Conflict #2: Billing vs. Marketing --------------------------------------

MARKETING_INSPECTION = InspectionPrompt(
    prompt_key="lesson.l02.marketing_inspect.prompt",
    options=(
        InspectionOption("everyone_ever_enrolled", "lesson.l02.marketing_inspect.option.everyone_ever_enrolled"),
        InspectionOption("only_current_payers", "lesson.l02.marketing_inspect.option.only_current_payers"),
        InspectionOption("only_active_app_users", "lesson.l02.marketing_inspect.option.only_active_app_users"),
    ),
    hint_key="lesson.l02.marketing_inspect.hint",
)

COMPARISON_2_INTERPRET_OPTIONS = (
    InterpretOption("different_construct", "lesson.l02.comparison2_interpret.option.different_construct"),
    InterpretOption("marketing_is_wrong", "lesson.l02.comparison2_interpret.option.marketing_is_wrong"),
    InterpretOption("billing_is_wrong", "lesson.l02.comparison2_interpret.option.billing_is_wrong"),
)

# --- The Real Gap -------------------------------------------------------------

GAP_INTERPRET_OPTIONS = (
    InterpretOption("all_a_bug", "lesson.l02.gap_interpret.option.all_a_bug"),
    InterpretOption("mixed_and_unresolved", "lesson.l02.gap_interpret.option.mixed_and_unresolved"),
    InterpretOption("noise_ignore_it", "lesson.l02.gap_interpret.option.noise_ignore_it"),
    InterpretOption("trust_marketing_instead", "lesson.l02.gap_interpret.option.trust_marketing_instead"),
)
# No evidence_key here, deliberately: gating the "no source resolves this
# population's status" fact on a single early interpretation pick meant a
# student who guessed wrong here - then correctly updated their own
# understanding a stage later, once FINANCE_LEAD_DIALOGUE confirms it
# outright - had no way to ever cite the fact they now genuinely know is
# true. finance_lead_confirms below records it unconditionally instead;
# the interpretation pick itself is still tracked (LessonTwoResult.
# gap_interpretation) and still feeds a real, if unscored, feedback signal
# about the student's own initial-belief-to-revision trajectory.

FINANCE_LEAD_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l02_finance_lead.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l02_finance_lead.line2"),
    )
)

REVISION_FIELD = BriefField(
    key="revision_choice",
    prompt_key="lesson.l02.revision.prompt",
    hint_key="lesson.l02.revision.hint",
    options=(
        BriefOption("still_billing_alone", "lesson.l02.revision.option.still_billing_alone"),
        BriefOption("billing_plus_something", "lesson.l02.revision.option.billing_plus_something"),
        BriefOption("not_sure_yet", "lesson.l02.revision.option.not_sure_yet"),
    ),
)

# --- Support's List -----------------------------------------------------------

SUPPORT_INTERPRET_OPTIONS = (
    InterpretOption("dedupe_before_trusting", "lesson.l02.support_interpret.option.dedupe_before_trusting"),
    InterpretOption("duplicates_dont_matter", "lesson.l02.support_interpret.option.duplicates_dont_matter"),
    InterpretOption("list_is_unusable", "lesson.l02.support_interpret.option.list_is_unusable"),
)

# --- Final Decision -------------------------------------------------------------

ANSWER_STRATEGY_FIELD = BriefField(
    key="answer_strategy",
    prompt_key="lesson.l02.decision.answer_strategy.prompt",
    options=(
        BriefOption("false_precision", "lesson.l02.decision.answer_strategy.option.false_precision"),
        BriefOption("naive_exclusion", "lesson.l02.decision.answer_strategy.option.naive_exclusion"),
        BriefOption("floor_and_range", "lesson.l02.decision.answer_strategy.option.floor_and_range"),
        BriefOption("cannot_determine", "lesson.l02.decision.answer_strategy.option.cannot_determine"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l02.decision.evidence.prompt",
    min_count=2,
    max_count=3,
)

KNOWN_GAP_FIELD = BriefField(
    key="known_gap",
    prompt_key="lesson.l02.decision.known_gap.prompt",
    options=(
        BriefOption("legacy_exclusion", "lesson.l02.decision.known_gap.option.legacy_exclusion"),
        BriefOption("tracking_bug_decoy", "lesson.l02.decision.known_gap.option.tracking_bug_decoy"),
        BriefOption("generic_caveat", "lesson.l02.decision.known_gap.option.generic_caveat"),
        BriefOption("no_real_gap", "lesson.l02.decision.known_gap.option.no_real_gap"),
    ),
)

SAFE_TO_CLAIM_FIELD = BriefField(
    key="safe_to_claim",
    prompt_key="lesson.l02.decision.safe_to_claim.prompt",
    options=(
        BriefOption("floor_and_range", "lesson.l02.decision.safe_to_claim.option.floor_and_range"),
        BriefOption("exact_precision", "lesson.l02.decision.safe_to_claim.option.exact_precision"),
        BriefOption("nothing_usable", "lesson.l02.decision.safe_to_claim.option.nothing_usable"),
    ),
)

NOT_SAFE_TO_CLAIM_FIELD = BriefField(
    key="not_safe_to_claim",
    prompt_key="lesson.l02.decision.not_safe_to_claim.prompt",
    options=(
        BriefOption("single_exact_total", "lesson.l02.decision.not_safe_to_claim.option.single_exact_total"),
        BriefOption("individual_customer_decision", "lesson.l02.decision.not_safe_to_claim.option.individual_customer_decision"),
        BriefOption("range_itself", "lesson.l02.decision.not_safe_to_claim.option.range_itself"),
    ),
)

RECOMMENDATION_FIELD = BriefField(
    key="recommendation",
    prompt_key="lesson.l02.decision.recommendation.prompt",
    options=(
        BriefOption("report_and_reconcile", "lesson.l02.decision.recommendation.option.report_and_reconcile"),
        BriefOption("use_raw_billing", "lesson.l02.decision.recommendation.option.use_raw_billing"),
        BriefOption("block_until_perfect", "lesson.l02.decision.recommendation.option.block_until_perfect"),
    ),
)

# --- Optional Mastery Challenge ------------------------------------------------

MASTERY_METRIC_OPTIONS = (
    MasteryOption("raw_counts", "lesson.l02.mastery.metric_raw_counts"),
    MasteryOption("proportions", "lesson.l02.mastery.metric_proportions"),
)

MASTERY_INTERPRET_OPTIONS = (
    MasteryOption("overrepresented", "lesson.l02.mastery.interpret_overrepresented"),
    MasteryOption("representative", "lesson.l02.mastery.interpret_representative"),
    MasteryOption("raw_already_answers_it", "lesson.l02.mastery.interpret_raw_already_answers_it"),
)

# --- Debrief --------------------------------------------------------------------

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_debrief.line2"),
    )
)


def _critical_evidence_present(context: LessonContext, selected_evidence_ids: set[str]) -> tuple[str, ...]:
    """Which of CRITICAL_EVIDENCE_KEYS the student's picked evidence
    actually covers - checked by substring on the picked items' own
    label_key, the same technique l01_question_first/scenario.py's
    _evidence_family() uses for its own (differently-shaped) evidence
    check."""
    present: set[str] = set()
    for item in context.evidence:
        if item.id not in selected_evidence_ids:
            continue
        for critical_key in CRITICAL_EVIDENCE_KEYS:
            if critical_key in item.label_key:
                present.add(critical_key)
    return tuple(sorted(present))


def build_lesson_two_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 02's real 18-stage investigation: one continuous
    LessonContext threaded via closures through every analytical stage, on
    four real, hand-crafted datasets (twist_data.py) rather than abstract
    High/Medium/Low source ratings. The four sources never let a student
    honestly reconstruct the true active-paying count - Billing
    structurally excludes the 30 real legacypay accounts, and no source
    re-establishes their current status - so the lesson's own correct
    output is a confirmed floor and a defensible range, not a single
    "corrected" total; ANSWER_STRATEGY_FIELD's own options score that
    distinction directly (see scoring.py)."""
    collected: dict = {}
    context = LessonContext()
    billing = generate_billing()
    app_log = generate_app_log()
    marketing = generate_marketing()
    support = generate_support()

    def _restore_context_if_present() -> None:
        saved = collected.get("analytical_context")
        if saved is not None:
            context.restore_from_dict(saved)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def framing(advance):
        return DialogueScene(app, FRAMING_DIALOGUE, on_complete=advance)

    # --- Source Map ---

    def source_map(advance):
        def on_complete(source_key):
            collected["initial_inspect_pick"] = source_key
            _sync_context_into_collected()
            advance()

        return SourceBoardScene(
            app,
            "lesson.l02.source_map.title",
            "lesson.l02.source_map.prompt",
            SOURCES,
            on_complete,
            guided=True,
            hint_key="lesson.l02.source_map.hint",
            context=context,
        )

    # --- Meet Billing ---

    def meet_billing(advance):
        def on_complete(_resolution):
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(
            app,
            billing,
            issues=(),
            on_complete=on_complete,
            context=context,
            visible_tabs=(WorkbenchTab.MISSION, WorkbenchTab.DATA),
            inspection_prompt=BILLING_INSPECTION,
        )

    def compute_billing(advance):
        # record_evidence=False: a bare group-by pick ("By status") has no
        # number attached, so it isn't useful evidence on its own - the
        # real, citable "100 confirmed active" fact comes from
        # comparison_1 below instead, which attaches the live value as
        # EvidenceItem.detail. The real AnalyticalAction/Python Mirror
        # line is still recorded (context= is passed) - same split as
        # l01_question_first's own Grain in Action act.
        def on_complete(_choices):
            _sync_context_into_collected()
            advance()

        return PipelineBuilderScene(
            app, "lesson.l02.billing_compute.title", billing, BILLING_REQUESTS, on_complete, context=context, record_evidence=False
        )

    # --- Meet the App Log ---

    def meet_app_log(advance):
        def on_complete(_resolution):
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(
            app,
            app_log,
            issues=(),
            on_complete=on_complete,
            context=context,
            visible_tabs=(WorkbenchTab.DATA,),
            inspection_prompt=APP_LOG_INSPECTION,
        )

    # --- Conflict #1 ---

    def comparison_1(advance):
        def on_complete(interpretation):
            collected["comparison_1_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l02.comparison1.title",
            narrative_keys=(
                "dialogue.l02_comparison1.line1",
                "dialogue.l02_comparison1.line2",
                "dialogue.l02_comparison1.line3",
            ),
            comparisons=(
                ComparisonValue(
                    "lesson.l02.evidence.billing_active_label",
                    float(billing_active_count(billing)),
                    python_code="(billing.status == 'active').sum()",
                ),
                ComparisonValue(
                    "lesson.l02.evidence.app_log_active_label",
                    float(app_log_active_count(app_log)),
                    python_code=(
                        "app_log = pd.read_json('go_app_activity_snapshot.json')\n"
                        "cutoff = pd.Timestamp('2026-06-01') - pd.Timedelta(days=30)\n"
                        "app_log[app_log.last_open >= cutoff].customer_id.nunique()"
                    ),
                ),
            ),
            interpret_prompt_key="lesson.l02.comparison1_interpret.prompt",
            interpret_options=COMPARISON_1_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    # --- Meet Marketing ---

    def meet_marketing(advance):
        def on_complete(_resolution):
            _sync_context_into_collected()
            advance()

        return WorkbenchScene(
            app,
            marketing,
            issues=(),
            on_complete=on_complete,
            context=context,
            visible_tabs=(WorkbenchTab.DATA,),
            inspection_prompt=MARKETING_INSPECTION,
        )

    # --- Conflict #2 ---

    def comparison_2(advance):
        def on_complete(interpretation):
            collected["comparison_2_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l02.comparison2.title",
            narrative_keys=("dialogue.l02_comparison2.line1", "dialogue.l02_comparison2.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l02.evidence.billing_active_label",
                    float(billing_active_count(billing)),
                    python_code="(billing.status == 'active').sum()",
                ),
                ComparisonValue(
                    "lesson.l02.evidence.marketing_enrolled_label",
                    float(marketing_enrolled_count(marketing)),
                    python_code=(
                        "marketing = pd.read_csv('crm_plus_enrollment_export.csv')\nmarketing.customer_id.nunique()"
                    ),
                ),
            ),
            interpret_prompt_key="lesson.l02.comparison2_interpret.prompt",
            interpret_options=COMPARISON_2_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    # --- The Real Gap ---

    def gap_discovery(advance):
        def on_complete(interpretation):
            collected["gap_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        counts = missing_from_billing_counts(marketing, billing)
        return ComparisonRevealScene(
            app,
            title_key="lesson.l02.gap.title",
            narrative_keys=("dialogue.l02_gap.line1", "dialogue.l02_gap.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l02.evidence.legacy_missing_label",
                    float(counts.get("legacypay", 0)),
                    python_code=(
                        "missing = marketing[~marketing.customer_id.isin(billing.customer_id)]\n"
                        "missing.payment_processor.value_counts()['legacypay']"
                    ),
                ),
                ComparisonValue(
                    "lesson.l02.evidence.trial_pending_missing_label",
                    float(counts.get("trial_pending", 0)),
                    python_code="missing.payment_processor.value_counts()['trial_pending']",
                ),
            ),
            interpret_prompt_key="lesson.l02.gap_interpret.prompt",
            interpret_options=GAP_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    def finance_lead_confirms(advance):
        def on_complete():
            _sync_context_into_collected()
            advance()

        return DialogueScene(
            app,
            FINANCE_LEAD_DIALOGUE,
            on_complete=on_complete,
            context=context,
            record_label_key="dialogue.l02_finance_lead.line2",
            record_evidence_key="lesson.l02.evidence.legacy_status_unresolved_label",
            record_key="legacy_status_unresolved",
        )

    def gut_check(advance):
        def on_complete(brief):
            collected["revision_choice"] = brief["revision_choice"]
            advance()

        return BriefBuilderScene(app, "lesson.l02.revision.title", (REVISION_FIELD,), on_complete, guided=False)

    # --- Support's List ---

    def support_list(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        raw_legacypay, unique_legacypay = support_legacypay_counts(support)
        return ComparisonRevealScene(
            app,
            title_key="lesson.l02.support.title",
            narrative_keys=("dialogue.l02_support.line1", "dialogue.l02_support.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l02.evidence.support_raw_label",
                    float(raw_legacypay),
                    python_code=(
                        "support = pd.read_excel('customer_success_vip_list.xlsx')\n"
                        "legacy_rows = support[support.payment_processor == 'legacypay']\n"
                        "len(legacy_rows)"
                    ),
                ),
                ComparisonValue(
                    "lesson.l02.evidence.support_unique_label",
                    float(unique_legacypay),
                    python_code="legacy_rows.customer_id.nunique()",
                ),
            ),
            interpret_prompt_key="lesson.l02.support_interpret.prompt",
            interpret_options=SUPPORT_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    # --- Evidence Review ---

    def evidence_review(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            billing,  # the dataset with the most real interactive history behind it (Compute Billing's own groupby)
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
            "lesson.l02.decision_title",
            steps=(
                ANSWER_STRATEGY_FIELD,
                DECISION_EVIDENCE_FIELD,
                KNOWN_GAP_FIELD,
                SAFE_TO_CLAIM_FIELD,
                NOT_SAFE_TO_CLAIM_FIELD,
                RECOMMENDATION_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery Challenge ---

    def mastery_challenge(advance):
        def on_complete(engaged, metric_key, interpretation_key):
            collected["mastery_engaged"] = engaged
            collected["mastery_metric"] = metric_key
            collected["mastery_interpretation"] = interpretation_key
            _sync_context_into_collected()
            advance()

        def compute(metric_key: str) -> tuple[tuple[str, float], tuple[str, float]]:
            _, unique_legacypay = support_legacypay_counts(support)
            if metric_key == "raw_counts":
                return (
                    ("lesson.l02.mastery.support_count_label", float(unique_legacypay)),
                    ("lesson.l02.mastery.population_count_label", float(len(LEGACYPAY))),
                )
            return (
                ("lesson.l02.mastery.support_share_label", support_legacypay_share(support)),
                ("lesson.l02.mastery.population_share_label", population_legacypay_share(marketing)),
            )

        def format_value(value: float) -> str:
            # "raw_counts" values are always >=14 here; "proportions"
            # values are always a 0-1 share - safe to key formatting off
            # magnitude for this specific pair of metrics, not a general
            # percentage-vs-count heuristic meant to generalize further.
            return f"{value:.0%}" if value <= 1 else f"{value:,.0f}"

        return MasteryChallengeScene(
            app,
            title_key="lesson.l02.mastery.title",
            narrative_keys=("dialogue.l02_mastery.line1", "dialogue.l02_mastery.line2"),
            metric_prompt_key="lesson.l02.mastery.metric_prompt",
            metric_options=MASTERY_METRIC_OPTIONS,
            compute=compute,
            interpret_prompt_key="lesson.l02.mastery.interpret_prompt",
            interpret_options=MASTERY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=format_value,
        )

    # --- Feedback / Debrief ---

    def _build_result() -> LessonTwoResult:
        # A plain function, not something stashed in `collected` - see
        # l01_question_first/scenario.py's own _build_result for why
        # (LessonRunner checkpoints `collected` via json.dumps, and
        # neither LessonTwoResult nor LessonEvaluation is serializable).
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))
        return LessonTwoResult(
            initial_inspect_pick=collected.get("initial_inspect_pick", ""),
            comparison_1_interpretation=collected.get("comparison_1_interpretation", ""),
            comparison_2_interpretation=collected.get("comparison_2_interpretation", ""),
            gap_interpretation=collected.get("gap_interpretation", ""),
            revision_choice=collected.get("revision_choice", ""),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(context, selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_02.number, 0)
        evaluation = score_lesson_two(result, LESSON_02, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        framing,
        source_map,
        meet_billing,
        compute_billing,
        meet_app_log,
        comparison_1,
        meet_marketing,
        comparison_2,
        gap_discovery,
        finance_lead_confirms,
        gut_check,
        support_list,
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
        lesson_number=2,
        collected=collected,
        definition=LESSON_02,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
