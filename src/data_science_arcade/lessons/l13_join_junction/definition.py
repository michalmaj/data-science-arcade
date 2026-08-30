from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

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
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.DATA_QUALITY, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=15,
)
