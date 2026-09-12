from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_17 = LessonDefinition(
    id="ds17_hypothesis_detective",
    chapter=4,
    number=17,
    title_key="lesson.l17.title",
    objective_keys=(
        "lesson.l17.objective1",
        "lesson.l17.objective2",
        "lesson.l17.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY),
    estimated_minutes=22,
    related_handbook_entry_id="a_hypothesis_has_a_timestamp",
)
