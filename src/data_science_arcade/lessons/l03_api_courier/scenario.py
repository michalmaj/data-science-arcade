from data_science_arcade.lessons.framework.api import APIRequestAttempt
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l03_api_courier.scoring import LessonThreeResult
from data_science_arcade.lessons.l03_api_courier.twist_data import (
    SHORTFALL_PAGE,
    generate_page_completeness,
    overall_completeness,
    page_completeness,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l03_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l03_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l03_briefing.line3"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l03_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l03_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l03_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l03_debrief.line3"),
    )
)

# Same request-log shape reused for both the guided and independent stages
# (only the endpoint label differs), matching Lessons 01/02's pattern:
# page 1-2 succeed, page 3 is rate-limited then succeeds on retry, page 4
# silently returns fewer records than expected (the twist), page 5 succeeds.
REQUEST_ATTEMPTS: tuple[APIRequestAttempt, ...] = (
    APIRequestAttempt(1, "api_console.status.ok", 20, True),
    APIRequestAttempt(2, "api_console.status.ok", 20, True),
    APIRequestAttempt(3, "api_console.status.rate_limited", 0, False),
    APIRequestAttempt(3, "api_console.status.ok", 20, True),
    APIRequestAttempt(SHORTFALL_PAGE, "api_console.status.ok", 12, True),
    APIRequestAttempt(5, "api_console.status.ok", 20, True),
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="completeness_judgment",
        prompt_key="lesson.l03.field.completeness_judgment.prompt",
        hint_key="lesson.l03.field.completeness_judgment.hint",
        options=(
            BriefOption("proceed_as_is", "lesson.l03.option.completeness_judgment.proceed_as_is"),
            BriefOption("refetch_first", "lesson.l03.option.completeness_judgment.refetch_first"),
            BriefOption("proceed_flagged", "lesson.l03.option.completeness_judgment.proceed_flagged"),
        ),
    ),
    BriefField(
        key="limitation",
        prompt_key="lesson.l03.field.limitation.prompt",
        hint_key="lesson.l03.field.limitation.hint",
        options=(
            BriefOption("status_not_enough", "lesson.l03.option.limitation.status_not_enough"),
            BriefOption("shortfall_size", "lesson.l03.option.limitation.shortfall_size"),
            BriefOption("retries_needed", "lesson.l03.option.limitation.retries_needed"),
        ),
    ),
)


def build_lesson_three_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 03's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonThreeResult once both console stages
    and the decision brief have completed."""
    collected: dict = {}
    twist_dataset = generate_page_completeness()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(total):
            collected["guided_records_collected"] = total
            advance()

        return APIConsoleScene(
            app,
            "lesson.l03.console_title_orders",
            "lesson.l03.endpoint_orders",
            REQUEST_ATTEMPTS,
            on_complete,
            guided=True,
            hint_key="lesson.l03.console_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(total):
            collected["independent_records_collected"] = total
            advance()

        return APIConsoleScene(
            app,
            "lesson.l03.console_title_tickets",
            "lesson.l03.endpoint_tickets",
            REQUEST_ATTEMPTS,
            on_complete,
            guided=False,
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l03.twist_title",
            narrative_keys=("dialogue.l03_twist.line1", "dialogue.l03_twist.line2"),
            dataset=twist_dataset,
            comparisons=(
                ("lesson.l03.twist_overall_label", overall_completeness(twist_dataset)),
                ("lesson.l03.twist_shortfall_label", page_completeness(twist_dataset, SHORTFALL_PAGE)),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l03.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonThreeResult(
            guided_records_collected=collected.get("guided_records_collected", 0),
            independent_records_collected=collected.get("independent_records_collected", 0),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected
