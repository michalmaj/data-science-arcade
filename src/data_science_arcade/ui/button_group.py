import pygame

from data_science_arcade.ui.button import Button


class ButtonGroup:
    """A vertical list of buttons with mouse hover and keyboard focus navigation.

    Keyboard: Up/Down (or Tab/Shift+Tab) move focus, Return/Space activate the
    focused button. Mouse: hover sets focus, click activates. Satisfies the
    spec's keyboard-navigation-with-visible-focus accessibility requirement.
    """

    def __init__(self, buttons: list[Button]) -> None:
        self.buttons = buttons
        self.focus_index = 0 if buttons else -1

    def _move_focus(self, step: int) -> None:
        if not self.buttons:
            return
        self.focus_index = (self.focus_index + step) % len(self.buttons)

    def _activate_focused(self) -> None:
        if 0 <= self.focus_index < len(self.buttons):
            self.buttons[self.focus_index].on_activate()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            for index, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.focus_index = index
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
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
        mouse_pos = pygame.mouse.get_pos()
        for index, button in enumerate(self.buttons):
            focused = index == self.focus_index
            hovered = button.rect.collidepoint(mouse_pos)
            button.draw(surface, focused=focused, hovered=hovered)
