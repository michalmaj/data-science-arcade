from data_science_arcade.workbench.context import CONTEXT_SCHEMA_VERSION, DecisionState, LessonContext


def test_starts_with_nothing_recorded():
    context = LessonContext()
    assert context.actions == ()
    assert context.evidence == ()
    assert context.decision is None


def test_record_action_returns_it_and_appends_it_in_order():
    context = LessonContext()

    first = context.record_action("first", python_code="a = 1")
    second = context.record_action("second")

    assert context.actions == (first, second)
    assert first.label_key == "first"
    assert first.python_code == "a = 1"
    assert second.python_code is None


def test_actions_get_unique_ids_when_content_actually_differs():
    context = LessonContext()

    one = context.record_action("same_label", python_code="a = 1")
    two = context.record_action("same_label", python_code="a = 2")

    assert one.id != two.id


def test_recording_identical_content_twice_with_no_key_still_appends_both():
    # No key means no implicit content-equality guess: two genuinely
    # different actions could coincidentally share the same label/code,
    # and that alone isn't reason to merge them.
    context = LessonContext()

    one = context.record_action("same_label", python_code="a = 1")
    two = context.record_action("same_label", python_code="a = 1")

    assert one.id != two.id
    assert context.actions == (one, two)


def test_recording_with_the_same_key_updates_the_existing_action_in_place():
    # Matters concretely for Lesson 06: guided_work and independent_challenge
    # deliberately present the same issues again, so `_make_choose` passes
    # the issue's own column as the key - resolving "price" in both rounds
    # must update one slot, not double the Python Mirror.
    context = LessonContext()

    first = context.record_action("wrong_option", python_code="a = 1", key="price")
    second = context.record_action("right_option", python_code="a = 2", key="price")

    assert context.actions == (second,)
    assert second.id == first.id  # same slot, not a new entry
    assert second.label_key == "right_option"
    assert second.python_code == "a = 2"  # latest content wins


def test_recording_with_a_different_key_does_not_update_the_other_slot():
    context = LessonContext()

    price_action = context.record_action("price_fix", python_code="a = 1", key="price")
    currency_action = context.record_action("currency_fix", python_code="b = 2", key="currency")

    assert context.actions == (price_action, currency_action)
    assert price_action.id != currency_action.id


def test_recording_evidence_with_the_same_key_updates_the_existing_item_in_place():
    context = LessonContext()
    action = context.record_action("fixed_price_column", python_code="x = 1", key="price")

    first = context.record_evidence("first observation", source_action=action, key="price")
    second = context.record_evidence("updated observation", source_action=action, key="price")

    assert context.evidence == (second,)
    assert second.id == first.id
    assert second.label_key == "updated observation"


def test_recording_evidence_identical_content_twice_with_no_key_still_appends_both():
    context = LessonContext()
    action = context.record_action("fixed_price_column", python_code="x = 1")

    one = context.record_evidence("price had a decimal separator issue", source_action=action)
    two = context.record_evidence("price had a decimal separator issue", source_action=action)

    assert one.id != two.id
    assert context.evidence == (one, two)


def test_record_evidence_references_a_real_action_id_not_a_hand_typed_string():
    context = LessonContext()
    action = context.record_action("fixed_price_column", python_code="x = 1")

    evidence = context.record_evidence("price had a decimal separator issue", source_action=action)

    assert context.evidence == (evidence,)
    assert evidence.source_action_id == action.id


def test_evidence_without_a_source_action_is_allowed():
    context = LessonContext()

    evidence = context.record_evidence("a finding with no backing action")

    assert evidence.source_action_id is None


def test_set_decision_is_read_back_via_the_decision_property():
    context = LessonContext()
    decision = DecisionState(choices={"field": "option"}, supporting_evidence_ids=("evidence_1",))

    context.set_decision(decision)

    assert context.decision is decision


def test_python_mirror_joins_only_actions_that_have_real_code_in_order():
    context = LessonContext()
    context.record_action("no code here")
    context.record_action("first line", python_code="a = 1")
    context.record_action("also no code")
    context.record_action("second line", python_code="b = 2")

    assert context.python_mirror() == "a = 1\nb = 2"


