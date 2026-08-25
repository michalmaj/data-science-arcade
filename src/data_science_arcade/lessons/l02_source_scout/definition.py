from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_02 = LessonDefinition(
    id="ds02_source_scout",
    chapter=1,
    number=2,
    title_key="lesson.l02.title",
    objective_keys=(
        "lesson.l02.objective1",
        "lesson.l02.objective2",
        "lesson.l02.objective3",
    ),
    scoring_dimensions=(ScoreDimension.DATA_QUALITY, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY),
)
