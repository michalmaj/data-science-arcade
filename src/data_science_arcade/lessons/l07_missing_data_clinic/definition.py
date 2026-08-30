from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_07 = LessonDefinition(
    id="ds07_missing_data_clinic",
    chapter=2,
    number=7,
    title_key="lesson.l07.title",
    objective_keys=(
        "lesson.l07.objective1",
        "lesson.l07.objective2",
        "lesson.l07.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.UNCERTAINTY, ScoreDimension.DATA_QUALITY),
    estimated_minutes=15,
)
