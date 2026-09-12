from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l18_randomization_control_room.scoring import score_lesson_eighteen

LESSON_18 = LessonDefinition(
    id="ds18_randomization_control_room",
    chapter=4,
    number=18,
    title_key="lesson.l18.title",
    objective_keys=(
        "lesson.l18.objective1",
        "lesson.l18.objective2",
        "lesson.l18.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
    estimated_minutes=24,
    related_handbook_entry_id="randomization_is_a_mechanism",
    scorer=score_lesson_eighteen,
)
