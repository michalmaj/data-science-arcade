from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l22_cohort_observatory.scoring import score_lesson_twenty_two

LESSON_22 = LessonDefinition(
    id="ds22_cohort_observatory",
    chapter=5,
    number=22,
    title_key="lesson.l22.title",
    objective_keys=(
        "lesson.l22.objective1",
        "lesson.l22.objective2",
        "lesson.l22.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=23,
    related_handbook_entry_id="cohorts_need_the_same_clock",
    scorer=score_lesson_twenty_two,
)
