from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l09_outlier_patrol.scoring import score_lesson_nine

LESSON_09 = LessonDefinition(
    id="ds09_outlier_patrol",
    chapter=2,
    number=9,
    title_key="lesson.l09.title",
    objective_keys=(
        "lesson.l09.objective1",
        "lesson.l09.objective2",
        "lesson.l09.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.REPRODUCIBILITY,
    ),
    estimated_minutes=26,
    related_handbook_entry_id="outlier_is_a_flag_not_a_verdict",
    scorer=score_lesson_nine,
)
