from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.sampling import SamplingGroup
from data_science_arcade.lessons.l05_sampling_mission.definition import LESSON_05
from data_science_arcade.lessons.l05_sampling_mission.scoring import LessonFiveResult
from data_science_arcade.lessons.l05_sampling_mission.twist_data import (
    DOMINANT_GROUP,
    apparent_satisfaction,
    generate_survey_responses,
    group_share_of_responses,
    unweighted_average_satisfaction,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l05_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l05_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_independent_intro.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_debrief.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l05_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l05_debrief.line3"),
    )
)

# Same 4 customer groups and 200-contact budget reused for both the guided
# and independent passes, matching Lessons 01-04's pattern.
CUSTOMER_GROUPS: tuple[SamplingGroup, ...] = (
    SamplingGroup("new", "lesson.l05.group.new"),
    SamplingGroup("regular", "lesson.l05.group.regular"),
    SamplingGroup("plus", "lesson.l05.group.plus"),
    SamplingGroup("lapsed", "lesson.l05.group.lapsed"),
)
TOTAL_BUDGET = 200
STEP = 10

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="sampling_strategy",
        prompt_key="lesson.l05.field.sampling_strategy.prompt",
        hint_key="lesson.l05.field.sampling_strategy.hint",
        options=(
            BriefOption("oversample_low_response", "lesson.l05.option.sampling_strategy.oversample_low_response"),
            BriefOption("weight_after_the_fact", "lesson.l05.option.sampling_strategy.weight_after_the_fact"),
            BriefOption("trust_raw_results", "lesson.l05.option.sampling_strategy.trust_raw_results"),
        ),
    ),
    BriefField(
        key="remaining_bias",
        prompt_key="lesson.l05.field.remaining_bias.prompt",
        hint_key="lesson.l05.field.remaining_bias.hint",
        options=(
            BriefOption("self_selection", "lesson.l05.option.remaining_bias.self_selection"),
            BriefOption("frame_coverage", "lesson.l05.option.remaining_bias.frame_coverage"),
            BriefOption("sample_size_per_group", "lesson.l05.option.remaining_bias.sample_size_per_group"),
        ),
    ),
)


def build_lesson_five_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 05's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonFiveResult once both allocator stages
    and the decision brief have completed."""
    collected: dict = {}
    responses_dataset = generate_survey_responses()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(allocation):
            collected["guided_allocation"] = allocation
            advance()

        return SamplingAllocatorScene(
            app,
            "lesson.l05.allocator_title",
            "lesson.l05.allocator_prompt",
            CUSTOMER_GROUPS,
            TOTAL_BUDGET,
            STEP,
            on_complete,
            guided=True,
            hint_key="lesson.l05.allocator_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(allocation):
            collected["independent_allocation"] = allocation
            advance()

        return SamplingAllocatorScene(
            app,
            "lesson.l05.allocator_title",
            "lesson.l05.allocator_prompt",
            CUSTOMER_GROUPS,
            TOTAL_BUDGET,
            STEP,
            on_complete,
            guided=False,
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l05.twist_title",
            narrative_keys=("dialogue.l05_twist.line1", "dialogue.l05_twist.line2"),
            dataset=responses_dataset,
            comparisons=(
                ("lesson.l05.twist_dominant_label", group_share_of_responses(responses_dataset, DOMINANT_GROUP)),
                ("lesson.l05.twist_apparent_label", apparent_satisfaction(responses_dataset)),
                ("lesson.l05.twist_unweighted_label", unweighted_average_satisfaction(responses_dataset)),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l05.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonFiveResult(
            guided_allocation=collected.get("guided_allocation", {}),
            independent_allocation=collected.get("independent_allocation", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=5, collected=collected, definition=LESSON_05
    )
    return runner, collected
