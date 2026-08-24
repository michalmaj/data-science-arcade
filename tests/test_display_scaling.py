from data_science_arcade.core.display import compute_scaled_rect, window_to_logical

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


def test_window_to_logical_is_identity_at_1_to_1_scale():
    assert window_to_logical((480, 270), LOGICAL_SIZE, (960, 540)) == (480, 270)


def test_window_to_logical_divides_out_a_uniform_scale_up():
    # 1920x1080 is an exact 2x scale-up with no letterbox.
    x, y = window_to_logical((1920, 1080), LOGICAL_SIZE, (1920, 1080))
    assert (round(x), round(y)) == (960, 540)


def test_window_to_logical_accounts_for_pillarbox_offset():
    window_size = (2000, 540)
    rect = compute_scaled_rect(LOGICAL_SIZE, window_size)

    # A click on the rect's left edge should map to logical x=0.
    x, _y = window_to_logical((rect.left, rect.top), LOGICAL_SIZE, window_size)
    assert round(x) == 0

    # A click inside the left pillarbox bar maps outside the logical canvas.
    x, _y = window_to_logical((rect.left - 10, rect.top), LOGICAL_SIZE, window_size)
    assert x < 0


def test_window_to_logical_accounts_for_letterbox_offset():
    window_size = (960, 1000)
    rect = compute_scaled_rect(LOGICAL_SIZE, window_size)

    _x, y = window_to_logical((rect.left, rect.top), LOGICAL_SIZE, window_size)
    assert round(y) == 0

    _x, y = window_to_logical((rect.left, rect.top - 10), LOGICAL_SIZE, window_size)
    assert y < 0
