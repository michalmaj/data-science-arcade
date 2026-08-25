from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_06 = LessonDefinition(
    id="ds06_schema_repair_shop",
    chapter=2,
    number=6,
    title_key="lesson.l06.title",
    objective_keys=(
        "lesson.l06.objective1",
        "lesson.l06.objective2",
        "lesson.l06.objective3",
    ),
    scoring_dimensions=(ScoreDimension.DATA_QUALITY, ScoreDimension.METHOD, ScoreDimension.REASONING),
)
