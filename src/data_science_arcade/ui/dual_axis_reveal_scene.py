from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.category_chart import category_x, draw_line_chart
from data_science_arcade.ui.comparison_reveal_scene import ComparisonValue, InterpretOption
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text, wrap_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
CHART_RECT = pygame.Rect(150, 46, 660, 92)
LEGEND_Y = CHART_RECT.bottom + 10
BOX_LEFT = 40
BOX_TOP = LEGEND_Y + 18
BOX_WIDTH = 880
BOX_PADDING = 14
NARRATIVE_TEXT_SIZE = 15
NARRATIVE_LINE_SPACING = 3
COMPARISON_TEXT_SIZE = 19
COMPARISON_ROW_HEIGHT = 28
NARRATIVE_COMPARISON_GAP = 8
INTERPRET_PROMPT_GAP = 14
FIRST_OPTION_GAP = 24
OPTION_SIZE = (420, 36)
OPTION_SPACING = 40
CONTINUE_BUTTON_SIZE = (200, 36)
CONTINUE_GAP = 16


@dataclass(frozen=True)
class DualAxisSeries:
    """One of the two real series drawn on the SAME chart rect, each
    independently normalized to its own (min, max) - the exact mechanism
    a rigged dual-axis chart uses to make two wildly different real
    percent changes look like the same visual shape. Only two points
    (a real start/end) are ever drawn - this scene is purpose-built for
    the before/after dual-axis case, not a general n-point chart."""

    label_key: str
    values: tuple[float, float]
    color: tuple[int, int, int]


