from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l20_ab_test_commander.scoring import score_lesson_twenty

LESSON_20 = LessonDefinition(
    id="ds20_ab_test_commander",
    chapter=4,
    number=20,
    title_key="lesson.l20.title",
    objective_keys=(
        "lesson.l20.objective1",
        "lesson.l20.objective2",
        "lesson.l20.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY, ScoreDimension.OVERCONFIDENCE),
    estimated_minutes=21,
    related_handbook_entry_id="an_experiment_needs_a_decision_rule",
    scorer=score_lesson_twenty,
)
