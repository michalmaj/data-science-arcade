from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l16_metric_forge.scoring import score_lesson_sixteen

LESSON_16 = LessonDefinition(
    id="ds16_metric_forge",
    chapter=4,
    number=16,
    title_key="lesson.l16.title",
    objective_keys=(
        "lesson.l16.objective1",
        "lesson.l16.objective2",
        "lesson.l16.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=29,
    related_handbook_entry_id="when_a_measure_becomes_a_target",
    scorer=score_lesson_sixteen,
)
