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
