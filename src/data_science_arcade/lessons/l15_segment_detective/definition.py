from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_15 = LessonDefinition(
    id="ds15_segment_detective",
    chapter=3,
    number=15,
    title_key="lesson.l15.title",
    objective_keys=(
        "lesson.l15.objective1",
        "lesson.l15.objective2",
        "lesson.l15.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE),
)
