from collections.abc import Callable

from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.sampling import SamplingGroup
from data_science_arcade.lessons.l05_sampling_mission.definition import LESSON_05
from data_science_arcade.lessons.l05_sampling_mission.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    LessonFiveResult,
    round_quality,
    score_lesson_five,
)
from data_science_arcade.lessons.l05_sampling_mission.twist_data import (
    draw_sample,
    estimated_problem_rate,
    frame_for,
    generate_population,
    region_availability,
    round1_mechanism,
    rural_share,
    sample_dataset,
    sample_python_code,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene, MasteryOption, MetricValue
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

BUDGET = 80
ALLOCATOR_STEP = 5
# Fixed seeds for the two system-driven SRS draws (Reveals 2 & 3) - hand-
# verified via a scratchpad script so both are real and neither is a
# knife-edge case: seed 2 draws 0 of the 15 Rural-synced rows, seed 29
# draws 4 of them - two honest draws, two different real numbers, from the
# identical design. See test_lesson05_twist_data.py's own seed-search
# coverage for the values this pair was chosen from.
SRS_SEED_A = 2
SRS_SEED_B = 29
# Separate seeds for whenever the player freely picks simple_random in
# Round 1 or Round 4 - distinct from the fixed A/B pair above, which
# always shows the same two system-driven draws regardless of player
# choice.
ROUND1_SRS_SEED = 7
ROUND4_SRS_SEED = 17
STRATIFIED_SEED = 13
REGIONS = ("metro", "suburban", "coastal", "rural")

# --- The Ask -----------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l05_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l05_briefing.line2"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l05_briefing.line3"),
    )
)

FRAMING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_framing.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_framing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_framing.line3"),
    )
)

# --- The four real root-cause dialogue variants, chosen by which real
# mechanism Round 1's own frame+strategy pick actually produced (see
# twist_data.round1_mechanism) - self-selection has two distinct concrete
# tellings (outcome-based vs regional/satisfaction-based), even though
# they share one abstract label for scoring purposes. -------------------

ROOT_CAUSE_SELF_SELECTION_TICKETS_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_tickets.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_tickets.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_pivot.line1"),
    )
)

ROOT_CAUSE_SELF_SELECTION_LOYALTY_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_loyalty.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_loyalty.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_pivot.line1"),
    )
)

ROOT_CAUSE_FRAME_COVERAGE_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_coverage.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_coverage.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_pivot.line1"),
    )
)

ROOT_CAUSE_DRAW_ORDER_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_order.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_order.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l05_root_cause_pivot.line1"),
    )
)

_ROOT_CAUSE_DIALOGUES: dict[str, Dialogue] = {
    "support_tickets": ROOT_CAUSE_SELF_SELECTION_TICKETS_DIALOGUE,
    "loyalty_app": ROOT_CAUSE_SELF_SELECTION_LOYALTY_DIALOGUE,
}


_TRACKING_EXPORT_ROOT_CAUSE_DIALOGUES = {
    "draw_order_bias": ROOT_CAUSE_DRAW_ORDER_DIALOGUE,
    "frame_coverage_gap": ROOT_CAUSE_FRAME_COVERAGE_DIALOGUE,
}


def _root_cause_dialogue(frame_key: str, strategy_key: str) -> Dialogue:
    if frame_key in _ROOT_CAUSE_DIALOGUES:
        return _ROOT_CAUSE_DIALOGUES[frame_key]
    return _TRACKING_EXPORT_ROOT_CAUSE_DIALOGUES[round1_mechanism(frame_key, strategy_key)]


DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_debrief.line2"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l05_debrief.line3"),
    )
)

# --- Round design fields (Frame + Strategy), reused for both Round 1
# (both fields) and Round 4 (Strategy only, frame fixed to the tracking
# export) - a real free pick each time, never scripted. --------------

FRAME_FIELD = BriefField(
    key="frame",
    prompt_key="lesson.l05.field.frame.prompt",
    options=(
        # tracking_export deliberately isn't index 0 - ButtonGroup defaults
        # keyboard focus to the first enabled button, and this is the one
        # field where a single option is unconditionally the best pick, so
        # index-0 correctness would silently pre-highlight the answer
        # before the player touches anything (the exact L04 default-focus
        # bug, fixed there by varying correct-option position).
        BriefOption("support_tickets", "lesson.l05.option.frame.support_tickets"),
        BriefOption("tracking_export", "lesson.l05.option.frame.tracking_export"),
        BriefOption("loyalty_app", "lesson.l05.option.frame.loyalty_app"),
    ),
)

