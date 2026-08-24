import pygame

LOGICAL_SIZE = (960, 540)
TARGET_FPS = 60


def compute_scaled_rect(logical_size: tuple[int, int], window_size: tuple[int, int]) -> pygame.Rect:
    """Largest centered rect that fits logical_size into window_size, preserving aspect ratio."""
    logical_w, logical_h = logical_size
    window_w, window_h = window_size
    scale = min(window_w / logical_w, window_h / logical_h)
    scaled_w = max(1, int(logical_w * scale))
    scaled_h = max(1, int(logical_h * scale))
    x = (window_w - scaled_w) // 2
    y = (window_h - scaled_h) // 2
    return pygame.Rect(x, y, scaled_w, scaled_h)


def window_to_logical(
    window_pos: tuple[float, float],
    logical_size: tuple[int, int],
    window_size: tuple[int, int],
) -> tuple[float, float]:
    """Inverse of the scale/letterbox compute_scaled_rect() applies, for mouse input.

    A point inside the letterbox/pillarbox bars maps outside the 0..logical_size
    range, which is fine: it simply won't collide with any on-screen button.
    """
    rect = compute_scaled_rect(logical_size, window_size)
    scale = rect.width / logical_size[0]
    x = (window_pos[0] - rect.x) / scale
    y = (window_pos[1] - rect.y) / scale
    return (x, y)
