from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_11 = LessonDefinition(
    id="ds11_distribution_observatory",
    chapter=3,
    number=11,
    title_key="lesson.l11.title",
    objective_keys=(
        "lesson.l11.objective1",
        "lesson.l11.objective2",
        "lesson.l11.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.OVERCONFIDENCE),
)
