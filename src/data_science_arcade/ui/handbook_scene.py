from enum import Enum

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.handbook.entries import GlossaryEntry, HandbookEntry
from data_science_arcade.handbook.registry import GLOSSARY_ENTRIES, HANDBOOK_ENTRIES, find_entry
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE, Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.handbook_pagination import paginate
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
TAB_BAR_Y = 42
TAB_SIZE = (160, 36)
TAB_SPACING = 170
CONTENT_RECT = pygame.Rect(30, 78, 900, 382)
BACK_BUTTON_Y = 495
INDEX_ROW_HEIGHT = 40
INDEX_ROW_SIZE = (820, 34)
BODY_FONT_SIZE = 15
BODY_LINE_SPACING = 4
BODY_TOP_OFFSET = 78  # below title + category, within CONTENT_RECT
NAV_RESERVED_HEIGHT = 90  # page-nav row + related row, reserved at the bottom of CONTENT_RECT
# 40/10 (a 30px center-to-center gap) left the page-nav row's own bottom
# edge overlapping the related row's top edge by a few pixels once real
# button heights are accounted for - caught by eye in a real screenshot,
# not by any test. 55/10 gives real clearance between the two rows.
PAGE_NAV_Y_OFFSET = 55  # from the bottom of the reserved footer
RELATED_Y_OFFSET = 10  # from the bottom of the reserved footer
RELATED_BUTTON_HEIGHT = 30
RELATED_BUTTON_PADDING = 28  # horizontal padding added to each label's own measured width
RELATED_BUTTON_GAP = 10
SOURCES_RESERVED_HEIGHT = 40  # extra vertical space reserved on every page when an article has source_keys


class HandbookTab(Enum):
    ARTICLES = "handbook.tab.articles"
    GLOSSARY = "handbook.tab.glossary"


def _display_key(entry: HandbookEntry | GlossaryEntry) -> str:
    return entry.title_key if isinstance(entry, HandbookEntry) else entry.term_key


