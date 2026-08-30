from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_24 = LessonDefinition(
    id="ds24_survey_bureau",
    chapter=5,
    number=24,
    title_key="lesson.l24.title",
    objective_keys=(
        "lesson.l24.objective1",
        "lesson.l24.objective2",
        "lesson.l24.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.UNCERTAINTY, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=15,
)
