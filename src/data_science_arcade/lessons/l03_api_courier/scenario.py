from data_science_arcade.lessons.framework.api import APIRequestAttempt, ContinuationOption
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l03_api_courier.definition import LESSON_03
from data_science_arcade.lessons.l03_api_courier.scoring import CRITICAL_EVIDENCE_KEYS, LessonThreeResult, score_lesson_three
from data_science_arcade.lessons.l03_api_courier.twist_data import (
    BEST_ACHIEVABLE_TOTAL,
    MASTERY_PAGE_SIZE,
    MASTERY_RECEIVED_TOTAL,
    MASTERY_TOTAL_COUNT,
    PAGE_SIZE,
    RATE_LIMITED_PAGE,
    SHORTFALL_ACTUAL,
    SHORTFALL_PAGE,
    TOTAL_COUNT,
    generate_pages,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene, MasteryOption, MetricValue
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask --------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l03_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l03_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l03_briefing.line3"),
    )
)

FRAMING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_framing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_framing.line2"),
    )
)

ROOT_CAUSE_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_root_cause.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_root_cause.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l03_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l03_debrief.line2"),
    )
)

# --- The Acquisition --------------------------------------------------------
#
# Two real branch trees, both built inside-out (the narrowest/final offer
# defined first, each wrapped by the choice that can reach it):
#
# 1. Page 1's own response offers a real, non-failure pagination choice -
#    follow the real next_cursor (the only path that actually reaches new
#    data) or resend the same request (a real, honest dead end: the same
#    page comes back, not a punishment, just not progress - resolves to a
#    single remaining "follow next_cursor" offer rather than repeating the
#    same 2-choice trap forever). Page 2's own data lives inside this tree
#    (as the "follow_cursor" outcome), not as its own top-level attempts
#    slot - every later page continues normally from there.
# 2. Page 5's rate limit offers the real failure choice (retry immediately
#    - fails again, then narrows to 2; wait and retry; or skip, leaving a
#    real, silent hole has_more still tracks as if the page were never
#    attempted).
#
# Every real attempt (successful or not) carries the same TOTAL_COUNT once
# it exists, matching real paginated APIs that report a query's total on
# every page rather than only the first.
RATE_LIMITED_STATUS = "api_console.status.rate_limited"
SKIPPED_STATUS = "api_console.status.skipped"

_PAGE1_FOLLOW_CURSOR = APIRequestAttempt(
    2, "api_console.status.ok", PAGE_SIZE, True, has_more=True, total_count=TOTAL_COUNT, next_cursor="page_3"
)
_PAGE1_RESEND = APIRequestAttempt(
    1,
    "api_console.status.ok",
    PAGE_SIZE,
    True,
    has_more=True,
    total_count=TOTAL_COUNT,
    next_cursor="page_2",
    continuation_options=(ContinuationOption("follow_cursor", "lesson.l03.continuation.follow_cursor", _PAGE1_FOLLOW_CURSOR),),
)
_PAGE1_INITIAL = APIRequestAttempt(
    1,
    "api_console.status.ok",
    PAGE_SIZE,
    True,
    has_more=True,
    total_count=TOTAL_COUNT,
    next_cursor="page_2",
    continuation_options=(
        ContinuationOption("follow_cursor", "lesson.l03.continuation.follow_cursor", _PAGE1_FOLLOW_CURSOR),
        ContinuationOption("resend", "lesson.l03.continuation.resend", _PAGE1_RESEND),
    ),
)