class HandbookScene(Scene):
    """The Analyst Handbook (spec §46): a bilingual reference library
    reachable from the Hub - an ARTICLES tab (full-prose theory, paginated
    - see ui/handbook_pagination.py) and a GLOSSARY tab (short lookup
    terms, one screen each, no pagination needed at that length). Both
    tabs share one "related concepts" mechanism via handbook/registry.py's
    find_entry(), which searches the union of both registries - a related
    reference can jump from an article to a glossary term or back, since
    neither kind is privileged over the other here.

    Covers all 30 lessons today (26 articles, 39 glossary terms) - see
    decisions/CONTENT_STYLE_GUIDE.md for the standard the content itself
    was written against. Both index lists paginate at a fixed, always-
    legible row height rather than shrinking rows to fit everything on
    one screen - real pagination the same way the article body already
    does, not a second, different overflow strategy."""

    def __init__(self, app, initial_entry_id: str | None = None) -> None:
        super().__init__(app)
        self.active_tab = HandbookTab.ARTICLES
        self.selected_article_id: str | None = None
        self.selected_glossary_id: str | None = None
        self.pages: list[list[str]] = [[]]
        self.page_index = 0
        self.index_page = 0

        if initial_entry_id is not None:
            self._open_entry(initial_entry_id)

        self._rebuild_buttons()

    def on_enter(self) -> None:
        # Locale may have changed while Handbook was off the scene stack
        # (Settings is only ever reachable from MainMenuScene, so this
        # can't happen mid-frame - see ui/settings_scene.py - but it can
        # happen between visits). Re-paginate so page breaks reflect the
        # current language's real text, and reset to page 1 rather than
        # guessing a page count that no longer matches.
        if self.selected_article_id is not None:
            self._paginate_current_article()
        self._rebuild_buttons()

    def _current_article(self) -> HandbookEntry | None:
        if self.selected_article_id is None:
            return None
        entry = find_entry(self.selected_article_id)
        return entry if isinstance(entry, HandbookEntry) else None

    def _current_glossary_entry(self) -> GlossaryEntry | None:
        if self.selected_glossary_id is None:
            return None
        entry = find_entry(self.selected_glossary_id)
        return entry if isinstance(entry, GlossaryEntry) else None

    def _paginate_current_article(self) -> None:
        article = self._current_article()
        if article is None:
            self.pages = [[]]
            self.page_index = 0
            return
        loc = self.app.localization
        paragraphs = [loc.t(key) for key in article.body_paragraph_keys]
        font = get_font(BODY_FONT_SIZE)
        line_height = font.get_linesize() + BODY_LINE_SPACING
        available_height = CONTENT_RECT.height - BODY_TOP_OFFSET - NAV_RESERVED_HEIGHT
        if article.source_keys:
            # Reserved on every page, not just the last one that ends up
            # showing it: pagination doesn't know in advance which page
            # will be last, so a per-page budget that only shrinks for
            # "the last page" can't be computed in one pass. Reserving
            # this uniformly costs at most one extra page for an article
            # with sources, in exchange for the sources line never
            # competing with the nav/related rows below it - a real gap
            # until now, since no real article populated source_keys yet.
            available_height -= SOURCES_RESERVED_HEIGHT
        max_lines_per_page = max(1, available_height // line_height)
        self.pages = paginate(paragraphs, font, CONTENT_RECT.width - 40, max_lines_per_page)
        self.page_index = 0

    def _sources_line_text(self, article: HandbookEntry) -> str | None:
        if not article.source_keys or self.page_index != len(self.pages) - 1:
            return None
        loc = self.app.localization
        sources_text = "; ".join(loc.t(key) for key in article.source_keys)
        return f"{loc.t('handbook.sources_label')}: {sources_text}"

    def _open_entry(self, entry_id: str) -> None:
        entry = find_entry(entry_id)
        if isinstance(entry, HandbookEntry):
            self.active_tab = HandbookTab.ARTICLES
            self.selected_article_id = entry.id
            self.selected_glossary_id = None
            self._paginate_current_article()
        elif isinstance(entry, GlossaryEntry):
            self.active_tab = HandbookTab.GLOSSARY
            self.selected_glossary_id = entry.id
            self.selected_article_id = None

    def _make_switch_tab(self, tab: HandbookTab):
        def switch() -> None:
            self.active_tab = tab
            self.selected_article_id = None
            self.selected_glossary_id = None
            self.index_page = 0
            self._rebuild_buttons()

        return switch

    def _make_open_article(self, entry_id: str):
        def open_article() -> None:
            self.selected_article_id = entry_id
            self._paginate_current_article()
            self._rebuild_buttons()

        return open_article

    def _make_open_glossary(self, entry_id: str):
        def open_glossary() -> None:
            self.selected_glossary_id = entry_id
            self._rebuild_buttons()

        return open_glossary

    def _make_open_related(self, entry_id: str):
        def open_related() -> None:
            self._open_entry(entry_id)
            self._rebuild_buttons()

        return open_related

    def _next_page(self) -> None:
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
            self._rebuild_buttons()

    def _previous_page(self) -> None:
        if self.page_index > 0:
            self.page_index -= 1
            self._rebuild_buttons()

    def _current_index_entries(self) -> tuple:
        raw = HANDBOOK_ENTRIES if self.active_tab is HandbookTab.ARTICLES else GLOSSARY_ENTRIES
        if raw and isinstance(raw[0], GlossaryEntry):
            # Alphabetical by the CURRENT locale's own translated term - a
            # reference lookup list is scanned, not read top to bottom, so
            # it needs a predictable order a player can jump into midway;
            # articles keep their curriculum order instead (a deliberate
            # reading sequence, not something to alphabetize away).
            loc = self.app.localization
            return tuple(sorted(raw, key=lambda entry: loc.t(entry.term_key)))
        return raw

    def _index_rows_per_page(self) -> int:
        available_height = CONTENT_RECT.height - 30 - NAV_RESERVED_HEIGHT
        return max(1, available_height // INDEX_ROW_HEIGHT)

    def _index_total_pages(self, entries: tuple) -> int:
        if not entries:
            return 1
        rows_per_page = self._index_rows_per_page()
        return -(-len(entries) // rows_per_page)  # ceil division

    def _next_index_page(self) -> None:
        entries = self._current_index_entries()
        if self.index_page < self._index_total_pages(entries) - 1:
            self.index_page += 1
            self._rebuild_buttons()

    def _previous_index_page(self) -> None:
        if self.index_page > 0:
            self.index_page -= 1
            self._rebuild_buttons()

    def _back(self) -> None:
        if self.selected_article_id is not None:
            self.selected_article_id = None
        elif self.selected_glossary_id is not None:
            self.selected_glossary_id = None
        else:
            self.app.scenes.pop()
            return
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        for index, tab in enumerate(HandbookTab):
            rect = pygame.Rect(0, 0, *TAB_SIZE)
            first_center_x = CENTER_X - (len(HandbookTab) - 1) * TAB_SPACING // 2
            rect.center = (first_center_x + index * TAB_SPACING, TAB_BAR_Y)
            buttons.append(Button(rect, loc.t(tab.value), self._make_switch_tab(tab)))

        if self.active_tab is HandbookTab.ARTICLES:
            if self.selected_article_id is not None:
                buttons.extend(self._build_article_detail_buttons())
            else:
                buttons.extend(self._build_index_buttons(self._current_index_entries(), self._make_open_article))
        else:
            if self.selected_glossary_id is not None:
                buttons.extend(self._build_glossary_detail_buttons())
            else:
                buttons.extend(self._build_index_buttons(self._current_index_entries(), self._make_open_glossary))

        back_rect = pygame.Rect(0, 0, 160, 44)
        back_rect.center = (CENTER_X, BACK_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("common.back"), self._back)
        buttons.append(self.back_button)

        self.buttons = ButtonGroup(buttons)
        self.buttons.focus_index = list(HandbookTab).index(self.active_tab)

    def _build_index_buttons(self, entries: tuple, make_open) -> list[Button]:
        # Real pagination, not a shrink-to-fit row height: this index has
        # grown from the original "3-4 articles, ~10 glossary terms" it
        # was built for to 26 articles and 39 glossary terms, and cramming
        # every one of them into one fixed-height list made every row's
        # own real 24px button text overlap its neighbors - the rects
        # themselves stayed within CONTENT_RECT (nothing here clips
        # overflow, so that much always "passed"), but the text rendered
        # inside each shrunk row didn't fit the row it was drawn in. A
        # fixed, always-legible row height paginates instead, matching
        # the same discipline this file's own article-body pagination
        # already uses (ui/handbook_pagination.py).
        if not entries:
            return []
        loc = self.app.localization
        rows_per_page = self._index_rows_per_page()
        total_pages = self._index_total_pages(entries)
        self.index_page = min(self.index_page, total_pages - 1)
        start = self.index_page * rows_per_page
        page_entries = entries[start : start + rows_per_page]

        buttons = []
        for row_index, entry in enumerate(page_entries):
            rect = pygame.Rect(0, 0, *INDEX_ROW_SIZE)
            rect.center = (CENTER_X, CONTENT_RECT.top + 30 + row_index * INDEX_ROW_HEIGHT)
            label = loc.t(_display_key(entry))
            buttons.append(Button(rect, label, make_open(entry.id)))

        if total_pages > 1:
            nav_y = CONTENT_RECT.bottom - PAGE_NAV_Y_OFFSET
            back_rect = pygame.Rect(0, 0, 120, 36)
            back_rect.center = (CENTER_X - 80, nav_y)
            self.index_back_page_button = Button(
                back_rect, loc.t("handbook.previous_page"), self._previous_index_page, enabled=self.index_page > 0
            )
            buttons.append(self.index_back_page_button)

            next_rect = pygame.Rect(0, 0, 120, 36)
            next_rect.center = (CENTER_X + 80, nav_y)
            self.index_next_page_button = Button(
                next_rect, loc.t("handbook.next_page"), self._next_index_page, enabled=self.index_page < total_pages - 1
            )
            buttons.append(self.index_next_page_button)

        return buttons

    def _build_article_detail_buttons(self) -> list[Button]:
        article = self._current_article()
        if article is None:
            return []
        loc = self.app.localization
        buttons = []

        # Dedicated keys, not brief.back/brief.next - both read "Back" in
        # English (and "Wstecz" in Polish), identical to the global exit
        # Back button drawn right below this row on the very same screen,
        # doing something completely different (previous paragraph vs.
        # leave the article) - the exact "what am I even clicking"
        # confusion this whole pass exists to fix, caught in the same
        # screenshot review that caught the index's own identical bug.
        nav_y = CONTENT_RECT.bottom - PAGE_NAV_Y_OFFSET
        back_page_rect = pygame.Rect(0, 0, 120, 36)
        back_page_rect.center = (CENTER_X - 80, nav_y)
        self.back_page_button = Button(
            back_page_rect, loc.t("handbook.previous_page"), self._previous_page, enabled=self.page_index > 0
        )
        buttons.append(self.back_page_button)

        next_page_rect = pygame.Rect(0, 0, 120, 36)
        next_page_rect.center = (CENTER_X + 80, nav_y)
        self.next_page_button = Button(
            next_page_rect, loc.t("handbook.next_page"), self._next_page, enabled=self.page_index < len(self.pages) - 1
        )
        buttons.append(self.next_page_button)

        related_y = CONTENT_RECT.bottom - RELATED_Y_OFFSET
        related_labels = []
        for related_id in article.related_entry_ids:
            related_entry = find_entry(related_id)
            if related_entry is not None:
                related_labels.append((related_id, loc.t(_display_key(related_entry))))

        # Related-concept labels range from a single short word to a full
        # multi-word Polish phrase (measured, not guessed - the original
        # fixed-width slot overflowed for "Poziom szczegółowości danych")
        # so each button is sized to its own real label instead of one
        # shared constant no single width could safely cover.
        font = get_font(BUTTON_TEXT_SIZE)
        widths = [font.size(label)[0] + RELATED_BUTTON_PADDING for _, label in related_labels]
        total_width = sum(widths) + RELATED_BUTTON_GAP * max(len(widths) - 1, 0)
        x = CENTER_X - total_width // 2
        for (related_id, label), button_width in zip(related_labels, widths):
            rect = pygame.Rect(0, 0, button_width, RELATED_BUTTON_HEIGHT)
            rect.center = (x + button_width // 2, related_y)
            buttons.append(Button(rect, label, self._make_open_related(related_id)))
            x += button_width + RELATED_BUTTON_GAP

        return buttons

    def _build_glossary_detail_buttons(self) -> list[Button]:
        entry = self._current_glossary_entry()
        if entry is None or entry.related_entry_id is None:
            return []
        loc = self.app.localization
        related_entry = find_entry(entry.related_entry_id)
        if related_entry is None:
            return []
        rect = pygame.Rect(0, 0, 280, 40)
        rect.center = (CENTER_X, CONTENT_RECT.bottom - RELATED_Y_OFFSET)
        return [Button(rect, loc.t("handbook.read_full_article"), self._make_open_related(entry.related_entry_id))]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, CONTENT_RECT, border_radius=8)
        self.buttons.draw(surface)

        if self.active_tab is HandbookTab.ARTICLES:
            if self.selected_article_id is not None:
                self._draw_article_detail(surface)
            else:
                self._draw_index(surface, self._current_index_entries())
        else:
            if self.selected_glossary_id is not None:
                self._draw_glossary_detail(surface)
            else:
                self._draw_index(surface, self._current_index_entries())

    def _draw_index(self, surface: pygame.Surface, entries: tuple) -> None:
        if not entries:
            return
        # Row positions are drawn by the buttons themselves (Button.draw
        # renders its own label) - only the page indicator (when there's
        # more than one page) needs its own draw call here.
        total_pages = self._index_total_pages(entries)
        if total_pages > 1:
            progress = f"{self.index_page + 1} / {total_pages}"
            draw_centered_text(surface, progress, (CENTER_X, CONTENT_RECT.bottom - PAGE_NAV_Y_OFFSET - 26), 13, colors.BUTTON_TEXT_DISABLED)

    def _draw_article_detail(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        article = self._current_article()
        if article is None:
            return
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40

        draw_centered_text(surface, loc.t(article.title_key), (CENTER_X, CONTENT_RECT.top + 22), 22, colors.TEXT)
        draw_centered_text(surface, loc.t(article.category_key), (CENTER_X, CONTENT_RECT.top + 50), 14, colors.BUTTON_TEXT_DISABLED)

        page = self.pages[self.page_index] if self.pages else []
        line_height = get_font(BODY_FONT_SIZE).get_linesize() + BODY_LINE_SPACING
        body_top = CONTENT_RECT.top + BODY_TOP_OFFSET
        for index, line in enumerate(page):
            if line:
                draw_single_line(surface, line, (left, body_top + index * line_height), width, BODY_FONT_SIZE, colors.TEXT)

        if len(self.pages) > 1:
            progress = f"{self.page_index + 1} / {len(self.pages)}"
            draw_centered_text(surface, progress, (CENTER_X, CONTENT_RECT.bottom - PAGE_NAV_Y_OFFSET - 26), 13, colors.BUTTON_TEXT_DISABLED)

        sources_line = self._sources_line_text(article)
        if sources_line is not None:
            draw_wrapped_text(
                surface,
                sources_line,
                (left, body_top + len(page) * line_height + 10),
                width,
                12,
                colors.BUTTON_TEXT_DISABLED,
            )

    def _draw_glossary_detail(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        entry = self._current_glossary_entry()
        if entry is None:
            return
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40

        draw_centered_text(surface, loc.t(entry.term_key), (CENTER_X, CONTENT_RECT.top + 30), 22, colors.TEXT)
        draw_wrapped_text(surface, loc.t(entry.definition_key), (left, CONTENT_RECT.top + 70), width, 15, colors.TEXT)
