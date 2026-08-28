from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_22 = LessonDefinition(
    id="ds22_cohort_observatory",
    chapter=5,
    number=22,
    title_key="lesson.l22.title",
    objective_keys=(
        "lesson.l22.objective1",
        "lesson.l22.objective2",
        "lesson.l22.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.UNCERTAINTY, ScoreDimension.OVERCONFIDENCE),
)
