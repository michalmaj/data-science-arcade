from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.brief import AnalyticalBrief, BriefField, BriefStep, MultiChoiceField
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.hint_controller import HintController
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
OPTION_SIZE = (420, 46)
FIRST_OPTION_Y = 175
OPTION_SPACING = 56
MIN_OPTION_SPACING = 48
"""Never below OPTION_SIZE[1] (46) plus a visible 2px gap - anything
tighter overlaps adjacent option buttons, a second real bug the same
screenshot pass caught right after fixing the hint/nav-button one."""
NAV_BUTTON_Y = 505
HINT_AREA_MARGIN = 6
HINT_AREA_RESERVED = 110
"""Vertical room a tiered hint's button + up to 3 revealed tiers needs
below the option list - reserved by shrinking option spacing (only for
fields that actually have a HintController) rather than risking the
hint area overlapping the nav buttons, the same "shrink to fit real
content, don't hardcode a content-dependent dimension" principle
HandbookScene's index rows already established for exactly this failure
mode. Caught by a real screenshot at the 4-option/3-tier worst case
before this existed, not by reasoning about it."""
MULTI_COUNT_Y = 155
"""Same 15px gap below the prompt line (140) that
ui/decision_builder_scene.py's own EVIDENCE_COUNT_Y uses below its
identically-positioned prompt - shown only for a MultiChoiceField, the
same way that scene only shows a count for its EvidenceField step."""
MULTI_FIELD_OPTIONS_TOP = 190
"""A MultiChoiceField's own options start 15px below FIRST_OPTION_Y -
otherwise the first option button (top edge ~152, per OPTION_SIZE)
silently renders on top of MULTI_COUNT_Y (155), since buttons draw after
the count text. The same reason ui/decision_builder_scene.py's own
FIRST_EVIDENCE_Y (185) sits below this scene's FIRST_OPTION_Y rather
than reusing it verbatim - caught by a real screenshot of the first
MultiChoiceField this scene ever rendered, not by reasoning about it."""


