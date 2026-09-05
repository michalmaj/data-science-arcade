from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l07_missing_data_clinic.scoring import score_lesson_seven

LESSON_07 = LessonDefinition(
    id="ds07_missing_data_clinic",
    chapter=2,
    number=7,
    title_key="lesson.l07.title",
    objective_keys=(
        "lesson.l07.objective1",
        "lesson.l07.objective2",
        "lesson.l07.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.REPRODUCIBILITY,
        ScoreDimension.EVIDENCE,
        ScoreDimension.REASONING,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.METHOD,
    ),
    # Honest per-stage estimate for the required path only (core path,
    # matching every prior lesson's own convention of excluding the
    # optional mastery act) - not reverse-engineered toward any target.
    estimated_minutes=32,
    related_handbook_entry_id="missingness_has_a_mechanism",
    scorer=score_lesson_seven,
)
