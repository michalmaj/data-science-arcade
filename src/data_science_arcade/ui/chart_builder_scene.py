from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.category_chart import category_x, draw_bar_chart, draw_line_chart, value_to_y
from data_science_arcade.ui.histogram import compute_bin_counts, draw_histogram
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
ASK_Y = 44
ASK_MAX_WIDTH = 860
CHART_RECT = pygame.Rect(150, 78, 660, 158)
CATEGORY_LABEL_Y = CHART_RECT.bottom + 8
COUNT_LABEL_GAP = 30
FIRST_OPTION_Y = CATEGORY_LABEL_Y + 52
OPTION_SIZE = (280, 40)
OPTION_SPACING = 300
NAV_BUTTON_Y = 500
HINT_Y = 468


@dataclass(frozen=True)
class ChartFormOption:
    """One complete, real, self-contained chart a student can pick - the
    same "every option is fully its own real render" discipline
    `JoinTypeOption` (L13) already established, applied here so a bar
    variant with a different category order, or a genuinely different
    series entirely (the distribution ask's own store-averages decoy),
    can sit as a sibling option without the scene needing any special
    per-form data-reshaping logic of its own.

    Never a scale override, a data-window override, or a denominator
    override - `ChartBuilderScene` has no such capability at all, unlike
    the shared `ChartDesignerScene` (Lesson 28's own territory)."""

    key: str
    label_key: str
    form: str  # "bar" | "line" | "histogram"
    mirror_intent: str  # e.g. "store_id vs return rate (%)" - real, short, descriptive
    labels: tuple[str, ...] | None = None  # bar/line
    values: tuple[float, ...] | None = None  # bar/line
    value_format: Callable[[float], str] = lambda v: f"{v:,.0f}"
    raw_values: tuple[float, ...] | None = None  # histogram - real, un-truncated, full population
    bin_edges: tuple[float, ...] | None = None  # histogram - one fixed, explicit, deterministic binning
    mirror_extra_code: str | None = None
    """Real pandas code needed to reach THIS option's own rendered
    series, beyond whatever the caller's shared data-prep action already
    computed (e.g. a sort_values() a sorted-bar option renders but a
    natural-order option doesn't) - shown before the Visualization-intent
    comment so the Mirror genuinely reproduces what actually got
    rendered, never silently omitting a transform the picture itself
    depended on. None (the default) means this option renders the shared
    data as-is, no extra line needed."""


