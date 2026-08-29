from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_28 = LessonDefinition(
    id="ds28_chart_crime_lab",
    chapter=6,
    number=28,
    title_key="lesson.l28.title",
    objective_keys=(
        "lesson.l28.objective1",
        "lesson.l28.objective2",
        "lesson.l28.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.COMMUNICATION, ScoreDimension.OVERCONFIDENCE),
)
