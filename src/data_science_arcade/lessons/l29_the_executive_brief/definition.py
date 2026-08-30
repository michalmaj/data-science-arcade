from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_29 = LessonDefinition(
    id="ds29_the_executive_brief",
    chapter=6,
    number=29,
    title_key="lesson.l29.title",
    objective_keys=(
        "lesson.l29.objective1",
        "lesson.l29.objective2",
        "lesson.l29.objective3",
    ),
    scoring_dimensions=(ScoreDimension.EVIDENCE, ScoreDimension.COMMUNICATION, ScoreDimension.UNCERTAINTY),
    estimated_minutes=15,
)
