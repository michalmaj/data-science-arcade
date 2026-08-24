from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension

LESSON_01 = LessonDefinition(
    id="ds01_question_first",
    chapter=1,
    number=1,
    title_key="lesson.l01.title",
    objective_keys=(
        "lesson.l01.objective1",
        "lesson.l01.objective2",
        "lesson.l01.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY),
)
