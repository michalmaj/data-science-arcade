from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.power import minimum_detectable_effect
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text, wrap_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
STEP_BUTTON_SIZE = (44, 44)
MINUS_X = CENTER_X - 120
WEEKS_VALUE_X = CENTER_X
PLUS_X = CENTER_X + 120
WEEKS_LABEL_Y = 180
STEPPER_Y = 230
STAT_ROW_1_Y = 290
STAT_ROW_2_Y = 320
STATUS_Y = 360
CONFIRM_SIZE = (220, 44)
CONFIRM_Y = 460


class PowerPlannerScene(Scene):
    """One live, interactive planning stepper - weeks 1-12, n/arm and MDE
    recomputed on every change, a status line for whether the current
    plan meets the business's own real sensitivity target. Seeded from an
    earlier blind "cold" pick (`initial_weeks`) so first paint already
    shows that pick's own real consequence - the "productive failure"
    moment - before the student ever touches a stepper.

    Deliberately not SamplingAllocatorScene: that scene's whole shape is
    "spend a shared, fixed budget across N groups, Confirm only once the
    budget is spent to exactly zero" - there is no such invalid state
    here (every weeks value 1-12 is a complete, legitimate plan), so
    Confirm is unconditionally enabled from first paint. Live interactive
    comparison during planning is the intended mechanic here (unlike a
    lesson where previewing an outcome before committing would be
    cheating the pedagogy) - planning IS comparing designs before the
    experiment starts.

    Exactly one `record_action`/`record_evidence` pair exists for the
    whole planning stage, fired once on Confirm for whatever `weeks`
    value is showing at that moment - "revising" is just moving the
    stepper before pressing Confirm; confirming without touching it is
    consciously keeping the cold pick. No second call, no offer/skip
    gate - unlike a stochastic re-execution, recomputing MDE for a new
    weeks value is free and deterministic."""

    def __init__(
        self,
        app,
        title_key: str,
        narrative_keys: tuple[str, ...],
        initial_weeks: int,
        min_weeks: int,
        max_weeks: int,
        weekly_n_per_arm: int,
        baseline_rate: float,
        business_minimum_effect: float,
        on_confirm: Callable[[int], None],
        context: LessonContext,
        record_key: str,
        mirror_action_label_key: str,
        mirror_python_code_for: Callable[[int], str],
        evidence_key: str,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.narrative_keys = narrative_keys
        self.weeks = initial_weeks
        self.min_weeks = min_weeks
        self.max_weeks = max_weeks
        self.weekly_n_per_arm = weekly_n_per_arm
        self.baseline_rate = baseline_rate
        self.business_minimum_effect = business_minimum_effect
        self.on_confirm = on_confirm
        self.context = context
        self.record_key = record_key
        self.mirror_action_label_key = mirror_action_label_key
        self.mirror_python_code_for = mirror_python_code_for
        self.evidence_key = evidence_key
        self._rebuild_buttons()

    def _n_per_arm(self) -> int:
        return self.weeks * self.weekly_n_per_arm

    def _mde(self) -> float:
        return minimum_detectable_effect(self.baseline_rate, self._n_per_arm())

    def _meets_target(self) -> bool:
        return self._mde() <= self.business_minimum_effect

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        minus_rect = pygame.Rect(0, 0, *STEP_BUTTON_SIZE)
        minus_rect.center = (MINUS_X, STEPPER_Y)
        minus_button = Button(minus_rect, "-", self._decrement, enabled=self.weeks > self.min_weeks)

        plus_rect = pygame.Rect(0, 0, *STEP_BUTTON_SIZE)
        plus_rect.center = (PLUS_X, STEPPER_Y)
        plus_button = Button(plus_rect, "+", self._increment, enabled=self.weeks < self.max_weeks)

        confirm_rect = pygame.Rect(0, 0, *CONFIRM_SIZE)
        confirm_rect.center = (CENTER_X, CONFIRM_Y)
        # Unconditionally enabled - every weeks value is a complete plan,
        # see this class's own docstring for why no gate exists here.
        self.confirm_button = Button(confirm_rect, loc.t("runtime.continue_button"), self._confirm)

        self.buttons = ButtonGroup([minus_button, plus_button, self.confirm_button])

    def _decrement(self) -> None:
        if self.weeks > self.min_weeks:
            self.weeks -= 1
            self._rebuild_buttons()

    def _increment(self) -> None:
        if self.weeks < self.max_weeks:
            self.weeks += 1
            self._rebuild_buttons()

    def _confirm(self) -> None:
        action = self.context.record_action(
            label_key=self.mirror_action_label_key,
            python_code=self.mirror_python_code_for(self.weeks),
            key=self.record_key,
        )
        self.context.record_evidence(label_key=self.evidence_key, source_action=action, key=self.evidence_key)
        self.on_confirm(self.weeks)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 26, colors.TEXT)

        y = 76
        narrative_font_size = 14
        narrative_font = get_font(narrative_font_size)
        for key in self.narrative_keys:
            text = loc.t(key)
            draw_wrapped_text(surface, text, (60, y), 840, narrative_font_size, colors.BUTTON_TEXT_DISABLED)
            y += len(wrap_text(text, narrative_font, 840)) * 18

        draw_centered_text(surface, loc.t("lesson.l19.planner.weeks_label"), (WEEKS_VALUE_X, WEEKS_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, str(self.weeks), (WEEKS_VALUE_X, STEPPER_Y), 26, colors.TEXT)

        self.buttons.draw(surface)

        n_text = f"{loc.t('lesson.l19.planner.n_per_arm_label')} {self._n_per_arm():,}"
        draw_centered_text(surface, n_text, (CENTER_X, STAT_ROW_1_Y), 18, colors.TEXT)

        mde_text = f"{loc.t('lesson.l19.planner.mde_label')} {self._mde() * 100:.2f}pp"
        draw_centered_text(surface, mde_text, (CENTER_X, STAT_ROW_2_Y), 18, colors.TEXT)

        meets = self._meets_target()
        status_key = "lesson.l19.planner.status_meets" if meets else "lesson.l19.planner.status_not_meets"
        status_color = colors.TEXT if meets else colors.BUTTON_FOCUS_BORDER
        draw_centered_text(surface, loc.t(status_key), (CENTER_X, STATUS_Y), 16, status_color)
