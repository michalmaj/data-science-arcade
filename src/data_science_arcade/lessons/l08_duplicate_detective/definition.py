from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l08_duplicate_detective.scoring import score_lesson_eight

LESSON_08 = LessonDefinition(
    id="ds08_duplicate_detective",
    chapter=2,
    number=8,
    title_key="lesson.l08.title",
    objective_keys=(
        "lesson.l08.objective1",
        "lesson.l08.objective2",
        "lesson.l08.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.REPRODUCIBILITY,
    ),
    # Honest per-stage estimate for the required path only (core path,
    # matching every prior lesson's own convention of excluding the
    # optional mastery act) - not reverse-engineered toward any target.
    estimated_minutes=28,
    related_handbook_entry_id="duplicates_need_an_identity",
    scorer=score_lesson_eight,
)