_PAGE5_WAIT_SUCCESS = APIRequestAttempt(
    RATE_LIMITED_PAGE, "api_console.status.ok", PAGE_SIZE, True, has_more=True, total_count=TOTAL_COUNT, next_cursor="page_6"
)
_PAGE5_SKIP = APIRequestAttempt(RATE_LIMITED_PAGE, SKIPPED_STATUS, 0, False, has_more=True, total_count=None)
_PAGE5_SECOND_RATE_LIMIT = APIRequestAttempt(
    RATE_LIMITED_PAGE,
    RATE_LIMITED_STATUS,
    0,
    False,
    has_more=True,
    total_count=None,
    continuation_options=(
        ContinuationOption("wait_and_retry", "lesson.l03.retry.wait_and_retry", _PAGE5_WAIT_SUCCESS),
        ContinuationOption("skip", "lesson.l03.retry.skip", _PAGE5_SKIP),
    ),
)
_PAGE5_INITIAL_RATE_LIMIT = APIRequestAttempt(
    RATE_LIMITED_PAGE,
    RATE_LIMITED_STATUS,
    0,
    False,
    has_more=True,
    total_count=None,
    continuation_options=(
        ContinuationOption("retry_immediately", "lesson.l03.retry.retry_immediately", _PAGE5_SECOND_RATE_LIMIT),
        ContinuationOption("wait_and_retry", "lesson.l03.retry.wait_and_retry", _PAGE5_WAIT_SUCCESS),
        ContinuationOption("skip", "lesson.l03.retry.skip", _PAGE5_SKIP),
    ),
)

REQUEST_ATTEMPTS: tuple[APIRequestAttempt, ...] = (
    _PAGE1_INITIAL,
    APIRequestAttempt(
        SHORTFALL_PAGE, "api_console.status.ok", SHORTFALL_ACTUAL, True, has_more=True, total_count=TOTAL_COUNT, next_cursor="page_4"
    ),
    APIRequestAttempt(4, "api_console.status.ok", PAGE_SIZE, True, has_more=True, total_count=TOTAL_COUNT, next_cursor="page_5"),
    _PAGE5_INITIAL_RATE_LIMIT,
    APIRequestAttempt(6, "api_console.status.ok", 12, True, has_more=False, total_count=TOTAL_COUNT),
)

# A real, if simplified, requests-shaped pagination loop: check the status
# before trusting the body, handle a 429 with one bounded wait using the
# server's own Retry-After, raise for any other real error, then walk
# next_cursor off the response's own nested pagination object rather than
# an ad hoc top-level field - matching the same shape APIConsoleScene's
# own response panel renders. The completeness check at the end is the
# same real comparison the completeness-reveal stage repeats live.
ACQUISITION_PYTHON_CODE = (
    "responses = []\n"
    "cursor = None\n"
    "while True:\n"
    "    response = requests.get('/api/orders/events', params={'cursor': cursor})\n"
    "    if response.status_code == 429:\n"
    "        time.sleep(int(response.headers.get('Retry-After', 5)))\n"
    "        response = requests.get('/api/orders/events', params={'cursor': cursor})\n"
    "    response.raise_for_status()\n"
    "    payload = response.json()\n"
    "    responses.append(payload)\n"
    "    if not payload['pagination']['has_more']:\n"
    "        break\n"
    "    cursor = payload['pagination']['next_cursor']\n"
    "\n"
    "received_total = sum(len(r['data']) for r in responses)\n"
    "received_total == responses[-1]['total_count']"
)

# --- Discovering incompleteness --------------------------------------------

INITIAL_GUT_CHECK_FIELD = BriefField(
    key="initial_gut_check",
    prompt_key="lesson.l03.gut_check.prompt",
    hint_key="lesson.l03.gut_check.hint",
    options=(
        BriefOption("yes_complete", "lesson.l03.gut_check.option.yes_complete"),
        BriefOption("not_sure", "lesson.l03.gut_check.option.not_sure"),
        BriefOption("probably_not", "lesson.l03.gut_check.option.probably_not"),
    ),
)

REVISED_GUT_CHECK_FIELD = BriefField(
    key="revised_gut_check",
    prompt_key="lesson.l03.revised_gut_check.prompt",
    options=(
        BriefOption("yes_still_fine", "lesson.l03.revised_gut_check.option.yes_still_fine"),
        BriefOption("no_would_flag_it", "lesson.l03.revised_gut_check.option.no_would_flag_it"),
    ),
)

COMPLETENESS_INTERPRET_OPTIONS = (
    InterpretOption("page_shortfall", "lesson.l03.completeness_interpret.option.page_shortfall"),
    InterpretOption("rate_limit_alone", "lesson.l03.completeness_interpret.option.rate_limit_alone"),
    InterpretOption("last_page_explains_it", "lesson.l03.completeness_interpret.option.last_page_explains_it"),
    InterpretOption("total_count_wrong", "lesson.l03.completeness_interpret.option.total_count_wrong"),
)

