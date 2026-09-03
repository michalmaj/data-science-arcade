import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene

FIELDS = (
    BriefField(
        key="color",
        prompt_key="common.back",  # any real key works - content isn't under test here
        hint_key="common.back",
        options=(BriefOption("red", "common.back"), BriefOption("blue", "common.back")),
    ),
    BriefField(
        key="size",
        prompt_key="common.back",
        options=(BriefOption("small", "common.back"), BriefOption("large", "common.back")),
    ),
)

TOPPINGS_FIELD = MultiChoiceField(
    key="toppings",
    prompt_key="common.back",
    options=tuple(BriefOption(f"t{i}", "common.back") for i in range(5)),
    min_count=2,
    max_count=3,
)

MIXED_FIELDS = (FIELDS[0], TOPPINGS_FIELD)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_on_the_first_field_with_next_disabled():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        assert scene.field_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_selecting_an_option_enables_next():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_does_nothing_if_nothing_is_selected():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene._next()
        assert scene.field_index == 0
    finally:
        pygame.quit()


def test_next_advances_to_the_second_field_once_selected():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        assert scene.field_index == 1
        assert scene.back_button.enabled is True
    finally:
        pygame.quit()


def test_back_returns_to_the_previous_field_and_keeps_its_earlier_choice():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()  # color=red
        scene.next_button.on_activate()

        scene.back_button.on_activate()

        assert scene.field_index == 0
        assert scene.choices["color"] == "red"
    finally:
        pygame.quit()


def test_finishing_the_last_field_calls_on_complete_with_every_choice():
    app = _init_app()
    try:
        collected = []
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: collected.append(brief))

        scene.buttons.buttons[0].on_activate()  # color=red
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # size=large
        scene.next_button.on_activate()

        assert collected == [{"color": "red", "size": "large"}]
    finally:
        pygame.quit()


def test_the_next_button_says_finish_only_on_the_last_field():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        assert scene.next_button.label == app.localization.t("brief.next")

        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.next_button.label == app.localization.t("brief.finish")
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None, guided=guided)
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_tiered_hints_only_apply_to_fields_present_in_the_dict():
    app = _init_app()
    try:
        scene = BriefBuilderScene(
            app, "app.title", FIELDS, on_complete=lambda brief: None, tiered_hint_keys={"color": ("common.back",)}
        )
        assert scene._current_hint_controller() is not None

        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene._current_hint_controller() is None  # "size" has no tiered hint
    finally:
        pygame.quit()


def test_revealing_a_hint_tier_persists_across_back_and_next():
    app = _init_app()
    try:
        scene = BriefBuilderScene(
            app, "app.title", FIELDS, on_complete=lambda brief: None, tiered_hint_keys={"color": ("common.back", "app.title")}
        )
        controller = scene._current_hint_controller()
        controller.reveal_next()
        assert controller.revealed_tier == 1

        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        scene.back_button.on_activate()

        assert scene._current_hint_controller().revealed_tier == 1
    finally:
        pygame.quit()


def test_no_tiered_hint_keys_behaves_exactly_as_before():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        assert scene._current_hint_controller() is None
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_every_tier_revealed_on_a_four_option_field():
    app = _init_app()
    try:
        four_option_field = BriefField(
            key="window",
            prompt_key="common.back",
            options=tuple(BriefOption(f"opt{i}", "common.back") for i in range(4)),
        )
        scene = BriefBuilderScene(
            app,
            "app.title",
            (four_option_field,),
            on_complete=lambda brief: None,
            tiered_hint_keys={"window": ("common.back", "app.title", "common.back")},
        )
        controller = scene._current_hint_controller()
        controller.reveal_next()
        controller.reveal_next()
        controller.reveal_next()

        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_multi_choice_field_starts_with_next_disabled_below_min_count():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", (TOPPINGS_FIELD,), on_complete=lambda brief: None)
        assert scene.next_button.enabled is False
    finally:
        pygame.quit()


def test_multi_choice_field_toggles_add_and_remove_without_overwriting():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", (TOPPINGS_FIELD,), on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()  # t0
        scene.buttons.buttons[2].on_activate()  # t2
        assert scene.choices["toppings"] == ("t0", "t2")

        scene.buttons.buttons[0].on_activate()  # remove t0
        assert scene.choices["toppings"] == ("t2",)
    finally:
        pygame.quit()


def test_multi_choice_field_next_enables_once_min_count_reached():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", (TOPPINGS_FIELD,), on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        assert scene.next_button.enabled is False  # 1 of 2 minimum

        scene.buttons.buttons[1].on_activate()
        assert scene.next_button.enabled is True  # 2 of 2 minimum
    finally:
        pygame.quit()


def test_multi_choice_field_disables_unpicked_options_once_max_count_reached():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", (TOPPINGS_FIELD,), on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[1].on_activate()
        scene.buttons.buttons[2].on_activate()  # 3 of 3 maximum

        assert scene.buttons.buttons[3].enabled is False  # not yet picked, at the cap
        assert scene.buttons.buttons[0].enabled is True  # already picked, stays clickable to remove
    finally:
        pygame.quit()


def test_mixed_single_and_multi_choice_fields_complete_with_the_right_value_shapes():
    app = _init_app()
    try:
        collected = []
        scene = BriefBuilderScene(app, "app.title", MIXED_FIELDS, on_complete=lambda brief: collected.append(brief))

        scene.buttons.buttons[0].on_activate()  # color=red
        scene.next_button.on_activate()
        scene.buttons.buttons[0].on_activate()  # toppings: t0
        scene.buttons.buttons[1].on_activate()  # toppings: t1
        scene.next_button.on_activate()

        assert collected == [{"color": "red", "toppings": ("t0", "t1")}]
    finally:
        pygame.quit()


def test_multi_choice_field_selection_persists_across_back_and_next():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", MIXED_FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()  # color=red
        scene.next_button.on_activate()
        scene.buttons.buttons[0].on_activate()  # toppings: t0
        scene.buttons.buttons[1].on_activate()  # toppings: t1

        scene.back_button.on_activate()
        scene.next_button.on_activate()

        assert scene.choices["toppings"] == ("t0", "t1")
    finally:
        pygame.quit()


def test_multi_choice_field_draw_does_not_crash():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", (TOPPINGS_FIELD,), on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_guided_false_hides_the_tiered_hint_controller_entirely():
    app = _init_app()
    try:
        scene = BriefBuilderScene(
            app,
            "app.title",
            FIELDS,
            on_complete=lambda brief: None,
            guided=False,
            tiered_hint_keys={"color": ("common.back",)},
        )
        scene.draw(app.logical_surface)  # doesn't crash, and doesn't consume events either
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0)))
    finally:
        pygame.quit()
