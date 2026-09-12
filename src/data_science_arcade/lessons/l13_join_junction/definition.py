from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l13_join_junction.scoring import score_lesson_thirteen

LESSON_13 = LessonDefinition(
    id="ds13_join_junction",
    chapter=3,
    number=13,
    title_key="lesson.l13.title",
    objective_keys=(
        "lesson.l13.objective1",
        "lesson.l13.objective2",
        "lesson.l13.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
    estimated_minutes=26,
    related_handbook_entry_id="joins_have_cardinality",
    scorer=score_lesson_thirteen,
)
