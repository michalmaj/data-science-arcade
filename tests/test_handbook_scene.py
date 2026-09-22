import os
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.fonts import get_font
from data_science_arcade.handbook.entries import HandbookEntry
from data_science_arcade.handbook.registry import GLOSSARY_ENTRIES, HANDBOOK_ENTRIES
from data_science_arcade.ui.handbook_scene import CONTENT_RECT, HandbookScene, HandbookTab


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_on_the_articles_tab_showing_the_index():
    app = _init_app()
    try:
        scene = HandbookScene(app)
        assert scene.active_tab is HandbookTab.ARTICLES
        assert scene.selected_article_id is None
    finally:
        pygame.quit()


def test_switching_tabs_preserves_correct_focus_index():
    # Tab buttons are appended before any content buttons in
    # _rebuild_buttons - focus_index must land on the tab that's actually
    # showing, matching WorkbenchScene's own precedent exactly.
    app = _init_app()
    try:
        scene = HandbookScene(app)
        scene.buttons.buttons[1].on_activate()  # GLOSSARY tab
        assert scene.active_tab is HandbookTab.GLOSSARY
        assert scene.buttons.focus_index == list(HandbookTab).index(HandbookTab.GLOSSARY)
    finally:
        pygame.quit()


def test_opening_an_article_from_the_index_shows_its_detail():
    app = _init_app()
    try:
        scene = HandbookScene(app)
        first_article_button = scene.buttons.buttons[2]  # after the 2 tab buttons
        first_article_button.on_activate()

        assert scene.selected_article_id == HANDBOOK_ENTRIES[0].id
        assert len(scene.pages) >= 1
        assert scene.page_index == 0
    finally:
        pygame.quit()


def test_opening_a_glossary_term_from_the_index_shows_its_detail():
    # The glossary index is sorted alphabetically by the active locale's
    # own translated term (a lookup list, unlike the curriculum-ordered
    # articles list) - this asserts against that real sorted order rather
    # than GLOSSARY_ENTRIES[0], which is only the first *registry* entry
    # and isn't generally the alphabetically-first one in every locale.
    app = _init_app()
    try:
        scene = HandbookScene(app)
        scene.buttons.buttons[1].on_activate()  # GLOSSARY tab
        expected_first_id = min(GLOSSARY_ENTRIES, key=lambda e: app.localization.t(e.term_key)).id
        first_term_button = scene.buttons.buttons[2]
        first_term_button.on_activate()

        assert scene.selected_glossary_id == expected_first_id
    finally:
        pygame.quit()


def test_back_from_detail_returns_to_index_then_pops_the_scene():
    app = _init_app()
    try:
        scene = HandbookScene(app)
        app.scenes.push(scene)
        scene.buttons.buttons[2].on_activate()  # open first article
        assert scene.selected_article_id is not None

        scene.back_button.on_activate()
        assert scene.selected_article_id is None
        assert app.scenes.current is scene  # still on Handbook, just back at the index

        scene.back_button.on_activate()
        assert app.scenes.current is not scene  # popped out of Handbook entirely
    finally:
        pygame.quit()


def test_next_and_back_page_are_disabled_at_the_real_boundaries():
    app = _init_app()
    try:
        # Find a real article that actually paginates to more than one
        # page in at least one locale, so Next has something to prove.
        scene = HandbookScene(app)
        multi_page_id = None
        for entry in HANDBOOK_ENTRIES:
            scene._open_entry(entry.id)
            if len(scene.pages) > 1:
                multi_page_id = entry.id
                break
        assert multi_page_id is not None, "expected at least one real article to paginate to >1 page"

        scene._open_entry(multi_page_id)
        scene._rebuild_buttons()
        assert scene.back_page_button.enabled is False
        assert scene.next_page_button.enabled is True

        while scene.next_page_button.enabled:
            scene.next_page_button.on_activate()

        assert scene.page_index == len(scene.pages) - 1
        assert scene.next_page_button.enabled is False
        assert scene.back_page_button.enabled is True
    finally:
        pygame.quit()


def test_related_concept_jump_crosses_from_an_article_to_a_glossary_term_and_back():
    app = _init_app()
    try:
        scene = HandbookScene(app)
        # observation_unit_and_grain has real related glossary entries.
        scene._open_entry("observation_unit_and_grain")
        scene._rebuild_buttons()
        related_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("handbook.glossary.observation_unit.term"))
        related_button.on_activate()

        assert scene.active_tab is HandbookTab.GLOSSARY
        assert scene.selected_glossary_id == "observation_unit"

        # And back: the glossary entry's own related_entry_id points at
        # the article - proving the union-aware lookup works both ways.
        read_full_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("handbook.read_full_article"))
        read_full_button.on_activate()

        assert scene.active_tab is HandbookTab.ARTICLES
        assert scene.selected_article_id == "observation_unit_and_grain"
    finally:
        pygame.quit()


