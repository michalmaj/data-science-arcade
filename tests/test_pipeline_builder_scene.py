import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.aggregation import AggregateOption, AggregationRequest, GroupByOption
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.workbench.context import LessonContext

SCHEMA = Schema(columns=(ColumnSchema("group_a", "object"), ColumnSchema("group_b", "object"), ColumnSchema("amount", "float64")))

FRAME = pd.DataFrame(
    [("x", "p", 10.0), ("x", "p", 20.0), ("y", "q", 5.0)],
    columns=["group_a", "group_b", "amount"],
)

DATASET = Dataset(name="synthetic", frame=FRAME, schema=SCHEMA, history=())

REQUESTS = (
    AggregationRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        value_column="amount",
        group_by_options=(
            GroupByOption("by_a", "common.on", "group_a"),
            GroupByOption("by_b", "common.off", "group_b"),
        ),
        aggregate_options=(
            AggregateOption("sum", "common.on", "sum"),
            AggregateOption("count", "common.off", "count"),
        ),
    ),
    AggregationRequest(
        key="request_b",
        prompt_key="app.title",
        hint_key="common.back",
        value_column="amount",
        group_by_options=(
            GroupByOption("by_a", "common.on", "group_a"),
            GroupByOption("by_b", "common.off", "group_b"),
        ),
        aggregate_options=(
            AggregateOption("sum", "common.on", "sum"),
            AggregateOption("count", "common.off", "count"),
        ),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return PipelineBuilderScene(app, "app.title", DATASET, REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_only_group_by_does_not_enable_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # group_by: by_a

        assert scene.next_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_both_group_by_and_aggregate_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # group_by: by_a
        scene.buttons.buttons[2].on_activate()  # aggregate: sum

        assert scene.choices == {"request_a": ("by_a", "sum")}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_is_a_no_op_before_both_choices_are_made():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene._next()

        assert scene.request_index == 0
    finally:
        pygame.quit()


def test_next_advances_and_back_restores_the_earlier_full_choice():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[2].on_activate()
        scene.next_button.on_activate()

        assert scene.request_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.request_index == 0
        assert scene._group_by_choice == "by_a"
        assert scene._aggregate_choice == "sum"
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[2].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # request_b group_by: by_b
        scene.buttons.buttons[3].on_activate()  # request_b aggregate: count

        scene.next_button.on_activate()

        assert collected == [{"request_a": ("by_a", "sum"), "request_b": ("by_b", "count")}]
    finally:
        pygame.quit()


def test_the_live_preview_reflects_real_pandas_computation():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # group_by: group_a
        scene.buttons.buttons[2].on_activate()  # aggregate: sum

        request = scene._current_request()
        group_by = scene._selected_group_by(request)
        aggregate = scene._selected_aggregate(request)
        grouped = dict(DATASET.frame.groupby(group_by.column)[request.value_column].agg(aggregate.func).items())

        assert grouped == {"x": 30.0, "y": 5.0}
    finally:
        pygame.quit()


def test_with_no_context_given_a_fresh_one_is_created():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert isinstance(scene.context, LessonContext)
        assert scene.context.actions == ()
    finally:
        pygame.quit()


def test_committing_a_complete_choice_records_a_real_action_and_evidence_with_realistic_pandas_code():
    app = _init_app()
    try:
        context = LessonContext()
        scene = PipelineBuilderScene(app, "app.title", DATASET, REQUESTS, lambda choices: None, context=context)
        scene.buttons.buttons[0].on_activate()  # group_by: by_a (column="group_a")
        scene.buttons.buttons[2].on_activate()  # aggregate: sum (func="sum")

        assert len(context.actions) == 1
        action = context.actions[0]
        assert action.python_code == "synthetic.groupby('group_a')['amount'].sum()"
        assert len(context.evidence) == 1
        assert context.evidence[0].source_action_id == action.id
    finally:
        pygame.quit()


def test_committing_two_different_requests_records_two_separate_actions():
    app = _init_app()
    try:
        context = LessonContext()
        scene = PipelineBuilderScene(app, "app.title", DATASET, REQUESTS, lambda choices: None, context=context)
        scene.buttons.buttons[0].on_activate()  # request_a group_by: by_a
        scene.buttons.buttons[2].on_activate()  # request_a aggregate: sum
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # request_b group_by: by_b
        scene.buttons.buttons[3].on_activate()  # request_b aggregate: count

        assert len(context.actions) == 2  # different request.key values - not merged
    finally:
        pygame.quit()


def test_recommitting_the_same_request_updates_its_one_slot_instead_of_accumulating():
    # Recording is keyed by request.key, so re-picking for the *same*
    # request - however many times, however the choice changes along the
    # way - always ends up as exactly one line reflecting the current pick,
    # not one line per click.
    app = _init_app()
    try:
        context = LessonContext()
        scene = PipelineBuilderScene(app, "app.title", DATASET, REQUESTS, lambda choices: None, context=context)
        scene.buttons.buttons[0].on_activate()  # group_by: by_a
        scene.buttons.buttons[2].on_activate()  # aggregate: sum -> commits (by_a, sum)
        scene.buttons.buttons[3].on_activate()  # aggregate: count -> commits (by_a, count)
        scene.buttons.buttons[2].on_activate()  # back to sum -> re-commits (by_a, sum)

        assert len(context.actions) == 1  # one slot for "request_a", not three
        assert context.actions[0].python_code == "synthetic.groupby('group_a')['amount'].sum()"
        assert len(context.evidence) == 1
    finally:
        pygame.quit()


def test_l12s_own_usage_pattern_is_unaffected_without_a_context():
    # Mirrors exactly how l12_groupby_kitchen/scenario.py constructs this
    # scene today - no context kwarg at all - confirming the new param is
    # fully backward compatible with the one real lesson using it.
    app = _init_app()
    try:
        collected = []
        scene = PipelineBuilderScene(app, "app.title", DATASET, REQUESTS, lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[2].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()
        scene.buttons.buttons[3].on_activate()
        scene.next_button.on_activate()

        assert collected == [{"request_a": ("by_a", "sum"), "request_b": ("by_b", "count")}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_a_full_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # no choice yet - the "pick both" placeholder path
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # only group_by chosen
            scene.buttons.buttons[2].on_activate()
            scene.draw(app.logical_surface)  # both chosen - the live table path
    finally:
        pygame.quit()
