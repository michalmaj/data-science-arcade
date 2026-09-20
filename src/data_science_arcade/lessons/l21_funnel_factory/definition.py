from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l21_funnel_factory.scoring import score_lesson_twenty_one

LESSON_21 = LessonDefinition(
    id="ds21_funnel_factory",
    chapter=5,
    number=21,
    title_key="lesson.l21.title",
    objective_keys=(
        "lesson.l21.objective1",
        "lesson.l21.objective2",
        "lesson.l21.objective3",
    ),
    scoring_dimensions=(ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
    # Raised from 20 after a real content-density check (L21-L30
    # integration-audit triage): 12 real stages (one more than the
    # 11-stage 22-24 min siblings this chapter otherwise shares), 6 real
    # funnel-definition micro-decisions across two full passes, two
    # multi-value reveals (3+ and 2+ real numbers each) each ending in a
    # real interpret decision, a 5-step Final Decision (4 fields +
    # 5-8-item evidence citation), and an optional 3-field mastery task -
    # genuinely denser than a 20-minute lesson, not adjusted to match any
    # sibling's own number mechanically.
    estimated_minutes=23,
    related_handbook_entry_id="a_funnel_is_a_definition",
    scorer=score_lesson_twenty_one,
)
