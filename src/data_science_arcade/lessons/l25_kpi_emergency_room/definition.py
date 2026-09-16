from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l25_kpi_emergency_room.scoring import score_lesson_twenty_five

LESSON_25 = LessonDefinition(
    id="ds25_kpi_emergency_room",
    chapter=5,
    number=25,
    title_key="lesson.l25.title",
    objective_keys=(
        "lesson.l25.objective1",
        "lesson.l25.objective2",
        "lesson.l25.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=22,
    related_handbook_entry_id="an_alert_is_a_symptom_not_a_diagnosis",
    scorer=score_lesson_twenty_five,
)
