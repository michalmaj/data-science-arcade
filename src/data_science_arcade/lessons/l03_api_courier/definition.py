from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_03 = LessonDefinition(
    id="ds03_api_courier",
    chapter=1,
    number=3,
    title_key="lesson.l03.title",
    objective_keys=(
        "lesson.l03.objective1",
        "lesson.l03.objective2",
        "lesson.l03.objective3",
    ),
    scoring_dimensions=(ScoreDimension.DATA_QUALITY, ScoreDimension.METHOD, ScoreDimension.UNCERTAINTY),
)
