from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

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
    scoring_dimensions=(ScoreDimension.DATA_QUALITY, ScoreDimension.METHOD, ScoreDimension.REASONING),
    estimated_minutes=15,
)
