from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l04_event_log_factory.scoring import score_lesson_four

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
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.REPRODUCIBILITY,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.REASONING,
    ),
    # Honest per-stage estimate for the required path only (core path,
    # matching l01/l02/l03's own convention of excluding the optional
    # mastery act) - not reverse-engineered toward any target.
    estimated_minutes=33,
    scorer=score_lesson_four,
)
