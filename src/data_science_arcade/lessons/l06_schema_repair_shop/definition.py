from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l06_schema_repair_shop.scoring import score_lesson_six

LESSON_06 = LessonDefinition(
    id="ds06_schema_repair_shop",
    chapter=2,
    number=6,
    title_key="lesson.l06.title",
    objective_keys=(
        "lesson.l06.objective1",
        "lesson.l06.objective2",
        "lesson.l06.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.REPRODUCIBILITY,
        ScoreDimension.EVIDENCE,
        ScoreDimension.REASONING,
        ScoreDimension.METHOD,
    ),
    # Honest per-stage estimate for the required path only (core path,
    # matching every prior lesson's own convention of excluding the
    # optional mastery act) - not reverse-engineered toward any target.
    # +2 over the original estimate for the corrective follow-up's new
    # duration_schema_check beat (a guaranteed real look at the migration
    # note before declaring its contract).
    estimated_minutes=33,
    related_handbook_entry_id="schema_is_a_contract",
    scorer=score_lesson_six,
)
