from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_04 = LessonDefinition(
    id="ds04_event_log_factory",
    chapter=1,
    number=4,
    title_key="lesson.l04.title",
    objective_keys=(
        "lesson.l04.objective1",
        "lesson.l04.objective2",
        "lesson.l04.objective3",
    ),
    scoring_dimensions=(ScoreDimension.DATA_QUALITY, ScoreDimension.METHOD, ScoreDimension.EVIDENCE),
)
