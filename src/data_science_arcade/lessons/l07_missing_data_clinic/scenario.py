from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.source import DataSource, SourceAttribute
from data_science_arcade.lessons.l07_missing_data_clinic.customer_data import (
    drop_rows_mean,
    generate_customers,
    segment_imputed_mean,
    true_population_mean,
)
from data_science_arcade.lessons.l07_missing_data_clinic.scoring import LessonSevenResult
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.source_board_scene import SourceBoardScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l07_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l07_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l07_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l07_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l07_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l07_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l07_debrief.line3"),
    )
)

# Same 5 strategies reused for both the guided and independent passes,
# matching Lessons 01-06's pattern. Every number here is the real output of
# customer_data.py's pandas computations (verified in
# tests/test_lesson07_customer_data.py), not a hand-picked display string -
# drop-rows and mean-imputation land on the same 68.0 by a genuine
# mathematical property (filling with the mean of what's left can't move
# the overall mean), not a coincidence the content author invented.
STRATEGIES: tuple[DataSource, ...] = (
    DataSource(
        key="drop_rows",
        name_key="lesson.l07.strategy.drop_rows",
        attributes=(
            SourceAttribute("lesson.l07.attribute.average_label", "lesson.l07.stat.drop_rows.average"),
            SourceAttribute("lesson.l07.attribute.sample_size_label", "lesson.l07.stat.drop_rows.sample_size"),
            SourceAttribute("lesson.l07.attribute.handling_label", "lesson.l07.stat.drop_rows.handling"),
        ),
    ),
    DataSource(
        key="mean_imputation",
        name_key="lesson.l07.strategy.mean_imputation",
        attributes=(
            SourceAttribute("lesson.l07.attribute.average_label", "lesson.l07.stat.mean_imputation.average"),
            SourceAttribute("lesson.l07.attribute.sample_size_label", "lesson.l07.stat.mean_imputation.sample_size"),
            SourceAttribute("lesson.l07.attribute.handling_label", "lesson.l07.stat.mean_imputation.handling"),
        ),
    ),
    DataSource(
        key="median_imputation",
        name_key="lesson.l07.strategy.median_imputation",
        attributes=(
            SourceAttribute("lesson.l07.attribute.average_label", "lesson.l07.stat.median_imputation.average"),
            SourceAttribute("lesson.l07.attribute.sample_size_label", "lesson.l07.stat.median_imputation.sample_size"),
            SourceAttribute("lesson.l07.attribute.handling_label", "lesson.l07.stat.median_imputation.handling"),
        ),
    ),
    DataSource(
        key="segment_imputation",
        name_key="lesson.l07.strategy.segment_imputation",
        attributes=(
            SourceAttribute("lesson.l07.attribute.average_label", "lesson.l07.stat.segment_imputation.average"),
            SourceAttribute("lesson.l07.attribute.sample_size_label", "lesson.l07.stat.segment_imputation.sample_size"),
            SourceAttribute("lesson.l07.attribute.handling_label", "lesson.l07.stat.segment_imputation.handling"),
        ),
    ),
    DataSource(
        key="preserve_missingness",
        name_key="lesson.l07.strategy.preserve_missingness",
        attributes=(
            SourceAttribute("lesson.l07.attribute.average_label", "lesson.l07.stat.preserve_missingness.average"),
            SourceAttribute("lesson.l07.attribute.sample_size_label", "lesson.l07.stat.preserve_missingness.sample_size"),
            SourceAttribute("lesson.l07.attribute.handling_label", "lesson.l07.stat.preserve_missingness.handling"),
        ),
    ),
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="strategy_choice",
        prompt_key="lesson.l07.field.strategy_choice.prompt",
        hint_key="lesson.l07.field.strategy_choice.hint",
        options=(
            BriefOption("segment_aware", "lesson.l07.option.strategy_choice.segment_aware"),
            BriefOption("preserve_and_flag", "lesson.l07.option.strategy_choice.preserve_and_flag"),
            BriefOption("drop_rows", "lesson.l07.option.strategy_choice.drop_rows"),
        ),
    ),
    BriefField(
        key="remaining_bias",
        prompt_key="lesson.l07.field.remaining_bias.prompt",
        hint_key="lesson.l07.field.remaining_bias.hint",
        options=(
            BriefOption("responders_not_representative", "lesson.l07.option.remaining_bias.responders_not_representative"),
            BriefOption("segment_boundary_uncertain", "lesson.l07.option.remaining_bias.segment_boundary_uncertain"),
            BriefOption("no_data_before_signup", "lesson.l07.option.remaining_bias.no_data_before_signup"),
        ),
    ),
)


def build_lesson_seven_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 07's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonSevenResult once both comparison stages
    and the decision brief have completed."""
    collected: dict = {}
    customers = generate_customers()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(strategy_key):
            collected["guided_strategy"] = strategy_key
            advance()

        return SourceBoardScene(
            app,
            "lesson.l07.board_title",
            "lesson.l07.board_prompt",
            STRATEGIES,
            on_complete,
            guided=True,
            hint_key="lesson.l07.board_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(strategy_key):
            collected["independent_strategy"] = strategy_key
            advance()

        return SourceBoardScene(app, "lesson.l07.board_title", "lesson.l07.board_prompt", STRATEGIES, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l07.twist_title",
            narrative_keys=("dialogue.l07_twist.line1", "dialogue.l07_twist.line2"),
            dataset=customers,
            comparisons=(
                ("lesson.l07.twist_reported_label", drop_rows_mean(customers)),
                ("lesson.l07.twist_segment_label", segment_imputed_mean(customers)),
                ("lesson.l07.twist_true_label", true_population_mean(customers)),
            ),
            value_format=lambda value: f"{value:.1f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l07.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonSevenResult(
            guided_strategy=collected.get("guided_strategy", ""),
            independent_strategy=collected.get("independent_strategy", ""),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected
