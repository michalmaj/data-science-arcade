from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.comparison_reveal_scene import InterpretOption
from data_science_arcade.ui.histogram import draw_histogram, draw_segmented_histogram, draw_value_marker
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
CHART_RECT = pygame.Rect(80, 66, 800, 150)
BIN_COUNT = 12
AXIS_LABEL_Y = CHART_RECT.bottom + 14
MARKER_ROW_Y = AXIS_LABEL_Y + 34
MARKER_BUTTON_SIZE = (300, 36)
"""Wide enough for the real toggled-on label - a translated marker name
plus its live ": $X,XXX.XX" value suffix, worst case measured at 235px
for PL's "Średnia konsumencka: $49.00" - not just the untoggled bare
name. 230 let that real text overflow the button outright (235 > 230),
independent of and worse than the indicator-bar-over-text collision a
screenshot first caught; caught only by rendering the real toggled state
in both languages, not by reasoning about the bare label alone."""
MARKER_SPACING = 320
SEGMENT_LEGEND_Y = MARKER_ROW_Y
INTERPRET_PROMPT_Y = MARKER_ROW_Y + 56
INTERPRET_PROMPT_SIZE = 18
INTERPRET_PROMPT_MAX_WIDTH = 820
OPTION_SIZE = (420, 40)
FIRST_OPTION_Y = INTERPRET_PROMPT_Y + 44
OPTION_SPACING = 44
NAV_BUTTON_Y = 500
HINT_GAP = 8

_SEGMENT_COLORS: tuple[tuple[int, int, int], ...] = (colors.BUTTON_FOCUS_BORDER, colors.SEGMENT_SECONDARY)


@dataclass(frozen=True)
class DistributionMarker:
    """One real, computed statistic the student can freely toggle on/off
    as a vertical line on the histogram - never itself correct/incorrect,
    never itself scored or recorded as Evidence just for being toggled
    (see DistributionExplorerScene's own docstring). `python_code`, when
    set, is folded into the single AnalyticalAction this scene records on
    Continue - real Python Mirror content for whichever markers the
    student actually chose to look at, without turning each toggle into
    its own recorded fact."""

    key: str
    label_key: str
    value: float
    python_code: str | None = None


