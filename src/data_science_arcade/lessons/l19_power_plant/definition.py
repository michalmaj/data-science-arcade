from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l19_power_plant.scoring import score_lesson_nineteen

LESSON_19 = LessonDefinition(
    id="ds19_power_plant",
    chapter=4,
    number=19,
    title_key="lesson.l19.title",
    objective_keys=(
        "lesson.l19.objective1",
        "lesson.l19.objective2",
        "lesson.l19.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.UNCERTAINTY, ScoreDimension.EVIDENCE),
    estimated_minutes=22,
    related_handbook_entry_id="power_is_a_design_property",
    scorer=score_lesson_nineteen,
)
