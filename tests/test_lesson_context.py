from data_science_arcade.workbench.context import DecisionState, LessonContext


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


def test_recording_identical_content_again_returns_the_existing_action_not_a_duplicate():
    # Matters concretely for Lesson 06: guided_work and independent_challenge
    # deliberately present the same issues again, so a student picking the
    # same correct option in both rounds must not double the Python Mirror.
    context = LessonContext()

    one = context.record_action("same_label", python_code="a = 1")
    two = context.record_action("same_label", python_code="a = 1")

    assert one is two
    assert context.actions == (one,)


def test_recording_identical_evidence_again_returns_the_existing_item_not_a_duplicate():
    context = LessonContext()
    action = context.record_action("fixed_price_column", python_code="x = 1")

    one = context.record_evidence("price had a decimal separator issue", source_action=action)
    two = context.record_evidence("price had a decimal separator issue", source_action=action)

    assert one is two
    assert context.evidence == (one,)


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

    context.restore_from_dict({"next_id": 99, "actions": [{"id": "action_1"}]})  # missing required "label_key"

    assert len(context.actions) == 1  # unchanged, not crashed
