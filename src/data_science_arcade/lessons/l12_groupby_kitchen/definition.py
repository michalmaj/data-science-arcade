from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_12 = LessonDefinition(
    id="ds12_groupby_kitchen",
    chapter=3,
    number=12,
    title_key="lesson.l12.title",
    objective_keys=(
        "lesson.l12.objective1",
        "lesson.l12.objective2",
        "lesson.l12.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
    ),
    estimated_minutes=24,
    related_handbook_entry_id="observation_unit_and_grain",
)
