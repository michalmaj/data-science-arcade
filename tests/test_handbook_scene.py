import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.fonts import get_font
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
    app = _init_app()
    try:
        scene = HandbookScene(app)
        scene.buttons.buttons[1].on_activate()  # GLOSSARY tab
        first_term_button = scene.buttons.buttons[2]
        first_term_button.on_activate()

        assert scene.selected_glossary_id == GLOSSARY_ENTRIES[0].id
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
    # spacing sized comfortably for the 4 real articles ran the glossary
    # tab's 10 real terms off the bottom of CONTENT_RECT entirely, the
    # last one overlapping the global Back button. Nothing in this
    # codebase clips overflow, so a scene has to keep its own content
    # inside its own bounds rather than relying on that.
    app = _init_app()
    try:
        scene = HandbookScene(app)
        for entries, switch_to_glossary in ((HANDBOOK_ENTRIES, False), (GLOSSARY_ENTRIES, True)):
            if switch_to_glossary:
                scene.buttons.buttons[1].on_activate()
            index_buttons = scene.buttons.buttons[2:-1]  # after the 2 tabs, before the global Back
            assert len(index_buttons) == len(entries)
            for button in index_buttons:
                assert CONTENT_RECT.top <= button.rect.top and button.rect.bottom <= CONTENT_RECT.bottom
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
