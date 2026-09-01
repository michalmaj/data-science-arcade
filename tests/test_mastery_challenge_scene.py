import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene, MasteryOption, MetricValue
from data_science_arcade.workbench.context import LessonContext

METRIC_OPTIONS = (MasteryOption("total", "common.back"), MasteryOption("average", "common.back"))
INTERPRET_OPTIONS = (MasteryOption("returning_higher", "common.back"), MasteryOption("about_same", "common.back"))


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _compute(metric_key: str) -> tuple[MetricValue, MetricValue]:
    return (
        MetricValue("common.back", 100.0, python_code="orders.groupby('household_id').size().ge(2).sum()"),
        MetricValue("dialogue.continue_hint", 50.0),
    )


def _make_scene(app, on_complete=lambda engaged, metric, interpretation: None, context=None):
    return MasteryChallengeScene(
        app,
        title_key="app.title",
        narrative_keys=("app.title",),
        metric_prompt_key="app.title",
        metric_options=METRIC_OPTIONS,
        compute=_compute,
        interpret_prompt_key="app.title",
        interpret_options=INTERPRET_OPTIONS,
        on_complete=on_complete,
        context=context if context is not None else LessonContext(),
    )


def test_starts_on_the_offer_phase():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene._phase.name == "OFFER"
        assert len(scene.buttons.buttons) == 2
    finally:
        pygame.quit()


def test_skip_fires_on_complete_immediately_with_engaged_false():
    app = _init_app()
    try:
        calls = []
        scene = _make_scene(app, on_complete=lambda engaged, metric, interpretation: calls.append((engaged, metric, interpretation)))

        scene.buttons.buttons[1].on_activate()  # skip

        assert calls == [(False, None, None)]
    finally:
        pygame.quit()


def test_skip_records_no_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)

        scene.buttons.buttons[1].on_activate()

        assert context.evidence == ()
    finally:
        pygame.quit()


def test_engage_moves_to_the_pick_phase():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # engage
        assert scene._phase.name == "PICK"
        assert len(scene.buttons.buttons) == len(METRIC_OPTIONS)
    finally:
        pygame.quit()


def test_picking_a_metric_computes_and_moves_to_the_result_phase():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # engage
        scene.buttons.buttons[0].on_activate()  # pick "total"

        assert scene._phase.name == "RESULT"
        assert scene._comparison == (
            MetricValue("common.back", 100.0, python_code="orders.groupby('household_id').size().ge(2).sum()"),
            MetricValue("dialogue.continue_hint", 50.0),
        )
        assert scene.finish_button.enabled is False  # no interpretation picked yet
    finally:
        pygame.quit()


def test_finish_does_nothing_until_an_interpretation_is_picked():
    app = _init_app()
    try:
        calls = []
        scene = _make_scene(app, on_complete=lambda e, m, i: calls.append((e, m, i)))
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[0].on_activate()

        scene._finish()

        assert calls == []
    finally:
        pygame.quit()


def test_completing_the_full_path_records_the_comparison_as_evidence_and_fires_on_complete():
    app = _init_app()
    try:
        calls = []
        context = LessonContext()
        scene = _make_scene(app, on_complete=lambda e, m, i: calls.append((e, m, i)), context=context)

        scene.buttons.buttons[0].on_activate()  # engage
        scene.buttons.buttons[1].on_activate()  # pick "average"
        scene.buttons.buttons[0].on_activate()  # interpret "returning_higher"
        scene.finish_button.on_activate()

        assert calls == [(True, "average", "returning_higher")]
        assert len(context.evidence) == 2
        assert context.evidence[0].detail == "$100"
        assert context.evidence[1].detail == "$50"
    finally:
        pygame.quit()


def test_finishing_records_a_metrics_own_python_code_onto_its_action():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)

        scene.buttons.buttons[0].on_activate()  # engage
        scene.buttons.buttons[0].on_activate()  # pick "total"
        scene.buttons.buttons[0].on_activate()  # interpret "returning_higher"
        scene.finish_button.on_activate()

        coded = next(a for a in context.actions if a.label_key == "common.back")
        assert coded.python_code == "orders.groupby('household_id').size().ge(2).sum()"
        uncoded = next(a for a in context.actions if a.label_key == "dialogue.continue_hint")
        assert uncoded.python_code is None
    finally:
        pygame.quit()


def test_three_interpret_options_still_fit_above_the_finish_button():
    # L01's real interpret_options has 2 entries, which is what this
    # scene's layout was implicitly validated against until L02 supplied
    # a real 3-entry set and the 3rd option rendered under the Finish
    # button - caught only by a real screenshot, not by any prior test.
    app = _init_app()
    try:
        three_options = (
            MasteryOption("a", "common.back"),
            MasteryOption("b", "common.back"),
            MasteryOption("c", "common.back"),
        )
        scene = MasteryChallengeScene(
            app,
            title_key="app.title",
            narrative_keys=("app.title",),
            metric_prompt_key="app.title",
            metric_options=METRIC_OPTIONS,
            compute=_compute,
            interpret_prompt_key="app.title",
            interpret_options=three_options,
            on_complete=lambda engaged, metric, interpretation: None,
            context=LessonContext(),
        )
        scene.buttons.buttons[0].on_activate()  # engage
        scene.buttons.buttons[0].on_activate()  # pick "total"

        assert scene._phase.name == "RESULT"
        last_option_bottom = scene.buttons.buttons[2].rect.bottom
        finish_top = scene.finish_button.rect.top
        assert last_option_bottom <= finish_top
    finally:
        pygame.quit()


def test_draw_does_not_crash_in_any_phase():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.draw(app.logical_surface)
        scene.buttons.buttons[0].on_activate()
        scene.draw(app.logical_surface)
        scene.buttons.buttons[0].on_activate()
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()
