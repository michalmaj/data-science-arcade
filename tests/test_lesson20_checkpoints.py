from data_science_arcade.lessons.l20_ab_test_commander.checkpoints import CHECKOUT_CHECKPOINTS, CORRECT_FINAL_CHECKPOINT


def test_there_are_three_checkpoints_in_day_order():
    assert [checkpoint.day for checkpoint in CHECKOUT_CHECKPOINTS] == [3, 10, 21]


def test_every_checkpoint_has_all_four_rows():
    for checkpoint in CHECKOUT_CHECKPOINTS:
        assert {row.key for row in checkpoint.rows} == {
            "primary_conversion",
            "guardrail_refund",
            "guardrail_support",
            "segment_mobile",
        }


def test_no_row_is_flagged():
    # This experiment's problem is a statistical illusion, not a
    # guardrail breach - see experiment_data.py.
    for checkpoint in CHECKOUT_CHECKPOINTS:
        assert all(row.flagged is False for row in checkpoint.rows)


def test_the_correct_final_checkpoint_is_the_last_one():
    assert CORRECT_FINAL_CHECKPOINT == 3 == len(CHECKOUT_CHECKPOINTS)
