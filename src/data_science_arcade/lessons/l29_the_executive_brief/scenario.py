from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l29_the_executive_brief.findings import FINDINGS_POOL, TARGET_FINDING_COUNT
from data_science_arcade.lessons.l29_the_executive_brief.scoring import LessonTwentyNineResult
from data_science_arcade.lessons.l29_the_executive_brief.twist_data import generate_app_update_data, percent_change
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.finding_picker_scene import FindingPickerScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l29_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l29_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l29_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l29_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="supporting_chart",
        prompt_key="lesson.l29.field.supporting_chart.prompt",
        hint_key="lesson.l29.field.supporting_chart.hint",
        options=(
            BriefOption("social_mentions_over_time", "lesson.l29.option.supporting_chart.social_mentions_over_time"),
            BriefOption("checkout_completion_over_time", "lesson.l29.option.supporting_chart.checkout_completion_over_time"),
            BriefOption("stock_price_over_time", "lesson.l29.option.supporting_chart.stock_price_over_time"),
        ),
    ),
    BriefField(
        key="confidence_level",
        prompt_key="lesson.l29.field.confidence_level.prompt",
        hint_key="lesson.l29.field.confidence_level.hint",
        options=(
            BriefOption("very_high_a_clear_triumph", "lesson.l29.option.confidence_level.very_high_a_clear_triumph"),
            BriefOption("high_sustained_with_a_mechanism", "lesson.l29.option.confidence_level.high_sustained_with_a_mechanism"),
            BriefOption("low_could_be_noise", "lesson.l29.option.confidence_level.low_could_be_noise"),
        ),
    ),
    BriefField(
        key="recommendation",
        prompt_key="lesson.l29.field.recommendation.prompt",
        hint_key="lesson.l29.field.recommendation.hint",
        options=(
            BriefOption("revert_immediately", "lesson.l29.option.recommendation.revert_immediately"),
            BriefOption("keep_and_monitor_returns", "lesson.l29.option.recommendation.keep_and_monitor_returns"),
            BriefOption("expand_everywhere_no_monitoring", "lesson.l29.option.recommendation.expand_everywhere_no_monitoring"),
        ),
    ),
    BriefField(
        key="caveats",
        prompt_key="lesson.l29.field.caveats.prompt",
        hint_key="lesson.l29.field.caveats.hint",
        options=(
            BriefOption("sample_size_was_tiny", "lesson.l29.option.caveats.sample_size_was_tiny"),
            BriefOption("competitor_redesigned_too", "lesson.l29.option.caveats.competitor_redesigned_too"),
            BriefOption("leadership_might_not_like_it", "lesson.l29.option.caveats.leadership_might_not_like_it"),
        ),
    ),
)


def build_lesson_twenty_nine_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 29's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyNineResult once both
    finding-picking stages and the decision brief have completed."""
    collected: dict = {}
    app_update_data = generate_app_update_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return FindingPickerScene(
            app,
            "lesson.l29.picker_title",
            "lesson.l29.picker_prompt",
            FINDINGS_POOL,
            TARGET_FINDING_COUNT,
            on_complete,
            guided=True,
            hint_key="lesson.l29.picker_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return FindingPickerScene(
            app,
            "lesson.l29.picker_title",
            "lesson.l29.picker_prompt",
            FINDINGS_POOL,
            TARGET_FINDING_COUNT,
            on_complete,
            guided=False,
            hint_key="lesson.l29.picker_hint",
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l29.twist_title",
            narrative_keys=("dialogue.l29_twist.line1", "dialogue.l29_twist.line2"),
            dataset=app_update_data,
            comparisons=(
                ("lesson.l29.twist_downloads_label", percent_change(app_update_data, "app_downloads")),
                ("lesson.l29.twist_session_label", percent_change(app_update_data, "session_length_minutes")),
            ),
            value_format=lambda value: f"{value:+.0%}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l29.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyNineResult(
            guided_choices=collected.get("guided_choices", ()),
            independent_choices=collected.get("independent_choices", ()),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected
