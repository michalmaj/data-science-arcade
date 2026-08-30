from dataclasses import dataclass

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import default_scorer


@dataclass(frozen=True)
class _FakeResult:
    completed: bool

    def completed_thoughtfully(self) -> bool:
        return self.completed


DEFINITION = LessonDefinition(
    id="fake",
    chapter=1,
    number=1,
    title_key="x",
    objective_keys=("x",),
    scoring_dimensions=(ScoreDimension.REASONING, ScoreDimension.EVIDENCE),
    estimated_minutes=15,
)


def test_scores_only_the_dimensions_the_lesson_declares():
    evaluation = default_scorer(_FakeResult(True), DEFINITION, hints_used=0)
    assert set(evaluation.dimension_scores) == {ScoreDimension.REASONING, ScoreDimension.EVIDENCE}


def test_completed_scores_higher_than_incomplete_at_equal_hints_used():
    completed = default_scorer(_FakeResult(True), DEFINITION, hints_used=0)
    incomplete = default_scorer(_FakeResult(False), DEFINITION, hints_used=0)
    for dimension in DEFINITION.scoring_dimensions:
        assert completed.dimension_scores[dimension] > incomplete.dimension_scores[dimension]


def test_more_hints_used_lowers_the_score_but_never_below_the_floor():
    no_hints = default_scorer(_FakeResult(True), DEFINITION, hints_used=0)
    some_hints = default_scorer(_FakeResult(True), DEFINITION, hints_used=2)
    many_hints = default_scorer(_FakeResult(True), DEFINITION, hints_used=50)

    for dimension in DEFINITION.scoring_dimensions:
        assert no_hints.dimension_scores[dimension] > some_hints.dimension_scores[dimension]
        assert many_hints.dimension_scores[dimension] == 20.0  # floor, not negative


def test_completed_thoughtfully_and_hints_used_are_carried_through():
    evaluation = default_scorer(_FakeResult(True), DEFINITION, hints_used=3)
    assert evaluation.completed_thoughtfully is True
    assert evaluation.hints_used == 3


def test_observations_mention_hints_only_when_any_were_used():
    with_hints = default_scorer(_FakeResult(True), DEFINITION, hints_used=1)
    without_hints = default_scorer(_FakeResult(True), DEFINITION, hints_used=0)

    assert any(obs.text_key == "lesson.feedback.hints_used" for obs in with_hints.observations)
    assert not any(obs.text_key == "lesson.feedback.hints_used" for obs in without_hints.observations)


def test_completion_observation_reflects_completion_state():
    completed = default_scorer(_FakeResult(True), DEFINITION, hints_used=0)
    incomplete = default_scorer(_FakeResult(False), DEFINITION, hints_used=0)

    assert completed.observations[0].text_key == "lesson.feedback.completed"
    assert incomplete.observations[0].text_key == "lesson.feedback.incomplete"
