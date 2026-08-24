import pygame

from data_science_arcade.ui.button import Button


class ButtonGroup:
    """A vertical list of buttons with mouse hover and keyboard focus navigation.

    Keyboard: Up/Down (or Tab/Shift+Tab) move focus, Return/Space activate the
    focused button. Mouse: hover sets focus, click activates. Satisfies the
    spec's keyboard-navigation-with-visible-focus accessibility requirement.
    Disabled buttons (e.g. locked lessons) are skipped entirely - not
    focusable, not hoverable, not clickable.
    """

    def __init__(self, buttons: list[Button]) -> None:
        self.buttons = buttons
        self.focus_index = self._first_enabled_index()

    def _enabled_indices(self) -> list[int]:
        return [index for index, button in enumerate(self.buttons) if button.enabled]

    def _first_enabled_index(self) -> int:
        enabled = self._enabled_indices()
        return enabled[0] if enabled else -1

    def sync_focus(self) -> None:
        """Call after changing which buttons are enabled outside of normal
        navigation (e.g. a course map re-rendering unlock state), to make
        sure focus isn't left sitting on a now-disabled button."""
        if self.focus_index not in self._enabled_indices():
            self.focus_index = self._first_enabled_index()

    def _move_focus(self, step: int) -> None:
        enabled = self._enabled_indices()
        if not enabled:
            self.focus_index = -1
            return
        if self.focus_index not in enabled:
            self.focus_index = enabled[0]
            return
        position = enabled.index(self.focus_index)
        self.focus_index = enabled[(position + step) % len(enabled)]

    def _activate_focused(self) -> None:
        if 0 <= self.focus_index < len(self.buttons):
            button = self.buttons[self.focus_index]
            if button.enabled:
                button.on_activate()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            for index, button in enumerate(self.buttons):
                if button.enabled and button.rect.collidepoint(event.pos):
                    self.focus_index = index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.enabled and button.rect.collidepoint(event.pos):
                    button.on_activate()
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._move_focus(-1 if getattr(event, "mod", 0) & pygame.KMOD_SHIFT else 1)
            elif event.key == pygame.K_DOWN:
                self._move_focus(1)
            elif event.key == pygame.K_UP:
                self._move_focus(-1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._activate_focused()

    def draw(self, surface: pygame.Surface) -> None:
        for index, button in enumerate(self.buttons):
            button.draw(surface, focused=index == self.focus_index)
