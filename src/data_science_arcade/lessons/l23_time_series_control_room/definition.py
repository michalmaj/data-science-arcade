from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.l23_time_series_control_room.scoring import score_lesson_twenty_three

LESSON_23 = LessonDefinition(
    id="ds23_time_series_control_room",
    chapter=5,
    number=23,
    title_key="lesson.l23.title",
    objective_keys=(
        "lesson.l23.objective1",
        "lesson.l23.objective2",
        "lesson.l23.objective3",
    ),
    scoring_dimensions=(
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.OVERCONFIDENCE,
    ),
    estimated_minutes=22,
    related_handbook_entry_id="time_series_have_a_calendar",
    scorer=score_lesson_twenty_three,
)