def test_no_wrapped_line_in_any_real_article_exceeds_the_content_width_in_either_locale():
    # The load-bearing check: raw paragraphs are *expected* to exceed
    # max_width before wrapping - this asserts on paginate()'s actual
    # output lines, which must not.
    app = _init_app()
    try:
        for locale in ("en", "pl"):
            app.localization.set_locale(locale)
            scene = HandbookScene(app)
            font = get_font(15)
            for entry in HANDBOOK_ENTRIES:
                scene._open_entry(entry.id)
                for page in scene.pages:
                    for line in page:
                        assert font.size(line)[0] <= CONTENT_RECT.width - 40, (entry.id, locale, line)
    finally:
        pygame.quit()


def test_draw_does_not_crash_for_any_real_entry_in_either_tab_or_locale():
    app = _init_app()
    try:
        for locale in ("en", "pl"):
            app.localization.set_locale(locale)
            scene = HandbookScene(app)
            scene.draw(app.logical_surface)  # index, ARTICLES

            for entry in HANDBOOK_ENTRIES:
                scene._open_entry(entry.id)
                scene._rebuild_buttons()
                scene.draw(app.logical_surface)

            scene.buttons.buttons[1].on_activate()  # GLOSSARY tab, index
            scene.draw(app.logical_surface)
            for entry in GLOSSARY_ENTRIES:
                scene._open_entry(entry.id)
                scene._rebuild_buttons()
                scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_on_enter_reset_to_page_one_after_a_locale_switch():
    app = _init_app()
    try:
        scene = HandbookScene(app)
        multi_page_id = next(
            (entry.id for entry in HANDBOOK_ENTRIES if len(HandbookScene(app, entry.id).pages) > 1),
            None,
        )
        assert multi_page_id is not None
        scene._open_entry(multi_page_id)
        scene.next_page_button = None
        scene._rebuild_buttons()
        scene.next_page_button.on_activate()
        assert scene.page_index == 1

        app.localization.set_locale("pl" if app.localization.locale == "en" else "en")
        scene.on_enter()

        assert scene.page_index == 0
    finally:
        pygame.quit()


def test_constructing_with_an_initial_entry_id_opens_it_directly():
    app = _init_app()
    try:
        scene = HandbookScene(app, initial_entry_id="metrics_need_definitions")
        assert scene.selected_article_id == "metrics_need_definitions"
    finally:
        pygame.quit()


def test_every_index_row_fits_inside_content_rect_for_both_tabs():
    # Caught by eye in a real screenshot, not by any test: a fixed row
    # spacing sized comfortably for the 4 real articles once shrank to
    # cram all 26 real articles / 39 real glossary terms into the same
    # space instead of paginating - rects stayed technically within
    # CONTENT_RECT, but rows became too short for their own real 24px
    # button text, which then visually overlapped its neighbors (a defect
    # this rect-bounds check alone can't see - the real fix is real
    # pagination, asserted below).
    app = _init_app()
    try:
        scene = HandbookScene(app)
        for is_glossary in (False, True):
            if is_glossary:
                scene.buttons.buttons[1].on_activate()
            index_buttons = scene.buttons.buttons[2:-1]  # after the 2 tabs, before the global Back
            row_buttons = [b for b in index_buttons if b not in (scene.index_back_page_button, scene.index_next_page_button)]
            assert len(row_buttons) <= scene._index_rows_per_page()
            for button in index_buttons:
                assert CONTENT_RECT.top <= button.rect.top and button.rect.bottom <= CONTENT_RECT.bottom
    finally:
        pygame.quit()


def test_glossary_index_is_alphabetical_per_locale_articles_are_not():
    # The real regression this guards: sorting only the glossary tab (a
    # lookup list) alphabetically, per the CURRENTLY active locale's own
    # translated term - not a fixed order baked in at authoring time,
    # which would only ever be alphabetical in one language. Confirmed
    # with a locale where the alphabetically-first term is NOT
    # GLOSSARY_ENTRIES[0] (it is in English, by coincidence).
    app = _init_app()
    try:
        app.localization.set_locale("pl")
        scene = HandbookScene(app)
        scene.buttons.buttons[1].on_activate()  # GLOSSARY tab
        assert GLOSSARY_ENTRIES[0].id != "exploratory_analysis"  # sanity: real reordering happened
        ordered = scene._current_index_entries()
        terms = [app.localization.t(entry.term_key) for entry in ordered]
        assert terms == sorted(terms)

        article_order = [entry.id for entry in HANDBOOK_ENTRIES]
        scene.buttons.buttons[0].on_activate()  # ARTICLES tab
        assert [entry.id for entry in scene._current_index_entries()] == article_order
    finally:
        pygame.quit()


