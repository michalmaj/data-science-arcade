from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.source import DataSource, SourceAttribute
from data_science_arcade.lessons.l02_source_scout.definition import LESSON_02
from data_science_arcade.lessons.l02_source_scout.scoring import LessonTwoResult
from data_science_arcade.lessons.l02_source_scout.twist_data import generate_analytics_opt_in, opt_in_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.source_board_scene import SourceBoardScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l02_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l02_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l02_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l02_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l02_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l02_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l02_debrief.line3"),
    )
)

# Rating keys are scoped per-attribute (not per-source): "High" has to
# agree in grammatical gender with whichever Polish noun the attribute is
# ("Wysoka" for Świeżość, "Wysoki" for Koszt, "Wysokie" for Ryzyko/
# Pokrycie), so the same three rating levels are shared across all sources
# that use a given attribute instead of duplicating 15 keys per source.
FRESHNESS = "lesson.l02.attr.freshness"
COVERAGE = "lesson.l02.attr.coverage"
COST = "lesson.l02.attr.cost"
BIAS_RISK = "lesson.l02.attr.bias_risk"
SCHEMA_QUALITY = "lesson.l02.attr.schema_quality"


def _rating(attribute_key: str, level: str) -> SourceAttribute:
    attribute_name = attribute_key.rsplit(".", 1)[-1]
    return SourceAttribute(attribute_key, f"lesson.l02.attr_rating.{attribute_name}.{level}")


SOURCES: tuple[DataSource, ...] = (
    DataSource(
        key="analytics",
        name_key="lesson.l02.source.analytics.name",
        attributes=(
            _rating(FRESHNESS, "high"),
            _rating(COVERAGE, "medium"),
            _rating(COST, "low"),
            _rating(BIAS_RISK, "high"),
            _rating(SCHEMA_QUALITY, "high"),
        ),
    ),
    DataSource(
        key="survey",
        name_key="lesson.l02.source.survey.name",
        attributes=(
            _rating(FRESHNESS, "medium"),
            _rating(COVERAGE, "low"),
            _rating(COST, "medium"),
            _rating(BIAS_RISK, "high"),
            _rating(SCHEMA_QUALITY, "medium"),
        ),
    ),
    DataSource(
        key="billing",
        name_key="lesson.l02.source.billing.name",
        attributes=(
            _rating(FRESHNESS, "low"),
            _rating(COVERAGE, "high"),
            _rating(COST, "low"),
            _rating(BIAS_RISK, "medium"),
            _rating(SCHEMA_QUALITY, "high"),
        ),
    ),
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="source_choice",
        prompt_key="lesson.l02.field.source_choice.prompt",
        hint_key="lesson.l02.field.source_choice.hint",
        options=(
            BriefOption("analytics_only", "lesson.l02.option.source_choice.analytics_only"),
            BriefOption("billing_only", "lesson.l02.option.source_choice.billing_only"),
            BriefOption("combine_sources", "lesson.l02.option.source_choice.combine_sources"),
        ),
    ),
    BriefField(
        key="limitation",
        prompt_key="lesson.l02.field.limitation.prompt",
        hint_key="lesson.l02.field.limitation.hint",
        options=(
            BriefOption("age_skew", "lesson.l02.option.limitation.age_skew"),
            BriefOption("free_tier_gap", "lesson.l02.option.limitation.free_tier_gap"),
            BriefOption("definition_mismatch", "lesson.l02.option.limitation.definition_mismatch"),
        ),
    ),
)


def build_lesson_two_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 02's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's choices as they progress -
    `result` holds the final LessonTwoResult once all three source/brief
    stages have completed."""
    collected: dict = {}
    twist_dataset = generate_analytics_opt_in()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(source_key):
            collected["guided_source_choice"] = source_key
            advance()

        return SourceBoardScene(
            app,
            "lesson.l02.board_title",
            "lesson.l02.board_prompt",
            SOURCES,
            on_complete,
            guided=True,
            hint_key="lesson.l02.board_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(source_key):
            collected["independent_source_choice"] = source_key
            advance()

        return SourceBoardScene(
            app,
            "lesson.l02.board_title",
            "lesson.l02.board_prompt_independent",
            SOURCES,
            on_complete,
            guided=False,
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l02.twist_title",
            narrative_keys=("dialogue.l02_twist.line1", "dialogue.l02_twist.line2"),
            dataset=twist_dataset,
            comparisons=(
                ("lesson.l02.twist_overall_label", opt_in_rate(twist_dataset, None)),
                ("lesson.l02.twist_young_label", opt_in_rate(twist_dataset, "18-34")),
                ("lesson.l02.twist_old_label", opt_in_rate(twist_dataset, "55+")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l02.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwoResult(
            guided_source_choice=collected.get("guided_source_choice", ""),
            independent_source_choice=collected.get("independent_source_choice", ""),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=2, collected=collected, definition=LESSON_02
    )
    return runner, collected
