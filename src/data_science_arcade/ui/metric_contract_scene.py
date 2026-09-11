from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.core.fonts import get_font
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text, wrap_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
ASK_Y = 46
ASK_MAX_WIDTH = 860
PICKER_Y = 100
PICKER_SIZE = (240, 40)
PICKER_SPACING = 260
VALUE_Y = 158
DETAIL_TOP = 210
DETAIL_LINE_GAP = 8
DETAIL_MAX_WIDTH = 760
FINISH_Y = 470
HINT_Y = 430


@dataclass(frozen=True)
class MetricDefinitionOption:
    """One real, fully self-contained candidate definition - never a bare
    name. `value` is the real, live-computed rate for this candidate at
    whatever moment the calling scenario stage is showing (the early
    snapshot at first pick, a stress-test outcome at a later reveal) -
    precomputed by the caller, the same "scenario computes the real
    numbers, the scene only renders them" split SegmentMixScene's own
    `SegmentRow` already establishes. `mirror_code` is this candidate's
    own real pandas definition - recorded onto the Python Mirror only for
    whichever candidate actually gets picked, never all three at once."""

    key: str
    label_key: str
    numerator_key: str
    denominator_key: str
    window_key: str
    mirror_code: str
    value: float


class MetricContractScene(Scene):
    """Lets the student pick one real candidate primary-metric definition
    from a small, fixed set (2-3 in practice) - each candidate shows its
    own real numerator/denominator/window text plus its own real,
    live-computed value, never a bare label. Picking is a free,
    un-punished toggle; Finish records one real Mirror action for
    whichever candidate is currently selected, keyed by the candidate's
    own key (never a fixed shared slot - the same "key by what was
    actually shown" fix `SegmentMixScene` needed after its own
    Mirror-overwrite bug).

    Reused for both the initial contract-building stage and the later
    revision stage (`initial_choice` seeds the prior pick so re-opening
    this scene doesn't silently reset a student's own already-reasonable
    choice) - the same real, un-punished "revise the whole contract, not
    just a decoration" shape every deepened lesson's own revision stage
    already gives.

    Deliberately not `SegmentSlicerScene` (a before/after-only rate pair,
    no denominator/window preview, no `LessonContext` integration) or
    `SegmentMixScene` (a rate+share table for a fixed pair of segments,
    not a set of competing metric DEFINITIONS of the same one number) -
    neither shape fits a metric contract, so this is its own small, new
    scene rather than a forced reuse."""

    def __init__(
        self,
        app,
        title_key: str,
        ask_prompt_key: str,
        definition_options: tuple[MetricDefinitionOption, ...],
        on_complete: Callable[[str], None],
        context: LessonContext,
        initial_choice: str | None = None,
        hint_key: str | None = None,
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.ask_prompt_key = ask_prompt_key
        self.definition_options = definition_options
        self.on_complete = on_complete
        self.context = context
        self.hint_key = hint_key
        self.guided = guided
        self.choice: str | None = initial_choice
        self._rebuild_buttons()

    def _selected_option(self) -> MetricDefinitionOption | None:
        if self.choice is None:
            return None
        return next(o for o in self.definition_options if o.key == self.choice)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        count = len(self.definition_options)
        start_x = CENTER_X - (count - 1) * PICKER_SPACING // 2
        for index, option in enumerate(self.definition_options):
            rect = pygame.Rect(0, 0, *PICKER_SIZE)
            rect.center = (start_x + index * PICKER_SPACING, PICKER_Y)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        finish_rect = pygame.Rect(0, 0, 160, 44)
        finish_rect.center = (CENTER_X, FINISH_Y)
        self.finish_button = Button(finish_rect, loc.t("brief.finish"), self._finish, enabled=self.choice is not None)
        buttons.append(self.finish_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choice = option_key
            self._rebuild_buttons()

        return choose

    def _finish(self) -> None:
        option = self._selected_option()
        if option is None:
            return
        self.context.record_action(label_key=self.title_key, python_code=option.mirror_code, key="metric_contract_primary")
        self.on_complete(self.choice)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 20), 22, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t(self.ask_prompt_key), (CENTER_X, ASK_Y), ASK_MAX_WIDTH, 16, colors.BUTTON_FOCUS_BORDER)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)
        self._draw_detail(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self.choice is None:
            return
        index = next(i for i, option in enumerate(self.definition_options) if option.key == self.choice)
        rect = self.buttons.buttons[index].rect
        marker = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_detail(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        option = self._selected_option()
        if option is None:
            draw_centered_text(surface, loc.t("metric_contract.pick_hint"), (CENTER_X, VALUE_Y), 15, colors.BUTTON_TEXT_DISABLED)
            return

        value_text = f"{loc.t('metric_contract.value_label')} {option.value * 100:.1f}%"
        draw_centered_text(surface, value_text, (CENTER_X, VALUE_Y), 22, colors.TEXT)

        left = CENTER_X - DETAIL_MAX_WIDTH // 2
        y = DETAIL_TOP
        font = get_font(15)
        line_height = font.get_linesize() + 4
        for prefix_key, text_key in (
            ("metric_contract.numerator_label", option.numerator_key),
            ("metric_contract.denominator_label", option.denominator_key),
            ("metric_contract.window_label", option.window_key),
        ):
            line = f"{loc.t(prefix_key)} {loc.t(text_key)}"
            draw_wrapped_text(surface, line, (left, y), DETAIL_MAX_WIDTH, 15, colors.TEXT)
            y += len(wrap_text(line, font, DETAIL_MAX_WIDTH)) * line_height + DETAIL_LINE_GAP