# --- Final Decision ---------------------------------------------------------

ACQUISITION_STRATEGY_FIELD = BriefField(
    key="acquisition_strategy",
    prompt_key="lesson.l03.decision.acquisition_strategy.prompt",
    options=(
        BriefOption("raw_no_caveat", "lesson.l03.decision.acquisition_strategy.option.raw_no_caveat"),
        BriefOption("floor_and_range", "lesson.l03.decision.acquisition_strategy.option.floor_and_range"),
        BriefOption("refuse_until_repull", "lesson.l03.decision.acquisition_strategy.option.refuse_until_repull"),
        BriefOption("discard_and_restart", "lesson.l03.decision.acquisition_strategy.option.discard_and_restart"),
    ),
)

DECISION_EVIDENCE_FIELD = EvidenceField(
    key="evidence",
    prompt_key="lesson.l03.decision.evidence.prompt",
    min_count=2,
    max_count=4,
)

KNOWN_GAP_FIELD = BriefField(
    key="known_gap",
    prompt_key="lesson.l03.decision.known_gap.prompt",
    options=(
        BriefOption("page_shortfall", "lesson.l03.decision.known_gap.option.page_shortfall"),
        BriefOption("page_shortfall_and_page5", "lesson.l03.decision.known_gap.option.page_shortfall_and_page5"),
        BriefOption("rate_limit_alone", "lesson.l03.decision.known_gap.option.rate_limit_alone"),
        BriefOption("nothing_missing", "lesson.l03.decision.known_gap.option.nothing_missing"),
        BriefOption("pagination_broken", "lesson.l03.decision.known_gap.option.pagination_broken"),
    ),
)

SAFE_TO_CLAIM_FIELD = BriefField(
    key="safe_to_claim",
    prompt_key="lesson.l03.decision.safe_to_claim.prompt",
    options=(
        BriefOption("floor_and_threshold_flag", "lesson.l03.decision.safe_to_claim.option.floor_and_threshold_flag"),
        BriefOption("exact_precision", "lesson.l03.decision.safe_to_claim.option.exact_precision"),
        BriefOption("nothing_usable", "lesson.l03.decision.safe_to_claim.option.nothing_usable"),
        BriefOption("gap_too_small", "lesson.l03.decision.safe_to_claim.option.gap_too_small"),
    ),
)

NOT_SAFE_TO_CLAIM_FIELD = BriefField(
    key="not_safe_to_claim",
    prompt_key="lesson.l03.decision.not_safe_to_claim.prompt",
    options=(
        BriefOption("single_exact_total", "lesson.l03.decision.not_safe_to_claim.option.single_exact_total"),
        BriefOption("api_unreliable", "lesson.l03.decision.not_safe_to_claim.option.api_unreliable"),
        BriefOption("escalation_ruled_out", "lesson.l03.decision.not_safe_to_claim.option.escalation_ruled_out"),
        BriefOption("range_itself_untrustworthy", "lesson.l03.decision.not_safe_to_claim.option.range_itself_untrustworthy"),
    ),
)

RECOMMENDATION_FIELD = BriefField(
    key="recommendation",
    prompt_key="lesson.l03.decision.recommendation.prompt",
    options=(
        BriefOption("report_range_and_flag", "lesson.l03.decision.recommendation.option.report_range_and_flag"),
        BriefOption("report_raw_and_move_on", "lesson.l03.decision.recommendation.option.report_raw_and_move_on"),
        BriefOption("block_on_repull", "lesson.l03.decision.recommendation.option.block_on_repull"),
    ),
)

# --- Optional Mastery --------------------------------------------------------

MASTERY_METRIC_OPTIONS = (
    MasteryOption("last_page_vs_page_size", "lesson.l03.mastery.metric_last_page_vs_page_size"),
    MasteryOption("received_vs_declared_total", "lesson.l03.mastery.metric_received_vs_declared_total"),
)

MASTERY_INTERPRET_OPTIONS = (
    MasteryOption("last_page_short", "lesson.l03.mastery.interpret_last_page_short"),
    MasteryOption("looks_complete", "lesson.l03.mastery.interpret_looks_complete"),
)

