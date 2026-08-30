from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_18 = LessonDefinition(
    id="ds18_randomization_control_room",
    chapter=4,
    number=18,
    title_key="lesson.l18.title",
    objective_keys=(
        "lesson.l18.objective1",
        "lesson.l18.objective2",
        "lesson.l18.objective3",
    ),
    scoring_dimensions=(ScoreDimension.DATA_QUALITY, ScoreDimension.METHOD, ScoreDimension.REASONING),
    estimated_minutes=15,
)
