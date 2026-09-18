from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l28_chart_crime_lab.scoring import score_lesson_twenty_eight

LESSON_28 = LessonDefinition(
    id="ds28_chart_crime_lab",
    chapter=6,
    number=28,
    title_key="lesson.l28.title",
    objective_keys=(
        "lesson.l28.objective1",
        "lesson.l28.objective2",
        "lesson.l28.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=26,
    related_handbook_entry_id="a_truthful_chart_can_still_mislead",
    scorer=score_lesson_twenty_eight,
)
