from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_19 = LessonDefinition(
    id="ds19_power_plant",
    chapter=4,
    number=19,
    title_key="lesson.l19.title",
    objective_keys=(
        "lesson.l19.objective1",
        "lesson.l19.objective2",
        "lesson.l19.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=15,
)