class DistributionExplorerScene(Scene):
    """A real, free-exploration histogram - the whole point of retiring
    the old `DistributionScene` linear 3-question quiz. One histogram
    (optionally two colored series, see `segment_series`) stays visible
    the entire stage; `markers` are independent toggle buttons, each
    showing/hiding its own vertical line and its own live value in its
    own button label - toggling one, several, or none is never itself
    right or wrong, never itself Evidence, and never itself scored. The
    only thing this scene ever grades is the single, optional interpret
    choice at the end (reusing `ComparisonRevealScene`'s own
    `InterpretOption`/evidence-key mechanics directly, not a parallel
    type) - scored signal only exists once the student interprets what
    they saw for a real question, never for the act of looking itself.

    `interpret_prompt_key`/`interpret_options` are optional (empty tuple
    = Continue enables immediately, no forced choice) so the same scene
    also serves a pure "just look, no quiz" beat (this lesson's own
    mastery act) without a second bespoke scene class.

    `segment_series`, when set to a tuple of `(key, label_key, values)`
    triples, draws that many colored series on the same chart instead of
    one plain histogram - used both for the real segment reveal
    (consumer/business) and, relabeled, the mastery transfer (two
    different processes) - one scene, multiple real uses, never three
    separate classes for what is mechanically the same chart."""

    def __init__(
        self,
        app,
        title_key: str,
        values: list[float],
        markers: tuple[DistributionMarker, ...],
        on_complete: Callable[[str | None], None],
        context: LessonContext,
        interpret_prompt_key: str | None = None,
        interpret_options: tuple[InterpretOption, ...] = (),
        interpret_hint_key: str | None = None,
        segment_series: tuple[tuple[str, str, list[float]], ...] | None = None,
        guided: bool = True,
        preamble_python_code: str | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.values = values
        self.min_value = min(values)
        self.max_value = max(values)
        self.markers = markers
        self.on_complete = on_complete
        self.context = context
        self.interpret_prompt_key = interpret_prompt_key
        self.interpret_options = interpret_options
        self.interpret_hint_key = interpret_hint_key
        self.segment_series = segment_series
        self.guided = guided
        self.preamble_python_code = preamble_python_code
        """A real line (or lines) of Python that has to run before any of
        `markers`' own python_code makes sense - e.g. segment_reveal's own
        join that brings a `segment` column into scope for the first time,
        since the player-facing frame never carries one before this reveal
        (see order_values.py's own module docstring). None everywhere else.
        Recorded once, always first, regardless of which markers are
        toggled - the reveal itself (and the interpret action it's
        attached to) happens the moment this stage is completed, not only
        when a marker happens to be on."""
        self.active_markers: set[str] = set()
        self._interpret_choice: str | None = None
        self._rebuild_buttons()

    def _requires_interpret(self) -> bool:
        return len(self.interpret_options) > 0

    def _continue_enabled(self) -> bool:
        return (not self._requires_interpret()) or self._interpret_choice is not None

    def _toggle_marker(self, key: str) -> Callable[[], None]:
        def toggle() -> None:
            if key in self.active_markers:
                self.active_markers.remove(key)
            else:
                self.active_markers.add(key)
            self._rebuild_buttons()

        return toggle

    def _choose_interpret(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._interpret_choice = option_key
            self._rebuild_buttons()

        return choose

    def _active_python_code(self) -> str | None:
        marker_lines = [m.python_code for m in self.markers if m.key in self.active_markers and m.python_code]
        if self.preamble_python_code is not None:
            return "\n".join([self.preamble_python_code, *marker_lines])
        return "\n".join(marker_lines) if marker_lines else None

    def _continue(self) -> None:
        if not self._continue_enabled():
            return
        python_code = self._active_python_code()
        if self._requires_interpret():
            chosen = next(o for o in self.interpret_options if o.key == self._interpret_choice)
            action = self.context.record_action(label_key=chosen.label_key, python_code=python_code)
            if chosen.evidence_key is not None:
                self.context.record_evidence(label_key=chosen.evidence_key, source_action=action, key=chosen.evidence_key)
            self.on_complete(self._interpret_choice)
            return
        if python_code is not None:
            self.context.record_action(label_key=self.title_key, python_code=python_code)
        self.on_complete(None)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        first_marker_x = CENTER_X - (len(self.markers) - 1) * MARKER_SPACING // 2
        self.marker_buttons: dict[str, Button] = {}
        for index, marker in enumerate(self.markers):
            rect = pygame.Rect(0, 0, *MARKER_BUTTON_SIZE)
            rect.center = (first_marker_x + index * MARKER_SPACING, MARKER_ROW_Y)
            active = marker.key in self.active_markers
            label = loc.t(marker.label_key)
            if active:
                label = f"{label}: ${marker.value:,.2f}"
            button = Button(rect, label, self._toggle_marker(marker.key))
            self.marker_buttons[marker.key] = button
            buttons.append(button)

        self.interpret_buttons: dict[str, Button] = {}
        if self._requires_interpret():
            for index, option in enumerate(self.interpret_options):
                rect = pygame.Rect(0, 0, *OPTION_SIZE)
                rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
                button = Button(rect, loc.t(option.label_key), self._choose_interpret(option.key))
                self.interpret_buttons[option.key] = button
                buttons.append(button)

        continue_rect = pygame.Rect(0, 0, 200, 44)
        continue_rect.center = (CENTER_X, NAV_BUTTON_Y)
        self.continue_button = Button(
            continue_rect, loc.t("runtime.continue_button"), self._continue, enabled=self._continue_enabled()
        )
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 28), 26, colors.TEXT)

        if self.segment_series is not None:
            series = tuple(
                (values, _SEGMENT_COLORS[index % len(_SEGMENT_COLORS)])
                for index, (_key, _label_key, values) in enumerate(self.segment_series)
            )
            draw_segmented_histogram(surface, CHART_RECT, series, self.min_value, self.max_value, BIN_COUNT)
        else:
            draw_histogram(surface, CHART_RECT, self.values, self.min_value, self.max_value, BIN_COUNT, colors.TEXT)

        # On a segmented chart, the marker line must never share a color
        # with either series' own bars (_SEGMENT_COLORS starts with this
        # same BUTTON_FOCUS_BORDER) - a marker landing inside that series'
        # own bar would render invisible, exactly the plain histogram's
        # own light-colored bars never risk. colors.TEXT contrasts against
        # both series colors and the plain histogram alike, so it's used
        # only for the segmented case to keep the plain case's own
        # existing, screenshot-verified look unchanged.
        marker_color = colors.TEXT if self.segment_series is not None else colors.BUTTON_FOCUS_BORDER
        for marker in self.markers:
            if marker.key in self.active_markers:
                draw_value_marker(surface, CHART_RECT, marker.value, self.min_value, self.max_value, marker_color)

        draw_centered_text(surface, f"${self.min_value:,.0f}", (CHART_RECT.left + 28, AXIS_LABEL_Y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, f"${self.max_value:,.0f}", (CHART_RECT.right - 28, AXIS_LABEL_Y), 14, colors.BUTTON_TEXT_DISABLED)

        if self.segment_series is not None:
            self._draw_segment_legend(surface)

        self.buttons.draw(surface)
        self._draw_selected_marker_indicators(surface)

        if self._requires_interpret():
            draw_centered_wrapped_text(
                surface, loc.t(self.interpret_prompt_key), (CENTER_X, INTERPRET_PROMPT_Y), INTERPRET_PROMPT_MAX_WIDTH, INTERPRET_PROMPT_SIZE, colors.TEXT
            )
            self._draw_selected_interpret_indicator(surface)
            if self.guided and self.interpret_hint_key:
                draw_wrapped_text(
                    surface, loc.t(self.interpret_hint_key), (CENTER_X - 300, NAV_BUTTON_Y - 40), 600, 14, colors.BUTTON_TEXT_DISABLED
                )

    def _draw_segment_legend(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        left = CHART_RECT.left
        y = CHART_RECT.top - 22
        for index, (_key, label_key, _values) in enumerate(self.segment_series):
            color = _SEGMENT_COLORS[index % len(_SEGMENT_COLORS)]
            swatch = pygame.Rect(left + index * 220, y, 14, 14)
            pygame.draw.rect(surface, color, swatch, border_radius=3)
            draw_wrapped_text(surface, loc.t(label_key), (left + index * 220 + 20, y - 2), 190, 14, colors.TEXT)

    def _draw_selected_marker_indicators(self, surface: pygame.Surface) -> None:
        for key, button in self.marker_buttons.items():
            if key not in self.active_markers:
                continue
            rect = button.rect
            marker_bar = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker_bar, border_radius=2)

    def _draw_selected_interpret_indicator(self, surface: pygame.Surface) -> None:
        if self._interpret_choice is None:
            return
        button = self.interpret_buttons.get(self._interpret_choice)
        if button is None:
            return
        rect = button.rect
        marker_bar = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker_bar, border_radius=2)
