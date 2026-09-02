from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l03_api_courier.scoring import score_lesson_three

LESSON_03 = LessonDefinition(
    id="ds03_api_courier",
    chapter=1,
    number=3,
    title_key="lesson.l03.title",
    objective_keys=(
        "lesson.l03.objective1",
        "lesson.l03.objective2",
        "lesson.l03.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.METHOD,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.REASONING,
    ),
    # Honest per-stage estimate for the required path only (core path,
    # matching l01/l02's own convention of excluding the optional mastery
    # act) - not reverse-engineered toward any target.
    estimated_minutes=33,
    scorer=score_lesson_three,
)
