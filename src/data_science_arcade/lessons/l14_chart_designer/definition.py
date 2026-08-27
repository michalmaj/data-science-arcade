from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_14 = LessonDefinition(
    id="ds14_chart_designer",
    chapter=3,
    number=14,
    title_key="lesson.l14.title",
    objective_keys=(
        "lesson.l14.objective1",
        "lesson.l14.objective2",
        "lesson.l14.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.COMMUNICATION, ScoreDimension.OVERCONFIDENCE),
)
