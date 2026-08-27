from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_20 = LessonDefinition(
    id="ds20_ab_test_commander",
    chapter=4,
    number=20,
    title_key="lesson.l20.title",
    objective_keys=(
        "lesson.l20.objective1",
        "lesson.l20.objective2",
        "lesson.l20.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.UNCERTAINTY, ScoreDimension.OVERCONFIDENCE),
)
