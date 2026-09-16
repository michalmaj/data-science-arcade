from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l24_survey_bureau.scoring import score_lesson_twenty_four

LESSON_24 = LessonDefinition(
    id="ds24_survey_bureau",
    chapter=5,
    number=24,
    title_key="lesson.l24.title",
    objective_keys=(
        "lesson.l24.objective1",
        "lesson.l24.objective2",
        "lesson.l24.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=25,
    related_handbook_entry_id="a_survey_is_a_sample_not_a_census",
    scorer=score_lesson_twenty_four,
)