def _format_cell(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


class ChartBuilderScene(Scene):
    """One real, live-rendered chart attempt for one stated business ask
    (`ask_prompt_key`, always visible) - pick a form, see the real chart
    redrawn from real data, never a static preview. Reuses the existing,
    already-generic drawing primitives directly: `category_chart.py`'s
    own `draw_bar_chart`/`draw_line_chart` for bar/line (always a zero
    baseline - no axis-scale control exists here at all, by construction,
    not just by content choice) and `histogram.py`'s own `draw_histogram`
    for the histogram form (already battle-tested by L11 at 100 rows,
    reused unchanged at this lesson's own 260-row scale - real bin counts
    are always computed and shown, never left implicit).

    Every `ChartFormOption` a caller offers must be genuinely safe and
    legible on its own: a form that would need to render one label per
    raw observation (e.g. a bar/line of 260 individual delivery times)
    must never be offered at all - not silently truncated to a subset,
    not rendered with overlapping labels. Every option this lesson
    actually offers uses an already-aggregated series (stores, days, or
    histogram bins), never a raw per-row render.

    `initial_choice` seeds a fresh instance with a prior pass's pick (a
    revision is just constructing this scene again, pre-filled - matching
    `AggregationBuilderScene`/`JoinBuilderScene`'s own established
    pattern, never a bespoke partial-resume mechanism).

    Never records a toggle/pick as its own AnalyticalAction or Evidence -
    the real chart attempt is recorded as ONE action, only once a choice
    is confirmed via Continue (matches the "toggling/picking mechanics
    are never themselves Evidence" discipline established since L11's own
    DistributionExplorerScene)."""

    def __init__(
        self,
        app,
        title_key: str,
        ask_prompt_key: str,
        form_options: tuple[ChartFormOption, ...],
        on_complete: Callable[[str], None],
        context: LessonContext,
        initial_choice: str | None = None,
        mirror_action_key: str = "chart_pipeline",
        hint_key: str | None = None,
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.ask_prompt_key = ask_prompt_key
        self.form_options = form_options
        self.on_complete = on_complete
        self.context = context
        self.mirror_action_key = mirror_action_key
        self.hint_key = hint_key
        self.guided = guided
        self.choice: str | None = initial_choice
        self._rebuild_buttons()

    def _selected_option(self) -> ChartFormOption | None:
        if self.choice is None:
            return None
        return next(o for o in self.form_options if o.key == self.choice)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        count = len(self.form_options)
        start_x = CENTER_X - (count - 1) * OPTION_SPACING // 2
        for index, option in enumerate(self.form_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (start_x + index * OPTION_SPACING, FIRST_OPTION_Y)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        continue_rect = pygame.Rect(0, 0, 160, 44)
        continue_rect.center = (CENTER_X, NAV_BUTTON_Y)
        self.continue_button = Button(continue_rect, loc.t("brief.finish"), self._finish, enabled=self.choice is not None)
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choice = option_key
            self._rebuild_buttons()

        return choose

    def _mirror_comment(self, option: ChartFormOption) -> str:
        # A real, disclosed scope boundary: matplotlib isn't a project
        # dependency, so this Mirror never claims a `.plot(...)` call is
        # executable - the chart form is communicated as a comment
        # alongside the real, exec()-able data-prep lines recorded
        # separately (by the caller, before this scene's own stage).
        return f"# Visualization intent: {option.form} chart - {option.mirror_intent}"

    def _finish(self) -> None:
        option = self._selected_option()
        if option is None:
            return
        python_code = self._mirror_comment(option)
        if option.mirror_extra_code:
            python_code = f"{option.mirror_extra_code}\n{python_code}"
        self.context.record_action(label_key=self.title_key, python_code=python_code, key=self.mirror_action_key)
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

        self._draw_chart(surface)
        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self.choice is None:
            return
        index = next(i for i, option in enumerate(self.form_options) if option.key == self.choice)
        rect = self.buttons.buttons[index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_chart(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        option = self._selected_option()
        if option is None:
            draw_centered_text(surface, loc.t("chart_builder.pick_hint"), (CENTER_X, CHART_RECT.centery), 15, colors.BUTTON_TEXT_DISABLED)
            return

        if option.form == "histogram":
            self._draw_histogram_chart(surface, option)
        else:
            self._draw_category_chart(surface, option)

    def _draw_category_chart(self, surface: pygame.Surface, option: ChartFormOption) -> None:
        labels = option.labels or ()
        values = list(option.values or ())
        min_value = 0.0  # always a real, honest zero baseline - no scale control exists here
        max_value = max(values) * 1.15 if values else 1.0

        if option.form == "line":
            draw_line_chart(surface, CHART_RECT, values, min_value, max_value, colors.BUTTON_FOCUS_BORDER)
        else:
            draw_bar_chart(surface, CHART_RECT, values, min_value, max_value, colors.TEXT)

        for index, (label, value) in enumerate(zip(labels, values)):
            x = category_x(index, len(labels), CHART_RECT)
            draw_centered_text(surface, label, (x, CATEGORY_LABEL_Y), 12, colors.BUTTON_TEXT_DISABLED)
            label_y = value_to_y(value, min_value, max_value, CHART_RECT) - 12
            draw_centered_text(surface, option.value_format(value), (x, label_y), 11, colors.BUTTON_TEXT_DISABLED)

    def _draw_histogram_chart(self, surface: pygame.Surface, option: ChartFormOption) -> None:
        loc = self.app.localization
        raw_values = list(option.raw_values or ())
        edges = option.bin_edges or ()
        bin_count = max(1, len(edges) - 1)
        min_value = edges[0] if edges else 0.0
        max_value = edges[-1] if edges else 1.0

        draw_histogram(surface, CHART_RECT, raw_values, min_value, max_value, bin_count, colors.TEXT)
        counts = compute_bin_counts(raw_values, min_value, max_value, bin_count)

        for index in range(bin_count):
            x = category_x(index, bin_count, CHART_RECT)
            label = f"{edges[index]:g}-{edges[index + 1]:g}"
            draw_centered_text(surface, label, (x, CATEGORY_LABEL_Y), 11, colors.BUTTON_TEXT_DISABLED)
            draw_centered_text(surface, str(counts[index]), (x, CATEGORY_LABEL_Y + 16), 11, colors.BUTTON_TEXT_DISABLED)

        total = sum(counts)
        note = loc.t("chart_builder.histogram_total").format(total=total)
        draw_centered_text(surface, note, (CENTER_X, CHART_RECT.top - 10), 12, colors.BUTTON_TEXT_DISABLED)