def test_python_mirror_is_empty_string_when_nothing_has_code():
    context = LessonContext()
    context.record_action("no code")

    assert context.python_mirror() == ""


def test_two_separate_contexts_do_not_share_ids_or_state():
    first = LessonContext()
    second = LessonContext()

    action_a = first.record_action("a")
    action_b = second.record_action("b")

    assert first.actions == (action_a,)
    assert second.actions == (action_b,)
    # Both start their own counter at 1 - fine, since uniqueness only needs
    # to hold within one context; two contexts sharing a lesson instance
    # today are actually the *same* object (see scenario.py), not two.
    assert action_a.id == action_b.id == "action_1"


def test_to_dict_and_restore_from_dict_round_trip_actions_evidence_and_decision():
    original = LessonContext()
    action = original.record_action("fixed_price", python_code="x = 1")
    original.record_evidence("price was wrong", source_action=action)
    original.set_decision(DecisionState(choices={"field": "option"}, supporting_evidence_ids=("evidence_1",)))

    restored = LessonContext()
    restored.restore_from_dict(original.to_dict())

    assert restored.actions == original.actions
    assert restored.evidence == original.evidence
    assert restored.decision == original.decision


def test_evidence_detail_round_trips_through_to_dict_and_restore_from_dict():
    original = LessonContext()
    original.record_evidence("30-day repeat rate", detail="42%")

    restored = LessonContext()
    restored.restore_from_dict(original.to_dict())

    assert restored.evidence[0].detail == "42%"


def test_recording_evidence_with_the_same_key_updates_its_detail_too():
    context = LessonContext()
    context.record_evidence("repeat rate", key="window", detail="38%")

    context.record_evidence("repeat rate", key="window", detail="41%")

    assert len(context.evidence) == 1
    assert context.evidence[0].detail == "41%"


def test_restore_continues_id_numbering_without_colliding_with_a_new_recording():
    original = LessonContext()
    original.record_action("a", python_code="a = 1")  # "action_1"
    original.record_action("b", python_code="b = 2")  # "action_2"

    restored = LessonContext()
    restored.restore_from_dict(original.to_dict())
    new_action = restored.record_action("c", python_code="c = 3")

    assert new_action.id == "action_3"  # continues from next_id, not restarting at 1


def test_restore_from_dict_is_a_no_op_when_the_incoming_state_is_not_ahead():
    context = LessonContext()
    context.record_action("a", python_code="a = 1")
    context.record_action("b", python_code="b = 2")
    snapshot_before_growing_further = context.to_dict()
    context.record_action("c", python_code="c = 3")  # context is now ahead of the old snapshot

    context.restore_from_dict(snapshot_before_growing_further)

    assert len(context.actions) == 3  # "c" was not rolled back


def test_restore_from_dict_ignores_a_malformed_payload_instead_of_raising():
    context = LessonContext()
    context.record_action("a", python_code="a = 1")

    context.restore_from_dict(
        {"version": CONTEXT_SCHEMA_VERSION, "next_id": 99, "actions": [{"id": "action_1"}]}  # missing "label_key"
    )

    assert len(context.actions) == 1  # unchanged, not crashed


def test_restore_from_dict_ignores_an_unrecognized_version():
    context = LessonContext()
    context.record_action("a", python_code="a = 1")

    context.restore_from_dict({"version": 999, "next_id": 99, "actions": []})

    assert len(context.actions) == 1  # unchanged - a version this build doesn't understand is not trusted


def test_to_dict_includes_the_current_schema_version():
    assert LessonContext().to_dict()["version"] == CONTEXT_SCHEMA_VERSION


def test_key_round_trips_through_to_dict_and_restore_from_dict():
    original = LessonContext()
    original.record_action("fixed_price", python_code="x = 1", key="price")

    restored = LessonContext()
    restored.restore_from_dict(original.to_dict())
    # Recording again under the same key after a restore must still update
    # in place, not append - proving `key` itself survived the round trip,
    # not just label_key/python_code.
    updated = restored.record_action("fixed_price_v2", python_code="x = 2", key="price")

    assert restored.actions == (updated,)
