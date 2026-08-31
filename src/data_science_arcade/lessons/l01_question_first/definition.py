from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l01_question_first.scoring import score_lesson_one

LESSON_01 = LessonDefinition(
    id="ds01_question_first",
    chapter=1,
    number=1,
    title_key="lesson.l01.title",
    objective_keys=(
        "lesson.l01.objective1",
        "lesson.l01.objective2",
        "lesson.l01.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.OVERCONFIDENCE,
    ),
    # This PR's real target, not a placeholder: the rebuild's own act
    # structure sums to 77 real minutes across 16 stages (before the
    # optional mastery act), each stage built around a real operation or
    # decision rather than dialogue - see decisions/IMPLEMENTATION_STATE.md
    # for the full act-by-act budget. Still only a planning estimate until
    # a real human stopwatch playthrough confirms it - the acceptance test
    # for this PR specifically, not this number on its own.
    estimated_minutes=77,
    related_handbook_entry_id="asking_an_analytical_question",
    scorer=score_lesson_one,
)