STRATEGY_FIELD = BriefField(
    key="strategy",
    prompt_key="lesson.l05.field.strategy.prompt",
    options=(
        BriefOption("convenience", "lesson.l05.option.strategy.convenience"),
        BriefOption("simple_random", "lesson.l05.option.strategy.simple_random"),
        BriefOption("stratified", "lesson.l05.option.strategy.stratified"),
    ),
)

ROUND1_TIERED_HINTS = {
    "frame": (
        "lesson.l05.hint.population_vs_frame.tier1",
        "lesson.l05.hint.population_vs_frame.tier2",
        "lesson.l05.hint.population_vs_frame.tier3",
    ),
    "strategy": (
        "lesson.l05.hint.random_from_biased_frame.tier1",
        "lesson.l05.hint.random_from_biased_frame.tier2",
        "lesson.l05.hint.random_from_biased_frame.tier3",
    ),
}

ROUND4_TIERED_HINTS = {
    "strategy": (
        "lesson.l05.hint.when_stratification_helps.tier1",
        "lesson.l05.hint.when_stratification_helps.tier2",
        "lesson.l05.hint.when_stratification_helps.tier3",
    ),
}

# --- The three real bias mechanisms (see twist_data.round1_mechanism),
# shared - same vocabulary, same order - by Prediction 1's field and by
# Reveal 1/2/4's own interpret step (predict, then confirm). -------------

_MECHANISM_LABELS: dict[str, str] = {
    "self_selection": "lesson.l05.mechanism.self_selection",
    "frame_coverage_gap": "lesson.l05.mechanism.frame_coverage_gap",
    "draw_order_bias": "lesson.l05.mechanism.draw_order_bias",
    "looks_solid": "lesson.l05.mechanism.looks_solid",
}

PREDICTION_1_FIELD = BriefField(
    key="prediction1",
    prompt_key="lesson.l05.field.prediction1.prompt",
    options=tuple(BriefOption(key, label) for key, label in _MECHANISM_LABELS.items()),
)

MECHANISM_INTERPRET_OPTIONS = tuple(InterpretOption(key, label) for key, label in _MECHANISM_LABELS.items())

PREDICTION_2_FIELD = BriefField(
    key="prediction2",
    prompt_key="lesson.l05.field.prediction2.prompt",
    options=(
        BriefOption("fully_fixed", "lesson.l05.option.prediction2.fully_fixed"),
        BriefOption("frame_ceiling_remains", "lesson.l05.option.prediction2.frame_ceiling_remains"),
        BriefOption("wont_help", "lesson.l05.option.prediction2.wont_help"),
        BriefOption("allocation_amount_only", "lesson.l05.option.prediction2.allocation_amount_only"),
    ),
)

# consistent_with_chance is always the correct read here (Reveal 3 always
# compares the same two fixed, system-driven draws) - not index 0, for the
# same default-focus reason every fixed-answer field above isn't either.
VARIABILITY_INTERPRET_OPTIONS = (
    InterpretOption("bigger_sample_would_match", "lesson.l05.option.variability.bigger_sample_would_match"),
    InterpretOption("one_must_be_wrong", "lesson.l05.option.variability.one_must_be_wrong"),
    InterpretOption("consistent_with_chance", "lesson.l05.option.variability.consistent_with_chance"),
    InterpretOption("design_must_be_flawed", "lesson.l05.option.variability.design_must_be_flawed"),
)

# --- Final Decision ------------------------------------------------------

# Every field below has exactly one objectively correct answer regardless
# of which draws the player actually ran (see scoring.py's module
# docstring) - so unlike Round 1's Frame/Strategy or the Reveal interpret
# steps, the correct option's *position* is deliberately never index 0 in
# any of them, matching the same real default-keyboard-focus bug L04 had
# to fix after the fact (ButtonGroup.__init__ defaults focus to the first
# enabled button, silently pre-highlighting an always-index-0 answer
# before the player has touched anything).

