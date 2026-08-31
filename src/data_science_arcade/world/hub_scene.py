import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.narrative.npc import MENTOR
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.handbook_scene import HandbookScene
from data_science_arcade.ui.text import draw_centered_text
from data_science_arcade.world.hub_dialogue import MENTOR_GREETING

CENTER_X = LOGICAL_SIZE[0] // 2
TERMINAL_SIZE = (280, 90)
MENTOR_SIZE = (200, 90)
HANDBOOK_SIZE = (240, 70)
BACK_BUTTON_Y = 460


class HubScene(Scene):
    """The NovaMart hub: a narrative/navigation layer, not a free-roam map
    (spec §15.3 explicitly warns against the hub becoming a large RPG map).
    A few clickable hotspots stand in for the eventual environment art:
    the Mission Terminal (-> course map), a recurring NPC (-> dialogue),
    and the Analyst Handbook (-> HandbookScene, spec §46)."""

    def __init__(self, app) -> None:
        super().__init__(app)
        terminal_rect = pygame.Rect(0, 0, *TERMINAL_SIZE)
        terminal_rect.center = (300, 280)
        mentor_rect = pygame.Rect(0, 0, *MENTOR_SIZE)
        mentor_rect.center = (660, 280)
        handbook_rect = pygame.Rect(0, 0, *HANDBOOK_SIZE)
        handbook_rect.center = (CENTER_X, 380)
        back_rect = pygame.Rect(0, 0, 200, 48)
        back_rect.center = (CENTER_X, BACK_BUTTON_Y)

        loc = app.localization
        self.terminal_button = Button(terminal_rect, loc.t("hub.mission_terminal"), self._open_terminal)
        self.mentor_button = Button(mentor_rect, loc.t(MENTOR.name_key), self._talk_to_mentor)
        self.handbook_button = Button(handbook_rect, loc.t("hub.handbook"), self._open_handbook)
        self.back_button = Button(back_rect, loc.t("common.back"), self._back)
        self.buttons = ButtonGroup([self.terminal_button, self.mentor_button, self.handbook_button, self.back_button])

    def _open_terminal(self) -> None:
        self.app.scenes.push(CourseMapScene(self.app))

    def _talk_to_mentor(self) -> None:
        dialogue = DialogueScene(self.app, MENTOR_GREETING, on_complete=self.app.scenes.pop, background=self)
        self.app.scenes.push(dialogue)

    def _open_handbook(self) -> None:
        self.app.scenes.push(HandbookScene(self.app))

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, self.app.localization.t("hub.title"), (CENTER_X, 60), 34, colors.TEXT)
        self.buttons.draw(surface)
