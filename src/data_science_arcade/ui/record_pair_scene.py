from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.record_pair import PairDecisions, RecordPair
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
CARD_WIDTH = 380
CARD_A_LEFT = 60
CARD_B_LEFT = 520
CARD_HEADER_Y = 115
FIELD_FIRST_Y = 150
FIELD_ROW_HEIGHT = 30
ACTION_BUTTON_SIZE = (220, 46)
ACTION_BUTTON_Y = 320
HINT_Y = 380
NAV_BUTTON_Y = 470


class RecordPairScene(Scene):
    """Step through candidate duplicate record pairs (spec §25 Lesson 08
    'Duplicate Detective'): two records shown side by side, differing
    fields highlighted, decide Merge or Keep Separate for each - the whole
    set of pairs stays step-indexed (spec's '1/2' progress pattern, same
    Back/Next chrome as the flow builder) rather than a flow diagram, since
    pair order carries no meaning the way a checkout flow's does.
    on_complete fires once every pair has a decision.

    guided=True also shows each pair's explanatory hint; guided=False
    hides it."""

    def __init__(
        self,
        app,
        title_key: str,
        prompt_key: str,
        pairs: tuple[RecordPair, ...],
        on_complete: Callable[[PairDecisions], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.prompt_key = prompt_key
        self.pairs = pairs
        self.on_complete = on_complete
        self.guided = guided
        self.pair_index = 0
        self.decisions: PairDecisions = {}
        self._rebuild_buttons()

    def _current_pair(self) -> RecordPair:
        return self.pairs[self.pair_index]

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        pair = self._current_pair()
        buttons: list[Button] = []

        merge_rect = pygame.Rect(0, 0, *ACTION_BUTTON_SIZE)
        merge_rect.center = (CENTER_X - 120, ACTION_BUTTON_Y)
        self.merge_button = Button(merge_rect, loc.t("record_pair.merge"), self._make_decide("merge"))
        buttons.append(self.merge_button)

        keep_separate_rect = pygame.Rect(0, 0, *ACTION_BUTTON_SIZE)
        keep_separate_rect.center = (CENTER_X + 120, ACTION_BUTTON_Y)
        self.keep_separate_button = Button(
            keep_separate_rect, loc.t("record_pair.keep_separate"), self._make_decide("keep_separate")
        )
        buttons.append(self.keep_separate_button)

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.pair_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_pair() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=pair.key in self.decisions)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _is_last_pair(self) -> bool:
        return self.pair_index == len(self.pairs) - 1

    def _make_decide(self, decision: str) -> Callable[[], None]:
        def decide() -> None:
            self.decisions[self._current_pair().key] = decision
            self._rebuild_buttons()

        return decide

    def _back(self) -> None:
        if self.pair_index > 0:
            self.pair_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_pair().key not in self.decisions:
            return
        if self._is_last_pair():
            self.on_complete(dict(self.decisions))
            return
        self.pair_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        pair = self._current_pair()

        progress = f"{self.pair_index + 1} / {len(self.pairs)}"
        draw_centered_text(surface, progress, (CENTER_X, 25), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 50), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(self.prompt_key), (CENTER_X, 85), 18, colors.TEXT)

        self._draw_record(surface, CARD_A_LEFT, "record_pair.record_a", pair.id_a, is_a=True)
        self._draw_record(surface, CARD_B_LEFT, "record_pair.record_b", pair.id_b, is_a=False)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, pair)

        if self.guided and pair.hint_key:
            draw_wrapped_text(surface, loc.t(pair.hint_key), (CENTER_X - 350, HINT_Y), 700, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_record(self, surface: pygame.Surface, left: int, label_key: str, record_id: str, is_a: bool) -> None:
        loc = self.app.localization
        header = f"{loc.t(label_key)} ({record_id})"
        draw_single_line(surface, header, (left, CARD_HEADER_Y), CARD_WIDTH, 17, colors.BUTTON_FOCUS_BORDER)

        for row, field in enumerate(self._current_pair().fields):
            value = field.value_a if is_a else field.value_b
            text = f"{loc.t(field.label_key)}: {value}"
            color = colors.TEXT if field.matches else colors.BUTTON_FOCUS_BORDER
            y = FIELD_FIRST_Y + row * FIELD_ROW_HEIGHT
            draw_single_line(surface, text, (left, y), CARD_WIDTH, 15, color)

    def _draw_selected_indicator(self, surface: pygame.Surface, pair: RecordPair) -> None:
        decision = self.decisions.get(pair.key)
        if decision is None:
            return
        button = self.merge_button if decision == "merge" else self.keep_separate_button
        rect = button.rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)