_TICKET_PULL_PYTHON_CODE = (
    "ticket_responses = []\n"
    "cursor = None\n"
    "while True:\n"
    "    payload = requests.get('/api/support/tickets', params={'cursor': cursor}).json()\n"
    "    ticket_responses.append(payload)\n"
    "    if not payload['pagination']['has_more']:\n"
    "        break\n"
    "    cursor = payload['pagination']['next_cursor']\n"
)
"""The mastery act's own dataset - a real, separate pull from
twist_data.py's own MASTERY_* numbers, never yet referenced anywhere else
in the persistent context-based mirror. Only one of the two compute()
branches below ever actually runs per playthrough (MasteryChallengeScene
computes exactly once, for whichever metric was picked), so each branch's
own *first* python_code needs this same self-contained load - neither can
assume the other one already ran."""


def _critical_evidence_present(context: LessonContext, selected_evidence_ids: set[str]) -> tuple[str, ...]:
    """Which of CRITICAL_EVIDENCE_KEYS the student's picked evidence
    actually covers - checked by substring on the picked items' own
    label_key, the same technique l02_source_scout/scenario.py's own
    _critical_evidence_present uses. Includes `page_skipped` on the pool
    regardless of path (it just never matches anything for a student whose
    page 5 was recovered, since nothing records that fact on that path) -
    score_lesson_three itself is what judges the right count per path."""
    present: set[str] = set()
    for item in context.evidence:
        if item.id not in selected_evidence_ids:
            continue
        for critical_key in CRITICAL_EVIDENCE_KEYS:
            if critical_key in item.label_key:
                present.add(critical_key)
    return tuple(sorted(present))


