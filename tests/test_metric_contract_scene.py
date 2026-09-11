import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.ui.metric_contract_scene import MetricContractScene, MetricDefinitionOption
from data_science_arcade.workbench.context import LessonContext

ELIGIBLE = MetricDefinitionOption(
    key="eligible_population",
    label_key="lesson.l16.metric.eligible_population",
    numerator_key="lesson.l16.metric.numerator.resolved_24h",
    denominator_key="lesson.l16.metric.denominator.eligible_population",
    window_key="lesson.l16.metric.window.no_wait",
    mirror_code="definition_a_rate = 0.82",
    value=0.82,
)
CLOSED_ONLY = MetricDefinitionOption(
    key="closed_only",
    label_key="lesson.l16.metric.closed_only",
    numerator_key="lesson.l16.metric.numerator.resolved_24h",
    denominator_key="lesson.l16.metric.denominator.closed_only",
    window_key="lesson.l16.metric.window.no_wait",
    mirror_code="definition_b_rate = 0.867",
    value=0.867,
)
DURABLE = MetricDefinitionOption(
    key="durable",
    label_key="lesson.l16.metric.durable",
    numerator_key="lesson.l16.metric.numerator.durable",
    denominator_key="lesson.l16.metric.denominator.durable",
    window_key="lesson.l16.metric.window.durable",
    mirror_code="durable_resolution_rate = 0.835",
    value=0.835,
)
CANDIDATES = (ELIGIBLE, CLOSED_ONLY, DURABLE)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _surface() -> pygame.Surface:
    return pygame.Surface(LOGICAL_SIZE)


def test_no_choice_disables_finish_and_picking_one_enables_it():
    app = _init_app()
    try:
        context = LessonContext()
        scene = MetricContractScene(app, "t", "a", CANDIDATES, lambda c: None, context)
        assert scene.finish_button.enabled is False
        scene.buttons.buttons[1].on_activate()  # closed_only
        assert scene.choice == "closed_only"
        assert scene.finish_button.enabled is True
    finally:
        pygame.quit()


def test_initial_choice_seeds_the_scene_for_a_real_revision():
    app = _init_app()
    try:
        context = LessonContext()
        scene = MetricContractScene(app, "t", "a", CANDIDATES, lambda c: None, context, initial_choice="durable")
        assert scene.choice == "durable"
        assert scene.finish_button.enabled is True
    finally:
        pygame.quit()


def test_finish_records_one_action_for_whichever_candidate_is_chosen():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = MetricContractScene(app, "t", "a", CANDIDATES, completed.append, context)
        scene.buttons.buttons[2].on_activate()  # durable
        scene.finish_button.on_activate()

        assert completed == ["durable"]
        assert len(context.actions) == 1
        assert context.actions[0].python_code == DURABLE.mirror_code
    finally:
        pygame.quit()


def test_revision_overwrites_the_same_slot_never_appending_a_second_action():
    # Matches SegmentMixScene's own "key by what's actually shown, never a
    # fixed shared slot" fix - here the slot IS fixed on purpose (there is
    # only ever one real primary-metric contract), so a revision must
    # UPDATE the one real action in place, not double it.
    app = _init_app()
    try:
        context = LessonContext()
        first = MetricContractScene(app, "t", "a", CANDIDATES, lambda c: None, context)
        first.buttons.buttons[0].on_activate()  # eligible_population
        first.finish_button.on_activate()

        second = MetricContractScene(app, "t", "a", CANDIDATES, lambda c: None, context, initial_choice="eligible_population")
        second.buttons.buttons[2].on_activate()  # durable
        second.finish_button.on_activate()

        assert len(context.actions) == 1
        assert context.actions[0].python_code == DURABLE.mirror_code
    finally:
        pygame.quit()


def test_draw_smoke_with_and_without_a_choice():
    app = _init_app()
    try:
        context = LessonContext()
        scene = MetricContractScene(app, "t", "a", CANDIDATES, lambda c: None, context)
        scene.draw(_surface())
        scene.buttons.buttons[0].on_activate()
        scene.draw(_surface())
    finally:
        pygame.quit()
