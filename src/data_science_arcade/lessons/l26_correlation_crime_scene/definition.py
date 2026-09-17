from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l26_correlation_crime_scene.scoring import score_lesson_twenty_six

LESSON_26 = LessonDefinition(
    id="ds26_correlation_crime_scene",
    chapter=6,
    number=26,
    title_key="lesson.l26.title",
    objective_keys=(
        "lesson.l26.objective1",
        "lesson.l26.objective2",
        "lesson.l26.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=24,
    related_handbook_entry_id="a_correlation_doesnt_name_its_own_cause",
    scorer=score_lesson_twenty_six,
)