def test_every_real_entry_is_reachable_by_paging_through_the_index():
    app = _init_app()
    try:
        for is_glossary, entries in ((False, HANDBOOK_ENTRIES), (True, GLOSSARY_ENTRIES)):
            scene = HandbookScene(app)
            if is_glossary:
                scene.buttons.buttons[1].on_activate()

            seen_ids: set[str] = set()
            for _ in range(len(entries) + 1):  # hard cap - never trust an unbounded paging loop
                row_buttons = [
                    b
                    for b in scene.buttons.buttons[2:-1]
                    if b not in (scene.index_back_page_button, scene.index_next_page_button)
                ]
                assert 1 <= len(row_buttons) <= scene._index_rows_per_page()
                for button in row_buttons:
                    button.on_activate()
                    if is_glossary:
                        seen_ids.add(scene.selected_glossary_id)
                        scene.selected_glossary_id = None
                    else:
                        seen_ids.add(scene.selected_article_id)
                        scene.selected_article_id = None
                    scene._rebuild_buttons()
                if not scene.index_next_page_button.enabled:
                    break
                scene.index_next_page_button.on_activate()

            assert seen_ids == {entry.id for entry in entries}
    finally:
        pygame.quit()


def test_sources_line_uses_the_dedicated_sources_label_not_related():
    app = _init_app()
    try:
        synthetic = HandbookEntry(
            id="synthetic_with_sources",
            title_key="app.title",
            category_key="handbook.category.foundations",
            body_paragraph_keys=("app.title",),
            source_keys=("app.title",),
        )
        with patch("data_science_arcade.handbook.registry.HANDBOOK_ENTRIES", (synthetic,)):
            scene = HandbookScene(app, initial_entry_id="synthetic_with_sources")
            line = scene._sources_line_text(synthetic)

        assert line is not None
        assert line.startswith(app.localization.t("handbook.sources_label"))
        assert not line.startswith(app.localization.t("handbook.related_label"))
    finally:
        pygame.quit()


def test_sources_line_only_appears_on_the_last_page():
    app = _init_app()
    try:
        synthetic = HandbookEntry(
            id="synthetic_with_sources",
            title_key="app.title",
            category_key="handbook.category.foundations",
            body_paragraph_keys=("app.title",),
            source_keys=("app.title",),
        )
        with patch("data_science_arcade.handbook.registry.HANDBOOK_ENTRIES", (synthetic,)):
            scene = HandbookScene(app, initial_entry_id="synthetic_with_sources")
            scene.pages = [["line one"], ["line two"]]  # force a 2-page article regardless of real content length

            scene.page_index = 0
            assert scene._sources_line_text(synthetic) is None

            scene.page_index = 1
            assert scene._sources_line_text(synthetic) is not None
    finally:
        pygame.quit()


def test_pagination_reserves_extra_height_when_an_article_has_sources():
    # A real gap until now: nothing reserved room for the sources line,
    # so on a full last page it could land in (or past) the nav/related
    # rows below it - untested because no real article used source_keys.
    # Reuses a real, already-long body paragraph (repeated to guarantee
    # more than one page's worth of lines) rather than fabricating text
    # or monkeypatching localization globally.
    app = _init_app()
    try:
        long_key = "handbook.article.observation_unit_and_grain.body.1"
        with_sources = HandbookEntry(
            id="with_sources", title_key="app.title", category_key="handbook.category.foundations",
            body_paragraph_keys=(long_key, long_key, long_key), source_keys=("app.title",),
        )
        without_sources = HandbookEntry(
            id="without_sources", title_key="app.title", category_key="handbook.category.foundations",
            body_paragraph_keys=(long_key, long_key, long_key),
        )

        with patch("data_science_arcade.handbook.registry.HANDBOOK_ENTRIES", (with_sources, without_sources)):
            scene = HandbookScene(app, initial_entry_id="with_sources")
            lines_with_sources = len(scene.pages[0])
            scene._open_entry("without_sources")
            lines_without_sources = len(scene.pages[0])

        assert lines_with_sources < lines_without_sources
    finally:
        pygame.quit()


def test_page_nav_row_does_not_overlap_the_related_row():
    # Caught by eye in a real screenshot, not by any test: the two
    # constants controlling these rows' y-offsets left the page-nav row's
    # own bottom edge a few pixels below the related row's top edge.
    app = _init_app()
    try:
        entry = next(e for e in HANDBOOK_ENTRIES if e.related_entry_ids)
        scene = HandbookScene(app, initial_entry_id=entry.id)
        assert scene.back_page_button.rect.bottom < scene.buttons.buttons[-2].rect.top
    finally:
        pygame.quit()
