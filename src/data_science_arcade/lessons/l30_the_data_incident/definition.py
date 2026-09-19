from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l30_the_data_incident.scoring import score_lesson_thirty

LESSON_30 = LessonDefinition(
    id="ds30_the_data_incident",
    chapter=6,
    number=30,
    title_key="lesson.l30.title",
    objective_keys=(
        "lesson.l30.objective1",
        "lesson.l30.objective2",
        "lesson.l30.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.COMMUNICATION,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=35,
    scorer=score_lesson_thirty,
)
