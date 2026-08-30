from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_12 = LessonDefinition(
    id="ds12_groupby_kitchen",
    chapter=3,
    number=12,
    title_key="lesson.l12.title",
    objective_keys=(
        "lesson.l12.objective1",
        "lesson.l12.objective2",
        "lesson.l12.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.DATA_QUALITY, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=15,
)
