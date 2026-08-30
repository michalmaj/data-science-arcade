from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_25 = LessonDefinition(
    id="ds25_kpi_emergency_room",
    chapter=5,
    number=25,
    title_key="lesson.l25.title",
    objective_keys=(
        "lesson.l25.objective1",
        "lesson.l25.objective2",
        "lesson.l25.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.COMMUNICATION, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=15,
)
