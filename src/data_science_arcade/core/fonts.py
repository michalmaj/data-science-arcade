import pygame

_cache: dict[int, pygame.font.Font] = {}


def get_font(size: int) -> pygame.font.Font:
    """Cached lookup for the default font at a given point size.

    Uses pygame's bundled default font, which covers Latin Extended-A (Polish
    diacritics included) without shipping/licensing a project font yet.
    """
    font = _cache.get(size)
    if font is None:
        font = pygame.font.Font(None, size)
        _cache[size] = font
    return font


def clear_cache() -> None:
    """Drop cached Font objects. Fonts are tied to the SDL context they were
    created in, so this must run right after every pygame.init() - App.init()
    already does this. Tests that call pygame.init() directly (a local
    fixture, not through App) must call this too: a stale Font surviving a
    pygame.quit()/init() cycle doesn't just render wrong, it can segfault
    the interpreter outright (seen when a parametrized test forgot this and
    crashed pytest mid-run rather than failing one test)."""
    _cache.clear()
