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
    created in, so this must run whenever pygame is (re-)initialized."""
    _cache.clear()
