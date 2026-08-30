from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_30 = LessonDefinition(
    id="ds30_the_data_incident",
    chapter=6,
    number=30,
    title_key="lesson.l30.title",
    objective_keys=(
        "lesson.l30.objective1",
        "lesson.l30.objective2",
        "lesson.l30.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.UNCERTAINTY, ScoreDimension.COMMUNICATION),
)
