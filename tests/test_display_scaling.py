from data_science_arcade.core.display import compute_scaled_rect

LOGICAL_SIZE = (960, 540)


def test_exact_logical_size_is_unscaled_and_unoffset():
    rect = compute_scaled_rect(LOGICAL_SIZE, (960, 540))
    assert rect.size == (960, 540)
    assert rect.topleft == (0, 0)


def test_uniform_scale_up_has_no_letterbox():
    rect = compute_scaled_rect(LOGICAL_SIZE, (1920, 1080))
    assert rect.size == (1920, 1080)
    assert rect.topleft == (0, 0)


def test_wider_window_is_pillarboxed():
    # 2000x540: same height, extra width -> vertical bars on the sides.
    rect = compute_scaled_rect(LOGICAL_SIZE, (2000, 540))
    assert rect.height == 540
    assert rect.width < 2000
    assert rect.top == 0
    assert rect.left > 0
    assert rect.left == (2000 - rect.width) // 2


def test_taller_window_is_letterboxed():
    # 960x1000: same width, extra height -> horizontal bars top/bottom.
    rect = compute_scaled_rect(LOGICAL_SIZE, (960, 1000))
    assert rect.width == 960
    assert rect.height < 1000
    assert rect.left == 0
    assert rect.top > 0
    assert rect.top == (1000 - rect.height) // 2
