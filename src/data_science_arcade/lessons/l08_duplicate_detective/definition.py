from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_08 = LessonDefinition(
    id="ds08_duplicate_detective",
    chapter=2,
    number=8,
    title_key="lesson.l08.title",
    objective_keys=(
        "lesson.l08.objective1",
        "lesson.l08.objective2",
        "lesson.l08.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=15,
)