class BriefBuilderScene(Scene):
    """The step-by-step 'build a structured analytical brief' wizard (spec
    §25 Lesson 01's core mechanic, kept generic so any lesson can reuse it):
    one field per screen, pick an option (doesn't auto-advance - has to be
    confirmed with Next, same as picking the wrong option and changing your
    mind should be cheap), Back/Next between fields. on_complete fires once
    every field has a choice.

    `fields` is `tuple[BriefField | MultiChoiceField, ...]` - most fields
    are still BriefField's plain single-select, but a MultiChoiceField
    (pick min_count-max_count from a fixed option list, e.g. "which
    properties should this event record") toggles multiple selections
    instead of overwriting a single one. This is the same relationship
    ui/decision_builder_scene.py already has to its own EvidenceField -
    adapted from that scene's real toggle/count/button-disable-at-max
    handling rather than invented fresh, but stored differently: this
    scene's self.choices already holds every field's value in one dict
    (str for BriefField, tuple[str, ...] for MultiChoiceField), where
    DecisionBuilderScene keeps its one EvidenceField's selection in a
    separate list because it always has exactly one, known in advance.

    guided=True also shows each field's explanatory hint text (spec Act 3
    'receive explanatory feedback'); guided=False hides it (Act 4 'less
    guidance').

    `tiered_hint_keys`, when given, maps a field's key to 1-3 hint tiers
    (HintController's own Direction->Concept->Procedure shape) - upgrading
    that one field from the single always-shown-or-hidden `hint_key` string
    to a real click-to-reveal-more control. Fields not present in this dict
    keep today's exact `hint_key` behavior unchanged. HintController
    instances are built once here, not passed in pre-built, so this scene
    keeps sole ownership of the button's screen position (computed from
    that field's own option count, so a longer field doesn't crowd its
    hint button - the same reason no fixed position could safely cover
    every field's option count)."""

    def __init__(
        self,
        app,
        title_key: str,
        fields: tuple[BriefStep, ...],
        on_complete: Callable[[AnalyticalBrief], None],
        guided: bool = True,
        tiered_hint_keys: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.fields = fields
        self.on_complete = on_complete
        self.guided = guided
        self.field_index = 0
        self.choices: AnalyticalBrief = {}
        # Which fields *will* get a HintController is fully known from
        # tiered_hint_keys alone - _option_spacing/_hint_button_topleft
        # check this, not self._hint_controllers, since they're needed to
        # compute the very positions the controllers below are built with.
        self._tiered_hint_keys = tiered_hint_keys or {}
        self._hint_controllers: dict[str, HintController] = {
            field.key: HintController(app, self._tiered_hint_keys[field.key], self._hint_button_topleft(field))
            for field in fields
            if field.key in self._tiered_hint_keys
        }
        self._rebuild_buttons()

    def _current_field(self) -> BriefStep:
        return self.fields[self.field_index]

    def _options_top(self, field: BriefStep) -> int:
        return MULTI_FIELD_OPTIONS_TOP if isinstance(field, MultiChoiceField) else FIRST_OPTION_Y

    def _option_spacing(self, field: BriefStep) -> int:
        if field.key not in self._tiered_hint_keys or len(field.options) <= 1:
            return OPTION_SPACING
        available = (NAV_BUTTON_Y - 20) - self._options_top(field) - HINT_AREA_RESERVED
        return max(MIN_OPTION_SPACING, min(OPTION_SPACING, available // len(field.options)))

    def _hint_button_topleft(self, field: BriefStep) -> tuple[int, int]:
        top = self._options_top(field) + len(field.options) * self._option_spacing(field) + HINT_AREA_MARGIN
        return (CENTER_X - 300, top)

    def _field_satisfied(self, field: BriefStep) -> bool:
        if isinstance(field, MultiChoiceField):
            selected = self.choices.get(field.key, ())
            return field.min_count <= len(selected) <= field.max_count
        return field.key in self.choices

    def _current_hint_controller(self) -> HintController | None:
        return self._hint_controllers.get(self._current_field().key)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        field = self._current_field()
        spacing = self._option_spacing(field)
        top = self._options_top(field)
        buttons = []
        is_multi = isinstance(field, MultiChoiceField)
        selected_multi = self.choices.get(field.key, ()) if is_multi else ()
        for index, option in enumerate(field.options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, top + index * spacing)
            if is_multi:
                selected = option.key in selected_multi
                enabled = selected or len(selected_multi) < field.max_count
                button = Button(rect, loc.t(option.label_key), self._make_toggle(option.key), enabled=enabled)
            else:
                button = Button(rect, loc.t(option.label_key), self._make_choose(option.key))
            buttons.append(button)

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.field_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_field() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=self._field_satisfied(field))
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _is_last_field(self) -> bool:
        return self.field_index == len(self.fields) - 1

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choices[self._current_field().key] = option_key
            self._rebuild_buttons()

        return choose

    def _make_toggle(self, option_key: str) -> Callable[[], None]:
        def toggle() -> None:
            field = self._current_field()
            assert isinstance(field, MultiChoiceField)
            selected = list(self.choices.get(field.key, ()))
            if option_key in selected:
                selected.remove(option_key)
            elif len(selected) < field.max_count:
                selected.append(option_key)
            self.choices[field.key] = tuple(selected)
            self._rebuild_buttons()

        return toggle

    def _back(self) -> None:
        if self.field_index > 0:
            self.field_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if not self._field_satisfied(self._current_field()):
            return
        if self._is_last_field():
            self.on_complete(dict(self.choices))
            return
        self.field_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed here: LessonRunner wraps every
        # stage in Pausable, which intercepts Escape before this scene ever
        # sees it (opens the pause menu instead of, say, accidentally
        # abandoning progress on this field).
        self.buttons.handle_event(event)
        controller = self._current_hint_controller()
        if self.guided and controller is not None:
            controller.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        field = self._current_field()

        progress = f"{self.field_index + 1} / {len(self.fields)}"
        draw_centered_text(surface, progress, (CENTER_X, 60), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 90), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(field.prompt_key), (CENTER_X, 140), 20, colors.TEXT)
        if isinstance(field, MultiChoiceField):
            selected_count = len(self.choices.get(field.key, ()))
            count_text = f"{selected_count} / {field.min_count}-{field.max_count}"
            draw_centered_text(surface, count_text, (CENTER_X, MULTI_COUNT_Y), 14, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, field)

        controller = self._current_hint_controller()
        if self.guided and controller is not None:
            text_top = self._hint_button_topleft(field)[1] + 34
            controller.draw(surface, (CENTER_X - 300, text_top))
        elif self.guided and field.hint_key:
            # 400 was always safe for every field that existed when it was
            # chosen (<=4 options) - grows only for a field whose own real
            # option count would otherwise run the hint text into its last
            # button, rather than moving hint text that's already shipped
            # and screenshot-verified at the fixed position.
            hint_top = max(400, self._hint_button_topleft(field)[1])
            draw_wrapped_text(
                surface,
                loc.t(field.hint_key),
                (CENTER_X - 300, hint_top),
                600,
                15,
                colors.BUTTON_TEXT_DISABLED,
            )

    def _draw_selected_indicator(self, surface: pygame.Surface, field: BriefStep) -> None:
        if isinstance(field, MultiChoiceField):
            selected_keys = self.choices.get(field.key, ())
            selected_indices = [i for i, option in enumerate(field.options) if option.key in selected_keys]
        else:
            selected_key = self.choices.get(field.key)
            if selected_key is None:
                return
            selected_indices = [next(i for i, option in enumerate(field.options) if option.key == selected_key)]
        # A filled bar on the leading edge, not a border - keyboard focus
        # already uses a full border (Button.draw), and this option can be
        # both focused and selected at once, or neither; a second border
        # around the same or a different button reads as "two things are
        # focused," so "selected" needs a visually distinct treatment.
        for index in selected_indices:
            rect = self.buttons.buttons[index].rect
            marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
