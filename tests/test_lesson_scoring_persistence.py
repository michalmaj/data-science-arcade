"""Regression coverage for a real product bug: course_map_scene.py's own
_start_lesson persists `runner.definition.scorer or default_scorer` - the
correct architecture - but a lesson whose LessonDefinition never actually
sets `scorer` silently falls back to default_scorer for the SAVED
evaluation even when its own scenario.py feedback stage already computes
and displays a real, content-aware one. L09 through L17 all had this bug
(each already has a dedicated score_lesson_* function, none of their
LessonDefinitions wired it) before this fix.

This file audits every lesson package under lessons/ dynamically (never a
hardcoded lesson-number list) so a future lesson that adds a score_lesson_*
function but forgets to wire it onto its own LessonDefinition fails here
immediately, the same way L09-L17 should have."""

import glob
import importlib
import inspect
import os

import pytest

from data_science_arcade.lessons.framework.definition import LessonDefinition

_LESSONS_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "src", "data_science_arcade", "lessons"
)


def _discover_lesson_packages() -> list[str]:
    pattern = os.path.join(_LESSONS_ROOT, "l[0-9][0-9]_*")
    return sorted(os.path.basename(path) for path in glob.glob(pattern) if os.path.isdir(path))


LESSON_PACKAGES = _discover_lesson_packages()

# Lessons whose scoring.py already exposes a cheap, reusable `_result()`
# representative-result builder in their own scoring test module - the
# same range this bug actually affected (L09-L17). L01-L08 already had
# `scorer` correctly wired (confirmed by the parametrized test below,
# which covers every package) and have no such reusable fixture; their
# own dimension_scores/scoring_dimensions agreement is exercised
# indirectly by their existing full-playthrough scenario tests instead of
# duplicated here.
_LESSONS_WITH_REPRESENTATIVE_RESULT_FIXTURES = tuple(range(9, 18))


@pytest.mark.parametrize("package", LESSON_PACKAGES)
def test_every_lesson_with_a_dedicated_scorer_has_it_wired_onto_its_definition(package: str) -> None:
    scoring_module = importlib.import_module(f"data_science_arcade.lessons.{package}.scoring")
    score_fns = [
        obj
        for name, obj in vars(scoring_module).items()
        if name.startswith("score_lesson_") and inspect.isfunction(obj) and obj.__module__ == scoring_module.__name__
    ]
    if not score_fns:
        pytest.skip(f"{package}.scoring has no dedicated score_lesson_* function yet")
    assert len(score_fns) == 1, f"{package}.scoring defines more than one score_lesson_* function - update this test's discovery"
    score_fn = score_fns[0]

    definition_module = importlib.import_module(f"data_science_arcade.lessons.{package}.definition")
    definitions = [
        obj for obj in vars(definition_module).values() if isinstance(obj, LessonDefinition)
    ]
    assert len(definitions) == 1, f"{package}.definition doesn't expose exactly one LessonDefinition constant"
    definition = definitions[0]

    assert definition.scorer is not None, (
        f"{package}: has a dedicated {score_fn.__name__} but LessonDefinition.scorer is None - "
        "the persisted evaluation silently falls back to default_scorer"
    )
    assert definition.scorer is score_fn, f"{package}: LessonDefinition.scorer is not its own {score_fn.__name__}"


@pytest.mark.parametrize("lesson_number", _LESSONS_WITH_REPRESENTATIVE_RESULT_FIXTURES)
def test_representative_result_dimension_scores_match_declared_scoring_dimensions(lesson_number: int) -> None:
    package = next(p for p in LESSON_PACKAGES if p.startswith(f"l{lesson_number:02d}_"))
    scoring_module = importlib.import_module(f"data_science_arcade.lessons.{package}.scoring")
    definition_module = importlib.import_module(f"data_science_arcade.lessons.{package}.definition")
    test_module = importlib.import_module(f"test_lesson{lesson_number:02d}_scoring")

    definition = next(obj for obj in vars(definition_module).values() if isinstance(obj, LessonDefinition))
    score_fn = next(
        obj
        for name, obj in vars(scoring_module).items()
        if name.startswith("score_lesson_") and inspect.isfunction(obj) and obj.__module__ == scoring_module.__name__
    )
    result = test_module._result()

    evaluation = score_fn(result, definition, hints_used=0)

    assert set(evaluation.dimension_scores) == set(definition.scoring_dimensions), (
        f"{package}: score_fn's own dimension_scores keys don't match LessonDefinition.scoring_dimensions - "
        "LessonFeedbackScene renders exactly the declared dimensions, so a mismatch here means either a "
        "dimension silently never renders or the scorer emits one the definition never declared"
    )
