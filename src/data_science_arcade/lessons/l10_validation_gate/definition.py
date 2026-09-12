from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l10_validation_gate.scoring import score_lesson_ten

LESSON_10 = LessonDefinition(
    id="ds10_validation_gate",
    chapter=2,
    number=10,
    title_key="lesson.l10.title",
    objective_keys=(
        "lesson.l10.objective1",
        "lesson.l10.objective2",
        "lesson.l10.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.REPRODUCIBILITY,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=29,
    related_handbook_entry_id="schema_is_a_contract",
    scorer=score_lesson_ten,
)