TARGET_POPULATION_FIELD = BriefField(
    key="target_population",
    prompt_key="lesson.l05.decision.target_population.prompt",
    options=(
        BriefOption("contacted_support", "lesson.l05.decision.target_population.option.contacted_support"),
        BriefOption("all_deliveries", "lesson.l05.decision.target_population.option.all_deliveries"),
        BriefOption("carrierco_only", "lesson.l05.decision.target_population.option.carrierco_only"),
        BriefOption("however_many_in_frame", "lesson.l05.decision.target_population.option.however_many_in_frame"),
    ),
)

SAMPLING_DESIGN_FIELD = BriefField(
    key="sampling_design",
    prompt_key="lesson.l05.decision.sampling_design.prompt",
    options=(
        BriefOption("keep_tickets_bigger", "lesson.l05.decision.sampling_design.option.keep_tickets_bigger"),
        BriefOption("average_everything", "lesson.l05.decision.sampling_design.option.average_everything"),
        BriefOption("stratified_export", "lesson.l05.decision.sampling_design.option.stratified_export"),
        BriefOption("simple_random_export", "lesson.l05.decision.sampling_design.option.simple_random_export"),
    ),
)

ESTIMATE_TO_REPORT_FIELD = BriefField(
    key="estimate_to_report",
    prompt_key="lesson.l05.decision.estimate_to_report.prompt",
    options=(
        BriefOption("tickets_biggest", "lesson.l05.decision.estimate_to_report.option.tickets_biggest"),
        BriefOption("average_every_draw", "lesson.l05.decision.estimate_to_report.option.average_every_draw"),
        BriefOption(
            "no_number_until_full_audit", "lesson.l05.decision.estimate_to_report.option.no_number_until_full_audit"
        ),
        BriefOption("best_design_scoped", "lesson.l05.decision.estimate_to_report.option.best_design_scoped"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l05.decision.evidence.prompt",
    min_count=2,
    max_count=3,
)

LIMITATION_FIELD = BriefField(
    key="limitation",
    prompt_key="lesson.l05.decision.limitation.prompt",
    options=(
        BriefOption("metro_over_surveyed", "lesson.l05.decision.limitation.option.metro_over_surveyed"),
        BriefOption(
            "no_one_fully_representative", "lesson.l05.decision.limitation.option.no_one_fully_representative"
        ),
        BriefOption("rural_quickship_gap", "lesson.l05.decision.limitation.option.rural_quickship_gap"),
        BriefOption(
            "every_region_equally_untrustworthy",
            "lesson.l05.decision.limitation.option.every_region_equally_untrustworthy",
        ),
    ),
)

CLAIM_SCOPE_FIELD = BriefField(
    key="claim_scope",
    prompt_key="lesson.l05.decision.claim_scope.prompt",
    options=(
        BriefOption("whole_company_one_rate", "lesson.l05.decision.claim_scope.option.whole_company_one_rate"),
        BriefOption("carrierco_regions_scoped", "lesson.l05.decision.claim_scope.option.carrierco_regions_scoped"),
        BriefOption(
            "company_wide_some_uncertainty", "lesson.l05.decision.claim_scope.option.company_wide_some_uncertainty"
        ),
        BriefOption("no_claim_until_full_audit", "lesson.l05.decision.claim_scope.option.no_claim_until_full_audit"),
    ),
)

NEXT_IMPROVEMENT_FIELD = BriefField(
    key="next_improvement",
    prompt_key="lesson.l05.decision.next_improvement.prompt",
    options=(
        BriefOption("more_budget_same_frame", "lesson.l05.decision.next_improvement.option.more_budget_same_frame"),
        BriefOption("switch_to_tickets_free", "lesson.l05.decision.next_improvement.option.switch_to_tickets_free"),
        BriefOption("nothing_needed", "lesson.l05.decision.next_improvement.option.nothing_needed"),
        BriefOption("sync_quickship_log", "lesson.l05.decision.next_improvement.option.sync_quickship_log"),
    ),
)

# --- Optional Mastery: transfer to a new question the core design was
# never deliberately built to answer ---------------------------------

MASTERY_METRIC_OPTIONS = (
    MasteryOption("stratified_sample", "lesson.l05.mastery.metric.stratified_sample"),
    MasteryOption("tracking_export", "lesson.l05.mastery.metric.tracking_export"),
)

MASTERY_INTERPRET_OPTIONS = (
    MasteryOption("needs_own_stratification", "lesson.l05.mastery.interpret.needs_own_stratification"),
    MasteryOption("trust_existing_sample", "lesson.l05.mastery.interpret.trust_existing_sample"),
    MasteryOption("behaves_like_everyone_else", "lesson.l05.mastery.interpret.behaves_like_everyone_else"),
    MasteryOption("more_budget_would_fix", "lesson.l05.mastery.interpret.more_budget_would_fix"),
)


# Every real option-bearing BriefField in this lesson, regardless of
# whether BriefBuilderScene or DecisionBuilderScene ends up rendering it -
# both scenes share the identical 420x46 OPTION_SIZE, and
# tests/test_option_label_widths.py checks every lesson's own
# DECISION_FIELDS the same way (a convention every lesson from L06 onward
# already follows).
DECISION_FIELDS: tuple[BriefField, ...] = (
    FRAME_FIELD,
    STRATEGY_FIELD,
    PREDICTION_1_FIELD,
    PREDICTION_2_FIELD,
    TARGET_POPULATION_FIELD,
    SAMPLING_DESIGN_FIELD,
    ESTIMATE_TO_REPORT_FIELD,
    LIMITATION_FIELD,
    CLAIM_SCOPE_FIELD,
    NEXT_IMPROVEMENT_FIELD,
)


class _DesignThenAllocateScene(Scene):
    """One LessonRunner stage that runs a design pick (BriefBuilderScene:
    Frame(+Strategy) or Strategy alone) then, only if the picked strategy
    is "stratified", a SamplingAllocatorScene for the real per-region
    budget split - a single advance()-equivalent call at the true end
    either way.

    Needed because LessonRunner's own stage list (and the checkpoint
    fingerprint derived from it) is fixed once, at runner-construction
    time, before any player choice exists - a stage that only sometimes
    appears can't be represented as a second, conditionally-included item
    in that list. This is the same problem MasteryChallengeScene's own
    internal OFFER/PICK/RESULT phases already solve for themselves, here
    generalized to wrap two already-existing, unmodified scenes instead of
    building bespoke phases from scratch."""

    def __init__(
        self,
        app,
        build_design: Callable[[Callable[[dict], None]], Scene],
        build_allocator: Callable[[dict, Callable[[dict], None]], Scene],
        on_complete: Callable[[dict, dict | None], None],
    ) -> None:
        super().__init__(app)
        self._build_allocator = build_allocator
        self._on_complete = on_complete
        self._design_choices: dict | None = None
        self._active: Scene = build_design(self._on_design_complete)

    def __getattr__(self, name: str):
        # Transparent proxying to whichever sub-scene is currently active
        # (the design pick, or the allocator once it's showing) - the same
        # "callers mostly don't need to know they're holding a wrapper"
        # pattern core/scenes.py's own Pausable already established, so
        # e.g. a test driving `.buttons`/`.next_button` doesn't need to
        # know which of the two real scenes is live at a given moment.
        return getattr(self._active, name)

    def _on_design_complete(self, choices: dict) -> None:
        self._design_choices = choices
        if choices.get("strategy") == "stratified":
            self._active = self._build_allocator(choices, self._on_allocation_complete)
        else:
            self._on_complete(choices, None)

    def _on_allocation_complete(self, allocation: dict) -> None:
        assert self._design_choices is not None
        self._on_complete(self._design_choices, allocation)

    def on_enter(self) -> None:
        self._active.on_enter()

    def on_exit(self) -> None:
        self._active.on_exit()

    def handle_event(self, event) -> None:
        self._active.handle_event(event)

    def draw(self, surface) -> None:
        self._active.draw(surface)


def build_lesson_five_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 05's real investigation: one hidden 960-delivery
    population, seen only through whichever sampling frame+strategy the
    player picks. Two free design rounds (Round 1: Frame+Strategy, a real
    temptation toward the free-but-badly-biased complaint list; Round 4:
    Strategy only, frame fixed to the best available list) bracket two
    system-driven reference draws (Reveals 2-3: the same design, drawn
    twice with different seeds, the sampling-variability beat) - four real
    seeded draws total, never a scripted composition. LessonContext is
    threaded through every analytical stage exactly like L01-L04; unlike
    L04, the Final Decision's correct answers are fixed (not branched on
    student state) since the hidden population and its three frames never
    change based on what the player did in the interactive rounds - L04's
    own Event A state genuinely varied because the *student's own spec*
    determined what its twist dataset looked like, which has no analogue
    here."""
    collected: dict = {}
    context = LessonContext()
    population = generate_population().frame

    def _restore_context_if_present() -> None:
        saved = collected.get("analytical_context")
        if saved is not None:
            context.restore_from_dict(saved)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    def _draw_for(frame_key: str, strategy_key: str, seed: int, allocation: dict | None):
        """Returns (sample, frame) - callers need the frame itself, not
        just the drawn sample, to correctly reweight a stratified draw's
        own estimate (see twist_data.estimated_problem_rate)."""
        frame = frame_for(population, frame_key)
        costed = frame_key == "tracking_export"
        sample = draw_sample(frame, strategy_key, BUDGET, costed=costed, seed=seed, allocation=allocation)
        return sample, frame

    def _estimate_for(sample, frame, strategy_key: str) -> float:
        """Only a stratified draw needs its own frame to reweight by -
        convenience/simple_random already give every row an equal chance,
        so a plain mean is already the correct estimator there."""
        return estimated_problem_rate(sample, frame=frame if strategy_key == "stratified" else None)

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def framing(advance):
        return DialogueScene(app, FRAMING_DIALOGUE, on_complete=advance)

    # --- Round 1: Frame + Strategy, a real free pick ---

    def round1_design(advance):
        def build_design(on_complete):
            return BriefBuilderScene(
                app,
                "lesson.l05.round1_title",
                (FRAME_FIELD, STRATEGY_FIELD),
                on_complete,
                guided=True,
                tiered_hint_keys=ROUND1_TIERED_HINTS,
            )

        def build_allocator(choices, on_complete):
            frame = frame_for(population, choices["frame"])
            availability = region_availability(frame)
            groups = tuple(
                SamplingGroup(region, f"lesson.l05.region.{region}", available=availability.get(region, 0))
                for region in REGIONS
                if availability.get(region, 0) > 0
            )
            return SamplingAllocatorScene(
                app,
                "lesson.l05.allocator_title",
                "lesson.l05.allocator_prompt",
                groups,
                BUDGET,
                ALLOCATOR_STEP,
                on_complete,
                guided=True,
                hint_key="lesson.l05.allocator_hint",
            )

        def on_complete(choices, allocation):
            collected["round1_choice"] = choices
            collected["round1_allocation"] = allocation
            advance()

        return _DesignThenAllocateScene(app, build_design, build_allocator, on_complete)

    def prediction1(advance):
        def on_complete(brief):
            collected["prediction1"] = brief["prediction1"]
            advance()

        return BriefBuilderScene(app, "lesson.l05.prediction1_title", (PREDICTION_1_FIELD,), on_complete, guided=True)

    def reveal1(advance):
        choice = collected.get("round1_choice", {})
        frame_key, strategy_key = choice.get("frame", "tracking_export"), choice.get("strategy", "convenience")
        allocation = collected.get("round1_allocation")
        seed = STRATIFIED_SEED if strategy_key == "stratified" else ROUND1_SRS_SEED
        sample, frame = _draw_for(frame_key, strategy_key, seed, allocation)
        code = sample_python_code(frame_key, strategy_key, BUDGET, seed, allocation)

        def on_complete(interpretation):
            collected["reveal1_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l05.reveal1.title",
            narrative_keys=("dialogue.l05_reveal1.line1", "dialogue.l05_reveal1.line2"),
            comparisons=(
                ComparisonValue("lesson.l05.reveal1.rural_share_label", rural_share(sample), python_code=code),
                ComparisonValue("lesson.l05.reveal1.estimate_label", _estimate_for(sample, frame, strategy_key)),
            ),
            interpret_prompt_key="lesson.l05.reveal1.interpret_prompt",
            interpret_options=MECHANISM_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Root cause: names the real mechanism, then pivots to "let's also
    # see a plain random draw from the fullest list" ---

    def root_cause(advance):
        choice = collected.get("round1_choice", {})
        dialogue = _root_cause_dialogue(choice.get("frame", "tracking_export"), choice.get("strategy", "convenience"))
        return DialogueScene(app, dialogue, on_complete=advance, context=context)

    # --- Reveals 2 & 3: system-driven, same design, two different seeds -
    # the sampling-variability beat ---

    def reveal2(advance):
        sample, frame = _draw_for("tracking_export", "simple_random", SRS_SEED_A, None)
        collected["reveal2_estimate"] = _estimate_for(sample, frame, "simple_random")
        code = sample_python_code("tracking_export", "simple_random", BUDGET, SRS_SEED_A, None)

        def on_complete(interpretation):
            collected["reveal2_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l05.reveal2.title",
            narrative_keys=("dialogue.l05_reveal2.line1", "dialogue.l05_reveal2.line2"),
            comparisons=(
                ComparisonValue("lesson.l05.reveal2.rural_share_label", rural_share(sample), python_code=code),
                ComparisonValue("lesson.l05.reveal2.estimate_label", collected["reveal2_estimate"]),
            ),
            interpret_prompt_key="lesson.l05.reveal2.interpret_prompt",
            interpret_options=MECHANISM_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    def reveal3(advance):
        sample_a, frame_a = _draw_for("tracking_export", "simple_random", SRS_SEED_A, None)
        sample_b, frame_b = _draw_for("tracking_export", "simple_random", SRS_SEED_B, None)
        code_a = sample_python_code("tracking_export", "simple_random", BUDGET, SRS_SEED_A, None)
        code_b = sample_python_code("tracking_export", "simple_random", BUDGET, SRS_SEED_B, None)

        def on_complete(interpretation):
            collected["reveal3_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l05.reveal3.title",
            narrative_keys=("dialogue.l05_reveal3.line1", "dialogue.l05_reveal3.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l05.reveal3.draw_a_label", _estimate_for(sample_a, frame_a, "simple_random"), python_code=code_a
                ),
                ComparisonValue(
                    "lesson.l05.reveal3.draw_b_label", _estimate_for(sample_b, frame_b, "simple_random"), python_code=code_b
                ),
            ),
            interpret_prompt_key="lesson.l05.reveal3.interpret_prompt",
            interpret_options=VARIABILITY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Round 4: Strategy only, frame fixed to the tracking export ---

    def round4_design(advance):
        def build_design(on_complete):
            return BriefBuilderScene(
                app,
                "lesson.l05.round4_title",
                (STRATEGY_FIELD,),
                on_complete,
                guided=True,
                tiered_hint_keys=ROUND4_TIERED_HINTS,
            )

        def build_allocator(_choices, on_complete):
            frame = frame_for(population, "tracking_export")
            availability = region_availability(frame)
            groups = tuple(
                SamplingGroup(region, f"lesson.l05.region.{region}", available=availability.get(region, 0))
                for region in REGIONS
                if availability.get(region, 0) > 0
            )
            return SamplingAllocatorScene(
                app,
                "lesson.l05.allocator_title",
                "lesson.l05.allocator_prompt",
                groups,
                BUDGET,
                ALLOCATOR_STEP,
                on_complete,
                guided=True,
                hint_key="lesson.l05.allocator_hint",
            )

        def on_complete(choices, allocation):
            collected["round4_choice"] = choices
            collected["round4_allocation"] = allocation
            advance()

        return _DesignThenAllocateScene(app, build_design, build_allocator, on_complete)

    def prediction2(advance):
        def on_complete(brief):
            collected["prediction2"] = brief["prediction2"]
            advance()

        return BriefBuilderScene(app, "lesson.l05.prediction2_title", (PREDICTION_2_FIELD,), on_complete, guided=True)

    def reveal4(advance):
        choice = collected.get("round4_choice", {})
        strategy_key = choice.get("strategy", "convenience")
        allocation = collected.get("round4_allocation")
        seed = STRATIFIED_SEED if strategy_key == "stratified" else ROUND4_SRS_SEED
        sample, frame = _draw_for("tracking_export", strategy_key, seed, allocation)
        code = sample_python_code("tracking_export", strategy_key, BUDGET, seed, allocation)

        def on_complete(interpretation):
            collected["reveal4_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l05.reveal4.title",
            narrative_keys=("dialogue.l05_reveal4.line1", "dialogue.l05_reveal4.line2"),
            comparisons=(
                ComparisonValue("lesson.l05.reveal4.rural_share_label", rural_share(sample), python_code=code),
                ComparisonValue("lesson.l05.reveal4.estimate_label", _estimate_for(sample, frame, strategy_key)),
            ),
            interpret_prompt_key="lesson.l05.reveal4.interpret_prompt",
            interpret_options=MECHANISM_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
        )

    # --- Evidence review: the final round's own draw, plus everything
    # accumulated so far ---

    def evidence_review(advance):
        choice = collected.get("round4_choice", {})
        strategy_key = choice.get("strategy", "convenience")
        allocation = collected.get("round4_allocation")
        seed = STRATIFIED_SEED if strategy_key == "stratified" else ROUND4_SRS_SEED
        sample, _frame = _draw_for("tracking_export", strategy_key, seed, allocation)
        dataset = sample_dataset(
            sample, "audit_sample", sample_python_code("tracking_export", strategy_key, BUDGET, seed, allocation)
        )

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
            "lesson.l05.decision_title",
            steps=(
                TARGET_POPULATION_FIELD,
                SAMPLING_DESIGN_FIELD,
                ESTIMATE_TO_REPORT_FIELD,
                DECISION_EVIDENCE_FIELD,
                LIMITATION_FIELD,
                CLAIM_SCOPE_FIELD,
                NEXT_IMPROVEMENT_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery: transfer to an Express-specific question ---

    def mastery_challenge(advance):
        round4_choice = collected.get("round4_choice", {})
        round4_strategy = round4_choice.get("strategy", "convenience")
        round4_allocation = collected.get("round4_allocation")
        round4_seed = STRATIFIED_SEED if round4_strategy == "stratified" else ROUND4_SRS_SEED
        stratified_sample, _frame = _draw_for("tracking_export", round4_strategy, round4_seed, round4_allocation)
        export_frame = frame_for(population, "tracking_export")

        def on_complete(engaged, metric_key, interpretation_key):
            collected["mastery_engaged"] = engaged
            collected["mastery_metric"] = metric_key
            collected["mastery_interpretation"] = interpretation_key
            _sync_context_into_collected()
            advance()

        def compute(metric_key: str) -> tuple[MetricValue, MetricValue]:
            sample = stratified_sample if metric_key == "stratified_sample" else export_frame
            express = sample[sample["is_express"]]
            non_express = sample[~sample["is_express"]]
            return (
                MetricValue("lesson.l05.mastery.express_n_label", float(len(express))),
                MetricValue("lesson.l05.mastery.non_express_n_label", float(len(non_express))),
            )

        return MasteryChallengeScene(
            app,
            title_key="lesson.l05.mastery.title",
            narrative_keys=("dialogue.l05_mastery.line1", "dialogue.l05_mastery.line2"),
            metric_prompt_key="lesson.l05.mastery.metric_prompt",
            metric_options=MASTERY_METRIC_OPTIONS,
            compute=compute,
            interpret_prompt_key="lesson.l05.mastery.interpret_prompt",
            interpret_options=MASTERY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
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

    def _build_result() -> LessonFiveResult:
        round1_choice = collected.get("round1_choice", {})
        round4_choice = collected.get("round4_choice", {})
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))
        round1_frame = round1_choice.get("frame", "")
        round1_strategy = round1_choice.get("strategy", "")
        round4_strategy = round4_choice.get("strategy", "")

        round1_availability = region_availability(frame_for(population, round1_frame)) if round1_frame else {}
        round4_availability = region_availability(frame_for(population, "tracking_export"))

        return LessonFiveResult(
            round1_frame=round1_frame,
            round1_strategy=round1_strategy,
            round4_strategy=round4_strategy,
            prediction1=collected.get("prediction1", ""),
            prediction2=collected.get("prediction2", ""),
            reveal1_interpretation=collected.get("reveal1_interpretation", ""),
            reveal2_interpretation=collected.get("reveal2_interpretation", ""),
            reveal3_interpretation=collected.get("reveal3_interpretation", ""),
            reveal4_interpretation=collected.get("reveal4_interpretation", ""),
            decision=decision,
            round1_quality=round_quality(
                round1_frame, round1_strategy, collected.get("round1_allocation"), round1_availability
            ),
            round4_quality=round_quality(
                "tracking_export", round4_strategy, collected.get("round4_allocation"), round4_availability
            ),
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_metric=collected.get("mastery_metric") or "",
            mastery_interpretation=collected.get("mastery_interpretation") or "",
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_05.number, 0)
        evaluation = score_lesson_five(result, LESSON_05, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        framing,
        round1_design,
        prediction1,
        reveal1,
        root_cause,
        reveal2,
        reveal3,
        round4_design,
        prediction2,
        reveal4,
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
        lesson_number=5,
        collected=collected,
        definition=LESSON_05,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
