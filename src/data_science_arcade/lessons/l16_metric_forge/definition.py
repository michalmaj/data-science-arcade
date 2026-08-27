from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_16 = LessonDefinition(
    id="ds16_metric_forge",
    chapter=4,
    number=16,
    title_key="lesson.l16.title",
    objective_keys=(
        "lesson.l16.objective1",
        "lesson.l16.objective2",
        "lesson.l16.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.OVERCONFIDENCE),
)
