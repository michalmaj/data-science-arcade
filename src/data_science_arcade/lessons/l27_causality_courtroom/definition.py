from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_27 = LessonDefinition(
    id="ds27_causality_courtroom",
    chapter=6,
    number=27,
    title_key="lesson.l27.title",
    objective_keys=(
        "lesson.l27.objective1",
        "lesson.l27.objective2",
        "lesson.l27.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.COMMUNICATION),
    estimated_minutes=15,
)
