from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_05 = LessonDefinition(
    id="ds05_sampling_mission",
    chapter=1,
    number=5,
    title_key="lesson.l05.title",
    objective_keys=(
        "lesson.l05.objective1",
        "lesson.l05.objective2",
        "lesson.l05.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY),
)
