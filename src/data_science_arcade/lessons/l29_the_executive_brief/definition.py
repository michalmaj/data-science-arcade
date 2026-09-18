from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l29_the_executive_brief.scoring import score_lesson_twenty_nine

LESSON_29 = LessonDefinition(
    id="ds29_the_executive_brief",
    chapter=6,
    number=29,
    title_key="lesson.l29.title",
    objective_keys=(
        "lesson.l29.objective1",
        "lesson.l29.objective2",
        "lesson.l29.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.COMMUNICATION,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=20,
    related_handbook_entry_id="not_every_true_fact_belongs_in_the_headline",
    scorer=score_lesson_twenty_nine,
)
