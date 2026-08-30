from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.flow import FlowEventOption, FlowStep
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l04_event_log_factory.definition import LESSON_04
from data_science_arcade.lessons.l04_event_log_factory.scoring import LessonFourResult
from data_science_arcade.lessons.l04_event_log_factory.twist_data import (
    MISSING_EVENT,
    event_rate,
    generate_checkout_events,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l04_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l04_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l04_briefing.line3"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l04_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l04_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l04_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l04_debrief.line3"),
    )
)

# Same 5-step checkout flow reused for both the guided and independent
# passes, matching Lessons 01/02's pattern: one correct event per step plus
# two decoys (an adjacent step's event, or a plausible-but-different action).
FLOW_STEPS: tuple[FlowStep, ...] = (
    FlowStep(
        key="product_page",
        short_label_key="lesson.l04.step.product_page.label",
        prompt_key="lesson.l04.step.product_page.prompt",
        hint_key="lesson.l04.step.product_page.hint",
        options=(
            FlowEventOption("app_opened", "lesson.l04.event.app_opened"),
            FlowEventOption("product_viewed", "lesson.l04.event.product_viewed"),
            FlowEventOption("search_performed", "lesson.l04.event.search_performed"),
        ),
    ),
    FlowStep(
        key="add_to_cart",
        short_label_key="lesson.l04.step.add_to_cart.label",
        prompt_key="lesson.l04.step.add_to_cart.prompt",
        hint_key="lesson.l04.step.add_to_cart.hint",
        options=(
            FlowEventOption("product_viewed", "lesson.l04.event.product_viewed"),
            FlowEventOption("wishlist_added", "lesson.l04.event.wishlist_added"),
            FlowEventOption("add_to_cart", "lesson.l04.event.add_to_cart"),
        ),
    ),
    FlowStep(
        key="checkout_started",
        short_label_key="lesson.l04.step.checkout_started.label",
        prompt_key="lesson.l04.step.checkout_started.prompt",
        hint_key="lesson.l04.step.checkout_started.hint",
        options=(
            FlowEventOption("cart_viewed", "lesson.l04.event.cart_viewed"),
            FlowEventOption("checkout_started", "lesson.l04.event.checkout_started"),
            FlowEventOption("add_to_cart", "lesson.l04.event.add_to_cart"),
        ),
    ),
    FlowStep(
        key="payment_entered",
        short_label_key="lesson.l04.step.payment_entered.label",
        prompt_key="lesson.l04.step.payment_entered.prompt",
        hint_key="lesson.l04.step.payment_entered.hint",
        options=(
            FlowEventOption("checkout_started", "lesson.l04.event.checkout_started"),
            FlowEventOption("promo_code_applied", "lesson.l04.event.promo_code_applied"),
            FlowEventOption("payment_info_entered", "lesson.l04.event.payment_info_entered"),
        ),
    ),
    FlowStep(
        key="order_confirmed",
        short_label_key="lesson.l04.step.order_confirmed.label",
        prompt_key="lesson.l04.step.order_confirmed.prompt",
        hint_key="lesson.l04.step.order_confirmed.hint",
        options=(
            FlowEventOption("payment_info_entered", "lesson.l04.event.payment_info_entered"),
            FlowEventOption("order_confirmed", "lesson.l04.event.order_confirmed"),
            FlowEventOption("order_cancelled", "lesson.l04.event.order_cancelled"),
        ),
    ),
)

CORRECT_EVENT_BY_STEP: dict[str, str] = {
    "product_page": "product_viewed",
    "add_to_cart": "add_to_cart",
    "checkout_started": "checkout_started",
    "payment_entered": "payment_info_entered",
    "order_confirmed": "order_confirmed",
}
"""The lesson's answer key - which option is actually correct per step.
Not consulted by FlowBuilderScene itself (guided_placement/independent_
placement just record whatever the player picked; scoring is deliberately
minimal, see LessonFourResult), only by tests and manual verification
scripts that need to drive a "correct" playthrough without assuming
option order encodes correctness (it deliberately doesn't - see below)."""

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="plan_judgment",
        prompt_key="lesson.l04.field.plan_judgment.prompt",
        hint_key="lesson.l04.field.plan_judgment.hint",
        options=(
            BriefOption("approve_as_is", "lesson.l04.option.plan_judgment.approve_as_is"),
            BriefOption("reject_fix_first", "lesson.l04.option.plan_judgment.reject_fix_first"),
            BriefOption("approve_with_flag", "lesson.l04.option.plan_judgment.approve_with_flag"),
        ),
    ),
    BriefField(
        key="required_change",
        prompt_key="lesson.l04.field.required_change.prompt",
        hint_key="lesson.l04.field.required_change.hint",
        options=(
            BriefOption("instrument_payment_event", "lesson.l04.option.required_change.instrument_payment_event"),
            BriefOption("cant_measure_dropoff", "lesson.l04.option.required_change.cant_measure_dropoff"),
            BriefOption("verify_before_relying", "lesson.l04.option.required_change.verify_before_relying"),
        ),
    ),
)


def build_lesson_four_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 04's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonFourResult once both flow stages and the
    decision brief have completed."""
    collected: dict = {}
    events_dataset = generate_checkout_events()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(placement):
            collected["guided_placement"] = placement
            advance()

        return FlowBuilderScene(app, "lesson.l04.flow_title", FLOW_STEPS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(placement):
            collected["independent_placement"] = placement
            advance()

        return FlowBuilderScene(app, "lesson.l04.flow_title", FLOW_STEPS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l04.twist_title",
            narrative_keys=("dialogue.l04_twist.line1", "dialogue.l04_twist.line2"),
            dataset=events_dataset,
            comparisons=(
                ("lesson.l04.twist_started_label", event_rate(events_dataset, "checkout_started")),
                ("lesson.l04.twist_payment_label", event_rate(events_dataset, MISSING_EVENT)),
                ("lesson.l04.twist_confirmed_label", event_rate(events_dataset, "order_confirmed")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l04.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonFourResult(
            guided_placement=collected.get("guided_placement", {}),
            independent_placement=collected.get("independent_placement", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=4, collected=collected, definition=LESSON_04
    )
    return runner, collected
