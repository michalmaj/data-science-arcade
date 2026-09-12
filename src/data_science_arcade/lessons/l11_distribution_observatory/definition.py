from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l11_distribution_observatory.scoring import score_lesson_eleven

LESSON_11 = LessonDefinition(
    id="ds11_distribution_observatory",
    chapter=3,
    number=11,
    title_key="lesson.l11.title",
    objective_keys=(
        "lesson.l11.objective1",
        "lesson.l11.objective2",
        "lesson.l11.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.COMMUNICATION,
    ),
    estimated_minutes=21,
    related_handbook_entry_id="a_summary_is_not_the_distribution",
    scorer=score_lesson_eleven,
)
