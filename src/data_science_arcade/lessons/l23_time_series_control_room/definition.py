from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_23 = LessonDefinition(
    id="ds23_time_series_control_room",
    chapter=5,
    number=23,
    title_key="lesson.l23.title",
    objective_keys=(
        "lesson.l23.objective1",
        "lesson.l23.objective2",
        "lesson.l23.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
)
