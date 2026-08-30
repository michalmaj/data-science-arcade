from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_09 = LessonDefinition(
    id="ds09_outlier_patrol",
    chapter=2,
    number=9,
    title_key="lesson.l09.title",
    objective_keys=(
        "lesson.l09.objective1",
        "lesson.l09.objective2",
        "lesson.l09.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
    estimated_minutes=15,
)
