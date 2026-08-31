from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l02_source_scout.scoring import score_lesson_two

LESSON_02 = LessonDefinition(
    id="ds02_source_scout",
    chapter=1,
    number=2,
    title_key="lesson.l02.title",
    objective_keys=(
        "lesson.l02.objective1",
        "lesson.l02.objective2",
        "lesson.l02.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.REASONING,
    ),
    # Honest current estimate for the 16 required stages (core path only,
    # matching l01_question_first's own convention of excluding the
    # optional mastery act) - not reverse-engineered toward any target;
    # see decisions/IMPLEMENTATION_STATE.md for the per-stage breakdown.
    estimated_minutes=58,
    related_handbook_entry_id="metrics_need_definitions",
    scorer=score_lesson_two,
)
