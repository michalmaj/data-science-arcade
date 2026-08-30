from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Pausable, Scene
from data_science_arcade.lessons.framework.investigation import InvestigationLead, InvestigationResult
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 76
PROMPT_MAX_WIDTH = 820
OPTION_SIZE = (620, 40)
FIRST_OPTION_Y = 140
OPTION_SPACING = 46
CONCLUDE_BUTTON_SIZE = (280, 48)
CONCLUDE_BUTTON_Y = 460


class InvestigationHubScene(Scene):
    """A menu of investigation leads the player chooses among, rather than
    a fixed sequence (spec §25 Lesson 30 'The Data Incident': "the student
    must decide where to investigate"). Picking a lead pushes its own
    reused scene, wrapped in its own Pausable whose Escape steps back to
    this hub - not a pause menu, since the hub is the thing LessonRunner
    already wraps in the real pause menu, one level up. Escaping a lead
    losing its own progress and needing to reopen it fresh mirrors the
    existing pause menu's own "Quit discards this attempt, no confirm"
    precedent, just one level shallower.

    Finishing a lead pops back here and marks it investigated (any
    completion counts - a lead's own reused scene grades its own choices,
    if it grades them at all; this hub only tracks *that* it was done).
    "Conclude" enables once `minimum_leads` have been investigated, in
    whatever order the player chose - genuine open navigation built
    entirely from scenes this course already has, per the spec's own
    "reuse systems... not a special-case engine" note, rather than a new
    investigation engine.

    Every lead's own content stays fixed regardless of which others were
    visited - the twist and final decision never depend on *which* subset
    was investigated, only that enough real investigation happened -
    matching every prior lesson's "grade on method, not a lucky path"
    discipline."""

    def __init__(
        self,
        app,
        title_key: str,
        prompt_key: str,
        leads: tuple[InvestigationLead, ...],
        minimum_leads: int,
        on_complete: Callable[[InvestigationResult], None],
        investigated_marker_key: str = "investigation.investigated_marker",
        conclude_button_key: str = "investigation.conclude_button",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.prompt_key = prompt_key
        self.leads = leads
        self.minimum_leads = minimum_leads
        self.on_complete = on_complete
        self.investigated_marker_key = investigated_marker_key
        self.conclude_button_key = conclude_button_key
        self.investigated: set[str] = set()
        self._rebuild_buttons()

    def _label_for(self, lead: InvestigationLead) -> str:
        loc = self.app.localization
        label = loc.t(lead.label_key)
        if lead.key in self.investigated:
            return f"{label} - {loc.t(self.investigated_marker_key)}"
        return label

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons = []
        for index, lead in enumerate(self.leads):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, self._label_for(lead), self._make_open(lead)))

        conclude_rect = pygame.Rect(0, 0, *CONCLUDE_BUTTON_SIZE)
        conclude_rect.center = (CENTER_X, CONCLUDE_BUTTON_Y)
        enough_investigated = len(self.investigated) >= self.minimum_leads
        self.conclude_button = Button(conclude_rect, loc.t(self.conclude_button_key), self._conclude, enabled=enough_investigated)
        buttons.append(self.conclude_button)

        self.buttons = ButtonGroup(buttons)

    def _make_open(self, lead: InvestigationLead) -> Callable[[], None]:
        def open_lead() -> None:
            lead_scene = lead.build_scene(self._make_close(lead.key))
            self.app.scenes.push(Pausable(self.app, lead_scene, on_escape=self.app.scenes.pop))

        return open_lead

    def _make_close(self, lead_key: str) -> Callable[..., None]:
        def close(*_choices) -> None:
            self.investigated.add(lead_key)
            self._rebuild_buttons()
            self.app.scenes.pop()

        return close

    def _conclude(self) -> None:
        self.on_complete(frozenset(self.investigated))

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps this stage
        # in Pausable, which intercepts Escape before this scene sees it -
        # same discipline as every other stage scene.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        progress = f"{len(self.investigated)} / {len(self.leads)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t(self.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, 16, colors.TEXT)

        self.buttons.draw(surface)