def build_lesson_three_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 03's real 12-stage investigation: one continuous
    LessonContext threaded via closures through every analytical stage, on
    one real, hand-scripted paginated pull (twist_data.py/REQUEST_ATTEMPTS)
    rather than a fully pre-scripted, zero-agency request log. The rate
    limit on page 5 offers a real, recoverable choice; page 3's silent
    shortfall never does - the two failure modes are deliberately never
    conflated (see Known Gap's own decoys), since only one of them is
    something a better retry strategy could have fixed. Page 1's own
    response offers a second, non-failure real choice - follow the real
    next_cursor or resend the same request - so continuation is read off
    real response metadata at least once, not only ever driven by an
    internal pointer the student never actually has to consult."""
    collected: dict = {}
    context = LessonContext()
    pages = generate_pages()

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

    # --- The Acquisition ---

    def acquisition(advance):
        def on_complete(total):
            collected["running_total"] = total
            collected["page5_recovered"] = total >= BEST_ACHIEVABLE_TOTAL
            _sync_context_into_collected()
            advance()

        return APIConsoleScene(
            app,
            "lesson.l03.console_title",
            "lesson.l03.endpoint",
            REQUEST_ATTEMPTS,
            on_complete,
            guided=True,
            hint_key="lesson.l03.console_hint",
            context=context,
            python_code=ACQUISITION_PYTHON_CODE,
            evidence_label_key="lesson.l03.evidence.running_total_label",
            record_evidence=False,
            skipped_status_key=SKIPPED_STATUS,
            skipped_evidence_label_key="lesson.l03.evidence.page_skipped_label",
        )

    def gut_check(advance):
        def on_complete(brief):
            collected["initial_gut_check"] = brief["initial_gut_check"]
            advance()

        return BriefBuilderScene(app, "lesson.l03.gut_check.title", (INITIAL_GUT_CHECK_FIELD,), on_complete, guided=False)

    def completeness_reveal(advance):
        def on_complete(interpretation):
            collected["interpret_choice"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l03.completeness_reveal.title",
            narrative_keys=("dialogue.l03_completeness_reveal.line1", "dialogue.l03_completeness_reveal.line2"),
            comparisons=(
                ComparisonValue("lesson.l03.evidence.running_total_label", float(collected.get("running_total", 0))),
                ComparisonValue(
                    "lesson.l03.evidence.total_count_label", float(TOTAL_COUNT), python_code="responses[-1]['total_count']"
                ),
            ),
            interpret_prompt_key="lesson.l03.completeness_interpret.prompt",
            interpret_options=COMPLETENESS_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    def root_cause_confirmed(advance):
        def on_complete():
            _sync_context_into_collected()
            advance()

        return DialogueScene(
            app,
            ROOT_CAUSE_DIALOGUE,
            on_complete=on_complete,
            context=context,
            record_label_key="dialogue.l03_root_cause.line2",
            record_evidence_key="lesson.l03.evidence.page3_shortfall_label",
            record_key="page3_shortfall",
        )

    def revised_gut_check(advance):
        def on_complete(brief):
            collected["revised_gut_check"] = brief["revised_gut_check"]
            advance()

        return BriefBuilderScene(app, "lesson.l03.revised_gut_check.title", (REVISED_GUT_CHECK_FIELD,), on_complete, guided=False)

    # --- Evidence Review ---

    def evidence_review(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            pages,
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
            "lesson.l03.decision_title",
            steps=(
                ACQUISITION_STRATEGY_FIELD,
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

        mastery_last_page_received = MASTERY_RECEIVED_TOTAL - 2 * MASTERY_PAGE_SIZE

        def compute(metric_key: str) -> tuple[MetricValue, MetricValue]:
            if metric_key == "last_page_vs_page_size":
                # The misleading framing: of course a last page looks
                # short next to a full page - that's true of every
                # genuine last page, so this comparison can never look
                # suspicious on its own, hiding the real shortfall behind
                # an expectation that's true for an unrelated reason.
                return (
                    MetricValue(
                        "lesson.l03.mastery.received_last_page_label",
                        float(mastery_last_page_received),
                        python_code=_TICKET_PULL_PYTHON_CODE + "len(ticket_responses[-1]['data'])",
                    ),
                    MetricValue("lesson.l03.mastery.page_size_label", float(MASTERY_PAGE_SIZE)),
                )
            return (
                MetricValue(
                    "lesson.l03.mastery.received_label",
                    float(MASTERY_RECEIVED_TOTAL),
                    python_code=_TICKET_PULL_PYTHON_CODE + "sum(len(r['data']) for r in ticket_responses)",
                ),
                MetricValue(
                    "lesson.l03.mastery.declared_label",
                    float(MASTERY_TOTAL_COUNT),
                    python_code="ticket_responses[-1]['total_count']",
                ),
            )

        return MasteryChallengeScene(
            app,
            title_key="lesson.l03.mastery.title",
            narrative_keys=("dialogue.l03_mastery.line1", "dialogue.l03_mastery.line2"),
            metric_prompt_key="lesson.l03.mastery.metric_prompt",
            metric_options=MASTERY_METRIC_OPTIONS,
            compute=compute,
            interpret_prompt_key="lesson.l03.mastery.interpret_prompt",
            interpret_options=MASTERY_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            value_format=lambda value: f"{value:,.0f}",
        )

    # --- Feedback / Debrief ---

    def _build_result() -> LessonThreeResult:
        # A plain function, not something stashed in `collected` - see
        # l01_question_first/scenario.py's own _build_result for why
        # (LessonRunner checkpoints `collected` via json.dumps, and
        # neither LessonThreeResult nor LessonEvaluation is serializable).
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))
        return LessonThreeResult(
            initial_gut_check=collected.get("initial_gut_check", ""),
            interpret_choice=collected.get("interpret_choice", ""),
            revised_gut_check=collected.get("revised_gut_check", ""),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(context, selected_evidence_ids),
            page5_recovered=collected.get("page5_recovered", True),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_metric=collected.get("mastery_metric") or "",
            mastery_interpretation=collected.get("mastery_interpretation") or "",
        )

    def feedback(advance):
        from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene

        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_03.number, 0)
        evaluation = score_lesson_three(result, LESSON_03, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        framing,
        acquisition,
        gut_check,
        completeness_reveal,
        root_cause_confirmed,
        revised_gut_check,
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
        lesson_number=3,
        collected=collected,
        definition=LESSON_03,
        on_resume=_restore_context_if_present,
    )
    return runner, collected
