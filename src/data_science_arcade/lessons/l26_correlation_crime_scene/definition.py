from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_26 = LessonDefinition(
    id="ds26_correlation_crime_scene",
    chapter=6,
    number=26,
    title_key="lesson.l26.title",
    objective_keys=(
        "lesson.l26.objective1",
        "lesson.l26.objective2",
        "lesson.l26.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY),
)
