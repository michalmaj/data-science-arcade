from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l21_funnel_factory.scoring import score_lesson_twenty_one

LESSON_21 = LessonDefinition(
    id="ds21_funnel_factory",
    chapter=5,
    number=21,
    title_key="lesson.l21.title",
    objective_keys=(
        "lesson.l21.objective1",
        "lesson.l21.objective2",
        "lesson.l21.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
    estimated_minutes=20,
    related_handbook_entry_id="a_funnel_is_a_definition",
    scorer=score_lesson_twenty_one,
)
