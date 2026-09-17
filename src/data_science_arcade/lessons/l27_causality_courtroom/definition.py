from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l27_causality_courtroom.scoring import score_lesson_twenty_seven

LESSON_27 = LessonDefinition(
    id="ds27_causality_courtroom",
    chapter=6,
    number=27,
    title_key="lesson.l27.title",
    objective_keys=(
        "lesson.l27.objective1",
        "lesson.l27.objective2",
        "lesson.l27.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=24,
    related_handbook_entry_id="a_group_difference_is_not_a_treatment_effect",
    scorer=score_lesson_twenty_seven,
)
