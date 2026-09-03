from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l05_sampling_mission.scoring import score_lesson_five

LESSON_05 = LessonDefinition(
    id="ds05_sampling_mission",
    chapter=1,
    number=5,
    title_key="lesson.l05.title",
    objective_keys=(
        "lesson.l05.objective1",
        "lesson.l05.objective2",
        "lesson.l05.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.DATA_QUALITY,
        ScoreDimension.METHOD,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.REASONING,
    ),
    # Honest per-stage estimate for the required path only (core path,
    # matching l01-l04's own convention of excluding the optional mastery
    # act) - not reverse-engineered toward any target.
    estimated_minutes=31,
    scorer=score_lesson_five,
)