class DualAxisRevealScene(Scene):
    """A small, lesson-local reveal that actually RENDERS the deceptive
    dual-axis chart - two real series, each independently scaled to its
    own (min, max) on one shared rect via `category_chart.draw_line_chart`
    (no new drawing primitive needed) - so the student sees the visual
    trick itself, not just a described claim that one exists, before the
    real percent-change `ComparisonValue`s beneath it expose it. Every
    other reveal in this codebase (`ComparisonRevealScene`) is text/
    number-only; this one exists specifically because Lesson 28's own
    central reflex is about chart PERCEPTION, and a chart lesson's own
    "technically truthful, still deceptive" case deserves a real chart,
    not a paraphrase of one.

    Deliberately narrow, not a generic multi-series chart component:
    exactly two series, exactly two points each (a real start/end), no
    axis-scale/window/denominator override machinery - `ChartDesignerScene`
    already owns that general territory. Reuses `ComparisonValue`/
    `InterpretOption` from `comparison_reveal_scene` directly rather than
    redefining near-identical dataclasses, and follows the exact same
    record_action/record_evidence-on-Continue contract."""

    def __init__(
        self,
        app,
        title_key: str,
        narrative_keys: tuple[str, ...],
        series_a: DualAxisSeries,
        series_b: DualAxisSeries,
        comparisons: tuple[ComparisonValue, ...],
        interpret_prompt_key: str,
        interpret_options: tuple[InterpretOption, ...],
        on_complete: Callable[[str], None],
        context: LessonContext,
        value_format: Callable[[float], str] = lambda value: f"{value:+.0%}",
        guided: bool = True,
        interpret_hint_key: str | None = None,
        comparisons_are_evidence: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.narrative_keys = narrative_keys
        self.series_a = series_a
        self.series_b = series_b
        self.comparisons = comparisons
        self.interpret_prompt_key = interpret_prompt_key
        self.interpret_options = interpret_options
        self.on_complete = on_complete
        self.context = context
        self.value_format = value_format
        self.guided = guided
        self.interpret_hint_key = interpret_hint_key
        self.comparisons_are_evidence = comparisons_are_evidence
        self._interpret_choice: str | None = None
        self._rebuild_buttons()

    def _format_value(self, item: ComparisonValue) -> str:
        formatter = item.value_format if item.value_format is not None else self.value_format
        return formatter(item.value)

    def _content_width(self) -> int:
        return BOX_WIDTH - 40

    def _narrative_height(self) -> int:
        loc = self.app.localization
        font = get_font(NARRATIVE_TEXT_SIZE)
        width = self._content_width()
        line_height = font.get_linesize() + NARRATIVE_LINE_SPACING
        total_lines = sum(len(wrap_text(loc.t(key), font, width)) for key in self.narrative_keys)
        return total_lines * line_height

    def _box_rect(self) -> pygame.Rect:
        height = (
            BOX_PADDING
            + self._narrative_height()
            + NARRATIVE_COMPARISON_GAP
            + len(self.comparisons) * COMPARISON_ROW_HEIGHT
            + BOX_PADDING
        )
        return pygame.Rect(BOX_LEFT, BOX_TOP, BOX_WIDTH, height)

    def _interpret_prompt_y(self) -> int:
        return self._box_rect().bottom + INTERPRET_PROMPT_GAP

    def _first_option_y(self) -> int:
        return self._interpret_prompt_y() + FIRST_OPTION_GAP

    def _options_bottom(self) -> int:
        return self._first_option_y() + (len(self.interpret_options) - 1) * OPTION_SPACING + OPTION_SIZE[1] // 2

    def _hint_top(self) -> int:
        return self._options_bottom() + 6

    def _continue_button_y(self) -> int:
        y = self._options_bottom() + CONTINUE_GAP
        if self.guided and self.interpret_hint_key:
            y += 30
        return y

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons = []
        first_option_y = self._first_option_y()
        for index, option in enumerate(self.interpret_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, first_option_y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        continue_rect = pygame.Rect(0, 0, *CONTINUE_BUTTON_SIZE)
        continue_rect.center = (CENTER_X, self._continue_button_y())
        self.continue_button = Button(
            continue_rect, loc.t("runtime.continue_button"), self._continue, enabled=self._interpret_choice is not None
        )
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._interpret_choice = option_key
            self._rebuild_buttons()

        return choose

    def _continue(self) -> None:
        if self._interpret_choice is None:
            return
        for item in self.comparisons:
            action = self.context.record_action(label_key=item.label_key, python_code=item.python_code, key=item.label_key)
            if self.comparisons_are_evidence:
                self.context.record_evidence(
                    label_key=item.label_key, source_action=action, key=item.label_key, detail=self._format_value(item)
                )
        chosen = next(o for o in self.interpret_options if o.key == self._interpret_choice)
        action = self.context.record_action(label_key=chosen.label_key)
        if chosen.evidence_key is not None:
            self.context.record_evidence(label_key=chosen.evidence_key, source_action=action, key=chosen.evidence_key)
        self.on_complete(self._interpret_choice)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def _draw_chart(self, surface: pygame.Surface) -> None:
        for series in (self.series_a, self.series_b):
            min_value, max_value = min(series.values), max(series.values)
            draw_line_chart(surface, CHART_RECT, list(series.values), min_value, max_value, series.color)
        pygame.draw.rect(surface, colors.BUTTON_TEXT_DISABLED, CHART_RECT, width=1)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        font = get_font(13)
        swatch = 10
        left = CHART_RECT.left
        for index, series in enumerate((self.series_a, self.series_b)):
            x = left + index * 240
            swatch_rect = pygame.Rect(x, LEGEND_Y, swatch, swatch)
            pygame.draw.rect(surface, series.color, swatch_rect)
            text = font.render(loc.t(series.label_key), True, colors.TEXT)
            surface.blit(text, (x + swatch + 6, LEGEND_Y - 1))

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 28), 26, colors.TEXT)
        self._draw_chart(surface)
        self._draw_legend(surface)

        box = self._box_rect()
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, box, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, box, width=1, border_radius=8)

        left = box.left + 20
        width = self._content_width()
        font = get_font(NARRATIVE_TEXT_SIZE)
        line_height = font.get_linesize() + NARRATIVE_LINE_SPACING
        y = box.top + BOX_PADDING
        for key in self.narrative_keys:
            text = loc.t(key)
            draw_wrapped_text(surface, text, (left, y), width, NARRATIVE_TEXT_SIZE, colors.TEXT, line_spacing=NARRATIVE_LINE_SPACING)
            y += len(wrap_text(text, font, width)) * line_height

        y += NARRATIVE_COMPARISON_GAP
        for item in self.comparisons:
            text = f"{loc.t(item.label_key)} {self._format_value(item)}"
            draw_wrapped_text(surface, text, (left, y), width, COMPARISON_TEXT_SIZE, colors.BUTTON_FOCUS_BORDER)
            y += COMPARISON_ROW_HEIGHT

        draw_centered_text(surface, loc.t(self.interpret_prompt_key), (CENTER_X, self._interpret_prompt_y()), 18, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)

        if self.guided and self.interpret_hint_key:
            draw_wrapped_text(
                surface, loc.t(self.interpret_hint_key), (CENTER_X - 300, self._hint_top()), 600, 14, colors.BUTTON_TEXT_DISABLED
            )

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self._interpret_choice is None:
            return
        selected_index = next(i for i, o in enumerate(self.interpret_options) if o.key == self._interpret_choice)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
